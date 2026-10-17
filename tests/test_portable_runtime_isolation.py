from pathlib import Path
from pt2vhf_aprs import updater


def test_helper_resets_inherited_onefile_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(updater, 'UPDATE_DIR', tmp_path)
    monkeypatch.setenv('_PYI_APPLICATION_HOME_DIR', r'C:\Temp\_MEIold')
    monkeypatch.setenv('_PYI_PARENT_PROCESS_LEVEL', '1')
    monkeypatch.setenv('_PYI_ARCHIVE_FILE', r'C:\old.exe')
    pending = {'path': str(tmp_path / 'new.exe'),
               'current_executable': str(tmp_path / 'app.exe'),
               'mode': 'windows-portable', 'pid': 123}
    helper = updater._write_windows_cmd_helper(pending).read_text(encoding='utf-8-sig')
    for setting in ('PYINSTALLER_RESET_ENVIRONMENT=1', '_MEIPASS2=',
                    '_PYI_APPLICATION_HOME_DIR=', '_PYI_PARENT_PROCESS_LEVEL=',
                    '_PYI_ARCHIVE_FILE='):
        assert 'set "' + setting + '"' in helper
        assert helper.index('set "' + setting + '"') < helper.index('start "" "%destination%"')
    assert 'goto portable_unhealthy' in helper
    assert 'previous portable restored' in helper
