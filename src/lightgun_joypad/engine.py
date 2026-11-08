"""Motor: IMU -> orientação -> ponto na tela -> mouse + botões.

Todos os ajustes podem ser trocados com o programa rodando (apply_config),
o que permite ao painel aplicar mudanças ao vivo.
"""
from __future__ import annotations

import bisect
import math
import sys
import threading
import time
from collections import deque

from .filters import OneEuro2D
from .fusion import BiasEstimator, Mahony
from .geometry import Homography, heading, median_forward, project, rotate_yaw
from .inputs import ButtonState, ImuSample, PointerSample

DEG = math.pi / 180.0
REL_COUNTS = (1920.0, 1080.0)  # "pixels" por tela inteira no modo relativo


def homography_from(cfg: dict, calib: dict | None) -> Homography:
    if calib and calib.get("homography"):
        return Homography(calib["homography"])
    s = cfg["screen"]
    return Homography.from_screen(s["width_m"], s["height_m"], s["distance_m"])


class Tracker:
    """Mantém a orientação do controle e converte em ponto da tela."""

    def __init__(self, cfg: dict, homography: Homography):
        self.ahrs = Mahony()
        self.bias = BiasEstimator()
        self.apply_config(cfg)
        self.set_homography(homography)
        self.yaw_offset = 0.0
        self.initialized = False

    def apply_config(self, cfg: dict) -> None:
        f = cfg["fusion"]
        b = cfg["auto_bias"]
        self.ahrs.kp = float(f["kp"])
        self.ahrs.accel_tolerance_g = max(0.01, float(f["accel_tolerance_g"]))
        self.bias.enabled = bool(b["enabled"])
        self.bias.window_s = float(b["window_s"])
        self.bias.still_range_dps = float(b["still_range_dps"])
        self.bias.accel_range_g = float(b["accel_range_g"])

    def set_homography(self, h: Homography) -> None:
        self.H = h
        self.center_heading = h.center_heading()

    def update(self, s: ImuSample) -> None:
        self.bias.update(s.gyro_dps, s.accel_g, s.dt)
        if not self.initialized:
            self.ahrs.reset_from_accel(s.accel_g)
            self.initialized = True
            return
        b = self.bias.bias
        g = ((s.gyro_dps[0] - b[0]) * DEG, (s.gyro_dps[1] - b[1]) * DEG, (s.gyro_dps[2] - b[2]) * DEG)
        self.ahrs.update(g, s.accel_g, s.dt)

    def forward(self):
        """Direção do cano no referencial da tela (yaw recentrado)."""
        return rotate_yaw(self.ahrs.forward(), -self.yaw_offset)

    def aim_uv(self):
        return project(self.forward())

    def aim_xy(self):
        uv = self.aim_uv()
        return None if uv is None else self.H.apply(*uv)

    def recenter(self) -> None:
        """Chamado com a arma apontada para o CENTRO da tela."""
        self.yaw_offset = heading(self.ahrs.forward()) - self.center_heading


class LightGun:
    def __init__(self, cfg: dict, tracker: Tracker, output, verbose: bool = False):
        self.tracker = tracker
        self.out = output
        self.verbose = verbose
        self.smooth: OneEuro2D | None = None
        self.history: deque = deque(maxlen=128)  # (t, x, y) filtrado
        self.fhist: deque = deque(maxlen=400)  # (t, direção do cano) p/ calibração
        self.pos = (0.5, 0.5)
        self.raw = None
        self.onscreen = False
        self.paused = False
        self.freeze_until = 0.0
        # Modo mouse: até quando a arma "cede" o cursor ao touchpad/mouse real.
        self.yield_until = 0.0
        self.offscreen_held = 0
        self.pressed: frozenset = frozenset()
        self._held_actions: dict = {}
        self.samples = 0
        # Contador de tiros + posição do último tiro (estande de teste lê daqui,
        # funciona tanto no modo driver quanto no modo mouse).
        self.shots = 0
        self.last_shot = (0.5, 0.5)
        # Tempo do sensor (soma dos dt do IMU): mais preciso que o relógio,
        # já que no Bluetooth as 3 amostras de cada pacote chegam juntas.
        self.sensor_t = 0.0
        self._wall_at_sample = None
        self._last_out = None
        self._rel_prev = None
        self._rel_acc = [0.0, 0.0]
        # Relógio: diferença entre o relógio de parede e o tempo do sensor
        # (mínimo observado = chegada mais rápida, sem o atraso das rajadas).
        self._clock_off = None
        self._last_arrival = None
        self._clock_win: deque = deque()  # mínimo deslizante (chegada, offset)
        self._loop_started = False
        self._af_held = 0
        self._af_down = False
        self._af_next = 0.0
        # Quando definido, o gatilho NÃO clica: entrega a direção do cano
        # para a calibração.
        self.capture_hook = None
        # Coice: função do controle que vibra (definida em run()).
        self.feedback = None
        # Mira fora da tela (para recarregar apontando para fora).
        self.outside = False
        self._shake_cool = 0.0
        self._pulse_release = None  # tiro curto agendado (recarregar por tranco)
        self.pointer_mode = False  # fonte "mouse comum"
        self.overlay_on = bool(cfg.get("overlay", {}).get("enabled", False))
        self.apply_config(cfg)

    def apply_config(self, cfg: dict) -> None:
        self.cfg = cfg
        sm = cfg["smoothing"]
        if sm.get("enabled", True):
            if self.smooth is None:
                self.smooth = OneEuro2D(sm["min_cutoff"], sm["beta"], sm["d_cutoff"])
            else:
                self.smooth.min_cutoff = float(sm["min_cutoff"])
                self.smooth.beta = float(sm["beta"])
                self.smooth.d_cutoff = float(sm["d_cutoff"])
        else:
            self.smooth = None
        aim = cfg.get("aim", {})
        self.sens = (float(aim.get("sensitivity_x", 1.0)), float(aim.get("sensitivity_y", 1.0)))
        self.offset = (float(aim.get("offset_x", 0.0)), float(aim.get("offset_y", 0.0)))
        self.jitter_lock = float(aim.get("jitter_lock", 0.0))
        self.lookback = cfg["shot"]["lookback_ms"] / 1000.0
        self.freeze = cfg["shot"]["freeze_ms"] / 1000.0
        self.af_period = 0.5 / max(1.0, float(cfg.get("autofire_hz", 10)))
        mo = cfg.get("motion", {})
        self.render_delay = max(0.0, float(mo.get("interp_ms", 16)) / 1000.0)
        self.output_period = 1.0 / max(30.0, float(mo.get("output_hz", 250)))
        self.max_extrap = max(0.0, float(mo.get("max_extrap_ms", 40)) / 1000.0)
        mode = cfg.get("mode", "absolute")
        if mode != getattr(self, "mode", None):
            self._rel_prev = None
        self.mode = mode
        self.rel_speed = float(cfg.get("relative_speed", 1.0))
        rl = cfg.get("reload", {})
        self.reload_offscreen = bool(rl.get("offscreen_aim", True))
        self.offscreen_margin = float(rl.get("offscreen_margin", 0.02))
        self.reload_shake = bool(rl.get("shake", False))
        self.shake_g = float(rl.get("shake_g", 2.5))
        ru = cfg.get("rumble", {})
        self.rumble_on = bool(ru.get("enabled", True))
        self.rumble_ms = int(ru.get("ms", 45))
        self.rumble_strength = float(ru.get("strength", 0.7))
        self.buttons_map = {
            (k if k.startswith(("BTN_", "KEY_")) else k.upper()): v for k, v in cfg["buttons"].items() if v
        }
        self.tracker.apply_config(cfg)

    def press_sensor_t(self, now: float | None = None) -> float:
        """Instante "agora" na escala de tempo do sensor."""
        if self._wall_at_sample is None:
            return self.sensor_t
        if now is None:
            now = time.monotonic()
        return self.sensor_t + (now - self._wall_at_sample)

    # ---- IMU ---------------------------------------------------------------
    def _update_clock(self, now: float) -> None:
        """Offset relógio-de-parede − tempo-do-sensor = mínimo do último 1 s.

        A leitura que chega mais rápido (sem esperar a rajada) dá o atraso
        real do Bluetooth; a janela deslizante se reajusta sozinha depois de
        travadas, reconexões ou deriva entre os relógios.
        """
        cand = now - self.sensor_t
        if self._last_arrival is not None and now - self._last_arrival > 0.5:
            self._clock_win.clear()  # voltou de uma desconexão
        w = self._clock_win
        while w and w[-1][1] >= cand:
            w.pop()
        w.append((now, cand))
        while w[0][0] < now - 1.0:
            w.popleft()
        self._clock_off = w[0][1]
        self._last_arrival = now

    def render_pos(self, now: float | None = None):
        """Posição suave para mostrar no instante `now` (relógio de parede).

        Interpola entre as leituras pelo tempo do sensor, `render_delay` atrás
        do presente; se o Bluetooth atrasou, prevê pela velocidade recente.
        """
        h = list(self.history)
        if not h or self._clock_off is None or self.render_delay <= 0 or self.pointer_mode:
            return self.pos
        if now is None:
            now = time.monotonic()
        s = now - self._clock_off - self.render_delay
        if s >= h[-1][0]:
            t1, x1, y1 = h[-1]
            gap = min(s - t1, self.max_extrap)
            if gap <= 0 or len(h) < 2:
                return (x1, y1)
            i = len(h) - 2
            while i > 0 and t1 - h[i][0] < 0.025:
                i -= 1
            t0, x0, y0 = h[i]
            if t1 - t0 <= 1e-6:
                return (x1, y1)
            vx, vy = (x1 - x0) / (t1 - t0), (y1 - y0) / (t1 - t0)
            return (min(max(x1 + vx * gap, 0.0), 1.0), min(max(y1 + vy * gap, 0.0), 1.0))
        if s <= h[0][0]:
            return (h[0][1], h[0][2])
        j = bisect.bisect_right([e[0] for e in h], s) - 1
        ta, xa, ya = h[j]
        tb, xb, yb = h[j + 1]
        f = (s - ta) / (tb - ta) if tb > ta else 1.0
        return (xa + (xb - xa) * f, ya + (yb - ya) * f)

    def can_move(self, now: float) -> bool:
        return (not self.paused and not self.offscreen_held and now >= self.freeze_until
                and now >= self.yield_until)

    def start_output_loop(self) -> None:
        """Atualiza o cursor num ritmo fixo (movimento uniforme)."""
        if self._loop_started:
            return
        self._loop_started = True
        threading.Thread(target=self._output_loop, daemon=True, name="cursor").start()

    def _output_loop(self) -> None:
        if sys.platform == "win32":
            try:
                import ctypes

                ctypes.windll.winmm.timeBeginPeriod(1)  # sleep com precisão de 1 ms
            except Exception:
                pass
        clock = time.monotonic
        nxt = clock()
        while True:
            nxt += self.output_period
            now = clock()
            try:
                if (self.render_delay > 0 and self.mode == "absolute" and self.history
                        and not self.pointer_mode and self.can_move(now)):
                    x, y = self.render_pos(now)
                    if self._last_out != (x, y):
                        self.out.move(x, y)
                        self._last_out = (x, y)
            except Exception as exc:  # nunca derruba a mira
                print(f"erro no laço do cursor: {exc}", flush=True)
            delay = nxt - clock()
            if delay > 0:
                time.sleep(delay)
            else:
                nxt = clock()

    def on_imu(self, s: ImuSample, now: float) -> None:
        self.tracker.update(s)
        self.sensor_t += s.dt
        self._update_clock(now)
        self._wall_at_sample = now
        self.samples += 1
        st = self.sensor_t
        self.fhist.append((st, self.tracker.ahrs.forward()))
        xy = self.tracker.aim_xy()
        self.raw = xy
        self._autofire_tick(st)
        self._shake_check(s, st)
        if xy is None:  # cano apontando para longe da tela
            self.onscreen = False
            self.outside = True
            self._rel_prev = None
            return
        self._on_aim(xy, st, now)

    def on_pointer(self, p: PointerSample, now: float) -> None:
        """Fonte "mouse comum": a posição já vem em coordenadas de tela."""
        self.pointer_mode = True
        self.sensor_t += p.dt
        self._update_clock(now)
        self._wall_at_sample = now
        self.samples += 1
        st = self.sensor_t
        r = self.cfg.get("region") or [0.0, 0.0, 1.0, 1.0]
        w, h = (r[2] - r[0]) or 1.0, (r[3] - r[1]) or 1.0
        x, y = (p.x - r[0]) / w, (p.y - r[1]) / h
        self.raw = (x, y)
        self._autofire_tick(st)
        self.outside = not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0)
        x, y = min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0)
        self.onscreen = not self.outside
        self.pos = (x, y)
        self.history.append((st, x, y))
        if self.can_move(now):
            self.out.move(x, y)
            self._last_out = (x, y)

    def _shake_check(self, s: ImuSample, st: float) -> None:
        if self._pulse_release is not None and st >= self._pulse_release:
            self._pulse_release = None
            self.out.button("left", False)
            self.offscreen_held = max(0, self.offscreen_held - 1)
        if not self.reload_shake or self.paused or st < self._shake_cool:
            return
        a = s.accel_g
        if math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]) > self.shake_g:
            self._shake_cool = st + 0.5
            self.offscreen_held += 1
            self._offscreen_press()
            self._pulse_release = st + 0.06

    def _kick(self) -> None:
        if self.rumble_on and self.feedback is not None:
            try:
                self.feedback(self.rumble_ms, self.rumble_strength)
            except Exception:
                pass

    def _offscreen_press(self) -> None:
        ox, oy = self.cfg.get("offscreen_position", [0.0, 0.0])
        if self.mode == "absolute":
            self.out.move(ox, oy)
        self.out.button("left", True)
        self._kick()

    def _on_aim(self, xy, st: float, now: float) -> None:
        x = 0.5 + (xy[0] - 0.5) * self.sens[0] + self.offset[0]
        y = 0.5 + (xy[1] - 0.5) * self.sens[1] + self.offset[1]
        sm = self.smooth
        if sm is not None:
            x, y = sm(x, y, st)
        m = self.offscreen_margin
        self.outside = not (-m <= x <= 1 + m and -m <= y <= 1 + m)
        can_move = self.can_move(now)
        if self.mode == "relative":
            self._relative(x, y, can_move)
            return
        if self.jitter_lock > 0 and self._last_out is not None:
            if math.hypot(x - self._last_out[0], y - self._last_out[1]) < self.jitter_lock:
                x, y = self._last_out
        self.onscreen = 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0
        x = min(max(x, 0.0), 1.0)
        y = min(max(y, 0.0), 1.0)
        self.pos = (x, y)
        self.history.append((st, x, y))
        if can_move and self.render_delay <= 0:  # sem suavização: move a cada leitura
            self.out.move(x, y)
            self._last_out = (x, y)

    def _relative(self, x: float, y: float, can_move: bool) -> None:
        """Modo mouse comum: envia só o deslocamento (jogos que não aceitam absoluto)."""
        self.onscreen = True
        if self._rel_prev is None:
            self._rel_prev = (x, y)
            return
        dx = (x - self._rel_prev[0]) * REL_COUNTS[0] * self.rel_speed + self._rel_acc[0]
        dy = (y - self._rel_prev[1]) * REL_COUNTS[1] * self.rel_speed + self._rel_acc[1]
        self._rel_prev = (x, y)
        ix, iy = int(dx), int(dy)
        self._rel_acc = [dx - ix, dy - iy]
        self.pos = (min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0))
        if can_move and (ix or iy):
            self.out.move_rel(ix, iy)

    def _autofire_tick(self, st: float) -> None:
        if self._af_held and not self.paused and st >= self._af_next:
            self._af_down = not self._af_down
            if self._af_down:
                self.last_shot = self.pos
                self.shots += 1
                self._kick()
            self.out.button("left", self._af_down)
            self._af_next = st + self.af_period

    def _pos_at(self, t: float):
        for ht, x, y in reversed(self.history):
            if ht <= t:
                return (x, y)
        return self.pos

    # ---- botões ------------------------------------------------------------
    def on_buttons(self, b: ButtonState, now: float) -> None:
        new = b.pressed
        for name in new - self.pressed:
            act = self.buttons_map.get(name)
            if act:
                self._press(name, act, now)
        for name in self.pressed - new:
            act = self._held_actions.pop(name, None)
            if act:
                self._release(act)
        self.pressed = new

    def recenter(self) -> None:
        self.tracker.recenter()
        if self.smooth is not None:
            self.smooth.reset()
        self.history.clear()
        self._rel_prev = None
        self._last_out = None

    def _press(self, name: str, act: str, now: float) -> None:
        if self.verbose:
            print(f"[{name}] -> {act}")
        if self.capture_hook is not None and act in ("trigger", "autofire"):
            self.capture_hook(median_forward(self.fhist, self.press_sensor_t(now)))
            return
        if act == "recenter":
            self.recenter()
            return
        if act == "toggle":
            self.paused = not self.paused
            print("mira PAUSADA" if self.paused else "mira ATIVA")
            return
        if act == "toggle_crosshair":
            self.overlay_on = not self.overlay_on
            return
        if act == "trigger" and self.reload_offscreen and self.outside and not self.paused:
            act = "offscreen_shot"  # mirou fora da tela: recarrega, como numa arma real
        if self.paused and act in ("trigger", "offscreen_shot", "autofire"):
            return
        if act in ("trigger", "offscreen_shot", "autofire"):
            self.yield_until = 0.0  # atirou: a arma retoma o cursor
        self._held_actions[name] = act
        if act == "trigger":
            x, y = self.pos
            if self.mode == "absolute":
                x, y = self._pos_at(self.press_sensor_t(now) - self.lookback)
                self.out.move(x, y)
            self.last_shot = (x, y)
            self.shots += 1
            self.out.button("left", True)
            self._kick()
            self.freeze_until = now + self.freeze
        elif act == "autofire":
            self._af_held += 1
            if self._af_held == 1:
                self.last_shot = self.pos
                self.shots += 1
                self._kick()
                self._af_down = True
                self.out.button("left", True)
                self._af_next = self.press_sensor_t(now) + self.af_period
        elif act == "offscreen_shot":
            self.offscreen_held += 1
            self._offscreen_press()
        elif act.startswith("mouse_"):
            self.out.button(act[6:], True)
        elif act.startswith("key:"):
            self.out.key(act[4:].lower(), True)

    def _release(self, act: str) -> None:
        if act == "trigger":
            self.out.button("left", False)
        elif act == "autofire":
            self._af_held = max(0, self._af_held - 1)
            if not self._af_held and self._af_down:
                self._af_down = False
                self.out.button("left", False)
        elif act == "offscreen_shot":
            self.out.button("left", False)
            self.offscreen_held = max(0, self.offscreen_held - 1)
            if not self.paused and self.mode == "absolute":
                self.out.move(*self.pos)
        elif act.startswith("mouse_"):
            self.out.button(act[6:], False)
        elif act.startswith("key:"):
            self.out.key(act[4:].lower(), False)

    def release_all(self) -> None:
        for act in list(self._held_actions.values()):
            try:
                self._release(act)
            except Exception:
                pass
        self._held_actions.clear()
        # Relógio: diferença entre o relógio de parede e o tempo do sensor
        # (mínimo observado = chegada mais rápida, sem o atraso das rajadas).
        self._clock_off = None
        self._last_arrival = None
        self._clock_win: deque = deque()  # mínimo deslizante (chegada, offset)
        self._loop_started = False
        self._af_held = 0
        self.pressed = frozenset()

    # ---- laço --------------------------------------------------------------
    def run(self, source) -> None:
        self.feedback = getattr(source, "rumble", None)
        self.pointer_mode = False
        self.start_output_loop()
        clock = time.monotonic
        warned_bias = False
        start = clock()
        for ev in source.events():
            now = clock()
            if isinstance(ev, ImuSample):
                self.on_imu(ev, now)
                if not warned_bias and not self.tracker.bias.acquired and now - start > 8.0:
                    warned_bias = True
                    print("dica: apoie o controle parado por ~1 s para calibrar o giroscópio (evita deriva).")
            elif isinstance(ev, PointerSample):
                self.on_pointer(ev, now)
            elif isinstance(ev, ButtonState):
                self.on_buttons(ev, now)
