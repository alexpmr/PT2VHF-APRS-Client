from __future__ import annotations

from pathlib import Path

from pt2vhf_aprs import local_server


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v1429_local_bind_still_publishes_real_lan_ip(monkeypatch):
    monkeypatch.setattr(local_server, "detect_lan_ipv4", lambda: "192.168.10.2")
    handle = local_server.LocalServerHandle(
        server=object(),
        server_kind="test",
        host="127.0.0.1",
        port=8080,
        start_port=8080,
    )

    assert handle.local_host == "127.0.0.1"
    assert handle.lan_host == "192.168.10.2"
    assert handle.scope == "local"
    assert handle.url == "http://127.0.0.1:8080"
    assert handle.share_url == "http://127.0.0.1:8080"
    assert handle.display_url == "http://192.168.10.2:8080"

    local_server._set_runtime(handle)
    info = local_server.runtime_info()

    assert info["bind_host"] == "127.0.0.1"
    assert info["host"] == "127.0.0.1"
    assert info["lan_ip"] == "192.168.10.2"
    assert info["display_host"] == "192.168.10.2"
    assert info["display_url"] == "http://192.168.10.2:8080"
    assert info["share_url"] == "http://127.0.0.1:8080"
    assert info["scope"] == "local"


def test_v1429_lan_bind_publishes_shareable_real_lan_url(monkeypatch):
    monkeypatch.setattr(local_server, "detect_lan_ipv4", lambda: "192.168.10.2")
    handle = local_server.LocalServerHandle(
        server=object(),
        server_kind="test",
        host="0.0.0.0",
        port=8080,
        start_port=8080,
    )

    assert handle.lan_host == "192.168.10.2"
    assert handle.scope == "lan"
    assert handle.display_url == "http://192.168.10.2:8080"
    assert handle.share_url == "http://192.168.10.2:8080"


def test_v1429_frontend_uses_display_url_or_lan_ip_even_when_scope_local():
    js = read("pt2vhf_aprs/static/js/app.js")

    assert "localInfo.display_url || localInfo.share_url" in js
    assert "if (lanHost && localPort)" in js
    assert "if (scope === 'lan') shareUrl = lanCandidate;" in js
    assert "if (scope !== 'lan') shareUrl = localUrl;" in js
    # v1.14.47 (#99): o botão mostra apenas IP:porta, sem prefixo "Web:".
    assert "lanHost ? ui('Web:', 'Web:')" not in js
    assert "value.textContent = compact ||" in js


def test_v1429_release_metadata_and_backlog():
    assert tuple(map(int, read("VERSION").strip().split("."))) >= (1, 14, 29)
    assert "## 1.14.29 - 2026-10-11" in read("CHANGELOG.md")
    assert '"1.14.29": {' in read("pt2vhf_aprs/version_notes.py")
    assert not any(line.startswith("## Novo —") for line in read("BACKLOG.md").splitlines())
