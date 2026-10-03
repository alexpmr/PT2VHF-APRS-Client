from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1814_version_metadata():
    assert read("VERSION").strip() == "1.8.14"
    assert '__version__ = "1.8.14"' in read("pt2vhf_aprs/__init__.py")
    win = read("windows/version_info.txt")
    assert "filevers=(1, 8, 14, 0)" in win
    assert "prodvers=(1, 8, 14, 0)" in win
    assert "FileVersion', '1.8.14'" in win
    assert "ProductVersion', '1.8.14'" in win


def test_v1814_about_explicitly_explains_aprs_in_all_languages():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")

    assert 'id="aboutAprsTitle"' in html
    assert 'id="aboutAprsText"' in html
    assert "aprsTitle: 'O que é APRS?'" in js
    assert "aprsTitle: 'What is APRS?'" in js
    assert "aprsTitle: '¿Qué es APRS?'" in js
    assert "aprsTitle: 'Qu’est-ce que l’APRS ?'" in js
    assert "Automatic Packet Reporting System" in js
    assert "posição, mensagens, telemetria, dados meteorológicos" in js
    assert "both over radio (RF) and through the APRS-IS network" in js
    assert "tanto por radio (RF) como a través de la red APRS-IS" in js
    assert "par radio (RF) comme via le réseau APRS-IS" in js
    assert "$('#aboutAprsTitle').textContent = copy.aprsTitle" in js
    assert "$('#aboutAprsText').textContent = copy.aprs" in js


def test_v1814_elevation_uses_dem_derived_hillshade():
    js = read("pt2vhf_aprs/static/js/app.js")
    html = read("pt2vhf_aprs/templates/index.html")
    db = read("pt2vhf_aprs/database.py")

    assert 'id="elevationToggle"' in html
    assert "Relevo com corte" in html
    assert "function elevationGridFromTerrarium(canvas)" in js
    assert "new Float32Array(256 * 256)" in js
    assert "function elevationHillshadeFactor(grid, x, y)" in js
    assert "const dzdx = (right - left) * 0.5;" in js
    assert "const dzdy = (down - up) * 0.5;" in js
    assert "const illumination = nx * lx + ny * ly + nz * lz;" in js
    assert "const shade = elevationHillshadeFactor(grid, x, y);" in js
    assert "if (altitude < threshold) continue;" in js
    assert "Math.min(9000, Math.max(100" in js
    assert "|| 3000" in js
    assert "elevation_threshold" in db
    assert "elevation_slider_max" in db
    assert "elevation_opacity" in db


def test_v1814_all_requested_backlogs_remain_covered():
    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    css = read("pt2vhf_aprs/static/css/app.css")
    backlog = read("BACKLOG.md")

    assert '<option value="auto" selected>Automático</option>' in html
    assert '<option value="aprs_is">APRS-IS</option>' in html
    assert '<option value="rf_direct">RF direto</option>' in html
    assert '<option value="rf_custom">RF personalizado</option>' in html
    assert "@media (max-height: 800px) and (min-width: 901px)" in css
    assert "function stationInteractionProfile(s)" in js
    assert "${interactionDisabled}>Ping/ACK</button>" in js
    assert "${interactionDisabled}>Trace</button>" in js
    assert "${interactionDisabled}>Enviar mensagem</button>" in js
    assert ".elevation-vertical-range { height: 255px; }" in css
    assert "## Concluído na v1.8.14" in backlog
    assert "hillshade derivado do próprio DEM" in backlog
    assert "explicação explícita de APRS" in backlog


def test_v1814_preserves_legacy_sqlite_migration_guard():
    database = read("pt2vhf_aprs/database.py")
    schema_end = database.index("        # Migração v1.7.7:")
    schema_script = database[:schema_end]
    migration_start = database.index('packet_columns = {row["name"]')
    migration_end = database.index('config_columns = {row["name"]', migration_start)
    migration = database[migration_start:migration_end]

    assert "idx_packets_medium_time" not in schema_script
    assert "idx_packets_medium_call_time" not in schema_script
    assert "idx_packets_fingerprint_time" not in schema_script
    assert 'if "medium" not in packet_columns:' in migration
    assert 'ALTER TABLE packets ADD COLUMN medium' in migration
    assert 'if "rx_fingerprint" not in packet_columns:' in migration
    assert 'ALTER TABLE packets ADD COLUMN rx_fingerprint' in migration
