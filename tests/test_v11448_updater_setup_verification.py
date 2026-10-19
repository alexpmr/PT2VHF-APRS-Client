"""#103: Setup só é considerado concluído quando a versão nova confirma execução."""
from pt2vhf_aprs import updater


def _helper_text(tmp_path, monkeypatch, mode="windows-installer"):
    monkeypatch.setattr(updater, "UPDATE_DIR", tmp_path)
    monkeypatch.setattr(updater, "UPDATE_RESULT_FILE", tmp_path / "last_update_result.txt")
    monkeypatch.setattr(updater, "SETUP_LOG_FILE", tmp_path / "installer_setup.log")
    monkeypatch.setattr(updater, "APPLY_LOG", tmp_path / "update_apply.log")
    exe = "PT2VHF_APRS_Client.exe" if mode == "windows-installer" else "PT2VHF_APRS_Client_Win7_Legacy_x64.exe"
    script = updater._write_windows_cmd_helper({
        "path": str(tmp_path / "setup.exe"),
        "current_executable": str(tmp_path / "old" / exe),
        "mode": mode,
        "version": "1.14.48",
        "pid": 1,
    })
    return script.read_text(encoding="utf-8")


def test_setup_helper_verifies_running_version_not_only_exit_code(tmp_path, monkeypatch):
    text = _helper_text(tmp_path, monkeypatch)
    assert "installer completed" not in text
    assert '/LOG="%setuplog%"' in text
    assert 'set "target=1.14.48"' in text
    assert "{4A513928-71DA-4DD7-9C06-13D0D8E90FEA}_is1" in text
    assert 'set "relaunch=%installdir%%exename%"' in text
    assert 'set "PT2VHF_UPDATE_READY_MARKER=%marker%"' in text
    assert 'findstr /C:"version=%target% " "%marker%"' in text
    assert "status=version_mismatch" in text and "status=unconfirmed" in text
    ok = text.index("status=ok")
    assert text.index('findstr /C:"version=%target% "') < ok


def test_legacy_setup_uses_its_own_inno_app_id(tmp_path, monkeypatch):
    text = _helper_text(tmp_path, monkeypatch, mode="windows-legacy-installer")
    assert "{0CE6C737-4D5A-4B9C-BACE-71406DFA1425}_is1" in text
    assert 'set "exename=PT2VHF_APRS_Client_Win7_Legacy_x64.exe"' in text


def test_last_update_result_parsing(tmp_path, monkeypatch):
    result_file = tmp_path / "last_update_result.txt"
    monkeypatch.setattr(updater, "UPDATE_RESULT_FILE", result_file)
    assert updater.last_update_result() is None
    result_file.write_text(
        "status=version_mismatch target=1.14.48 found=1.14.40 exe=C:\\Program Files\\PT2VHF APRS Client\\PT2VHF_APRS_Client.exe \n",
        encoding="utf-8",
    )
    result = updater.last_update_result()
    assert result["status"] == "version_mismatch"
    assert result["target"] == "1.14.48" and result["found"] == "1.14.40"
    assert result["exe"].endswith("PT2VHF_APRS_Client.exe")
    assert "recorded_at" in result


def test_marker_format_matches_helper_check():
    # windows_app._mark_updated_instance_ready grava "ready version=X pid=Y";
    # o helper procura "version=X " (com espaço) para não aceitar 1.14.480.
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "windows_app.py").read_text(encoding="utf-8")
    assert '"ready version={} pid={}' in source
