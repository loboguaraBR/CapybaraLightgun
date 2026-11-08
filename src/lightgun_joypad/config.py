"""Configuração com perfis (um por jogo) e caminhos de arquivos."""
from __future__ import annotations

import copy
import json
import os
import sys
import threading
from pathlib import Path

DEFAULTS: dict = {
    # Fonte da mira: "auto" (controle com giroscópio: Switch ou PlayStation),
    # "switch", "playstation" ou "mouse" (mouse comum vira light gun).
    "input_source": "auto",
    # Entrada: "auto" | "evdev" (Linux, drivers do kernel) | "hidapi"
    "input_backend": "auto",
    # Controle preferido: "auto" | "pro" | "joycon-r" | "joycon-l"
    "device": "auto",
    # Saída: "auto" | "uinput" (Linux) | "sendinput" (Windows) | "console"
    "output_backend": "auto",
    # Para onde vai a mira:
    #   "lightgun" = só light gun (driver): dispositivo próprio que a área de
    #                trabalho ignora — cursor e touchpad ficam livres; emuladores
    #                que leem o dispositivo direto (RetroArch/udev) usam a arma.
    #                Só no Linux.
    #   "mouse"    = mouse do sistema: move o cursor (funciona com qualquer jogo).
    "output_target": "lightgun" if sys.platform.startswith("linux") else "mouse",
    # Modo mouse: se o touchpad/mouse real se mexer, a arma solta o cursor por
    # alguns segundos (volta ao atirar ou quando o tempo acaba).
    "mouse_yield": {"enabled": True, "seconds": 2.5},
    # "absolute" = light gun (vai onde o cano aponta)
    # "relative" = mouse comum movido pelo giroscópio (jogos que não aceitam absoluto)
    "mode": "absolute",
    "relative_speed": 1.0,
    # Área da tela (normalizada sobre a área de trabalho inteira) onde a mira
    # é mapeada: [x0, y0, x1, y1]. Útil com vários monitores.
    "region": [0.0, 0.0, 1.0, 1.0],
    # Windows: índice do monitor (0, 1, ...) — sobrescreve "region".
    "monitor": None,
    # Escalas para o backend hidapi (dados crus do controle).
    "gyro_dps_per_lsb": 0.070,
    "accel_g_per_lsb": 1.0 / 4096.0,
    # Ajustes da mira.
    "aim": {
        "sensitivity_x": 1.0,  # 1 = arma real; >1 = menos movimento cobre a tela
        "sensitivity_y": 1.0,
        "offset_x": 0.0,  # ajuste fino do ponto de impacto (fração da tela)
        "offset_y": 0.0,
        "jitter_lock": 0.0,  # ignora movimentos menores que isso (fração da tela)
    },
    # Fusão: ganho de correção da inclinação pelo acelerômetro.
    "fusion": {"kp": 0.35, "accel_tolerance_g": 0.25},
    # Estimativa do bias do giroscópio quando o controle está parado.
    "auto_bias": {"enabled": True, "window_s": 0.6, "still_range_dps": 1.5, "accel_range_g": 0.03},
    # Geometria usada quando não há calibração.
    "screen": {"width_m": 1.21, "height_m": 0.68, "distance_m": 2.0},
    # One Euro: min_cutoff menor = mais estável parado; beta maior = menos lag.
    "smoothing": {"enabled": True, "min_cutoff": 1.2, "beta": 6.0, "d_cutoff": 1.0},
    # Movimento contínuo: o Bluetooth entrega as leituras em rajadas (3 a cada
    # ~15 ms) e às vezes trava. O cursor é atualizado num ritmo fixo
    # (output_hz), interpolando com `interp_ms` de atraso e prevendo o
    # movimento por até `max_extrap_ms` quando o Bluetooth atrasa.
    # interp_ms = 0 desliga (cursor salta a cada leitura).
    "motion": {"interp_ms": 16, "output_hz": 250, "max_extrap_ms": 40},
    # Compensação do "tranco" ao apertar o gatilho.
    "shot": {"lookback_ms": 25, "freeze_ms": 60},
    # Recarregar como numa light gun de verdade:
    #   offscreen_aim: apertar o gatilho mirando FORA da tela = tiro fora da tela
    #   shake: um tranco forte na arma (> shake_g) também recarrega
    "reload": {"offscreen_aim": True, "offscreen_margin": 0.02, "shake": False, "shake_g": 2.5},
    # Coice: vibração curta a cada tiro (Joy-Con/Pro/DualSense/DS4 no Linux).
    "rumble": {"enabled": True, "ms": 45, "strength": 0.7},
    # Mira desenhada na tela (útil no modo driver, em jogos sem mira).
    "overlay": {"enabled": False, "size": 36},
    # Troca automática para este perfil quando a janela ativa tiver uma destas
    # palavras (separadas por vírgula), ex.: "retroarch, mame".
    "auto_match": "",
    # Tiros por segundo da ação "autofire".
    "autofire_hz": 10,
    # Para onde a mira vai num "tiro fora da tela" (recarregar).
    "offscreen_position": [0.0, 0.0],
    # Linux/evdev: capturar os botões com exclusividade.
    "grab": False,
    # Botão -> ação (veja ACTIONS). Também aceita nomes crus do evdev.
    "buttons": {
        "ZR": "trigger",
        "ZL": "trigger",
        "R": "offscreen_shot",
        "L": "offscreen_shot",
        "A": "mouse_right",
        "RIGHT": "mouse_right",
        "B": "mouse_middle",
        "DOWN": "mouse_middle",
        "Y": "recenter",
        "LEFT": "recenter",
        "X": "key:1",
        "UP": "key:1",
        "PLUS": "key:5",
        "MINUS": "key:5",
        "HOME": "toggle",
        "CAPTURE": "toggle",
        "SR": "key:esc",
        "SL": "key:enter",
        # Fonte "mouse comum"
        "MOUSE_LEFT": "trigger",
        "MOUSE_RIGHT": "offscreen_shot",
        "MOUSE_MIDDLE": "key:5",
        "MOUSE_X1": "key:1",
        "MOUSE_X2": "recenter",
    },
}

ACTIONS = {
    "": "nada",
    "trigger": "Gatilho (clique esquerdo)",
    "autofire": "Tiro automático",
    "offscreen_shot": "Tiro fora da tela (recarregar)",
    "mouse_left": "Clique esquerdo",
    "mouse_right": "Clique direito",
    "mouse_middle": "Clique do meio",
    "recenter": "Recentrar mira",
    "toggle": "Pausar/retomar mira",
    "toggle_crosshair": "Mostrar/esconder mira na tela",
    "key": "Tecla do teclado…",
}

KEY_NAMES = (
    [chr(c) for c in range(ord("a"), ord("z") + 1)]
    + [str(d) for d in range(10)]
    + [f"f{i}" for i in range(1, 13)]
    + ["enter", "esc", "space", "tab", "backspace", "shift", "ctrl", "alt", "up", "down", "left", "right",
       "insert", "delete", "home", "end", "pageup", "pagedown", "pause"]
)

BUTTON_NAMES = ["ZR", "R", "ZL", "L", "A", "B", "X", "Y", "UP", "DOWN", "LEFT", "RIGHT",
                "PLUS", "MINUS", "HOME", "CAPTURE", "SL", "SR", "RSTICK", "LSTICK",
                "MOUSE_LEFT", "MOUSE_RIGHT", "MOUSE_MIDDLE", "MOUSE_X1", "MOUSE_X2"]

# Como cada botão se chama em cada controle (para mostrar na tela).
BUTTON_LABELS = {
    "ZR": "ZR · R2", "R": "R · R1", "ZL": "ZL · L2", "L": "L · L1",
    "A": "A · ○", "B": "B · ✕", "X": "X · △", "Y": "Y · □",
    "PLUS": "+ · Options", "MINUS": "− · Create/Share", "HOME": "Home · PS", "CAPTURE": "Captura · touchpad",
    "RSTICK": "R3", "LSTICK": "L3", "UP": "↑", "DOWN": "↓", "LEFT": "←", "RIGHT": "→",
    "MOUSE_LEFT": "Mouse esq.", "MOUSE_RIGHT": "Mouse dir.", "MOUSE_MIDDLE": "Mouse meio",
    "MOUSE_X1": "Mouse lateral 1", "MOUSE_X2": "Mouse lateral 2",
}

# Perfis prontos (sobreposições em cima de DEFAULTS).
PRESETS: dict = {
    "Padrão (light gun)": {},
    "MAME (-offscreen_reload)": {
        "buttons": dict(DEFAULTS["buttons"], R="mouse_right", L="mouse_right"),
    },
    "Arcade tiro rápido": {
        "buttons": dict(DEFAULTS["buttons"], ZR="autofire", ZL="trigger"),
        "autofire_hz": 12,
        "smoothing": {"enabled": True, "min_cutoff": 1.8, "beta": 10.0, "d_cutoff": 1.0},
    },
    "Precisão (tiro ao alvo)": {
        "smoothing": {"enabled": True, "min_cutoff": 0.6, "beta": 4.0, "d_cutoff": 1.0},
        "aim": dict(DEFAULTS["aim"], jitter_lock=0.0015),
        "shot": {"lookback_ms": 35, "freeze_ms": 90},
    },
    "Mouse comum como light gun": {
        "input_source": "mouse",
        "output_target": "lightgun",
        "motion": {"interp_ms": 0, "output_hz": 250, "max_extrap_ms": 0},
        "smoothing": {"enabled": False, "min_cutoff": 1.2, "beta": 6.0, "d_cutoff": 1.0},
        "shot": {"lookback_ms": 0, "freeze_ms": 0},
    },
    "PlayStation (DualSense/DS4)": {
        "input_source": "playstation",
    },
    "Mouse giroscópio (PC/FPS)": {
        "mode": "relative",
        "relative_speed": 1.5,
        "buttons": dict(DEFAULTS["buttons"], ZR="mouse_left", ZL="mouse_right", R="key:r", L="key:shift"),
    },
}


def config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "lightgun-joypad"


def default_config_path() -> Path:
    return config_dir() / "config.json"


def default_calibration_path() -> Path:
    return config_dir() / "calibration.json"


def merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if k == "buttons" and isinstance(v, dict):
            out[k] = dict(v)  # mapa de botões do perfil substitui o padrão
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


class ConfigStore:
    """Arquivo config.json: {"active": nome, "profiles": {nome: config}}."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else default_config_path()
        self.lock = threading.RLock()
        self.active = "Padrão (light gun)"
        self.profiles: dict = {}
        self.load()

    def load(self) -> None:
        data = {}
        if self.path.exists():
            with open(self.path, encoding="utf-8") as fh:
                data = json.load(fh)
        if "profiles" in data:
            self.profiles = {n: merge(DEFAULTS, p) for n, p in data["profiles"].items()}
            self.active = data.get("active") or next(iter(self.profiles), self.active)
        elif data:  # formato antigo: config única
            self.profiles = {"Padrão (light gun)": merge(DEFAULTS, data)}
        if not self.profiles:
            self.profiles = {n: merge(DEFAULTS, p) for n, p in PRESETS.items()}
        if self.active not in self.profiles:
            self.active = next(iter(self.profiles))

    def save(self) -> None:
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump({"active": self.active, "profiles": self.profiles}, fh, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)

    def effective(self, name: str | None = None) -> dict:
        with self.lock:
            return merge(DEFAULTS, self.profiles[name or self.active])

    def set_profile(self, name: str, cfg: dict) -> None:
        with self.lock:
            self.profiles[name] = merge(DEFAULTS, cfg)

    def create(self, name: str, base: str | None = None) -> None:
        with self.lock:
            if name in self.profiles:
                raise ValueError("já existe um perfil com esse nome")
            if base in self.profiles:
                self.profiles[name] = copy.deepcopy(self.profiles[base])
            else:
                self.profiles[name] = merge(DEFAULTS, PRESETS.get(base or "", {}))

    def delete(self, name: str) -> None:
        with self.lock:
            if len(self.profiles) <= 1:
                raise ValueError("precisa existir pelo menos um perfil")
            self.profiles.pop(name, None)
            if self.active == name:
                self.active = next(iter(self.profiles))

    def rename(self, old: str, new: str) -> None:
        with self.lock:
            if new in self.profiles:
                raise ValueError("já existe um perfil com esse nome")
            self.profiles = {(new if k == old else k): v for k, v in self.profiles.items()}
            if self.active == old:
                self.active = new


def load_config(path: str | None = None) -> dict:
    if path and not Path(path).exists():
        raise FileNotFoundError(f"config não encontrada: {path}")
    return ConfigStore(path).effective()


def write_default_config(path: str | None = None) -> Path:
    store = ConfigStore(path)
    store.save()
    return store.path


def load_calibration(path: str | None = None) -> dict | None:
    p = Path(path) if path else default_calibration_path()
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def save_calibration(data: dict, path: str | None = None) -> Path:
    p = Path(path) if path else default_calibration_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return p
