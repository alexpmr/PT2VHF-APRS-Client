#!/usr/bin/env python3
"""Remove obsolete GitHub Release installers/manuals; preserve notes, tags and SBOMs.

Dry-run by default. --execute requires the GitHub Actions token and main branch.
Only Release attachments of distribution file types are eligible. Never remove
the latest published stable release, regardless of filename.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "https://api.github.com"
DISTRIBUTION = re.compile(
    r"\.(?:exe|msi|dmg|pkg|deb|rpm|appimage|pdf|zip|7z|tar\.gz)$",
    flags=re.IGNORECASE,
)
REQUIRED_CURRENT = (
    "PT2VHF_APRS_Client_Setup_x64_",
    "PT2VHF_APRS_Client_Portable_x64_",
    "PT2VHF_APRS_Client_Setup_Win7_Legacy_x64_",
    "PT2VHF_APRS_Client_macOS_arm64_",
    "PT2VHF_APRS_Client_Manual_",
)


def api(method: str, path: str):
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "PT2VHF-Release-Maintenance",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    url = API + path
    for attempt in range(12):
        try:
            req = Request(url, method=method, headers=headers)
            with urlopen(req, timeout=50) as response:
                result = json.loads(response.read()) if method == "GET" else None
                remaining = response.headers.get("X-RateLimit-Remaining")
                reset = response.headers.get("X-RateLimit-Reset")
                if remaining and reset and int(remaining) <= 3:
                    delay = max(0, int(reset) - int(time.time())) + 3
                    if delay > 0:
                        print("GitHub rate limit near exhaustion; waiting " + str(delay) + " seconds", flush=True)
                        time.sleep(delay)
                return result
        except HTTPError as exc:
            reset = exc.headers.get("X-RateLimit-Reset")
            retry = exc.headers.get("Retry-After")
            remaining = exc.headers.get("X-RateLimit-Remaining")
            msg = exc.read(512).decode("utf-8", errors="replace")
            if exc.code in (403, 429) and (retry or remaining == "0" or "secondary rate limit" in msg.lower()):
                delay = int(retry) if retry and retry.isdigit() else (
                    max(3, int(reset) - int(time.time()) + 3) if reset and reset.isdigit() else 75
                )
                print("Rate limited; waiting " + str(delay) + " seconds", flush=True)
                time.sleep(delay)
                continue
            raise RuntimeError(method + " " + path + " failed: HTTP " + str(exc.code) + " " + msg) from exc
        except (URLError, TimeoutError) as exc:
            if attempt >= 11:
                raise
            time.sleep(min(60, 2 ** attempt))
    raise RuntimeError("GitHub API retries exhausted")


def all_releases(repository: str):
    for page in range(1, 50):
        batch = api("GET", "/repos/" + repository + "/releases?per_page=100&page=" + str(page))
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected Releases API response")
        yield from batch
        if len(batch) < 100:
            return
    raise RuntimeError("More than 4900 releases: refusing incomplete pagination")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Actually delete obsolete distribution assets")
    args = parser.parse_args()
    repository = os.environ.get("GITHUB_REPOSITORY", "alexpmr/PT2VHF-APRS-Client")
    if repository != "alexpmr/PT2VHF-APRS-Client":
        raise RuntimeError("Unexpected repository; refusing cleanup")
    version = Path(__file__).resolve().parents[1].joinpath("VERSION").read_text(encoding="utf-8").strip()
    expected_tag = "v" + version
    current = api("GET", "/repos/" + repository + "/releases/latest")
    if current.get("tag_name") != expected_tag or current.get("draft") or current.get("prerelease"):
        raise RuntimeError("Latest published release does not match VERSION; refusing cleanup")
    current_assets = {asset["name"] for asset in current.get("assets", [])}
    if len(current_assets) < 15 or any(not any(name.startswith(prefix) for name in current_assets) for prefix in REQUIRED_CURRENT):
        raise RuntimeError("Latest release seems incomplete: aborting to protect working downloads")

    if args.execute:
        if os.environ.get("GITHUB_REF") != "refs/heads/main":
            raise RuntimeError("Refusing destructive cleanup outside main")
        if not os.environ.get("GH_TOKEN") and not os.environ.get("GITHUB_TOKEN"):
            raise RuntimeError("Missing GitHub Actions token")

    releases = list(all_releases(repository))
    candidates = []
    protected = 0
    for rel in releases:
        if rel.get("id") == current["id"] or rel.get("tag_name") == expected_tag:
            protected += len(rel.get("assets", []))
            continue
        if rel.get("draft"):  # Avoid interfering with ongoing draft packaging.
            continue
        for asset in rel.get("assets", []):
            if DISTRIBUTION.search(str(asset["name"])):
                candidates.append((rel["tag_name"], int(asset["id"]), asset["name"], int(asset.get("size") or 0)))

    count = len(candidates)
    total_gib = round(sum(x[3] for x in candidates) / (1024 ** 3), 2)
    print(json.dumps({
        "mode": "EXECUTE" if args.execute else "DRY_RUN",
        "current_release": expected_tag,
        "release_records": len(releases),
        "latest_assets_protected": protected,
        "old_distribution_files": count,
        "old_distribution_size_gib": total_gib,
    }, ensure_ascii=False), flush=True)

    if not args.execute:
        for tag, _id, name, _size in candidates[:15]:
            print("WOULD DELETE", tag, name, flush=True)
        return

    deleted = 0
    for tag, asset_id, name, size in candidates:
        api("DELETE", "/repos/" + repository + "/releases/assets/" + str(asset_id))
        deleted += 1
        if deleted % 25 == 0 or deleted == count:
            print("DELETED", deleted, "of", count, "last:", tag, name, flush=True)
        # GitHub secondary API limit for DELETE requests is point-weighted.
        time.sleep(0.45)
    print("DONE: deleted", deleted, "old installers/packages/manuals; current release", expected_tag, "untouched", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("FAILED:", str(exc), file=sys.stderr, flush=True)
        sys.exit(1)
