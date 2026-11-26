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

app="dist/PT2VHF APRS Client.app"
# Assinatura Developer ID (v2.0.7): só quando MACOS_SIGN_IDENTITY vem do CI. Sem ela, segue sem assinar.
if [[ -n "${MACOS_SIGN_IDENTITY:-}" ]]; then
  echo "Assinando com: $MACOS_SIGN_IDENTITY"
  # de dentro para fora: bibliotecas e executáveis primeiro, depois o .app
  find "$app/Contents" -type f \( -name "*.so" -o -name "*.dylib" -o -perm -111 \) -print0 |
    while IFS= read -r -d '' file; do
      if file "$file" | grep -q "Mach-O"; then
        codesign --force --timestamp --options runtime --entitlements macos/entitlements.plist \
          --sign "$MACOS_SIGN_IDENTITY" "$file"
      fi
    done
  codesign --force --timestamp --options runtime --entitlements macos/entitlements.plist \
    --sign "$MACOS_SIGN_IDENTITY" "$app"
  codesign --verify --deep --strict --verbose=2 "$app"
fi

stage="dist-macos/dmg-stage"
rm -rf "$stage"
mkdir -p "$stage"
cp -R "$app" "$stage/"
ln -s /Applications "$stage/Applications"
if [[ "${PT2VHF_MACOS_LEGACY:-0}" == "1" ]]; then
  cp docs/INSTALL_MACOS_LEGACY.md "$stage/INSTALL_MACOS_LEGACY.md"
else
  cp docs/INSTALL_MACOS.md "$stage/INSTALL_MACOS.md"
fi
cp LICENSE "$stage/LICENSE"

dmg="dist-macos/PT2VHF_APRS_Client_macOS_${label}_v${version}.dmg"
hdiutil create -volname "PT2VHF APRS Client ${version}" -srcfolder "$stage" -ov -format UDZO "$dmg"

if [[ -n "${MACOS_SIGN_IDENTITY:-}" ]]; then
  codesign --force --timestamp --sign "$MACOS_SIGN_IDENTITY" "$dmg"
  if [[ -n "${MACOS_NOTARY_APPLE_ID:-}" && -n "${MACOS_NOTARY_PASSWORD:-}" && -n "${MACOS_NOTARY_TEAM_ID:-}" ]]; then
    xcrun notarytool submit "$dmg" --apple-id "$MACOS_NOTARY_APPLE_ID" --password "$MACOS_NOTARY_PASSWORD" \
      --team-id "$MACOS_NOTARY_TEAM_ID" --wait --timeout 30m
    xcrun stapler staple "$dmg"
    xcrun stapler validate "$dmg"
    spctl --assess --type open --context context:primary-signature --verbose=2 "$dmg"
  else
    echo "Aviso: DMG assinado, mas sem notarização (faltam MACOS_NOTARY_*)." >&2
  fi
fi

echo "Artefatos macOS:"
find dist-macos -maxdepth 1 -type f -print
