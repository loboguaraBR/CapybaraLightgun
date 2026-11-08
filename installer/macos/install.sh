#!/bin/bash
# Instalador do Light Gun Joypad para macOS (não precisa de administrador).
#  - ambiente Python em ~/Library/Application Support/LightGunJoypad
#  - aplicativo ~/Applications/Light Gun Joypad.app
#  - abre sozinho no login (na barra de menus), via LaunchAgent
set -euo pipefail
SRC="$(cd "$(dirname "$0")/../.." && pwd)"
APP_SUPPORT="$HOME/Library/Application Support/LightGunJoypad"
VENV="$APP_SUPPORT/venv"
APP="$HOME/Applications/Light Gun Joypad.app"
AGENT="$HOME/Library/LaunchAgents/com.lightgunjoypad.app.plist"
say() { printf '\n\033[1;32m==>\033[0m %s\n' "$*"; }

# 1) Python 3.9+
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3 /usr/local/bin/python3 /opt/homebrew/bin/python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
    PY="$(command -v "$c")"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.9+ não encontrado."
  echo "Instale pelo site https://www.python.org/downloads/macos/ (ou: brew install python) e rode de novo."
  exit 1
fi
say "Python: $PY ($("$PY" -V))"

# 2) Ambiente e programa
say "Parando versão anterior (se houver)"
launchctl unload "$AGENT" >/dev/null 2>&1 || true
pkill -f "$VENV/bin/python" >/dev/null 2>&1 || true

say "Criando ambiente em $APP_SUPPORT"
mkdir -p "$APP_SUPPORT"
"$PY" -m venv --clear "$VENV"
"$VENV/bin/python" -m pip install -q --upgrade pip
say "Instalando o programa (PyQt5, SDL2, hidapi, pygame)"
"$VENV/bin/python" -m pip install -q "$SRC[sim]"
install -m 0755 "$SRC/installer/macos/uninstall.sh" "$APP_SUPPORT/uninstall.sh"

# 3) Aplicativo (.app) — as permissões do macOS ficam com o nome dele
say "Criando $APP"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cat > "$APP/Contents/MacOS/LightGunJoypad" <<EOS
#!/bin/bash
exec "$VENV/bin/python" -m lightgun_joypad gui "\$@"
EOS
chmod +x "$APP/Contents/MacOS/LightGunJoypad"
cat > "$APP/Contents/Info.plist" <<EOS
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Light Gun Joypad</string>
  <key>CFBundleDisplayName</key><string>Light Gun Joypad</string>
  <key>CFBundleIdentifier</key><string>com.lightgunjoypad.app</string>
  <key>CFBundleExecutable</key><string>LightGunJoypad</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>$("$VENV/bin/python" -c 'import lightgun_joypad as m; print(m.__version__)')</string>
  <key>LSMinimumSystemVersion</key><string>10.15</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
EOS
# Ícone: desenhado pelo próprio programa e convertido com as ferramentas do macOS
ICONSET="$(mktemp -d)/icon.iconset"
mkdir -p "$ICONSET"
QT_QPA_PLATFORM=offscreen "$VENV/bin/python" - "$ICONSET" <<'PYEOF' || true
import sys
from PyQt5 import QtWidgets
app = QtWidgets.QApplication([])
from lightgun_joypad.gui import GREEN, make_icon
icon = make_icon(GREEN)
for s in (16, 32, 128, 256, 512):
    icon.pixmap(s, s).save(f"{sys.argv[1]}/icon_{s}x{s}.png")
    icon.pixmap(2 * s, 2 * s).save(f"{sys.argv[1]}/icon_{s}x{s}@2x.png")
PYEOF
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/icon.icns" 2>/dev/null || true
touch "$APP"

# 4) Abrir no login (escondido na barra de menus)
say "Ativando a abertura automática no login"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$AGENT" <<EOS
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.lightgunjoypad.app</string>
  <key>ProgramArguments</key>
  <array><string>/usr/bin/open</string><string>-g</string><string>-a</string><string>$APP</string>
         <string>--args</string><string>--tray</string></array>
  <key>RunAtLoad</key><true/>
</dict></plist>
EOS
launchctl load -w "$AGENT" >/dev/null 2>&1 || true

say "Autoteste"
"$VENV/bin/python" -m lightgun_joypad selftest || true

open "$APP"
cat <<EOS

Instalado!
 • O aplicativo "Light Gun Joypad" está em ~/Applications e abre sozinho no login (ícone da mira na barra de menus).
 • IMPORTANTE: libere o aplicativo em Ajustes do Sistema → Privacidade e Segurança:
     - Acessibilidade (para mover o cursor e clicar)
     - Monitoramento de Entrada (para ler o controle)
   O botão amarelo "Liberar permissões do macOS" no aplicativo abre essas telas.
   Depois de liberar, encerre e abra o aplicativo de novo.
 • Pareie o Joy-Con / DualSense em Ajustes do Sistema → Bluetooth.
 • Desinstalar: "$APP_SUPPORT/uninstall.sh"
EOS
