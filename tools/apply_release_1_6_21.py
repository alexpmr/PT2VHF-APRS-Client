from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

def version_tuple(value: str) -> tuple[int, ...]:
    parts = []
    for piece in str(value or "").strip().lstrip("vV").split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            break
    return tuple(parts or [0])

if version_tuple(version) < (1, 6, 21):
    raise SystemExit(f"v1.6.21 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": [
        '__version__ = "1.6.21"',
    ],
    "pt2vhf_aprs/database.py": [
        '"active_stations": active_stations',
        '"active_station_packets": eligible_packets',
        "NOT LIKE 'telemetry%'",
        "excluded_calls",
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "data.active_stations || []",
        "ui('Estações mais ativas', 'Most active stations')",
        "Carregando estatísticas",
        "Replay sincronizado com o período das Estatísticas.",
    ],
    "pt2vhf_aprs/templates/index.html": [
        '>Estatísticas</button>',
        '<h2>Estatísticas da rede</h2>',
        'Atualizar estatísticas',
    ],
    "tests/test_core.py": [
        "test_topology_stats_active_stations_excludes_telemetry_igates_and_digipeaters",
    ],
    "README.md": [
        "# PT2VHF APRS Client - v1.6.21",
        "estações mais ativas",
    ],
}
for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.6.21 validation failed: {needle!r} missing from {rel}")

print("v1.6.21 statistics/active-stations validation OK")
