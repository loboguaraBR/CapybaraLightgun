#!/bin/bash
# Remove o Capybara Lightgun (mantém a configuração em ~/Library/Application Support/capybara-lightgun).
APP_SUPPORT="$HOME/Library/Application Support/CapybaraLightgun"
AGENT="$HOME/Library/LaunchAgents/com.capybaralightgun.app.plist"
launchctl unload "$AGENT" >/dev/null 2>&1
rm -f "$AGENT"
pkill -f "$APP_SUPPORT/venv/bin/python" >/dev/null 2>&1
rm -rf "$HOME/Applications/Capybara Lightgun.app" "$APP_SUPPORT"
echo "Capybara Lightgun removido."
echo "As permissões em Privacidade e Segurança podem ser removidas à mão (botão −)."
