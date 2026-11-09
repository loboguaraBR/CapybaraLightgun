"""Conversão de eixos (sem dependências; usada por evdev e hidapi)."""


def to_lightgun_axes(fam: str, v: tuple) -> tuple:
    """Converte para a convenção interna: X = cano (frente), Y = esquerda, Z = cima.

    Sony e SDL (mesmo padrão): X = direita, Y = cima, Z = em direção ao jogador.
    O "cano" de um controle PlayStation é a frente dele (onde fica a luz).
    """
    if fam in ("playstation", "sdl"):
        return (-v[2], -v[0], v[1])
    return v
