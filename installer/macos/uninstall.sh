#!/bin/bash
# Remove o Light Gun Joypad (mantém a configuração em ~/Library/Application Support/lightgun-joypad).
APP_SUPPORT="$HOME/Library/Application Support/LightGunJoypad"
AGENT="$HOME/Library/LaunchAgents/com.lightgunjoypad.app.plist"
launchctl unload "$AGENT" >/dev/null 2>&1
rm -f "$AGENT"
pkill -f "$APP_SUPPORT/venv/bin/python" >/dev/null 2>&1
rm -rf "$HOME/Applications/Light Gun Joypad.app" "$APP_SUPPORT"
echo "Light Gun Joypad removido."
echo "As permissões em Privacidade e Segurança podem ser removidas à mão (botão −)."
