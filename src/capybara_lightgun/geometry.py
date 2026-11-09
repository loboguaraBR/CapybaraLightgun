"""Geometria da mira: direção do cano -> ponto na tela.

Uma light gun real acerta onde a reta do cano cruza a tela. Aqui fazemos o
mesmo: a direção do cano (no mundo, já com o yaw recentrado) é projetada num
plano virtual a 1 m à frente (u = direita, v = cima). De um ponto de vista
fixo, a relação entre esse plano virtual e a tela real é EXATAMENTE uma
homografia (transformação projetiva). Por isso, calibrando 4+ pontos
(cantos + centro), a mira fica fisicamente correta mesmo com a pessoa fora
do eixo da tela, tela inclinada, etc.
"""
from __future__ import annotations

import math
import statistics
from typing import Optional, Sequence

MIN_FORWARD = 0.05  # abaixo disso o cano aponta "de lado"/para trás da tela


def rotate_yaw(f, angle: float):
    """Gira o vetor f em torno do eixo vertical (Z) por `angle` rad."""
    c, s = math.cos(angle), math.sin(angle)
    return (c * f[0] - s * f[1], s * f[0] + c * f[1], f[2])


def heading(f) -> float:
    """Direção horizontal (yaw) de um vetor no mundo. Positivo = esquerda."""
    return math.atan2(f[1], f[0])


def project(f) -> Optional[tuple]:
    """Interseção do raio f com o plano x=1 -> (u, v). u: direita, v: cima."""
    fx, fy, fz = f
    if fx < MIN_FORWARD:
        return None
    return (-fy / fx, fz / fx)


def solve_linear(a: list, b: list) -> list:
    """Eliminação de Gauss com pivotamento parcial (sistemas pequenos)."""
    n = len(b)
    m = [list(a[i]) + [b[i]] for i in range(n)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("sistema singular (pontos de calibração degenerados)")
        m[col], m[piv] = m[piv], m[col]
        p = m[col][col]
        for r in range(col + 1, n):
            f = m[r][col] / p
            if f:
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = m[r][n] - sum(m[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / m[r][r]
    return x


class Homography:
    """Mapeia (u, v) do plano virtual -> (x, y) normalizado da tela [0..1]."""

    def __init__(self, m: Sequence[float]):
        if len(m) != 9:
            raise ValueError("homografia precisa de 9 coeficientes")
        self.m = [float(v) for v in m]

    @classmethod
    def from_screen(cls, width_m: float, height_m: float, distance_m: float) -> "Homography":
        """Modelo geométrico sem calibração: pessoa centralizada a `distance_m`."""
        sx = distance_m / width_m
        sy = distance_m / height_m
        return cls([sx, 0.0, 0.5, 0.0, -sy, 0.5, 0.0, 0.0, 1.0])

    @classmethod
    def fit(cls, src: Sequence[tuple], dst: Sequence[tuple]) -> "Homography":
        """Mínimos quadrados (DLT com h33=1) para >= 4 correspondências."""
        if len(src) != len(dst) or len(src) < 4:
            raise ValueError("são necessários pelo menos 4 pontos")
        rows, rhs = [], []
        for (u, v), (x, y) in zip(src, dst):
            rows.append([u, v, 1.0, 0.0, 0.0, 0.0, -u * x, -v * x])
            rhs.append(x)
            rows.append([0.0, 0.0, 0.0, u, v, 1.0, -u * y, -v * y])
            rhs.append(y)
        ata = [[sum(r[i] * r[j] for r in rows) for j in range(8)] for i in range(8)]
        atb = [sum(r[i] * rhs[k] for k, r in enumerate(rows)) for i in range(8)]
        h = solve_linear(ata, atb)
        return cls(h + [1.0])

    def apply(self, u: float, v: float) -> Optional[tuple]:
        m = self.m
        w = m[6] * u + m[7] * v + m[8]
        if abs(w) < 1e-9:
            return None
        return ((m[0] * u + m[1] * v + m[2]) / w, (m[3] * u + m[4] * v + m[5]) / w)

    def inverse(self) -> "Homography":
        a, b, c, d, e, f, g, h, i = self.m
        A = e * i - f * h
        B = -(d * i - f * g)
        C = d * h - e * g
        det = a * A + b * B + c * C
        if abs(det) < 1e-15:
            raise ValueError("homografia não inversível")
        inv = [
            A, -(b * i - c * h), b * f - c * e,
            B, a * i - c * g, -(a * f - c * d),
            C, -(a * h - b * g), a * e - b * d,
        ]
        return Homography([v / det for v in inv])

    def center_heading(self) -> float:
        """Yaw (rad, mundo) da direção que acerta o centro da tela."""
        uv = self.inverse().apply(0.5, 0.5)
        if uv is None:
            return 0.0
        return math.atan2(-uv[0], 1.0)

    def to_list(self) -> list:
        return list(self.m)


def median_forward(hist, t_press: float):
    """Direção mediana do cano entre 250 ms e 30 ms antes do aperto."""
    window = [f for t, f in hist if t_press - 0.25 <= t <= t_press - 0.03]
    if len(window) < 5:
        window = [f for _, f in list(hist)[-10:]]
    f = tuple(statistics.median(v[i] for v in window) for i in range(3))
    n = math.sqrt(sum(c * c for c in f)) or 1.0
    return (f[0] / n, f[1] / n, f[2] / n)
