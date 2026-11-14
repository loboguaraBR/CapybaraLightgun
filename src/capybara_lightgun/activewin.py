"""Texto que identifica a janela ativa (classe + título + programa).

Usado para trocar de perfil automaticamente conforme o jogo aberto.
Linux/X11: libX11 (ctypes). Windows: GetForegroundWindow + nome do executável.
macOS: lsappinfo (nome do aplicativo em primeiro plano, sem permissões extras).
"""
from __future__ import annotations

import os
import subprocess
import sys


def active_window_text() -> str:
    try:
        if sys.platform == "win32":
            return _windows()
        if sys.platform == "darwin":
            return _mac()
        if os.environ.get("DISPLAY"):
            return _x11()
    except Exception:
        pass
    return ""


def _x11() -> str:
    # Direto pela libX11: rodar `xprop` aqui (thread do painel) travava a mira.
    from . import x11

    return x11.window_text(x11.active_window())


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


def _mac() -> str:
    asn = subprocess.run(["lsappinfo", "front"], capture_output=True, text=True, timeout=1).stdout.strip()
    if not asn:
        return ""
    info = subprocess.run(["lsappinfo", "info", "-only", "name", "-only", "bundleid", asn],
                          capture_output=True, text=True, timeout=1).stdout
    return info.replace("\n", " ")
