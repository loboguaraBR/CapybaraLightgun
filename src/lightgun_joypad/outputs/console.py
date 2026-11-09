"""Saída de teste: desenha a mira no terminal (não mexe no mouse).

Serve para treinar/validar a mira sem olhar para o cursor: aponte para um
canto da TV e confira se a cruz no terminal foi para o canto certo.
"""
from __future__ import annotations

import sys
import time

COLS, ROWS = 48, 15


class ConsoleOutput:
    name = "console (simulation, mouse untouched)"

    def __init__(self):
        self.x = self.y = 0.5
        self.buttons: set = set()
        self.keys: set = set()
        self._drawn = False
        self._last_draw = 0.0
        self.status = ""

    def move(self, x: float, y: float) -> None:
        self.x, self.y = x, y
        self._draw()

    def move_rel(self, dx: int, dy: int) -> None:
        self.x = min(max(self.x + dx / 1920, 0.0), 1.0)
        self.y = min(max(self.y + dy / 1080, 0.0), 1.0)
        self._draw()

    def button(self, name: str, down: bool) -> None:
        (self.buttons.add if down else self.buttons.discard)(name)
        self._draw(force=True)

    def key(self, name: str, down: bool) -> None:
        (self.keys.add if down else self.keys.discard)(name)
        self._draw(force=True)

    def _draw(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last_draw < 1 / 30:
            return
        self._last_draw = now
        cx = min(max(int(self.x * (COLS - 1) + 0.5), 0), COLS - 1)
        cy = min(max(int(self.y * (ROWS - 1) + 0.5), 0), ROWS - 1)
        mark = "X" if "left" in self.buttons else "+"
        lines = ["+" + "-" * COLS + "+"]
        for r in range(ROWS):
            row = [" "] * COLS
            if r == ROWS // 2:
                row[COLS // 2] = "."
            if r == cy:
                row[cx] = mark
            lines.append("|" + "".join(row) + "|")
        lines.append("+" + "-" * COLS + "+")
        info = f" x={self.x:6.3f} y={self.y:6.3f}  mouse={','.join(sorted(self.buttons)) or '-'}"
        info += f"  teclas={','.join(sorted(self.keys)) or '-'}  {self.status}"
        lines.append(info.ljust(COLS + 2)[: max(COLS + 2, len(info))])
        out = sys.stdout
        if self._drawn:
            out.write(f"\x1b[{len(lines)}F")
        out.write("\n".join("\x1b[2K" + ln for ln in lines) + "\n")
        out.flush()
        self._drawn = True

    def close(self) -> None:
        pass
