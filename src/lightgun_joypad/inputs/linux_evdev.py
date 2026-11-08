"""Linux: lê o controle pelo driver do kernel hid-nintendo (evdev).

O driver cria dois dispositivos por controle: o gamepad (botões) e o
"... (IMU)" com acelerômetro (ABS_X/Y/Z) e giroscópio (ABS_RX/RY/RZ), já
calibrados de fábrica, com MSC_TIMESTAMP por amostra (~200 Hz efetivos).
"""
from __future__ import annotations

import select
import time

from evdev import InputDevice, ecodes as e, list_devices as _ev_list

from .base import ButtonState, DeviceLost, ImuSample, NoDeviceFound

VENDOR = 0x057E
_PREF_ORDER = ["pro", "joycon-r", "joycon-l", "combined", "other"]

_LOGICAL = {
    e.BTN_SOUTH: "B", e.BTN_EAST: "A", e.BTN_NORTH: "X", e.BTN_WEST: "Y",
    e.BTN_TL: "L", e.BTN_TR: "R", e.BTN_TL2: "ZL", e.BTN_TR2: "ZR",
    e.BTN_SELECT: "MINUS", e.BTN_START: "PLUS", e.BTN_MODE: "HOME", e.BTN_Z: "CAPTURE",
    e.BTN_THUMBL: "LSTICK", e.BTN_THUMBR: "RSTICK",
    e.BTN_DPAD_UP: "UP", e.BTN_DPAD_DOWN: "DOWN", e.BTN_DPAD_LEFT: "LEFT", e.BTN_DPAD_RIGHT: "RIGHT",
}
# Kernels mais novos expõem SL/SR como botões "grip".
for _name, _logical in (("BTN_GRIPL", "SL"), ("BTN_GRIPR", "SR"), ("BTN_GRIPL2", "SL"), ("BTN_GRIPR2", "SR")):
    if hasattr(e, _name):
        _LOGICAL[getattr(e, _name)] = _logical


def _raw_names(code: int) -> list:
    n = e.BTN.get(code) or e.KEY.get(code)
    if n is None:
        return [f"CODE_{code}"]
    return list(n) if isinstance(n, (list, tuple)) else [n]


def _kind(name: str) -> str:
    if "Pro Controller" in name:
        return "pro"
    if "Combined" in name:
        return "combined"
    if "Right Joy-Con" in name or "Joy-Con (R)" in name:
        return "joycon-r"
    if "Left Joy-Con" in name or "Joy-Con (L)" in name:
        return "joycon-l"
    return "other"


def _is_switch(dev: InputDevice) -> bool:
    return dev.info.vendor == VENDOR or "Nintendo" in dev.name or "Joy-Con" in dev.name


def _scan():
    imus, pads = [], []
    for path in _ev_list():
        try:
            dev = InputDevice(path)
        except OSError:
            continue
        if not _is_switch(dev):
            dev.close()
            continue
        caps = dev.capabilities()
        if dev.name.endswith("(IMU)") and e.EV_ABS in caps:
            imus.append(dev)
        elif e.EV_KEY in caps:
            pads.append(dev)
        else:
            dev.close()
    return imus, pads


def list_devices() -> list:
    imus, pads = _scan()
    out = [{"kind": _kind(d.name), "name": d.name, "path": d.path, "imu": d in imus} for d in imus + pads]
    for d in imus + pads:
        d.close()
    return out


class EvdevSource:
    def __init__(self, imu: InputDevice, pad: InputDevice | None, grab: bool):
        self.imu = imu
        self.pad = pad
        self.kind = _kind(imu.name)
        self.name = f"{imu.name} (evdev)"
        ai = imu.absinfo
        self.accel_res = float(ai(e.ABS_X).resolution or 4096)
        self.gyro_res = float(ai(e.ABS_RX).resolution or 14247)
        if grab and pad is not None:
            pad.grab()

    @classmethod
    def open(cls, prefer: str = "auto", grab: bool = False):
        imus, pads = _scan()
        if not imus:
            for d in pads:
                d.close()
            hint = ""
            if pads:
                hint = " (há controle, mas sem acesso ao IMU — verifique o driver hid-nintendo e as permissões)"
            raise NoDeviceFound("nenhum IMU do hid-nintendo encontrado" + hint)
        if prefer != "auto":
            imus = [d for d in imus if _kind(d.name) == prefer] or imus
        imus.sort(key=lambda d: _PREF_ORDER.index(_kind(d.name)))
        imu = imus[0]
        pad = None
        # Mesmo controle: mesmo MAC (uniq).
        for p in pads:
            if imu.uniq and p.uniq == imu.uniq:
                pad = p
                break
        if pad is None:  # Joy-Cons combinados pelo joycond, etc.
            for p in pads:
                if _kind(p.name) == "combined":
                    pad = p
                    break
        if pad is None and pads:
            pad = pads[0]
        for d in imus + pads:
            if d is not imu and d is not pad:
                d.close()
        return cls(imu, pad, grab)

    def events(self):
        devs = {self.imu.fd: self.imu}
        if self.pad is not None:
            devs[self.pad.fd] = self.pad
        acc = [0, 0, 0]
        gyr = [0, 0, 0]
        ts_prev = None
        ts_cur = None
        t_prev = None
        pressed_codes: set = set()
        hat = {e.ABS_HAT0X: 0, e.ABS_HAT0Y: 0}
        last_buttons = None
        axis_idx = {e.ABS_X: (acc, 0), e.ABS_Y: (acc, 1), e.ABS_Z: (acc, 2),
                    e.ABS_RX: (gyr, 0), e.ABS_RY: (gyr, 1), e.ABS_RZ: (gyr, 2)}
        while True:
            try:
                ready, _, _ = select.select(list(devs), [], [], 2.0)
            except OSError as exc:
                raise DeviceLost(str(exc)) from exc
            if not ready:
                raise DeviceLost("controle parou de enviar dados")
            for fd in ready:
                dev = devs[fd]
                try:
                    evs = list(dev.read())
                except OSError as exc:
                    raise DeviceLost(str(exc)) from exc
                for ev in evs:
                    if dev is self.imu:
                        if ev.type == e.EV_ABS and ev.code in axis_idx:
                            arr, i = axis_idx[ev.code]
                            arr[i] = ev.value
                        elif ev.type == e.EV_MSC and ev.code == e.MSC_TIMESTAMP:
                            ts_cur = ev.value
                        elif ev.type == e.EV_SYN and ev.code == e.SYN_REPORT:
                            dt = None
                            if ts_cur is not None and ts_prev is not None:
                                d_us = (ts_cur - ts_prev) & 0xFFFFFFFF
                                if 0 < d_us < 100_000:
                                    dt = d_us / 1e6
                            if dt is None:
                                t = ev.timestamp()
                                dt = 0.005 if t_prev is None else min(max(t - t_prev, 0.0), 0.1)
                            t_prev = ev.timestamp()
                            ts_prev = ts_cur
                            g = self.gyro_res
                            a = self.accel_res
                            yield ImuSample((gyr[0] / g, gyr[1] / g, gyr[2] / g), (acc[0] / a, acc[1] / a, acc[2] / a), dt)
                    else:
                        if ev.type == e.EV_KEY:
                            if ev.value:
                                pressed_codes.add(ev.code)
                            else:
                                pressed_codes.discard(ev.code)
                        elif ev.type == e.EV_ABS and ev.code in hat:
                            hat[ev.code] = ev.value
                        elif ev.type == e.EV_SYN and ev.code == e.SYN_REPORT:
                            names = set()
                            for c in pressed_codes:
                                names.update(_raw_names(c))
                                if c in _LOGICAL:
                                    names.add(_LOGICAL[c])
                            if hat[e.ABS_HAT0X] < 0:
                                names.add("LEFT")
                            elif hat[e.ABS_HAT0X] > 0:
                                names.add("RIGHT")
                            if hat[e.ABS_HAT0Y] < 0:
                                names.add("UP")
                            elif hat[e.ABS_HAT0Y] > 0:
                                names.add("DOWN")
                            fs = frozenset(names)
                            if fs != last_buttons:
                                last_buttons = fs
                                yield ButtonState(fs)

    def close(self) -> None:
        for d in (self.imu, self.pad):
            if d is None:
                continue
            try:
                d.ungrab()
            except Exception:
                pass
            try:
                d.close()
            except Exception:
                pass
