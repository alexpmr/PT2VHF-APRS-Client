# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).parent
hiddenimports = collect_submodules("aprslib")

a = Analysis(
    [str(ROOT / "windows_legacy_app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "pt2vhf_aprs" / "templates"), "pt2vhf_aprs/templates"),
        (str(ROOT / "pt2vhf_aprs" / "static"), "pt2vhf_aprs/static"),
        (str(ROOT / "pt2vhf_aprs" / "data"), "pt2vhf_aprs/data"),
        (str(ROOT / "VERSION"), "."),
        (str(ROOT / "windows" / "app_icon.ico"), "windows"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["webview", "clr", "pythonnet"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PT2VHF_APRS_Client_Win7_Legacy_x64",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(ROOT / "windows" / "app_icon.ico"),
    version=str(ROOT / "windows" / "version_info.txt"),
)
