#!/usr/bin/env bash
# Remove o Light Gun Joypad (mantém sua configuração em ~/.config/lightgun-joypad).
set -u
systemctl --user disable --now lightgun-joypad.service 2>/dev/null
rm -f "$HOME/.config/systemd/user/lightgun-joypad.service"
systemctl --user daemon-reload 2>/dev/null
pkill -f "^$HOME/.local/share/lightgun-joypad/venv/bin/python" 2>/dev/null
rm -f "$HOME/.config/autostart/lightgun-joypad.desktop"
rm -f "$HOME/.local/bin/lightgun-joypad" \
      "$HOME/.local/share/applications/lightgun-joypad.desktop" \
      "$HOME/.local/share/applications/lightgun-joypad-sim.desktop"
rm -rf "$HOME/.local/share/lightgun-joypad"
echo "Light Gun Joypad removido. Configuração mantida em ~/.config/lightgun-joypad"
echo "(as regras de sistema ficam em /etc/udev/rules.d/70-lightgun-joypad.rules e /etc/bluetooth/input.conf)"
