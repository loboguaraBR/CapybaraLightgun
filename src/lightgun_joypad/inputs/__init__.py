"""Fontes de mira: controles com giroscópio (Switch, PS4/PS5) ou o mouse comum."""
from __future__ import annotations

import sys

from .base import ButtonState, DeviceLost, ImuSample, NoDeviceFound, PointerSample  # noqa: F401

# input_source:
#   "auto"        qualquer controle com giroscópio (Nintendo, PlayStation, outros)
#   "switch"      Joy-Con / Pro Controller (caminho próprio, o mais preciso)
#   "playstation" DualSense / DualShock 4
#   "gamepad"     outro controle com giroscópio (SDL: Steam Deck/Controller, 8BitDo...)
#   "mouse"       mouse do sistema (para quem não tem controle com giroscópio)
SOURCES = {  # rótulos em inglês (a interface traduz)
    "auto": "Automatic (any controller with a gyroscope)",
    "switch": "Nintendo Switch (Joy-Con / Pro Controller)",
    "playstation": "PlayStation (DualSense PS5 / DualShock 4)",
    "gamepad": "Other controller with a gyroscope (SDL)",
    "mouse": "System mouse (no controller)",
}


def _try(errors: list, label: str, fn):
    try:
        return fn()
    except (ImportError, NoDeviceFound, OSError) as exc:
        errors.append(f"{label}: {exc}")
        return None


def open_source(cfg: dict):
    src = cfg.get("input_source", "auto")
    if src == "mouse":
        from .mouse_source import MouseSource

        return MouseSource.open()
    prefer = cfg.get("device", "auto")
    linux = sys.platform.startswith("linux")
    backend = cfg.get("input_backend", "auto")
    errors: list = []

    def evdev(fams):
        from .linux_evdev import EvdevSource

        return EvdevSource.open(prefer, grab=bool(cfg.get("grab")), families=fams)

    def switch_hid():
        from .switch_hid import HidSource

        return HidSource.open(prefer if prefer not in ("ps4", "ps5") else "auto",
                              gyro_scale=float(cfg["gyro_dps_per_lsb"]), accel_scale=float(cfg["accel_g_per_lsb"]))

    def sdl():
        from .sdl_source import SdlSource

        return SdlSource.open(prefer)

    def ps_hid():
        from .ps_hid import PsHidSource

        return PsHidSource.open(prefer)

    # Ordem de tentativa: o caminho mais preciso de cada família primeiro.
    plan = []
    use_evdev = linux and backend in ("auto", "evdev")
    use_hid = backend in ("auto", "hidapi")
    if src in ("auto", "switch"):
        if use_evdev:
            plan.append(("evdev/switch", lambda: evdev(("switch",))))
        if use_hid:
            plan.append(("hidapi/switch", switch_hid))
    if src in ("auto", "playstation"):
        if use_evdev:
            plan.append(("evdev/playstation", lambda: evdev(("playstation",))))
        plan.append(("sdl", sdl))
        if use_hid and not linux:
            plan.append(("hidapi/playstation", ps_hid))
    if src == "gamepad" or (src == "auto"):
        if ("sdl", sdl) not in plan:
            plan.append(("sdl", sdl))
    no_gyro: list = []

    def attempt(label, fn):
        try:
            return fn()
        except (ImportError, NoDeviceFound, OSError) as exc:
            errors.append(f"{label}: {exc}")
            no_gyro.extend(getattr(exc, "no_gyro", []) or [])
            return None

    for label, fn in plan:
        s = attempt(label, fn)
        if s is not None:
            return s
    exc = NoDeviceFound("nenhum controle com giroscópio encontrado.\n  " + "\n  ".join(errors))
    exc.no_gyro = no_gyro
    raise exc


def list_all() -> list:
    out = []
    if sys.platform.startswith("linux"):
        try:
            from .linux_evdev import list_devices as ev_list

            out += [("evdev", d) for d in ev_list()]
        except ImportError as exc:
            out.append(("evdev", f"indisponível: {exc}"))
    for mod in ("switch_hid", "ps_hid", "sdl_source"):
        try:
            m = __import__(f"lightgun_joypad.inputs.{mod}", fromlist=["list_devices"])
            out += [("sdl" if mod == "sdl_source" else "hidapi", d) for d in m.list_devices()]
        except ImportError as exc:
            out.append(("hidapi", f"indisponível: {exc}"))
    return out
