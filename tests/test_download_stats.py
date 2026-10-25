"""Contador acumulado de downloads por tipo de build."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("download_stats", ROOT / ".github" / "download-stats" / "stats.py")
ds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ds)
EXAMPLES = json.loads((ROOT / ".github" / "download-stats" / "examples.json").read_text(encoding="utf-8"))


class DownloadStats(unittest.TestCase):
    def test_asset_names_map_to_build_types(self):
        for name, kind in EXAMPLES.items():
            self.assertEqual(ds.kind(name), kind, name)

    def test_counts_survive_deleted_releases_and_never_go_down(self):
        typed = [n for n, k in EXAMPLES.items() if k]
        other = [n for n, k in EXAMPLES.items() if not k]
        with tempfile.TemporaryDirectory() as tmp:
            first = [{"tag_name": "v1", "assets": [{"name": typed[0], "download_count": 5}]
                      + [{"name": n, "download_count": 50} for n in other]}]
            self.assertEqual(ds.main(tmp, releases=first)[ds.kind(typed[0])], 5)
            # v1 apagada; v2 nova; um contador que "voltou" não diminui o total.
            second = [{"tag_name": "v2", "assets": [{"name": typed[0], "download_count": 3}]}]
            self.assertEqual(ds.main(tmp, releases=second)[ds.kind(typed[0])], 8)
            second[0]["assets"][0]["download_count"] = 1
            out = ds.main(tmp, releases=second)
            self.assertEqual(out[ds.kind(typed[0])], 8)
            badge = json.loads((Path(tmp) / (ds.kind(typed[0]) + ".json")).read_text())
            self.assertEqual((badge["schemaVersion"], badge["message"]), (1, "8"))
            self.assertIn(out["total"], (0, 8))

    def test_readme_shows_every_badge(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for key in [k for k, _ in ds.TYPES] + list(ds.GROUPS) + ["total"]:
            if key in ds.CONFIG.get("readme_skip", []):
                continue
            self.assertIn("badges%2Fdownloads%2F" + key + ".json", text, key)

    def test_thousands_use_dot(self):
        self.assertEqual(ds.badge(12345)["message"], "12.345")


if __name__ == "__main__":
    unittest.main()
