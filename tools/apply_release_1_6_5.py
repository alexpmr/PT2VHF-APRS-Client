from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html_path = ROOT / "pt2vhf_aprs/templates/index.html"
js_path = ROOT / "pt2vhf_aprs/static/js/app.js"
css_path = ROOT / "pt2vhf_aprs/static/css/app.css"
db_path = ROOT / "pt2vhf_aprs/database.py"
service_path = ROOT / "pt2vhf_aprs/aprs_service.py"
tests_path = ROOT / "tests/test_core.py"
icon_path = ROOT / "windows/make_icon.py"

html = html_path.read_text(encoding="utf-8")
html = html.replace(
    '<div class="traffic-animation-panel map-traffic-panel">',
    '<div class="traffic-animation-panel map-traffic-panel hidden">'
)
html = html.replace(
    '<div id="trafficActivityIndicator" class="traffic-activity-indicator"',
    '<button id="toggleReplayBarButton" type="button" class="btn secondary replay-toggle-button" aria-pressed="false" title="Mostrar/ocultar histórico">Histórico</button>\n    <div id="trafficActivityIndicator" class="traffic-activity-indicator"',
    1
)

for button in (
    '<button id="clearTracklogsButton" type="button" class="btn secondary">Limpar tracklogs</button>\n',
    '<button id="clearStationsButton" type="button" class="btn danger">Limpar estações</button>\n',
    '<button id="clearMessagesButton" type="button" class="btn danger">Limpar mensagens</button>\n',
    '<button id="clearLogButton" type="button" class="btn secondary">Limpar log</button>\n',
):
    html = html.replace(button, "", 1)

html = html.replace(
'''            <label class="check-field message-sound-check">
              <input name="sound_on_personal_message" type="checkbox" checked>
              <span>Tocar sinal sonoro ao receber mensagem para minha estação</span>
            </label>
''', "", 1)
html = html.replace(
'''            <label class="check-field">
              <input name="sound_on_station_activity" type="checkbox" checked>
              <span>Tocar sinal sonoro quando uma estação transmitir</span>
            </label>
''', "", 1)

updates_anchor = '''      <div class="config-card full-card config-section config-section-app">
        <h3>Atualizações</h3>'''
notifications = '''      <div class="config-card full-card config-section config-section-app">
        <h3>Notificações</h3>
        <div class="form-grid two-cols notification-settings-grid">
          <label class="check-field">
            <input name="sound_on_personal_message" type="checkbox" checked>
            <span>Tocar som no navegador ao receber mensagem para minha estação</span>
          </label>
          <label class="check-field">
            <input name="sound_on_station_activity" type="checkbox" checked>
            <span>Tocar som no navegador quando uma estação visível transmitir</span>
          </label>
          <label class="field">
            <span>Volume das notificações</span>
            <div class="range-field-row">
              <input name="notification_volume" id="notificationVolume" type="range" min="0" max="100" step="1" value="70">
              <output id="notificationVolumeValue" for="notificationVolume">70%</output>
            </div>
          </label>
          <label class="field">
            <span>Som</span>
            <select name="notification_sound" id="notificationSound">
              <option value="beep">Beep</option>
              <option value="chime">Chime</option>
              <option value="radio">Rádio</option>
            </select>
          </label>
        </div>
        <div class="config-actions">
          <button id="testNotificationSound" type="button" class="btn secondary">Testar som</button>
          <span class="hint">O volume e o som selecionado são aplicados aos avisos emitidos pelo navegador.</span>
        </div>
      </div>

'''
if updates_anchor in html and 'id="notificationVolume"' not in html:
    html = html.replace(updates_anchor, notifications + updates_anchor, 1)

backup_anchor = '''      <div class="config-card full-card config-section config-section-app">
        <h3>Backup da configuração</h3>'''
maintenance = '''      <div class="config-card full-card config-section config-section-app maintenance-card">
        <h3>Manutenção</h3>
        <p class="hint">Ações abaixo removem dados do banco local. Cada operação exige confirmação.</p>
        <div class="maintenance-actions">
          <button id="clearTracklogsButton" type="button" class="btn danger">Limpar tracklogs</button>
          <button id="clearStationsButton" type="button" class="btn danger">Limpar estações</button>
          <button id="clearMessagesButton" type="button" class="btn danger">Limpar mensagens</button>
          <button id="clearLogButton" type="button" class="btn danger">Limpar Log APRS-IS</button>
        </div>
      </div>

'''
if backup_anchor in html and "maintenance-card" not in html:
    html = html.replace(backup_anchor, maintenance + backup_anchor, 1)
html_path.write_text(html, encoding="utf-8")

db = db_path.read_text(encoding="utf-8")
db = db.replace(
    '    "sound_on_station_activity": 1,\n',
    '    "sound_on_station_activity": 1,\n    "notification_volume": 70,\n    "notification_sound": "beep",\n',
    1
)
db = db.replace(
    '''        if "sound_on_station_activity" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN sound_on_station_activity INTEGER NOT NULL DEFAULT 1")
''',
    '''        if "sound_on_station_activity" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN sound_on_station_activity INTEGER NOT NULL DEFAULT 1")
        if "notification_volume" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN notification_volume INTEGER NOT NULL DEFAULT 70")
        if "notification_sound" not in config_columns:
            conn.execute("ALTER TABLE config ADD COLUMN notification_sound TEXT NOT NULL DEFAULT 'beep'")
''',
    1
)
db = db.replace(
    '    merged["sound_on_station_activity"] = 1 if bool(merged["sound_on_station_activity"]) else 0\n',
    '    merged["sound_on_station_activity"] = 1 if bool(merged["sound_on_station_activity"]) else 0\n    merged["notification_volume"] = max(0, min(100, int(merged["notification_volume"] or 0)))\n    merged["notification_sound"] = str(merged["notification_sound"] or "beep").lower().strip()\n    if merged["notification_sound"] not in {"beep", "chime", "radio"}:\n        merged["notification_sound"] = "beep"\n',
    1
)
db = db.replace(
    're.fullmatch(r"[A-Z0-9]{1,6}(?:-[0-9]{1,2})?", call)',
    're.fullmatch(r"[A-Z0-9]{1,6}(?:-[A-Z0-9]{1,2})?", call)'
)
db_path.write_text(db, encoding="utf-8")

service = service_path.read_text(encoding="utf-8")
service = service.replace(
    're.fullmatch(r"[A-Z0-9]{1,6}(?:-[0-9]{1,2})?", destination)',
    're.fullmatch(r"[A-Z0-9]{1,6}(?:-[A-Z0-9]{1,2})?", destination)'
)
service_path.write_text(service, encoding="utf-8")

js = js_path.read_text(encoding="utf-8")
js = js.replace(
    "    soundOnStationActivity: true,\n",
    "    soundOnStationActivity: true,\n    notificationVolume: 70,\n    notificationSound: 'beep',\n",
    1
)

old_sound = '''  function playStationActivitySound(callsign) {
    if (!state.soundOnStationActivity || !stationIsVisible(callsign)) return;
    const now = Date.now();
    if (now - state.lastActivitySoundAt < 700) return;
    state.lastActivitySoundAt = now;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;
      if (!state.activityAudioContext) state.activityAudioContext = new AudioContextClass();
      const ctx = state.activityAudioContext;
      if (ctx.state === 'suspended') ctx.resume().catch(() => {});
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.0001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.08, ctx.currentTime + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.16);
      oscillator.connect(gain).connect(ctx.destination);
      oscillator.start();
      oscillator.stop(ctx.currentTime + 0.18);
    } catch (_) {}
  }'''
new_sound = '''  function playBrowserNotificationSound(sound = state.notificationSound) {
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass || Number(state.notificationVolume || 0) <= 0) return;
      if (!state.activityAudioContext) state.activityAudioContext = new AudioContextClass();
      const ctx = state.activityAudioContext;
      if (ctx.state === 'suspended') ctx.resume().catch(() => {});
      const profile = {
        beep:  { type:'sine',     f1:880, f2:880, duration:.18 },
        chime: { type:'sine',     f1:660, f2:990, duration:.32 },
        radio: { type:'triangle', f1:520, f2:740, duration:.24 }
      }[sound] || { type:'sine', f1:880, f2:880, duration:.18 };
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      const level = Math.max(.0001, Math.min(.16, (Number(state.notificationVolume || 70) / 100) * .12));
      oscillator.type = profile.type;
      oscillator.frequency.setValueAtTime(profile.f1, ctx.currentTime);
      oscillator.frequency.linearRampToValueAtTime(profile.f2, ctx.currentTime + profile.duration);
      gain.gain.setValueAtTime(.0001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(level, ctx.currentTime + .015);
      gain.gain.exponentialRampToValueAtTime(.0001, ctx.currentTime + profile.duration);
      oscillator.connect(gain).connect(ctx.destination);
      oscillator.start();
      oscillator.stop(ctx.currentTime + profile.duration + .02);
    } catch (_) {}
  }

  function playStationActivitySound(callsign) {
    if (!state.soundOnStationActivity || !stationIsVisible(callsign)) return;
    const now = Date.now();
    if (now - state.lastActivitySoundAt < 700) return;
    state.lastActivitySoundAt = now;
    playBrowserNotificationSound();
  }'''
if old_sound not in js:
    raise SystemExit("sound function not found")
js = js.replace(old_sound, new_sound, 1)

js = js.replace(
    "      state.soundOnStationActivity = !!cfg.sound_on_station_activity;\n",
    "      state.soundOnStationActivity = !!cfg.sound_on_station_activity;\n      state.notificationVolume = Math.max(0, Math.min(100, Number(cfg.notification_volume ?? 70)));\n      state.notificationSound = ['beep','chime','radio'].includes(String(cfg.notification_sound || '')) ? String(cfg.notification_sound) : 'beep';\n      if ($('#notificationVolumeValue')) $('#notificationVolumeValue').textContent = String(state.notificationVolume) + '%';\n",
    1
)

js = js.replace(
    "  function showIncomingMessageAlert(message) {\n    state.currentAlertMessage = message;\n",
    "  function showIncomingMessageAlert(message) {\n    state.currentAlertMessage = message;\n    if (state.soundOnPersonalMessage) playBrowserNotificationSound();\n",
    1
)

hook = "  $('#messageType').addEventListener('change', updateMessageComposerMode);"
extra = '''  $('#notificationVolume')?.addEventListener('input', event => {
    state.notificationVolume = Math.max(0, Math.min(100, Number(event.target.value || 0)));
    if ($('#notificationVolumeValue')) $('#notificationVolumeValue').textContent = String(state.notificationVolume) + '%';
  });
  $('#notificationSound')?.addEventListener('change', event => {
    state.notificationSound = String(event.target.value || 'beep');
  });
  $('#testNotificationSound')?.addEventListener('click', () => {
    const volume = $('#notificationVolume');
    const sound = $('#notificationSound');
    if (volume) state.notificationVolume = Math.max(0, Math.min(100, Number(volume.value || 0)));
    if (sound) state.notificationSound = String(sound.value || 'beep');
    playBrowserNotificationSound();
  });

  function setReplayPanelVisible(visible) {
    const panel = $('.map-traffic-panel');
    const button = $('#toggleReplayBarButton');
    if (!panel || !button) return;
    panel.classList.toggle('hidden', !visible);
    button.classList.toggle('active-filter', !!visible);
    button.setAttribute('aria-pressed', visible ? 'true' : 'false');
    button.textContent = visible ? ui('Ocultar histórico', 'Hide history') : ui('Histórico', 'History');
    requestAnimationFrame(() => state.map?.invalidateSize?.());
  }
  $('#toggleReplayBarButton')?.addEventListener('click', () => {
    const panel = $('.map-traffic-panel');
    setReplayPanelVisible(!!panel?.classList.contains('hidden'));
  });
  setReplayPanelVisible(false);

'''
if extra.strip() not in js:
    js = js.replace(hook, extra + hook, 1)
js_path.write_text(js, encoding="utf-8")

css = css_path.read_text(encoding="utf-8")
css += '''
/* v1.6.5 */
.replay-toggle-button.active-filter { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(59,166,255,.14); }
.maintenance-card { border-color: rgba(220,70,70,.34); }
.maintenance-actions { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
.notification-settings-grid { align-items:end; }
'''
css_path.write_text(css, encoding="utf-8")

tests = tests_path.read_text(encoding="utf-8")
if "test_v165_maintenance_notifications_and_ssid" not in tests:
    tests += '''

def test_v165_maintenance_notifications_and_ssid():
    root = Path(__file__).resolve().parent.parent
    html = (root / "pt2vhf_aprs" / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "pt2vhf_aprs" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    service = (root / "pt2vhf_aprs" / "aprs_service.py").read_text(encoding="utf-8")
    assert "maintenance-card" in html
    assert html.count('id="clearTracklogsButton"') == 1
    assert html.count('id="clearStationsButton"') == 1
    assert html.count('id="clearMessagesButton"') == 1
    assert html.count('id="clearLogButton"') == 1
    assert 'id="notificationVolume"' in html
    assert 'id="notificationSound"' in html
    assert 'id="testNotificationSound"' in html
    assert 'id="toggleReplayBarButton"' in html
    assert 'map-traffic-panel hidden' in html
    assert "playBrowserNotificationSound" in js
    assert "[A-Z0-9]{1,6}(?:-[A-Z0-9]{1,2})?" in service


def test_v165_favorite_accepts_alphanumeric_suffix():
    original = db.DB_PATH
    try:
        with tempfile.TemporaryDirectory() as td:
            db.DB_PATH = Path(td) / "test.db"
            db.init_db()
            assert db.set_favorite("PY2OFU-D", True) is True
            assert "PY2OFU-D" in db.list_favorites()
    finally:
        db.DB_PATH = original
'''
tests_path.write_text(tests, encoding="utf-8")
