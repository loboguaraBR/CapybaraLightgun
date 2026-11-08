"""Núcleo do cliente residente: lê o controle numa thread, aplica perfis,
calibração e expõe o estado para a interface (gui.py)."""
from __future__ import annotations

import os
import sys
import threading
import time

from . import __version__
from .calibration import TARGETS, Calibrator
from .config import ConfigStore, config_dir, default_calibration_path, load_calibration, save_calibration
from .engine import LightGun, Tracker, homography_from
from .inputs import DeviceLost, NoDeviceFound, open_source
from .outputs import OutputProxy


def effective_config(store: ConfigStore, name: str | None = None) -> dict:
    """Config do perfil, com as combinações impossíveis corrigidas."""
    cfg = store.effective(name)
    if not sys.platform.startswith("linux"):
        cfg["output_target"] = "mouse"  # o modo driver só existe no Linux
    return cfg


class ClientApp:
    def __init__(self, store: ConfigStore, calib_path: str | None = None, output_backend: str | None = None):
        self.store = store
        self.calib_path = calib_path
        cfg = effective_config(store)
        self.calib = load_calibration(calib_path)
        self.out = OutputProxy(cfg, output_backend)
        self.tracker = Tracker(cfg, homography_from(cfg, self.calib))
        if self.calib and self.calib.get("gyro_bias_dps"):
            self.tracker.bias.bias = list(self.calib["gyro_bias_dps"])
        self.gun = LightGun(cfg, self.tracker, self.out)
        self.lock = threading.RLock()
        self.status = "procurando controle..."
        self.device = ""
        self.connected = False
        self.src = None
        self.cal: Calibrator | None = None
        self._cal_prev_paused = False
        self.cal_last = None  # resultado da última calibração (para o painel)
        self._rate = 0.0
        self._rate_n = 0
        self._rate_t = time.monotonic()
        self.started = time.time()
        self.stop = threading.Event()

    # ---- controle ------------------------------------------------------------
    def controller_loop(self) -> None:
        while not self.stop.is_set():
            cfg = effective_config(self.store)
            try:
                src = open_source(cfg)
            except NoDeviceFound as exc:
                self.connected = False
                self.status = "sem controle — " + str(exc).splitlines()[-1].strip()
                self.stop.wait(2.0)
                continue
            except Exception as exc:
                self.connected = False
                self.status = f"erro ao abrir o controle: {exc}"
                self.stop.wait(3.0)
                continue
            self.src = src
            self._src_choice = cfg.get("input_source", "auto")
            self.device = src.name
            self.connected = True
            self.status = "conectado"
            print(f"controle conectado: {src.name}", flush=True)
            try:
                self.gun.run(src)
            except DeviceLost as exc:
                self.status = f"desconectado ({exc})"
            except Exception as exc:
                self.status = f"erro: {exc}"
            finally:
                self.connected = False
                self.src = None
                self.gun.release_all()
                try:
                    src.close()
                except Exception:
                    pass
                print(f"controle: {self.status}", flush=True)
            self.stop.wait(1.0)

    def reconnect(self) -> None:
        src = self.src
        if src is not None:
            try:
                src.close()  # a leitura falha e o laço reabre o controle
            except Exception:
                pass

    # ---- configuração --------------------------------------------------------
    def apply_active(self) -> None:
        cfg = effective_config(self.store)
        src = self.src
        if src is not None and (cfg.get("input_source", "auto") != getattr(self, "_src_choice", None)):
            self.reconnect()  # trocou a fonte da mira: reabre
        self.gun.apply_config(cfg)
        self.out.reconfigure(cfg)
        if not self.calib:
            self.tracker.set_homography(homography_from(cfg, None))

    # ---- calibração ----------------------------------------------------------
    def calibrate_start(self) -> None:
        with self.lock:
            if self.cal is None:
                self._cal_prev_paused = self.gun.paused
            self.cal = Calibrator(self.tracker)
            self.cal_last = None
            self.gun.paused = True
            self.gun.capture_hook = self._on_capture

    def _on_capture(self, forward) -> None:
        with self.lock:
            cal = self.cal
            if cal is None:
                return
            if cal.add(forward):
                data = cal.to_dict(self.device)
                save_calibration(data, self.calib_path)
                self.calib = data
                self.cal_last = {"rms": cal.result[1], "ok": True}
                self._cal_end()

    def calibrate_cancel(self) -> None:
        with self.lock:
            if self.cal is not None:
                self.cal.cancel()
                self._cal_end()

    def _cal_end(self) -> None:
        self.cal = None
        self.gun.capture_hook = None
        self.gun.paused = self._cal_prev_paused
        if self.gun.smooth is not None:
            self.gun.smooth.reset()

    def calibration_reset(self) -> None:
        with self.lock:
            p = self.calib_path or default_calibration_path()
            try:
                os.remove(p)
            except FileNotFoundError:
                pass
            self.calib = None
            self.tracker.set_homography(homography_from(effective_config(self.store), None))

    # ---- estado para o painel ------------------------------------------------
    def state(self) -> dict:
        now = time.monotonic()
        if now - self._rate_t >= 0.5:
            self._rate = (self.gun.samples - self._rate_n) / (now - self._rate_t)
            self._rate_n, self._rate_t = self.gun.samples, now
        g = self.gun
        raw = g.raw
        cal = self.cal
        cal_state = None
        if cal is not None:
            tgt = cal.target()
            cal_state = {
                "step": cal.step, "total": len(TARGETS),
                "label": tgt[0] if tgt else "", "target": list(tgt[1]) if tgt else None,
                "message": cal.message,
            }
        return {
            "version": __version__,
            "connected": self.connected,
            "device": self.device,
            "status": self.status,
            "rate": round(self._rate),
            "bias_ok": self.tracker.bias.acquired,
            "bias": [round(b, 3) for b in self.tracker.bias.bias],
            "paused": g.paused,
            "mode": g.mode,
            "target": g.cfg.get("output_target", "mouse"),
            "source": g.cfg.get("input_source", "auto"),
            "family": getattr(self.src, "family", "") if self.connected else "",
            "outside": g.outside,
            "overlay_on": g.overlay_on,
            "yielding": time.monotonic() < g.yield_until,
            "pos": [round(g.pos[0], 4), round(g.pos[1], 4)],
            "raw": [round(raw[0], 4), round(raw[1], 4)] if raw else None,
            "onscreen": g.onscreen,
            "pressed": sorted(g.pressed),
            "profile": self.store.active,
            "calibrating": cal_state,
            "cal_last": self.cal_last,
            "calibration": {
                "loaded": bool(self.calib),
                "rms": (self.calib or {}).get("rms_error"),
                "created": (self.calib or {}).get("created"),
            },
            "output": {"name": self.out.name, "error": self.out.error},
        }

    # ---- perfis ----------------------------------------------------------------
    def select_profile(self, name: str) -> None:
        if name not in self.store.profiles:
            raise ValueError("perfil não existe")
        self.manual_profile = name
        self.store.active = name
        self.store.save()
        self.apply_active()

    def save_profile(self, name: str, cfg: dict) -> None:
        self.store.set_profile(name, cfg)
        self.store.save()
        if name == self.store.active:
            self.apply_active()

    # ---- troca automática de perfil ------------------------------------------
    def auto_switch(self, window_text: str) -> str | None:
        """Ativa o perfil cujo `auto_match` aparece no texto da janela ativa.

        Sem correspondência, volta ao perfil escolhido manualmente.
        Retorna o nome do perfil se trocou.
        """
        text = (window_text or "").lower()
        if not text or "light gun joypad" in text:
            return None
        store = self.store
        if not hasattr(self, "manual_profile") or self.manual_profile not in store.profiles:
            self.manual_profile = store.active
        target = None
        for name, prof in store.profiles.items():
            words = [w.strip().lower() for w in str(prof.get("auto_match", "")).split(",") if w.strip()]
            if any(w in text for w in words):
                target = name
                break
        target = target or self.manual_profile
        if target != store.active:
            store.active = target
            self.apply_active()
            return target
        return None

    def reset_bias(self) -> None:
        self.tracker.bias.acquired = False
        self.tracker.bias.bias = [0.0, 0.0, 0.0]

    def start(self) -> None:
        threading.Thread(target=self.controller_loop, daemon=True, name="controle").start()

    def shutdown(self) -> None:
        self.stop.set()
        self.reconnect()
        try:
            self.gun.release_all()
        finally:
            self.out.close()


def redirect_output_to_log() -> None:
    """Sem console (pythonw / atalho): grava a saída num arquivo de log."""
    if sys.stdout is None or sys.stderr is None or not sys.stdout.isatty():
        d = config_dir()
        d.mkdir(parents=True, exist_ok=True)
        f = open(d / "client.log", "a", encoding="utf-8", buffering=1)
        f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} lightgun-joypad {__version__} ---\n")
        sys.stdout = sys.stderr = f
