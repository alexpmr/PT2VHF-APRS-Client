"""Backlog 12/11/2026: splash "Powered by www.PT2VHF.com" como no PT2VHF Sat Tool v1.7.2."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_banner_is_shipped_resized_in_static():
    banner = ROOT / "pt2vhf_aprs/static/img/welcome-banner.jpg"
    assert banner.exists() and banner.stat().st_size < 400_000
    from PIL import Image
    with Image.open(banner) as im:
        assert 1100 <= im.width <= 1300 and abs(im.width / im.height - 1672 / 941) < 0.01
    # A pasta static inteira entra em todos os pacotes (Windows, Win7, ARM64, Linux e macOS).
    for spec in [*(ROOT / "windows").glob("*.spec"), *(ROOT / "linux").glob("*.spec"), *(ROOT / "macos").glob("*.spec")]:
        assert "'static'" in spec.read_text(encoding="utf-8").replace('"', "'"), spec


def test_splash_layout_banner_link_close_and_countdown():
    html = (ROOT / "pt2vhf_aprs/templates/index.html").read_text(encoding="utf-8")
    box = html[html.index('id="officialSiteNotice"'):html.index('id="whatsNewModal"')]
    assert 'id="officialSiteNoticeBanner"' in box and 'href="https://www.pt2vhf.com"' in box
    assert "img/welcome-banner.jpg" in box and 'alt="Powered by www.PT2VHF.com"' in box
    actions = box[box.index("official-site-notice-actions"):]
    assert actions.index("officialSiteNoticeLink") < actions.index("officialSiteNoticeCountdown") \
        < actions.index("officialSiteNoticeClose")
    assert "⏱ 10 s" in actions and 'id="officialSiteNoticeBar"' in actions
    css = (ROOT / "pt2vhf_aprs/static/css/app.css").read_text(encoding="utf-8")
    assert ".official-site-banner img{display:block;width:100%;height:auto" in css
    assert "background:#f08a24" in css


def test_splash_closes_itself_after_ten_seconds_and_keeps_the_rule():
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert "const OFFICIAL_SITE_NOTICE_SECONDS = 10;" in js
    block = js[js.index("const OFFICIAL_SITE_NOTICE_SECONDS"):js.index("setTimeout(showOfficialSiteNotice, 1500);")]
    assert "if (left <= 0) { hideOfficialSiteNotice(); return; }" in block
    assert "setInterval(tick, 1000)" in block and "\\u23f1 ${left} s" in block
    assert "addEventListener('click', hideOfficialSiteNotice)" in block
    # Mesma regra de antes: uma vez por abertura, depois de 1,5 s, esperando outros avisos.
    assert "officialSiteNoticeShown" in block and ".message-alert-overlay:not(.hidden)" in block


def test_splash_is_an_in_window_layer_closed_by_esc_or_click_outside():
    """15/11/2026: splash integrado à janela principal (camada), fecha com Esc ou clique fora do banner."""
    css = (ROOT / "pt2vhf_aprs/static/css/app.css").read_text(encoding="utf-8")
    assert ".official-site-notice{position:fixed;inset:0;" in css and "background:#040a11d6" in css
    js = (ROOT / "pt2vhf_aprs/static/js/app.js").read_text(encoding="utf-8")
    assert "if (event.target === event.currentTarget) hideOfficialSiteNotice();" in js
    assert "event.key === 'Escape' && !$('#officialSiteNotice')?.classList.contains('hidden')" in js
    # Nenhuma janela nativa separada para o splash.
    for launcher in ("windows_app.py", "linux_app.py", "macos_app.py"):
        assert (ROOT / launcher).read_text(encoding="utf-8").count("create_window(") == 1
