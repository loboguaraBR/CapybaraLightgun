# Legal notice and disclaimer

**English** · [Português (Brasil)](AVISO-LEGAL.md)

Applies to **Capybara Lightgun** (the "Software"), including its source code,
installers, documentation and translations, as published at
<https://github.com/loboguaraBR/CapybaraLightgun>.

> **Summary.** The Software was **generated with the AI assistant Claude
> (Anthropic)**. It is provided **as is, without any warranty**. **Each person
> who downloads, installs, uses, modifies or distributes it is solely
> responsible for that use.** The author does not control, monitor or approve
> how third parties use it, and is not liable for any consequence of that
> use, to the maximum extent permitted by law.

---

## 1. About this document

1.1. This notice is informational. It does **not** replace the
[`LICENSE`](LICENSE) (MIT License), which is the legal grant of rights for the
Software. This notice does not restrict the rights the MIT License gives you.
If anything here conflicts with the `LICENSE`, the `LICENSE` prevails.

1.2. This notice is **not legal advice**. Laws differ between countries. If you
have legal questions about your use of the Software, consult a qualified
professional in your jurisdiction.

1.3. If any part of this notice is found unenforceable, the remaining parts
remain in effect.

## 2. Generated with artificial intelligence (Claude)

2.1. The Software (source code, tests, installers, documentation and
translations) was **generated with the assistance of Claude**, an artificial
intelligence model developed by **Anthropic**, used through the *Claude Code*
tool. The project author directed the work, made the decisions, tested it on
their own equipment and published it.

2.2. AI-generated content can contain **errors, bugs, security
vulnerabilities, inaccurate translations or incorrect statements** that were
not detected during testing. Review the code and the documentation before
relying on them.

2.3. **Anthropic** is not a party to this project. It does not endorse,
sponsor, maintain or take responsibility for the Software. "Claude" and
"Anthropic" are trademarks of Anthropic, PBC, and are mentioned here only to
disclose how the Software was made.

## 3. No warranty

To the maximum extent permitted by applicable law, the Software is provided
**"AS IS" and "AS AVAILABLE"**, with **no warranty of any kind**, express or
implied. This includes, without limitation, warranties of merchantability,
fitness for a particular purpose, accuracy, reliability, security,
availability, compatibility with any device or system, and
non-infringement. The Software may stop working with future versions of
operating systems, drivers, devices or games.

## 4. Limitation of liability

To the maximum extent permitted by applicable law, **the author, copyright
holders and contributors are not liable** for any claim, damage, loss or
expense of any kind, whether direct, indirect, incidental, special,
consequential or punitive. This includes, without limitation:
- damage to or malfunction of computers, controllers, other devices or
  software;
- loss or corruption of data, settings or saved games;
- personal injury or damage to property;
- suspension, ban or penalty on accounts, games or online services;
- lost profits, revenue, business or opportunities;
- any consequence of the use, misuse or inability to use the Software;
- any act or omission of **third parties**, including people who use, modify
  or redistribute the Software;

whether the claim is based on contract, tort (including negligence), strict
liability or any other theory, even if advised of the possibility of such
damage.

## 5. Your responsibility for how the Software is used

5.1. **You alone are responsible** for your decision to download, install,
use, modify or distribute the Software, and for every consequence of doing
so.

5.2. **The author does not control, monitor, review or approve how anyone
uses the Software**, including modified versions. Any use that is illegal,
harmful, abusive, or that breaks contracts, terms of service or the rights of
others is contrary to the purpose of the project. **It is the sole
responsibility of the person who does it.**

5.3. You are responsible for complying with all laws, regulations, licenses,
terms of service and agreements that apply to you. This includes the terms of
games, platforms, emulators, devices and online services you use together
with the Software.

5.4. If you don't agree with this notice, don't download, install or use the
Software.

## 6. Purpose and uses the project does not intend

6.1. Capybara Lightgun is a **non-commercial, educational and development**
project. It was made to let developers **quickly test gyroscope features** in
their applications, and to let people use gyroscope devices they own as
light-gun-style pointers on their own computers (**interoperability**).

6.2. The project is **not intended** for, and the author does not support,
using it to: cheat or gain unfair advantage in games or competitions;
circumvent technical restrictions, copy protection or anti-cheat systems;
commit fraud; gain unauthorized access to systems; harass, harm or endanger
anyone; or any other unlawful purpose.

6.3. The Software is **not certified** for medical, safety-critical,
industrial or professional accessibility use. Don't rely on it where a failure
could cause harm.

## 7. Modified versions and redistribution by others

7.1. The MIT License lets anyone modify and redistribute the Software. **The
author is not responsible for modified versions, forks, compiled or packaged
builds, or copies distributed by third parties**, nor for any changes they
make.

7.2. The only official source is the repository linked at the top of this
notice. Download the Software from there.

## 8. No affiliation; trademarks

The project is **independent**. It is not affiliated with, sponsored by, or
endorsed by Nintendo, Sony Interactive Entertainment, Microsoft, Valve,
8BitDo, Apple, Anthropic or any other company. *Nintendo Switch, Joy-Con,
PlayStation, DualSense, DualShock, Xbox, Steam, Steam Deck, Windows, macOS,
Claude* and other names are trademarks of their respective owners. They are
used only to describe compatibility or how the Software was made (nominative
use), and no device or brand is preferred or endorsed. The project's focus is
the **gyroscope** as a sensor.

## 9. No proprietary content; no circumvention

The Software contains **no** proprietary code, firmware, cryptographic keys,
BIOS, ROMs, games or other copyrighted material belonging to device or game
manufacturers. It only uses **public operating-system interfaces** (evdev,
uinput, HID, SDL, Win32, Quartz) and device report formats documented
publicly or by the community, for interoperability. It does **not** modify
device firmware and does **not** circumvent copy protection, DRM or other
technological protection measures.

## 10. Games, emulators, ROMs and online services

The Software does not provide, host or link to games, ROMs or BIOS files. If
you use emulators, **you are responsible** for owning legitimate copies and for
complying with copyright law and the applicable licenses. Input emulation may
**violate the terms of service** of online or competitive games, or trigger
anti-cheat systems. Don't use the Software where that is not allowed.

## 11. Changes to your system and security

The installers make user-level, reversible changes, described in the
[installation guide](docs/INSTALL.md). On Linux, with your permission (sudo),
they also add a udev rule, load kernel modules, and set
`ClassicBondedOnly=false` in BlueZ. **That setting lets Bluetooth input
devices connect without bonding, which slightly reduces a Bluetooth security
default.** Evaluate this risk for your environment before installing. You
can revert it by restoring the backup of `/etc/bluetooth/input.conf`. Read
the scripts before running them.

## 12. Hardware and physical safety

Moving a device in the air carries a risk of injury and damage. Use the
**wrist strap**, keep clear space around you and other people, hold the device
firmly and take breaks. Vibration ("recoil") is optional and can be turned
off. The author is not responsible for injuries or damage to devices, screens
or property.

## 13. Privacy

The Software makes **no network connections** and collects **no telemetry**.
Settings, calibration and logs stay on your computer. The optional automatic
profile switching reads the title or class of the active window **locally**,
only to compare it with words you configured. That information is never
stored or sent.

## 14. Third-party software

The Software depends on third-party packages with **their own licenses**,
including PyQt5 (GPL v3 or commercial), Qt, SDL2 and PySDL2 (zlib and public
domain), pygame (LGPL), python-evdev / evdev-binary (BSD) and hidapi
(BSD/GPL/original). The installers download them from PyPI. The MIT License
of this project covers only this project's own code. If you redistribute a
bundle that includes these components, you must also comply with their
licenses, notably the GPL terms of PyQt5.

## 15. Contributions

By contributing to the project, you agree that your contribution is licensed
under the MIT License and that you have the right to submit it. You remain
responsible for your contribution.

---

Copyright (c) 2026 loboguaraBR · Software licensed under the [MIT License](LICENSE).
