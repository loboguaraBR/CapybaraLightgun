"""Fusão do IMU (giroscópio + acelerômetro) para orientação absoluta.

Convenção de eixos do controle (a mesma do driver hid-nintendo do Linux):
    X: aponta para os gatilhos (o "cano" da arma)
    Y: aponta para a esquerda
    Z: aponta para cima (para fora dos botões)

Mundo: Z para cima (gravidade), X/Y no plano horizontal.

O filtro é um Mahony 6DOF: o giroscópio dá a rotação (rápida, sem atraso),
o acelerômetro corrige devagar a inclinação (pitch/roll) pela gravidade.
O yaw (direção horizontal) não tem referência absoluta — o Switch não tem
magnetômetro — então ele é corrigido pelo "recentrar" e pela estimativa
contínua do bias do giroscópio.
"""
from __future__ import annotations

import math

Vec3 = tuple
Quat = tuple


def quat_mul(a: Quat, b: Quat) -> Quat:
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return (
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    )


def quat_conj(q: Quat) -> Quat:
    return (q[0], -q[1], -q[2], -q[3])


def quat_normalize(q: Quat) -> Quat:
    n = math.sqrt(q[0] ** 2 + q[1] ** 2 + q[2] ** 2 + q[3] ** 2)
    if n < 1e-12:
        return (1.0, 0.0, 0.0, 0.0)
    return (q[0] / n, q[1] / n, q[2] / n, q[3] / n)


def quat_from_rotvec(rx: float, ry: float, rz: float) -> Quat:
    """Quaternion de uma rotação dada por vetor eixo*ângulo (rad)."""
    ang = math.sqrt(rx * rx + ry * ry + rz * rz)
    if ang < 1e-9:
        return quat_normalize((1.0, rx * 0.5, ry * 0.5, rz * 0.5))
    s = math.sin(ang * 0.5) / ang
    return (math.cos(ang * 0.5), rx * s, ry * s, rz * s)


def quat_from_euler(yaw: float, pitch: float, roll: float) -> Quat:
    """Euler ZYX (yaw em Z, pitch em Y, roll em X) -> quaternion corpo->mundo."""
    cy, sy = math.cos(yaw * 0.5), math.sin(yaw * 0.5)
    cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
    cr, sr = math.cos(roll * 0.5), math.sin(roll * 0.5)
    return (
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    )


def quat_rotate(q: Quat, v: Vec3) -> Vec3:
    """Rotaciona v (no referencial do corpo) para o mundo."""
    w, x, y, z = q
    vx, vy, vz = v
    # t = 2 * (q.xyz x v)
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )


class Mahony:
    """Filtro de orientação Mahony (giroscópio + acelerômetro)."""

    def __init__(self, kp: float = 0.4, accel_tolerance_g: float = 0.25):
        self.kp = kp
        self.accel_tolerance_g = accel_tolerance_g
        self.q: Quat = (1.0, 0.0, 0.0, 0.0)

    def reset_from_accel(self, accel: Vec3, yaw: float = 0.0) -> None:
        ax, ay, az = accel
        n = math.sqrt(ax * ax + ay * ay + az * az)
        if n < 1e-6:
            self.q = quat_from_euler(yaw, 0.0, 0.0)
            return
        ax, ay, az = ax / n, ay / n, az / n
        roll = math.atan2(ay, az)
        pitch = math.atan2(-ax, math.hypot(ay, az))
        self.q = quat_from_euler(yaw, pitch, roll)

    def gravity_body(self) -> Vec3:
        """Direção "para cima" do mundo vista no referencial do controle."""
        q0, q1, q2, q3 = self.q
        return (
            2.0 * (q1 * q3 - q0 * q2),
            2.0 * (q0 * q1 + q2 * q3),
            q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3,
        )

    def update(self, gyro_rad: Vec3, accel_g: Vec3, dt: float) -> None:
        gx, gy, gz = gyro_rad
        ax, ay, az = accel_g
        n = math.sqrt(ax * ax + ay * ay + az * az)
        if self.kp > 0.0 and n > 1e-6:
            # Confia menos no acelerômetro quando há aceleração linear
            # (tranco do gatilho, movimento brusco do braço).
            w = 1.0 - abs(n - 1.0) / self.accel_tolerance_g
            if w > 0.0:
                ax, ay, az = ax / n, ay / n, az / n
                vx, vy, vz = self.gravity_body()
                ex = ay * vz - az * vy
                ey = az * vx - ax * vz
                ez = ax * vy - ay * vx
                k = self.kp * w
                gx += k * ex
                gy += k * ey
                gz += k * ez
        dq = quat_from_rotvec(gx * dt, gy * dt, gz * dt)
        self.q = quat_normalize(quat_mul(self.q, dq))

    def forward(self) -> Vec3:
        """Para onde o cano (eixo X do controle) aponta, no mundo."""
        return quat_rotate(self.q, (1.0, 0.0, 0.0))


class BiasEstimator:
    """Estima o bias (deriva) do giroscópio quando o controle está parado.

    Funciona em janelas: se durante `window_s` o giroscópio e o acelerômetro
    variam muito pouco, o controle está apoiado/parado e a média do
    giroscópio é o bias. A mão humana sempre treme, então segurando a arma
    a janela não fecha e nenhum movimento real é "engolido" como bias.
    """

    def __init__(
        self,
        window_s: float = 0.6,
        still_range_dps: float = 1.5,
        accel_range_g: float = 0.03,
        blend: float = 0.5,
        max_jump_dps: float = 6.0,
        enabled: bool = True,
    ):
        self.window_s = window_s
        self.still_range_dps = still_range_dps
        self.accel_range_g = accel_range_g
        self.blend = blend
        self.max_jump_dps = max_jump_dps
        self.enabled = enabled
        self.bias = [0.0, 0.0, 0.0]
        self.acquired = False
        self.updates = 0
        self._reset()

    def _reset(self) -> None:
        self._t = 0.0
        self._n = 0
        self._sum = [0.0, 0.0, 0.0]
        self._gmin = [math.inf] * 3
        self._gmax = [-math.inf] * 3
        self._amin = [math.inf] * 3
        self._amax = [-math.inf] * 3

    def update(self, gyro_dps: Vec3, accel_g: Vec3, dt: float) -> bool:
        """Alimenta uma amostra. Retorna True se o bias foi atualizado."""
        if not self.enabled:
            return False
        for i in range(3):
            g, a = gyro_dps[i], accel_g[i]
            if g < self._gmin[i]:
                self._gmin[i] = g
            if g > self._gmax[i]:
                self._gmax[i] = g
            if a < self._amin[i]:
                self._amin[i] = a
            if a > self._amax[i]:
                self._amax[i] = a
        moving = any(self._gmax[i] - self._gmin[i] > self.still_range_dps for i in range(3)) or any(
            self._amax[i] - self._amin[i] > self.accel_range_g for i in range(3)
        )
        if moving:
            self._reset()
            return False
        for i in range(3):
            self._sum[i] += gyro_dps[i]
        self._n += 1
        self._t += dt
        if self._t < self.window_s or self._n < 10:
            return False
        mean = [s / self._n for s in self._sum]
        self._reset()
        if not self.acquired:
            self.bias = mean
            self.acquired = True
            self.updates += 1
            return True
        if all(abs(mean[i] - self.bias[i]) < self.max_jump_dps for i in range(3)):
            for i in range(3):
                self.bias[i] += self.blend * (mean[i] - self.bias[i])
            self.updates += 1
            return True
        return False
