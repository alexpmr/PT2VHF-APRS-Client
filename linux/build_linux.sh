#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV=".venv-build-linux"

if [[ ! -d "$VENV" ]]; then
  "$PYTHON_BIN" -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r requirements-linux.txt
"$VENV/bin/python" -m pytest -q

rm -rf build dist dist-linux
mkdir -p dist-linux
"$VENV/bin/pyinstaller" --noconfirm --clean linux/PT2VHF_APRS_Client_Linux.spec
"$VENV/bin/cyclonedx-py" environment --spec-version 1.6 --output-format JSON --output-file dist-linux/SBOM-Linux.cdx.json
"$VENV/bin/pip-licenses" --format=plain-vertical --with-license-file --no-license-path --output-file=dist-linux/THIRD_PARTY_LICENSES_Linux.txt

version="$(tr -d '\r\n ' < VERSION)"
mkdir -p dist-linux/package
cp dist/PT2VHF_APRS_Client_Linux_x86_64 "dist-linux/package/PT2VHF_APRS_Client_Linux_x86_64_v${version}"
cp docs/INSTALL_LINUX.md dist-linux/package/INSTALL_LINUX.md
cp LICENSE dist-linux/package/LICENSE
cp THIRD_PARTY_NOTICES.md dist-linux/package/THIRD_PARTY_NOTICES.md
cp dist-linux/SBOM-Linux.cdx.json dist-linux/package/SBOM-Linux.cdx.json
cp dist-linux/THIRD_PARTY_LICENSES_Linux.txt dist-linux/package/THIRD_PARTY_LICENSES_Linux.txt
tar -czf "dist-linux/PT2VHF_APRS_Client_Linux_x86_64_v${version}.tar.gz" -C dist-linux/package .

appdir="dist-linux/AppDir"
mkdir -p "$appdir/usr/bin" "$appdir/usr/share/applications" "$appdir/usr/share/icons/hicolor/scalable/apps"
cp dist/PT2VHF_APRS_Client_Linux_x86_64 "$appdir/usr/bin/pt2vhf-aprs-client"
chmod 0755 "$appdir/usr/bin/pt2vhf-aprs-client"
cp pt2vhf_aprs/static/img/app_logo.svg "$appdir/usr/share/icons/hicolor/scalable/apps/pt2vhf-aprs-client.svg"
cp pt2vhf_aprs/static/img/app_logo.svg "$appdir/pt2vhf-aprs-client.svg"
cat > "$appdir/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/pt2vhf-aprs-client" "$@"
EOF
chmod 0755 "$appdir/AppRun"
cat > "$appdir/pt2vhf-aprs-client.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=PT2VHF APRS Client
Comment=Cliente APRS-IS
Exec=pt2vhf-aprs-client
Icon=pt2vhf-aprs-client
Terminal=false
Categories=Network;HamRadio;
EOF
cp "$appdir/pt2vhf-aprs-client.desktop" "$appdir/usr/share/applications/pt2vhf-aprs-client.desktop"

if command -v curl >/dev/null 2>&1; then
  curl -fsSL -o dist-linux/appimagetool.AppImage \
    https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x dist-linux/appimagetool.AppImage
  ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 dist-linux/appimagetool.AppImage \
    "$appdir" "dist-linux/PT2VHF_APRS_Client_x86_64_v${version}.AppImage"
fi

if command -v dpkg-deb >/dev/null 2>&1; then
  root="dist-linux/deb-root"
  mkdir -p "$root/DEBIAN" "$root/usr/local/bin" "$root/usr/share/applications" "$root/usr/share/doc/pt2vhf-aprs-client"
  cp dist/PT2VHF_APRS_Client_Linux_x86_64 "$root/usr/local/bin/pt2vhf-aprs-client"
  chmod 0755 "$root/usr/local/bin/pt2vhf-aprs-client"
  cp docs/INSTALL_LINUX.md "$root/usr/share/doc/pt2vhf-aprs-client/INSTALL_LINUX.md"
  cp LICENSE "$root/usr/share/doc/pt2vhf-aprs-client/LICENSE"
  cat > "$root/DEBIAN/control" <<EOF
Package: pt2vhf-aprs-client
Version: ${version}
Section: hamradio
Priority: optional
Architecture: amd64
Maintainer: Alex, PT2VHF
Description: Cliente APRS-IS com mapa, mensagens, estacoes, log e topologia observada.
 A interface usa janela integrada quando o ambiente Linux oferece um backend
 WebView compativel e utiliza o navegador local como fallback.
EOF
  cat > "$root/usr/share/applications/pt2vhf-aprs-client.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=PT2VHF APRS Client
Comment=Cliente APRS-IS
Exec=/usr/local/bin/pt2vhf-aprs-client
Terminal=false
Categories=Network;HamRadio;
EOF
  dpkg-deb --build "$root" "dist-linux/pt2vhf-aprs-client_${version}_amd64.deb"
fi

echo "Artefatos Linux:"
find dist-linux -maxdepth 1 -type f -printf '%f\n'
