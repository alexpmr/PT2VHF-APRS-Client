"""v1.14.58: retenção permanente de todos os itens por padrão."""
import json

from pt2vhf_aprs import database as db, retention, tnc_service, v111_features


def test_all_defaults_are_permanent():
    assert set(retention.DEFAULT_DAYS.values()) == {0}
    assert set(v111_features.RETENTION_DEFAULTS.values()) == {0}
    assert tnc_service.TNC_DEFAULTS["retention_days"] == 0


def test_new_install_keeps_everything(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "new.db")
    db.init_db()
    policy = retention.get_policy()
    assert set(policy["policies"].values()) == {0}
    assert retention.apply_retention()["deleted"] == 0


def test_old_defaults_migrate_but_user_choices_stay(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "old.db")
    db.init_db()
    with db.connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS retention_policies (category TEXT PRIMARY KEY, days INTEGER NOT NULL, updated_at TEXT)")
        for category, days in retention.LEGACY_DEFAULT_DAYS.items():
            conn.execute("INSERT OR REPLACE INTO retention_policies(category,days) VALUES(?,?)", (category, days))
        conn.execute("UPDATE retention_policies SET days=7 WHERE category='packets'")  # escolha do usuário
        conn.execute("DELETE FROM schema_migrations_v112 WHERE migration_key=?", (retention.PERMANENT_DEFAULTS_MIGRATION,))
    policies = retention.get_policy()["policies"]
    assert policies["stations"] == 0 and policies["topology_events"] == 0 and policies["messages"] == 0
    assert policies["packets"] == 7
    retention.save_policy({"stations": 30}, True)          # usuário escolhe de novo depois da migração
    assert retention.get_policy()["policies"]["stations"] == 30


def test_v111_and_tnc_old_defaults_become_permanent(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "v111.db")
    db.init_db()
    v111_features._ensure_schema()
    with db.connection() as conn:
        conn.execute("INSERT OR REPLACE INTO settings_v111(key,payload,updated_at) VALUES('retention',?,'x')",
                     (json.dumps({**v111_features.LEGACY_RETENTION_DEFAULTS, "messages_days": 0, "tracks_days": 60}),))
    values = v111_features.retention_settings()
    assert values["packets_days"] == 0 and values["tracks_days"] == 60
    assert tnc_service.normalize_tnc_config({"retention_days": 14}, strict=False)["retention_days"] == 0
    saved = tnc_service.normalize_tnc_config({"retention_days": 14, "retention_permanent_v11458": True}, strict=False)
    assert saved["retention_days"] == 14
