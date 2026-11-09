"""Calibração guiada pelo terminal: centro + 4 cantos -> homografia.

Não precisa ver cursor nenhum: basta mirar nos cantos FÍSICOS da tela e
apertar o gatilho. O ponto registrado é a mediana dos ~200 ms ANTES do
aperto, para o tranco do dedo não estragar a medida.
"""
from __future__ import annotations

import math
import statistics
import time
from collections import deque
from datetime import datetime, timezone

from .engine import Tracker
from .geometry import Homography, heading, median_forward, project, rotate_yaw  # noqa: F401
from .inputs import ButtonState, ImuSample

TARGETS = [
    ("CENTRO da tela", (0.5, 0.5)),
    ("canto SUPERIOR ESQUERDO", (0.0, 0.0)),
    ("canto SUPERIOR DIREITO", (1.0, 0.0)),
    ("canto INFERIOR DIREITO", (1.0, 1.0)),
    ("canto INFERIOR ESQUERDO", (0.0, 1.0)),
]


def fit_calibration(src_pts, dst_pts):
    """Ajusta a homografia e devolve (H, erro_rms normalizado)."""
    H = Homography.fit(src_pts, dst_pts)
    errs = []
    for uv, (x, y) in zip(src_pts, dst_pts):
        p = H.apply(*uv)
        errs.append(math.hypot(p[0] - x, p[1] - y) if p else 1.0)
    return H, math.sqrt(sum(e * e for e in errs) / len(errs))


def _trigger_names(cfg: dict) -> set:
    names = {k for k, v in cfg["buttons"].items() if v == "trigger"}
    return names or {"ZR", "ZL"}


def run_calibration(cfg: dict, source, homography: Homography) -> dict:
    tracker = Tracker(cfg, homography)
    trig = _trigger_names(cfg)
    hist: deque = deque(maxlen=400)  # (t, forward_mundo)
    events = source.events()
    pressed = frozenset()

    def pump_until(cond, timeout=None):
        nonlocal pressed
        t0 = time.monotonic()
        for ev in events:
            now = time.monotonic()
            if isinstance(ev, ImuSample):
                tracker.update(ev)
                hist.append((now, tracker.ahrs.forward()))
            elif isinstance(ev, ButtonState):
                newly = ev.pressed - pressed
                pressed = ev.pressed
                if newly & trig:
                    return now
            if cond is not None and cond():
                return now
            if timeout is not None and now - t0 > timeout:
                return None
        return None

    print("\n1) Apoie o controle PARADO numa superfície (calibrando o giroscópio)...")
    if pump_until(lambda: tracker.bias.acquired, timeout=15.0) is None and not tracker.bias.acquired:
        print("   não detectei o controle parado; seguindo sem bias (pode derivar mais).")
    else:
        b = tracker.bias.bias
        print(f"   ok. bias do giroscópio = ({b[0]:+.2f}, {b[1]:+.2f}, {b[2]:+.2f}) °/s")

    print("\nAgora segure como uma arma, na posição em que vai jogar.")
    print(f"Para cada alvo: mire com calma e aperte o gatilho ({'/'.join(sorted(trig))}).\n")

    def capture(t_press: float):
        return median_forward(hist, t_press)

    src_pts, dst_pts = [], []
    i = 0
    while i < len(TARGETS):
        label, dst = TARGETS[i]
        print(f"{i + 2}) Mire no {label} e aperte o gatilho...")
        t = pump_until(None)
        if t is None:
            raise RuntimeError("fluxo de dados do controle terminou")
        f = capture(t)
        if i == 0:
            # O centro define o "zero" do yaw desta sessão.
            tracker.yaw_offset = heading(f)
        uv = project(rotate_yaw(f, -tracker.yaw_offset))
        if uv is None:
            print("   mira muito fora (apontando para o lado/trás). Tente de novo.")
            continue
        print(f"   registrado: ângulo horiz {math.degrees(math.atan(uv[0])):+.1f}°, vert {math.degrees(math.atan(uv[1])):+.1f}°")
        src_pts.append(uv)
        dst_pts.append(dst)
        i += 1

    H, rms = fit_calibration(src_pts, dst_pts)
    left = math.degrees(math.atan(src_pts[1][0]))
    right = math.degrees(math.atan(src_pts[2][0]))
    print(f"\nCampo de visão da tela: ~{abs(right - left):.1f}° na horizontal.")
    print(f"Erro residual da calibração: {rms * 100:.2f}% da tela", end="")
    print("  (ótimo)" if rms < 0.01 else "  (ok)" if rms < 0.03 else "  (alto — refaça mirando com mais calma)")
    return {
        "version": 1,
        "created": datetime.now(timezone.utc).isoformat(),
        "device": getattr(source, "name", ""),
        "homography": H.to_list(),
        "rms_error": rms,
        "points_uv": src_pts,
        "gyro_bias_dps": list(tracker.bias.bias),
    }


class Calibrator:
    """Calibração passo a passo (usada pelo painel e pelo simulador)."""

    def __init__(self, tracker: Tracker):
        self.tracker = tracker
        self.step = 0
        self.src: list = []
        self.dst: list = []
        self.result = None  # (Homography, rms)
        self.message = ""
        self._saved_offset = tracker.yaw_offset

    @property
    def done(self) -> bool:
        return self.result is not None

    def target(self):
        return TARGETS[self.step] if self.step < len(TARGETS) else None

    def add(self, forward) -> bool:
        """Registra o tiro no alvo atual. Retorna True quando terminou."""
        if self.done or forward is None:
            return self.done
        if self.step == 0:
            self.tracker.yaw_offset = heading(forward)
        uv = project(rotate_yaw(forward, -self.tracker.yaw_offset))
        if uv is None:
            self.message = "Aim too far off (pointing sideways). Try again."
            return False
        self.src.append(uv)
        self.dst.append(TARGETS[self.step][1])
        self.step += 1
        self.message = ""
        if self.step == len(TARGETS):
            try:
                H, rms = fit_calibration(self.src, self.dst)
            except ValueError:
                self.message = "Invalid points — starting over."
                self.step, self.src, self.dst = 0, [], []
                return False
            self.tracker.set_homography(H)
            self.result = (H, rms)
            return True
        return False

    def cancel(self) -> None:
        self.tracker.yaw_offset = self._saved_offset

    def to_dict(self, device: str = "") -> dict:
        H, rms = self.result
        return {
            "version": 1,
            "created": datetime.now(timezone.utc).isoformat(),
            "device": device,
            "homography": H.to_list(),
            "rms_error": rms,
            "points_uv": self.src,
            "gyro_bias_dps": list(self.tracker.bias.bias),
        }
