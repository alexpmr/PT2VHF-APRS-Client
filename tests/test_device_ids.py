"""Base aprs-deviceid: cópia embutida atual, Mic-E e atualização semanal."""
import json
from pathlib import Path

from pt2vhf_aprs import device_ids, database as db

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_YAML = """
---
classes:
 - class: ht
   shown: HT
   description: Hand-held radio

mice:
 - suffix: "_\\""
   vendor: Yaesu
   model: FTM-350
   class: rig

 - suffix: "_0"
   vendor: Yaesu
   model: FT3D
   class: ht

micelegacy:
 - prefix: ">"
   vendor: Kenwood
   model: TH-D7
   class: ht
   features:
     - messaging

 - prefix: ">"
   suffix: "^"
   vendor: Kenwood
   model: TH-D74
   class: ht
   features:
     - messaging

tocalls:
 - tocall: APDW??
   vendor: WB2OSZ
   model: DireWolf

 - tocall: APX???
   vendor: "Traveler's ptFlex"
   model: Xastir
   os: Linux/Unix
"""


def test_parser_reads_all_sections_and_quoted_values():
    parsed = device_ids.parse_tocalls_yaml(SAMPLE_YAML)
    assert [e["suffix"] for e in parsed["mice"]] == ['_"', "_0"]
    assert parsed["micelegacy"][1] == {"prefix": ">", "suffix": "^", "vendor": "Kenwood", "model": "TH-D74",
                                       "class": "ht", "features": ["messaging"]}
    assert parsed["tocalls"][1]["vendor"] == "Traveler's ptFlex"
    assert parsed["classes"][0]["class"] == "ht"


def test_bundled_snapshot_is_current_and_keeps_own_tocall():
    payload = json.loads((ROOT / "pt2vhf_aprs/data/aprs_device_ids.json").read_text(encoding="utf-8"))
    assert device_ids.snapshot_is_valid(payload)
    assert len(payload["entries"]) >= 480
    assert payload["mice"] and payload["micelegacy"] and payload["classes"]
    assert any(e["tocall"] == "APZVHF" and e.get("local_override") for e in payload["entries"])


def test_mice_new_style_and_kenwood_legacy():
    parsed = device_ids.parse_tocalls_yaml(SAMPLE_YAML)
    mice, legacy = parsed["mice"], parsed["micelegacy"]
    ft3d = "PY2ABC-7>T4SQVY,WIDE1-1,qAR,PY2XX:`DIl l]>/`Hello 73_0"
    assert device_ids.resolve_mice(ft3d, mice, legacy)["model"] == "FT3D"
    assert "messaging" in device_ids.resolve_mice(ft3d, mice, legacy)["features"]
    thd74 = "PY2ABC-7>T4SQVY,qAR,PY2XX:`DIl l]>/>comment^"
    assert device_ids.resolve_mice(thd74, mice, legacy)["model"] == "TH-D74"
    thd7 = "PY2ABC-7>T4SQVY,qAR,PY2XX:`DIl l]>/>"
    assert device_ids.resolve_mice(thd7, mice, legacy)["model"] == "TH-D7"
    assert device_ids.resolve_mice("PY2ABC>APDW17:!2330.00S/04630.00W-", mice, legacy) is None


def test_database_resolves_mice_and_tocall_from_raw():
    db.reload_aprs_device_ids()
    tocall, meta = db.resolve_aprs_device_from_raw("PY2ABC-7>T4SQVY,qAR,PY2XX:`DIl l]>/`Hi_0")
    assert tocall == "Mic-E" and meta["vendor"] == "Yaesu" and meta["identified"]
    tocall, meta = db.resolve_aprs_device_from_raw("PY2ABC>APDW17,qAR,PY2XX:!2330.00S/04630.00W-")
    assert tocall == "APDW17" and meta["friendly_name"] == "Dire Wolf 1.7"
    info = db.aprs_map_device_metadata("PY2ABC-7>T4SQVY,qAR,PY2XX:`DIl l]>/`Hi_0")
    assert info["device_tocall"] == "Mic-E" and info["device_model"] == "FT3D"


def test_weekly_refresh_writes_user_copy_and_is_used(tmp_path, monkeypatch):
    real_yaml = SAMPLE_YAML + "".join(f"\n - tocall: APQ{i:03d}\n   vendor: Test\n   model: M{i}\n" for i in range(400))
    assert device_ids.refresh_due(tmp_path)
    result = device_ids.refresh_now(tmp_path, downloader=lambda url: real_yaml)
    assert result["ok"] and result["entries"] >= 400
    assert not device_ids.refresh_due(tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "pt2vhf_aprs.db")
    db.reload_aprs_device_ids()
    try:
        assert db.resolve_aprs_device_id("APQ007")["model"] == "M7"
        assert db.resolve_aprs_device_id("APZVHF")["model"] == "PT2VHF APRS Client"
    finally:
        monkeypatch.undo()
        db.reload_aprs_device_ids()


def test_truncated_download_is_rejected(tmp_path):
    result = device_ids.refresh_now(tmp_path, downloader=lambda url: SAMPLE_YAML)
    assert not result["ok"]
    assert not device_ids.user_snapshot_path(tmp_path).exists()
