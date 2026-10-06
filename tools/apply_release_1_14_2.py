from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

if read("VERSION").strip() != "1.14.2":
    raise SystemExit("VERSION must be 1.14.2")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.14.2"'],
    "windows/version_info.txt": [
        "filevers=(1, 14, 2, 0)",
        "prodvers=(1, 14, 2, 0)",
        "FileVersion', '1.14.2'",
        "ProductVersion', '1.14.2'",
    ],
    "pt2vhf_aprs/templates/index.html": [
        "css/v142.css",
        "js/v142.js",
    ],
    "pt2vhf_aprs/web.py": [
        "register_v142_routes",
        "register_v142_routes(app)",
    ],
    "pt2vhf_aprs/v142_features.py": [
        "def rf_coverage_points(",
        "UPPER(COALESCE(medium,''))='RF'",
        "source\": \"rf_quality",
        "source\": \"rf_density",
        "/api/v142/rf-coverage",
    ],
    "pt2vhf_aprs/static/js/v142.js": [
        "v142-rf-heatmap-canvas",
        "createRadialGradient",
        "this._map.getZoom()",
        "mapPeriodHours",
        "mapViewSelectAllButton",
        "mapViewClearAllButton",
        "/api/v142/rf-coverage",
        "/api/v110/ais-profile/",
        "Imagem ilustrativa do tipo",
    ],
    "pt2vhf_aprs/static/css/v142.css": [
        ".v142-rf-heatmap-canvas",
        ".v142-ais-enrichment",
        ".v142-ais-illustration",
    ],
    "pt2vhf_aprs/database.py": [
        '"vessel_name": vessel_name',
        '"vessel_callsign": vessel_callsign',
        '"nav_status": nav_status',
        '"draught_m": draught',
        '"speed_knots": sog_knots',
    ],
    "pt2vhf_aprs/static/js/app.js": [
        "function aisShipTypeLabel(value)",
        "function aisNavigationStatusLabel(value)",
        "Nome da embarcação",
        "Velocidade sobre o fundo",
        "Fonte dos dados",
    ],
    "tests/test_v142_release.py": [
        "test_v142_rf_coverage_uses_confirmed_rf_and_quality_then_density_fallback",
        "test_v142_ais_parser_extracts_extended_fields",
        "test_v142_ais_popup_and_async_enrichment_are_explicitly_labeled",
    ],
}
for rel, needles in checks.items():
    body = read(rel)
    for needle in needles:
        if needle not in body:
            raise SystemExit(f"v1.14.2 validation failed: {needle!r} missing from {rel}")

print("v1.14.2 validation OK")
