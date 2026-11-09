from __future__ import annotations

from dataclasses import dataclass


class NoDeviceFound(Exception):
    pass


class DeviceLost(Exception):
    pass


@dataclass
class ImuSample:
    gyro_dps: tuple  # (x, y, z) graus/s, convenção X=cano, Y=esquerda, Z=cima
    accel_g: tuple  # (x, y, z) em g
    dt: float  # segundos desde a amostra anterior


@dataclass
class ButtonState:
    pressed: frozenset  # nomes lógicos (ZR, A, ...) e crus (BTN_TR2, ...)


@dataclass
class PointerSample:
    """Posição já em coordenadas de tela (fonte "mouse comum")."""

    x: float  # 0..1 na área de trabalho inteira
    y: float
    dt: float
