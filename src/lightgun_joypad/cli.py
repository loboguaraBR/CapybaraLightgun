"""Linha de comando: lightgun-joypad [run|calibrate|buttons|devices|init-config]."""
from __future__ import annotations

import argparse
import sys
import time

from . import __version__
from .config import (
    default_calibration_path, default_config_path, load_calibration, load_config,
    save_calibration, write_default_config,
)
from .inputs import ButtonState, DeviceLost, NoDeviceFound, list_all, open_source


def _cmd_run(args, cfg) -> int:
    from .engine import LightGun, Tracker, homography_from
    from .outputs import open_output

    calib = load_calibration(args.calibration)
    if calib:
        print(f"calibração carregada (erro {calib.get('rms_error', 0) * 100:.2f}% da tela)")
    else:
        s = cfg["screen"]
        print(f"sem calibração: usando geometria {s['width_m']}x{s['height_m']} m a {s['distance_m']} m "
              "(rode `lightgun-joypad calibrate` para mira exata)")
    out = open_output(cfg, "console" if args.dry_run else None)
    print(f"saída: {out.name}")
    recenter_btns = [k for k, v in cfg["buttons"].items() if v == "recenter"]
    try:
        while True:
            try:
                src = open_source(cfg)
            except NoDeviceFound as exc:
                if not args.wait:
                    print(exc)
                    return 2
                print("aguardando controle...", end="\r")
                time.sleep(2)
                continue
            print(f"controle: {src.name}")
            print(f"-> aponte para o CENTRO da tela e aperte {'/'.join(recenter_btns) or 'recenter'} para alinhar.")
            tracker = Tracker(cfg, homography_from(cfg, calib))
            if calib and calib.get("gyro_bias_dps"):
                tracker.bias.bias = list(calib["gyro_bias_dps"])
            gun = LightGun(cfg, tracker, out, verbose=args.verbose)
            try:
                gun.run(src)
            except DeviceLost as exc:
                print(f"\ncontrole desconectado ({exc}).")
                if not args.wait:
                    return 1
            finally:
                gun.release_all()
                src.close()
    except KeyboardInterrupt:
        print("\nencerrado.")
        return 0
    finally:
        out.close()


def _cmd_calibrate(args, cfg) -> int:
    from .calibration import run_calibration
    from .engine import homography_from

    try:
        src = open_source(cfg)
    except NoDeviceFound as exc:
        print(exc)
        return 2
    print(f"controle: {src.name}")
    try:
        data = run_calibration(cfg, src, homography_from(cfg, None))
    except KeyboardInterrupt:
        print("\ncalibração cancelada.")
        return 1
    finally:
        src.close()
    path = save_calibration(data, args.calibration)
    print(f"\ncalibração salva em {path}")
    print("Ao jogar, aperte o botão de recentrar mirando no centro sempre que a mira escorregar.")
    return 0


def _cmd_buttons(args, cfg) -> int:
    try:
        src = open_source(cfg)
    except NoDeviceFound as exc:
        print(exc)
        return 2
    print(f"controle: {src.name} — aperte botões (Ctrl+C para sair)")
    try:
        for ev in src.events():
            if isinstance(ev, ButtonState) and ev.pressed:
                logical = sorted(n for n in ev.pressed if not n.startswith(("BTN_", "KEY_", "CODE_")))
                raw = sorted(n for n in ev.pressed if n.startswith(("BTN_", "KEY_", "CODE_")))
                acts = [f"{n}->{cfg['buttons'][n]}" for n in logical + raw if n in cfg["buttons"]]
                print(f"botões: {logical}  crus: {raw}  ações: {acts}")
    except (KeyboardInterrupt, DeviceLost):
        pass
    finally:
        src.close()
    return 0


def _cmd_sim(args, cfg) -> int:
    try:
        from .simulator import run_simulator
    except ImportError as exc:
        print(f"o simulador precisa do pygame: pip install pygame ({exc})")
        return 2
    return run_simulator(cfg, args.calibration, windowed=args.windowed, display=args.display)


def _cmd_gui(args, cfg) -> int:
    try:
        from .gui import run_gui
    except ImportError as exc:
        print(f"o aplicativo precisa do PyQt5: pip install PyQt5 ({exc})")
        return 2
    return run_gui(args.config, args.calibration, start_hidden=getattr(args, "tray", False))


def _cmd_devices(args, cfg) -> int:
    found = list_all()
    if not found:
        print("nada encontrado.")
    for backend, d in found:
        print(f"[{backend}] {d}")
    return 0


def _cmd_init_config(args, cfg) -> int:
    p = write_default_config(args.config)
    print(f"config padrão escrita em {p}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="lightgun-joypad", description="Joy-Con / Pro Controller como light gun (gyro).")
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--config", help=f"arquivo de config (padrão: {default_config_path()})")
    ap.add_argument("--calibration", help=f"arquivo de calibração (padrão: {default_calibration_path()})")
    ap.add_argument("--input", choices=["auto", "evdev", "hidapi"], help="backend de entrada")
    ap.add_argument("--device", choices=["auto", "pro", "joycon-r", "joycon-l"], help="controle preferido")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="usar o controle como light gun (padrão)")
    r.add_argument("--dry-run", action="store_true", help="não mexe no mouse; desenha a mira no terminal")
    r.add_argument("--wait", action="store_true", help="espera o controle conectar e reconecta sozinho")
    r.add_argument("-v", "--verbose", action="store_true")
    for name in ("gui", "client", "panel"):
        g = sub.add_parser(name, help="aplicativo: light gun + painel de configuração (janela e bandeja)"
                           if name == "gui" else f"o mesmo que 'gui'")
        g.add_argument("--tray", action="store_true", help="inicia escondido na bandeja")
    sm = sub.add_parser("sim", help="simulador: estande de tiro em tela cheia para testar a mira")
    sm.add_argument("--windowed", metavar="LxA", help="janela em vez de tela cheia, ex.: 1280x720")
    sm.add_argument("--display", type=int, default=0, help="monitor onde abrir (0, 1, ...)")
    sub.add_parser("calibrate", help="calibração guiada (centro + 4 cantos)")
    sub.add_parser("buttons", help="mostra o nome dos botões apertados")
    sub.add_parser("devices", help="lista controles detectados")
    sub.add_parser("selftest", help="autoteste do sistema (não precisa de controle)")
    sub.add_parser("init-config", help="cria o arquivo de config com os valores padrão")
    args = ap.parse_args(argv)
    if args.cmd is None:
        args.cmd, args.dry_run, args.wait, args.verbose = "run", False, True, False
    cfg = load_config(args.config)
    if args.input:
        cfg["input_backend"] = args.input
    if args.device:
        cfg["device"] = args.device
    handlers = {
        "run": _cmd_run, "calibrate": _cmd_calibrate, "buttons": _cmd_buttons,
        "devices": _cmd_devices, "sim": _cmd_sim,
        "selftest": lambda a, c: __import__("lightgun_joypad.selftest", fromlist=["run"]).run(),
        "gui": _cmd_gui, "client": _cmd_gui, "panel": _cmd_gui, "init-config": _cmd_init_config,
    }
    return handlers[args.cmd](args, cfg)


if __name__ == "__main__":
    sys.exit(main())
