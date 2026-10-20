"""v1.14.49: erros JS e resumo do mapa vão para o diagnostics.log."""
from pt2vhf_aprs import diagnostics as diag
from pt2vhf_aprs.web import create_app


def test_client_event_endpoint_logs_and_validates(monkeypatch):
    events = []
    monkeypatch.setattr(diag, "log_event", lambda name, **kw: events.append((name, kw)))
    client = create_app().test_client()
    ok = client.post("/api/diagnostics/client-event", json={
        "kind": "map_render",
        "details": {"user_agent": "Edg/1" * 200, "topology_lines_drawn": 0, "canvas_2d": True},
    })
    assert ok.status_code == 200
    name, fields = events[-1]
    assert name == "client_map_render"
    assert len(fields["user_agent"]) == 400
    assert fields["topology_lines_drawn"] == 0 and fields["canvas_2d"] is True
    bad = client.post("/api/diagnostics/client-event", json={"kind": "anything"})
    assert bad.status_code == 400
