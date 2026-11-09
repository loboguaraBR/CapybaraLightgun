"""Saídas: mouse absoluto (a "light gun" vista pelo sistema/emulador)."""
from __future__ import annotations

import sys


def keys_in_config(cfg: dict) -> list:
    return sorted({a[4:].lower() for a in cfg.get("buttons", {}).values() if isinstance(a, str) and a.startswith("key:")})


def open_output(cfg: dict, backend: str | None = None):
    backend = backend or cfg.get("output_backend", "auto")
    if backend == "auto":
        backend = {"win32": "sendinput", "darwin": "quartz"}.get(sys.platform, "uinput")
    region = cfg.get("region") or [0.0, 0.0, 1.0, 1.0]
    keys = keys_in_config(cfg)
    if backend == "uinput":
        from .linux_uinput import UInputOutput

        return UInputOutput(region, keys, target=cfg.get("output_target", "mouse"))
    if backend == "sendinput":
        from .windows_sendinput import SendInputOutput

        return SendInputOutput(region, keys, monitor=cfg.get("monitor"))
    if backend == "quartz":
        from .mac_quartz import QuartzOutput

        return QuartzOutput(region, keys, monitor=cfg.get("monitor"))
    if backend == "console":
        from .console import ConsoleOutput

        return ConsoleOutput()
    if backend == "none":
        return NullOutput()
    raise ValueError(f"backend de saída desconhecido: {backend}")


class NullOutput:
    name = "none (test)"

    def move(self, x, y): pass

    def move_rel(self, dx, dy): pass

    def button(self, name, down): pass

    def key(self, name, down): pass

    def close(self): pass


class OutputProxy:
    """Saída trocável em tempo real (o painel pode mudar região/backend)."""

    def __init__(self, cfg: dict, backend: str | None = None):
        import threading

        self.lock = threading.RLock()
        self.real = None
        self.sig = None
        self.error = ""
        self.backend = backend
        self.reconfigure(cfg)

    @property
    def name(self) -> str:
        return getattr(self.real, "name", "none")

    def reconfigure(self, cfg: dict) -> None:
        sig = (self.backend or cfg.get("output_backend"), tuple(cfg.get("region") or ()), cfg.get("monitor"),
               cfg.get("output_target"))
        if sig == self.sig and self.real is not None:
            return
        with self.lock:
            if self.real is not None:
                try:
                    self.real.close()
                except Exception:
                    pass
                self.real = None
            try:
                self.real = open_output(cfg, self.backend)
                self.error = ""
                if cfg.get("output_target") == "lightgun" and not sys.platform.startswith("linux"):
                    self.error = ("Light-gun-only (driver) mode exists only on Linux (Windows and macOS would "
                                  "need a system driver). Using the system mouse.")
            except Exception as exc:
                self.error = str(exc)
            self.sig = sig

    def _call(self, meth: str, *args) -> None:
        with self.lock:
            if self.real is not None:
                getattr(self.real, meth)(*args)

    def move(self, x, y):
        self._call("move", x, y)

    def move_rel(self, dx, dy):
        self._call("move_rel", dx, dy)

    def button(self, name, down):
        self._call("button", name, down)

    def key(self, name, down):
        self._call("key", name, down)

    def close(self):
        with self.lock:
            if self.real is not None:
                self.real.close()
                self.real = None
