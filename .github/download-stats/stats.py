"""Contador acumulado de downloads por tipo de build, para os selos do README.

O GitHub só conta downloads por arquivo de cada release, e releases/arquivos antigos
podem ser apagados. Aqui o histórico fica no ramo `badges` (`downloads/state.json`):
para cada versão e arquivo guarda o maior número já visto, então o total nunca zera.
Os totais por tipo (definidos em `types.json`, ao lado) viram arquivos "endpoint"
do shields.io em `downloads/<tipo>.json`.

Uso: python .github/download-stats/stats.py <pasta>
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

CONFIG = json.loads((Path(__file__).with_name("types.json")).read_text(encoding="utf-8"))
TYPES = [(key, re.compile(pattern, re.I)) for key, pattern in CONFIG["types"]]
GROUPS = CONFIG.get("groups", {})
TOTAL = CONFIG.get("total") or list(GROUPS) or [key for key, _ in TYPES]


def kind(asset_name):
    for key, pattern in TYPES:
        if pattern.search(asset_name):
            return key
    return None  # hashes, SBOM, metadados de atualização etc. não contam


def fetch_releases(repository, token=None, opener=urllib.request.urlopen):
    releases, page = [], 1
    while True:
        req = urllib.request.Request("https://api.github.com/repos/%s/releases?per_page=100&page=%d" % (repository, page),
                                     headers={"Accept": "application/vnd.github+json", "User-Agent": "download-stats"})
        if token:
            req.add_header("Authorization", "Bearer " + token)
        with opener(req, timeout=30) as resp:
            batch = json.loads(resp.read())
        releases += batch
        if len(batch) < 100:
            return releases
        page += 1


def merge(state, releases):
    """Atualiza o histórico com o maior contador visto de cada (versão, arquivo)."""
    seen = state.setdefault("assets", {})
    for release in releases:
        tag = str(release.get("tag_name") or "")
        if not tag or release.get("draft"):
            continue
        for asset in release.get("assets", []):
            key = tag + "/" + asset["name"]
            seen[key] = max(int(seen.get(key, 0)), int(asset.get("download_count") or 0))
    return state


def totals(state):
    out = {key: 0 for key, _ in TYPES}
    for key, count in state.get("assets", {}).items():
        k = kind(key.split("/", 1)[1])
        if k:
            out[k] += count
    for group, members in GROUPS.items():
        out[group] = sum(out[m] for m in members)
    out["total"] = sum(out[k] for k in TOTAL)
    return out


def badge(count, label="downloads"):
    return {"schemaVersion": 1, "label": label, "message": "{:,}".format(count).replace(",", "."),
            "color": "2ea44f" if count else "lightgrey", "cacheSeconds": 1800}


def main(folder, repository=None, token=None, releases=None):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "state.json"
    state = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    merge(state, releases if releases is not None else fetch_releases(repository, token))
    path.write_text(json.dumps(state, indent=1, sort_keys=True), encoding="utf-8")
    result = totals(state)
    for key, count in result.items():
        (folder / (key + ".json")).write_text(json.dumps(badge(count)), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1] if len(sys.argv) > 1 else "downloads", os.environ["GITHUB_REPOSITORY"],
                          os.environ.get("GITHUB_TOKEN")), indent=1))
