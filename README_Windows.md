# Mandala Generator for Windows

The packaged Windows build **does not require Python** — the interpreter
and all libraries are bundled inside the program. Download, install, run.

It comes in two forms:

| Form | File | Purpose |
| --- | --- | --- |
| Installer | `MandalaSetup-<version>.exe` | Regular installation: shortcuts, uninstaller |
| Portable | `Mandala-portable-<version>.zip` | No installation: unzip and run |

Windows 10 and 11 (64-bit) are supported.

---

## Table of contents

1. [Getting the installer](#getting-the-installer)
2. [Installation](#installation)
3. [Drawing parameters](#drawing-parameters)
4. [Where mandalas and logs are stored](#where-mandalas-and-logs-are-stored)
5. [Portable version](#portable-version)
6. [Uninstalling](#uninstalling)
7. [Troubleshooting](#troubleshooting)
8. [Building from source](#building-from-source)
9. [Repository layout](#repository-layout)
10. [Appendix: styles and palettes](#appendix-styles-and-palettes)

---

## Getting the installer

### Option 1: GitHub Actions — no Windows machine needed

The installer is built automatically in the GitHub cloud.

1. Put the project in a GitHub repository:

   ```bash
   git init
   git add .
   git commit -m "Mandala Generator"
   git remote add origin https://github.com/<user>/<repository>.git
   git push -u origin main
   ```

2. Open the repository's **Actions** tab → in the left sidebar select
   **Build Windows installer** → click **Run workflow** → **Run workflow**.
   (The build also starts automatically when a tag is pushed, e.g. `2.3`
   or `v1.0.0`.)

3. After a few minutes the finished run contains an artifact named
   **Mandala-Windows** — download it. Inside:

   - `MandalaSetup-<version>.exe` — the installer;
   - `Mandala-portable-<version>.zip` — the portable version.

Note: artifacts are only available to users signed in to GitHub.

### Option 2: build on any Windows machine

All you need is Windows 10/11 and an internet connection — the script
does everything itself:

1. Copy the project to the Windows machine (e.g. unzip the repository).
2. Double-click `windows\build_windows.bat`.
3. The script will, in order: install Python (for building only), install
   the dependencies, build the application (PyInstaller), install
   Inno Setup, and produce `MandalaSetup-<version>.exe` plus a portable zip.
4. The finished files appear in the `dist\` directory (it opens
   automatically).

Subsequent builds are faster — Python and the environment are kept
between runs.

---

## Installation

1. Run `MandalaSetup-<version>.exe`.
2. If Windows shows the blue **SmartScreen** window ("Windows protected
   your PC"), click **More info** → **Run anyway**. The warning appears
   because the installer has no digital signature (a certificate costs
   money); the code itself is ordinary.
3. Follow the wizard: installation runs **without administrator rights**,
   by default into `%LOCALAPPDATA%\Mandala` (inside your profile).
4. When done, you can launch the program right away (checkbox in the
   wizard).

Shortcuts: **Start → Mandala Generator** and, optionally, the desktop.

On every launch a **settings window** opens — adjust the parameters
and click "Draw" (the button is labelled in Russian).

---

## Drawing parameters

There are two equivalent ways to set the parameters — both are stored in
the same `config.ini` file.

### Settings window

Opens on every launch and lives independently of the drawing window.

- **Drawing speed** — slider 1–20 with a time estimate
  (1 — slow, about 7 minutes; 20 — fast, about 4 seconds);
- **Coloring** — always / outlines only / random on each launch;
- **Palette** — random, all families combined, or one of the four
  (warm soft, cool soft, warm bright, cool bright);
- **Save format** — PDF (vector) / PNG / JPG;
- **Window size** and **line width**;
- **Ring sizes** — center radius and band/layer widths (advanced);
- Buttons "Open the mandala folder" and "Open config.ini".

The **"Draw"** button saves the parameters and starts the generation in
its own window **without closing** the settings window — you can change
parameters and draw several mandalas in a row. **"Save config.ini"** only
saves them. The settings window closes only via its own close button;
closing the "Mandala Generator" window does not affect it.

The interface of the settings window is in Russian; the values map
one-to-one onto the `config.ini` keys below.

### config.ini file

Location: `%APPDATA%\Mandala\config.ini` (paste this path into the
Explorer address bar). It opens in Notepad. The file is created
automatically on the first launch; its comments are in Russian — only
the values after `=` matter. The same file opens from a button in the
settings window.

Example:

```ini
[Рисование]
; Цвет фона: имя (white, black, ...) или #rrggbb
BG_COLOR = white
; Скорость: 1 — медленно (~440 c), 20 — быстро (~4 c)
DRAW_SPEED_LEVEL = 12
```

Main parameters:

| Parameter | Default | Purpose |
| --- | --- | --- |
| `BG_COLOR`, `LINE_COLOR` | `white`, `black` | Background and outline colors |
| `LINE_WIDTH` | `1.5` | Pen width, px |
| `DRAW_SPEED_LEVEL` | `15` | Animation speed, 1–20 |
| `COLOR_MODE` | `yes` | Coloring: `yes` / `no` / `random` |
| `PALETTE_CHOICE` | `random` | Palette: `random`, `all`, `warm_soft`, `cool_soft`, `warm_bright`, `cool_bright` |
| `SAVE_FORMAT` | `pdf` | `pdf` (vector) / `png` / `jpg` |
| `WINDOW_SIZE` | `1000` | Window size, px (400–2000) |
| `CIRCLE_RADIUS`, `BAND1_WIDTH`…`L5_WIDTH` | see config.py | Center radius and ring widths |
| `PAINT_LAYER_RINGS` | `true` | Color the layer rings |

The `[Веса стилей]` section controls pattern probabilities: `0` disables
a pattern, `2` makes it twice as likely. All weights are already listed
in the file as active lines — edit any value (put comments on their own
lines above):

```ini
[Веса стилей]
; the "Om" symbol is never picked:
CENTER_7 = 0
; "Leaf with vein (45°)" is three times as likely:
LAYER_5 = 3.0
```

The `[Веса цветов]` section works the same way for individual palette
colors: `0` excludes a color, `2` makes it twice as likely:

```ini
[Веса цветов]
; this color is never picked:
WARM_SOFT_#e8a87c = 0
; twice as likely:
COOL_BRIGHT_#3d6a99 = 2.0
```

Every center, band, layer and every palette color together with its
probability is already listed in `config.ini` as an active line — the
file contains the full parameter set.

**Edits are never lost:** the settings window updates known values in
place and keeps your comments, line order and unknown lines. Editing the
file in Notepad while the program is closed is always safe. The full
reference of styles and colors is in the
[appendix](#appendix-styles-and-palettes) — and right inside `config.ini`,
where every style number and every palette color is listed as an active
line with its weight, while comment lines explain the numbering.

**Resetting to defaults** — delete a parameter from the file, or the whole
`config.ini` (it is recreated on the next launch).

---

## Where mandalas and logs are stored

| What | Regular installation | Portable version |
| --- | --- | --- |
| Mandalas | `Pictures\Mandala` (`%USERPROFILE%\Pictures\Mandala`; shown as «Изображения» in Russian Windows) | `img\` next to `Mandala.exe` |
| Logs | `%LOCALAPPDATA%\Mandala\logs` | `log\` next to `Mandala.exe` |
| config.ini | `%APPDATA%\Mandala\config.ini` | next to `Mandala.exe` |

The mandala folder can be opened directly from the settings window.

---

## Portable version

Unzip `Mandala-portable-<version>.zip` into any writable folder
(e.g. `D:\Mandala`) and run `Mandala.exe`. All data is kept next to the
program, nothing is registered in the system — handy on a USB stick.
Do not delete the `portable.ini` marker file: it is what enables this
mode.

---

## Uninstalling

**Settings → Apps → Mandala Generator → Uninstall** (or the classic
Control Panel → Programs and Features).

Uninstalling the program **does not touch your data**: generated
mandalas, logs and `config.ini` remain. Remove them manually if needed:

- `%USERPROFILE%\Pictures\Mandala`
- `%APPDATA%\Mandala`
- `%LOCALAPPDATA%\Mandala`

For the portable version, just delete the folder.

---

## Troubleshooting

**SmartScreen blocks the launch.** Click "More info" → "Run anyway".
Alternatively, build the installer yourself
(see [Building from source](#building-from-source)).

**The antivirus flags the program as suspicious.** This occasionally
happens with any unsigned PyInstaller build. Add the program to the
exclusions, or build it yourself from the sources on your machine.

**The program does not start and reports "Программа не смогла
запуститься".** Details are written to a `crash-<date>-<time>.txt` file
in the logs directory (see the table above). Send that file to whoever
builds the program.

**The settings window opens on every launch — by design.** If it is in
the way, close it: an already started drawing keeps running, and the
parameters can be edited in `config.ini` (the window re-reads the file
when you switch back to it).

**config.ini cannot be found.** Press Win+R, paste
`%APPDATA%\Mandala\config.ini`, press Enter.

---

## Building from source

A single script on a Windows machine with internet access:

```bat
windows\build_windows.bat
```

What happens, step by step:

1. **Python** — if the machine has no Python 3.9+, the script downloads
   and silently installs Python 3.12.8 (for the current user only; needed
   for building, not included in the finished program).
2. **Dependencies** — `.venv-win` is created and `pillow`, `pycairo`,
   `pyinstaller` are installed (see `windows\requirements-win.txt`).
   Pycairo bundles Cairo inside the pip package — no GTK/MSYS2 downloads
   needed.
3. **Application** — PyInstaller builds `dist\Mandala\Mandala.exe` from
   `windows\mandala.spec` (onedir, windowed, icon `windows\icon.ico`).
4. **Installer** — Inno Setup 6 is installed if necessary (free, from
   jrsoftware.org), then `windows\installer\mandala.iss` is compiled →
   `dist\MandalaSetup-<version>.exe`.
5. **Portable zip** — `windows\make_portable.ps1` packs the same
   application with the `portable.ini` marker.

The version is set in `windows\version.txt` (a single line, e.g. `2.2`);
it goes into the installer file name and into the Apps list. To change
the icon, replace `windows\icon.ico`.

If for some reason you need the `cairocffi` variant instead of `pycairo`:
`windows\update_cairo_dlls.ps1` downloads the required Cairo DLLs (MSYS2)
into `windows\cairo_dlls\`, and the spec includes them in the build
automatically.

---

## Appendix: styles and palettes

All names come from `config.py`. Weights are set by number in the
`[Веса стилей]` section: `CENTER_<n>`, `BAND_<n>`, `LAYER_<n>`.

### Center patterns (`CENTER_<n>`)

| # | Pattern |
| --- | --- |
| 1 | Radial rays |
| 2 | Concentric circles |
| 3 | Spiral |
| 4 | Inner loops |
| 5 | Bullseye (dense center) |
| 6 | Star of David (outer rays) |
| 7 | Om |
| 8 | Flower |
| 9 | Lotus |
| 10 | Sun |
| 11 | Knot |

### Separator bands (`BAND_<n>`)

| # | Band |
| --- | --- |
| 1 | Straight strokes |
| 2 | Small circles (sparse) |
| 3 | Zigzag |
| 4 | Double circles |
| 5 | Double strokes |
| 6 | Circles |
| 7 | Squares |
| 8 | Semicircles |
| 9 | Small circles 2 |
| 10 | Wave |
| 11 | Diamonds |
| 12 | Double wave |

### Petal layers (`LAYER_<n>`)

| # | Layer |
| --- | --- |
| 1 | Flame with dots |
| 2 | Double rings |
| 3 | Leaf in leaf with vein |
| 4 | Classic leaf with pistil |
| 5 | Leaf with vein (45°) |
| 6 | Large half-leaf with small ones |
| 7 | Double leaf |
| 8 | Leaf, pistil with three dots |
| 9 | Triple leaf |
| 10 | Half-leaf (triple pistil) |
| 11 | Double half-leaf |
| 12 | Leaf with veins |
| 13 | Fan (no center) |
| 14 | Double half-leaf with pistil |
| 15 | Double half-leaf (with dot) |
| 16 | Triple rhombus with pistil |
| 17 | Double leaf with dot |

### Palettes (`PALETTE_CHOICE`)

Each family contains 11 colors; weight keys in `[Веса цветов]` are
`<FAMILY>_<#hex>`.

**warm_soft** — warm soft (pastel):
`#e8a87c #e6b8b0 #f0d8a8 #d9b8a3 #d4c5a0 #c9b7a3 #ead4b8 #e3c4a8 #dcc0a0 #e0cbb0 #d8c8b0`

**cool_soft** — cool soft (pastel):
`#a8c5a0 #8fbcd4 #b8a4c9 #9bb8a3 #a9a3c9 #c3d4c0 #a8bfd0 #b0c9b8 #9fb8c4 #bcb0d0 #a4bcc9`

**warm_bright** — warm bright:
`#f4a261 #e76f51 #e9c46a #bc4749 #bc6c25 #d97642 #c98a3f #d94f2b #e08544 #a83e2c #c25a35`

**cool_bright** — cool bright:
`#2a9d8f #3a6673 #8ab17d #6a994e #3d6a99 #7f63a8 #4d8fa8 #2f7a6b #5a4a8f #3a8fa0 #4a7d8f`

---

## Repository layout

```
mandala\                     # package source code (see README.md)
├── settings.py              # reads config.ini, applies it to Config
├── settings_dialog.py       # settings window (opens on every launch)
├── draw_session.py          # session: drawing window runs independently
├── app_paths.py             # data locations: mandalas, logs, config.ini
└── cairo_backend.py         # Cairo backend: pycairo (Windows) / cairocffi
mandala_app.py               # entry point of the packaged application
windows\
├── build_windows.bat        # one-command build
├── mandala.spec             # PyInstaller spec
├── installer\mandala.iss    # installer script (Inno Setup 6)
├── make_portable.ps1        # portable zip builder
├── update_cairo_dlls.ps1    # (optional) Cairo DLLs for the cairocffi route
├── requirements-win.txt     # build dependencies
├── icon.ico, version.txt
tests\test_settings.py       # settings module checks
.github\workflows\
└── build-windows.yml        # automatic build in GitHub Actions
```
