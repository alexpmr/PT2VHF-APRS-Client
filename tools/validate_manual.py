from __future__ import annotations

import sys
from pathlib import Path
from pypdf import PdfReader

REQUIRED = [
    "PT2VHF APRS Client",
    "Manual do Usuário",
    "Primeira configuração",
    "APRS-IS e filtros",
    "Mapa e topologia observada",
    "Mensagens",
    "Estações e Log",
    "Diagnóstico rápido",
    "Changelog",
]

def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Uso: validate_manual.py arquivo.pdf")
    path = Path(sys.argv[1])
    size = path.stat().st_size if path.exists() else 0
    if size < 120_000:
        raise SystemExit(f"Manual inválido ou pequeno demais: {size} bytes")
    reader = PdfReader(str(path))
    if len(reader.pages) < 12:
        raise SystemExit(f"Manual incompleto: apenas {len(reader.pages)} páginas")
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    missing = [item for item in REQUIRED if item not in text]
    if missing:
        raise SystemExit("Manual sem seções obrigatórias: " + ", ".join(missing))
    print(f"Manual validado: {len(reader.pages)} páginas, {size} bytes")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
