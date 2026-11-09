"""DualShock 4 (PS4) e DualSense (PS5) por HID cru (Windows, ou Linux sem driver).

EXPERIMENTAL. Lê giroscópio, acelerômetro e botões dos relatórios de entrada:
- DS4: USB 0x01 / Bluetooth 0x11 (ativado lendo o feature report 0x02)
- DS5: USB 0x01 / Bluetooth 0x31 (ativado lendo o feature report 0x05)
Usa a escala nominal dos sensores; o bias é estimado pelo programa e a
calibração da tela absorve diferenças de escala.
"""
from __future__ import annotations

import struct
import time

from .base import ButtonState, DeviceLost, ImuSample, NoDeviceFound
from .linux_evdev_axes import to_lightgun_axes

VENDOR = 0x054C
PIDS = {0x05C4: "ps4", 0x09CC: "ps4", 0x0BA0: "ps4", 0x0CE6: "ps5", 0x0DF2: "ps5"}
GYRO_DPS_PER_LSB = 1 / 16.0
ACCEL_G_PER_LSB = 1 / 8192.0

_HAT = {0: {"UP"}, 1: {"UP", "RIGHT"}, 2: {"RIGHT"}, 3: {"DOWN", "RIGHT"}, 4: {"DOWN"},
        5: {"DOWN", "LEFT"}, 6: {"LEFT"}, 7: {"UP", "LEFT"}}


def _buttons(b0: int, b1: int, b2: int) -> frozenset:
    names = set(_HAT.get(b0 & 0x0F, ()))
    for mask, n in ((0x10, "Y"), (0x20, "B"), (0x40, "A"), (0x80, "X")):  # □ ✕ ○ △
        if b0 & mask:
            names.add(n)
    for mask, n in ((0x01, "L"), (0x02, "R"), (0x04, "ZL"), (0x08, "ZR"), (0x10, "MINUS"),
                    (0x20, "PLUS"), (0x40, "LSTICK"), (0x80, "RSTICK")):
        if b1 & mask:
            names.add(n)
    if b2 & 0x01:
        names.add("HOME")
    if b2 & 0x02:
        names.add("CAPTURE")  # clique do touchpad
    return frozenset(names)


def parse_report(data, kind: str):
    """Retorna (botões, gyro_dps, accel_g) na convenção interna, ou None."""
    rid = data[0]
    if kind == "ps4":
        if rid == 0x01 and len(data) >= 25:
            base = 1
        elif rid == 0x11 and len(data) >= 27:
            base = 3
        else:
            return None
        b0, b1, b2 = data[base + 4], data[base + 5], data[base + 6]
        g = struct.unpack_from("<3h", bytes(data[base + 12:base + 18]))
        a = struct.unpack_from("<3h", bytes(data[base + 18:base + 24]))
    else:
        if rid == 0x01 and len(data) >= 28:
            base = 1
        elif rid == 0x31 and len(data) >= 29:
            base = 2
        else:
            return None
        b0, b1, b2 = data[base + 7], data[base + 8], data[base + 9]
        g = struct.unpack_from("<3h", bytes(data[base + 15:base + 21]))
        a = struct.unpack_from("<3h", bytes(data[base + 21:base + 27]))
    gyro = to_lightgun_axes("playstation", tuple(v * GYRO_DPS_PER_LSB for v in g))
    accel = to_lightgun_axes("playstation", tuple(v * ACCEL_G_PER_LSB for v in a))
    return _buttons(b0, b1, b2), gyro, accel


def list_devices() -> list:
    from .switch_hid import _hid

    out = []
    for d in _hid().enumerate(VENDOR, 0):
        kind = PIDS.get(d.get("product_id"))
        if kind:
            out.append({"kind": kind, "path": d["path"], "name": d.get("product_string") or kind})
    return out


class PsHidSource:
    family = "playstation"

    def __init__(self, dev, info):
        self.dev = dev
        self.kind = info["kind"]
        self.name = f"{info['name']} (hidapi, experimental)"

    @classmethod
    def open(cls, prefer: str = "auto"):
        from .switch_hid import _hid

        devs = list_devices()
        if prefer in ("ps4", "ps5"):
            devs = [d for d in devs if d["kind"] == prefer] or devs
        if not devs:
            raise NoDeviceFound("nenhum DualShock 4 / DualSense via HID")
        info = devs[0]
        dev = _hid().device()
        dev.open_path(info["path"])
        # Ativa os relatórios completos (com sensores) no Bluetooth.
        for rid, size in ((0x02, 37), (0x05, 41)):
            try:
                dev.get_feature_report(rid, size)
            except Exception:
                pass
        dev.set_nonblocking(0)
        return cls(dev, info)

    def events(self):
        last_buttons = None
        last_t = None
        while True:
            try:
                data = self.dev.read(128, 200)
            except (OSError, ValueError) as exc:
                raise DeviceLost(str(exc)) from exc
            now = time.monotonic()
            if not data:
                if last_t is not None and now - last_t > 2.0:
                    raise DeviceLost("controle parou de enviar dados")
                continue
            r = parse_report(data, self.kind)
            if r is None:
                continue
            buttons, gyro, accel = r
            dt = 0.004 if last_t is None else min(max(now - last_t, 0.001), 0.1)
            last_t = now
            if buttons != last_buttons:
                last_buttons = buttons
                yield ButtonState(buttons)
            yield ImuSample(gyro, accel, dt)

    def close(self) -> None:
        try:
            self.dev.close()
        except Exception:
            pass
