#!/usr/bin/env bash
# Instalador do Light Gun Joypad para Linux.
#  - ambiente Python próprio em ~/.local/share/lightgun-joypad
#  - comando ~/.local/bin/lightgun-joypad
#  - aplicativo que abre sozinho (na bandeja) quando você entra no Linux
#  - atalho "Light Gun Joypad" no menu de aplicativos
#  - correção do Bluetooth/permissões (pede a senha de administrador 1 vez)
set -euo pipefail
SRC="$(cd "$(dirname "$0")/../.." && pwd)"
APP="$HOME/.local/share/lightgun-joypad"
VENV="$APP/venv"
BIN="$HOME/.local/bin"
say() { printf '\n\033[1;32m==>\033[0m %s\n' "$*"; }

command -v python3 >/dev/null || { echo "python3 não encontrado. Instale o Python 3.9+."; exit 1; }
python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' || { echo "precisa do Python 3.9 ou mais novo"; exit 1; }

# 1) Sistema: Bluetooth aceitar Joy-Con + regras udev (só se ainda faltar)
need_sys=0
grep -qE '^\s*ClassicBondedOnly\s*=\s*false' /etc/bluetooth/input.conf 2>/dev/null || need_sys=1
grep -q 054c /etc/udev/rules.d/70-lightgun-joypad.rules 2>/dev/null || need_sys=1
if [ "$need_sys" = 1 ] && [ -z "${LGJ_SKIP_SYSTEM:-}" ]; then
  say "Ajustando Bluetooth e permissões (vai pedir sua senha)"
  if [ "$(id -u)" -eq 0 ]; then "$SRC/scripts/fix-linux-joycon.sh"
  elif command -v pkexec >/dev/null && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] && [ ! -t 0 ]; then pkexec "$SRC/scripts/fix-linux-joycon.sh"
  else sudo "$SRC/scripts/fix-linux-joycon.sh"; fi
else
  say "Bluetooth e permissões já estão ok"
fi

# 2) Ambiente Python isolado
say "Criando ambiente Python em $APP"
mkdir -p "$APP"
if ! python3 -m venv --clear "$VENV" >/dev/null 2>&1; then
  # Ubuntu/Debian sem python3-venv: cria sem pip e instala o pip oficial
  rm -rf "$VENV"
  python3 -m venv --without-pip "$VENV"
  TMP="$(mktemp -d)"
  curl -fsSL https://bootstrap.pypa.io/get-pip.py -o "$TMP/get-pip.py"
  "$VENV/bin/python" -I "$TMP/get-pip.py" -q
  rm -rf "$TMP"
fi
"$VENV/bin/python" -m pip install -q --upgrade pip
say "Instalando o programa"
"$VENV/bin/python" -m pip install -q "$SRC[sim]"
install -m 0644 "$SRC/installer/icon.svg" "$APP/icon.svg"
install -m 0755 "$SRC/installer/linux/uninstall.sh" "$APP/uninstall.sh"

# 3) Comando no PATH
mkdir -p "$BIN"
cat > "$BIN/lightgun-joypad" <<EOS
#!/usr/bin/env bash
exec "$VENV/bin/lightgun-joypad" "\$@"
EOS
chmod +x "$BIN/lightgun-joypad"

# 4) Atalhos: menu de aplicativos + início automático (na bandeja)
mkdir -p "$HOME/.local/share/applications" "$HOME/.config/autostart"
cat > "$HOME/.local/share/applications/lightgun-joypad.desktop" <<EOS
[Desktop Entry]
Type=Application
Name=Light Gun Joypad
Comment=Joy-Con / Pro Controller como light gun
Exec=$BIN/lightgun-joypad gui
Icon=$APP/icon.svg
Terminal=false
Categories=Game;Utility;
Keywords=lightgun;joycon;gyro;mira;
StartupWMClass=lightgun-joypad
EOS
cat > "$HOME/.local/share/applications/lightgun-joypad-sim.desktop" <<EOS
[Desktop Entry]
Type=Application
Name=Light Gun Joypad — Simulador
Comment=Estande de tiro com o Joy-Con (feche o aplicativo principal antes)
Exec=$BIN/lightgun-joypad sim
Icon=$APP/icon.svg
Terminal=false
Categories=Game;
EOS
cat > "$HOME/.config/autostart/lightgun-joypad.desktop" <<EOS
[Desktop Entry]
Type=Application
Name=Light Gun Joypad
Comment=Light gun na bandeja do sistema
Exec=$BIN/lightgun-joypad gui --tray
Icon=$APP/icon.svg
Terminal=false
X-GNOME-Autostart-enabled=true
EOS
command -v update-desktop-database >/dev/null && update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

# Versões antigas usavam um serviço systemd + painel no navegador: remove.
if [ -f "$HOME/.config/systemd/user/lightgun-joypad.service" ]; then
  systemctl --user disable --now lightgun-joypad.service >/dev/null 2>&1 || true
  rm -f "$HOME/.config/systemd/user/lightgun-joypad.service"
  systemctl --user daemon-reload || true
fi

# 5) Abre agora (se já estiver aberto, só reinicia com a versão nova)
pkill -f "^$VENV/bin/python" 2>/dev/null || true
sleep 0.5
if [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
  nohup "$BIN/lightgun-joypad" gui >/dev/null 2>&1 &
fi

say "Instalado!"
cat <<EOS
  • O aplicativo já está aberto e vai iniciar sozinho (na bandeja) quando você entrar no Linux.
  • Abrir: menu de aplicativos → "Light Gun Joypad" (ou clique no ícone da mira na bandeja).
  • Primeiro passo: Calibrar → mire no centro e nos 4 cantos e aperte o ZR.
  • Desinstalar: $APP/uninstall.sh
EOS
case ":$PATH:" in *":$BIN:"*) ;; *) echo "  • Obs.: adicione $BIN ao PATH para usar o comando 'lightgun-joypad' no terminal.";; esac
