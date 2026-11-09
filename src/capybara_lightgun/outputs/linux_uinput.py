"""Linux: cria a light gun virtual via /dev/uinput.

Dois jeitos (output_target):
- "mouse":    dispositivo absoluto comum — a área de trabalho o usa como mouse.
- "lightgun": dispositivo "Capybara Lightgun (driver)" que a área de trabalho
              IGNORA (regra udev LIBINPUT_IGNORE_DEVICE; no X11 também
              `xinput disable`). O cursor e o touchpad ficam livres; emuladores
              que leem o evdev direto (RetroArch com driver udev) usam a arma.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time

from evdev import AbsInfo, UInput, ecodes as e

MAX = 65535
DRIVER_NAME = "Capybara Lightgun (driver)"
DRIVER_PRODUCT = 0x4C4A
MOUSE_NAME = "Capybara Lightgun"
MOUSE_PRODUCT = 0x4C47


def _xinput_disable(name: str) -> None:
    """X11: tira o dispositivo do cursor (sem root). No-op fora do X11."""
    if not os.environ.get("DISPLAY") or not shutil.which("xinput"):
        return
    for _ in range(40):
        try:
            out = subprocess.run(["xinput", "list"], capture_output=True, text=True, timeout=2).stdout
        except Exception:
            return
        ids = [ln.split("id=")[1].split()[0] for ln in out.splitlines() if name in ln and "id=" in ln]
        if ids:
            for i in ids:
                subprocess.run(["xinput", "disable", i], capture_output=True, timeout=2)
            return
        time.sleep(0.1)

_ALIASES = {
    "esc": "ESC", "escape": "ESC", "enter": "ENTER", "return": "ENTER", "space": "SPACE",
    "tab": "TAB", "backspace": "BACKSPACE", "up": "UP", "down": "DOWN", "left": "LEFT",
    "right": "RIGHT", "shift": "LEFTSHIFT", "ctrl": "LEFTCTRL", "control": "LEFTCTRL",
    "alt": "LEFTALT", "pause": "PAUSE",
}

_MOUSE = {"left": e.BTN_LEFT, "right": e.BTN_RIGHT, "middle": e.BTN_MIDDLE}


def keycode(name: str) -> int:
    n = _ALIASES.get(name.lower(), name.upper())
    code = e.ecodes.get("KEY_" + n)
    if code is None:
        raise ValueError(f"tecla desconhecida: {name}")
    return code


class UInputOutput:

    def __init__(self, region, keys, target: str = "mouse"):
        self.region = [float(v) for v in region]
        self.target = target
        driver = target == "lightgun"
        self.name = "virtual light gun (driver, cursor free)" if driver else "system mouse (absolute)"
        absinfo = AbsInfo(value=MAX // 2, min=0, max=MAX, fuzz=0, flat=0, resolution=0)
        try:
            self.mouse = UInput(
                {e.EV_KEY: list(_MOUSE.values()), e.EV_ABS: [(e.ABS_X, absinfo), (e.ABS_Y, absinfo)]},
                name=DRIVER_NAME if driver else MOUSE_NAME,
                vendor=0x1209,
                product=DRIVER_PRODUCT if driver else MOUSE_PRODUCT,
                version=1,
                bustype=e.BUS_USB,
            )
        except Exception as exc:  # permissão de /dev/uinput
            raise OSError(
                f"não consegui criar o mouse virtual ({exc}). Rode scripts/install-linux.sh "
                "para instalar a regra udev de /dev/uinput (ou teste com sudo)."
            ) from exc
        from ..config import KEY_NAMES

        # Registra todas as teclas suportadas: o remapeamento muda ao vivo.
        self.keys = {}
        for k in list(KEY_NAMES) + list(keys):
            try:
                self.keys[k] = keycode(k)
            except ValueError:
                pass
        self.kbd = UInput({e.EV_KEY: sorted(set(self.keys.values()))}, name="Capybara Lightgun Keys",
                          vendor=0x1209, product=0x4C48, version=1, bustype=e.BUS_USB)
        self.rel = None  # criado só se o modo relativo for usado
        # No modo driver, só envia movimento depois que a área de trabalho
        # deixou de usar o dispositivo (nunca mexe no cursor).
        self._ready = threading.Event()
        if driver:
            def hide():
                try:
                    _xinput_disable(DRIVER_NAME)
                finally:
                    self._ready.set()
            threading.Thread(target=hide, daemon=True).start()
        else:
            self._ready.set()
        self._last = None

    def move(self, x: float, y: float) -> None:
        if not self._ready.is_set():
            return
        r = self.region
        ax = int(round((r[0] + x * (r[2] - r[0])) * MAX))
        ay = int(round((r[1] + y * (r[3] - r[1])) * MAX))
        ax = min(max(ax, 0), MAX)
        ay = min(max(ay, 0), MAX)
        if (ax, ay) == self._last:
            return
        self._last = (ax, ay)
        self.mouse.write(e.EV_ABS, e.ABS_X, ax)
        self.mouse.write(e.EV_ABS, e.ABS_Y, ay)
        self.mouse.syn()

    def move_rel(self, dx: int, dy: int) -> None:
        if self.rel is None:
            self.rel = UInput({e.EV_KEY: list(_MOUSE.values()), e.EV_REL: [e.REL_X, e.REL_Y]},
                              name="Capybara Lightgun (relative)", vendor=0x1209, product=0x4C49,
                              version=1, bustype=e.BUS_USB)
        if dx:
            self.rel.write(e.EV_REL, e.REL_X, dx)
        if dy:
            self.rel.write(e.EV_REL, e.REL_Y, dy)
        self.rel.syn()
        self._last = None

    def button(self, name: str, down: bool) -> None:
        if not self._ready.is_set():
            return
        self.mouse.write(e.EV_KEY, _MOUSE[name], 1 if down else 0)
        self.mouse.syn()

    def key(self, name: str, down: bool) -> None:
        if name not in self.keys:
            return
        self.kbd.write(e.EV_KEY, self.keys[name], 1 if down else 0)
        self.kbd.syn()

    def close(self) -> None:
        for d in (self.mouse, self.kbd, self.rel):
            if d is not None:
                d.close()
