from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.8.6":
    raise SystemExit(f"v1.8.6 validation failed: VERSION={version!r}")

checks = {
    "pt2vhf_aprs/__init__.py": ['__version__ = "1.8.6"'],
    "pt2vhf_aprs/static/js/app.js": [
        "function repairMapVisibilityStateV186()",
        "renderMapViewTree([], []);",
        "pt2vhf_map_view_all_cleared",
        "_pt2vhfMapViewportSyncBound",
        "state.map.invalidateSize({ animate: false });",
        "window.addEventListener('resize', syncViewport);",
        "window.addEventListener('orientationchange', syncViewport);",
        "if (tree && !tree.querySelector('.map-view-node')) renderMapViewTree([], []);",
        "root:stations",
        "root:digis",
        "root:igates",
        "root:objects",
        "root:tracklogs",
        "root:rf",
        "root:igate-links",
        "root:packets",
    ],
    "pt2vhf_aprs/templates/index.html": [
        'id="mapItemsButton"',
        'id="mapItemsMenu"',
        'id="mapViewTree"',
        'id="mapViewSelectAllButton"',
        'id="mapViewClearAllButton"',
    ],
    "pt2vhf_aprs/static/css/app.css": [
        "@media (max-height: 800px) and (min-width: 901px)",
        ".message-composer",
        ".station-popup",
        ".map-view-tree-menu",
    ],
    "tests/test_v186_map_items_recovery.py": [
        "test_v186_map_ver_controls_and_categories_are_present",
        "test_v186_map_tree_is_rendered_before_backend_data_arrives",
        "test_v186_recovers_only_unintentional_all_disabled_visibility",
        "test_v186_low_height_rules_do_not_change_global_map_geometry",
    ],
    "pt2vhf_aprs/version_notes.py": ['"1.8.6"'],
    "CHANGELOG.md": ["## 1.8.6 - 2026-10-02"],
    "README.md": ["# PT2VHF APRS Client - v1.8.6", "## Novidades da v1.8.6"],
}

for rel, needles in checks.items():
    text = (ROOT / rel).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"v1.8.6 validation failed: {needle!r} missing from {rel}")

css = (ROOT / "pt2vhf_aprs/static/css/app.css").read_text(encoding="utf-8")
start = css.index("@media (max-height: 800px) and (min-width: 901px)")
end = css.index(".required-fields-note", start)
low_height = css[start:end]
for forbidden in (".app-header {", ".tabs {", "body.map-context-visible main", "main { height:"):
    if forbidden in low_height:
        raise SystemExit(f"v1.8.6 validation failed: global map geometry still altered by low-height CSS: {forbidden}")

js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
add_controls = js[js.index("function addMapControls()"):js.index("function syncMapLegendCollapsed()")]
if add_controls.index("renderMapViewTree([], []);") > add_controls.index("const period = $('#mapPeriodHours');"):
    raise SystemExit("v1.8.6 validation failed: map tree is not rendered before control/data setup")

print("v1.8.6 map items recovery and viewport stability validation OK")
