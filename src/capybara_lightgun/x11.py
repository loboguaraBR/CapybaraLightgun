"""Linux/X11 direto pela libX11/libXrandr (ctypes), sem abrir processos.

Rodar `xprop`/`xwininfo`/`xrandr` várias vezes por segundo travava a mira: cada
processo novo copia a memória do app (Qt incluso) segurando o GIL, e a thread
que move o cursor ficava parada por 25–250 ms. As chamadas ctypes liberam o
GIL e levam microssegundos.

Cada thread usa a sua própria conexão (Xlib não é compartilhável entre threads
sem XInitThreads).
"""
from __future__ import annotations

import ctypes
import ctypes.util
import os
import threading

_c_ulong_p = ctypes.POINTER(ctypes.c_ulong)


class _MonitorInfo(ctypes.Structure):
    _fields_ = [("name", ctypes.c_ulong), ("primary", ctypes.c_int), ("automatic", ctypes.c_int),
                ("noutput", ctypes.c_int), ("x", ctypes.c_int), ("y", ctypes.c_int),
                ("width", ctypes.c_int), ("height", ctypes.c_int), ("mwidth", ctypes.c_int),
                ("mheight", ctypes.c_int), ("outputs", _c_ulong_p)]


_libs: dict = {}
_ERR = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
_local = threading.local()


def _load():
    if "x" in _libs:
        return _libs["x"], _libs["xr"]
    x = xr = None
    name = ctypes.util.find_library("X11")
    if name:
        x = ctypes.cdll.LoadLibrary(name)
        x.XOpenDisplay.restype = ctypes.c_void_p
        x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x.XDefaultRootWindow.restype = ctypes.c_ulong
        x.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        x.XInternAtom.restype = ctypes.c_ulong
        x.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        x.XGetWindowProperty.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_long, ctypes.c_long, ctypes.c_int,
            ctypes.c_ulong, _c_ulong_p, ctypes.POINTER(ctypes.c_int), _c_ulong_p, _c_ulong_p,
            ctypes.POINTER(ctypes.c_void_p)]
        x.XFree.argtypes = [ctypes.c_void_p]
        x.XGetGeometry.argtypes = [ctypes.c_void_p, ctypes.c_ulong, _c_ulong_p] + \
            [ctypes.POINTER(ctypes.c_int)] * 2 + [ctypes.POINTER(ctypes.c_uint)] * 4
        x.XTranslateCoordinates.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int,
                                            ctypes.c_int, ctypes.POINTER(ctypes.c_int),
                                            ctypes.POINTER(ctypes.c_int), _c_ulong_p]
        x.XSetErrorHandler.restype = ctypes.c_void_p
        x.XSetErrorHandler.argtypes = [_ERR]
        # Janela que fechou no meio da consulta gera BadWindow; o tratador
        # padrão da Xlib encerraria o programa.
        _libs["err"] = _ERR(lambda d, e: 0)
        x.XSetErrorHandler(_libs["err"])
        name = ctypes.util.find_library("Xrandr")
        if name:
            xr = ctypes.cdll.LoadLibrary(name)
            xr.XRRGetMonitors.restype = ctypes.POINTER(_MonitorInfo)
            xr.XRRGetMonitors.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int,
                                          ctypes.POINTER(ctypes.c_int)]
            xr.XRRFreeMonitors.argtypes = [ctypes.POINTER(_MonitorInfo)]
    _libs["x"], _libs["xr"] = x, xr
    return x, xr


class _Conn:
    def __init__(self):
        self.x, self.xr = _load()
        self.dpy = self.x.XOpenDisplay(None) if self.x and os.environ.get("DISPLAY") else None
        if self.dpy:
            self.root = self.x.XDefaultRootWindow(self.dpy)
            self.atoms = {}

    def atom(self, name: str) -> int:
        a = self.atoms.get(name)
        if a is None:
            a = self.atoms[name] = self.x.XInternAtom(self.dpy, name.encode(), False)
        return a

    def prop(self, win: int, name: str, kind: str = "card"):
        """Lista de inteiros (format 32) ou bytes (format 8) da propriedade."""
        typ, fmt, n, after = ctypes.c_ulong(), ctypes.c_int(), ctypes.c_ulong(), ctypes.c_ulong()
        data = ctypes.c_void_p()
        st = self.x.XGetWindowProperty(self.dpy, win, self.atom(name), 0, 4096, False, 0,  # AnyPropertyType
                                       ctypes.byref(typ), ctypes.byref(fmt), ctypes.byref(n),
                                       ctypes.byref(after), ctypes.byref(data))
        if st != 0 or not data.value:
            return None
        try:
            if fmt.value == 32:  # vem como C long
                return list(ctypes.cast(data, ctypes.POINTER(ctypes.c_long))[:n.value])
            if fmt.value == 8:
                return ctypes.string_at(data, n.value)
            return None
        finally:
            self.x.XFree(data)


def _conn() -> _Conn | None:
    c = getattr(_local, "conn", None)
    if c is None:
        try:
            c = _Conn()
        except Exception:
            c = None
        _local.conn = c
    return c if c is not None and c.dpy else None


def available() -> bool:
    return _conn() is not None


def monitors() -> list:
    """[(x, y, largura, altura, primário), ...] na ordem do XRandR."""
    c = _conn()
    if c is None or c.xr is None:
        return []
    n = ctypes.c_int()
    m = c.xr.XRRGetMonitors(c.dpy, c.root, True, ctypes.byref(n))
    if not m:
        return []
    try:
        return [(m[i].x, m[i].y, m[i].width, m[i].height, bool(m[i].primary)) for i in range(n.value)]
    finally:
        c.xr.XRRFreeMonitors(m)


def active_window() -> int:
    c = _conn()
    if c is None:
        return 0
    v = c.prop(c.root, "_NET_ACTIVE_WINDOW")
    return int(v[0]) & 0xFFFFFFFF if v else 0


def window_pid(win: int) -> int:
    c = _conn()
    v = c.prop(win, "_NET_WM_PID") if c and win else None
    return int(v[0]) if v else 0


def window_text(win: int) -> str:
    """Classe + título da janela (o mesmo que o `xprop WM_CLASS _NET_WM_NAME` dava)."""
    c = _conn()
    if c is None or not win:
        return ""
    parts = []
    for name in ("WM_CLASS", "_NET_WM_NAME", "WM_NAME"):
        v = c.prop(win, name)
        if isinstance(v, bytes) and v:
            parts.append(v.replace(b"\0", b" ").decode("utf-8", "replace").strip())
    return " ".join(parts)


def window_rect(win: int):
    """(x, y, largura, altura) absolutos na área de trabalho, ou None."""
    c = _conn()
    if c is None or not win:
        return None
    root = ctypes.c_ulong()
    x, y = ctypes.c_int(), ctypes.c_int()
    w, h, b, d = ctypes.c_uint(), ctypes.c_uint(), ctypes.c_uint(), ctypes.c_uint()
    if not c.x.XGetGeometry(c.dpy, win, ctypes.byref(root), ctypes.byref(x), ctypes.byref(y),
                            ctypes.byref(w), ctypes.byref(h), ctypes.byref(b), ctypes.byref(d)):
        return None
    ax, ay, child = ctypes.c_int(), ctypes.c_int(), ctypes.c_ulong()
    if not c.x.XTranslateCoordinates(c.dpy, win, c.root, 0, 0, ctypes.byref(ax), ctypes.byref(ay),
                                     ctypes.byref(child)):
        return None
    return (ax.value, ay.value, w.value, h.value)
