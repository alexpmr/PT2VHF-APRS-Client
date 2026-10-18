"""Render the README download table from the latest published GitHub release only.

For each package type, display its own GitHub Release asset download_count.
No downloads from previous versions are carried into the current version.
Usage: GH_TOKEN=$GITHUB_TOKEN python tools/sync_readme_release_downloads.py
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

REPO = os.getenv("GITHUB_REPOSITORY", "alexpmr/PT2VHF-APRS-Client")
TOKEN = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
BASE = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "PT2VHF-APRS-Client-current-downloads",
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


def build_section(release: dict) -> str:
    """Return one row per package type, sourced only from this release's assets."""
    tag = str(release.get("tag_name") or "").strip()
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("Missing or invalid latest release tag")
    prefix = f"https://github.com/{REPO}/releases/download/{tag}/"
    packages: dict[str, dict] = {}
    for asset in release.get("assets") or []:
        category = classify_asset(str(asset.get("name") or ""))
        if category is None:
            continue
        url = str(asset.get("browser_download_url") or "")
        if not url.startswith(prefix):
            continue
        if category in packages:
            raise ValueError(f"Duplicate application package category in {tag}: {category}")
        packages[category] = asset

    lines = [
        "<!-- DOWNLOAD_TABLE_START -->",
        f"## Downloads — versão {tag.removeprefix('v')}",
        "",
        "| Sistema | Tipo de pacote | Arquitetura | Baixar versão atual | Downloads da versão |",
        "|---|---|---|---|---:|",
    ]
    total = 0
    valid_counters = 0
    for key, system, package, architecture in CATEGORIES:
        asset = packages.get(key)
        if asset is None:
            lines.append(f"| {system} | {package} | {architecture} | Indisponível | — |")
            continue
        link = f"[Baixar]({asset['browser_download_url']})"
        raw_count = asset.get("download_count")
        if type(raw_count) is int and raw_count >= 0:
            total += raw_count
            valid_counters += 1
            display_count = f"{raw_count:,}".replace(",", ".")
        else:
            display_count = "—"
        lines.append(f"| {system} | {package} | {architecture} | {link} | {display_count} |")

    manual = next(
        (a.get("browser_download_url") for a in release.get("assets") or []
         if "manual" in str(a.get("name", "")).lower()
         and str(a.get("name", "")).lower().endswith(".pdf")
         and str(a.get("browser_download_url", "")).startswith(prefix)),
        None,
    )
    lines.extend([
        "",
        f"**Total contabilizado dos pacotes da {tag}: {total:,}.**".replace(",", "."),
        f"*Formatos com contagem disponível: {valid_counters}/{len(CATEGORIES)}.*",
        "",
        "> A contagem corresponde apenas aos downloads dos arquivos desta versão "
        "segundo o GitHub Releases. Cada nova versão começa com seus próprios contadores; "
        "versões anteriores não são somadas. Não representa instalações nem usuários únicos.",
        "",
        (f"[Manual PDF]({manual}) · " if manual else "")
        + f"[Notas da versão atual](https://github.com/{REPO}/releases/tag/{tag}) · "
        + f"[Todas as versões](https://github.com/{REPO}/releases)",
        "<!-- DOWNLOAD_TABLE_END -->",
        "",
    ])
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
    release = api("/releases/latest")
    tag = str(release.get("tag_name") or "")
    expected = os.getenv("PT2VHF_RELEASE_VERSION", "").strip().removeprefix("v")
    if expected and tag != "v" + expected:
        raise RuntimeError(f"Release incomplete: expected v{expected}, latest is {tag}")
    available = {
        classify_asset(str(asset.get("name") or ""))
        for asset in release.get("assets") or []
        if str(asset.get("browser_download_url") or "").startswith(
            f"https://github.com/{REPO}/releases/download/{tag}/"
        )
    }
    if expected and len(available - {None}) < len(CATEGORIES):
        raise RuntimeError("Release incomplete: some application formats have not been published")
    readme, sha = get_content("README.md")
    if not readme:
        raise RuntimeError("README.md not found")
    section = build_section(release)
    output = render_readme(readme, section)
    updated = update_content(
        "README.md", output, readme, sha,
        f"docs: refresh per-package download counts for {tag}",
    )
    print(f"Release {tag}: {len(available - {None})} package formats; README changed={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
