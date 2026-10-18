"""Maintain a top-of-README lifetime *known minimum* of release-asset downloads.

Usage in GitHub Actions: GH_TOKEN=$GITHUB_TOKEN python tools/sync_readme_release_downloads.py
Only counts published GitHub Release assets; removed assets observed earlier are kept.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

REPO = os.getenv("GITHUB_REPOSITORY", "alexpmr/PT2VHF-APRS-Client")
TOKEN = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
BASE = f"https://api.github.com/repos/{REPO}"
HISTORY_PATH = "data/release_download_history.json"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "PT2VHF-APRS-Client-download-history",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

CATEGORIES = (
    ("win_setup_x64", "Windows 10/11", "Instalador EXE", "x64"),
    ("win_portable_x64", "Windows 10/11", "Portátil EXE", "x64"),
    ("win_setup_arm64", "Windows 10/11", "Instalador EXE", "ARM64"),
    ("win_portable_arm64", "Windows 10/11", "Portátil EXE", "ARM64"),
    ("win7_setup_x64", "Windows 7 Legacy", "Instalador EXE", "x64"),
    ("win7_portable_x64", "Windows 7 Legacy", "Portátil EXE", "x64"),
    ("linux_appimage_x64", "Linux", "AppImage", "x86_64"),
    ("linux_deb_x64", "Linux", "DEB", "x86_64"),
    ("linux_tar_x64", "Linux", "TAR.GZ", "x86_64"),
    ("linux_appimage_arm64", "Linux", "AppImage", "ARM64"),
    ("linux_deb_arm64", "Linux", "DEB", "ARM64"),
    ("linux_tar_arm64", "Linux", "TAR.GZ", "ARM64"),
    ("mac_dmg_x64", "macOS", "DMG", "Intel x86_64"),
    ("mac_dmg_arm64", "macOS", "DMG", "Apple Silicon"),
)


def api(path: str, method: str = "GET", payload: dict | None = None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = dict(HEADERS)
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, headers=headers, method=method, data=data)
    with urllib.request.urlopen(request, timeout=50) as response:
        return json.load(response)


def classify_asset(name: str) -> str | None:
    n = name.lower()
    if not (n.startswith("pt2vhf_aprs_client") or n.startswith("pt2vhf-aprs-client")
            or n.startswith("pt2vhf_aprs_")):
        return None
    if any(word in n for word in ("manual", "checksum", "sbom", "license", "source", "debug")):
        return None
    arm = "arm64" in n or "aarch64" in n
    x64 = "x64" in n or "x86_64" in n or "amd64" in n
    if n.endswith((".exe", ".msi")) or (n.endswith(".zip") and "portable" in n):
        if "win7" in n or "legacy" in n:
            if not x64:
                return None
            return "win7_portable_x64" if "portable" in n else "win7_setup_x64" if "setup" in n else None
        if "portable" not in n and "setup" not in n:
            return None
        arch = "arm64" if arm else "x64" if x64 else None
        return f"win_{'portable' if 'portable' in n else 'setup'}_{arch}" if arch else None
    if n.endswith(".dmg"):
        return "mac_dmg_arm64" if arm else "mac_dmg_x64" if x64 else None
    if n.endswith((".appimage", ".deb", ".tar.gz", ".tgz")):
        kind = "appimage" if n.endswith(".appimage") else "deb" if n.endswith(".deb") else "tar"
        arch = "arm64" if arm else "x64" if x64 else None
        return f"linux_{kind}_{arch}" if arch else None
    return None


def fetch_releases() -> list[dict]:
    all_releases = []
    for page in range(1, 100):
        batch = api(f"/releases?per_page=100&page={page}")
        if not isinstance(batch, list):
            raise RuntimeError("GitHub Releases returned an unexpected value")
        all_releases += [r for r in batch if not r.get("draft")]
        if len(batch) < 100:
            return all_releases
    raise RuntimeError("More than 9,900 releases: pagination limit reached")


def collect_history(releases: list[dict], previous: dict, now: str) -> tuple[dict, bool]:
    history = {"schema": 1, "updated_at": previous.get("updated_at"),
               "assets": dict(previous.get("assets") or {})}
    changed = not previous.get("schema")
    for release in releases:
        tag = str(release.get("tag_name") or "")
        for asset in release.get("assets") or []:
            category = classify_asset(str(asset.get("name") or ""))
            if category is None or asset.get("id") is None:
                continue
            raw_count = asset.get("download_count")
            if not isinstance(raw_count, int) or raw_count < 0:
                continue
            asset_id = str(asset["id"])
            old = history["assets"].get(asset_id) or {}
            new_count = max(int(old.get("count", 0)), raw_count)
            item = {"tag": tag, "name": asset["name"], "category": category,
                    "count": new_count}
            if item != {k: old.get(k) for k in item}:
                history["assets"][asset_id] = item
                changed = True
    if changed:
        history["updated_at"] = now
    return history, changed


def current_packages(releases: list[dict]) -> dict[str, dict]:
    results: dict[str, dict] = {}
    releases = sorted((r for r in releases if not r.get("prerelease")), key=lambda r: r.get("published_at") or r.get("created_at") or "", reverse=True)
    for release in releases:
        for asset in release.get("assets") or []:
            category = classify_asset(str(asset.get("name") or ""))
            url = str(asset.get("browser_download_url") or "")
            if category and category not in results and url.startswith(f"https://github.com/{REPO}/releases/download/"):
                results[category] = {"url": url, "tag": release.get("tag_name") or ""}
    return results


def build_section(releases: list[dict], history: dict, latest_tag: str) -> str:
    counts = {k: 0 for k, *_ in CATEGORIES}
    observed = set()
    for asset in history.get("assets", {}).values():
        category = asset.get("category")
        if category in counts:
            counts[category] += max(0, int(asset.get("count", 0)))
            observed.add(category)
    available = current_packages(releases)
    lines = [
        "<!-- DOWNLOAD_TABLE_START -->",
        f"## Downloads — versão {latest_tag.removeprefix('v')}",
        "",
        "| Sistema | Tipo de pacote | Arquitetura | Baixar versão disponível | Downloads acumulados |",
        "|---|---|---|---|---:|",
    ]
    for key, system, package, arch in CATEGORIES:
        item = available.get(key)
        if item:
            version = str(item["tag"])
            label = "Baixar" if version == latest_tag else f"Baixar {version}"
            link = f"[{label}]({item['url']})"
        else:
            link = "Indisponível"
        count = f"≥ {counts[key]:,}".replace(",", ".") if key in observed else "—"
        lines.append(f"| {system} | {package} | {arch} | {link} | {count} |")
    total = sum(counts.values())
    observed_tags = {str(a.get("tag")) for a in history.get("assets", {}).values() if a.get("tag")}
    coverage = f"{len(observed_tags)} versões públicas com assets recuperáveis" if observed_tags else "nenhuma release coletada"
    when = history.get("updated_at") or "Aguardando primeira coleta automática"
    if "T" in when:
        when = when.replace("T", " ").replace("+00:00", " UTC")
    latest = next((r for r in releases if r.get("tag_name") == latest_tag), {})
    manual = next((a.get("browser_download_url") for a in latest.get("assets", [])
                   if "manual" in str(a.get("name", "")).lower()
                   and str(a.get("name", "")).lower().endswith(".pdf")
                   and str(a.get("browser_download_url", "")).startswith(f"https://github.com/{REPO}/releases/download/")), None)
    lines += [
        "",
        f"**Total mínimo conhecido de downloads dos pacotes: ≥ {total:,}.**".replace(",", "."),
        f"**Cobertura histórica disponível:** {coverage}.",
        "",
        "> **Contadores históricos mínimos (≥):** soma dos downloads dos arquivos de versões ainda "
        "consultáveis e dos registros previamente preservados. Instaladores removidos antes da primeira "
        "coleta não podem ser recuperados pela API do GitHub. Esses números **não são instalações "
        "nem usuários únicos**; arquivos auxiliares não entram no total.",
        "",
        f"*Última alteração dos dados coletados: {when}.*",
        "",
        (f"[Manual PDF]({manual}) · " if manual else "")
        + f"[Notas da versão atual](https://github.com/{REPO}/releases/tag/{latest_tag}) · "
        + f"[Todas as versões](https://github.com/{REPO}/releases)",
        "<!-- DOWNLOAD_TABLE_END -->",
        "",
    ]
    return "\n".join(lines)


def render_readme(source: str, section: str) -> str:
    start_marker = "<!-- DOWNLOAD_TABLE_START -->"
    end_marker = "<!-- DOWNLOAD_TABLE_END -->"
    if start_marker in source and end_marker in source:
        start = source.index(start_marker)
        end = source.index(end_marker, start) + len(end_marker)
        source = source[:start].rstrip("\n") + "\n\n" + source[end:].lstrip("\n")
    else:
        match = re.search(r"(?m)^## Downloads — versão [^\n]*\n", source)
        if match:
            next_heading = re.search(r"(?m)^## ", source[match.end():])
            end = match.end() + next_heading.start() if next_heading else len(source)
            source = source[:match.start()].rstrip("\n") + "\n\n" + source[end:].lstrip("\n")
    lines = source.split("\n", 1)
    if len(lines) != 2 or not lines[0].startswith("# PT2VHF APRS Client"):
        raise ValueError("Unexpected README title; refusing to modify")
    description = "Cliente APRS-IS para Windows, Linux e macOS, com mapas, mensagens, topologia RF e TNC."
    body = lines[1].lstrip("\n")
    if body.startswith(description + "\n\n"):
        body = body[len(description) + 2:]
    return lines[0] + "\n\n" + description + "\n\n" + section.rstrip() + "\n\n" + body


def get_content(path: str) -> tuple[str, str | None]:
    try:
        response = api("/contents/" + urllib.parse.quote(path, safe="/") + "?ref=main")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return "", None
        raise
    return base64.b64decode(response["content"]).decode("utf-8"), response["sha"]


def update_content(path: str, data: str, existing: str, sha: str | None, message: str) -> bool:
    if data == existing:
        return False
    if not TOKEN:
        raise RuntimeError("GH_TOKEN or GITHUB_TOKEN required to publish README updates")
    body = {"message": message, "branch": "main",
            "content": base64.b64encode(data.encode("utf-8")).decode("ascii")}
    if sha:
        body["sha"] = sha
    api("/contents/" + urllib.parse.quote(path, safe="/"), method="PUT", payload=body)
    return True


def main() -> int:
    releases = fetch_releases()
    latest = api("/releases/latest")
    tag = str(latest["tag_name"])
    expected = os.getenv("PT2VHF_RELEASE_VERSION", "").strip().removeprefix("v")
    if expected and tag != "v" + expected:
        raise RuntimeError(f"Release incomplete: expected v{expected}, latest is {tag}")
    latest_categories = {classify_asset(str(a.get("name") or "")) for a in latest.get("assets") or []}
    if expected and len(latest_categories - {None}) < len(CATEGORIES):
        raise RuntimeError("Release incomplete: some application formats have not been published")
    releases = [latest] + [r for r in releases if r.get("id") != latest.get("id")]
    previous_raw, previous_sha = get_content(HISTORY_PATH)
    previous = json.loads(previous_raw) if previous_raw else {}
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    history, changed = collect_history(releases, previous, now)
    readme, readme_sha = get_content("README.md")
    if not readme:
        raise RuntimeError("README.md not found")
    new_readme = render_readme(readme, build_section(releases, history, tag))
    history_text = json.dumps(history, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    saved = update_content(HISTORY_PATH, history_text, previous_raw, previous_sha,
                           "docs: preserve per-asset cumulative download history")
    updated = update_content("README.md", new_readme, readme, readme_sha,
                             "docs: display current downloads and historical minimum by installer")
    print(f"Release {tag}: {len(history['assets'])} assets; history changed={saved}; README changed={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
