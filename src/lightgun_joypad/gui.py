"""Aplicativo de janela (Qt): light gun residente com ícone na bandeja.

- A janela é o painel de configuração; fechar a janela mantém o programa
  rodando na bandeja (perto do relógio).
- Calibração e estande de teste abrem em tela cheia.
- Nada de rede: a instância única usa um canal local do sistema
  (QLocalServer = socket Unix / named pipe do Windows).
"""
from __future__ import annotations

import copy
import math
import random
import sys
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtNetwork import QLocalServer, QLocalSocket

from . import __version__
from .client import ClientApp, redirect_output_to_log
from .config import ACTIONS, BUTTON_NAMES, KEY_NAMES, PRESETS, ConfigStore

APP_ID = "lightgun-joypad-gui"

GREEN = QColor("#4ade80")
BLUE = QColor("#60a5fa")
AMBER = QColor("#fbbf24")
RED = QColor("#f87171")
MUTED = QColor("#9aa3b5")

STYLE = """
QWidget { font-size: 10pt; }
QGroupBox { border: 1px solid #2a3142; border-radius: 10px; margin-top: 14px; padding: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #9aa3b5; }
QPushButton { background: #1e2330; border: 1px solid #2a3142; border-radius: 8px; padding: 7px 12px; }
QPushButton:hover { border-color: #60a5fa; }
QPushButton#primary { background: #14532d; border-color: #166534; }
QPushButton#seg:checked { background: #1d4ed8; border-color: #3b82f6; color: white; font-weight: 600; }
QPushButton#primary:hover { border-color: #4ade80; }
QTabWidget::pane { border: 1px solid #2a3142; border-radius: 10px; top: -1px; }
QTabBar::tab { background: transparent; padding: 9px 16px; color: #9aa3b5; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #e6e9ef; border-bottom: 2px solid #4ade80; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit { background: #1e2330; border: 1px solid #2a3142; border-radius: 6px; padding: 4px 8px; }
QLabel#help { color: #9aa3b5; font-size: 9pt; }
QLabel#value { color: #60a5fa; min-width: 64px; }
QLabel#bname { background: #1e2330; border: 1px solid #2a3142; border-radius: 6px; padding: 3px 8px; font-weight: 600; }
QLabel#bname[on="true"] { background: #1d4ed8; border-color: #3b82f6; }
QSlider::groove:horizontal { height: 6px; background: #2a3142; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #2f7a4f; border-radius: 3px; }
QSlider::handle:horizontal { background: #4ade80; width: 16px; margin: -6px 0; border-radius: 8px; }
QScrollArea { border: none; }
"""


def dark_palette() -> QtGui.QPalette:
    p = QtGui.QPalette()
    bg, base, text = QColor("#0f1218"), QColor("#171b24"), QColor("#e6e9ef")
    p.setColor(QtGui.QPalette.Window, bg)
    p.setColor(QtGui.QPalette.WindowText, text)
    p.setColor(QtGui.QPalette.Base, base)
    p.setColor(QtGui.QPalette.AlternateBase, QColor("#1e2330"))
    p.setColor(QtGui.QPalette.Text, text)
    p.setColor(QtGui.QPalette.Button, QColor("#1e2330"))
    p.setColor(QtGui.QPalette.ButtonText, text)
    p.setColor(QtGui.QPalette.Highlight, QColor("#2563eb"))
    p.setColor(QtGui.QPalette.HighlightedText, Qt.white)
    p.setColor(QtGui.QPalette.ToolTipBase, base)
    p.setColor(QtGui.QPalette.ToolTipText, text)
    p.setColor(QtGui.QPalette.PlaceholderText, MUTED)
    return p


def make_icon(color: QColor) -> QtGui.QIcon:
    pm = QtGui.QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#171b24"))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(0, 0, 64, 64, 14, 14)
    pen = QPen(color, 5, cap=Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(32, 32), 17, 17)
    for a, b in (((32, 5), (32, 17)), ((32, 47), (32, 59)), ((5, 32), (17, 32)), ((47, 32), (59, 32))):
        p.drawLine(QPointF(*a), QPointF(*b))
    p.setBrush(color)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(32, 32), 4, 4)
    p.end()
    return QtGui.QIcon(pm)


def get_path(d, path):
    for k in path.split("."):
        d = d.get(k) if isinstance(d, dict) else None
    return d


def set_path(d, path, value):
    ks = path.split(".")
    for k in ks[:-1]:
        d = d.setdefault(k, {})
    d[ks[-1]] = value


# --------------------------------------------------------------------------
# Definição dos ajustes
# --------------------------------------------------------------------------
F = dict
FIELDS = {
    "Mira": [
        F(p="aim.sensitivity_x", t="range", min=.3, max=3, step=.05, l="Sensibilidade horizontal",
          h="1,00 = arma real: a mira segue exatamente o cano. Acima de 1, um movimento menor cobre a tela."),
        F(p="aim.sensitivity_y", t="range", min=.3, max=3, step=.05, l="Sensibilidade vertical",
          h="Igual à horizontal, para cima/baixo."),
        F(p="aim.offset_x", t="range", min=-.1, max=.1, step=.001, pct=True, l="Ajuste fino horizontal",
          h="Alça de mira: desloca o ponto de impacto se o tiro cai sempre um pouco ao lado."),
        F(p="aim.offset_y", t="range", min=-.1, max=.1, step=.001, pct=True, l="Ajuste fino vertical",
          h="Positivo = mais para baixo."),
        F(p="motion.interp_ms", t="range", min=0, max=50, step=1, l="Suavidade do movimento (ms)",
          h="O Bluetooth entrega as leituras em rajadas e às vezes trava; isto deixa o cursor andar num ritmo "
            "uniforme. Maior = mais liso, porém um pouco mais atrasado. 0 = desligado (o cursor salta)."),
        F(p="motion.output_hz", t="range", min=60, max=1000, step=10, l="Atualização do cursor (Hz)",
          h="Quantas vezes por segundo o cursor é atualizado. 250 é ótimo; suba se o monitor for de 144 Hz+."),
        F(p="motion.max_extrap_ms", t="range", min=0, max=100, step=5, l="Previsão nas travadas (ms)",
          h="Quando o Bluetooth atrasa, continua o movimento por até este tempo em vez de congelar."),
        F(p="smoothing.enabled", t="check", l="Filtro anti-tremor",
          h="Desligue só para comparar: a mira fica crua, com o tremor da mão."),
        F(p="smoothing.min_cutoff", t="range", min=.1, max=5, step=.05, l="Estabilidade parado (Hz)",
          h="Menor = mira mais firme parada, porém mais \"pesada\" em movimentos lentos."),
        F(p="smoothing.beta", t="range", min=0, max=30, step=.5, l="Resposta a movimentos rápidos",
          h="Maior = menos atraso em giros rápidos. Jogos frenéticos: suba. Tiro ao alvo: abaixe."),
        F(p="aim.jitter_lock", t="range", min=0, max=.01, step=.0005, pct=True, l="Trava de micro-movimento",
          h="Ignora movimentos menores que isso. Ajuda em alvos pequenos. 0 = desligado."),
    ],
    "Tiro": [
        F(p="shot.lookback_ms", t="range", min=0, max=100, step=5, l="Compensação do tranco (ms)",
          h="O tiro usa a posição de X ms antes do aperto, para o tranco do dedo não desviar a mira."),
        F(p="shot.freeze_ms", t="range", min=0, max=250, step=10, l="Congelar mira após o tiro (ms)",
          h="Segura o cursor parado logo após atirar."),
        F(p="autofire_hz", t="range", min=2, max=25, step=1, l="Tiro automático (tiros/s)",
          h="Velocidade da ação \"Tiro automático\" (mapeie na aba Botões)."),
        F(p="offscreen_position", t="select", l="Tiro fora da tela vai para",
          h="Onde o cursor vai para \"atirar fora da tela\" (recarregar em vários jogos).",
          o=[([0.0, 0.0], "Canto superior esquerdo"), ([1.0, 0.0], "Canto superior direito"),
             ([0.0, 1.0], "Canto inferior esquerdo"), ([1.0, 1.0], "Canto inferior direito"),
             ([0.5, 1.0], "Meio da borda de baixo")]),
    ],
    "Saída": [
        F(p="output_target", t="select", l="A mira controla",
          h="Só light gun (driver): a área de trabalho ignora a arma; cursor e touchpad ficam livres e o "
            "RetroArch (driver de entrada udev) usa a arma. Mouse do sistema: a arma move o cursor "
            "(funciona com qualquer jogo, inclusive MAME).",
          o=[("lightgun", "Só light gun (driver) — cursor livre"), ("mouse", "Mouse do sistema")]),
        F(p="mouse_yield.enabled", t="check", l="Ceder ao touchpad/mouse",
          h="Modo mouse: se você mexer no touchpad ou no mouse, a arma solta o cursor por alguns segundos "
            "(volta ao atirar)."),
        F(p="mouse_yield.seconds", t="range", min=.5, max=10, step=.5, l="Tempo cedido (s)",
          h="Quanto tempo a arma espera depois do último movimento do touchpad/mouse."),
        F(p="mode", t="select", l="Modo da mira",
          h="Light gun: vai onde o cano aponta (emuladores, jogos de tiro). Mouse giroscópio: move o mouse "
            "comum, para jogos de PC que não aceitam mouse absoluto.",
          o=[("absolute", "Light gun (absoluto)"), ("relative", "Mouse giroscópio (relativo)")]),
        F(p="relative_speed", t="range", min=.1, max=6, step=.1, l="Velocidade no modo mouse",
          h="Só no modo relativo."),
        F(p="region", t="region", l="Área da tela",
          h="Fração da área de trabalho onde a mira atua (x0, y0, x1, y1). Com 2 monitores lado a lado, "
            "o da esquerda é 0 · 0 · 0,5 · 1."),
        F(p="monitor", t="monitor", l="Monitor", h="Número do monitor (0, 1…). -1 = usa a área acima.", win=True),
        F(p="grab", t="check", l="Esconder o controle dos jogos",
          h="O jogo deixa de ver o Joy-Con como gamepad (evita comandos duplicados). Vale ao reconectar.",
          linux=True),
    ],
    "Sensor": [
        F(p="fusion.kp", t="range", min=0, max=2, step=.05, l="Correção pela gravidade",
          h="Quão rápido o acelerômetro corrige a inclinação. Maior = menos deriva vertical, mas sente mais os trancos."),
        F(p="fusion.accel_tolerance_g", t="range", min=.05, max=.6, step=.01, l="Tolerância a trancos (g)",
          h="Acima disso de aceleração, o acelerômetro é ignorado."),
        F(p="auto_bias.enabled", t="check", l="Auto-correção da deriva",
          h="Mede o erro do giroscópio sozinho sempre que o controle fica apoiado parado."),
        F(p="auto_bias.still_range_dps", t="range", min=.5, max=5, step=.1, l="Limite de \"parado\" (°/s)",
          h="Se a deriva não é corrigida com o controle na mesa, aumente um pouco."),
        F(p="screen.width_m", t="range", min=.3, max=4, step=.01, l="Largura da tela (m)", h="Só usado sem calibração."),
        F(p="screen.height_m", t="range", min=.2, max=2.5, step=.01, l="Altura da tela (m)", h="Só usado sem calibração."),
        F(p="screen.distance_m", t="range", min=.3, max=6, step=.05, l="Distância até a tela (m)",
          h="Só usado sem calibração."),
    ],
}


# --------------------------------------------------------------------------
# Widgets
# --------------------------------------------------------------------------
class LivePreview(QtWidgets.QWidget):
    """Mini-tela com a mira ao vivo (verde) e a mira crua sem filtro (cinza)."""

    def __init__(self):
        super().__init__()
        self.pos = (0.5, 0.5)
        self.raw = None
        self.active = False
        self.setMinimumSize(300, 169)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setFixedHeight(190)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        rw = min(w, h * 16 / 9)
        rh = rw * 9 / 16
        r = QRectF((w - rw) / 2, (h - rh) / 2, rw, rh)
        p.setPen(QPen(QColor("#2a3142"), 1))
        p.setBrush(QColor("#0b0e14"))
        p.drawRoundedRect(r, 8, 8)
        p.setPen(QPen(QColor("#1c2230"), 1))
        for i in range(1, 8):
            x = r.left() + r.width() * i / 8
            p.drawLine(QPointF(x, r.top()), QPointF(x, r.bottom()))
        for i in range(1, 6):
            y = r.top() + r.height() * i / 6
            p.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))
        if self.raw:
            rx = r.left() + min(max(self.raw[0], 0), 1) * r.width()
            ry = r.top() + min(max(self.raw[1], 0), 1) * r.height()
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#8b93a7"))
            p.drawEllipse(QPointF(rx, ry), 3, 3)
        c = GREEN if self.active else QColor("#3b4252")
        x = r.left() + self.pos[0] * r.width()
        y = r.top() + self.pos[1] * r.height()
        p.setPen(QPen(c, 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(x, y), 10, 10)
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            p.drawLine(QPointF(x + dx * 4, y + dy * 4), QPointF(x + dx * 17, y + dy * 17))


class Row(QtWidgets.QWidget):
    """Um ajuste: título + explicação à esquerda, controle à direita."""

    changed = QtCore.pyqtSignal(str, object)

    def __init__(self, f: dict, value):
        super().__init__()
        self.f = f
        lay = QtWidgets.QGridLayout(self)
        lay.setContentsMargins(4, 8, 4, 8)
        lay.setHorizontalSpacing(16)
        title = QtWidgets.QLabel(f"<b>{f['l']}</b>")
        help_ = QtWidgets.QLabel(f.get("h", ""))
        help_.setObjectName("help")
        help_.setWordWrap(True)
        left = QtWidgets.QVBoxLayout()
        left.setSpacing(2)
        left.addWidget(title)
        left.addWidget(help_)
        lay.addLayout(left, 0, 0)
        lay.setColumnStretch(0, 5)
        lay.setColumnStretch(1, 4)
        t = f["t"]
        if t == "range":
            self.scale = 1.0 / f["step"]
            self.slider = QtWidgets.QSlider(Qt.Horizontal)
            self.slider.setRange(round(f["min"] * self.scale), round(f["max"] * self.scale))
            self.slider.setValue(round(float(value) * self.scale))
            self.val = QtWidgets.QLabel()
            self.val.setObjectName("value")
            self.val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._show(float(value))
            self.slider.valueChanged.connect(self._slid)
            lay.addWidget(self.slider, 0, 1)
            lay.addWidget(self.val, 0, 2)
        elif t == "check":
            self.box = QtWidgets.QCheckBox("ligado")
            self.box.setChecked(bool(value))
            self.box.toggled.connect(lambda v: self.changed.emit(f["p"], bool(v)))
            lay.addWidget(self.box, 0, 1)
        elif t == "select":
            self.combo = QtWidgets.QComboBox()
            for val, txt in f["o"]:
                self.combo.addItem(txt, val)
                if val == value:
                    self.combo.setCurrentIndex(self.combo.count() - 1)
            self.combo.currentIndexChanged.connect(lambda i: self.changed.emit(f["p"], self.combo.itemData(i)))
            lay.addWidget(self.combo, 0, 1)
        elif t == "region":
            box = QtWidgets.QHBoxLayout()
            self.spins = []
            for i, v in enumerate(value or [0, 0, 1, 1]):
                s = QtWidgets.QDoubleSpinBox()
                s.setRange(0, 1)
                s.setSingleStep(0.05)
                s.setDecimals(3)
                s.setValue(float(v))
                s.valueChanged.connect(self._region)
                self.spins.append(s)
                box.addWidget(s)
            lay.addLayout(box, 0, 1)
        elif t == "monitor":
            self.spin = QtWidgets.QSpinBox()
            self.spin.setRange(-1, 8)
            self.spin.setValue(-1 if value is None else int(value))
            self.spin.valueChanged.connect(lambda v: self.changed.emit(f["p"], None if v < 0 else v))
            lay.addWidget(self.spin, 0, 1)

    def _show(self, v: float) -> None:
        if self.f.get("pct"):
            self.val.setText(f"{v * 100:+.2f}%" if self.f["min"] < 0 else f"{v * 100:.2f}%")
        elif abs(v) >= 10 or self.f["step"] >= 1:
            self.val.setText(f"{v:.0f}")
        else:
            self.val.setText(f"{v:.2f}")

    def _slid(self, iv: int) -> None:
        v = round(iv / self.scale, 6)
        self._show(v)
        self.changed.emit(self.f["p"], v)

    def _region(self) -> None:
        self.changed.emit(self.f["p"], [s.value() for s in self.spins])


class ActionPicker(QtWidgets.QWidget):
    changed = QtCore.pyqtSignal(str)

    def __init__(self, current: str):
        super().__init__()
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.act = QtWidgets.QComboBox()
        for val, txt in ACTIONS.items():
            self.act.addItem(txt, val)
        self.key = QtWidgets.QComboBox()
        for k in KEY_NAMES:
            self.key.addItem(k.upper(), k)
        is_key = (current or "").startswith("key:")
        self.act.setCurrentIndex(self.act.findData("key" if is_key else (current or "")))
        if is_key:
            i = self.key.findData(current[4:])
            self.key.setCurrentIndex(max(0, i))
        self.key.setVisible(is_key)
        lay.addWidget(self.act, 3)
        lay.addWidget(self.key, 1)
        self.act.currentIndexChanged.connect(self._emit)
        self.key.currentIndexChanged.connect(self._emit)

    def _emit(self) -> None:
        a = self.act.currentData()
        self.key.setVisible(a == "key")
        self.changed.emit(f"key:{self.key.currentData()}" if a == "key" else a)


# --------------------------------------------------------------------------
# Janelas de tela cheia
# --------------------------------------------------------------------------
def _target_screen(widget=None) -> QtGui.QScreen:
    return QtWidgets.QApplication.primaryScreen()


class CalibrationWindow(QtWidgets.QWidget):
    """Mostra os 5 alvos; o tiro é capturado pelo núcleo (não clica)."""

    finished = QtCore.pyqtSignal()

    def __init__(self, app: ClientApp):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.app = app
        self.setWindowTitle("Calibração — Light Gun Joypad")
        self.setCursor(Qt.BlankCursor)
        self.done_at = None
        self.state = {}
        self.timer = QtCore.QTimer(self, interval=30, timeout=self._tick)

    def start(self) -> None:
        scr = _target_screen()
        self.setGeometry(scr.geometry())
        self.showFullScreen()
        self.activateWindow()
        self.app.calibrate_start()
        self.timer.start()

    def _tick(self) -> None:
        self.state = self.app.state()
        if self.state["calibrating"] is None:
            last = self.state.get("cal_last")
            if last and last.get("ok"):
                if self.done_at is None:
                    self.done_at = time.monotonic()
                elif time.monotonic() - self.done_at > 2.5:
                    self._close()
            else:
                self._close()
        self.update()

    def _close(self) -> None:
        self.timer.stop()
        self.close()
        self.finished.emit()

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_Escape:
            self.app.calibrate_cancel()
            self._close()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#05070a"))
        cal = self.state.get("calibrating")
        big = QtGui.QFont(self.font())
        big.setPointSize(max(18, H // 40))
        big.setBold(True)
        small = QtGui.QFont(self.font())
        small.setPointSize(max(11, H // 80))
        if cal and cal["target"]:
            x, y = cal["target"][0] * (W - 1), cal["target"][1] * (H - 1)
            for rad, col in ((60, RED), (40, Qt.white), (20, RED)):
                p.setPen(QPen(QColor(col), 4))
                p.drawEllipse(QPointF(x, y), rad, rad)
            p.setPen(QPen(Qt.white, 2))
            p.drawLine(QPointF(x - 85, y), QPointF(x + 85, y))
            p.drawLine(QPointF(x, y - 85), QPointF(x, y + 85))
            p.setPen(QColor("#fde68a"))
            p.setFont(big)
            ty = H * (0.25 if cal["step"] == 0 else 0.4)
            p.drawText(QRectF(W * 0.05, ty - 70, W * 0.9, 90), Qt.AlignHCenter | Qt.AlignBottom | Qt.TextWordWrap,
                       f"Calibração {cal['step'] + 1}/{cal['total']}: mire no {cal['label']} e aperte o gatilho")
            p.setFont(small)
            p.setPen(QColor("#cbd5e1"))
            p.drawText(QRectF(W * 0.05, ty + 26, W * 0.9, 60), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap,
                       cal["message"] or "segure como vai jogar · mire com calma · ESC cancela")
        else:
            last = self.state.get("cal_last") or {}
            if last.get("ok"):
                rms = last["rms"]
                q = "ótimo" if rms < 0.01 else "bom" if rms < 0.03 else "alto — refaça mirando com mais calma"
                p.setFont(big)
                p.setPen(GREEN)
                p.drawText(QRectF(W * 0.05, H * 0.35, W * 0.9, 120), Qt.AlignCenter | Qt.TextWordWrap, f"✓ Calibrado! erro {rms * 100:.2f}% da tela ({q})")


class TestRange(QtWidgets.QWidget):
    """Estande de teste em tela cheia.

    Lê a mira e os tiros direto da arma, então funciona no modo driver (cursor
    livre) e no modo mouse. Sem controle conectado, o mouse faz o papel da arma.
    """

    def __init__(self, app: ClientApp):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Estande de teste — Light Gun Joypad")
        self.app = app
        self.seen_shots = app.gun.shots
        self.setMouseTracking(True)
        self.setCursor(Qt.BlankCursor)
        self.hide_cross = False
        self.mouse = QPointF(-100, -100)
        self.target = None
        self.target_t = 0.0
        self.impacts = []
        self.stats = {"shots": 0, "hits": 0, "err": []}
        self.timer = QtCore.QTimer(self, interval=8, timeout=self._tick)
        self.timer.setTimerType(Qt.PreciseTimer)

    def start(self) -> None:
        self.setGeometry(_target_screen().geometry())
        self.showFullScreen()
        self.activateWindow()
        self._new_target()
        self.timer.start()

    def _new_target(self) -> None:
        r = max(22, self.height() * 0.045)
        self.target = (random.uniform(2 * r, self.width() - 2 * r), random.uniform(2 * r, self.height() - 2 * r), r)
        self.target_t = time.monotonic()

    def _shoot(self, pt: QPointF) -> None:
        self.stats["shots"] += 1
        hit = False
        if self.target:
            d = math.hypot(pt.x() - self.target[0], pt.y() - self.target[1])
            self.stats["err"].append(d)
            hit = d <= self.target[2]
        if hit:
            self.stats["hits"] += 1
            self._new_target()
        self.impacts.append((pt, hit, time.monotonic()))

    def _tick(self) -> None:
        g = self.app.gun
        if self.app.connected:
            rx, ry = g.render_pos()
            self.mouse = QPointF(rx * self.width(), ry * self.height())
            if g.shots != self.seen_shots:
                self.seen_shots = g.shots
                sx, sy = g.last_shot
                self._shoot(QPointF(sx * self.width(), sy * self.height()))
        if time.monotonic() - self.target_t > 4.0:
            self._new_target()
        now = time.monotonic()
        self.impacts = [i for i in self.impacts if now - i[2] < 1.6]
        self.update()

    def mouseMoveEvent(self, ev):
        if not self.app.connected:
            self.mouse = QPointF(ev.pos())

    def mousePressEvent(self, ev):
        # Com o controle conectado os tiros vêm da arma (evita contar 2x no modo mouse).
        if ev.button() == Qt.LeftButton and not self.app.connected:
            self._shoot(QPointF(ev.pos()))

    def keyPressEvent(self, ev):
        k = ev.key()
        if k == Qt.Key_Escape:
            self.timer.stop()
            self.close()
        elif k == Qt.Key_H:
            self.hide_cross = not self.hide_cross
        elif k == Qt.Key_N:
            self.stats = {"shots": 0, "hits": 0, "err": []}

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#0e1118"))
        W, H = self.width(), self.height()
        p.setPen(QPen(QColor("#1c2230"), 1))
        for i in range(1, 8):
            p.drawLine(W * i // 8, 0, W * i // 8, H)
        for i in range(1, 6):
            p.drawLine(0, H * i // 6, W, H * i // 6)
        if self.target:
            x, y, r = self.target
            for k, col in enumerate((RED, Qt.white, RED, Qt.white, RED)):
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(col))
                p.drawEllipse(QPointF(x, y), r * (1 - k * 0.2), r * (1 - k * 0.2))
            frac = min(1.0, (time.monotonic() - self.target_t) / 4.0)
            p.setPen(QPen(AMBER, 3))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(x - r - 7, y - r - 7, 2 * r + 14, 2 * r + 14), 90 * 16, int(360 * 16 * (1 - frac)))
        now = time.monotonic()
        for pt, hit, t in self.impacts:
            age = now - t
            col = QColor(GREEN if hit else AMBER)
            col.setAlphaF(max(0.0, 1 - age / 1.6))
            p.setPen(Qt.NoPen)
            p.setBrush(col)
            p.drawEllipse(pt, 7, 7)
            p.setPen(QPen(col, 2))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(pt, 12 + age * 30, 12 + age * 30)
        if not self.hide_cross:
            m = self.mouse
            p.setPen(QPen(GREEN, 2))
            p.drawEllipse(m, 18, 18)
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                p.drawLine(QPointF(m.x() + dx * 8, m.y() + dy * 8), QPointF(m.x() + dx * 28, m.y() + dy * 28))
        e = self.stats["err"]
        mean = sum(e) / len(e) if e else 0.0
        p.setPen(QColor("#cbd5e1"))
        txt = (f"tiros {self.stats['shots']} · acertos {self.stats['hits']} · erro médio {mean:.1f} px "
               f"({mean / max(W, 1) * 100:.1f}% da largura)" + (" · MIRA ESCONDIDA" if self.hide_cross else "")
               + "      H esconder mira · N zerar · ESC sair")
        p.drawText(16, 28, txt)


# --------------------------------------------------------------------------
# Janela principal
# --------------------------------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app: ClientApp, tray_ok: bool):
        super().__init__()
        self.app = app
        self.tray_ok = tray_ok
        self.quitting = False
        self.work = copy.deepcopy(app.store.effective())
        self.button_rows: dict = {}
        self.cal_win = None
        self.test_win = None
        self.setWindowTitle("Light Gun Joypad")
        self.setWindowIcon(make_icon(GREEN))
        self.resize(1180, 760)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(14, 10, 14, 14)

        # topo
        top = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("<span style='font-size:15pt;font-weight:700'>Light Gun "
                                 "<span style='color:#4ade80'>Joypad</span></span>")
        self.status = QtWidgets.QLabel()
        self.rate = QtWidgets.QLabel()
        self.rate.setObjectName("help")
        self.profile_combo = QtWidgets.QComboBox()
        self.profile_combo.setMinimumWidth(220)
        self.profile_combo.activated.connect(lambda i: self._select_profile(self.profile_combo.itemText(i)))
        self.saved = QtWidgets.QLabel("")
        self.saved.setStyleSheet("color:#4ade80")
        top.addWidget(title)
        top.addSpacing(18)
        top.addWidget(self.status)
        top.addSpacing(10)
        top.addWidget(self.rate)
        top.addStretch(1)
        self.t_driver = QtWidgets.QPushButton("🎯  Só light gun (driver)")
        self.t_mouse = QtWidgets.QPushButton("🖱  Mouse do sistema")
        self.t_driver.setToolTip("A área de trabalho ignora a arma: cursor e touchpad livres. "
                                 "Use no RetroArch (driver de entrada udev).")
        self.t_mouse.setToolTip("A arma move o cursor do sistema. Funciona com qualquer jogo. "
                                "Mexer no touchpad faz a arma ceder o cursor por alguns segundos.")
        grp = QtWidgets.QButtonGroup(self)
        for b, val in ((self.t_driver, "lightgun"), (self.t_mouse, "mouse")):
            b.setCheckable(True)
            b.setObjectName("seg")
            b.setMinimumWidth(b.fontMetrics().horizontalAdvance(b.text()) + 60)
            grp.addButton(b)
            b.clicked.connect(lambda _=False, v=val: self._set_target(v))
            top.addWidget(b)
        if not sys.platform.startswith("linux"):
            self.t_driver.setEnabled(False)
            self.t_driver.setToolTip("Só no Linux (no Windows precisaria de driver de kernel).")
        top.addSpacing(14)
        top.addWidget(self.saved)
        top.addWidget(QtWidgets.QLabel("Perfil:"))
        top.addWidget(self.profile_combo)
        root.addLayout(top)

        body = QtWidgets.QHBoxLayout()
        root.addLayout(body, 1)

        # coluna ao vivo
        live = QtWidgets.QGroupBox("Ao vivo")
        live.setFixedWidth(420)
        lv = QtWidgets.QVBoxLayout(live)
        self.preview = LivePreview()
        lv.addWidget(self.preview)
        self.chips = QtWidgets.QLabel(" ")
        self.chips.setMinimumHeight(26)
        lv.addWidget(self.chips)
        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        self.i_dev, self.i_bias, self.i_cal, self.i_out, self.i_mode = (QtWidgets.QLabel() for _ in range(5))
        for lbl in (self.i_dev, self.i_bias, self.i_cal, self.i_out, self.i_mode):
            lbl.setWordWrap(True)
        for name, w in (("Controle", self.i_dev), ("Giroscópio", self.i_bias), ("Calibração", self.i_cal),
                        ("Saída", self.i_out), ("Modo", self.i_mode)):
            k = QtWidgets.QLabel(name)
            k.setObjectName("help")
            form.addRow(k, w)
        lv.addLayout(form)
        grid = QtWidgets.QGridLayout()
        self.b_cal = QtWidgets.QPushButton("🎯  Calibrar")
        self.b_cal.setObjectName("primary")
        self.b_test = QtWidgets.QPushButton("🔫  Estande de teste")
        self.b_rec = QtWidgets.QPushButton("⊕  Recentrar")
        self.b_pause = QtWidgets.QPushButton("⏸  Pausar mira")
        self.b_recon = QtWidgets.QPushButton("↻  Reconectar")
        self.b_bias = QtWidgets.QPushButton("⟲  Medir giroscópio")
        self.b_calreset = QtWidgets.QPushButton("Apagar calibração")
        self.b_quit = QtWidgets.QPushButton("⏻  Encerrar")
        btns = [self.b_cal, self.b_test, self.b_rec, self.b_pause, self.b_recon, self.b_bias, self.b_calreset, self.b_quit]
        for i, b in enumerate(btns):
            grid.addWidget(b, i // 2, i % 2)
        lv.addLayout(grid)
        tip = QtWidgets.QLabel("<b>Só light gun (driver)</b>: o cursor e o touchpad ficam livres; o RetroArch "
                               "(driver de entrada <i>udev</i>) usa a arma. <b>Mouse do sistema</b>: a arma move o "
                               "cursor; mexer no touchpad faz ela ceder por alguns segundos. <b>HOME</b> no controle "
                               "pausa a mira. Recentrar: aponte para o <b>centro</b> da tela e aperte <b>Y</b>.")
        tip.setObjectName("help")
        tip.setWordWrap(True)
        lv.addWidget(tip)
        lv.addStretch(1)
        body.addWidget(live)

        self.tabs = QtWidgets.QTabWidget()
        body.addWidget(self.tabs, 1)
        self._build_tabs()

        self.b_cal.clicked.connect(self.open_calibration)
        self.b_test.clicked.connect(self.open_test)
        self.b_rec.clicked.connect(self.app.gun.recenter)
        self.b_pause.clicked.connect(self.toggle_pause)
        self.b_recon.clicked.connect(self.app.reconnect)
        self.b_bias.clicked.connect(self.app.reset_bias)
        self.b_calreset.clicked.connect(self._cal_reset)
        self.b_quit.clicked.connect(self.quit_app)

        self.save_timer = QtCore.QTimer(self, singleShot=True, interval=250, timeout=self._save)
        self.live_timer = QtCore.QTimer(self, interval=16, timeout=self._live)
        self.live_timer.start()
        self._fill_profiles()

    # ---- abas -------------------------------------------------------------
    def _scroll(self, inner: QtWidgets.QWidget) -> QtWidgets.QScrollArea:
        sa = QtWidgets.QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(inner)
        return sa

    def _build_tabs(self) -> None:
        cur = self.tabs.currentIndex()
        self.tabs.clear()
        self.button_rows = {}
        plat = sys.platform
        for tab, fields in FIELDS.items():
            w = QtWidgets.QWidget()
            v = QtWidgets.QVBoxLayout(w)
            if tab == "Mira":
                hint = QtWidgets.QLabel("Dica: deixe as sensibilidades em 1,00 para a mira ser fiel ao cano, como "
                                        "uma light gun de verdade. Mude só se o jogo pedir.")
                hint.setObjectName("help")
                hint.setWordWrap(True)
                v.addWidget(hint)
            for f in fields:
                if f.get("win") and plat != "win32":
                    continue
                if f.get("linux") and not plat.startswith("linux"):
                    continue
                row = Row(f, get_path(self.work, f["p"]))
                row.changed.connect(self._changed)
                v.addWidget(row)
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.HLine)
                line.setStyleSheet("color:#2a3142")
                v.addWidget(line)
            if tab == "Saída":
                n = QtWidgets.QLabel("<b>Emuladores:</b> RetroArch → Entrada → Tipo de dispositivo <i>Light Gun</i>; "
                                     "MAME → <code>-lightgun -lightgun_device mouse</code>. Jogos de PC sem suporte a "
                                     "mouse absoluto → modo <i>Mouse giroscópio</i>.")
                n.setWordWrap(True)
                n.setObjectName("help")
                v.addWidget(n)
            v.addStretch(1)
            self.tabs.addTab(self._scroll(w), tab)
        self.tabs.insertTab(2, self._scroll(self._buttons_tab()), "Botões")
        self.tabs.addTab(self._scroll(self._profiles_tab()), "Perfis")
        if cur >= 0:
            self.tabs.setCurrentIndex(cur)

    def _buttons_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        hint = QtWidgets.QLabel("Aperte um botão no controle: o nome dele acende. As mudanças valem na hora.")
        hint.setObjectName("help")
        v.addWidget(hint)
        self.btn_grid = QtWidgets.QGridLayout()
        self.btn_grid.setColumnStretch(1, 1)
        v.addLayout(self.btn_grid)
        names = list(BUTTON_NAMES) + [n for n in self.work["buttons"] if n not in BUTTON_NAMES]
        for n in names:
            self._add_button_row(n)
        v.addStretch(1)
        n = QtWidgets.QLabel("Um botão fora da lista (nome cru do Linux, ex.: BTN_TR2) aparece aqui sozinho quando "
                             "você o aperta.")
        n.setObjectName("help")
        n.setWordWrap(True)
        v.addWidget(n)
        return w

    def _add_button_row(self, name: str) -> None:
        r = self.btn_grid.rowCount()
        lab = QtWidgets.QLabel(name)
        lab.setObjectName("bname")
        lab.setAlignment(Qt.AlignCenter)
        lab.setMinimumWidth(90)
        picker = ActionPicker(self.work["buttons"].get(name, ""))

        def changed(a, n=name):
            b = dict(self.work["buttons"])
            if a:
                b[n] = a
            else:
                b.pop(n, None)
            self._changed("buttons", b)

        picker.changed.connect(changed)
        self.btn_grid.addWidget(lab, r, 0)
        self.btn_grid.addWidget(picker, r, 1)
        self.button_rows[name] = lab

    def _profiles_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        hint = QtWidgets.QLabel("Um perfil por jogo ou emulador. O perfil ativo vale na hora; também dá para trocar "
                                "pelo seletor no topo ou pelo ícone da bandeja.")
        hint.setObjectName("help")
        hint.setWordWrap(True)
        v.addWidget(hint)
        store = self.app.store
        for name in list(store.profiles):
            row = QtWidgets.QHBoxLayout()
            act = name == store.active
            lab = QtWidgets.QLabel(f"<b>{name}</b>" + ("  <span style='color:#4ade80'>(ativo)</span>" if act else ""))
            row.addWidget(lab, 1)
            if not act:
                b = QtWidgets.QPushButton("Usar")
                b.clicked.connect(lambda _=False, n=name: self._select_profile(n))
                row.addWidget(b)
            for txt, fn in (("Duplicar", self._dup), ("Renomear", self._ren), ("Apagar", self._del)):
                b = QtWidgets.QPushButton(txt)
                b.clicked.connect(lambda _=False, n=name, f=fn: f(n))
                row.addWidget(b)
            fr = QtWidgets.QFrame()
            fr.setLayout(row)
            fr.setStyleSheet("QFrame{border:1px solid %s;border-radius:8px}" % ("#4ade80" if act else "#2a3142")
                             + " QLabel{border:none}")
            v.addWidget(fr)
        v.addSpacing(16)
        v.addWidget(QtWidgets.QLabel("<b>Novo perfil</b>"))
        row = QtWidgets.QHBoxLayout()
        self.new_name = QtWidgets.QLineEdit()
        self.new_name.setPlaceholderText("Nome do jogo")
        self.new_base = QtWidgets.QComboBox()
        self.new_base.addItems(list(PRESETS))
        b = QtWidgets.QPushButton("Criar")
        b.setObjectName("primary")
        b.clicked.connect(self._create)
        row.addWidget(self.new_name, 2)
        row.addWidget(QtWidgets.QLabel("a partir de"))
        row.addWidget(self.new_base, 2)
        row.addWidget(b)
        v.addLayout(row)
        p = QtWidgets.QLabel(f"Arquivo: {store.path}")
        p.setObjectName("help")
        p.setTextInteractionFlags(Qt.TextSelectableByMouse)
        v.addWidget(p)
        v.addStretch(1)
        return w

    # ---- perfis ------------------------------------------------------------
    def _fill_profiles(self) -> None:
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(list(self.app.store.profiles))
        self.profile_combo.setCurrentText(self.app.store.active)
        self.profile_combo.blockSignals(False)
        tray = getattr(self, "tray", None)
        if tray is not None:
            tray.rebuild_profiles()

    def _reload(self) -> None:
        self.work = copy.deepcopy(self.app.store.effective())
        self._fill_profiles()
        self._build_tabs()

    def _select_profile(self, name: str) -> None:
        self._flush()
        self.app.select_profile(name)
        self._reload()

    def _err(self, exc) -> None:
        QtWidgets.QMessageBox.warning(self, "Light Gun Joypad", str(exc))

    def _dup(self, name):
        new, ok = QtWidgets.QInputDialog.getText(self, "Duplicar perfil", "Nome da cópia:", text=f"{name} (cópia)")
        if ok and new.strip():
            try:
                self.app.store.create(new.strip(), name)
                self.app.store.save()
                self._reload()
            except ValueError as exc:
                self._err(exc)

    def _ren(self, name):
        new, ok = QtWidgets.QInputDialog.getText(self, "Renomear perfil", "Novo nome:", text=name)
        if ok and new.strip() and new.strip() != name:
            try:
                self.app.store.rename(name, new.strip())
                self.app.store.save()
                self._reload()
            except ValueError as exc:
                self._err(exc)

    def _del(self, name):
        if QtWidgets.QMessageBox.question(self, "Apagar perfil", f"Apagar o perfil \"{name}\"?") != QtWidgets.QMessageBox.Yes:
            return
        try:
            self.app.store.delete(name)
            self.app.store.save()
            self.app.apply_active()
            self._reload()
        except ValueError as exc:
            self._err(exc)

    def _create(self):
        name = self.new_name.text().strip()
        if not name:
            self.new_name.setFocus()
            return
        try:
            self.app.store.create(name, self.new_base.currentText())
            self.app.select_profile(name)
            self._reload()
        except ValueError as exc:
            self._err(exc)

    # ---- salvar ------------------------------------------------------------
    def _changed(self, path: str, value) -> None:
        set_path(self.work, path, value)
        self.save_timer.start()

    def _flush(self) -> None:
        if self.save_timer.isActive():
            self.save_timer.stop()
            self._save()

    def _save(self) -> None:
        self.app.save_profile(self.app.store.active, copy.deepcopy(self.work))
        self.saved.setText("✓ salvo")
        QtCore.QTimer.singleShot(1200, lambda: self.saved.setText(""))

    # ---- ações -------------------------------------------------------------
    def _set_target(self, value: str) -> None:
        if self.work.get("output_target") == value:
            return
        self.work["output_target"] = value
        self._flush()
        self._save()
        self._build_tabs()

    def _check_yield(self, s: dict) -> None:
        """Modo mouse: detecta o touchpad/mouse real mexendo o cursor e faz a arma ceder."""
        g = self.app.gun
        cfg = g.cfg
        y = cfg.get("mouse_yield", {})
        if (cfg.get("output_target") != "mouse" or not y.get("enabled", True) or g.mode != "absolute"
                or not s["connected"] or g.paused):
            self._prev_cur = None
            return
        cur = QtGui.QCursor.pos()
        out = g._last_out
        now = time.monotonic()
        prev = getattr(self, "_prev_cur", None)
        if prev is not None:
            dx, dy = cur.x() - prev.x(), cur.y() - prev.y()
            if now < g.yield_until:
                if abs(dx) + abs(dy) > 2:  # ainda mexendo no touchpad
                    g.yield_until = now + float(y.get("seconds", 2.5))
            else:
                ex = ey = 0.0
                po = getattr(self, "_prev_out", None)
                if out and po:
                    vg = QtWidgets.QApplication.primaryScreen().virtualGeometry()
                    r = cfg.get("region") or [0, 0, 1, 1]
                    ex = (out[0] - po[0]) * (r[2] - r[0]) * vg.width()
                    ey = (out[1] - po[1]) * (r[3] - r[1]) * vg.height()
                if math.hypot(dx - ex, dy - ey) > 12 + 0.5 * math.hypot(ex, ey):
                    g.yield_until = now + float(y.get("seconds", 2.5))
        self._prev_cur = cur
        self._prev_out = out

    def toggle_pause(self) -> None:
        self.app.gun.paused = not self.app.gun.paused

    def _cal_reset(self) -> None:
        if QtWidgets.QMessageBox.question(self, "Calibração", "Apagar a calibração salva?") == QtWidgets.QMessageBox.Yes:
            self.app.calibration_reset()

    def open_calibration(self) -> None:
        self.cal_win = CalibrationWindow(self.app)
        self.cal_win.start()

    def open_test(self) -> None:
        self.test_win = TestRange(self.app)
        self.test_win.start()

    # ---- ao vivo -----------------------------------------------------------
    def _live(self) -> None:
        s = self.app.state()
        self._check_yield(s)
        tray = getattr(self, "tray", None)
        if tray is not None:
            tray.update_state(s)
        if not self.isVisible():
            return
        if s["connected"]:
            col, txt = (GREEN if s["bias_ok"] else AMBER), ("mira pausada" if s["paused"] else
                                                            "cedendo ao touchpad" if s["yielding"] else "light gun ativa")
        else:
            col, txt = RED, s["status"]
        self.status.setText(f"<span style='color:{col.name()}'>●</span> {txt}")
        self.rate.setText(f"IMU {s['rate']}/s")
        self.preview.pos = self.app.gun.render_pos() if s["connected"] else s["pos"]
        self.preview.raw = s["raw"]
        self.preview.active = s["connected"] and not s["paused"]
        self.preview.update()
        logical = [n for n in s["pressed"] if not n.startswith(("BTN_", "KEY_", "CODE_"))]
        shown = logical or s["pressed"]
        self.chips.setText(" ".join(f"<span style='background:#1d4ed8;color:white;font-weight:600'>&nbsp;{n}&nbsp;</span>"
                                    for n in shown) or " ")
        self.i_dev.setText(s["device"] or "—")
        self.i_bias.setText(("ok (" + ", ".join(f"{b:.2f}" for b in s["bias"]) + " °/s)") if s["bias_ok"]
                            else "<span style='color:#fbbf24'>apoie o controle parado ~1 s</span>")
        c = s["calibration"]
        self.i_cal.setText(f"ok · erro {c['rms'] * 100:.2f}%" if c["loaded"]
                           else "<span style='color:#fbbf24'>não calibrado (usando tamanho da tela)</span>")
        o = s["output"]
        self.i_out.setText(o["name"] + (f"<br><span style='color:#f87171'>{o['error']}</span>" if o["error"] else ""))
        self.i_mode.setText("mouse giroscópio" if s["mode"] == "relative" else "light gun (absoluto)")
        self.t_driver.setChecked(s["target"] == "lightgun")
        self.t_mouse.setChecked(s["target"] != "lightgun")
        self.b_pause.setText("▶  Retomar mira" if s["paused"] else "⏸  Pausar mira")
        pressed = set(s["pressed"])
        for n, lab in self.button_rows.items():
            on = "true" if n in pressed else "false"
            if lab.property("on") != on:
                lab.setProperty("on", on)
                lab.style().unpolish(lab)
                lab.style().polish(lab)
        if not logical:
            for n in s["pressed"]:
                if n.startswith(("BTN_", "KEY_")) and n not in self.button_rows:
                    self._add_button_row(n)
        if s["profile"] != self.profile_combo.currentText():
            self._reload()

    # ---- janela/bandeja ----------------------------------------------------
    def show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, ev):
        self._flush()
        if self.tray_ok and not self.quitting:
            ev.ignore()
            self.hide()
            if not getattr(self, "_told", False):
                self._told = True
                self.tray.showMessage("Light Gun Joypad", "Continua rodando aqui na bandeja. "
                                      "Clique no ícone para abrir; botão direito para sair.", make_icon(GREEN), 4000)
        else:
            self.quit_app()

    def quit_app(self) -> None:
        self._flush()
        self.quitting = True
        QtWidgets.QApplication.quit()


class Tray(QtWidgets.QSystemTrayIcon):
    def __init__(self, win: MainWindow):
        super().__init__(make_icon(MUTED))
        self.win = win
        self.app = win.app
        self.setToolTip("Light Gun Joypad")
        m = QtWidgets.QMenu()
        m.addAction("Abrir painel", win.show_window)
        self.a_pause = m.addAction("Pausar mira", win.toggle_pause)
        m.addAction("Recentrar (mire no centro)", self.app.gun.recenter)
        m.addAction("Calibrar…", win.open_calibration)
        m.addAction("Estande de teste…", win.open_test)
        self.profiles_menu = m.addMenu("Perfil")
        m.addSeparator()
        m.addAction("Encerrar", win.quit_app)
        self.setContextMenu(m)
        self.menu = m
        self.activated.connect(self._activated)
        self._last = None
        self.rebuild_profiles()

    def rebuild_profiles(self) -> None:
        self.profiles_menu.clear()
        group = QtWidgets.QActionGroup(self.profiles_menu)
        for name in self.app.store.profiles:
            a = self.profiles_menu.addAction(name)
            a.setCheckable(True)
            a.setChecked(name == self.app.store.active)
            group.addAction(a)
            a.triggered.connect(lambda _=False, n=name: self.win._select_profile(n))

    def _activated(self, reason) -> None:
        if reason in (QtWidgets.QSystemTrayIcon.Trigger, QtWidgets.QSystemTrayIcon.DoubleClick):
            if self.win.isVisible() and not self.win.isMinimized():
                self.win.hide()
            else:
                self.win.show_window()

    def update_state(self, s: dict) -> None:
        key = (s["connected"], s["paused"], s["bias_ok"])
        if key == self._last:
            return
        prev = self._last
        self._last = key
        col = MUTED if not s["connected"] else (AMBER if s["paused"] or not s["bias_ok"] else GREEN)
        self.setIcon(make_icon(col))
        tip = "Light Gun Joypad — " + (("pausada" if s["paused"] else "ativa") if s["connected"] else "sem controle")
        self.setToolTip(tip)
        self.a_pause.setText("Retomar mira" if s["paused"] else "Pausar mira")
        if prev is not None and prev[0] != s["connected"]:
            self.showMessage("Light Gun Joypad", ("Controle conectado: " + s["device"]) if s["connected"]
                             else "Controle desconectado", make_icon(col), 2500)


# --------------------------------------------------------------------------
def _already_running() -> bool:
    sock = QLocalSocket()
    sock.connectToServer(APP_ID)
    if sock.waitForConnected(300):
        sock.write(b"show")
        sock.flush()
        sock.waitForBytesWritten(300)
        sock.disconnectFromServer()
        return True
    return False


def run_gui(config_path=None, calib_path=None, start_hidden: bool = False) -> int:
    QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    qapp = QtWidgets.QApplication(sys.argv[:1])
    qapp.setApplicationName("Light Gun Joypad")
    qapp.setApplicationVersion(__version__)
    qapp.setQuitOnLastWindowClosed(False)
    if _already_running():
        return 0
    QLocalServer.removeServer(APP_ID)  # restos de uma execução que caiu
    server = QLocalServer()
    server.listen(APP_ID)

    redirect_output_to_log()
    qapp.setStyle("Fusion")
    qapp.setPalette(dark_palette())
    qapp.setStyleSheet(STYLE)
    qapp.setWindowIcon(make_icon(GREEN))

    store = ConfigStore(config_path)
    if not store.path.exists():
        store.save()
    core = ClientApp(store, calib_path)
    core.start()

    tray_ok = QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()
    win = MainWindow(core, tray_ok)
    if tray_ok:
        win.tray = Tray(win)
        win.tray.show()
    else:
        win.tray = None

    def on_conn():
        c = server.nextPendingConnection()
        if c is not None:
            c.readyRead.connect(lambda c=c: (c.readAll(), win.show_window()))

    server.newConnection.connect(on_conn)
    if not (start_hidden and tray_ok):
        win.show_window()
    print(f"light gun ativa (janela{'+ bandeja' if tray_ok else ''})", flush=True)
    try:
        rc = qapp.exec_()
    finally:
        core.shutdown()
        server.close()
    return rc
