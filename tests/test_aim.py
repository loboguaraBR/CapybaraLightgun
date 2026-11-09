"""Testes da matemática da mira, incluindo simulação física de uma arma."""
import math
import random

import pytest

from lightgun_joypad.config import DEFAULTS
from lightgun_joypad.engine import LightGun, Tracker
from lightgun_joypad.filters import OneEuro2D
from lightgun_joypad.fusion import BiasEstimator, Mahony, quat_conj, quat_from_euler, quat_mul, quat_rotate
from lightgun_joypad.geometry import Homography, project
from lightgun_joypad.inputs import ButtonState, ImuSample
from lightgun_joypad.inputs.switch_hid import parse_buttons, parse_imu

W, H, D = 1.21, 0.68, 2.0  # TV 55" a 2 m


def target_euler(x, y, eye=(0.0, 0.0), roll=0.0, yaw0=0.0):
    """Yaw/pitch para acertar o ponto (x,y) normalizado da tela, olho em `eye` (m)."""
    dx = (x - 0.5) * W - eye[0]
    dy = (0.5 - y) * H - eye[1]
    yaw = math.atan2(-dx, D)  # yaw positivo = esquerda
    pitch = -math.atan2(dy, math.hypot(D, dx))  # pitch negativo = nariz para cima
    return yaw + yaw0, pitch, roll


def simulate(path, dt=0.005, gyro_bias=(0, 0, 0), noise=0.0, seed=1):
    """Gera amostras de IMU (gyro °/s, accel g) seguindo uma lista de quaternions."""
    rnd = random.Random(seed)
    out = []
    for q0, q1 in zip(path, path[1:]):
        d = quat_mul(quat_conj(q0), q1)
        if d[0] < 0:
            d = tuple(-c for c in d)
        ang = 2 * math.acos(min(1.0, d[0]))
        s = math.sqrt(max(1e-18, 1 - d[0] ** 2))
        axis = (d[1] / s, d[2] / s, d[3] / s) if ang > 1e-9 else (0, 0, 0)
        w = tuple(math.degrees(axis[i] * ang / dt) + gyro_bias[i] + rnd.gauss(0, noise) for i in range(3))
        up = quat_rotate(quat_conj(q1), (0, 0, 1))
        acc = tuple(up[i] + rnd.gauss(0, noise * 0.002) for i in range(3))
        out.append(ImuSample(w, acc, dt))
    return out


def slerp_path(e0, e1, n):
    return [quat_from_euler(*[a + (b - a) * k / n for a, b in zip(e0, e1)]) for k in range(n + 1)]


def make_tracker(cfg=None):
    cfg = cfg or DEFAULTS
    return Tracker(cfg, Homography.from_screen(W, H, D))


def test_reset_from_accel_matches_gravity():
    m = Mahony()
    a = (0.3, -0.2, 0.93)
    m.reset_from_accel(a)
    n = math.sqrt(sum(c * c for c in a))
    g = m.gravity_body()
    assert all(abs(g[i] - a[i] / n) < 1e-9 for i in range(3))


def test_mahony_corrects_wrong_tilt():
    m = Mahony(kp=2.0)
    m.reset_from_accel((0, 0, 1))
    true_q = quat_from_euler(0, -0.3, 0.2)
    acc = quat_rotate(quat_conj(true_q), (0, 0, 1))
    for _ in range(2000):
        m.update((0, 0, 0), acc, 0.005)
    g = m.gravity_body()
    assert all(abs(g[i] - acc[i]) < 1e-3 for i in range(3))


def test_homography_fit_recovers_exact_mapping():
    true = Homography([0.9, 0.05, 0.48, -0.02, -1.6, 0.52, 0.03, -0.01, 1.0])
    src = [(-0.3, 0.2), (0.3, 0.18), (0.31, -0.17), (-0.29, -0.16), (0.01, 0.0)]
    dst = [true.apply(*p) for p in src]
    fit = Homography.fit(src, dst)
    for p, q in zip(src, dst):
        r = fit.apply(*p)
        assert abs(r[0] - q[0]) < 1e-9 and abs(r[1] - q[1]) < 1e-9
    inv = fit.inverse()
    u, v = inv.apply(*fit.apply(0.1, -0.05))
    assert abs(u - 0.1) < 1e-9 and abs(v + 0.05) < 1e-9


@pytest.mark.parametrize("target", [(0.5, 0.5), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.2, 0.8), (0.73, 0.31)])
def test_simulated_gun_hits_targets(target):
    """Arma parada no centro, gira até o alvo: a mira deve cair no alvo."""
    start = target_euler(0.5, 0.5)
    end = target_euler(*target)
    path = [quat_from_euler(*start)] * 50 + slerp_path(start, end, 120) + [quat_from_euler(*end)] * 30
    tr = make_tracker()
    for s in simulate(path):
        tr.update(s)
    x, y = tr.aim_xy()
    assert abs(x - target[0]) < 0.003 and abs(y - target[1]) < 0.003


def test_roll_does_not_move_cursor():
    """Girar o pulso (roll) não pode tirar a mira do lugar — igual arma real."""
    a = target_euler(0.3, 0.6, roll=0.0)
    b = target_euler(0.3, 0.6, roll=0.8)
    c = target_euler(0.5, 0.5)
    path = [quat_from_euler(*c)] * 20 + slerp_path(c, a, 80) + slerp_path(a, b, 100)
    tr = make_tracker()
    for s in simulate(path):
        tr.update(s)
    x, y = tr.aim_xy()
    assert abs(x - 0.3) < 0.003 and abs(y - 0.6) < 0.003


def test_recenter_fixes_unknown_start_heading_and_offaxis_player():
    """Jogador fora do eixo, sentado de lado: calibração por cantos + recentrar acerta."""
    eye = (0.4, -0.25)  # 40 cm à direita, 25 cm abaixo do centro
    yaw0 = 1.1  # controle ligado apontando para outra direção
    # "Calibração": medir (u, v) de cada alvo com o yaw do centro como zero.
    pts = [(0.5, 0.5), (0, 0), (1, 0), (1, 1), (0, 1)]
    c_yaw = target_euler(0.5, 0.5, eye)[0]
    src = []
    for p in pts:
        yaw, pitch, _ = target_euler(*p, eye=eye)
        f = quat_rotate(quat_from_euler(yaw - c_yaw, pitch, 0), (1, 0, 0))
        src.append(project(f))
    Hc = Homography.fit(src, pts)
    tr = Tracker(DEFAULTS, Hc)
    center = target_euler(0.5, 0.5, eye, yaw0=yaw0)
    tgt = target_euler(0.85, 0.15, eye, roll=0.3, yaw0=yaw0)
    seq = [quat_from_euler(*center)] * 40
    samples = simulate(seq)
    for s in samples:
        tr.update(s)
    tr.recenter()  # apertou Y mirando no centro
    for s in simulate([quat_from_euler(*center)] + slerp_path(center, tgt, 150)):
        tr.update(s)
    x, y = tr.aim_xy()
    assert abs(x - 0.85) < 0.004 and abs(y - 0.15) < 0.004


def test_bias_estimator_removes_drift():
    bias = (0.8, -0.5, 1.3)
    a = target_euler(0.5, 0.5)
    tr = make_tracker()
    # 1,5 s parado na mesa (com ruído) -> estima bias
    for s in simulate([quat_from_euler(*a)] * 300, gyro_bias=bias, noise=0.08):
        tr.update(s)
    assert tr.bias.acquired
    assert all(abs(tr.bias.bias[i] - bias[i]) < 0.05 for i in range(3))
    tr.recenter()
    # 20 s apontando para o centro: deriva deve ser pequena
    for s in simulate([quat_from_euler(*a)] * 4000, gyro_bias=bias, noise=0.08, seed=2):
        tr.update(s)
    x, y = tr.aim_xy()
    assert abs(x - 0.5) < 0.02 and abs(y - 0.5) < 0.01


def test_bias_estimator_ignores_hand_tremor():
    est = BiasEstimator()
    rnd = random.Random(3)
    for k in range(2000):
        g = (2.0 * math.sin(k * 0.3) + rnd.gauss(0, 1), rnd.gauss(0, 2), rnd.gauss(0, 2))
        est.update(g, (0, 0, 1), 0.005)
    assert not est.acquired


def test_one_euro_still_and_fast():
    f = OneEuro2D(1.2, 6.0, 1.0)
    rnd = random.Random(0)
    xs = [f(0.5 + rnd.gauss(0, 0.004), 0.5, k * 0.005)[0] for k in range(400)]
    assert max(xs[200:]) - min(xs[200:]) < 0.006  # tremor bem reduzido
    f.reset()
    t = 0.0
    for k in range(60):  # varredura rápida de 1 tela em 0,3 s
        t = k * 0.005
        x, _ = f(k / 60, 0.5, t)
    assert x > 0.9  # quase sem atraso


def test_trigger_uses_position_before_jerk():
    class Out:
        def __init__(self):
            self.log = []

        def move(self, x, y):
            self.log.append(("move", round(x, 3), round(y, 3)))

        def button(self, n, d):
            self.log.append(("btn", n, d))

        def key(self, n, d):
            pass

    out = Out()
    cfg = dict(DEFAULTS, smoothing={"enabled": False})
    gun = LightGun(cfg, make_tracker(cfg), out)
    for i in range(10):
        gun.history.append((1.0 + i * 0.005, 0.2, 0.2))
    gun.pos = (0.3, 0.3)  # tranco já mexeu a mira
    gun.sensor_t, gun._wall_at_sample = 1.07, 5.0
    gun.on_buttons(ButtonState(frozenset({"ZR"})), 5.0)
    assert out.log[0] == ("move", 0.2, 0.2)
    assert out.log[1] == ("btn", "left", True)
    gun.on_buttons(ButtonState(frozenset()), 1.2)
    assert out.log[-1] == ("btn", "left", False)


def test_hid_report_parsing():
    data = [0] * 49
    data[0] = 0x30
    data[3] = 0x80 | 0x01  # ZR + Y
    data[4] = 0x02  # PLUS
    import struct

    struct.pack_into("<6h", buf := bytearray(12), 0, 100, -200, 4096, 10, 20, -30)
    data[13:25] = list(buf)
    assert parse_buttons(data) == {"ZR", "Y", "PLUS"}
    (g, a), *_ = parse_imu(data, "joycon-r", 0.07, 1 / 4096)
    assert a == pytest.approx((100 / 4096, 200 / 4096, -1.0))
    assert g == pytest.approx((0.7, -1.4, 2.1))
