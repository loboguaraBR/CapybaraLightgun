"""Filtro One Euro 2D: tira o tremor da mão sem atrasar movimentos rápidos.

Parado/lento -> corte baixo (mira estável). Rápido -> corte alto (sem lag).
"""
from __future__ import annotations

import math


def _alpha(cutoff: float, dt: float) -> float:
    tau = 1.0 / (2.0 * math.pi * cutoff)
    return 1.0 / (1.0 + tau / dt)


class OneEuro2D:
    def __init__(self, min_cutoff: float = 1.2, beta: float = 6.0, d_cutoff: float = 1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.reset()

    def reset(self) -> None:
        self._t = None
        self._x = (0.0, 0.0)
        self._dx = (0.0, 0.0)

    def __call__(self, x: float, y: float, t: float) -> tuple:
        if self._t is None:
            self._t = t
            self._x = (x, y)
            self._dx = (0.0, 0.0)
            return self._x
        dt = t - self._t
        if dt <= 1e-6:
            dt = 1e-3
        self._t = t
        px, py = self._x
        ad = _alpha(self.d_cutoff, dt)
        dx = ad * ((x - px) / dt) + (1.0 - ad) * self._dx[0]
        dy = ad * ((y - py) / dt) + (1.0 - ad) * self._dx[1]
        self._dx = (dx, dy)
        speed = math.hypot(dx, dy)
        a = _alpha(self.min_cutoff + self.beta * speed, dt)
        self._x = (px + a * (x - px), py + a * (y - py))
        return self._x
