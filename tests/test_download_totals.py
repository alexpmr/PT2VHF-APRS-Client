"""Regression tests for counters of the latest published release only."""
import unittest

from tools import sync_readme_release_downloads as d


def asset(asset_id, name, count, tag="v1.14.46"):
    return {
        "id": asset_id, "name": name, "download_count": count,
        "browser_download_url": f"https://github.com/{d.REPO}/releases/download/{tag}/{name}",
    }


def release(tag, *assets):
    return {"tag_name": tag, "assets": list(assets)}


class CurrentReleaseDownloadTests(unittest.TestCase):
    def test_classification_covers_fourteen_packages(self):
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
        for suffix, category in samples.items():
            with self.subTest(suffix=suffix):
                self.assertEqual(category, d.classify_asset("PT2VHF_APRS_Client_" + suffix))
        self.assertEqual("linux_deb_x64", d.classify_asset("pt2vhf-aprs-client_1.14.46_amd64.deb"))
        self.assertEqual("linux_deb_arm64", d.classify_asset("pt2vhf-aprs-client_1.14.46_arm64.deb"))
        self.assertIsNone(d.classify_asset("PT2VHF_APRS_Client_Manual_v1.14.46.pdf"))

    def test_counts_are_exact_for_current_release_only(self):
        current = release("v1.14.46",
            asset(1, "PT2VHF_APRS_Client_Setup_x64_v1.14.46.exe", 8),
            asset(2, "PT2VHF_APRS_Client_Portable_x64_v1.14.46.exe", 6),
            asset(3, "PT2VHF_APRS_Client_Manual_v1.14.46.pdf", 800))
        text = d.build_section(current)
        self.assertIn("| Windows 10/11 | Instalador EXE | x64 |", text)
        self.assertIn("| 8 |", text)
        self.assertIn("| 6 |", text)
        self.assertIn("**Total contabilizado dos pacotes da v1.14.46: 14.**", text)
        self.assertNotIn("≥", text)
        self.assertNotIn("acumulados", text.lower())
        self.assertNotIn("814", text)
        self.assertEqual(1, text.count("Manual PDF"))

    def test_new_release_resets_counts(self):
        old = release("v1.14.46", asset(1, "PT2VHF_APRS_Client_Setup_x64_v1.14.46.exe", 1000))
        current = release("v1.14.47", asset(2, "PT2VHF_APRS_Client_Setup_x64_v1.14.47.exe", 0, "v1.14.47"))
        text = d.build_section(current)
        self.assertIn("| 0 |", text)
        self.assertIn("v1.14.47", text)
        self.assertNotIn("v1.14.46", text)
        self.assertNotIn("1.000", text)
        self.assertTrue(d.build_section(old).endswith("<!-- DOWNLOAD_TABLE_END -->\n"))

    def test_missing_and_invalid_counter_are_not_fabricated(self):
        missing = release("v1.14.46", asset(1, "PT2VHF_APRS_Client_Setup_x64_v1.14.46.exe", None))
        text = d.build_section(missing)
        self.assertIn("| Windows 10/11 | Instalador EXE | x64 |", text)
        self.assertIn("[Baixar](", text)
        self.assertIn("| — |", text)
        self.assertIn("| Windows 10/11 | Portátil EXE | x64 | Indisponível | — |", text)

    def test_duplicate_package_type_is_rejected(self):
        a = asset(1, "PT2VHF_APRS_Client_Setup_x64_v1.14.46.exe", 3)
        b = asset(2, "PT2VHF_APRS_Client_Setup_x64_v1.14.46.exe", 4)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            d.build_section(release("v1.14.46", a, b))

    def test_readme_sync_preserves_notes_and_is_idempotent(self):
        item = asset(1, "PT2VHF_APRS_Client_Setup_x64_v1.14.46.exe", 3)
        manual = asset(2, "PT2VHF_APRS_Client_Manual_v1.14.46.pdf", 20)
        section = d.build_section(release("v1.14.46", item, manual))
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
