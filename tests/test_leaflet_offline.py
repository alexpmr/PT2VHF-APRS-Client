import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "pt2vhf_aprs" / "static" / "vendor" / "leaflet"


def test_leaflet_is_served_locally_without_cdn():
    html = (ROOT / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    assert "unpkg.com" not in html
    assert "filename='vendor/leaflet/leaflet.js'" in html


def test_leaflet_vendor_matches_pinned_integrity_and_assets():
    html = (ROOT / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    digest = base64.b64encode(hashlib.sha256((VENDOR / "leaflet.js").read_bytes()).digest()).decode()
    assert f'integrity="sha256-{digest}"' in html
    for name in ("layers.png", "layers-2x.png", "marker-icon.png", "marker-icon-2x.png", "marker-shadow.png"):
        assert (VENDOR / "images" / name).is_file()
