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
machine="${PT2VHF_LINUX_ARCH:-$(uname -m)}"
case "$machine" in
  x86_64|amd64)
    arch="x86_64"
    deb_arch="amd64"
    appimage_arch="x86_64"
    ;;
  aarch64|arm64)
    arch="arm64"
    deb_arch="arm64"
    appimage_arch="aarch64"
    ;;
  *)
    echo "Arquitetura Linux não suportada: $machine" >&2
    exit 2
    ;;
esac
binary_src="dist/PT2VHF_APRS_Client_Linux_x86_64"
binary_name="PT2VHF_APRS_Client_Linux_${arch}_v${version}"
mkdir -p dist-linux/package
cp "$binary_src" "dist-linux/package/$binary_name"
cp docs/INSTALL_LINUX.md dist-linux/package/INSTALL_LINUX.md
cp LICENSE dist-linux/package/LICENSE
cp THIRD_PARTY_NOTICES.md dist-linux/package/THIRD_PARTY_NOTICES.md
cp dist-linux/SBOM-Linux.cdx.json dist-linux/package/SBOM-Linux.cdx.json
cp dist-linux/THIRD_PARTY_LICENSES_Linux.txt dist-linux/package/THIRD_PARTY_LICENSES_Linux.txt
tar -czf "dist-linux/PT2VHF_APRS_Client_Linux_${arch}_v${version}.tar.gz" -C dist-linux/package .

appdir="dist-linux/AppDir"
mkdir -p "$appdir/usr/bin" "$appdir/usr/share/applications" "$appdir/usr/share/icons/hicolor/256x256/apps"
cp "$binary_src" "$appdir/usr/bin/pt2vhf-aprs-client"
chmod 0755 "$appdir/usr/bin/pt2vhf-aprs-client"

# Ícone Linux simplificado; logomarca oficial preservada em
# pt2vhf_aprs/static/img/app_logo.png para a interface e o manual.
"$VENV/bin/python" - <<'PY'
from pathlib import Path
from tools.compact_icon import render_compact_icon
dst = Path("dist-linux/pt2vhf-aprs-client.png")
render_compact_icon(256).save(dst)
PY
cp dist-linux/pt2vhf-aprs-client.png "$appdir/usr/share/icons/hicolor/256x256/apps/pt2vhf-aprs-client.png"
cp dist-linux/pt2vhf-aprs-client.png "$appdir/pt2vhf-aprs-client.png"
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
    https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${appimage_arch}.AppImage
  chmod +x dist-linux/appimagetool.AppImage
  ARCH="$appimage_arch" APPIMAGE_EXTRACT_AND_RUN=1 dist-linux/appimagetool.AppImage \
    "$appdir" "dist-linux/PT2VHF_APRS_Client_${arch}_v${version}.AppImage"
fi

if command -v dpkg-deb >/dev/null 2>&1; then
  root="dist-linux/deb-root"
  mkdir -p "$root/DEBIAN" "$root/usr/local/bin" "$root/usr/share/applications" "$root/usr/share/doc/pt2vhf-aprs-client" "$root/usr/share/icons/hicolor/256x256/apps"
  cp "$binary_src" "$root/usr/local/bin/pt2vhf-aprs-client"
  chmod 0755 "$root/usr/local/bin/pt2vhf-aprs-client"
  cp docs/INSTALL_LINUX.md "$root/usr/share/doc/pt2vhf-aprs-client/INSTALL_LINUX.md"
  cp LICENSE "$root/usr/share/doc/pt2vhf-aprs-client/LICENSE"
  cp dist-linux/pt2vhf-aprs-client.png "$root/usr/share/icons/hicolor/256x256/apps/pt2vhf-aprs-client.png"
  cat > "$root/DEBIAN/control" <<EOF
Package: pt2vhf-aprs-client
Version: ${version}
Section: hamradio
Priority: optional
Architecture: ${deb_arch}
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
Icon=pt2vhf-aprs-client
Terminal=false
Categories=Network;HamRadio;
EOF
  dpkg-deb --build "$root" "dist-linux/pt2vhf-aprs-client_${version}_${deb_arch}.deb"
fi

echo "Artefatos Linux:"
find dist-linux -maxdepth 1 -type f -printf '%f\n'
