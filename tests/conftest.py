import pytest


@pytest.fixture(autouse=True)
def _no_real_monitors(monkeypatch):
    """Os testes não dependem dos monitores da máquina (xrandr)."""
    import capybara_lightgun.outputs as o

    monkeypatch.setattr(o, "x11_monitors", lambda: ([], (0, 0)))
    monkeypatch.setattr(o, "_active_mon", {"idx": None, "started": True})
