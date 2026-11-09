"""Qualquer controle com giroscópio, via SDL (Linux e Windows).

O SDL (o mesmo da Steam e dos emuladores) reconhece DualSense, DualShock 4,
Steam Controller/Deck, 8BitDo e outros com sensores, entrega giroscópio e
acelerômetro já calibrados, com carimbo de tempo, e faz a vibração.

Os controles Nintendo ficam de fora daqui: eles têm o caminho próprio
(hid-nintendo / hidapi), que já é o mais preciso.

Convenção do SDL: X = direita, Y = cima, Z = em direção ao jogador; giroscópio
em rad/s, acelerômetro em m/s² (≈ +9,8 "para cima" em repouso).
"""
from __future__ import annotations

import ctypes
import math
import os
import time
import warnings

from .base import ButtonState, DeviceLost, ImuSample, NoDeviceFound
from .linux_evdev_axes import to_lightgun_axes

G = 9.80665
RAD2DEG = 180.0 / math.pi

_HINTS = {
    "SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS": "1",
    "SDL_GAMECONTROLLER_USE_BUTTON_LABELS": "0",  # botões por posição
    "SDL_JOYSTICK_HIDAPI_SWITCH": "0",  # Nintendo tem caminho próprio
    "SDL_JOYSTICK_HIDAPI_JOY_CONS": "0",
    "SDL_JOYSTICK_HIDAPI_PS4_RUMBLE": "1",
    "SDL_JOYSTICK_HIDAPI_PS5_RUMBLE": "1",
}


def _sdl():
    for k, v in _HINTS.items():
        os.environ.setdefault(k, v)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            import sdl2
        except ImportError as exc:
            raise ImportError("instale PySDL2 e pysdl2-dll (pip install PySDL2 pysdl2-dll)") from exc
    return sdl2


def _button_map(sdl2) -> dict:
    # SDL nomeia como Xbox (A = baixo); o programa usa nomes posicionais Nintendo.
    m = {
        sdl2.SDL_CONTROLLER_BUTTON_A: "B", sdl2.SDL_CONTROLLER_BUTTON_B: "A",
        sdl2.SDL_CONTROLLER_BUTTON_X: "Y", sdl2.SDL_CONTROLLER_BUTTON_Y: "X",
        sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER: "L", sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: "R",
        sdl2.SDL_CONTROLLER_BUTTON_BACK: "MINUS", sdl2.SDL_CONTROLLER_BUTTON_START: "PLUS",
        sdl2.SDL_CONTROLLER_BUTTON_GUIDE: "HOME", sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK: "LSTICK",
        sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK: "RSTICK", sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: "UP",
        sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: "DOWN", sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: "LEFT",
        sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: "RIGHT",
    }
    for attr, name in (("SDL_CONTROLLER_BUTTON_MISC1", "CAPTURE"), ("SDL_CONTROLLER_BUTTON_TOUCHPAD", "CAPTURE"),
                       ("SDL_CONTROLLER_BUTTON_PADDLE1", "P1"), ("SDL_CONTROLLER_BUTTON_PADDLE2", "P2"),
                       ("SDL_CONTROLLER_BUTTON_PADDLE3", "P3"), ("SDL_CONTROLLER_BUTTON_PADDLE4", "P4")):
        if hasattr(sdl2, attr):
            m[getattr(sdl2, attr)] = name
    return m


def sdl_to_sample(gyro_rad, accel_ms2, dt: float) -> ImuSample:
    gyro = to_lightgun_axes("sdl", tuple(v * RAD2DEG for v in gyro_rad))
    accel = to_lightgun_axes("sdl", tuple(v / G for v in accel_ms2))
    return ImuSample(gyro, accel, dt)


def _name(sdl2, ctrl) -> str:
    n = sdl2.SDL_GameControllerName(ctrl)
    return n.decode("utf-8", "replace") if n else "controle"


def _is_nintendo(sdl2, ctrl) -> bool:
    return sdl2.SDL_GameControllerGetVendor(ctrl) == 0x057E


def list_devices() -> list:
    sdl2 = _sdl()
    if sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_SENSOR) != 0:
        return []
    out = []
    try:
        sdl2.SDL_PumpEvents()
        for i in range(sdl2.SDL_NumJoysticks()):
            if not sdl2.SDL_IsGameController(i):
                continue
            c = sdl2.SDL_GameControllerOpen(i)
            if not c:
                continue
            out.append({"name": _name(sdl2, c), "gyro": bool(sdl2.SDL_GameControllerHasSensor(c, sdl2.SDL_SENSOR_GYRO))})
            sdl2.SDL_GameControllerClose(c)
    finally:
        sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_SENSOR)
    return out


class SdlSource:
    family = "sdl"

    def __init__(self, sdl2, ctrl):
        self.sdl2 = sdl2
        self.ctrl = ctrl
        self.kind = "sdl"
        self.name = f"{_name(sdl2, ctrl)} (SDL)"
        joy = sdl2.SDL_GameControllerGetJoystick(ctrl)
        self.instance = sdl2.SDL_JoystickInstanceID(joy)
        self.buttons = _button_map(sdl2)
        for s in (sdl2.SDL_SENSOR_GYRO, sdl2.SDL_SENSOR_ACCEL):
            sdl2.SDL_GameControllerSetSensorEnabled(ctrl, s, sdl2.SDL_TRUE)

    @classmethod
    def open(cls, prefer: str = "auto"):
        sdl2 = _sdl()
        if sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_SENSOR) != 0:
            raise NoDeviceFound("SDL não iniciou: " + sdl2.SDL_GetError().decode())
        sdl2.SDL_PumpEvents()
        no_gyro = []
        for i in range(sdl2.SDL_NumJoysticks()):
            if not sdl2.SDL_IsGameController(i):
                continue
            c = sdl2.SDL_GameControllerOpen(i)
            if not c:
                continue
            if _is_nintendo(sdl2, c):
                sdl2.SDL_GameControllerClose(c)
                continue
            if sdl2.SDL_GameControllerHasSensor(c, sdl2.SDL_SENSOR_GYRO):
                return cls(sdl2, c)
            no_gyro.append(_name(sdl2, c))
            sdl2.SDL_GameControllerClose(c)
        sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_SENSOR)
        if no_gyro:
            exc = NoDeviceFound(f"{', '.join(no_gyro)}: sem giroscópio (controles de Xbox comuns não têm). "
                                "Use o mouse do sistema ou um controle com giroscópio.")
            exc.no_gyro = no_gyro
            raise exc
        raise NoDeviceFound("nenhum controle com giroscópio pelo SDL")

    def rumble(self, ms: int = 45, strength: float = 0.7) -> None:
        mag = int(max(0.0, min(1.0, strength)) * 0xFFFF)
        self.sdl2.SDL_GameControllerRumble(self.ctrl, mag, mag, int(ms))

    def events(self):
        sdl2 = self.sdl2
        ev = sdl2.SDL_Event()
        acc = [0.0, G, 0.0]
        pressed: set = set()
        triggers = {sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT: "ZL", sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT: "ZR"}
        last_us = None
        last_data = time.monotonic()
        last_buttons = frozenset()
        while True:
            got = sdl2.SDL_WaitEventTimeout(ctypes.byref(ev), 100)
            while got:
                t = ev.type
                if t == sdl2.SDL_CONTROLLERSENSORUPDATE and ev.csensor.which == self.instance:
                    d = ev.csensor.data
                    if ev.csensor.sensor == sdl2.SDL_SENSOR_ACCEL:
                        acc = [d[0], d[1], d[2]]
                    elif ev.csensor.sensor == sdl2.SDL_SENSOR_GYRO:
                        us = ev.csensor.timestamp_us or ev.csensor.timestamp * 1000
                        dt = 0.004 if last_us is None else (us - last_us) / 1e6
                        last_us = us
                        if not 0 < dt < 0.1:
                            dt = 0.004
                        last_data = time.monotonic()
                        yield sdl_to_sample((d[0], d[1], d[2]), acc, dt)
                elif t in (sdl2.SDL_CONTROLLERBUTTONDOWN, sdl2.SDL_CONTROLLERBUTTONUP) and ev.cbutton.which == self.instance:
                    n = self.buttons.get(ev.cbutton.button)
                    if n:
                        (pressed.add if t == sdl2.SDL_CONTROLLERBUTTONDOWN else pressed.discard)(n)
                elif t == sdl2.SDL_CONTROLLERAXISMOTION and ev.caxis.which == self.instance:
                    n = triggers.get(ev.caxis.axis)
                    if n:
                        v = ev.caxis.value
                        if v > 12000:
                            pressed.add(n)
                        elif v < 6000:
                            pressed.discard(n)
                elif t == sdl2.SDL_CONTROLLERDEVICEREMOVED and ev.cdevice.which == self.instance:
                    raise DeviceLost("controle desconectado")
                got = sdl2.SDL_PollEvent(ctypes.byref(ev))
            fs = frozenset(pressed)
            if fs != last_buttons:
                last_buttons = fs
                yield ButtonState(fs)
            if time.monotonic() - last_data > 2.0:
                raise DeviceLost("o controle parou de enviar o giroscópio")

    def close(self) -> None:
        try:
            self.sdl2.SDL_GameControllerClose(self.ctrl)
            self.sdl2.SDL_QuitSubSystem(self.sdl2.SDL_INIT_GAMECONTROLLER | self.sdl2.SDL_INIT_SENSOR)
        except Exception:
            pass
