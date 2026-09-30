from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    require(read("VERSION").strip() == "1.7.21", "VERSION must be 1.7.21")
    require('__version__ = "1.7.21"' in read("pt2vhf_aprs/__init__.py"), "Python version mismatch")

    html = read("pt2vhf_aprs/templates/index.html")
    js = read("pt2vhf_aprs/static/js/app.js")
    css = read("pt2vhf_aprs/static/css/app.css")
    database = read("pt2vhf_aprs/database.py")
    updater = read("pt2vhf_aprs/updater.py")
    web = read("pt2vhf_aprs/web.py")
    notes = read("pt2vhf_aprs/version_notes.py")

    require('id="mapHoverInfoPanel"' in html, "Map hover panel missing")
    require("pt2vhfInteractionPane" in js, "Interactive map pane missing")
    require("trackHoverSummary" in js, "Tracklog hover summary missing")
    require("showTopologyHover" in js, "Topology hover details missing")
    require("pt2vhf-interaction-pane" in css, "Interactive pane CSS missing")

    for column in ("path TEXT", "raw TEXT", "rssi REAL", "snr REAL"):
        require(column in database, f"Track metadata column missing: {column}")
    require('packet.get("rssi")' in database and 'packet.get("snr")' in database, "RF metadata persistence missing")

    require("cleanup_obsolete_downloads" in updater, "Updater cleanup missing")
    require("target.unlink(missing_ok=True)" in updater, "Updater overwrite semantics missing")
    require("cleanup_obsolete_downloads(__version__)" in web, "Startup cleanup hook missing")
    require('"1.7.21"' in notes, "Version notes missing")

    print("v1.7.21 production validation OK")


if __name__ == "__main__":
    main()
