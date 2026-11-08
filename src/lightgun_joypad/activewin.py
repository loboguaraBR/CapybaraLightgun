"""Texto que identifica a janela ativa (classe + título + programa).

Usado para trocar de perfil automaticamente conforme o jogo aberto.
Linux/X11: xprop. Windows: GetForegroundWindow + nome do executável.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys


def active_window_text() -> str:
    try:
        if sys.platform == "win32":
            return _windows()
        if os.environ.get("DISPLAY") and shutil.which("xprop"):
            return _x11()
    except Exception:
        pass
    return ""


def _x11() -> str:
    out = subprocess.run(["xprop", "-root", "_NET_ACTIVE_WINDOW"], capture_output=True, text=True, timeout=1).stdout
    wid = out.strip().split()[-1] if out.strip() else ""
    if not wid.startswith("0x") or wid == "0x0":
        return ""
    info = subprocess.run(["xprop", "-id", wid, "WM_CLASS", "_NET_WM_NAME"],
                          capture_output=True, text=True, timeout=1).stdout
    return info.replace("\n", " ")


def _windows() -> str:
    import ctypes
    from ctypes import wintypes

    u, k = ctypes.WinDLL("user32"), ctypes.WinDLL("kernel32")
    hwnd = u.GetForegroundWindow()
    if not hwnd:
        return ""
    buf = ctypes.create_unicode_buffer(512)
    u.GetWindowTextW(hwnd, buf, 512)
    title = buf.value
    pid = wintypes.DWORD()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    exe = ""
    h = k.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
    if h:
        size = wintypes.DWORD(512)
        pbuf = ctypes.create_unicode_buffer(512)
        if k.QueryFullProcessImageNameW(h, 0, pbuf, ctypes.byref(size)):
            exe = os.path.basename(pbuf.value)
        k.CloseHandle(h)
    return f"{exe} {title}"
