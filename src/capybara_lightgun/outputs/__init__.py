"""Saídas: mouse absoluto (a "light gun" vista pelo sistema/emulador)."""
from __future__ import annotations

import os
import sys
import time

FULL = [0.0, 0.0, 1.0, 1.0]
_mon_cache: tuple = (0.0, None)


def _read_x11_monitors() -> tuple:
    from .. import x11

    mons = x11.monitors()
    size = (max((m[0] + m[2] for m in mons), default=0), max((m[1] + m[3] for m in mons), default=0))
    return mons, size


def x11_monitors() -> tuple:
    """Linux/X11: ([(x, y, w, h, primário), ...], (largura, altura) da área de trabalho).

    Lê pelo XRandR na primeira vez; depois devolve o valor que a thread de
    fundo atualiza, sem nenhuma chamada ao X no caminho do cursor.
    """
    global _mon_cache
    if _mon_cache[1] is None:
        _mon_cache = (time.monotonic(), _read_x11_monitors())
    return _mon_cache[1]


_active_mon: dict = {"idx": None, "started": False}


def _active_window_monitor() -> int | None:
    """Índice do monitor com o centro da janela ativa (None = manter o atual).

    Janelas deste processo (painel, calibração, estande do Capybara Lightgun)
    não contam: a arma continua no monitor do jogo.
    """
    from .. import x11

    mons, _ = x11_monitors()
    if len(mons) < 2:
        return None
    wid = x11.active_window()
    if not wid or x11.window_pid(wid) == os.getpid():
        return None
    r = x11.window_rect(wid)
    if not r:
        return None
    cx, cy = r[0] + r[2] / 2, r[1] + r[3] / 2
    for i, (x, y, w, h, _) in enumerate(mons):
        if x <= cx < x + w and y <= cy < y + h:
            return i
    return None


def _watch_active_window() -> None:
    global _mon_cache
    n = 0
    while True:
        n += 1
        if n % 4 == 0:  # monitores: a cada 2 s (conectar/desligar a TV)
            try:
                _mon_cache = (time.monotonic(), _read_x11_monitors())
            except Exception:
                pass
        try:
            i = _active_window_monitor()
            if i is not None:
                _active_mon["idx"] = i
        except Exception:
            pass
        time.sleep(0.5)


def _start_watch() -> None:
    if _active_mon["started"] or not os.environ.get("DISPLAY"):
        return
    import threading

    _active_mon["started"] = True
    threading.Thread(target=_watch_active_window, daemon=True, name="monitor-ativo").start()


def screen_region(cfg: dict) -> list:
    """Fração da área de trabalho onde a mira trabalha, já resolvendo o monitor.

    Linux com vários monitores e a área padrão (tela toda): a arma usa o
    monitor inteiro onde está a janela ativa (o jogo, em tela cheia ou não),
    acompanhando quando ela muda de monitor. Antes ela se espalhava por todos
    os monitores: o movimento saía multiplicado e o cursor fugia para o outro
    monitor. `monitor` (0, 1…) fixa um monitor; uma área diferente da padrão é
    respeitada como está.
    """
    region = [float(v) for v in (cfg.get("region") or FULL)]
    if not sys.platform.startswith("linux") or cfg.get("output_target") == "lightgun":
        # Modo driver: quem lê o dispositivo (RetroArch com driver udev) mapeia a
        # faixa inteira dele para a própria tela do jogo, não para a área de
        # trabalho; recortar o monitor aqui comprimiria a mira.
        return region
    mon = cfg.get("monitor")
    if mon is None and region != FULL:
        return region
    mons, (W, H) = x11_monitors()
    if not mons or not W or not H or (mon is None and len(mons) == 1):
        return region
    if mon is None:
        _start_watch()
        mon = _active_mon["idx"]
    if mon is not None and 0 <= int(mon) < len(mons):
        x, y, w, h, _ = mons[int(mon)]
    else:
        x, y, w, h, _ = next((m for m in mons if m[4]), mons[0])
    return [x / W, y / H, (x + w) / W, (y + h) / H]


def cursor_from_gun(cursor: tuple, recent, now: float, size: tuple, tol_px: float = 25.0,
                    window_s: float = 0.25) -> bool:
    """O cursor está onde a arma o colocou?

    `cursor` e as posições de `recent` ((t, fx, fy), em fração da área de
    trabalho) são comparados em pixels. O X aplica o movimento da arma com
    alguns ms de atraso, então vale qualquer posição enviada nos últimos
    `window_s` segundos (mais a última, se a arma está parada). Comparar o
    deslocamento do cursor com o da arma confundia esse atraso com o touchpad
    e a arma cedia o cursor no meio da mira (travava e depois saltava).
    """
    pts = list(recent)
    if not pts:
        return True
    cand = [p for p in pts if now - p[0] <= window_s] or pts[-1:]
    w, h = size
    cx, cy = cursor
    return min(((cx - fx) * w) ** 2 + ((cy - fy) * h) ** 2 for _, fx, fy in cand) <= tol_px ** 2


def keys_in_config(cfg: dict) -> list:
    return sorted({a[4:].lower() for a in cfg.get("buttons", {}).values() if isinstance(a, str) and a.startswith("key:")})


def open_output(cfg: dict, backend: str | None = None):
    backend = backend or cfg.get("output_backend", "auto")
    if backend == "auto":
        backend = {"win32": "sendinput", "darwin": "quartz"}.get(sys.platform, "uinput")
    region = screen_region(cfg)
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

        import collections

        self.lock = threading.RLock()
        # Posições enviadas (t, fx, fy em fração da área de trabalho): o painel
        # usa para saber se quem mexeu o cursor foi a arma ou o touchpad.
        self.recent = collections.deque(maxlen=600)
        self.real = None
        self.sig = None
        self.error = ""
        self.backend = backend
        self.reconfigure(cfg)

    @property
    def name(self) -> str:
        return getattr(self.real, "name", "none")

    def reconfigure(self, cfg: dict) -> None:
        self.cfg = cfg
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
        with self.lock:
            real = self.real
            if real is None:
                return
            if sys.platform.startswith("linux") and hasattr(real, "region"):
                r = screen_region(self.cfg)  # o jogo pode ter mudado de monitor
                if r != real.region:
                    real.region = r
                    real._last = None
            real.move(x, y)
            r = getattr(real, "region", None) or FULL
            self.recent.append((time.monotonic(), r[0] + x * (r[2] - r[0]), r[1] + y * (r[3] - r[1])))

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
