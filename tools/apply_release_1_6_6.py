from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html_path = ROOT / "pt2vhf_aprs/templates/index.html"
js_path = ROOT / "pt2vhf_aprs/static/js/app.js"
css_path = ROOT / "pt2vhf_aprs/static/css/app.css"
db_path = ROOT / "pt2vhf_aprs/database.py"
web_path = ROOT / "pt2vhf_aprs/web.py"
tests_path = ROOT / "tests/test_core.py"
icon_path = ROOT / "windows/make_icon.py"

html = html_path.read_text(encoding="utf-8")

# Logo oficial fornecida pelo usuário.
html = html.replace(
    '<link rel="icon" type="image/svg+xml" href="{{ url_for(\'static\', filename=\'img/app_logo.svg\') }}">',
    '<link rel="icon" type="image/jpeg" href="{{ url_for(\'static\', filename=\'img/aprs_logo_official.jpg\') }}">'
)
html = html.replace(
    'src="{{ url_for(\'static\', filename=\'img/app_logo.svg\') }}"',
    'src="{{ url_for(\'static\', filename=\'img/aprs_logo_official.jpg\') }}"'
)

# Bandeiras reais ao lado do seletor, evitando o fallback "BR"/"US" do Windows.
old_lang = '''          <label class="field theme-field">
            <span>Idioma / Language</span>
            <select name="language" id="appLanguage">
              <option value="pt-BR">🇧🇷 Português - padrão</option>
              <option value="en">🇺🇸 English</option>
            </select>
            <small>O idioma é aplicado imediatamente à interface.</small>
          </label>'''
new_lang = '''          <label class="field theme-field">
            <span>Idioma / Language</span>
            <div class="language-select-wrap">
              <img id="languageFlag" class="language-flag" src="{{ url_for('static', filename='img/flag_br.svg') }}" alt="Brasil">
              <select name="language" id="appLanguage">
                <option value="pt-BR">Português - padrão</option>
                <option value="en">English</option>
              </select>
            </div>
            <small>O idioma é aplicado imediatamente à interface.</small>
          </label>'''
if old_lang in html:
    html = html.replace(old_lang, new_lang, 1)

# Botão Limpar tudo no bloco Manutenção.
if 'id="clearAllDataButton"' not in html:
    html = html.replace(
        '<button id="clearLogButton" type="button" class="btn danger">Limpar Log APRS-IS</button>',
        '<button id="clearLogButton" type="button" class="btn danger">Limpar Log APRS-IS</button>\n'
        '          <button id="clearAllDataButton" type="button" class="btn danger maintenance-clear-all">Limpar tudo…</button>',
        1
    )

# O botão do rodapé não pode depender da validação HTML nativa do submit.
html = html.replace(
    '<button id="saveConfigFooterButton" type="submit" class="btn primary">Salvar configuração</button>',
    '<button id="saveConfigFooterButton" type="button" class="btn primary">Salvar configuração</button>',
    1
)
html_path.write_text(html, encoding="utf-8")

# Banco: limpeza operacional completa, preservando configuração, favoritos e estado do mapa.
db = db_path.read_text(encoding="utf-8")
if "def clear_operational_data()" not in db:
    anchor = '''def clear_messages() -> int:
    with connection() as conn:
        cur = conn.execute("DELETE FROM messages")
        return max(0, int(cur.rowcount or 0))


'''
    func = '''def clear_operational_data() -> dict[str, int]:
    """Limpa dados operacionais mantendo configuração, favoritos e map_state."""
    tables = (
        "tracks",
        "stations",
        "messages",
        "aprs_log",
        "packets",
        "topology_edges",
        "topology_events",
    )
    deleted: dict[str, int] = {}
    with connection() as conn:
        for table in tables:
            cur = conn.execute(f"DELETE FROM {table}")
            deleted[table] = max(0, int(cur.rowcount or 0))
    return deleted


'''
    if anchor not in db:
        raise SystemExit("clear_messages anchor not found")
    db = db.replace(anchor, anchor + func, 1)
db_path.write_text(db, encoding="utf-8")

web = web_path.read_text(encoding="utf-8")
if '/api/maintenance/clear-all' not in web:
    anchor = '''    @app.post("/api/messages/clear")
    def api_clear_messages():
        deleted = db.clear_messages()
        return jsonify({"ok": True, "deleted": deleted})

'''
    route = '''    @app.post("/api/maintenance/clear-all")
    def api_clear_all_operational_data():
        try:
            deleted = db.clear_operational_data()
            return jsonify({"ok": True, "deleted": deleted})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400

'''
    if anchor not in web:
        raise SystemExit("messages clear route anchor not found")
    web = web.replace(anchor, anchor + route, 1)
web_path.write_text(web, encoding="utf-8")

js = js_path.read_text(encoding="utf-8")

# Bandeira acompanha o idioma selecionado.
lang_hook = "  function applyLanguage(language) {"
if "function syncLanguageFlag()" not in js:
    insert = '''  function syncLanguageFlag() {
    const flag = $('#languageFlag');
    const select = $('#appLanguage');
    if (!flag || !select) return;
    const english = select.value === 'en';
    flag.src = english ? '/static/img/flag_us.svg' : '/static/img/flag_br.svg';
    flag.alt = english ? 'United States' : 'Brasil';
  }

'''
    pos = js.find(lang_hook)
    if pos < 0:
        raise SystemExit("applyLanguage hook not found")
    js = js[:pos] + insert + js[pos:]

# Ao carregar e ao mudar idioma, sincronizar a bandeira.
js = js.replace(
    "      applyLanguage(state.language);\n",
    "      applyLanguage(state.language);\n      syncLanguageFlag();\n",
    1
)
if "$('#appLanguage')?.addEventListener('change'" in js and "syncLanguageFlag();" not in js[js.find("$('#appLanguage')?.addEventListener('change'"):js.find("$('#appLanguage')?.addEventListener('change'")+700]:
    start = js.find("$('#appLanguage')?.addEventListener('change'")
    end = js.find("});", start)
    if start >= 0 and end > start:
        block = js[start:end+3]
        if "syncLanguageFlag();" not in block:
            block = block.replace("{", "{\n    syncLanguageFlag();", 1)
            js = js[:start] + block + js[end+3:]

# Salvar: clique direto e proteção contra exceções anteriores ao bloco try original.
if "$('#saveConfigFooterButton')?.addEventListener('click'" not in js:
    hook = "  $('#configForm').addEventListener('submit', async e => {"
    handler = '''  $('#saveConfigFooterButton')?.addEventListener('click', async event => {
    event.preventDefault();
    try {
      await saveConfigForm();
    } catch (err) {
      console.error(err);
      toast(ui('Não foi possível salvar a configuração: ', 'Could not save configuration: ') + (err?.message || err), 'error');
    }
  });

'''
    if hook not in js:
        raise SystemExit("config submit hook not found")
    js = js.replace(hook, handler + hook, 1)

# Modal: também capturar qualquer exceção para nunca ficar sem resposta.
old_modal = '''  $('#unsavedSaveButton')?.addEventListener('click', async () => {
    const target = state.pendingTab;
    if (await saveConfigForm()) {
      $('#unsavedConfigModal')?.classList.add('hidden');
      state.pendingTab = '';
      if (target) activateTab(target);
    }
  });'''
new_modal = '''  $('#unsavedSaveButton')?.addEventListener('click', async () => {
    const target = state.pendingTab;
    try {
      if (await saveConfigForm()) {
        $('#unsavedConfigModal')?.classList.add('hidden');
        state.pendingTab = '';
        if (target) activateTab(target);
      }
    } catch (err) {
      console.error(err);
      toast(ui('Não foi possível salvar a configuração: ', 'Could not save configuration: ') + (err?.message || err), 'error');
    }
  });'''
if old_modal in js:
    js = js.replace(old_modal, new_modal, 1)

# Limpar tudo com confirmação reforçada.
if "$('#clearAllDataButton')?.addEventListener('click'" not in js:
    hook = "  $('#clearLogButton')?.addEventListener('click', async () => {"
    pos = js.find(hook)
    if pos < 0:
        raise SystemExit("clearLog handler not found")
    end = js.find("\n  });", pos)
    if end < 0:
        raise SystemExit("clearLog handler end not found")
    end += len("\n  });")
    handler = '''

  $('#clearAllDataButton')?.addEventListener('click', async () => {
    const first = window.confirm(
      ui(
        'LIMPAR TUDO? Esta ação apagará estações, tracklogs, mensagens, Log APRS-IS, pacotes e histórico de topologia. A configuração da estação e os favoritos serão preservados.\\n\\nEsta operação não pode ser desfeita.',
        'CLEAR EVERYTHING? This will delete stations, track logs, messages, APRS-IS log, packets and topology history. Station configuration and favorites will be preserved.\\n\\nThis operation cannot be undone.'
      )
    );
    if (!first) return;
    const second = window.confirm(ui('Confirma definitivamente a limpeza de todos os dados operacionais?', 'Do you definitely confirm deleting all operational data?'));
    if (!second) return;

    try {
      const result = await api('/api/maintenance/clear-all', { method:'POST' });
      state.messages = [];
      state.stations = [];
      state.logs = [];
      state.trafficEvents = [];
      state.trafficIndex = 0;
      state.lastTrafficPacketId = 0;
      clearTrafficReplayLayers();
      renderMessages();
      renderStations();
      renderLog(true);
      await loadMapData();
      await refreshStatus();
      localStorage.removeItem('pt2vhf_last_seen_msg');
      $('#messageBadge')?.classList.add('hidden');
      const total = Object.values(result.deleted || {}).reduce((sum, value) => sum + Number(value || 0), 0);
      toast(ui('Dados operacionais limpos: ', 'Operational data cleared: ') + total.toLocaleString(currentLocale()) + ui(' registro(s).', ' record(s).'), 'ok');
    } catch (err) {
      toast(err.message, 'error');
    }
  });'''
    js = js[:end] + handler + js[end:]

js_path.write_text(js, encoding="utf-8")

css = css_path.read_text(encoding="utf-8")
if "/* v1.6.6 */" not in css:
    css += '''
/* v1.6.6 */
.language-select-wrap {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 8px;
  align-items: center;
}
.language-flag {
  width: 26px;
  height: 18px;
  object-fit: cover;
  border-radius: 2px;
  border: 1px solid rgba(255,255,255,.28);
  box-shadow: 0 1px 3px rgba(0,0,0,.25);
}
.maintenance-clear-all {
  font-weight: 800;
  border-width: 2px;
  box-shadow: 0 0 0 2px rgba(220,55,70,.12), 0 0 16px rgba(220,55,70,.18);
}
'''
css_path.write_text(css, encoding="utf-8")

# Ícone Windows a partir da logo oficial.
icon_path.write_text('''from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "pt2vhf_aprs" / "static" / "img" / "aprs_logo_official.jpg"
OUTPUT = ROOT / "windows" / "app_icon.ico"

source = Image.open(SOURCE).convert("RGBA")
canvas = Image.new("RGBA", (1024, 1024), (255, 255, 255, 255))
fitted = ImageOps.contain(source, (980, 980), method=Image.Resampling.LANCZOS)
canvas.alpha_composite(fitted, ((1024 - fitted.width)//2, (1024 - fitted.height)//2))
canvas.save(OUTPUT, format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print(OUTPUT)
''', encoding="utf-8")

tests = tests_path.read_text(encoding="utf-8")
if "test_v166_clear_all_language_and_save" not in tests:
    tests += '''

def test_v166_clear_all_language_and_save():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    web = (root / "pt2vhf_aprs" / "web.py").read_text(encoding="utf-8")

    assert 'id="languageFlag"' in html
    assert 'img/flag_br.svg' in html
    assert 'id="saveConfigFooterButton" type="button"' in html
    assert 'id="clearAllDataButton"' in html
    assert "syncLanguageFlag" in js
    assert "saveConfigFooterButton" in js
    assert "/api/maintenance/clear-all" in web
    assert "maintenance-clear-all" in html
    assert "aprs_logo_official.jpg" in html


def test_v166_clear_operational_data_preserves_config_and_favorites():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            db.save_config({"callsign":"PT2VHF","latitude":-15.8,"longitude":-47.9,"altitude":1000})
            db.set_favorite("PY2ABC-9", True)
            db.add_message("in", "PY2ABC-9", "PT2VHF", "Teste", status="Recebida")
            db.add_aprs_log("RX", "PY2ABC-9>APRS:teste")
            db.record_packet("PY2ABC-9>APRS:teste", "PY2ABC-9", "status")
            db.upsert_station({
                "from":"PY2ABC-9","format":"uncompressed","latitude":-15.81,"longitude":-47.91,
                "speed":0,"course":0,"altitude":1000,"symbol_table":"/","symbol":">",
                "comment":"Teste","path":[],"raw":"x"
            })
            deleted = db.clear_operational_data()
            assert sum(deleted.values()) >= 4
            assert db.get_config()["callsign"] == "PT2VHF"
            assert "PY2ABC-9" in db.list_favorites()
            assert db.list_messages() == []
            assert db.list_stations() == []
            assert db.list_aprs_log() == []
            assert db.packet_traffic_events(hours=0, limit=20)["events"] == []
    finally:
        db.DB_PATH = original
'''
tests_path.write_text(tests, encoding="utf-8")
