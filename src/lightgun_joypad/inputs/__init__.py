"""Fontes de mira: controles com giroscópio (Switch, PS4/PS5) ou o mouse comum."""
from __future__ import annotations

import sys

from .base import ButtonState, DeviceLost, ImuSample, NoDeviceFound, PointerSample  # noqa: F401

# input_source: "auto" (qualquer controle com giroscópio), "switch",
# "playstation" ou "mouse".
SOURCES = {
    "auto": "Automático (Switch ou PlayStation)",
    "switch": "Nintendo Switch (Joy-Con / Pro Controller)",
    "playstation": "PlayStation (DualSense PS5 / DualShock 4)",
    "mouse": "Mouse comum",
}


def open_source(cfg: dict):
    src = cfg.get("input_source", "auto")
    if src == "mouse":
        from .mouse_source import MouseSource

        return MouseSource.open()
    families = ("switch", "playstation") if src == "auto" else (src,)
    backend = cfg.get("input_backend", "auto")
    prefer = cfg.get("device", "auto")
    errors = []
    order = [backend] if backend != "auto" else (["evdev", "hidapi"] if sys.platform.startswith("linux") else ["hidapi"])
    for name in order:
        for fam in (families if name == "hidapi" else (None,)):
            try:
                if name == "evdev":
                    from .linux_evdev import EvdevSource

                    return EvdevSource.open(prefer, grab=bool(cfg.get("grab")), families=families)
                if name == "hidapi" and fam == "switch":
                    from .switch_hid import HidSource

                    return HidSource.open(
                        prefer if prefer not in ("ps4", "ps5") else "auto",
                        gyro_scale=float(cfg["gyro_dps_per_lsb"]),
                        accel_scale=float(cfg["accel_g_per_lsb"]),
                    )
                if name == "hidapi" and fam == "playstation":
                    from .ps_hid import PsHidSource

                    return PsHidSource.open(prefer)
                if name not in ("evdev", "hidapi"):
                    raise ValueError(f"backend de entrada desconhecido: {name}")
            except (ImportError, NoDeviceFound, OSError) as exc:
                errors.append(f"{name}{'/' + fam if fam else ''}: {exc}")
    raise NoDeviceFound("nenhum controle com giroscópio encontrado.\n  " + "\n  ".join(errors))


def list_all() -> list:
    out = []
    if sys.platform.startswith("linux"):
        try:
            from .linux_evdev import list_devices as ev_list

            out += [("evdev", d) for d in ev_list()]
        except ImportError as exc:
            out.append(("evdev", f"indisponível: {exc}"))
    for mod in ("switch_hid", "ps_hid"):
        try:
            m = __import__(f"lightgun_joypad.inputs.{mod}", fromlist=["list_devices"])
            out += [("hidapi", d) for d in m.list_devices()]
        except ImportError as exc:
            out.append(("hidapi", f"indisponível: {exc}"))
    return out
