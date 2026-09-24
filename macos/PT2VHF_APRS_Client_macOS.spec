# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

ROOT = Path(SPECPATH).parent
VERSION = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
hiddenimports = collect_submodules('aprslib') + collect_submodules('webview')
webview_datas = collect_data_files('webview')

a = Analysis(
    [str(ROOT / 'macos_app.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'pt2vhf_aprs' / 'templates'), 'pt2vhf_aprs/templates'),
        (str(ROOT / 'pt2vhf_aprs' / 'static'), 'pt2vhf_aprs/static'),
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PT2VHF_APRS_Client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PT2VHF_APRS_Client',
)

app = BUNDLE(
    coll,
    name='PT2VHF APRS Client.app',
    icon=str(ROOT / 'macos' / 'app_icon.icns'),
    bundle_identifier='br.com.pt2vhf.aprsclient',
    version=VERSION,
    info_plist={
        'NSHighResolutionCapable': True,
        'NSLocationWhenInUseUsageDescription': 'O PT2VHF APRS Client pode usar sua localização para preencher as coordenadas da estação quando você solicitar.',
    },
)
