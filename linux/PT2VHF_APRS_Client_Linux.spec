# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import platform
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

ROOT = Path(SPECPATH).parent
hiddenimports = collect_submodules('aprslib') + collect_submodules('webview')
webview_datas = collect_data_files('webview')

a = Analysis(
    [str(ROOT / 'linux_app.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'pt2vhf_aprs' / 'templates'), 'pt2vhf_aprs/templates'),
        (str(ROOT / 'pt2vhf_aprs' / 'static'), 'pt2vhf_aprs/static'),
        (str(ROOT / 'pt2vhf_aprs' / 'data'), 'pt2vhf_aprs/data'),
        (str(ROOT / 'VERSION'), '.'),
        *webview_datas,
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
ARCH = 'arm64' if platform.machine().lower() in ('aarch64', 'arm64') else 'x86_64'

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f'PT2VHF_APRS_Client_Linux_{ARCH}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
