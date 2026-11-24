from pt2vhf_aprs import os_language as ol


def test_map_language_variants():
    assert ol.map_language("pt_BR.UTF-8") == "pt-BR"
    assert ol.map_language("de_DE") == "de-DE"
    assert ol.map_language("zh-Hans-CN") == "zh-CN"
    assert ol.map_language("Portuguese_Brazil") == "pt-BR"
    assert ol.map_language("en_US") == "en"
    assert ol.map_language("C") is None
    assert ol.map_language("POSIX") is None


def test_unsupported_language_falls_back_to_english(monkeypatch):
    monkeypatch.setattr(ol, "_candidates", lambda: ["ru_RU.UTF-8"])
    ol.system_language.cache_clear()
    try:
        assert ol.system_language() == "en"
    finally:
        ol.system_language.cache_clear()


def test_config_follows_os_until_user_chooses(tmp_path, monkeypatch):
    from pt2vhf_aprs import database as db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "lang.db")
    monkeypatch.setattr(ol, "system_language", lambda: "fr")
    db.init_db()
    assert db.get_config()["language"] == "fr"
    db.save_config({"language": "ja-JP"})
    assert db.get_config()["language"] == "ja-JP"
