"""Windows: move o mouse em coordenadas ABSOLUTAS via SendInput."""
from __future__ import annotations

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

INPUT_MOUSE, INPUT_KEYBOARD = 0, 1
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP = 0x0008, 0x0010
MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP = 0x0020, 0x0040
MOUSEEVENTF_VIRTUALDESK = 0x4000
MOUSEEVENTF_ABSOLUTE = 0x8000
KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP, KEYEVENTF_SCANCODE = 0x0001, 0x0002, 0x0008

ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]


class _UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _UNION)]


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = wintypes.UINT

_VK = {
    "enter": 0x0D, "return": 0x0D, "esc": 0x1B, "escape": 0x1B, "space": 0x20, "tab": 0x09,
    "backspace": 0x08, "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "shift": 0xA0, "ctrl": 0xA2, "control": 0xA2, "alt": 0xA4, "pause": 0x13,
    "insert": 0x2D, "delete": 0x2E, "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
}
_EXTENDED = {0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0x24, 0x23, 0x21, 0x22}
for _i in range(1, 13):
    _VK[f"f{_i}"] = 0x6F + _i

_MOUSE_FLAGS = {
    "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
}


def vk_code(name: str) -> int:
    n = name.lower()
    if n in _VK:
        return _VK[n]
    if len(n) == 1 and (n.isalpha() or n.isdigit()):
        return ord(n.upper())
    raise ValueError(f"tecla desconhecida: {name}")


def _set_dpi_aware() -> None:
    try:
        ctypes.WinDLL("shcore").SetProcessDpiAwareness(2)  # per-monitor
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass


def virtual_desktop() -> tuple:
    return (user32.GetSystemMetrics(76), user32.GetSystemMetrics(77),
            user32.GetSystemMetrics(78), user32.GetSystemMetrics(79))


def monitors() -> list:
    rects = []
    proto = ctypes.WINFUNCTYPE(ctypes.c_int, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)

    def cb(hmon, hdc, rect, data):
        r = rect.contents
        rects.append((r.left, r.top, r.right, r.bottom))
        return 1

    user32.EnumDisplayMonitors(None, None, proto(cb), 0)
    return rects


class SendInputOutput:
    name = "system mouse (SendInput)"

    def __init__(self, region, keys, monitor=None):
        _set_dpi_aware()
        vx, vy, vw, vh = virtual_desktop()
        self._virt = (vx, vy, max(vw, 1), max(vh, 1))
        self.region = [float(v) for v in region]
        if monitor is not None:
            mons = monitors()
            if not 0 <= int(monitor) < len(mons):
                raise ValueError(f"monitor {monitor} não existe (há {len(mons)})")
            l, t, r, b = mons[int(monitor)]
            self.region = [(l - vx) / vw, (t - vy) / vh, (r - vx) / vw, (b - vy) / vh]
        self.keys: dict = {}
        self._last = None

    def _send(self, *inputs: INPUT) -> None:
        arr = (INPUT * len(inputs))(*inputs)
        user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))

    def move(self, x: float, y: float) -> None:
        r = self.region
        nx = r[0] + x * (r[2] - r[0])
        ny = r[1] + y * (r[3] - r[1])
        ax = int(round(min(max(nx, 0.0), 1.0) * 65535))
        ay = int(round(min(max(ny, 0.0), 1.0) * 65535))
        if (ax, ay) == self._last:
            return
        self._last = (ax, ay)
        inp = INPUT(type=INPUT_MOUSE)
        inp.mi = MOUSEINPUT(ax, ay, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK, 0, 0)
        self._send(inp)

    def move_rel(self, dx: int, dy: int) -> None:
        inp = INPUT(type=INPUT_MOUSE)
        inp.mi = MOUSEINPUT(int(dx), int(dy), 0, MOUSEEVENTF_MOVE, 0, 0)
        self._send(inp)
        self._last = None

    def button(self, name: str, down: bool) -> None:
        flag = _MOUSE_FLAGS[name][0 if down else 1]
        inp = INPUT(type=INPUT_MOUSE)
        inp.mi = MOUSEINPUT(0, 0, 0, flag, 0, 0)
        self._send(inp)

    def key(self, name: str, down: bool) -> None:
        vk = self.keys.get(name)
        if vk is None:
            try:
                vk = self.keys[name] = vk_code(name)
            except ValueError:
                return
        scan = user32.MapVirtualKeyW(vk, 0)
        flags = KEYEVENTF_SCANCODE | (0 if down else KEYEVENTF_KEYUP)
        if vk in _EXTENDED:
            flags |= KEYEVENTF_EXTENDEDKEY
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
        self._send(inp)

    def close(self) -> None:
        pass
