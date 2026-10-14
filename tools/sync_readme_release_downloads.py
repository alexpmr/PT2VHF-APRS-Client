"""Publish README download links only after *all* release assets exist.

Uses the GitHub contents API so the update applies safely to latest main even
when the release pipeline was triggered from an older SHA.
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.request
import urllib.error

REPO = os.environ.get("GITHUB_REPOSITORY", "alexpmr/PT2VHF-APRS-Client")
TOKEN = os.environ["GH_TOKEN"]
VERSION = os.environ.get("PT2VHF_RELEASE_VERSION", "1.14.33")
TAG = "v" + VERSION
BASE = "https://api.github.com/repos/" + REPO
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "PT2VHF-APRS-Client-Release",
    "Authorization": "Bearer " + TOKEN,
    "X-GitHub-Api-Version": "2022-11-28",
}


def api(url, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, method=method, headers=HEADERS
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)


release = api(BASE + "/releases/tags/" + TAG)
asset_names = {a["name"] for a in release.get("assets", [])}
if len(asset_names) < 15:
    raise SystemExit("Expected all 15 platform downloads before README sync")
blob = api(BASE + "/contents/README.md?ref=main")
source = base64.b64decode(blob["content"]).decode("utf-8")
start = source.index("## Downloads — versão ")
# Delimit the Downloads section using the next generic Markdown H2.
# A release is valid even without a version-named "Novidades" heading.
next_heading = re.search(r"(?m)^## ", source[start + len("## Downloads — versão "):])
if not next_heading:
    raise SystemExit("Could not locate the heading following Downloads")
end = start + len("## Downloads — versão ") + next_heading.start()
section = source[start:end]
old_version_match = re.search(r"## Downloads — versão (\d+\.\d+\.\d+)", section)
if not old_version_match:
    raise SystemExit("Downloads heading not recognized")
old_version = old_version_match.group(1)
# Validate asset availability BEFORE changing visible public links.
links = re.findall(
    r"https://github\.com/" + re.escape(REPO) +
    r"/releases/download/v" + re.escape(old_version) +
    r"/([^\s)]+)", section
)
if len(links) < 15:
    raise SystemExit("Expected at least 15 download links, got " + str(len(links)))
missing = sorted({name.replace(old_version, VERSION) for name in links} - asset_names)
if missing:
    raise SystemExit("Cannot publish nonexistent assets: " + ", ".join(missing))
new_section = section.replace(old_version, VERSION)
new_section = new_section.replace(" (última publicada)", "")
new_section = re.sub(
    r"\*\*Links diretos de todos os instaladores e edições portáteis publicados\.\*\*.*?\n",
    "**Links diretos de todos os instaladores e edições portáteis publicados na release " + TAG + ".**\n",
    new_section,
)
# Remove obsolete warning about a new release still being built.
new_section = re.sub(
    r"A nova v" + re.escape(VERSION) +
    r" está em preparação:.*?não retorna 404\. Na publicação, o pipeline atualiza a lista automaticamente\.",
    "Todos os links foram verificados nos Assets desta release.",
    new_section,
)
output = source[:start] + new_section + source[end:]
if output == source:
    print("README already updated")
else:
    api(
        BASE + "/contents/README.md", method="PUT",
        payload={
            "message": "docs: update published v" + VERSION + " direct downloads",
            "content": base64.b64encode(output.encode("utf-8")).decode("ascii"),
            "sha": blob["sha"],
            "branch": "main",
        },
    )
    print("Updated README links to " + TAG)
