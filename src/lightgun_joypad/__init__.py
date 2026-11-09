"""Joy-Con / Pro Controller do Nintendo Switch como light gun (Linux e Windows)."""
__version__ = "0.7.0"


def gui_strings() -> set:
    """Textos de tabelas que a interface traduz (para o teste de idiomas)."""
    from .config import ACTIONS, BUTTON_LABELS, PRESETS
    from .gui_fields import CAL_LABELS, FIELDS, TAB_TITLES
    from .inputs import SOURCES

    out = set(ACTIONS.values()) | set(SOURCES.values()) | set(PRESETS) | set(TAB_TITLES) | set(CAL_LABELS)
    out |= {v for v in BUTTON_LABELS.values() if v.startswith(("Mouse", "Capture"))}
    for fields in FIELDS.values():
        for f in fields:
            out.add(f["l"])
            if f.get("h"):
                out.add(f["h"])
            for _, txt in f.get("o", []):
                out.add(txt)
    out |= {
        # nomes das saídas e mensagens vindas do núcleo
        "virtual light gun (driver, cursor free)", "system mouse (absolute)", "system mouse (SendInput)",
        "system mouse (Quartz)", "none (test)", "none", "console (simulation, mouse untouched)",
        "Light-gun-only (driver) mode exists only on Linux (Windows and macOS would need a system driver). "
        "Using the system mouse.",
        "Aim too far off (pointing sideways). Try again.", "Invalid points — starting over.",
        "Accessibility", "Input Monitoring",
    }
    return out
