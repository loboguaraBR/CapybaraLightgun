"""Simulador: estande de tiro em tela cheia para testar a light gun.

Usa exatamente o mesmo pipeline do modo real (Tracker + LightGun), mas em
vez de mexer no mouse do sistema, desenha a mira numa janela. Não precisa de
/dev/uinput.

Teclas:
  ESC  sair                 C  calibrar (centro + 4 cantos, na própria tela)
  H    esconder/mostrar mira (teste "às cegas")
  R    recentrar (mire no centro)   T  rastro da mira   N  zerar placar
  Sem controle conectado, o mouse faz o papel da arma (para testar a tela).
"""
from __future__ import annotations

import math
import random
import threading
import time
from collections import deque

from .calibration import fit_calibration, median_forward
from .config import load_calibration, save_calibration
from .engine import LightGun, Tracker, homography_from
from .geometry import heading, project, rotate_yaw
from .inputs import DeviceLost, NoDeviceFound, open_source

CAL_TARGETS = [
    ("CENTRO", (0.5, 0.5)),
    ("SUPERIOR ESQUERDO", (0.0, 0.0)),
    ("SUPERIOR DIREITO", (1.0, 0.0)),
    ("INFERIOR DIREITO", (1.0, 1.0)),
    ("INFERIOR ESQUERDO", (0.0, 1.0)),
]


class SimOutput:
    """Recebe o que iria para o mouse (chamado na thread do controle)."""

    def __init__(self):
        self.name = "simulador"
        self.pos = (0.5, 0.5)
        self.shots: deque = deque()
        self.keys: deque = deque()
        self.gun: "SimGun | None" = None

    def move(self, x, y):
        self.pos = (x, y)

    def move_rel(self, dx, dy):
        x, y = self.pos
        self.pos = (min(max(x + dx / 1920, 0.0), 1.0), min(max(y + dy / 1080, 0.0), 1.0))

    def button(self, name, down):
        if not down:
            return
        fwd = None
        if self.gun is not None and name == "left":
            fwd = median_forward(self.gun.fhist, self.gun.press_sensor_t())
        self.shots.append({"button": name, "pos": self.pos, "forward": fwd, "t": time.monotonic()})

    def key(self, name, down):
        if down:
            self.keys.append(name)

    def close(self):
        pass


class SimGun(LightGun):
    pass


class ControllerThread(threading.Thread):
    def __init__(self, cfg, calib):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.out = SimOutput()
        self.tracker = Tracker(cfg, homography_from(cfg, calib))
        if calib and calib.get("gyro_bias_dps"):
            self.tracker.bias.bias = list(calib["gyro_bias_dps"])
        self.gun = SimGun(cfg, self.tracker, self.out)
        self.out.gun = self.gun
        self.status = "procurando controle..."
        self.device = ""
        self.connected = False

    def run(self):
        while True:
            try:
                src = open_source(self.cfg)
            except NoDeviceFound as exc:
                self.connected = False
                self.status = "sem controle: " + str(exc).splitlines()[-1].strip()
                time.sleep(2)
                continue
            self.device = src.name
            self.connected = True
            self.status = "conectado"
            try:
                self.gun.run(src)
            except DeviceLost as exc:
                self.status = f"desconectado ({exc})"
            except Exception as exc:  # não derruba a janela
                self.status = f"erro: {exc}"
            finally:
                self.connected = False
                self.gun.release_all()
                src.close()
            time.sleep(1)


def run_simulator(cfg: dict, calib_path: str | None = None, windowed: str | None = None, display: int = 0) -> int:
    import pygame

    calib = load_calibration(calib_path)
    ctl = ControllerThread(cfg, calib)
    ctl.start()

    pygame.init()
    if windowed:
        w, h = (int(v) for v in windowed.lower().split("x"))
        screen = pygame.display.set_mode((w, h), display=display)
    else:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, display=display)
    pygame.display.set_caption("lightgun-joypad — simulador")
    W, H = screen.get_size()
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("dejavusansmono,monospace", max(14, H // 60))
    big = pygame.font.SysFont("dejavusans,sans", max(28, H // 22), bold=True)

    rnd = random.Random()
    target_r = max(18, int(H * 0.045))
    show_cross = True
    show_trail = True
    trail: deque = deque(maxlen=40)
    impacts: deque = deque(maxlen=30)
    stats = {"shots": 0, "hits": 0, "err": []}
    target = None
    target_t = 0.0
    cal_step = None  # None ou índice em CAL_TARGETS
    cal_src, cal_dst = [], []
    message, message_t = "Mire no CENTRO e aperte Y (ou R) para alinhar. C = calibrar.", time.monotonic()
    rate, rate_n, rate_t = 0.0, 0, time.monotonic()

    def say(txt):
        nonlocal message, message_t
        message, message_t = txt, time.monotonic()

    def new_target():
        nonlocal target, target_t
        m = target_r * 2
        target = (rnd.uniform(m, W - m), rnd.uniform(m, H - m))
        target_t = time.monotonic()

    def handle_shot(px, py, fwd):
        nonlocal cal_step, cal_src, cal_dst
        if cal_step is not None:
            if fwd is None:
                return
            if cal_step == 0:
                ctl.tracker.yaw_offset = heading(fwd)
            uv = project(rotate_yaw(fwd, -ctl.tracker.yaw_offset))
            if uv is None:
                say("Mira muito fora — tente de novo.")
                return
            cal_src.append(uv)
            cal_dst.append(CAL_TARGETS[cal_step][1])
            cal_step += 1
            if cal_step == len(CAL_TARGETS):
                Hm, rms = fit_calibration(cal_src, cal_dst)
                ctl.tracker.set_homography(Hm)
                ctl.gun.smooth and ctl.gun.smooth.reset()
                cal_step = None
                txt = f"Calibrado! erro {rms * 100:.2f}% da tela"
                if not windowed:
                    p = save_calibration({
                        "version": 1, "homography": Hm.to_list(), "rms_error": rms,
                        "points_uv": cal_src, "gyro_bias_dps": list(ctl.tracker.bias.bias),
                        "device": ctl.device, "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    }, calib_path)
                    txt += f" — salvo em {p}"
                else:
                    txt += " (janela: não salvo; use tela cheia para salvar)"
                say(txt)
            return
        stats["shots"] += 1
        hit = False
        if target is not None:
            d = math.hypot(px - target[0], py - target[1])
            stats["err"].append(d)
            hit = d <= target_r
        impacts.append((px, py, time.monotonic(), hit))
        if hit:
            stats["hits"] += 1
            new_target()

    new_target()
    running = True
    while running:
        now = time.monotonic()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                k = ev.key
                if k == pygame.K_ESCAPE:
                    if cal_step is not None:
                        cal_step = None
                        say("Calibração cancelada.")
                    else:
                        running = False
                elif k == pygame.K_h:
                    show_cross = not show_cross
                    say("Mira VISÍVEL" if show_cross else "Mira ESCONDIDA — atire às cegas e veja onde acertou")
                elif k == pygame.K_t:
                    show_trail = not show_trail
                elif k == pygame.K_n:
                    stats = {"shots": 0, "hits": 0, "err": []}
                    impacts.clear()
                elif k in (pygame.K_r, pygame.K_SPACE):
                    ctl.tracker.recenter()
                    say("Recentrado.")
                elif k == pygame.K_c:
                    cal_step, cal_src, cal_dst = 0, [], []
                    say("Calibração: mire em cada alvo e aperte o gatilho.")
            elif ev.type == pygame.MOUSEBUTTONDOWN and not ctl.connected and ev.button == 1:
                handle_shot(*ev.pos, None)

        # Posição da mira
        if ctl.connected:
            x, y = ctl.out.pos
            px, py = x * W, y * H
        else:
            px, py = pygame.mouse.get_pos()
        trail.append((px, py))

        # Tiros vindos do controle
        while ctl.out.shots:
            shot = ctl.out.shots.popleft()
            if shot["button"] == "left":
                sx, sy = shot["pos"]
                handle_shot(sx * W, sy * H, shot["forward"])
        ctl.out.keys.clear()

        if cal_step is None and now - target_t > 4.0:
            new_target()

        # Taxa do IMU
        if now - rate_t >= 1.0:
            rate = (ctl.gun.samples - rate_n) / (now - rate_t)
            rate_n, rate_t = ctl.gun.samples, now

        # ---- desenho ----
        screen.fill((14, 17, 24))
        grid = (28, 33, 44)
        for i in range(1, 8):
            pygame.draw.line(screen, grid, (W * i // 8, 0), (W * i // 8, H))
        for i in range(1, 6):
            pygame.draw.line(screen, grid, (0, H * i // 6), (W, H * i // 6))
        pygame.draw.rect(screen, (70, 80, 100), (0, 0, W, H), 3)
        pygame.draw.circle(screen, (60, 70, 90), (W // 2, H // 2), 6, 1)

        if cal_step is not None:
            label, (tx, ty) = CAL_TARGETS[cal_step]
            cx, cy = int(tx * (W - 1)), int(ty * (H - 1))
            for r, c in ((60, (255, 80, 80)), (40, (255, 255, 255)), (20, (255, 80, 80))):
                pygame.draw.circle(screen, c, (cx, cy), r, 4)
            pygame.draw.line(screen, (255, 255, 255), (cx - 80, cy), (cx + 80, cy), 2)
            pygame.draw.line(screen, (255, 255, 255), (cx, cy - 80), (cx, cy + 80), 2)
            t = big.render(f"Calibração {cal_step + 1}/5: mire no {label} e atire", True, (255, 220, 120))
            screen.blit(t, t.get_rect(center=(W // 2, H // 3 if cal_step else H // 4)))
        elif target is not None:
            tx, ty = int(target[0]), int(target[1])
            frac = min(1.0, (now - target_t) / 4.0)
            pygame.draw.circle(screen, (220, 60, 60), (tx, ty), target_r)
            pygame.draw.circle(screen, (255, 255, 255), (tx, ty), int(target_r * 0.66))
            pygame.draw.circle(screen, (220, 60, 60), (tx, ty), int(target_r * 0.33))
            pygame.draw.arc(screen, (255, 200, 80), (tx - target_r - 6, ty - target_r - 6, 2 * target_r + 12, 2 * target_r + 12),
                            math.pi / 2, math.pi / 2 + 2 * math.pi * (1 - frac), 3)

        for ix, iy, it, hit in impacts:
            age = now - it
            if age > 1.5:
                continue
            col = (80, 255, 120) if hit else (255, 210, 60)
            pygame.draw.circle(screen, col, (int(ix), int(iy)), 7)
            pygame.draw.circle(screen, col, (int(ix), int(iy)), int(12 + age * 30), 2)

        if show_cross:
            if show_trail and len(trail) > 1:
                pts = [(int(a), int(b)) for a, b in trail]
                pygame.draw.lines(screen, (60, 120, 200), False, pts, 2)
            raw = ctl.gun.raw if ctl.connected else None
            if raw is not None:
                pygame.draw.circle(screen, (110, 110, 140), (int(raw[0] * W), int(raw[1] * H)), 3)
            c = (80, 255, 160)
            ipx, ipy = int(px), int(py)
            pygame.draw.circle(screen, c, (ipx, ipy), 18, 2)
            pygame.draw.line(screen, c, (ipx - 28, ipy), (ipx - 8, ipy), 2)
            pygame.draw.line(screen, c, (ipx + 8, ipy), (ipx + 28, ipy), 2)
            pygame.draw.line(screen, c, (ipx, ipy - 28), (ipx, ipy - 8), 2)
            pygame.draw.line(screen, c, (ipx, ipy + 8), (ipx, ipy + 28), 2)

        # HUD
        err = stats["err"]
        mean_err = sum(err) / len(err) if err else 0.0
        lines = [
            f"controle: {ctl.device or '-'}  [{ctl.status}]" + ("" if ctl.connected else "  (mouse simula a arma)"),
            f"IMU: {rate:5.0f} amostras/s   bias gyro: {'ok' if ctl.tracker.bias.acquired else 'apoie parado ~1s'}"
            f" ({', '.join(f'{b:+.2f}' for b in ctl.tracker.bias.bias)}) °/s   FPS: {clock.get_fps():4.0f}",
            f"tiros: {stats['shots']}  acertos: {stats['hits']}  erro médio: {mean_err:5.1f} px"
            f" ({mean_err / W * 100:4.1f}% da largura)" + ("" if show_cross else "   [MIRA ESCONDIDA]"),
            "ESC sair | C calibrar | Y/R recentrar | H esconder mira | T rastro | N zerar",
        ]
        if ctl.gun.paused:
            lines.append("MIRA PAUSADA (HOME/Captura)")
        for i, ln in enumerate(lines):
            screen.blit(font.render(ln, True, (170, 180, 200)), (12, 10 + i * (font.get_height() + 2)))
        if message and now - message_t < 6:
            m = font.render(message, True, (255, 230, 140))
            screen.blit(m, m.get_rect(midbottom=(W // 2, H - 14)))

        pygame.display.flip()
        clock.tick(240)

    pygame.quit()
    return 0
