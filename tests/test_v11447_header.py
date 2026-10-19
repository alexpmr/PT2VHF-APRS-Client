"""v1.14.47: regressions for title typography and Web address label."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def content(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_header_version_matches_heading_font_without_changing_about():
    html = content("pt2vhf_aprs/templates/index.html")
    css = content("pt2vhf_aprs/static/css/app.css")
    assert re.search(r'<h1>PT2VHF APRS Client\s*<span class="app-version">v{{ app_version }}</span></h1>', html)
    assert ".brand h1 .app-version" in css
    rule = re.search(r"\.brand h1 \.app-version\s*\{([^}]*)\}", css)
    assert rule
    for part in ("font-family: inherit", "font-size: inherit", "font-weight: inherit"):
        assert part in rule.group(1)
    assert '<h3>PT2VHF APRS Client <span class="app-version">' in html
    assert "@media (max-width: 760px)" in css


def test_web_header_has_only_address_even_when_remote_active():
    html = content("pt2vhf_aprs/templates/index.html")
    js = content("pt2vhf_aprs/static/js/app.js")
    css = content("pt2vhf_aprs/static/css/app.css")
    header = html[html.index('<header class="app-header">'):html.index("</header>")]
    assert 'id="webAccessStatus"' in header
    assert 'id="webAccessUrl"' in header
    assert 'id="webAccessLabel"' not in header
    assert not any(x in header for x in ("Web em uso:", "Web LAN:", "Web local:"))
    updater = js[js.index("function updateWebAccessStatus("):js.index("const retentionCategories", js.index("function updateWebAccessStatus("))]
    assert "webAccessLabel" not in updater
    assert "if (label) label.textContent" not in updater
    assert "value.textContent = compact" in updater
    assert "header.classList.toggle('remote-active', remoteActive)" in updater
    assert ".web-access-status.remote-active" in css
