#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV="${VENV:-.venv-build-macos}"
MACOS_REQUIREMENTS="${MACOS_REQUIREMENTS:-requirements-macos.txt}"

if [[ ! -d "$VENV" ]]; then
  "$PYTHON_BIN" -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r "$MACOS_REQUIREMENTS"
"$VENV/bin/python" -m pytest -q
"$VENV/bin/python" macos/make_icon.py

rm -rf build dist dist-macos
mkdir -p dist-macos
"$VENV/bin/pyinstaller" --noconfirm --clean macos/PT2VHF_APRS_Client_macOS.spec

version="$(tr -d '\r\n ' < VERSION)"
arch="$(uname -m)"
case "$arch" in
  arm64) label="arm64" ;;
  x86_64) label="x86_64" ;;
  *) label="$arch" ;;
esac
if [[ "${PT2VHF_MACOS_LEGACY:-0}" == "1" ]]; then
  [[ "$arch" == "x86_64" ]] || { echo "Legacy exige Intel x86_64" >&2; exit 1; }
  label="Intel_Legacy"
fi

"$VENV/bin/cyclonedx-py" environment --spec-version 1.6 --output-format JSON --output-file "dist-macos/SBOM-macOS-${label}.cdx.json"
"$VENV/bin/pip-licenses" --format=plain-vertical --with-license-file --no-license-path --output-file="dist-macos/THIRD_PARTY_LICENSES_macOS_${label}.txt"

stage="dist-macos/dmg-stage"
rm -rf "$stage"
mkdir -p "$stage"
cp -R "dist/PT2VHF APRS Client.app" "$stage/"
ln -s /Applications "$stage/Applications"
if [[ "${PT2VHF_MACOS_LEGACY:-0}" == "1" ]]; then
  cp docs/INSTALL_MACOS_LEGACY.md "$stage/INSTALL_MACOS_LEGACY.md"
else
  cp docs/INSTALL_MACOS.md "$stage/INSTALL_MACOS.md"
fi
cp LICENSE "$stage/LICENSE"

dmg="dist-macos/PT2VHF_APRS_Client_macOS_${label}_v${version}.dmg"
hdiutil create -volname "PT2VHF APRS Client ${version}" -srcfolder "$stage" -ov -format UDZO "$dmg"

echo "Artefatos macOS:"
find dist-macos -maxdepth 1 -type f -print
