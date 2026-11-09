"""Idiomas: todo texto traduzido em todos os idiomas, com os mesmos campos {…}."""
import importlib
import string

import pytest

from lightgun_joypad import i18n
from lightgun_joypad.locales import collect_strings

LANGS = [c for c in i18n.LANGUAGES if c != "en"]


def fields(s: str) -> set:
    return {f for _, f, _, _ in string.Formatter().parse(s) if f}


@pytest.mark.parametrize("code", LANGS)
def test_every_string_translated_with_same_placeholders(code):
    T = importlib.import_module(f"lightgun_joypad.locales.{code}").T
    strings = collect_strings()
    missing = sorted(strings - set(T))
    assert not missing, f"{code}: faltam {len(missing)}: {missing[:5]}"
    for en in strings:
        assert T[en].strip(), (code, en)
        assert fields(T[en]) == fields(en), (code, en, T[en])
    assert "<h3>" in T["@help"]


def test_english_is_default_and_help_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(i18n, "config_dir", lambda: tmp_path / "lightgun-joypad")
    assert i18n.saved_language() == "en"
    i18n.set_language("en")
    assert i18n.tr("Calibrate") == "Calibrate"
    assert "<h3>" in i18n.tr("@help")


def test_choice_is_saved_and_unknown_falls_back(tmp_path, monkeypatch):
    monkeypatch.setattr(i18n, "config_dir", lambda: tmp_path / "lgj")
    i18n.save_language("zh_CN")
    assert i18n.saved_language() == "zh_CN"
    i18n.set_language("zh_CN")
    assert i18n.tr("Calibrate") == "校准"
    # o seletor nunca é traduzido: é o caminho de volta para o inglês
    assert i18n.SELECTOR_LABEL == "🌐 Language" and i18n.LANGUAGES["en"] == "English"
    i18n.set_language("xx")
    assert i18n.current() == "en"
    i18n.set_language("en")


def test_legacy_portuguese_profile_names_are_migrated(tmp_path):
    import json

    from lightgun_joypad.config import ConfigStore

    p = tmp_path / "c.json"
    p.write_text(json.dumps({"active": "Arcade tiro rápido", "profiles": {
        "Padrão (light gun)": {"aim": {"sensitivity_x": 1.3}},
        "Arcade tiro rápido": {"autofire_hz": 15},
        "Meu jogo": {}}}), encoding="utf-8")
    s = ConfigStore(p)
    assert set(s.profiles) == {"Default (light gun)", "Rapid-fire arcade", "Meu jogo"}
    assert s.active == "Rapid-fire arcade"
    assert s.profiles["Default (light gun)"]["aim"]["sensitivity_x"] == 1.3
    assert s.profiles["Rapid-fire arcade"]["autofire_hz"] == 15
