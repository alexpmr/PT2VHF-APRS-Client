from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def wait_port(host: str, port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("Servidor local não iniciou a tempo.")


def seed(data_dir: Path) -> None:
    os.environ["PT2VHF_DATA_DIR"] = str(data_dir)
    from pt2vhf_aprs import database as db
    db.DB_PATH = data_dir / "pt2vhf_aprs.db"
    db.init_db()
    db.save_config({
        "callsign": "PT2VHF", "ssid": 15, "latitude": -15.7939, "longitude": -47.8828,
        "altitude": 1100, "comment": "PT2VHF APRS Client - demonstração do manual",
        "aprs_filter": db.BRAZIL_FILTER, "app_theme": "dark", "connect_on_start": False,
    })
    for idx, (call, lat, lon, info) in enumerate([
        ("PY2ABC-9", -15.81, -47.91, "Móvel em Brasília"),
        ("PT2XYZ-7", -15.72, -47.88, "Estação fixa"),
        ("PY1TEST-10", -15.86, -47.80, "Demonstração APRS"),
    ]):
        db.upsert_station({
            "from": call, "format": "uncompressed", "latitude": lat, "longitude": lon,
            "speed": 18.0 + idx*7, "course": 80 + idx*40, "altitude": 1050 + idx*40,
            "symbol_table": "/", "symbol": ">", "comment": info,
            "path": ["WIDE1-1", "WIDE2-1"], "raw": f"{call}>APRS,WIDE1-1,WIDE2-1:!demo",
        })
    db.add_message("in", "PY2ABC-9", "PT2VHF-15", "Bom dia! Teste de mensagem APRS.", msg_id="101", status="Recebida")
    db.add_message("out", "PT2VHF-15", "PY2ABC-9", "Recebido. Aplicação funcionando.", msg_id="102", status="ACK")
    db.add_aprs_log("RX", "# aprsc 2.1.12-g123 24 Sep 2026 14:00:00 GMT")
    db.add_aprs_log("RX", "# logresp PT2VHF-15 verified, server BRAZIL")
    db.add_aprs_log("RX", "PY2ABC-9>APRS,WIDE1-1,WIDE2-1:!1548.60S/04754.60W>Demo")
    db.add_aprs_log("TX", "PT2VHF-15>APRS,TCPIP*::PY2ABC-9:Recebido{102")


def capture(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pt2vhf-manual-") as td:
        data_dir = Path(td)
        seed(data_dir)
        env = os.environ.copy()
        env["PT2VHF_DATA_DIR"] = str(data_dir)
        env["PT2VHF_PORT"] = "8765"
        proc = subprocess.Popen(
            [sys.executable, str(ROOT / "app.py")],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        try:
            wait_port("127.0.0.1", 8765)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
                page.goto("http://127.0.0.1:8765", wait_until="networkidle")
                page.wait_for_timeout(1800)
                page.screenshot(path=str(output_dir / "map.png"))
                for tab, filename in [("messages","messages.png"),("stations","stations.png"),("log","log.png")]:
                    page.evaluate("""(name) => document.querySelector('.tab[data-tab="' + name + '"]').click()""", tab)
                    page.wait_for_timeout(650)
                    page.screenshot(path=str(output_dir / filename))
                page.evaluate("""() => document.querySelector('.tab[data-tab="analysis"]').click()""")
                page.wait_for_timeout(650)
                page.screenshot(path=str(output_dir / "analysis.png"))
                page.evaluate("""() => document.querySelector('.tab[data-tab="config"]').click()""")
                page.wait_for_timeout(700)
                # A v1.6 usa uma única página de Configuração, compartimentalizada por seções.
                page.screenshot(path=str(output_dir / "config-aprs.png"))
                page.locator("#toggleFilterBuilderButton").scroll_into_view_if_needed()
                page.evaluate("() => document.querySelector('#toggleFilterBuilderButton').click()")
                page.wait_for_timeout(350)
                page.screenshot(path=str(output_dir / "filter-editor.png"))
                page.locator("#appTheme").scroll_into_view_if_needed()
                page.wait_for_timeout(350)
                page.screenshot(path=str(output_dir / "config-app.png"))
                browser.close()
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    capture(Path(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
