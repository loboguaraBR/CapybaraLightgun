#!/usr/bin/env bash
# Corrige o necessário para o Joy-Con funcionar no Linux (rodar como root):
#  1) BlueZ: aceitar a conexão HID de controles sem "bonding" (Joy-Con)
#  2) regras udev: acesso ao IMU/botões e ao /dev/uinput sem root
#  3) módulos hid-nintendo e uinput
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "rode com: sudo $0"; exit 1; }
cd "$(dirname "$0")/.."

CONF=/etc/bluetooth/input.conf
changed=0
if ! grep -qE '^\s*ClassicBondedOnly\s*=\s*false' "$CONF" 2>/dev/null; then
  if [ -f "$CONF" ]; then
    [ -f "$CONF.bak-lightgun" ] || cp "$CONF" "$CONF.bak-lightgun"
    if grep -qE '^\s*#?\s*ClassicBondedOnly' "$CONF"; then
      sed -i -E 's/^\s*#?\s*ClassicBondedOnly\s*=.*/ClassicBondedOnly=false/' "$CONF"
    else
      sed -i -E '0,/^\[General\]/s//[General]\nClassicBondedOnly=false/' "$CONF"
    fi
  else
    printf '[General]\nClassicBondedOnly=false\n' > "$CONF"
  fi
  changed=1
fi
echo "BlueZ: $(grep ClassicBondedOnly "$CONF")"

install -m 0644 udev/70-lightgun-joypad.rules /etc/udev/rules.d/
echo uinput > /etc/modules-load.d/lightgun-joypad.conf
modprobe uinput || true
modprobe hid_nintendo || true
udevadm control --reload-rules
udevadm trigger

if [ "$changed" = 1 ]; then
  systemctl daemon-reload || true
  systemctl restart bluetooth
  # Em alguns notebooks o reinício deixa o Bluetooth bloqueado/desligado.
  sleep 1
  rfkill unblock bluetooth 2>/dev/null || true
  for _ in 1 2 3 4 5; do
    bluetoothctl power on >/dev/null 2>&1 && break
    sleep 1
  done
  echo
  echo "Bluetooth reiniciado. Aperte um botão do Joy-Con para ele reconectar."
  echo "Se não reconectar: remova o Joy-Con nas configurações de Bluetooth, segure o botão de sync e pareie de novo."
fi
echo "Pronto."
