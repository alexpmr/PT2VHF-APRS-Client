from __future__ import annotations

from pathlib import Path

from pt2vhf_aprs import database as db

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def edge(
    *,
    direct: int = 0,
    inferred: int = 0,
    packets: int = 1,
    distance: float = 10.0,
    last_seen: str = "2026-10-08T23:27:51+00:00",
):
    return {
        "packet_count": packets,
        "rf_transport_count": direct,
        "rf_path_count": inferred,
        "distance_km": distance,
        "first_seen": "2026-10-08T22:00:00+00:00",
        "last_seen": last_seen,
        "classification_source": "RF direto do transporte" if direct else "RF inferido do path",
    }


def connect(graph, a: str, b: str, payload):
    graph.setdefault(a, {})[b] = payload
    graph.setdefault(b, {})[a] = payload


def test_v1417_release_history_is_preserved():
    assert "## 1.14.17 - 2026-10-09" in read("CHANGELOG.md")
    assert '"1.14.17": {' in read("pt2vhf_aprs/version_notes.py")
    assert "## Implementado na v1.14.17" in read("BACKLOG.md")


def test_v1417_long_inferred_edge_is_reconstructed_when_supported():
    graph = {}
    positions = {
        "A": (0.0, 0.0),
        "B": (0.0, 2.0),
        "C": (0.0, 4.0),
        "D": (0.0, 7.0),
    }
    connect(graph, "A", "D", edge(inferred=4, packets=4, distance=780.0))
    connect(graph, "A", "B", edge(direct=3, packets=3, distance=220.0))
    connect(graph, "B", "C", edge(direct=4, packets=4, distance=220.0))
    connect(graph, "C", "D", edge(direct=5, packets=5, distance=330.0))

    payload = db._rf_route_payload(["A", "D"], graph, positions)

    assert payload is not None
    assert payload["nodes"] == ["A", "B", "C", "D"]
    assert payload["original_nodes"] == ["A", "D"]
    assert payload["refinement_applied"] is True
    assert payload["reconstructed_intermediate_nodes"] == ["B", "C"]
    assert payload["unresolved_inferred_edges"] == []
    assert payload["direct_edges"] == 3
    assert all(item["reconstructed"] for item in payload["edges"])


def test_v1417_long_inferred_edge_stays_inferred_when_no_supported_chain():
    graph = {}
    positions = {"A": (0.0, 0.0), "D": (0.0, 7.0)}
    connect(graph, "A", "D", edge(inferred=5, packets=5, distance=780.0))

    payload = db._rf_route_payload(["A", "D"], graph, positions)

    current = tuple(int(part) for part in read("VERSION").strip().split("."))
    if current >= (1, 14, 20):
        assert payload is None
    else:
        assert payload is not None
        assert payload["nodes"] == ["A", "D"]
        assert payload["refinement_applied"] is False
        assert len(payload["unresolved_inferred_edges"]) == 1
        assert payload["unresolved_inferred_edges"][0]["source"] == "A"
        assert payload["unresolved_inferred_edges"][0]["target"] == "D"


def test_v1417_long_direct_rf_edge_is_never_broken_only_by_distance():
    graph = {}
    positions = {"A": (0.0, 0.0), "D": (0.0, 8.0)}
    connect(graph, "A", "D", edge(direct=1, packets=1, distance=890.0))

    payload = db._rf_route_payload(["A", "D"], graph, positions)

    assert payload is not None
    assert payload["nodes"] == ["A", "D"]
    assert payload["refinement_applied"] is False
    assert payload["unresolved_inferred_edges"] == []
    assert payload["direct_edges"] == 1


def test_v1417_refinement_prefers_direct_chain_over_inferred_chain():
    graph = {}
    positions = {
        "A": (0.0, 0.0),
        "B": (0.0, 2.0),
        "C": (1.0, 2.0),
        "D": (0.0, 7.0),
    }
    connect(graph, "A", "D", edge(inferred=10, packets=10, distance=780.0))
    connect(graph, "A", "B", edge(direct=2, packets=2, distance=300.0))
    connect(graph, "B", "D", edge(direct=2, packets=2, distance=480.0))
    connect(graph, "A", "C", edge(inferred=20, packets=20, distance=300.0))
    connect(graph, "C", "D", edge(inferred=20, packets=20, distance=480.0))

    result = db._rf_refine_inferred_edge("A", "D", graph, positions)

    assert result is not None
    assert result["nodes"] == ["A", "B", "D"]
    assert result["direct_edges"] == 2


def test_v1417_refinement_respects_temporal_proximity():
    graph = {}
    positions = {"A": (0.0, 0.0), "B": (0.0, 3.0), "D": (0.0, 7.0)}
    connect(graph, "A", "D", edge(inferred=4, packets=4, distance=780.0))
    old = "2026-10-05T00:00:00+00:00"
    connect(graph, "A", "B", edge(direct=4, packets=4, distance=330.0, last_seen=old))
    connect(graph, "B", "D", edge(direct=4, packets=4, distance=450.0, last_seen=old))

    payload = db._rf_route_payload(["A", "D"], graph, positions)

    current = tuple(int(part) for part in read("VERSION").strip().split("."))
    assert payload is not None
    if current >= (1, 14, 20):
        # v1.14.20 permite compor alcançabilidade histórica: o tempo classifica
        # a evidência, mas não elimina uma cadeia espacialmente coerente.
        assert payload["nodes"] == ["A", "B", "D"]
        assert payload["refinement_applied"] is True
    else:
        assert payload["nodes"] == ["A", "D"]
        assert payload["refinement_applied"] is False
        assert len(payload["unresolved_inferred_edges"]) == 1


def test_v1417_full_backup_button_uses_explicit_download_flow():
    js = read("pt2vhf_aprs/static/js/v190.js")
    html = read("pt2vhf_aprs/templates/index.html")
    assert 'id="v190BackupFull"' in js
    assert "async function createFullBackup()" in js
    assert "save_local_download('/api/v190/backup/full', suggested)" in js
    assert "response.blob()" in js
    assert "triggerBlobDownload(blob, filename)" in js
    assert 'id="globalProcessingOverlay"' in html


def test_v1417_processing_overlay_is_reusable_and_used_by_long_operations():
    js = read("pt2vhf_aprs/static/js/app.js")
    v190 = read("pt2vhf_aprs/static/js/v190.js")
    css = read("pt2vhf_aprs/static/css/app.css")
    assert "function showProcessing(" in js
    assert "function updateProcessing(" in js
    assert "function hideProcessing(" in js
    assert "async function withProcessing(" in js
    assert "window.pt2vhfWithProcessing = withProcessing;" in js
    assert "const processingToken = showProcessing(" in js
    assert "withProcessing(" in v190
    assert ".global-processing-overlay" in css
    assert "@keyframes pt2vhf-processing-clock" in css


def test_v1417_native_backup_bridge_exists_on_all_desktop_launchers():
    for path in ("windows_app.py", "linux_app.py", "macos_app.py"):
        content = read(path)
        assert "def save_local_download(" in content
        assert 'allowed = {"/api/v190/backup/full"}' in content
        assert "with urlopen(local_url, timeout=180)" in content


def test_v1417_backup_endpoint_reports_errors_explicitly():
    backend = read("pt2vhf_aprs/v190_features.py")
    assert 'response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"' in backend
    assert '"X-PT2VHF-Backup-Version"' in backend
    assert 'return jsonify({"ok": False, "error": f"Falha ao gerar backup completo: {exc}"}), 500' in backend


def test_v1417_configuration_uses_single_vertical_scroll():
    css = read("pt2vhf_aprs/static/css/app.css")
    assert "v1.14.17 - Configuração usa somente a rolagem principal da aba" in css
    assert "#tab-config #configForm.config-grid" in css
    assert "overflow-y: auto;" in css
    assert "#tab-config #configForm .config-card :is(div, section, article, fieldset, ul, ol)" in css
    assert "max-height: none !important;" in css
    assert "overflow: visible !important;" in css
