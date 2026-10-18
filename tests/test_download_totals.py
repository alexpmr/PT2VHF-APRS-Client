"""Regression coverage for lifetime per-package GitHub Release counters."""
import unittest
from tools import sync_readme_release_downloads as d


def asset(asset_id, name, count, tag="v1.14.46"):
    return {"id": asset_id, "name": name, "download_count": count,
            "browser_download_url": f"https://github.com/{d.REPO}/releases/download/{tag}/{name}"}


class DownloadTotalsTests(unittest.TestCase):
    def test_all_current_package_types(self):
        samples = {
            "Setup_x64_v1.14.46.exe": "win_setup_x64",
            "Portable_x64_v1.14.46.exe": "win_portable_x64",
            "Setup_ARM64_v1.14.46.exe": "win_setup_arm64",
            "Portable_ARM64_v1.14.46.exe": "win_portable_arm64",
            "Setup_Win7_Legacy_x64_v1.14.46.exe": "win7_setup_x64",
            "Win7_Legacy_Portable_x64_v1.14.46.exe": "win7_portable_x64",
            "x86_64_v1.14.46.AppImage": "linux_appimage_x64",
            "Linux_x86_64_v1.14.46.tar.gz": "linux_tar_x64",
            "arm64_v1.14.46.AppImage": "linux_appimage_arm64",
            "Linux_arm64_v1.14.46.tar.gz": "linux_tar_arm64",
            "macOS_x86_64_v1.14.46.dmg": "mac_dmg_x64",
            "macOS_arm64_v1.14.46.dmg": "mac_dmg_arm64",
        }
        self.assertEqual(14, len(d.CATEGORIES))
        for filename, category in samples.items():
            self.assertEqual(category, d.classify_asset("PT2VHF_APRS_Client_" + filename))
        self.assertEqual("linux_deb_x64", d.classify_asset("pt2vhf-aprs-client_1.14.46_amd64.deb"))
        self.assertEqual("linux_deb_arm64", d.classify_asset("pt2vhf-aprs-client_1.14.46_arm64.deb"))
        self.assertIsNone(d.classify_asset("PT2VHF_APRS_Client_Manual_v1.14.46.pdf"))

    def test_assets_stay_recorded_and_count_never_drops(self):
        a = asset(100, "PT2VHF_APRS_Client_Setup_x64_v1.14.46.exe", 8)
        b = asset(200, "PT2VHF_APRS_Client_Portable_x64_v1.14.46.exe", 6)
        release = {"tag_name": "v1.14.46", "published_at": "2026-10-18T12:00:00Z", "assets": [a, b]}
        history, changed = d.collect_history([release], {}, "2026-10-18T12:00:00Z")
        self.assertTrue(changed)
        updated, changed = d.collect_history([{"tag_name": "v1.14.46", "assets": [
            dict(a, download_count=2)]}], history, "2026-10-19T12:00:00Z")
        self.assertFalse(changed)
        self.assertEqual(history, updated)
        self.assertEqual(6, updated["assets"]["200"]["count"])
        text = d.build_section([release], updated, "v1.14.46")
        self.assertIn("≥ 14", text)
        self.assertIn("≥ 8", text)
        self.assertIn("≥ 6", text)

    def test_missing_package_has_no_broken_link(self):
        a = asset(100, "PT2VHF_APRS_Client_Setup_x64_v1.14.46.exe", 3)
        release = {"tag_name": "v1.14.46", "published_at": "2026-10-18T12:00:00Z", "assets": [a]}
        history, _ = d.collect_history([release], {}, "2026-10-18T12:00:00Z")
        text = d.build_section([release], history, "v1.14.46")
        self.assertIn("| Windows 10/11 | Portátil EXE | x64 | Indisponível | — |", text)

    def test_readme_sync_is_idempotent_and_keeps_notes(self):
        a = asset(100, "PT2VHF_APRS_Client_Setup_x64_v1.14.46.exe", 3)
        manual = asset(333, "PT2VHF_APRS_Client_Manual_v1.14.46.pdf", 12)
        release = {"tag_name": "v1.14.46", "assets": [a, manual]}
        history, _ = d.collect_history([release], {}, "2026-10-18T12:00:00Z")
        section = d.build_section([release], history, "v1.14.46")
        old = ("# PT2VHF APRS Client - v1.14.46\n\nNovidades iniciais.\n\n"
               "## Downloads — versão 1.14.46\n\nLinks antigos.\n\n"
               "## Novidades da v1.14.45\n\nHistórico antigo.\n")
        once = d.render_readme(old, section)
        self.assertEqual(once, d.render_readme(once, section))
        self.assertLess(once.index("## Downloads"), once.index("Novidades iniciais."))
        self.assertIn("Histórico antigo.", once)
        self.assertNotIn("Links antigos.", once)
        self.assertIn("[Manual PDF](", once)


if __name__ == "__main__":
    unittest.main()
