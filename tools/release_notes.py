from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def current_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def changelog_section(version: str) -> str:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^## v{re.escape(version)}\b[^\n]*\n(?P<body>.*?)(?=^## v|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return "- Consulte o CHANGELOG.md para os detalhes desta versão."
    return match.group("body").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="release-notes.md")
    args = parser.parse_args()

    version = current_version()
    changes = changelog_section(version)
    output = f"""## PT2VHF APRS Client v{version}

### Novidades e alterações

{changes}

## Downloads

### Windows
- `PT2VHF_APRS_Client_Setup_x64_v{version}.exe` - instalador recomendado.
- `PT2VHF_APRS_Client_Portable_x64_v{version}.exe` - executável portátil.

### Linux
- `PT2VHF_APRS_Client_x86_64_v{version}.AppImage` - AppImage portátil.
- `PT2VHF_APRS_Client_Linux_x86_64_v{version}.tar.gz` - pacote portátil.
- `pt2vhf-aprs-client_{version}_amd64.deb` - Debian/Ubuntu e derivados.

### macOS
- `PT2VHF_APRS_Client_macOS_arm64_v{version}.dmg` - Apple Silicon.
- `PT2VHF_APRS_Client_macOS_x86_64_v{version}.dmg` - Macs Intel.

### Documentação
- `PT2VHF_APRS_Client_Manual_v{version}.pdf` - manual completo gerado a partir da versão e do changelog.

## Assinatura de código

Os builds podem permanecer sem assinatura/notarização de plataforma enquanto o projeto conclui os respectivos processos de assinatura. Use somente os arquivos publicados na Release oficial.

- Windows: consulte `CODE_SIGNING_POLICY.md`.
- macOS: consulte `docs/INSTALL_MACOS.md` para o procedimento seguro de primeira abertura.
"""
    (ROOT / args.output).write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
