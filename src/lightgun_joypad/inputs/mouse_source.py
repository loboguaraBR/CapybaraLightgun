"""Mouse comum como light gun.

Lê a posição do cursor e os botões do mouse a 250 Hz e alimenta a light gun
virtual (modo "Só light gun (driver)"): o emulador recebe uma arma com
coordenadas absolutas, recarregar, tiro automático e teclas mapeadas.

Botões: MOUSE_LEFT, MOUSE_RIGHT, MOUSE_MIDDLE (e MOUSE_X1/X2 no Windows).
Linux: X11 (XQueryPointer, sem root). Wayland não permite ler o cursor global.
macOS: Quartz (posição) + estado físico dos botões.
"""
from __future__ import annotations

import ctypes
import ctypes.util
import os
import sys
import time

from .base import ButtonState, NoDeviceFound, PointerSample


class _X11:
    def __init__(self):
        if not os.environ.get("DISPLAY"):
            raise NoDeviceFound("mouse como arma precisa do X11 (no Wayland o cursor global não é acessível)")
        lib = ctypes.util.find_library("X11")
        if not lib:
            raise NoDeviceFound("libX11 não encontrada")
        x = ctypes.cdll.LoadLibrary(lib)
        x.XOpenDisplay.restype = ctypes.c_void_p
        x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x.XDefaultRootWindow.restype = ctypes.c_ulong
        x.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        x.XDefaultScreen.argtypes = [ctypes.c_void_p]
        x.XDisplayWidth.argtypes = [ctypes.c_void_p, ctypes.c_int]
        x.XDisplayHeight.argtypes = [ctypes.c_void_p, ctypes.c_int]
        x.XQueryPointer.argtypes = [ctypes.c_void_p, ctypes.c_ulong] + [ctypes.c_void_p] * 7
        x.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.x = x
        self.dpy = x.XOpenDisplay(None)
        if not self.dpy:
            raise NoDeviceFound("não consegui abrir o display X11")
        self.root = x.XDefaultRootWindow(self.dpy)
        scr = x.XDefaultScreen(self.dpy)
        self.w = max(1, x.XDisplayWidth(self.dpy, scr))
        self.h = max(1, x.XDisplayHeight(self.dpy, scr))
        self._r = ctypes.c_ulong()
        self._c = ctypes.c_ulong()
        self._rx, self._ry, self._wx, self._wy = (ctypes.c_int() for _ in range(4))
        self._m = ctypes.c_uint()

    def query(self):
        b = ctypes.byref
        self.x.XQueryPointer(self.dpy, self.root, b(self._r), b(self._c), b(self._rx), b(self._ry),
                             b(self._wx), b(self._wy), b(self._m))
        m = self._m.value
        names = set()
        if m & (1 << 8):
            names.add("MOUSE_LEFT")
        if m & (1 << 9):
            names.add("MOUSE_MIDDLE")
        if m & (1 << 10):
            names.add("MOUSE_RIGHT")
        return self._rx.value / (self.w - 1), self._ry.value / (self.h - 1), frozenset(names)

    def close(self):
        if self.dpy:
            self.x.XCloseDisplay(self.dpy)
            self.dpy = None


class _Win:
    def __init__(self):
        from ctypes import wintypes

        self.u = ctypes.WinDLL("user32")
        try:
            ctypes.WinDLL("shcore").SetProcessDpiAwareness(2)
        except Exception:
            pass
        self.pt = wintypes.POINT()

    def query(self):
        u = self.u
        u.GetCursorPos(ctypes.byref(self.pt))
        vx, vy = u.GetSystemMetrics(76), u.GetSystemMetrics(77)
        vw, vh = max(2, u.GetSystemMetrics(78)), max(2, u.GetSystemMetrics(79))
        names = set()
        for vk, n in ((0x01, "MOUSE_LEFT"), (0x02, "MOUSE_RIGHT"), (0x04, "MOUSE_MIDDLE"),
                      (0x05, "MOUSE_X1"), (0x06, "MOUSE_X2")):
            if u.GetAsyncKeyState(vk) & 0x8000:
                names.add(n)
        return (self.pt.x - vx) / (vw - 1), (self.pt.y - vy) / (vh - 1), frozenset(names)

    def close(self):
        pass


class _Mac:
    def __init__(self):
        from .. import macos

        self.m = macos
        self.area = macos.desktop()
        self._n = 0

    def query(self):
        m = self.m
        self._n += 1
        if self._n % 500 == 0:  # telas podem mudar (monitor conectado/desligado)
            self.area = m.desktop()
        cx, cy = m.cursor()
        ax, ay, aw, ah = self.area
        names = set()
        for i, n in ((0, "MOUSE_LEFT"), (1, "MOUSE_RIGHT"), (2, "MOUSE_MIDDLE"), (3, "MOUSE_X1"), (4, "MOUSE_X2")):
            if m.button_down(i):
                names.add(n)
        return (cx - ax) / max(1.0, aw - 1), (cy - ay) / max(1.0, ah - 1), frozenset(names)

    def close(self):
        pass


class MouseSource:
    family = "mouse"
    kind = "mouse"
    name = "mouse do sistema"

    def __init__(self, rate_hz: float = 250.0):
        self.api = _Win() if sys.platform == "win32" else _Mac() if sys.platform == "darwin" else _X11()
        self.period = 1.0 / rate_hz
        self._closed = False

    @classmethod
    def open(cls):
        return cls()

    def events(self):
        last_buttons = None
        nxt = time.monotonic()
        prev = None
        while not self._closed:
            x, y, buttons = self.api.query()
            now = time.monotonic()
            dt = self.period if prev is None else now - prev
            prev = now
            if buttons != last_buttons:
                last_buttons = buttons
                yield ButtonState(buttons)
            yield PointerSample(x, y, dt)
            nxt += self.period
            d = nxt - time.monotonic()
            if d > 0:
                time.sleep(d)
            else:
                nxt = time.monotonic()

    def close(self) -> None:
        self._closed = True
        try:
            self.api.close()
        except Exception:
            pass
