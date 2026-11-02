#!/usr/bin/env bash
# Compilação Catalina Intel. O ambiente macOS 10.15 real é OBRIGATÓRIO.
set -euo pipefail
cd "$(dirname "$0")/.."

test "$(uname -s)" = Darwin || { echo "Este build exige macOS" >&2; exit 1; }
test "$(uname -m)" = x86_64 || { echo "Este build exige Mac Intel x86_64" >&2; exit 1; }
os="$(sw_vers -productVersion)"
case "$os" in 10.15.*) ;; *) echo "Catalina 10.15.x obrigatório; detectado $os" >&2; exit 1;; esac

export PYTHON_BIN="${PYTHON_BIN:-python3.10}"
"$PYTHON_BIN" -c 'import sys,platform; assert sys.version_info[:2] == (3,10), sys.version; assert platform.machine() == "x86_64"'
export MACOSX_DEPLOYMENT_TARGET=10.15
export PT2VHF_MACOS_LEGACY=1
export VENV=.venv-build-macos-catalina
export MACOS_REQUIREMENTS=requirements-macos-legacy.txt

bash macos/build_macos.sh

version="$(tr -d '\r\n ' < VERSION)"
app="dist/PT2VHF APRS Client.app"
dmg="dist-macos/PT2VHF_APRS_Client_macOS_Intel_Legacy_v${version}.dmg"
test -f "$dmg"
min_os="$(/usr/libexec/PlistBuddy -c 'Print :LSMinimumSystemVersion' "$app/Contents/Info.plist")"
test "$min_os" = "10.15.0" || { echo "Info.plist incorreto: $min_os" >&2; exit 1; }
bin="$app/Contents/MacOS/PT2VHF_APRS_Client"
file "$bin" | grep -q "x86_64" || { echo "Binário não é Intel x86_64" >&2; exit 1; }
hdiutil verify "$dmg"

# Smoke test real no host Catalina com sessão gráfica (nunca simulado por alteração de plist).
open -n "$app"
sleep 12
if ! pgrep -f 'PT2VHF_APRS_Client' >/dev/null; then
  echo "Aplicativo não permaneceu aberto no Catalina após 12s" >&2
  exit 1
fi
pkill -f 'PT2VHF_APRS_Client' || true

"$PYTHON_BIN" - "$dmg" "$os" "$version" <<'PY'
import hashlib,json,sys
from pathlib import Path
f=Path(sys.argv[1]); h=hashlib.sha256(f.read_bytes()).hexdigest()
out={"build_os":sys.argv[2],"architecture":"x86_64","platform":"macos-x64-legacy",
     "version":sys.argv[3],"filename":f.name,"size":f.stat().st_size,
     "sha256":h,"bundle_min_os":"10.15.0","gui_smoke":"passed",
     "source":"native-catalina-self-hosted"}
Path("dist-macos/catalina-verification.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out))
PY
