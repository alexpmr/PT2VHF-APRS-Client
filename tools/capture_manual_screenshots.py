from __future__ import annotations

import argparse
import json
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
    # Caminho Internet/APRS-IS confirmado, independente de evidência RF.
    # PY1TEST-10 tem indicativo-base de 7 caracteres e é rejeitado pelo parser.
    # O teste usa PY2ABC-9 (válido) para verificar de fato o enlace qAr.
    db.record_topology_from_raw(
        "PY2ABC-9>APRS,TCPIP*,qAr,PT2XYZ-7:>enlace internet",
        medium="APRS-IS",
    )
    db.add_message("in", "PY2ABC-9", "PT2VHF-15", "Bom dia! Teste de mensagem APRS.", msg_id="101", status="Recebida")
    db.add_message("out", "PT2VHF-15", "PY2ABC-9", "Recebido. Aplicação funcionando.", msg_id="102", status="ACK")
    db.add_aprs_log("RX", "# aprsc 2.1.12-g123 24 Sep 2026 14:00:00 GMT")
    db.add_aprs_log("RX", "# logresp PT2VHF-15 verified, server BRAZIL")
    db.add_aprs_log("RX", "PY2ABC-9>APRS,WIDE1-1,WIDE2-1:!1548.60S/04754.60W>Demo")
    db.add_aprs_log("TX", "PT2VHF-15>APRS,TCPIP*::PY2ABC-9:Recebido{102")


def wait_runtime_url(data_dir: Path, timeout: float = 15.0) -> str:
    runtime_file = data_dir / "local_server.json"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            payload = json.loads(runtime_file.read_text(encoding="utf-8"))
            host = str(payload.get("host") or "127.0.0.1")
            port = int(payload.get("port") or 0)
            if port > 0:
                wait_port(host, port, timeout=2.0)
                return f"http://{host}:{port}"
        except Exception:
            pass
        time.sleep(0.1)
    raise RuntimeError("A interface local do cliente não publicou a porta selecionada.")


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
            local_url = wait_runtime_url(data_dir)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
                page.goto(local_url, wait_until="networkidle")
                page.wait_for_timeout(1800)
                # Em release nova, o popup legítimo "Novidades" cobre as abas.
                # Confirmá-lo antes dos testes reais de clique (em vez de usar
                # clicks forçados que ignorariam a interação do usuário).
                if page.locator("#whatsNewModal").is_visible():
                    page.locator("#whatsNewClose").click()
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

                # Regressão do PU2MUS: salvar alertas deve funcionar sem
                # querySelector(...).forEach em um único elemento.
                page.locator("#v190AlertsSave").scroll_into_view_if_needed()
                page.locator("#v190AlertsSave").click()
                page.wait_for_function(
                    "() => document.querySelector('#toast')?.textContent?.includes('Alertas salvos')",
                    timeout=10000,
                )

                # Regressão funcional real: fechar modal com salvar/descartar/
                # cancelar, sem depender só de testes que buscam strings no JS.
                page.locator('input[name="comment"]').fill("Beacon 1.14.4 salvo no modal")
                page.locator('.tab[data-tab="stations"]').click()
                page.locator("#unsavedConfigModal").wait_for(state="visible")
                page.locator("#unsavedSaveButton").click()
                page.wait_for_function(
                    "() => document.querySelector('.tab[data-tab=stations]')?.classList.contains('active') && document.querySelector('#unsavedConfigModal')?.classList.contains('hidden')",
                    timeout=15000,
                )
                cfg = page.request.get(f"{local_url}/api/config").json()
                assert cfg["comment"] == "Beacon 1.14.4 salvo no modal", "Modal Salvar e sair não persistiu"

                page.locator('.tab[data-tab="config"]').click()
                # A abertura da aba dispara GET /api/config assíncrono.
                # Esperar a recarga antes de editar evita corrida do próprio
                # cenário de teste com o preenchimento efetuado pela API.
                page.wait_for_timeout(900)
                page.locator('input[name="comment"]').fill("Alteração para cancelar")
                page.locator('.tab[data-tab="stations"]').click()
                page.locator("#unsavedConfigModal").wait_for(state="visible")
                page.locator("#unsavedCancelButton").click()
                assert page.locator('.tab[data-tab="config"]').get_attribute("class").find("active") >= 0
                assert page.locator('input[name="comment"]').input_value() == "Alteração para cancelar"

                page.locator('.tab[data-tab="stations"]').click()
                page.locator("#unsavedConfigModal").wait_for(state="visible")
                page.locator("#unsavedDiscardButton").click()
                page.wait_for_function(
                    "() => document.querySelector('.tab[data-tab=stations]')?.classList.contains('active') && document.querySelector('#unsavedConfigModal')?.classList.contains('hidden')",
                    timeout=15000,
                )
                cfg = page.request.get(f"{local_url}/api/config").json()
                assert cfg["comment"] == "Beacon 1.14.4 salvo no modal", "Descartar alterou config persistida"

                page.locator('#stationsTable tbody .station-row[data-callsign="PY2ABC-9"]').click(button="right")
                page.locator("#stationQuickMessagePanel").wait_for(state="visible", timeout=10000)
                assert page.locator("#stationQuickMessageCall").inner_text() == "PY2ABC-9"

                # A evidência de Internet deve existir na API e na visualização,
                # sem ficar bloqueada quando categorias de marcadores forem ocultadas.
                assert any(
                    e["kind"] == "igate"
                    for e in page.request.get(f"{local_url}/api/topology?hours=0").json()
                ), "API não forneceu enlace Internet do cenário de teste"
                assert page.request.get(f"{local_url}/api/topology?hours=0.25").ok
                page.locator('.tab[data-tab="map"]').click()
                page.wait_for_timeout(500)
                page.evaluate("""() => {
                    const toggle = document.querySelector('#mapViewTree input[data-map-state-key="stationsEnabled"]');
                    if (!toggle) throw new Error('Filtro Estações ausente');
                    toggle.checked = false;
                    toggle.dispatchEvent(new Event('change', { bubbles: true }));
                }""")
                # O mapa principal usa Leaflet preferCanvas=true; SVG path
                # não é criado para polylines em Canvas. Inspecionamos a
                # camada real do Leaflet e o seu vínculo com a evidência APRS.
                page.wait_for_function(
                    """() => {
                        const map = window.pt2vhfMainMap;
                        if (!map || !window.L) return false;
                        let visible = false;
                        map.eachLayer(layer => {
                            if (layer?._pt2vhfEdge?.kind === 'igate'
                                && String(layer.options?.dashArray || '').includes('7')
                                && map.hasLayer(layer)) {
                                visible = true;
                            }
                        });
                        return visible;
                    }""",
                    timeout=12000,
                )
                page.set_viewport_size({"width": 1280, "height": 720})
                page.locator('.tab[data-tab="satellites"]').click()
                page.wait_for_timeout(900)
                sat_layout = page.evaluate("""() => {
                    const tab=document.querySelector('#tab-satellites');
                    const workspace=document.querySelector('.satellite-workspace');
                    const sidebar=document.querySelector('.satellite-sidebar');
                    const map=document.querySelector('#satelliteMap');
                    const sb=sidebar?.getBoundingClientRect();
                    const mp=map?.getBoundingClientRect();
                    return {
                        overflow: tab ? tab.scrollWidth > tab.clientWidth + 2 : true,
                        sidebarWidth: sb?.width || 0,
                        mapWidth: mp?.width || 0,
                        columns: workspace ? getComputedStyle(workspace).gridTemplateColumns : ''
                    };
                }""")
                assert not sat_layout["overflow"], f"SAT com overflow horizontal: {sat_layout}"
                assert sat_layout["sidebarWidth"] >= 300, f"Sidebar SAT ilegível: {sat_layout}"
                assert sat_layout["mapWidth"] >= 300, f"Mapa SAT colapsado: {sat_layout}"
                page.set_viewport_size({"width": 1440, "height": 900})
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
