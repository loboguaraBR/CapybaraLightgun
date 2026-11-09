"""macOS: acesso ao sistema via ctypes (Quartz/CoreGraphics, Acessibilidade, IOKit).

Sem dependências extras. Tudo aqui só é importado no macOS.

Permissões que o macOS pede (Ajustes do Sistema → Privacidade e Segurança):
- Acessibilidade: para mover o cursor e clicar (saída "mouse do sistema").
- Monitoramento de Entrada: para ler controles e o mouse em segundo plano.
"""
from __future__ import annotations

import ctypes
import subprocess
from ctypes import POINTER, Structure, byref, c_bool, c_double, c_int32, c_int64, c_uint16, c_uint32, c_void_p

_FW = "/System/Library/Frameworks/{0}.framework/{0}"


class CGPoint(Structure):
    _fields_ = [("x", c_double), ("y", c_double)]


class CGSize(Structure):
    _fields_ = [("width", c_double), ("height", c_double)]


class CGRect(Structure):
    _fields_ = [("origin", CGPoint), ("size", CGSize)]


cg = ctypes.cdll.LoadLibrary(_FW.format("CoreGraphics"))
cf = ctypes.cdll.LoadLibrary(_FW.format("CoreFoundation"))

cf.CFRelease.argtypes = [c_void_p]
cg.CGEventCreate.restype = c_void_p
cg.CGEventCreate.argtypes = [c_void_p]
cg.CGEventGetLocation.restype = CGPoint
cg.CGEventGetLocation.argtypes = [c_void_p]
cg.CGEventSourceButtonState.restype = c_bool
cg.CGEventSourceButtonState.argtypes = [c_int32, c_uint32]
cg.CGGetActiveDisplayList.restype = c_int32
cg.CGGetActiveDisplayList.argtypes = [c_uint32, POINTER(c_uint32), POINTER(c_uint32)]
cg.CGDisplayBounds.restype = CGRect
cg.CGDisplayBounds.argtypes = [c_uint32]
cg.CGMainDisplayID.restype = c_uint32
cg.CGEventCreateMouseEvent.restype = c_void_p
cg.CGEventCreateMouseEvent.argtypes = [c_void_p, c_uint32, CGPoint, c_uint32]
cg.CGEventCreateKeyboardEvent.restype = c_void_p
cg.CGEventCreateKeyboardEvent.argtypes = [c_void_p, c_uint16, c_bool]
cg.CGEventSetIntegerValueField.argtypes = [c_void_p, c_uint32, c_int64]
cg.CGEventPost.argtypes = [c_uint32, c_void_p]

# Tipos de evento
LEFT_DOWN, LEFT_UP, RIGHT_DOWN, RIGHT_UP, MOVED = 1, 2, 3, 4, 5
LEFT_DRAG, RIGHT_DRAG, OTHER_DOWN, OTHER_UP, OTHER_DRAG = 6, 7, 25, 26, 27
HID_EVENT_TAP = 0
STATE_HID = 1  # estado físico dos botões
FIELD_CLICK_STATE, FIELD_DELTA_X, FIELD_DELTA_Y = 1, 4, 5

# Códigos de tecla virtuais do macOS (layout ANSI)
KEYCODES = {
    "a": 0x00, "s": 0x01, "d": 0x02, "f": 0x03, "h": 0x04, "g": 0x05, "z": 0x06, "x": 0x07, "c": 0x08,
    "v": 0x09, "b": 0x0B, "q": 0x0C, "w": 0x0D, "e": 0x0E, "r": 0x0F, "y": 0x10, "t": 0x11, "o": 0x1F,
    "u": 0x20, "i": 0x22, "p": 0x23, "l": 0x25, "j": 0x26, "k": 0x28, "n": 0x2D, "m": 0x2E,
    "1": 0x12, "2": 0x13, "3": 0x14, "4": 0x15, "5": 0x17, "6": 0x16, "7": 0x1A, "8": 0x1C, "9": 0x19, "0": 0x1D,
    "enter": 0x24, "return": 0x24, "tab": 0x30, "space": 0x31, "backspace": 0x33, "esc": 0x35, "escape": 0x35,
    "shift": 0x38, "ctrl": 0x3B, "control": 0x3B, "alt": 0x3A,
    "left": 0x7B, "right": 0x7C, "down": 0x7D, "up": 0x7E,
    "f1": 0x7A, "f2": 0x78, "f3": 0x63, "f4": 0x76, "f5": 0x60, "f6": 0x61, "f7": 0x62, "f8": 0x64,
    "f9": 0x65, "f10": 0x6D, "f11": 0x67, "f12": 0x6F,
    "home": 0x73, "end": 0x77, "pageup": 0x74, "pagedown": 0x79, "delete": 0x75, "insert": 0x72,
    "pause": 0x71,  # F15 (o Mac não tem Pause)
}


# ---- telas e cursor --------------------------------------------------------
def displays() -> list:
    """Retângulos (x, y, w, h) de cada tela, em pontos, coordenadas globais."""
    ids = (c_uint32 * 16)()
    n = c_uint32(0)
    if cg.CGGetActiveDisplayList(16, ids, byref(n)) != 0 or n.value == 0:
        ids[0] = cg.CGMainDisplayID()
        n.value = 1
    out = []
    for i in range(n.value):
        r = cg.CGDisplayBounds(ids[i])
        out.append((r.origin.x, r.origin.y, r.size.width, r.size.height))
    return out


def desktop() -> tuple:
    """União de todas as telas: (x, y, w, h)."""
    ds = displays()
    x0 = min(d[0] for d in ds)
    y0 = min(d[1] for d in ds)
    x1 = max(d[0] + d[2] for d in ds)
    y1 = max(d[1] + d[3] for d in ds)
    return (x0, y0, max(1.0, x1 - x0), max(1.0, y1 - y0))


def cursor() -> tuple:
    ev = cg.CGEventCreate(None)
    p = cg.CGEventGetLocation(ev)
    cf.CFRelease(ev)
    return (p.x, p.y)


def button_down(index: int) -> bool:
    """0 = esquerdo, 1 = direito, 2 = meio, 3/4 = laterais."""
    return bool(cg.CGEventSourceButtonState(STATE_HID, index))


# ---- eventos sintéticos ----------------------------------------------------
def post_mouse(kind: int, x: float, y: float, button: int = 0, dx: int = 0, dy: int = 0) -> None:
    ev = cg.CGEventCreateMouseEvent(None, kind, CGPoint(x, y), button)
    if not ev:
        return
    if kind in (LEFT_DOWN, LEFT_UP, RIGHT_DOWN, RIGHT_UP, OTHER_DOWN, OTHER_UP):
        cg.CGEventSetIntegerValueField(ev, FIELD_CLICK_STATE, 1)
    if dx or dy:
        cg.CGEventSetIntegerValueField(ev, FIELD_DELTA_X, int(dx))
        cg.CGEventSetIntegerValueField(ev, FIELD_DELTA_Y, int(dy))
    cg.CGEventPost(HID_EVENT_TAP, ev)
    cf.CFRelease(ev)


def post_key(code: int, down: bool) -> None:
    ev = cg.CGEventCreateKeyboardEvent(None, code, down)
    if ev:
        cg.CGEventPost(HID_EVENT_TAP, ev)
        cf.CFRelease(ev)


# ---- permissões ------------------------------------------------------------
def accessibility_ok(prompt: bool = False) -> bool:
    """Permissão de Acessibilidade (necessária para mover o cursor/clicar)."""
    try:
        ax = ctypes.cdll.LoadLibrary(_FW.format("ApplicationServices"))
        ax.AXIsProcessTrusted.restype = c_bool
        if not prompt:
            return bool(ax.AXIsProcessTrusted())
        key = c_void_p.in_dll(ax, "kAXTrustedCheckOptionPrompt")
        true = c_void_p.in_dll(cf, "kCFBooleanTrue")
        kcb = ctypes.addressof(ctypes.c_char.in_dll(cf, "kCFTypeDictionaryKeyCallBacks"))
        vcb = ctypes.addressof(ctypes.c_char.in_dll(cf, "kCFTypeDictionaryValueCallBacks"))
        cf.CFDictionaryCreate.restype = c_void_p
        cf.CFDictionaryCreate.argtypes = [c_void_p, POINTER(c_void_p), POINTER(c_void_p), ctypes.c_long, c_void_p, c_void_p]
        keys = (c_void_p * 1)(key.value)
        vals = (c_void_p * 1)(true.value)
        opts = cf.CFDictionaryCreate(None, keys, vals, 1, kcb, vcb)
        ax.AXIsProcessTrustedWithOptions.restype = c_bool
        ax.AXIsProcessTrustedWithOptions.argtypes = [c_void_p]
        ok = bool(ax.AXIsProcessTrustedWithOptions(opts))
        cf.CFRelease(opts)
        return ok
    except Exception:
        return True  # não dá para checar: não bloqueia


def input_monitoring_ok(prompt: bool = False) -> bool:
    """Permissão de Monitoramento de Entrada (ler controles/mouse em segundo plano)."""
    try:
        io = ctypes.cdll.LoadLibrary(_FW.format("IOKit"))
        if not hasattr(io, "IOHIDCheckAccess"):
            return True  # macOS < 10.15
        io.IOHIDCheckAccess.restype = c_uint32
        io.IOHIDCheckAccess.argtypes = [c_uint32]
        status = io.IOHIDCheckAccess(1)  # kIOHIDRequestTypeListenEvent
        if status == 0:
            return True
        if prompt:
            io.IOHIDRequestAccess.restype = c_bool
            io.IOHIDRequestAccess.argtypes = [c_uint32]
            return bool(io.IOHIDRequestAccess(1))
        return False
    except Exception:
        return True


def open_privacy(pane: str) -> None:
    """pane: "Accessibility" ou "ListenEvent"."""
    subprocess.Popen(["open", f"x-apple.systempreferences:com.apple.preference.security?Privacy_{pane}"])


def missing_permissions() -> list:
    out = []
    if not accessibility_ok():
        out.append("Accessibility")
    if not input_monitoring_ok():
        out.append("Input Monitoring")
    return out


def request_permissions() -> None:
    if not accessibility_ok(prompt=True):
        open_privacy("Accessibility")
    if not input_monitoring_ok(prompt=True):
        open_privacy("ListenEvent")
