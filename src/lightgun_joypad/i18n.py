"""Idiomas da interface.

Os textos do aplicativo são escritos em inglês (o idioma padrão) e passam por
`tr()`. Cada idioma é um arquivo em `locales/` com um dicionário
{texto em inglês: tradução}. Chaves começando com "@" são textos longos
(ex.: "@help"), que existem também em inglês (`locales/en.py`).

A escolha fica salva em settings.json, na pasta de configuração.
"""
from __future__ import annotations

import importlib
import json

from .config import config_dir

# código -> nome no próprio idioma (o seletor mostra sempre assim)
LANGUAGES = {
    "en": "English",
    "pt_BR": "Português (Brasil)",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "zh_CN": "中文（简体）",
}
DEFAULT = "en"
# Rótulo do seletor: sempre em inglês, para achar o caminho de volta
# mesmo se um idioma desconhecido for escolhido por engano.
SELECTOR_LABEL = "🌐 Language"

_current = DEFAULT
_catalog: dict = {}
_english: dict = {}


def _load(code: str) -> dict:
    try:
        return importlib.import_module(f"lightgun_joypad.locales.{code}").T
    except (ImportError, AttributeError):
        return {}


def settings_path():
    return config_dir() / "settings.json"


def saved_language() -> str:
    try:
        code = json.loads(settings_path().read_text(encoding="utf-8")).get("language", DEFAULT)
    except (OSError, ValueError):
        code = DEFAULT
    return code if code in LANGUAGES else DEFAULT


def save_language(code: str) -> None:
    p = settings_path()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data["language"] = code
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def set_language(code: str) -> None:
    global _current, _catalog, _english
    if code not in LANGUAGES:
        code = DEFAULT
    _current = code
    _english = _load("en")
    _catalog = {} if code == "en" else _load(code)


def current() -> str:
    return _current


def tr(text: str) -> str:
    """Traduz um texto em inglês para o idioma atual (ou devolve o inglês)."""
    if not _english and not _catalog:
        set_language(_current)
    out = _catalog.get(text)
    if out:
        return out
    if text.startswith("@"):
        return _english.get(text, text)
    return text
