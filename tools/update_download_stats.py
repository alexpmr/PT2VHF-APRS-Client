#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
START = "<!-- DOWNLOAD_STATS_START -->"
END = "<!-- DOWNLOAD_STATS_END -->"

REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "alexpmr/PT2VHF-APRS-Client").strip()
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()


def _request_json(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "PT2VHF-APRS-Client-download-stats",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_releases() -> list[dict]:
    releases: list[dict] = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=100&page={page}"
        batch = _request_json(url)
        if not batch:
            break
        releases.extend(item for item in batch if not item.get("draft"))
        if len(batch) < 100:
            break
        page += 1
    return releases


def classify_asset(name: str) -> str | None:
    n = name.lower()

    # Only application packages count. Documentation, SBOMs and license
    # inventories are deliberately excluded from adoption totals.
    if n.endswith((".exe", ".msi")):
        return "windows"
    if "portable_x64" in n and n.endswith(".zip"):
        return "windows"
    if n.endswith(".dmg"):
        return "macos"
    if n.endswith(".deb") or n.endswith(".appimage"):
        return "linux"
    if "linux" in n and n.endswith((".tar.gz", ".tgz")):
        return "linux"
    return None


def build_table(releases: list[dict]) -> str:
    rows: list[str] = []
    totals = {"windows": 0, "linux": 0, "macos": 0}

    for release in releases:
        counts = {"windows": 0, "linux": 0, "macos": 0}
        for asset in release.get("assets") or []:
            platform = classify_asset(str(asset.get("name") or ""))
            if platform:
                counts[platform] += int(asset.get("download_count") or 0)

        total = sum(counts.values())
        for key in totals:
            totals[key] += counts[key]

        tag = str(release.get("tag_name") or "").strip()
        if not tag:
            continue
        tag_url = f"https://github.com/{REPOSITORY}/releases/tag/{quote(tag, safe='')}"
        rows.append(
            f"| [{tag}]({tag_url}) | {counts['windows']} | {counts['linux']} | "
            f"{counts['macos']} | **{total}** |"
        )

    grand_total = sum(totals.values())
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        START,
        "",
        f"_Atualizado automaticamente em **{updated}** a partir dos contadores das GitHub Releases._",
        "",
        "| Release | Windows | Linux | macOS | Total |",
        "|---|---:|---:|---:|---:|",
        *rows,
        f"| **Acumulado** | **{totals['windows']}** | **{totals['linux']}** | "
        f"**{totals['macos']}** | **{grand_total}** |",
        "",
        "> Os números representam downloads dos pacotes do aplicativo, não usuários únicos. "
        "Manual PDF, SBOMs e arquivos de licenças não entram no total.",
        "",
        END,
    ]
    return "\n".join(lines)


def main() -> int:
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("Marcadores DOWNLOAD_STATS não encontrados no README.md.")

    start = text.index(START)
    end = text.index(END, start) + len(END)
    block = build_table(fetch_releases())
    updated = text[:start] + block + text[end:]
    README.write_text(updated, encoding="utf-8")
    print("README download statistics updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
