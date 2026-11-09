# Capybara Lightgun

**English** · [Português (Brasil)](README.pt-BR.md)

Capybara Lightgun turns **any device with a gyroscope** into an **absolute
pointer**, a light gun that aims where you physically point. It runs on
**Linux**, **Windows** and **macOS** (experimental), and it can also use the
**system mouse** when no gyroscope device is available.

> **Gyroscope first, device-agnostic.** The project is about the gyroscope
> as a sensor, not about any brand or product. It reads angular velocity and
> acceleration from whatever device exposes them through the operating system
> (game controllers today, other IMU devices tomorrow) and turns them into a
> calibrated, physically accurate aim. Device names in this document only say
> what is known to work. They are not a preference or an endorsement.

> 🤖 **Generated with Claude.** This project (code, tests, installers,
> documentation and translations) was **generated with the AI assistant
> Claude, by Anthropic**, under the direction of the project author, who
> tested and published it. AI-generated software can contain errors: review
> it before relying on it. Anthropic is not affiliated with this project.

> ⚖️ **Use at your own risk.** The software is provided **as is, without any
> warranty**. **Whoever uses, modifies or distributes it is solely responsible
> for that use.** The author does not control and is not responsible for how
> third parties use it. Read the full [legal notice](DISCLAIMER.md).

**Documentation:** [Installation guide (Linux · Windows · macOS)](docs/INSTALL.md) ·
[Legal notice](DISCLAIMER.md) · [License](LICENSE) ·
[Guia completo em português](docs/GUIA-pt-BR.md)

---

## Contents

- [Why this project exists](#why-this-project-exists)
- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Supported inputs, outputs and platforms](#supported-inputs-outputs-and-platforms)
- [Installation](#installation)
- [Using the app](#using-the-app)
- [For developers: a gyroscope test bench](#for-developers-a-gyroscope-test-bench)
- [Project layout and tests](#project-layout-and-tests)
- [Translations](#translations)
- [License (MIT): what it means](#license-mit-what-it-means)
- [Disclaimer and legal notices](#disclaimer-and-legal-notices) · full text: [DISCLAIMER.md](DISCLAIMER.md)

---

## Why this project exists

Capybara Lightgun is a **personal, educational, non-profit project**. It was
created to:

1. **Help developers test gyroscope features quickly.** If you are building an
   app, game, emulator, accessibility tool or research prototype that uses
   motion or gyro aiming, you can use this project as a ready-made test bench.
   It reads real IMU data, fuses it into an orientation, maps it to the screen
   and delivers it as standard mouse or pointer events that your application
   already understands, so you don't have to write a driver first.
2. **Make light-gun-style aiming accessible** with hardware people already
   own, on modern displays where classic CRT light guns no longer work.
3. **Share the techniques openly** (sensor fusion, calibration through a
   projective transform, low-latency smoothing) so others can learn from them
   and improve them.

It is **not** meant to make money, compete with any product, or harm anyone.
That is why it is released under the permissive **MIT License** (see below).

## What it does

- **Absolute aiming:** the cursor goes exactly where the device points, like a
  real light gun, not like a relative "gyro mouse". Rolling the wrist does not
  move the aim.
- **Calibration:** aim at the screen center and the 4 corners. The mapping is
  a homography, so the aim stays correct even if you are off-axis or the
  screen is tilted.
- **Smooth, low-latency motion:** the cursor updates at a fixed rate (250 Hz
  by default), interpolated on the sensor's own clock. This hides Bluetooth
  bursts and stalls. An adaptive "One Euro" filter removes hand tremor without
  adding lag to fast movements.
- **Shot stabilization:** the shot uses the aim position from a few
  milliseconds before the trigger press, so the finger's jerk doesn't move it.
- **Drift handling:** the gyroscope bias is re-estimated whenever the device
  rests still, and a one-button recenter is available.
- **Two output modes:**
  - **Light gun only (driver)**, Linux only: a separate virtual light gun
    device that the desktop ignores. The system cursor and touchpad stay free,
    and emulators that read input devices directly (e.g. RetroArch with the
    `udev` driver) use it.
  - **System mouse:** moves the real cursor and works with anything. It
    automatically gives the cursor back while you use the touchpad or mouse.
- **Light gun extras:** off-screen reload (optional), reload by jerking the
  device (optional), auto-fire, keyboard keys on any button, rumble "recoil",
  an on-screen crosshair overlay, and per-game profiles that switch
  automatically based on the active window.
- **Desktop app:** a native window with a tray or menu-bar icon, a live
  preview, a full-screen calibration and test range, in 6 languages.
- **Works without a gyroscope too:** with the **system mouse** as the input
  source, users without a gyro device still get the light gun features
  (reload, auto-fire, keys, overlay, profiles).

## How it works

```
gyroscope + accelerometer ──► orientation (Mahony filter, gravity-corrected)
        │
        ▼
barrel direction ──► ray / plane intersection ──► calibrated homography ──► (x, y) on screen
        │                                                                     │
        ▼                                                                     ▼
 One Euro filter + fixed-rate interpolation                     absolute pointer output
                                                    (uinput on Linux · SendInput on Windows · Quartz on macOS)
```

- Sensor axes from each device family are converted to one internal
  convention (X = barrel, Y = left, Z = up). Device-specific code is limited
  to reading the sensor; everything after that is shared.
- No yaw reference exists without a magnetometer, so horizontal drift is
  handled with automatic bias estimation and a recenter button.

## Supported inputs, outputs and platforms

**Inputs (aim sources)**, chosen automatically or in the app:

| Source | How it is read | Notes |
|---|---|---|
| Nintendo Switch Joy-Con / Pro Controller | Linux kernel driver (`hid-nintendo`, evdev) · raw HID elsewhere | Most tested path |
| DualSense (PS5) / DualShock 4 (PS4) | Linux kernel driver · SDL | Point the front of the controller at the screen |
| Other controllers with a gyroscope | SDL (generic sensor API) | e.g. Steam Deck/Controller, 8BitDo models with gyro |
| System mouse | OS cursor position and buttons | For users without a gyro device |

Controllers without a gyroscope, such as most standard Xbox controllers,
can't aim. The app says so and suggests the mouse.

**Outputs:** virtual light gun device (Linux), system mouse (Linux, Windows,
macOS), gyro-mouse relative mode, keyboard keys.

**Platforms:** Linux (X11; tested), Windows (implemented, not yet validated on
real hardware), macOS (experimental, see [`docs/TESTE-MAC.md`](docs/TESTE-MAC.md)).
CI runs the test suite on Linux, Windows and macOS.

## Installation

> 📘 **Step-by-step guide for each system** (requirements, pairing, permissions,
> emulator setup, troubleshooting, updating and uninstalling):
> **[docs/INSTALL.md](docs/INSTALL.md)**. Below is the short version.

Requires Python 3.9+. Each installer creates its own isolated environment and
doesn't touch your system Python.

**Linux**
```bash
./installer/linux/install.sh
```
It may ask for your password once, to install a udev rule (device
permissions) and set BlueZ `ClassicBondedOnly=false`, which is needed by
controllers such as Joy-Cons. See [changes made to your system](#changes-made-to-your-system).

**Windows:** double-click `installer\windows\Instalar.bat` (no administrator
rights needed; installs Python through `winget` if missing).

**macOS (experimental):** double-click `installer/macos/Instalar.command`, then
allow the app under *System Settings → Privacy & Security → Accessibility* and
*Input Monitoring*.

All installers add a menu/start entry and start the app at login (minimized
to the tray). Uninstallers are included. A detailed user guide in Portuguese
is available at [`docs/GUIA-pt-BR.md`](docs/GUIA-pt-BR.md).

## Using the app

1. Rest the device still for ~1 s (the gyroscope status shows **ok**).
2. Click **Calibrate**, aim at the center and the 4 corners, and pull the trigger.
3. Pick the mode: **Light gun only (driver)** or **System mouse**.
4. Try it in the **Test range** (full screen, with hit statistics).

The **Help** tab covers emulator setup (RetroArch, MAME, Dolphin,
DuckStation/PCSX2) and precision tips. Command-line usage:

```bash
capybara-lightgun gui            # the app (also: --tray)
capybara-lightgun run --dry-run  # draw the aim in the terminal; doesn't move the mouse
capybara-lightgun calibrate      # terminal calibration
capybara-lightgun buttons        # show button names as you press them
capybara-lightgun devices        # list detected devices
capybara-lightgun selftest       # check the system without any device
capybara-lightgun sim            # pygame target range
```

## For developers: a gyroscope test bench

Ways to use Capybara Lightgun while developing gyro or pointer features:

- **Feed your app real gyro aiming without writing a driver.** Your
  application just receives absolute mouse or pointer events (or reads the
  virtual device on Linux).
- **Inspect sensor behaviour:** the live preview shows the filtered aim and
  the raw, unfiltered aim side by side. `run --dry-run` prints the aim in the
  terminal.
- **Try your own algorithms:** fusion (`fusion.py`), geometry and calibration
  (`geometry.py`), filtering (`filters.py`) and the pipeline (`engine.py`) are
  small, documented and covered by tests that simulate a physical gun in front
  of a screen.
- **Add a new device:** write an input source that yields `ImuSample`
  (gyro °/s, accel g, dt) and `ButtonState`, converted to the internal axis
  convention. Everything else (calibration, smoothing, outputs, app) works
  unchanged.

## Project layout and tests

```
src/capybara_lightgun/
  fusion.py, geometry.py, filters.py   sensor fusion, projection/homography, One Euro
  engine.py                            pipeline: IMU → aim → pointer + buttons
  calibration.py                       center + 4 corners calibration
  inputs/                              evdev (Linux), raw HID, SDL, system mouse
  outputs/                             uinput, SendInput, Quartz, console
  client.py, gui.py, gui_fields.py     resident app (Qt) and settings
  i18n.py, locales/                    translations
  selftest.py, simulator.py            self-test and pygame target range
installer/                             Linux, Windows and macOS installers
tests/                                 pytest suite
```

```bash
python -m venv .venv && .venv/bin/pip install -e '.[dev,sim]'
.venv/bin/pytest
```

## Translations

The UI is available in English (default), Português (Brasil), Español,
Français, Deutsch and 中文（简体）. The **🌐 Language** selector always stays in
English, so it is easy to switch back. To add a language, copy a file in
`src/capybara_lightgun/locales/`, translate it, register it in `i18n.py`, and
run the tests. `tests/test_i18n.py` flags any missing text.

---

## License (MIT): what it means

This project is licensed under the **MIT License** (see [`LICENSE`](LICENSE)).
In plain words (the `LICENSE` file is the binding text):

- **You may** use, copy, modify, merge, publish, distribute, sublicense and
  sell copies of the software, for any purpose, including commercial use.
- **On one condition:** keep the copyright notice and the license text in
  all copies or substantial portions of the software.
- **No warranty:** the software is provided "as is", without warranty of any
  kind, express or implied, including merchantability, fitness for a
  particular purpose and non-infringement.
- **No liability:** the authors and copyright holders are not liable for any
  claim, damages or other liability arising from the software or its use.

**Why MIT?** The goal is to let anyone, especially developers, study, test,
reuse and improve these gyroscope techniques with as little friction as
possible. The author's **non-profit intent** is a statement of purpose. It
does **not** add restrictions to the license.

## Disclaimer and legal notices

> The complete, authoritative notice is **[DISCLAIMER.md](DISCLAIMER.md)**
> (Portuguese: [AVISO-LEGAL.md](AVISO-LEGAL.md)). It covers, among other
> things, the use of AI (Claude) to generate the project and the fact that
> **each user is solely responsible for how they use the software**. The
> section below is a summary.

*This section is informational and is not legal advice. Laws vary by country.
If you have legal questions, consult a qualified professional. Nothing here
limits or extends the [`LICENSE`](LICENSE); where they differ, the `LICENSE`
prevails.*

### No warranty, use at your own risk
To the maximum extent permitted by applicable law, the software is provided
**"AS IS"**, without warranties of any kind. The authors and contributors are
**not responsible** for any direct or indirect damage, loss of data, damage to
hardware or software, injury, lost profits, account bans or any other
consequence of installing, using, modifying or distributing this software. You
decide whether and how to use it, and you take responsibility for that use.

### Purpose and intended use
Capybara Lightgun is a non-commercial, educational and development tool for
**interoperability**: it lets devices you own work as pointing devices on your
own computer. It is **not intended** for, and must not be used for, cheating,
gaining unfair advantages, circumventing restrictions, or harming people,
systems or businesses.

### No affiliation, trademarks
This project is **independent**. It is not affiliated with, sponsored by, or
endorsed by Nintendo, Sony Interactive Entertainment, Microsoft, Valve, 8BitDo,
Apple, or any other company. *Nintendo Switch, Joy-Con, PlayStation,
DualSense, DualShock, Xbox, Steam, Steam Deck, macOS, Windows* and other names
are trademarks of their respective owners. They appear here **only to
identify compatibility** (nominative use). Listing a device is not a
recommendation, and no device is preferred: the project targets the
**gyroscope** as a sensor.

### No proprietary content, no circumvention
The project contains **no** proprietary code, firmware, encryption keys,
BIOS, ROMs, games or other copyrighted material from device or game makers.
It only uses **public operating-system interfaces** (evdev/uinput, HID, SDL,
Win32, Quartz) and publicly documented or community-documented device
reports, for interoperability. It does **not** modify device firmware and
does **not** circumvent copy protection, DRM or any other technological
protection measure.

### Games, emulators and online services
Capybara Lightgun doesn't provide or link to games or ROMs. If you use it
with emulators, **you are responsible** for owning legal copies and complying
with the applicable licenses and laws. Input emulation may **violate the
terms of service** of online or competitive games, or trigger anti-cheat
systems. Don't use it where that is not allowed. The authors are not
responsible for account suspensions or other penalties.

### Changes made to your system
The installers are transparent, user-level and reversible. Depending on the
platform, they may:
- **Linux:** add a udev rule (`/etc/udev/rules.d/70-capybara-lightgun.rules`)
  granting the logged-in user access to supported controllers and
  `/dev/uinput`. Load the `uinput` and `hid-nintendo` modules. Set
  `ClassicBondedOnly=false` in `/etc/bluetooth/input.conf`, with a backup.
  **Note:** that setting lets Bluetooth input devices connect without
  bonding. Controllers such as Joy-Cons need it, but it slightly relaxes a
  BlueZ security default. Review it if you are in a sensitive environment,
  and restore the backup to revert.
- **All platforms:** create an isolated Python environment, a menu/start
  shortcut and a start-at-login entry. Uninstallers remove them (your
  settings are kept).
- **macOS:** ask you to grant Accessibility and Input Monitoring permissions.

Please read the scripts in `installer/` and `scripts/` before running them.

### Privacy
The app makes **no network connections** and collects **no telemetry**.
Settings, calibration and logs are stored only on your computer. The
optional automatic profile switching reads the **title or class of the active
window** locally, only to match the words you configure. It is never stored
or sent anywhere.

### Physical safety
You are moving a device in the air: use the **wrist strap**, keep clear space
around you and others, hold the device firmly, and take breaks. Rumble is
optional.

### Third-party software
Capybara Lightgun depends on third-party packages that have **their own
licenses**, including PyQt5 (GPL v3 or commercial), Qt, SDL2 and PySDL2
(zlib and public domain), pygame (LGPL), python-evdev / evdev-binary (BSD) and
hidapi (BSD/GPL/original). The installers download them from PyPI. The MIT
License of this project covers only this project's own code. If you
**redistribute a bundle** that includes these components (for example a
packaged executable), you must comply with their licenses too, notably the
GPL terms of PyQt5.

### Contributions
By contributing, you agree that your contribution is licensed under the same
MIT License and that you have the right to submit it.

---

Copyright (c) 2026 loboguaraBR. Licensed under the [MIT License](LICENSE).
