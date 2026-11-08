"""Lógica da saída do macOS com o sistema simulado (roda em qualquer plataforma)."""
import importlib
import sys
import types

import pytest

from lightgun_joypad.config import KEY_NAMES


@pytest.fixture
def fake_macos(monkeypatch):
    posted = []
    m = types.ModuleType("lightgun_joypad.macos")
    m.LEFT_DOWN, m.LEFT_UP, m.RIGHT_DOWN, m.RIGHT_UP, m.MOVED = 1, 2, 3, 4, 5
    m.LEFT_DRAG, m.RIGHT_DRAG, m.OTHER_DOWN, m.OTHER_UP, m.OTHER_DRAG = 6, 7, 25, 26, 27
    m.displays = lambda: [(0.0, 0.0, 1440.0, 900.0), (1440.0, -200.0, 1920.0, 1080.0)]
    m.desktop = lambda: (0.0, -200.0, 3360.0, 1100.0)
    m.cursor = lambda: (100.0, 100.0)
    m.post_mouse = lambda kind, x, y, button=0, dx=0, dy=0: posted.append(("m", kind, round(x), round(y), button))
    m.post_key = lambda code, down: posted.append(("k", code, down))
    src = open(importlib.util.find_spec("lightgun_joypad").submodule_search_locations[0] + "/macos.py").read()
    keys_src = src[src.index("KEYCODES = {"):src.index("}", src.index("KEYCODES = {")) + 1]
    exec(keys_src, m.__dict__)
    monkeypatch.setitem(sys.modules, "lightgun_joypad.macos", m)
    import lightgun_joypad
    monkeypatch.setattr(lightgun_joypad, "macos", m, raising=False)
    sys.modules.pop("lightgun_joypad.outputs.mac_quartz", None)
    mq = importlib.import_module("lightgun_joypad.outputs.mac_quartz")
    yield m, mq, posted
    sys.modules.pop("lightgun_joypad.outputs.mac_quartz", None)


def test_all_keys_have_mac_codes(fake_macos):
    m, _, _ = fake_macos
    assert [k for k in KEY_NAMES if k not in m.KEYCODES] == []


def test_monitor_mapping_and_drag(fake_macos):
    _, mq, posted = fake_macos
    o = mq.QuartzOutput([0, 0, 1, 1], [], monitor=1)  # 2º monitor, acima/à direita
    o.move(0.0, 0.0)
    o.move(1.0, 1.0)
    assert posted[0] == ("m", 5, 1440, -200, 0)
    assert posted[1] == ("m", 5, 3359, 879, 0)
    o.button("left", True)
    o.move(0.5, 0.5)  # botão segurado -> evento de arrastar
    o.button("left", False)
    kinds = [p[1] for p in posted[2:]]
    assert kinds == [1, 6, 2]


def test_region_on_whole_desktop_and_keys(fake_macos):
    _, mq, posted = fake_macos
    o = mq.QuartzOutput([0, 0, 0.5, 1], [])
    o.move(1.0, 0.5)
    assert posted[-1][2:4] == (1680, 350)
    o.key("enter", True)
    o.key("enter", False)
    assert posted[-2:] == [("k", 0x24, True), ("k", 0x24, False)]
    o.button("right", True)
    o.close()  # solta botões presos
    assert posted[-1][1] == 4
