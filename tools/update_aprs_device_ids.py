"""Atualiza a cópia embutida da base aprs-deviceid (pt2vhf_aprs/data/aprs_device_ids.json).

Uso: python tools/update_aprs_device_ids.py [caminho/para/tocalls.yaml]
Sem argumento, baixa de aprs-deviceid.aprsfoundation.org (ou do GitHub).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pt2vhf_aprs import device_ids  # noqa: E402

target = ROOT / "pt2vhf_aprs" / "data" / "aprs_device_ids.json"
if len(sys.argv) > 1:
    source = Path(sys.argv[1])
    snapshot = device_ids.build_snapshot(device_ids.parse_tocalls_yaml(source.read_text(encoding="utf-8")),
                                         device_ids.SOURCE_URLS[0])
    assert device_ids.snapshot_is_valid(snapshot), "tocalls.yaml incompleto"
    target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
else:
    result = device_ids.refresh_now(target.parent)
    assert result.get("ok"), result
print(f"{target}: {len(json.loads(target.read_text(encoding='utf-8'))['entries'])} TOCALLs")
