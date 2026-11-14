# Installation guide

**English** · [Português (Brasil)](INSTALACAO.md)

This guide explains, step by step, how to install, configure, update and
remove **Capybara Lightgun** on **Linux**, **Windows** and **macOS**.

> Before installing, read the [legal notice](../DISCLAIMER.md). By installing
> or using the software you accept that you use it **at your own risk** and
> that **you alone are responsible** for how you use it.

---

## Contents

1. [Before you start (all systems)](#1-before-you-start-all-systems)
2. [Linux](#2-linux)
3. [Windows](#3-windows)
4. [macOS (experimental)](#4-macos-experimental)
5. [Pairing your device](#5-pairing-your-device)
6. [First use: calibration and test](#6-first-use-calibration-and-test)
7. [Setting up emulators and games](#7-setting-up-emulators-and-games)
8. [Troubleshooting](#8-troubleshooting)
9. [Updating](#9-updating)
10. [Uninstalling](#10-uninstalling)
11. [Manual installation (developers)](#11-manual-installation-developers)
12. [Where files are stored](#12-where-files-are-stored)

---

## 1. Before you start (all systems)

**You need:**
- A computer with **Linux**, **Windows 10/11** or **macOS 10.15+**.
- **Python 3.9 or newer.** On Windows the installer can install it for you.
- An **internet connection** during installation, to download the Python
  packages. After that, the app works offline and never connects to the
  network.
- **One aim source:**
  - any device with a **gyroscope** the system can read (for example
    Joy-Con, Pro Controller, DualSense, DualShock 4, Steam Deck/Controller,
    some 8BitDo models), or
  - just the **system mouse**, if you don't have a gyroscope device. Most
    standard Xbox controllers have no gyroscope.

**Download the project**, either way:
- **ZIP:** open <https://github.com/loboguaraBR/CapybaraLightgun>, click
  **Code → Download ZIP**, and extract it to a folder you will keep (the
  installers copy what they need, but keeping the folder makes updates
  easier).
- **Git:**
  ```bash
  git clone https://github.com/loboguaraBR/CapybaraLightgun.git
  cd CapybaraLightgun
  ```

**Close other controller tools** that may grab the device: Steam (or turn off
Steam Input for that controller), BetterJoy, DS4Windows, reWASD, joycond and
similar.

---

## 2. Linux

Tested on Ubuntu/Linux Mint with X11. It should work on other distributions
with a recent kernel (5.16+ for Nintendo controllers) and BlueZ.

### 2.1 Install

```bash
cd CapybaraLightgun
./installer/linux/install.sh
```

What the installer does:
1. **Asks for your password once** (sudo), only if needed, to:
   - install the udev rule `/etc/udev/rules.d/70-capybara-lightgun.rules`,
     which gives the logged-in user access to supported controllers and to
     `/dev/uinput` without root;
   - load the `uinput` and `hid-nintendo` kernel modules;
   - set `ClassicBondedOnly=false` in `/etc/bluetooth/input.conf`, with a
     backup. Controllers such as Joy-Cons need this to connect. It slightly
     relaxes a BlueZ security default; see the [legal notice](../DISCLAIMER.md).
2. Creates an **isolated Python environment** in
   `~/.local/share/capybara-lightgun` (your system Python is not touched). If
   `python3-venv` is missing, it downloads the official `get-pip` instead of
   asking you to install packages.
3. Installs the `capybara-lightgun` command in `~/.local/bin`.
4. Adds **Capybara Lightgun** (and the **Simulator**) to the applications
   menu, and makes the app start minimized in the tray when you log in.
5. Opens the app.

You can review everything first: `installer/linux/install.sh` and
`scripts/fix-linux-joycon.sh`.

### 2.2 After installing

- **Re-connect the controller** (turn it off and on, or re-pair it) so the
  new permissions apply.
- If the command `capybara-lightgun` is not found in a terminal, log out and
  back in (so `~/.local/bin` enters your `PATH`).

### 2.3 Linux-specific notes

- **Two output modes:** *Light gun only (driver)* creates a virtual light gun
  that the desktop ignores, so the cursor and touchpad stay free (made for
  RetroArch with the `udev` input driver). *System mouse* moves the real
  cursor and works with any game.
- **Wayland:** the gun output works, but reading the system mouse as an aim
  source, the on-screen crosshair and the automatic profile switching need
  **X11**.

---

## 3. Windows

> Status: implemented and covered by the automatic tests, but **not yet
> validated with real controllers on Windows**. Please report problems.

### 3.1 Install

1. Download and extract the project (see [section 1](#1-before-you-start-all-systems)).
2. Open the folder `installer\windows` and **double-click `Instalar.bat`**.
   - If Windows SmartScreen shows "Windows protected your PC", click
     **More info → Run anyway**. The script is plain text; you can open it in
     Notepad to review it first.
3. The installer:
   - finds Python 3.9+, or installs Python 3.12 for your user through
     `winget` (no administrator rights needed);
   - creates an isolated environment in `%LOCALAPPDATA%\CapybaraLightgun`;
   - installs the program and its dependencies (hidapi, PyQt5, SDL2, pygame);
   - creates shortcuts in the **Start menu** and on the **Desktop**, plus a
     **Startup** shortcut so the app opens in the tray when you log in;
   - registers the app in **Settings → Apps** (to uninstall it there);
   - opens the app.

If `winget` is not available, install Python from
<https://www.python.org/downloads/>, **check "Add python.exe to PATH"**, and
run `Instalar.bat` again.

### 3.2 Windows-specific notes

- Only the **System mouse** output exists on Windows. A separate light gun
  device would need a kernel driver.
- Close **Steam** (or disable Steam Input for the controller), **BetterJoy**
  and **DS4Windows**: they compete for the controller.
- If Windows "Enhance pointer precision" is on, it only affects the *Gyro
  mouse (relative)* mode, not the absolute light gun.

---

## 4. macOS (experimental)

> Status: **experimental**. Implemented and covered by automatic tests on
> Macs (Apple Silicon and Intel), but not yet validated on a real Mac with
> controllers. The checklist in [`TESTE-MAC.md`](TESTE-MAC.md) helps report
> results.

### 4.1 Install

1. Install **Python 3.9+** from <https://www.python.org/downloads/macos/> or
   with Homebrew (`brew install python`).
2. Download and extract the project.
3. In Finder, open `installer/macos` and **double-click `Instalar.command`**.
   If macOS blocks it, **right-click → Open → Open**.
4. The installer:
   - creates an isolated environment in
     `~/Library/Application Support/CapybaraLightgun`;
   - creates the app **`~/Applications/Capybara Lightgun.app`** with an icon;
   - makes it open at login (icon in the menu bar) through a LaunchAgent;
   - runs a self-test and opens the app.

### 4.2 Permissions (required)

macOS asks for two permissions. Without them the gun can't move the cursor or
read the controller:

1. In the app, click the yellow button **⚠ Grant macOS permissions** (or open
   *System Settings → Privacy & Security*).
2. Turn on **Capybara Lightgun** under **Accessibility** and under **Input
   Monitoring**.
3. **Quit** the app (menu bar icon → Quit) and open it again.

### 4.3 macOS-specific notes
- Only the **System mouse** output exists on macOS.
- Nintendo controllers are read through HID; PlayStation and other
  controllers through SDL.

---

## 5. Pairing your device

Pair through your system's Bluetooth settings (or connect with USB when the
device supports it). Put the device in **pairing mode** first:

| Device | Pairing mode | How to hold it as a gun |
|---|---|---|
| Joy-Con (L or R) | Hold the small **sync** button on the rail until the lights run back and forth | Upright like a pistol, the trigger (ZR/ZL) under your index finger |
| Pro Controller | Hold the **sync** button on the top edge | Point the top edge (triggers) at the screen |
| DualSense (PS5) | Hold **Create + PS** until the light bar blinks quickly | Point the front (light bar side) at the screen |
| DualShock 4 (PS4) | Hold **Share + PS** until the light bar blinks quickly | Point the front at the screen |
| Steam Deck / other gyro devices | See the maker's manual | Point the front at the screen |
| System mouse | Nothing to pair | — |

**Linux tip:** if a Joy-Con connects but its lights **keep blinking**, the
BlueZ setting is missing. Run
`sudo ./scripts/fix-linux-joycon.sh`, then press a button on the Joy-Con.

---

## 6. First use: calibration and test

1. Open **Capybara Lightgun** (menu, Start menu, Applications, or the tray
   icon).
2. Choose the **🌐 Language** at the top if you want. It is always labeled in
   English, so you can always find your way back.
3. In the **Controller** tab, keep the aim source on **Automatic** or pick
   your device (or **System mouse**).
4. **Rest the device still** on a table for ~1 s, until *Gyroscope: ok*.
5. Click **🎯 Calibrate**. Holding the device the way you will play, aim at the
   **center** and then at the **4 corners**, pulling the trigger at each
   target. The result shows the error (below 1% is great).
6. Click **🔫 Test range** and shoot the targets. **H** hides the crosshair,
   which is a good way to check that the aim follows where you point. **ESC**
   exits.
7. If the aim drifts sideways while playing: point at the **center** of the
   screen and press **Y** (□ on PlayStation).

---

## 7. Setting up emulators and games

| Software | Mode in Capybara Lightgun | Setting in the software |
|---|---|---|
| **RetroArch** (Linux) | *Light gun only (driver)* | Settings → Drivers → Input = `udev`; Port 1 → Device Type = *Light Gun*, Mouse Index = *Capybara Lightgun (driver)* |
| **RetroArch** (Windows/macOS) | *System mouse* | Port 1 → Device Type = *Light Gun* (mouse) |
| **MAME** | *System mouse* | `-lightgun -lightgun_device mouse` (and `-offscreen_reload` to reload with the 2nd button) |
| **Dolphin** (Wii) | *System mouse* | Wii Remote → Point = mouse cursor |
| **DuckStation / PCSX2** (GunCon) | *System mouse* | Controller = GunCon, aim with the mouse |
| PC games without absolute mouse | *Gyro mouse (relative)* (Output tab) | Normal mouse aiming |

Make one **profile** per game in the *Profiles* tab. Type words from the game
window (e.g. `retroarch`, `mame`) to switch profiles automatically.

### NES Zapper in RetroArch (FCEUmm core)

Tested on Linux (X11) with RetroArch 1.22:

1. In Capybara Lightgun, use the **System mouse** output. RetroArch's default
   input driver (`x`) then sees the gun. *Light gun only (driver)* mode is
   invisible to that driver.
2. *Quick Menu → Controls → Port 2 Controls → Device Type* = **Zapper**. Duck
   Hunt and most Zapper games only read **port 2**: on port 1 the crosshair
   shows up but shots don't register.
3. *Settings → Input → Port 2 Controls → Mouse Index* = **0**. The `x` driver
   only serves mouse 0: with another index the crosshair doesn't even appear.
4. *Quick Menu → Core Options → Zapper Mode* = **Crosshair light gun**
   (`fceumm_zapper_mode = "clightgun"`). *Mouse* mode uses relative motion and
   the aim drifts.
5. The trigger is the left click (`input_player2_gun_trigger_mbtn = "1"`, the
   default). In Capybara, check on the *Buttons* tab that the button you use
   as the trigger is set to *Trigger*.

Close RetroArch before editing `retroarch.cfg` by hand, because it saves its
settings when it exits.

---

## 8. Troubleshooting

| Problem | What to do |
|---|---|
| "No controller found" | Check it is paired and connected; close Steam/BetterJoy/DS4Windows; click **Reconnect**. On Linux, run `capybara-lightgun devices`. |
| Joy-Con lights keep blinking (Linux) | `sudo ./scripts/fix-linux-joycon.sh`, then press a Joy-Con button. |
| Bluetooth turned off after the fix (some laptops) | `rfkill unblock bluetooth` and `bluetoothctl power on`, then re-pair. |
| "No gyroscope" message | That controller has no gyroscope (e.g. standard Xbox). Use the **System mouse** source. |
| Aim drifts sideways slowly | Rest the device still for 1 s (auto-correction), or press **Y** aiming at the center. |
| Aim shakes when still | Lower *Stability when still* or enable *Micro-movement lock* (Aim tab). |
| Cursor moves in steps | Raise *Motion smoothness* to 20–25 ms (Aim tab); keep the device closer to the computer. |
| Shot lands off when pulling the trigger | Raise *Trigger jerk compensation* (Shooting tab). |
| Cursor fights with the touchpad | Use *Light gun only (driver)* (Linux), or keep *Yield to touchpad/mouse* on. |
| macOS: nothing moves | Grant **Accessibility** and **Input Monitoring**, then reopen the app. |
| Chose a language by mistake | Find **🌐 Language** at the top (always in English) and pick *English*. |

**Check your system without any device:**
```bash
capybara-lightgun selftest
```
On Windows, run it from
`%LOCALAPPDATA%\CapybaraLightgun\venv\Scripts\capybara-lightgun selftest`. On
macOS, from
`~/Library/Application\ Support/CapybaraLightgun/venv/bin/capybara-lightgun selftest`.

The app log is `client.log` in the [settings folder](#12-where-files-are-stored).

---

## 9. Updating

Download the new version (ZIP or `git pull`) and **run the installer again**.
Settings, profiles, calibration and language are kept.

---

## 10. Uninstalling

| System | How |
|---|---|
| Linux | `~/.local/share/capybara-lightgun/uninstall.sh` |
| Windows | *Settings → Apps → Capybara Lightgun → Uninstall*, or `installer\windows\Desinstalar.bat` |
| macOS | `~/Library/Application\ Support/CapybaraLightgun/uninstall.sh` |

Your settings are kept; delete the [settings folder](#12-where-files-are-stored)
to remove them too. On Linux, the system changes can be reverted with
`sudo rm /etc/udev/rules.d/70-capybara-lightgun.rules
/etc/modules-load.d/capybara-lightgun.conf`, and by restoring
`/etc/bluetooth/input.conf` from its backup (`input.conf.bak-lightgun`).

---

## 11. Manual installation (developers)

```bash
git clone https://github.com/loboguaraBR/CapybaraLightgun.git
cd CapybaraLightgun
python3 -m venv .venv
.venv/bin/pip install -e '.[dev,sim]'     # Windows: .venv\Scripts\pip install -e ".[dev,sim]"
.venv/bin/pytest                           # tests
.venv/bin/capybara-lightgun selftest       # system check
.venv/bin/capybara-lightgun gui            # run the app
```

On Linux, device access still needs the udev rule
(`sudo ./scripts/fix-linux-joycon.sh`).

---

## 12. Where files are stored

| | Program | Settings, calibration, language, log |
|---|---|---|
| Linux | `~/.local/share/capybara-lightgun` | `~/.config/capybara-lightgun` |
| Windows | `%LOCALAPPDATA%\CapybaraLightgun` | `%APPDATA%\capybara-lightgun` |
| macOS | `~/Library/Application Support/CapybaraLightgun` and `~/Applications/Capybara Lightgun.app` | `~/Library/Application Support/capybara-lightgun` |
