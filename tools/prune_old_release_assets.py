#!/usr/bin/env python3
"""Delete binary/manual attachments from obsolete GitHub Releases, preserving history.

One-time maintenance. Never delete releases, tags, source, or the latest release.
Validated specifically for v1.14.42. Reruns are idempotent.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EXPECTED_LATEST = "v1.14.42"
API = "https://api.github.com"
REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GH_TOKEN"]
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
KEEP_NAMES = {"SBOM", "LICENSE", "LICENCE", "THIRD_PARTY"}
DELETE_EXTENSIONS = (".exe", ".msi", ".msix", ".pdf", ".dmg", ".pkg", ".deb",
                     ".rpm", ".appimage", ".zip", ".7z", ".tar.gz", ".tgz")
summary = {"latest": EXPECTED_LATEST, "dry_run": DRY_RUN, "scanned": 0,
           "deleted": 0, "failed": 0, "preserved_current": 0,
           "preserved_historical_metadata": True, "failure_details": []}


def api(method: str, path: str, *, missing_ok: bool = False):
    url = path if path.startswith("https://") else API + path
    headers = {"Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "PT2VHF-release-maintenance"}
    req = Request(url, headers=headers, method=method)
    for attempt in range(4):
        try:
            with urlopen(req, timeout=45) as response:
                data = response.read()
                return json.loads(data) if data else None
        except HTTPError as exc:
            if missing_ok and exc.code == 404:
                return None
            if exc.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise
        except (TimeoutError, URLError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def pages(path: str):
    page = 1
    while True:
        values = api("GET", path + ("&" if "?" in path else "?") + f"per_page=100&page={page}")
        if not values:
            break
        yield from values
        if len(values) < 100:
            break
        page += 1


def is_obsolete_distribution(name: str) -> bool:
    lower = name.lower()
    return lower.endswith(DELETE_EXTENSIONS)


def main():
    # A hard version pin ensures this one-time cleanup cannot silently delete
    # binaries from a later release if the workflow is rerun after an update.
    version = Path("VERSION").read_text(encoding="utf-8").strip()
    latest = api("GET", f"/repos/{REPO}/releases/latest")
    if version != EXPECTED_LATEST.removeprefix("v") or latest["tag_name"] != EXPECTED_LATEST:
        raise SystemExit("ABORT: VERSION/main and latest release must both be " + EXPECTED_LATEST)
    current = list(pages(f"/repos/{REPO}/releases/{latest['id']}/assets"))
    names = [a["name"] for a in current]
    assert len(current) >= 20, "ABORT: current release must have at least 20 attachments"
    assert any(n.lower().endswith(".pdf") for n in names), "ABORT: current manual absent"
    assert any(n.lower().endswith(".exe") for n in names), "ABORT: current Windows artifacts absent"
    summary["preserved_current"] = len(current)
    print(f"Preserving latest {EXPECTED_LATEST}: {len(current)} assets", flush=True)
    for release in pages(f"/repos/{REPO}/releases"):
        if release["id"] == latest["id"]:
            continue
        for attachment in pages(f"/repos/{REPO}/releases/{release['id']}/assets"):
            name = attachment["name"]
            if not is_obsolete_distribution(name):
                continue
            summary["scanned"] += 1
            print(("WOULD DELETE" if DRY_RUN else "DELETE") + f" {release['tag_name']}/{name}", flush=True)
            if DRY_RUN:
                continue
            try:
                api("DELETE", f"/repos/{REPO}/releases/assets/{attachment['id']}", missing_ok=True)
                summary["deleted"] += 1
            except (HTTPError, URLError, TimeoutError) as exc:
                summary["failed"] += 1
                summary["failure_details"].append(f"{release['tag_name']}/{name}: {exc}")
    # Independently confirm the current release remains complete.
    after = list(pages(f"/repos/{REPO}/releases/{latest['id']}/assets"))
    if {a["id"] for a in current} != {a["id"] for a in after}:
        raise RuntimeError("Current assets changed during maintenance!")
    report = json.dumps(summary, indent=2, ensure_ascii=False)
    print(report)
    output = os.environ.get("GITHUB_STEP_SUMMARY")
    if output:
        with open(output, "a", encoding="utf-8") as summary_file:
            summary_file.write("## Limpeza de versões antigas\n\n")
            summary_file.write(f"- Release mantida: {EXPECTED_LATEST} ({len(after)} arquivos)\n")
            summary_file.write(f"- Distribuições antigas identificadas: {summary['scanned']}\n")
            summary_file.write(f"- Distribuições antigas apagadas: {summary['deleted']}\n")
            summary_file.write(f"- Falhas: {summary['failed']}\n")
            summary_file.write("- Tags, notas de release, código-fonte e arquivos de licenças preservados.\n")
    if summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
