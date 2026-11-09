"""Linux: lê controles com giroscópio pelos drivers do kernel (evdev).

- Nintendo (hid-nintendo): Joy-Con, Pro Controller — dispositivo "... (IMU)".
- Sony (hid-playstation / hid-sony): DualSense (PS5), DualShock 4 (PS4) —
  dispositivo "... Motion Sensors".

Cada controle tem um dispositivo de botões e outro de sensores com
acelerômetro (ABS_X/Y/Z) e giroscópio (ABS_RX/RY/RZ), já calibrados, com
MSC_TIMESTAMP por amostra. A vibração (coice do tiro) usa force feedback.
"""
from __future__ import annotations

import select

from evdev import InputDevice, ecodes as e, ff, list_devices as _ev_list

from .base import ButtonState, DeviceLost, ImuSample, NoDeviceFound
from .linux_evdev_axes import to_lightgun_axes

NINTENDO = 0x057E
SONY = 0x054C
_PREF_ORDER = ["pro", "joycon-r", "joycon-l", "combined", "ps5", "ps4", "other"]

# Nomes lógicos posicionais (padrão Nintendo). No PlayStation:
# ✕=B, ○=A, △=X, □=Y, L1=L, R1=R, L2=ZL, R2=ZR, Create/Share=MINUS,
# Options=PLUS, PS=HOME.
_LOGICAL = {
    e.BTN_SOUTH: "B", e.BTN_EAST: "A", e.BTN_NORTH: "X", e.BTN_WEST: "Y",
    e.BTN_TL: "L", e.BTN_TR: "R", e.BTN_TL2: "ZL", e.BTN_TR2: "ZR",
    e.BTN_SELECT: "MINUS", e.BTN_START: "PLUS", e.BTN_MODE: "HOME", e.BTN_Z: "CAPTURE",
    e.BTN_THUMBL: "LSTICK", e.BTN_THUMBR: "RSTICK",
    e.BTN_DPAD_UP: "UP", e.BTN_DPAD_DOWN: "DOWN", e.BTN_DPAD_LEFT: "LEFT", e.BTN_DPAD_RIGHT: "RIGHT",
}
for _name, _logical in (("BTN_GRIPL", "SL"), ("BTN_GRIPR", "SR"), ("BTN_GRIPL2", "SL"), ("BTN_GRIPR2", "SR")):
    if hasattr(e, _name):
        _LOGICAL[getattr(e, _name)] = _logical


def _raw_names(code: int) -> list:
    n = e.BTN.get(code) or e.KEY.get(code)
    if n is None:
        return [f"CODE_{code}"]
    return list(n) if isinstance(n, (list, tuple)) else [n]


def family(dev: InputDevice) -> str:
    n = dev.name
    if dev.info.vendor == NINTENDO or "Nintendo" in n or "Joy-Con" in n:
        return "switch"
    if dev.info.vendor == SONY or "DualSense" in n or "Wireless Controller" in n:
        return "playstation"
    return ""


def _kind(dev: InputDevice) -> str:
    n = dev.name
    if family(dev) == "playstation":
        return "ps5" if ("DualSense" in n or dev.info.product in (0x0CE6, 0x0DF2)) else "ps4"
    if "Pro Controller" in n:
        return "pro"
    if "Combined" in n:
        return "combined"
    if "Right Joy-Con" in n or "Joy-Con (R)" in n:
        return "joycon-r"
    if "Left Joy-Con" in n or "Joy-Con (L)" in n:
        return "joycon-l"
    return "other"


def _is_imu(dev: InputDevice) -> bool:
    caps = dev.capabilities()
    if e.EV_ABS not in caps:
        return False
    props = dev.input_props()
    return (dev.name.endswith("(IMU)") or "Motion Sensors" in dev.name
            or e.INPUT_PROP_ACCELEROMETER in props)


def _scan(families=("switch", "playstation")):
    imus, pads = [], []
    for path in _ev_list():
        try:
            dev = InputDevice(path)
        except OSError:
            continue
        fam = family(dev)
        if fam not in families or "Touchpad" in dev.name:
            dev.close()
            continue
        if _is_imu(dev):
            imus.append(dev)
        elif e.EV_KEY in dev.capabilities():
            pads.append(dev)
        else:
            dev.close()
    return imus, pads


def list_devices() -> list:
    imus, pads = _scan()
    out = [{"kind": _kind(d), "family": family(d), "name": d.name, "path": d.path, "imu": d in imus}
           for d in imus + pads]
    for d in imus + pads:
        d.close()
    return out


def _same_controller(a: InputDevice, b: InputDevice) -> bool:
    if a.uniq and b.uniq:
        return a.uniq == b.uniq
    return bool(a.phys) and a.phys.split("/")[0] == (b.phys or "").split("/")[0]


class EvdevSource:
    def __init__(self, imu: InputDevice, pad: InputDevice | None, grab: bool):
        self.imu = imu
        self.pad = pad
        self.family = family(imu)
        self.kind = _kind(imu)
        self.name = f"{imu.name} (evdev)"
        ai = imu.absinfo
        default_acc, default_gyro = (8192, 1024) if self.family == "playstation" else (4096, 14247)
        self.accel_res = float(ai(e.ABS_X).resolution or default_acc)
        self.gyro_res = float(ai(e.ABS_RX).resolution or default_gyro)
        self._ff_id = None
        self._ff_len = None
        if grab and pad is not None:
            pad.grab()

    @classmethod
    def open(cls, prefer: str = "auto", grab: bool = False, families=("switch", "playstation")):
        imus, pads = _scan(families)
        if not imus:
            for d in pads:
                d.close()
            hint = ""
            if pads:
                hint = (" (há controle, mas sem acesso aos sensores — rode scripts/fix-linux-joycon.sh "
                        "para liberar as permissões)")
            raise NoDeviceFound("nenhum controle com giroscópio encontrado" + hint)
        if prefer != "auto":
            imus = [d for d in imus if _kind(d) == prefer] or imus
        imus.sort(key=lambda d: _PREF_ORDER.index(_kind(d)))
        imu = imus[0]
        pad = next((p for p in pads if family(p) == family(imu) and _same_controller(imu, p)), None)
        if pad is None:  # Joy-Cons combinados pelo joycond, etc.
            pad = next((p for p in pads if _kind(p) == "combined"), None)
        if pad is None:
            pad = next((p for p in pads if family(p) == family(imu)), None)
        for d in imus + pads:
            if d is not imu and d is not pad:
                d.close()
        return cls(imu, pad, grab)

    # ---- vibração ----------------------------------------------------------
    def rumble(self, ms: int = 45, strength: float = 0.7) -> None:
        """Coice: vibra o controle por `ms` milissegundos (se o driver suportar)."""
        pad = self.pad
        if pad is None or e.EV_FF not in pad.capabilities():
            return
        try:
            mag = int(max(0.0, min(1.0, strength)) * 0xFFFF)
            if self._ff_id is None or self._ff_len != (ms, mag):
                effect = ff.Effect(
                    e.FF_RUMBLE, -1 if self._ff_id is None else self._ff_id, 0,
                    ff.Trigger(0, 0), ff.Replay(int(ms), 0),
                    ff.EffectType(ff_rumble_effect=ff.Rumble(strong_magnitude=mag, weak_magnitude=mag)),
                )
                self._ff_id = pad.upload_effect(effect)
                self._ff_len = (ms, mag)
            pad.write(e.EV_FF, self._ff_id, 1)
        except OSError:
            pass

    # ---- leitura -----------------------------------------------------------
    def events(self):
        devs = {self.imu.fd: self.imu}
        if self.pad is not None:
            devs[self.pad.fd] = self.pad
        fam = self.family
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
            except (OSError, ValueError) as exc:
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
                            g, a = self.gyro_res, self.accel_res
                            yield ImuSample(
                                to_lightgun_axes(fam, (gyr[0] / g, gyr[1] / g, gyr[2] / g)),
                                to_lightgun_axes(fam, (acc[0] / a, acc[1] / a, acc[2] / a)),
                                dt,
                            )
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
        if self._ff_id is not None and self.pad is not None:
            try:
                self.pad.erase_effect(self._ff_id)
            except Exception:
                pass
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
