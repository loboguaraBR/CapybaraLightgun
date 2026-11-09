"""macOS: mouse do sistema via Quartz (CGEventPost).

Precisa da permissão de Acessibilidade. Sem ela o macOS descarta os eventos
em silêncio; o aplicativo avisa e oferece o atalho para liberar.
"""
from __future__ import annotations

from .. import macos as M

_BTN = {  # nome -> (botão, desce, sobe, arrasta)
    "left": (0, M.LEFT_DOWN, M.LEFT_UP, M.LEFT_DRAG),
    "right": (1, M.RIGHT_DOWN, M.RIGHT_UP, M.RIGHT_DRAG),
    "middle": (2, M.OTHER_DOWN, M.OTHER_UP, M.OTHER_DRAG),
}


class QuartzOutput:
    name = "system mouse (Quartz)"

    def __init__(self, region, keys, monitor=None):
        self.region = [float(v) for v in region]
        self.monitor = monitor
        self.held: list = []
        self._last = None
        self._refresh()
        x, y = M.cursor()
        self._pos = (x, y)

    def _refresh(self) -> None:
        if self.monitor is not None:
            ds = M.displays()
            if not 0 <= int(self.monitor) < len(ds):
                raise ValueError(f"monitor {self.monitor} não existe (há {len(ds)})")
            self.area = ds[int(self.monitor)]
            self.reg = [0.0, 0.0, 1.0, 1.0]
        else:
            self.area = M.desktop()
            self.reg = self.region

    def _to_global(self, x: float, y: float) -> tuple:
        ax, ay, aw, ah = self.area
        r = self.reg
        gx = ax + (r[0] + x * (r[2] - r[0])) * (aw - 1)
        gy = ay + (r[1] + y * (r[3] - r[1])) * (ah - 1)
        return (gx, gy)

    def _move_event(self) -> tuple:
        if self.held:
            b = _BTN[self.held[-1]]
            return b[3], b[0]
        return M.MOVED, 0

    def move(self, x: float, y: float) -> None:
        gx, gy = self._to_global(x, y)
        key = (round(gx, 1), round(gy, 1))
        if key == self._last:
            return
        self._last = key
        dx, dy = int(gx - self._pos[0]), int(gy - self._pos[1])
        self._pos = (gx, gy)
        kind, btn = self._move_event()
        M.post_mouse(kind, gx, gy, btn, dx, dy)

    def move_rel(self, dx: int, dy: int) -> None:
        cx, cy = M.cursor()
        ax, ay, aw, ah = M.desktop()
        gx = min(max(cx + dx, ax), ax + aw - 1)
        gy = min(max(cy + dy, ay), ay + ah - 1)
        self._pos = (gx, gy)
        self._last = None
        kind, btn = self._move_event()
        M.post_mouse(kind, gx, gy, btn, dx, dy)

    def button(self, name: str, down: bool) -> None:
        btn, d, u, _ = _BTN[name]
        x, y = self._pos
        if down:
            self.held.append(name)
        elif name in self.held:
            self.held.remove(name)
        M.post_mouse(d if down else u, x, y, btn)

    def key(self, name: str, down: bool) -> None:
        code = M.KEYCODES.get(name.lower())
        if code is not None:
            M.post_key(code, down)

    def close(self) -> None:
        for name in list(self.held):
            self.button(name, False)
