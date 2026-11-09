"""Traduções da interface. Cada módulo define T = {texto em inglês: tradução}.

`collect_strings()` encontra todos os textos traduzíveis do programa; o teste
tests/test_i18n.py garante que todo idioma tem todos, com os mesmos campos {…}.
"""
from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent


def _tr_calls(path: Path) -> set:
    out = set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant) \
                and isinstance(node.args[0].value, str):
            f = node.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
            if name in ("tr", "_status"):
                out.add(node.args[0].value)
    return out


def collect_strings() -> set:
    from .. import gui_strings

    strings = set()
    for p in PKG.rglob("*.py"):
        if "locales" not in p.parts:
            strings |= _tr_calls(p)
    strings |= gui_strings()
    return {s for s in strings if s and not s.startswith("@")}
