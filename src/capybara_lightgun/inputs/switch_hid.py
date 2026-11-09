"""Protocolo HID do Joy-Con / Pro Controller (Windows, ou Linux sem hid-nintendo).

Fala direto com o controle: ativa o IMU (subcomando 0x40) e o modo de
relatório completo 0x30, que traz 3 amostras de IMU (~5 ms cada) a cada
~15 ms, além dos botões.
"""
from __future__ import annotations

import struct
import time

from .base import ButtonState, DeviceLost, ImuSample, NoDeviceFound

VENDOR = 0x057E
PIDS = {0x2006: "joycon-l", 0x2007: "joycon-r", 0x2009: "pro", 0x200E: "grip"}
_PREF_ORDER = ["pro", "joycon-r", "joycon-l", "grip"]

_RUMBLE_NEUTRAL = [0x00, 0x01, 0x40, 0x40, 0x00, 0x01, 0x40, 0x40]

# (byte, máscara, nome)
_BUTTONS = [
    (3, 0x01, "Y"), (3, 0x02, "X"), (3, 0x04, "B"), (3, 0x08, "A"),
    (3, 0x10, "SR"), (3, 0x20, "SL"), (3, 0x40, "R"), (3, 0x80, "ZR"),
    (4, 0x01, "MINUS"), (4, 0x02, "PLUS"), (4, 0x04, "RSTICK"), (4, 0x08, "LSTICK"),
    (4, 0x10, "HOME"), (4, 0x20, "CAPTURE"),
    (5, 0x01, "DOWN"), (5, 0x02, "UP"), (5, 0x04, "RIGHT"), (5, 0x08, "LEFT"),
    (5, 0x10, "SR"), (5, 0x20, "SL"), (5, 0x40, "L"), (5, 0x80, "ZL"),
]


def parse_buttons(data) -> frozenset:
    return frozenset(name for byte, mask, name in _BUTTONS if data[byte] & mask)


def parse_imu(data, kind: str, gyro_scale: float, accel_scale: float) -> list:
    """Retorna [(gyro_dps, accel_g)] x3 na convenção X=cano, Y=esq., Z=cima."""
    out = []
    for i in range(3):
        off = 13 + 12 * i
        ax, ay, az, gx, gy, gz = struct.unpack_from("<6h", bytes(data[off:off + 12]))
        if kind == "joycon-r":
            # IMU do Joy-Con direito é montado invertido (igual ao hid-nintendo).
            ay, az, gy, gz = -ay, -az, -gy, -gz
        out.append(
            (
                (gx * gyro_scale, gy * gyro_scale, gz * gyro_scale),
                (ax * accel_scale, ay * accel_scale, az * accel_scale),
            )
        )
    return out


def _hid():
    try:
        import hid  # pacote "hidapi" (cython-hidapi)
    except ImportError as exc:
        raise ImportError("instale o pacote 'hidapi' (pip install hidapi)") from exc
    if not hasattr(hid, "device"):
        raise ImportError("o módulo 'hid' instalado não é o cython-hidapi; use: pip uninstall hid && pip install hidapi")
    return hid


def list_devices() -> list:
    hid = _hid()
    out = []
    for d in hid.enumerate(VENDOR, 0):
        kind = PIDS.get(d.get("product_id"))
        if kind:
            out.append(
                {
                    "kind": kind,
                    "path": d["path"],
                    "name": d.get("product_string") or kind,
                    "usb": d.get("interface_number", -1) >= 0 and d.get("bus_type", 1) == 1,
                    "serial": d.get("serial_number") or "",
                }
            )
    return out


class HidSource:
    def __init__(self, dev, info: dict, gyro_scale: float, accel_scale: float):
        self.dev = dev
        self.info = info
        self.kind = info["kind"]
        self.name = f"{info['name']} (hidapi)"
        self.gyro_scale = gyro_scale
        self.accel_scale = accel_scale
        self._counter = 0

    @classmethod
    def open(cls, prefer: str = "auto", gyro_scale: float = 0.070, accel_scale: float = 1 / 4096):
        devs = list_devices()
        if prefer != "auto":
            devs = [d for d in devs if d["kind"] == prefer]
        if not devs:
            raise NoDeviceFound("nenhum Joy-Con/Pro Controller via HID (pareie por Bluetooth ou ligue no USB)")
        devs.sort(key=lambda d: _PREF_ORDER.index(d["kind"]))
        last_err = None
        for info in devs:
            try:
                dev = _hid().device()
                dev.open_path(info["path"])
                src = cls(dev, info, gyro_scale, accel_scale)
                src._setup()
                return src
            except OSError as exc:
                last_err = exc
        raise NoDeviceFound(f"não consegui abrir o controle: {last_err}")

    # ---- protocolo -------------------------------------------------------
    def _write(self, payload: list) -> None:
        buf = payload + [0] * max(0, 49 - len(payload))
        if self.dev.write(buf) < 0:
            raise OSError("falha ao escrever no controle")

    def _subcmd(self, cmd: int, args: list) -> None:
        self._counter = (self._counter + 1) & 0x0F
        self._write([0x01, self._counter] + _RUMBLE_NEUTRAL + [cmd] + list(args))
        deadline = time.monotonic() + 0.3
        while time.monotonic() < deadline:  # espera a resposta 0x21
            r = self.dev.read(64, 30)
            if r and r[0] == 0x21 and len(r) > 14 and r[14] == cmd:
                return
        # Alguns clones não respondem; segue mesmo assim.

    def _setup(self) -> None:
        if self.info.get("usb") and self.kind == "pro":
            for cmd in (0x02, 0x03, 0x02, 0x04):  # handshake, baud, handshake, só-HID
                self._write([0x80, cmd])
                time.sleep(0.05)
        self._subcmd(0x40, [0x01])  # liga o IMU
        self._subcmd(0x03, [0x30])  # relatório completo 60 Hz com IMU
        self._subcmd(0x30, [0x01])  # LED do jogador 1
        self.dev.set_nonblocking(0)

    # ---- leitura ----------------------------------------------------------
    def events(self):
        last_buttons = None
        last_t = None
        while True:
            try:
                data = self.dev.read(64, 200)
            except (OSError, ValueError) as exc:
                raise DeviceLost(str(exc)) from exc
            if not data:
                if last_t is not None and time.monotonic() - last_t > 2.0:
                    raise DeviceLost("controle parou de enviar dados")
                continue
            if data[0] != 0x30 or len(data) < 49:
                continue
            now = time.monotonic()
            gap = 0.015 if last_t is None else now - last_t
            last_t = now
            # 3 amostras de ~5 ms. Se relatórios se perderam (gap grande),
            # espalha o tempo perdido para não "encolher" o movimento.
            dt = 0.005 if gap < 0.025 else min(gap, 0.1) / 3.0
            buttons = parse_buttons(data)
            if buttons != last_buttons:
                last_buttons = buttons
                yield ButtonState(buttons)
            for gyro, accel in parse_imu(data, self.kind, self.gyro_scale, self.accel_scale):
                yield ImuSample(gyro, accel, dt)

    def close(self) -> None:
        try:
            self.dev.close()
        except Exception:
            pass
