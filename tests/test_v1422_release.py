from pathlib import Path

from pt2vhf_aprs import database as db
from pt2vhf_aprs import spacetime_topology as st

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_v1422_version_and_release_markers():
    assert read("VERSION").strip() == "1.14.22"
    assert '__version__ = "1.14.22"' in read("pt2vhf_aprs/__init__.py")

    overlay = read("pt2vhf_aprs/spacetime_topology.py")
    assert "Ranking de alcançabilidade RF, incluindo rotas multi-hop históricas" in overlay
    assert "legacy_current_fallback" in overlay
    assert '"multi_hop"' in overlay

    web = read("pt2vhf_aprs/web.py")
    assert "def _topology_diagnostic_payload(" in web
    assert '@app.get("/api/export/topology-json")' in web
    assert '"schema_version": "pt2vhf-topology-diagnostic-1"' in web

    html = read("pt2vhf_aprs/templates/index.html")
    assert 'id="jsonExportButton"' in html
    assert 'id="jsonExportModal"' in html

    app = read("pt2vhf_aprs/static/js/app.js")
    assert "async function exportTopologyJson()" in app
    assert "/api/export/topology-json?" in app
    assert "Gerando diagnóstico JSON" in app


def test_v1422_record_ranking_explores_multi_hop_paths(monkeypatch):
    graph = {
        "A": {"B": {"packet_count": 10}},
        "B": {"A": {"packet_count": 10}, "C": {"packet_count": 9}},
        "C": {"B": {"packet_count": 9}, "D": {"packet_count": 8}},
        "D": {"C": {"packet_count": 8}},
        "E": {"F": {"packet_count": 30}},
        "F": {"E": {"packet_count": 30}},
    }
    positions = {
        "A": (0.0, 0.0),
        "B": (0.0, 2.0),
        "C": (0.0, 5.0),
        "D": (0.0, 10.0),
        "E": (1.0, 0.0),
        "F": (1.0, 1.0),
    }

    def fake_route_graph(hours=0):
        return graph, positions

    def fake_payload(nodes, _graph, _positions, *, refine_inferred=True):
        for left, right in zip(nodes, nodes[1:]):
            if right not in graph.get(left, {}):
                return None
        direct = db.haversine_km(*positions[nodes[0]], *positions[nodes[-1]])
        return {
            "source": nodes[0],
            "target": nodes[-1],
            "nodes": list(nodes),
            "hops": len(nodes) - 1,
            "distance_km": direct,
            "direct_distance_km": direct,
            "observations": 10,
            "direct_edges": len(nodes) - 1,
            "inferred_edges": 0,
            "route_evidence_end": "2026-10-10T12:00:00+00:00",
            "edges": [],
        }

    monkeypatch.setattr(st, "_route_graph", fake_route_graph)
    monkeypatch.setattr(st, "_route_payload", fake_payload)

    records = st._route_records(hours=0, limit=10, max_hops=6, beam_width=100)
    assert records
    assert records[0]["nodes"] == ["A", "B", "C", "D"]
    assert records[0]["hops"] == 3
    assert records[0]["multi_hop"] is True
    assert any(int(record.get("hops") or 0) > 1 for record in records)


def test_v1422_icon_asset_and_windows_taskbar_identity():
    icon = ROOT / "pt2vhf_aprs" / "static" / "img" / "aprs_taskbar_icon.png"
    assert icon.exists()
    assert icon.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    make_icon = read("windows/make_icon.py")
    assert "aprs_taskbar_icon.png" in make_icon
    assert "(256, 256)" in make_icon

    windows_app = read("windows_app.py")
    assert 'APP_USER_MODEL_ID = "PT2VHF.APRS.Client"' in windows_app
    assert "SetCurrentProcessExplicitAppUserModelID" in windows_app


def test_v1422_json_export_does_not_export_secrets_by_design():
    web = read("pt2vhf_aprs/web.py")
    assert '"config_safe": safe_config' in web
    assert '"passcode"' not in web[web.index("safe_config = {"):web.index("try:", web.index("safe_config = {"))]
    assert "DIAGNOSTIC_EXPORT_MAX_EVENTS" in web
    assert "DIAGNOSTIC_EXPORT_MAX_TRACKS" in web
    assert '"truncated": {' in web


def test_v1422_native_save_supports_json():
    for rel in ("windows_app.py", "linux_app.py", "macos_app.py"):
        source = read(rel)
        assert 'suffix == ".json"' in source
        assert '"JSON (*.json)"' in source
