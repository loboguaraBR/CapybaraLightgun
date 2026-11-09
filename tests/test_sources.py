"""Fontes novas (PlayStation, mouse) e recursos de arma (recarregar, coice, perfis automáticos)."""
import struct

from lightgun_joypad.client import ClientApp, effective_config
from lightgun_joypad.config import DEFAULTS, ConfigStore, merge
from lightgun_joypad.engine import LightGun
from lightgun_joypad.fusion import quat_from_euler
from lightgun_joypad.inputs import ButtonState, ImuSample, PointerSample
from lightgun_joypad.inputs.linux_evdev_axes import to_lightgun_axes
from lightgun_joypad.inputs.ps_hid import parse_report

from test_aim import make_tracker, simulate, target_euler
from test_features import Rec


def test_playstation_axes_flat_controller_is_level():
    # DualSense deitado na mesa: gravidade em +Y (padrão Sony/SDL) -> "para cima" interno (+Z)
    assert to_lightgun_axes("playstation", (0.0, 1.0, 0.0)) == (0.0, -0.0, 1.0)
    # girar para a esquerda = yaw positivo em torno do eixo vertical (Y Sony -> Z interno)
    assert to_lightgun_axes("playstation", (0.0, 30.0, 0.0))[2] == 30.0
    # a frente do controle (−Z Sony, longe do jogador) é o cano (+X interno)
    assert to_lightgun_axes("playstation", (0.0, 0.0, -1.0))[0] == 1.0


def test_ps5_usb_report_parsing():
    data = bytearray(64)
    data[0] = 0x01
    data[8] = 0x08 | 0x20  # d-pad solto (8) + ✕
    data[9] = 0x08  # R2
    data[10] = 0x01  # PS
    struct.pack_into("<3h", data, 16, 16, 0, 0)  # gyro X = 1 °/s
    struct.pack_into("<3h", data, 22, 0, 8192, 0)  # accel Y = 1 g
    buttons, gyro, accel = parse_report(list(data), "ps5")
    assert buttons == {"B", "ZR", "HOME"}
    assert accel == (0.0, -0.0, 1.0)
    assert gyro[1] == -1.0


def test_ps4_bt_report_parsing():
    data = bytearray(78)
    data[0] = 0x11
    data[3 + 4] = 0x00 | 0x80  # d-pad cima + △
    data[3 + 5] = 0x02  # R1
    buttons, _, _ = parse_report(list(data), "ps4")
    assert buttons == {"UP", "X", "R"}


def _gun(**over):
    cfg = merge(DEFAULTS, dict({"smoothing": {"enabled": False}, "motion": {"interp_ms": 0}}, **over))
    out = Rec()
    return LightGun(cfg, make_tracker(cfg), out), out


def test_trigger_aiming_offscreen_reloads():
    gun, out = _gun(reload={"offscreen_aim": True, "offscreen_margin": 0.02, "shake": False, "shake_g": 2.5})
    kicks = []
    gun.feedback = lambda ms, s: kicks.append(ms)
    a = target_euler(0.5, 0.5)
    b = target_euler(1.3, 0.5)  # 30% além da borda direita
    for k, s in enumerate(simulate([quat_from_euler(*a)] * 5 + [quat_from_euler(*a)] + [quat_from_euler(*b)] * 5)):
        gun.on_imu(s, 0.005 * k)
    assert gun.outside
    gun.on_buttons(ButtonState(frozenset({"ZR"})), 1.0)
    ox, oy = DEFAULTS["offscreen_position"]
    assert ("move", ox, oy) in out.log and ("btn", "left", True) in out.log
    assert kicks, "coice no tiro"
    assert gun.shots == 0  # não contou como tiro na tela


def test_shake_reloads_once():
    gun, out = _gun(reload={"offscreen_aim": True, "offscreen_margin": 0.02, "shake": True, "shake_g": 2.5})
    still = ImuSample((0, 0, 0), (0, 0, 1), 0.005)
    jolt = ImuSample((0, 0, 0), (0, 0, 3.5), 0.005)
    seq = [still] * 5 + [jolt, jolt] + [still] * 30
    for k, s in enumerate(seq):
        gun.on_imu(s, 0.005 * k)
    downs = [x for x in out.log if x == ("btn", "left", True)]
    ups = [x for x in out.log if x == ("btn", "left", False)]
    assert len(downs) == 1 and len(ups) == 1


def test_mouse_pointer_source_maps_region():
    gun, out = _gun(region=[0.5, 0.0, 1.0, 1.0])  # monitor da direita
    gun.on_pointer(PointerSample(0.75, 0.25, 0.004), 0.0)
    assert out.log[-1] == ("move", 0.5, 0.25)
    gun.on_buttons(ButtonState(frozenset({"MOUSE_LEFT"})), 0.01)
    assert ("btn", "left", True) in out.log


def test_system_mouse_passthrough_no_double_clicks():
    """Sem controle: mouse do sistema como fonte E saída (Windows ou modo mouse)."""
    gun, out = _gun(output_target="mouse")
    gun.on_pointer(PointerSample(0.3, 0.4, 0.004), 0.0)
    assert not any(x[0] == "move" for x in out.log)  # o cursor já está lá
    gun.on_buttons(ButtonState(frozenset({"MOUSE_LEFT"})), 0.01)
    gun.on_buttons(ButtonState(frozenset()), 0.05)
    assert not any(x[0] == "btn" for x in out.log)  # clique físico já foi; não dobra
    assert gun.shots == 1
    # botão direito = tiro fora da tela: vai ao canto, clica e volta
    gun.on_buttons(ButtonState(frozenset({"MOUSE_RIGHT"})), 0.1)
    gun.on_buttons(ButtonState(frozenset()), 0.2)
    ox, oy = DEFAULTS["offscreen_position"]
    assert out.log == [("move", ox, oy), ("btn", "left", True), ("btn", "left", False), ("move", 0.3, 0.4)]


def test_sdl_sample_conversion():
    from lightgun_joypad.inputs.sdl_source import sdl_to_sample

    s = sdl_to_sample((0.0, 1.0, 0.0), (0.0, 9.80665, 0.0), 0.004)  # deitado; girando p/ esquerda
    assert s.accel_g == (0.0, -0.0, 1.0)
    assert abs(s.gyro_dps[2] - 57.29578) < 1e-3


def test_auto_profile_switch(tmp_path):
    s = ConfigStore(tmp_path / "c.json")
    s.profiles["MAME (-offscreen_reload)"]["auto_match"] = "mame, groovymame"
    app = ClientApp(s, str(tmp_path / "cal.json"), output_backend="none")
    assert app.auto_switch('WM_CLASS = "mame" "MAME: Time Crisis"') == "MAME (-offscreen_reload)"
    assert s.active == "MAME (-offscreen_reload)"
    assert app.auto_switch('WM_CLASS = "google-chrome"') == "Default (light gun)"  # volta ao manual
    assert app.auto_switch("Light Gun Joypad") is None
