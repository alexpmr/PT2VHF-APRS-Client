"""v1.14.54: teste de escuta do TNC e monitor de bytes ao vivo."""
import socket
import threading

from pt2vhf_aprs import database as db, tnc_listen, tnc_service as tnc


def _frame():
    return tnc.kiss_encode(tnc.tnc2_to_ax25("PT2ABC-9>APRS,WIDE1-1:!1545.00S/04752.80W>teste"))


def _serve_once(payload: bytes):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)

    def run():
        conn, _ = srv.accept()
        conn.sendall(payload)
        threading.Event().wait(0.5)
        conn.close()
        srv.close()

    threading.Thread(target=run, daemon=True).start()
    return srv.getsockname()[1]


def _config_tcp(tmp_path, monkeypatch, port):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "tnc.db")
    db.init_db()
    cfg = tnc.get_tnc_config()
    cfg.update({"transport": "tcp", "tcp_host": "127.0.0.1", "tcp_port": port})
    tnc.save_tnc_config(cfg)


def test_standalone_listen_decodes_valid_packets(tmp_path, monkeypatch):
    _config_tcp(tmp_path, monkeypatch, _serve_once(_frame() * 2))
    r = tnc_listen.listen_test(3, service=tnc.TNCService())
    assert r["mode"] == "standalone" and r["verdict"] == "ok" and r["ok"]
    assert r["valid_packets"] == 2
    assert r["packets"][0].startswith("PT2ABC-9>APRS")


def test_standalone_listen_reports_text_and_silence(tmp_path, monkeypatch):
    _config_tcp(tmp_path, monkeypatch, _serve_once(b"cmd:\r\nMYCALL PT2ABC\r\n"))
    assert tnc_listen.listen_test(3, service=tnc.TNCService())["verdict"] == "text_not_kiss"
    _config_tcp(tmp_path, monkeypatch, _serve_once(b""))
    r = tnc_listen.listen_test(3, service=tnc.TNCService())
    assert r["verdict"] == "no_bytes" and any("145.570" in h for h in r["hints"])


def test_diagnose_garbage_suggests_other_baud_rates():
    verdict, hints = tnc_listen.diagnose(bytes_rx=50, kiss_frames=0, valid=0, invalid=0, printable=0.2,
                                         protocol="kiss", seconds=10, serial_baud=9600, transport="serial")
    assert verdict == "garbage_not_kiss" and "115200" in hints[1] and "9600," not in hints[1]


def test_connection_error_is_explained(tmp_path, monkeypatch):
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); port = srv.getsockname()[1]; srv.close()
    _config_tcp(tmp_path, monkeypatch, port)
    r = tnc_listen.listen_test(3, service=tnc.TNCService())
    assert r["verdict"] == "error" and r["error"]


def test_rx_monitor_logs_bytes_and_frames(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "mon.db")
    db.init_db()
    svc = tnc.TNCService()
    raw = _frame()
    svc._log_rx("bytes", raw)
    payload = tnc.KissStreamDecoder().feed(raw)[0][1]
    svc._handle_rf_frame(payload)
    svc._handle_rf_frame(b"\x00" * 3)
    data = svc.rx_monitor(0)
    kinds = [e["kind"] for e in data["entries"]]
    assert kinds == ["bytes", "ax25", "invalid"]
    assert data["entries"][1]["text"].startswith("PT2ABC-9>APRS")
    assert svc.rx_monitor(data["seq"])["entries"] == []


def test_session_mode_uses_monitor_without_reopening(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "ses.db")
    db.init_db()
    svc = tnc.TNCService()
    svc._set_status(connected=True, endpoint="COM10 @ 9600")
    raw = _frame()

    def fake_sleep(_):
        svc._log_rx("bytes", raw)
        svc._log_rx("ax25", raw, "PT2ABC-9>APRS:x")

    r = tnc_listen.listen_test(5, service=svc, sleep=fake_sleep)
    assert r["mode"] == "session" and r["verdict"] == "ok" and r["bytes_rx"] == len(raw)
