#!/usr/bin/env bash
# Remove o Capybara Lightgun (mantém sua configuração em ~/.config/capybara-lightgun).
set -u
systemctl --user disable --now capybara-lightgun.service 2>/dev/null
rm -f "$HOME/.config/systemd/user/capybara-lightgun.service"
systemctl --user daemon-reload 2>/dev/null
pkill -f "^$HOME/.local/share/capybara-lightgun/venv/bin/python" 2>/dev/null
rm -f "$HOME/.config/autostart/capybara-lightgun.desktop"
rm -f "$HOME/.local/bin/capybara-lightgun" \
      "$HOME/.local/share/applications/capybara-lightgun.desktop" \
      "$HOME/.local/share/applications/capybara-lightgun-sim.desktop"
rm -rf "$HOME/.local/share/capybara-lightgun"
echo "Capybara Lightgun removido. Configuração mantida em ~/.config/capybara-lightgun"
echo "(as regras de sistema ficam em /etc/udev/rules.d/70-capybara-lightgun.rules e /etc/bluetooth/input.conf)"
