"""Fontes de dados do controle (IMU + botões)."""
from __future__ import annotations

import sys

from .base import ButtonState, DeviceLost, ImuSample, NoDeviceFound  # noqa: F401


def open_source(cfg: dict):
    backend = cfg.get("input_backend", "auto")
    prefer = cfg.get("device", "auto")
    errors = []
    order = [backend] if backend != "auto" else (["evdev", "hidapi"] if sys.platform.startswith("linux") else ["hidapi"])
    for name in order:
        try:
            if name == "evdev":
                from .linux_evdev import EvdevSource

                return EvdevSource.open(prefer, grab=bool(cfg.get("grab")))
            if name == "hidapi":
                from .switch_hid import HidSource

                return HidSource.open(
                    prefer,
                    gyro_scale=float(cfg["gyro_dps_per_lsb"]),
                    accel_scale=float(cfg["accel_g_per_lsb"]),
                )
            raise ValueError(f"backend de entrada desconhecido: {name}")
        except (ImportError, NoDeviceFound, OSError) as exc:
            errors.append(f"{name}: {exc}")
    raise NoDeviceFound("nenhum controle Switch encontrado.\n  " + "\n  ".join(errors))


def list_all() -> list:
    out = []
    if sys.platform.startswith("linux"):
        try:
            from .linux_evdev import list_devices as ev_list

            out += [("evdev", d) for d in ev_list()]
        except ImportError as exc:
            out.append(("evdev", f"indisponível: {exc}"))
    try:
        from .switch_hid import list_devices as hid_list

        out += [("hidapi", d) for d in hid_list()]
    except ImportError as exc:
        out.append(("hidapi", f"indisponível: {exc}"))
    return out
