"""Definição dos ajustes mostrados no aplicativo (sem Qt; textos em inglês)."""
from __future__ import annotations

from .inputs import SOURCES

F = dict
# Textos em inglês; Row/ActionPicker traduzem com tr() ao montar a tela.
FIELDS = {
    "Controller": [
        F(p="input_source", t="select", l="Aim source",
          h="Joy-Con/Pro Controller (the most precise), DualSense, DualShock 4, others with a gyroscope "
            "(Steam Deck/Controller, 8BitDo…) or the system mouse for those without a controller. "
            "Regular Xbox controllers have no gyroscope: use the mouse.",
          o=list(SOURCES.items())),
        F(p="rumble.enabled", t="check", l="Recoil (rumble on each shot)",
          h="Vibrates the controller on every shot, like a gun's recoil. Joy-Con, Pro, DualSense and DS4."),
        F(p="rumble.ms", t="range", min=10, max=200, step=5, l="Recoil duration (ms)", h="Longer = heavier recoil."),
        F(p="rumble.strength", t="range", min=.1, max=1, step=.05, l="Recoil strength", h="Vibration intensity."),
        F(p="reload.offscreen_aim", t="check", l="Reload by aiming off-screen",
          h="Like a real light gun: point outside the screen and pull the trigger to reload."),
        F(p="reload.offscreen_margin", t="range", min=0, max=.2, step=.005, pct=True, l="Off-screen margin",
          h="How far past the edge counts as outside. Increase it if you reload by accident near the edges."),
        F(p="reload.shake", t="check", l="Reload with a jerk",
          h="A strong jerk of the gun (downwards, like pumping a shotgun) fires an off-screen shot."),
        F(p="reload.shake_g", t="range", min=1.5, max=6, step=.1, l="Jerk strength (g)",
          h="Lower = reloads with less force. If it reloads by itself when aiming fast, increase it."),
    ],
    "Aim": [
        F(p="aim.sensitivity_x", t="range", min=.3, max=3, step=.05, l="Horizontal sensitivity",
          h="1.00 = real gun: the aim follows the barrel exactly. Above 1, a smaller movement covers the screen."),
        F(p="aim.sensitivity_y", t="range", min=.3, max=3, step=.05, l="Vertical sensitivity",
          h="Same as horizontal, for up/down."),
        F(p="aim.offset_x", t="range", min=-.1, max=.1, step=.001, pct=True, l="Horizontal fine adjustment",
          h="Gun sight: shifts the point of impact if shots always land slightly to one side."),
        F(p="aim.offset_y", t="range", min=-.1, max=.1, step=.001, pct=True, l="Vertical fine adjustment",
          h="Positive = lower."),
        F(p="motion.interp_ms", t="range", min=0, max=50, step=1, l="Motion smoothness (ms)",
          h="Bluetooth delivers readings in bursts and sometimes stalls; this keeps the cursor moving at a steady "
            "pace. Higher = smoother but slightly more delayed. 0 = off (the cursor jumps)."),
        F(p="motion.output_hz", t="range", min=60, max=1000, step=10, l="Cursor update rate (Hz)",
          h="How many times per second the cursor is updated. 250 is great; raise it for 144 Hz+ monitors."),
        F(p="motion.max_extrap_ms", t="range", min=0, max=100, step=5, l="Prediction during stalls (ms)",
          h="When Bluetooth lags, keeps the movement going for up to this long instead of freezing."),
        F(p="smoothing.enabled", t="check", l="Anti-tremor filter",
          h="Turn it off only to compare: the aim becomes raw, with your hand's tremor."),
        F(p="smoothing.min_cutoff", t="range", min=.1, max=5, step=.05, l="Stability when still (Hz)",
          h="Lower = steadier aim when still, but \"heavier\" in slow movements."),
        F(p="smoothing.beta", t="range", min=0, max=30, step=.5, l="Response to fast movements",
          h="Higher = less lag on fast turns. Frantic games: raise it. Target shooting: lower it."),
        F(p="aim.jitter_lock", t="range", min=0, max=.01, step=.0005, pct=True, l="Micro-movement lock",
          h="Ignores movements smaller than this. Helps with small targets. 0 = off."),
    ],
    "Shooting": [
        F(p="shot.lookback_ms", t="range", min=0, max=100, step=5, l="Trigger jerk compensation (ms)",
          h="The shot uses the position from X ms before the press, so the finger's jerk doesn't throw off the aim."),
        F(p="shot.freeze_ms", t="range", min=0, max=250, step=10, l="Freeze aim after the shot (ms)",
          h="Holds the cursor still right after shooting."),
        F(p="autofire_hz", t="range", min=2, max=25, step=1, l="Auto-fire (shots/s)",
          h="Speed of the \"Auto-fire\" action (map it in the Buttons tab)."),
        F(p="offscreen_position", t="select", l="Off-screen shot goes to",
          h="Where the cursor goes to \"shoot off-screen\" (reload in many games).",
          o=[([0.0, 0.0], "Top-left corner"), ([1.0, 0.0], "Top-right corner"),
             ([0.0, 1.0], "Bottom-left corner"), ([1.0, 1.0], "Bottom-right corner"),
             ([0.5, 1.0], "Middle of the bottom edge")]),
    ],
    "Output": [
        F(p="output_target", t="select", l="The aim controls",
          h="Light gun only (driver): the desktop ignores the gun; cursor and touchpad stay free and RetroArch "
            "(udev input driver) uses the gun. System mouse: the gun moves the cursor (works with any game, "
            "including MAME).",
          o=[("lightgun", "Light gun only (driver) — cursor free"), ("mouse", "System mouse")]),
        F(p="overlay.enabled", t="check", l="Show crosshair on screen",
          h="Draws a crosshair on top of everything, where the gun points. Useful in driver mode for games that "
            "don't show one (shortcut: top button or the \"Show/hide on-screen crosshair\" action)."),
        F(p="overlay.size", t="range", min=16, max=96, step=2, l="On-screen crosshair size (px)", h=""),
        F(p="mouse_yield.enabled", t="check", l="Yield to touchpad/mouse",
          h="Mouse mode: if you move the touchpad or mouse, the gun releases the cursor for a few seconds "
            "(it comes back when you shoot)."),
        F(p="mouse_yield.seconds", t="range", min=.5, max=10, step=.5, l="Yield time (s)",
          h="How long the gun waits after the last touchpad/mouse movement."),
        F(p="mode", t="select", l="Aim mode",
          h="Light gun: goes where the barrel points (emulators, shooting games). Gyro mouse: moves the regular "
            "mouse, for PC games that don't accept an absolute mouse.",
          o=[("absolute", "Light gun (absolute)"), ("relative", "Gyro mouse (relative)")]),
        F(p="relative_speed", t="range", min=.1, max=6, step=.1, l="Gyro mouse speed",
          h="Relative mode only."),
        F(p="region", t="region", l="Screen area",
          h="Fraction of the desktop where the aim works (x0, y0, x1, y1). With 2 monitors side by side, "
            "the left one is 0 · 0 · 0.5 · 1."),
        F(p="monitor", t="monitor", l="Monitor", h="Monitor number (0, 1…). -1 = use the area above.", nolinux=True),
        F(p="grab", t="check", l="Hide the controller from games",
          h="Games stop seeing the controller as a gamepad (avoids duplicate commands). Applies on reconnect.",
          linux=True),
    ],
    "Sensor": [
        F(p="fusion.kp", t="range", min=0, max=2, step=.05, l="Gravity correction",
          h="How fast the accelerometer corrects the tilt. Higher = less vertical drift, but feels jerks more."),
        F(p="fusion.accel_tolerance_g", t="range", min=.05, max=.6, step=.01, l="Jerk tolerance (g)",
          h="Above this acceleration, the accelerometer is ignored."),
        F(p="auto_bias.enabled", t="check", l="Automatic drift correction",
          h="Measures the gyroscope error by itself whenever the controller rests still."),
        F(p="auto_bias.still_range_dps", t="range", min=.5, max=5, step=.1, l="\"Still\" threshold (°/s)",
          h="If drift isn't corrected with the controller on the table, increase it a little."),
        F(p="screen.width_m", t="range", min=.3, max=4, step=.01, l="Screen width (m)", h="Only used without calibration."),
        F(p="screen.height_m", t="range", min=.2, max=2.5, step=.01, l="Screen height (m)", h="Only used without calibration."),
        F(p="screen.distance_m", t="range", min=.3, max=6, step=.05, l="Distance to the screen (m)",
          h="Only used without calibration."),
    ],
}
TAB_TITLES = ["Controller", "Aim", "Buttons", "Shooting", "Output", "Sensor", "Profiles", "Help"]
CAL_LABELS = ["CENTER of the screen", "TOP-LEFT corner", "TOP-RIGHT corner", "BOTTOM-RIGHT corner",
              "BOTTOM-LEFT corner"]
