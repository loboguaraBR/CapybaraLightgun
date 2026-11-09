"""Autoteste: confere as peças do sistema sem precisar de controle.

    lightgun-joypad selftest

Roda nos testes automáticos (Linux, Windows e macOS) e serve de roteiro para
quem for testar num computador novo. Não move o cursor nem clica.
"""
from __future__ import annotations

import os
import sys
import time
import traceback

RESULTS: list = []


def check(name: str, required: bool = True):
    def deco(fn):
        try:
            info = fn()
            RESULTS.append((name, "ok", info or ""))
        except Exception as exc:  # noqa: BLE001
            RESULTS.append((name, "FALHOU" if required else "aviso", f"{type(exc).__name__}: {exc}"))
            if os.environ.get("LGJ_SELFTEST_TRACE"):
                traceback.print_exc()
        return fn
    return deco


def run() -> int:
    plat = sys.platform

    @check("núcleo: mira simulada acerta o alvo")
    def _core():
        from .config import DEFAULTS, merge
        from .engine import LightGun, Tracker
        from .fusion import quat_conj, quat_from_euler, quat_mul, quat_rotate
        from .geometry import Homography
        from .inputs import ImuSample
        import math

        cfg = merge(DEFAULTS, {"smoothing": {"enabled": False}, "motion": {"interp_ms": 0}})

        class Out:
            def move(self, x, y): self.p = (x, y)
            def move_rel(self, *a): pass
            def button(self, *a): pass
            def key(self, *a): pass

        gun = LightGun(cfg, Tracker(cfg, Homography.from_screen(1.21, 0.68, 2.0)), Out())
        yaw1, pitch1 = math.atan2(-(0.8 - 0.5) * 1.21, 2.0), -math.atan2((0.5 - 0.3) * 0.68, math.hypot(2.0, 0.3 * 1.21))
        path = [quat_from_euler(0, 0, 0)] * 20 + [quat_from_euler(yaw1 * k / 100, pitch1 * k / 100, 0) for k in range(101)]
        for q0, q1 in zip(path, path[1:]):
            d = quat_mul(quat_conj(q0), q1)
            ang = 2 * math.acos(min(1.0, d[0]))
            sn = math.sqrt(max(1e-18, 1 - d[0] ** 2))
            w = tuple(math.degrees(d[i + 1] / sn * ang / 0.005) if ang > 1e-9 else 0.0 for i in range(3))
            gun.on_imu(ImuSample(w, quat_rotate(quat_conj(q1), (0, 0, 1)), 0.005), 0.0)
        x, y = gun.pos
        assert abs(x - 0.8) < 0.01 and abs(y - 0.3) < 0.01, (x, y)
        return f"mira em ({x:.3f}, {y:.3f}), esperado (0.800, 0.300)"

    @check("SDL (controles com giroscópio)", required=False)
    def _sdl():
        from .inputs.sdl_source import list_devices

        devs = list_devices()
        return f"{len(devs)} controle(s): {devs}" if devs else "biblioteca ok, nenhum controle conectado"

    if plat in ("win32", "darwin"):
        @check("hidapi (Joy-Con / Pro Controller)")
        def _hid():
            from .inputs.switch_hid import list_devices

            devs = list_devices()
            return f"{len(devs)} controle(s) Nintendo" if devs else "biblioteca ok, nenhum Joy-Con conectado"

    @check("mouse do sistema como fonte (leitura do cursor)", required=plat != "linux" or bool(os.environ.get("DISPLAY")))
    def _mouse():
        from .inputs.mouse_source import MouseSource

        m = MouseSource()
        x, y, b = m.api.query()
        m.close()
        return f"cursor em ({x:.3f}, {y:.3f}), botões {sorted(b) or '-'}"

    if plat == "darwin":
        @check("macOS: telas")
        def _displays():
            from . import macos

            return f"{macos.displays()} → área total {macos.desktop()}"

        @check("macOS: teclas mapeadas")
        def _keys():
            from . import macos
            from .config import KEY_NAMES

            missing = [k for k in KEY_NAMES if k not in macos.KEYCODES]
            assert not missing, missing
            return f"{len(KEY_NAMES)} teclas"

        @check("macOS: saída Quartz (criação, sem mover o cursor)")
        def _quartz():
            from .outputs.mac_quartz import QuartzOutput

            o = QuartzOutput([0, 0, 1, 1], [])
            return f"área {o.area}"

        @check("macOS: permissões", required=False)
        def _perms():
            from . import macos

            missing = macos.missing_permissions()
            assert not missing, "falta: " + ", ".join(missing)
            return "Acessibilidade e Monitoramento de Entrada liberados"

    if plat == "win32":
        @check("Windows: saída SendInput (criação)")
        def _win():
            from .outputs.windows_sendinput import SendInputOutput, monitors

            SendInputOutput([0, 0, 1, 1], [])
            return f"{len(monitors())} monitor(es)"

    @check("janela de troca automática de perfil", required=False)
    def _win_text():
        from .activewin import active_window_text

        t = active_window_text()
        return repr(t[:80]) if t else "sem janela ativa (normal em servidor de testes)"

    @check("aplicativo: monta a janela, a bandeja e o estande (fora da tela)")
    def _gui():
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        import tempfile

        from PyQt5 import QtWidgets

        from . import gui
        from .client import ClientApp
        from .config import ConfigStore

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        d = tempfile.mkdtemp()
        store = ConfigStore(os.path.join(d, "c.json"))
        core = ClientApp(store, os.path.join(d, "cal.json"), output_backend="none")
        win = gui.MainWindow(core, False)
        win.tray = None
        win.show()
        rng = gui.TestRange(core)
        t = time.time()
        while time.time() - t < 0.5:
            app.processEvents()
            time.sleep(0.01)
        rng.close()
        win.quitting = True
        win.close()
        return f"{win.tabs.count()} abas"

    width = max(len(n) for n, _, _ in RESULTS)
    print(f"\nAutoteste do Light Gun Joypad — {plat}, Python {sys.version.split()[0]}\n")
    for name, status, info in RESULTS:
        mark = {"ok": "✓", "aviso": "!", "FALHOU": "✗"}[status]
        print(f" {mark} {name.ljust(width)}  {info}")
    failed = [r for r in RESULTS if r[1] == "FALHOU"]
    print(f"\n{'TUDO OK' if not failed else f'{len(failed)} FALHA(S)'}\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run())
