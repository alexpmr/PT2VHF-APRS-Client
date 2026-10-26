#!/usr/bin/env python3
"""Publica metadados APRS após copiar instaladores REAIS para a hospedagem.

Uso: python scripts/sync_aprs_manifest.py --version 1.14.59 --apply
Sem --apply, apenas demonstra o resultado, sem modificar o manifesto.
Nao publica arquivos inexistentes, fontes, checksums ou URLs de GitLab.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from datetime import date
from pathlib import Path

SITE = "https://www.pt2vhf.com"
ROOT = Path(__file__).resolve().parents[1] / "publish"
FILES = ROOT / "downloads" / "aprs-client"
MANIFEST = ROOT / "updates.json"

def candidates(version: str):
    return [
        ("windows-installer","win-setup-x64","x64","windows-x64",f"PT2VHF_APRS_Client_Setup_x64_v{version}.exe"),
        ("windows-portable","win-portable-x64","x64","windows-x64",f"PT2VHF_APRS_Client_Portable_x64_v{version}.exe"),
        ("windows-installer","win-setup-arm64","ARM64","windows-arm64",f"PT2VHF_APRS_Client_Setup_ARM64_v{version}.exe"),
        ("windows-portable","win-portable-arm64","ARM64","windows-arm64",f"PT2VHF_APRS_Client_Portable_ARM64_v{version}.exe"),
        ("linux-appimage","linux-appimage-x64","x64","linux-x64",f"PT2VHF_APRS_Client_x86_64_v{version}.AppImage"),
        ("linux-appimage","linux-appimage-arm64","ARM64","linux-arm64",f"PT2VHF_APRS_Client_arm64_v{version}.AppImage"),
        ("linux-deb","linux-deb-x64","x64","linux-x64",f"pt2vhf-aprs-client_{version}_amd64.deb"),
        ("linux-deb","linux-deb-arm64","ARM64","linux-arm64",f"pt2vhf-aprs-client_{version}_arm64.deb"),
        ("linux-targz","linux-tar-x64","x64","linux-x64",f"PT2VHF_APRS_Client_Linux_x86_64_v{version}.tar.gz"),
        ("linux-targz","linux-tar-arm64","ARM64","linux-arm64",f"PT2VHF_APRS_Client_Linux_arm64_v{version}.tar.gz"),
        ("macos","mac-dmg-x64","Intel","macos-x64",f"PT2VHF_APRS_Client_macOS_x86_64_v{version}.dmg"),
        ("macos","mac-dmg-arm64","Apple Silicon","macos-arm64",f"PT2VHF_APRS_Client_macOS_arm64_v{version}.dmg"),
    ]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", required=True)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        p.error("Versao semantica X.Y.Z obrigatoria")
    with MANIFEST.open(encoding="utf-8") as f:
        manifest = json.load(f)
    if manifest.get("schema") != 1:
        raise SystemExit("Esquema inesperado do updates.json")
    entry = manifest["products"]["aprs"]
    if entry.get("developmentVersion") != args.version:
        raise SystemExit("Versao nao corresponde ao codigo em desenvolvimento")
    base = FILES.resolve()
    published = []
    for category, key, arch, platform, name in candidates(args.version):
        path = FILES / name
        if not path.is_file():
            continue
        if path.is_symlink() or path.resolve().parent != base:
            raise SystemExit("Caminho fora do diretório oficial: " + name)
        size = path.stat().st_size
        if size <= 0:
            raise SystemExit("Arquivo vazio: " + name)
        with path.open("rb") as handle:
            header = handle.read(4)
            if name.endswith(".exe") and not header.startswith(b"MZ"):
                raise SystemExit("Executavel Windows invalido: " + name)
            if name.endswith(".AppImage") and header != b"\x7fELF":
                raise SystemExit("AppImage invalido: " + name)
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        published.append({
            "category": category, "counterKey": key, "architecture": arch,
            "platform": platform, "name": name,
            "url": SITE + "/downloads/aprs-client/" + name,
            "size": size, "sha256": digest,
            "detail": "PT2VHF APRS Client " + arch,
        })
    if not published:
        raise SystemExit("Nenhum arquivo instalador validado: nao publicar versao")
    entry["version"] = args.version
    entry["date"] = date.today().isoformat()
    entry["notes"] = "Atualizador migrado para o site PT2VHF; arquivos verificados por tamanho e SHA-256."
    entry["files"] = published
    entry["releaseStatus"] = "Pacotes homologados hospedados no site PT2VHF."
    manifest["updated"] = date.today().isoformat()
    if not args.apply:
        print(json.dumps({"preview": published}, ensure_ascii=False, indent=2))
        print("Dry-run: execute novamente com --apply apos conferir os arquivos na hospedagem.")
        return
    staging = MANIFEST.with_suffix(".json.tmp")
    try:
        with staging.open("w", encoding="utf-8") as out:
            json.dump(manifest, out, ensure_ascii=False, indent=2)
            out.write("\n")
        os.replace(staging, MANIFEST)
    finally:
        staging.unlink(missing_ok=True)
    print(f"Atualizada versao {args.version} com {len(published)} pacotes reais.")

if __name__ == "__main__":
    main()
