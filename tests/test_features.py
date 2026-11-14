"""Recursos do cliente: perfis, tiro automático, modo relativo, calibração."""
import copy

from capybara_lightgun.calibration import Calibrator
from capybara_lightgun.config import DEFAULTS, ConfigStore, merge
from capybara_lightgun.engine import LightGun
from capybara_lightgun.inputs import ButtonState
from capybara_lightgun.fusion import quat_from_euler, quat_rotate

from test_aim import make_tracker, simulate, slerp_path, target_euler


class Rec:
    def __init__(self):
        self.log = []

    def move(self, x, y):
        self.log.append(("move", x, y))

    def move_rel(self, dx, dy):
        self.log.append(("rel", dx, dy))

    def button(self, n, d):
        self.log.append(("btn", n, d))

    def key(self, n, d):
        self.log.append(("key", n, d))


def test_store_profiles_roundtrip(tmp_path):
    p = tmp_path / "c.json"
    s = ConfigStore(p)
    assert "Default (light gun)" in s.profiles
    s.create("Meu jogo", "Rapid-fire arcade")
    s.active = "Meu jogo"
    s.save()
    s2 = ConfigStore(p)
    assert s2.active == "Meu jogo"
    assert s2.effective()["buttons"]["ZR"] == "autofire"
    s2.rename("Meu jogo", "Outro")
    assert s2.active == "Outro"


def test_legacy_flat_config_is_migrated(tmp_path):
    p = tmp_path / "c.json"
    p.write_text('{"aim": {"sensitivity_x": 1.5}}')
    s = ConfigStore(p)
    assert s.effective()["aim"]["sensitivity_x"] == 1.5
    assert s.effective()["aim"]["sensitivity_y"] == 1.0


def test_autofire_toggles_and_releases():
    cfg = merge(DEFAULTS, {"buttons": {"ZR": "autofire"}, "autofire_hz": 10})
    out = Rec()
    gun = LightGun(cfg, make_tracker(cfg), out)
    e = target_euler(0.5, 0.5)
    samples = simulate([quat_from_euler(*e)] * 2)
    gun.on_imu(samples[0], 0.0)
    gun.on_buttons(ButtonState(frozenset({"ZR"})), 0.0)
    for k, s in enumerate(simulate([quat_from_euler(*e)] * 201)):  # 1 s
        gun.on_imu(s, 0.005 * k)
    clicks = [x for x in out.log if x[0] == "btn"]
    downs = sum(1 for x in clicks if x[2])
    assert 9 <= downs <= 11
    gun.on_buttons(ButtonState(frozenset()), 1.0)
    assert [x for x in out.log if x[0] == "btn"][-1] == ("btn", "left", False)


def test_relative_mode_sends_deltas():
    cfg = merge(DEFAULTS, {"mode": "relative", "smoothing": {"enabled": False}})
    out = Rec()
    gun = LightGun(cfg, make_tracker(cfg), out)
    a, b = target_euler(0.5, 0.5), target_euler(0.75, 0.5)
    for k, s in enumerate(simulate([quat_from_euler(*a)] * 5 + slerp_path(a, b, 50))):
        gun.on_imu(s, 0.005 * k)
    dx = sum(x[1] for x in out.log if x[0] == "rel")
    assert abs(dx - 0.25 * 1920) < 5
    assert not any(x[0] == "move" for x in out.log)


def test_calibrator_from_forward_vectors():
    tr = make_tracker()
    cal = Calibrator(tr)
    eye_yaw = 0.7  # direção arbitrária
    for x, y in [(0.5, 0.5), (0, 0), (1, 0), (1, 1), (0, 1)]:
        yaw, pitch, _ = target_euler(x, y, yaw0=eye_yaw)
        done = cal.add(quat_rotate(quat_from_euler(yaw, pitch, 0), (1, 0, 0)))
    assert done and cal.result[1] < 1e-6


def test_capture_hook_blocks_click():
    out = Rec()
    cfg = copy.deepcopy(DEFAULTS)
    gun = LightGun(cfg, make_tracker(cfg), out)
    got = []
    gun.capture_hook = got.append
    for k, s in enumerate(simulate([quat_from_euler(*target_euler(0.5, 0.5))] * 60)):
        gun.on_imu(s, 0.005 * k)
    gun.on_buttons(ButtonState(frozenset({"ZR"})), 0.3)
    assert len(got) == 1 and not any(x[0] == "btn" for x in out.log)


def test_yield_blocks_moves_until_trigger():
    out = Rec()
    cfg = copy.deepcopy(DEFAULTS)
    cfg["smoothing"]["enabled"] = False
    gun = LightGun(cfg, make_tracker(cfg), out)
    samples = simulate([quat_from_euler(*target_euler(0.5, 0.5))] * 40)
    gun.yield_until = 100.0
    for k, s in enumerate(samples[:20]):
        gun.on_imu(s, 1.0 + 0.005 * k)
    assert not any(x[0] == "move" for x in out.log)  # cedendo: não mexe no cursor
    gun.on_buttons(ButtonState(frozenset({"ZR"})), 1.2)  # atirou: retoma
    assert gun.yield_until == 0.0
    for k, s in enumerate(samples[20:]):
        gun.on_imu(s, 2.0 + 0.005 * k)
    assert any(x[0] == "move" for x in out.log)


def _bursty_run(interp_ms):
    """Arma girando em velocidade constante; Bluetooth entrega 3 leituras a cada
    15 ms e trava 120 ms no meio. Mede a uniformidade do cursor a 250 Hz."""
    cfg = merge(DEFAULTS, {"smoothing": {"enabled": False}, "motion": {"interp_ms": interp_ms}})
    gun = LightGun(cfg, make_tracker(cfg), Rec())
    a, b = target_euler(0.2, 0.5), target_euler(0.8, 0.5)
    samples = simulate([quat_from_euler(*a)] * 40 + slerp_path(a, b, 240) + [quat_from_euler(*b)] * 40)
    # horário de chegada: rajadas de 3 a cada 15 ms; entre as leituras 150 e
    # 174 o Bluetooth trava 120 ms e depois entrega tudo de uma vez.
    arrivals, t = [], 1.0
    for i in range(len(samples)):
        if i % 3 == 0:
            t += 0.015
        arrivals.append(t)
    for i in range(150, 174):
        arrivals[i] = arrivals[174]
    shown, k = [], 0
    clock = 1.2
    while clock < arrivals[-1]:
        while k < len(samples) and arrivals[k] <= clock:
            gun.on_imu(samples[k], arrivals[k])
            k += 1
        shown.append(gun.render_pos(clock)[0] if interp_ms else gun.pos[0])
        clock += 0.004
    # só o trecho em que a arma está girando
    steps = [b2 - a2 for a2, b2 in zip(shown, shown[1:])]
    lo = next(i for i, v in enumerate(shown) if v > 0.21)
    hi = next(i for i, v in enumerate(shown) if v > 0.79)
    steps = steps[lo:hi]
    return max(abs(s) for s in steps), sum(1 for s in steps if abs(s) < 1e-9) / len(steps)


def test_motion_is_uniform_with_bursty_bluetooth():
    raw_max, raw_still = _bursty_run(0)
    smooth_max, smooth_still = _bursty_run(16)
    # sem suavização: saltos grandes e o cursor parado ~2/3 dos quadros;
    # com: passos pequenos e quase nunca parado durante o giro
    assert smooth_max < raw_max * 0.5
    assert smooth_still < raw_still * 0.5


def test_old_profile_gets_new_default_buttons_but_keeps_its_own(tmp_path):
    """Perfil salvo antes do suporte a mouse: ganha MOUSE_*, sem perder o que já tinha."""
    import json

    from capybara_lightgun.config import ConfigStore

    p = tmp_path / "c.json"
    p.write_text(json.dumps({"active": "old", "profiles": {
        "old": {"buttons": {"ZR": "autofire", "A": "", "BTN_TR2": "key:r"}},
    }}))
    b = ConfigStore(p).effective()["buttons"]
    assert b["MOUSE_LEFT"] == "trigger"  # veio do padrão
    assert b["ZR"] == "autofire"  # mapeamento do perfil manda
    assert b["A"] == ""  # "nada" escolhido pelo usuário não volta
    assert b["BTN_TR2"] == "key:r"  # nome cru do evdev continua
