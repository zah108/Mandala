# CHANGELOG — Mandala Generator

This document describes what changed between the previous version of
the program and the current version (described in `README.md`).

The biggest change is a full architectural rework: the single-file
`turtle`-based script became a modular package rendered with
**Cairo**, with a reworked animation/speed system and direct vector
PDF export.

---

## 2.4 (unreleased)

- The settings window now opens on every launch. The "Показывать это окно
  при каждом запуске" checkbox was removed along with the
  `SHOW_SETTINGS_DIALOG` config key (the key is silently ignored in old
  `config.ini` files).
- "Рисовать" no longer closes the settings window: drawing runs in its own
  window while the settings stay open, so several mandalas can be drawn in
  a row. The close button of the drawing window only hides that window;
  the settings window closes only via its own close button. The app exits
  when both windows are closed.
- The "Сохранить" button is renamed to "Сохранить config.ini".
- Fixed: the drawing-speed slider was never initialized from `config.ini`
  (it always started at level 15 regardless of the file).
- The settings window re-reads `config.ini` when it regains focus after
  the file was edited externally.
- `config.ini` now lists every pattern weight (centers, bands, layers) and
  every palette color weight as an active editable line, instead of
  commented examples only.

## 2.3

- `config.ini` is no longer regenerated wholesale when saved from the
  settings window: known values are updated in place, while user comments,
  line order and unknown lines are preserved.
- The generated template now documents every pattern style (centers 1–11,
  bands 1–12, layers 1–17) next to the weight examples.
- New `[Веса цветов]` section: per-color palette weights (0 — excluded,
  2 — twice as likely), keys like `WARM_SOFT_#e8a87c`.
- README_Windows (EN) / README_Windows_RU (RU): appendix with the full
  style and palette reference.

## Windows distribution (2026-10-27)

New: a complete Windows build kit. The program now ships as an
`MandalaSetup.exe` installer (no Python required on the target machine)
plus a portable zip; drawing parameters are configurable without editing
code.

- `mandala/settings.py` — external `config.ini` applied over `config.py`
  (colors, speed, palette, ring sizes, `SAVE_FORMAT`, style weights).
  Invalid values are ignored with warnings; a commented Russian template
  is created on first run; settings are applied once per run (`ensure_applied`).
- `mandala/settings_dialog.py` — Tkinter settings window before drawing:
  speed slider with a time estimate, color mode, palette, save format,
  window size, line width, ring sizes; saves to `config.ini`.
- `mandala/app_paths.py` — data locations: installed → `Pictures\Mandala`
  for images, `%LOCALAPPDATA%` for logs, `%APPDATA%` for `config.ini`;
  portable mode (a `portable.ini` marker next to the exe) keeps everything
  next to the program; dev mode unchanged (`img/`, `log/` in the package).
- `mandala/cairo_backend.py` — Cairo backend selection: `pycairo` on
  Windows (the wheel bundles Cairo statically, no external DLLs),
  `cairocffi` for macOS/dev. Drawing code is untouched.
- `mandala_app.py` — frozen entry point: DPI awareness, Cairo DLL preload,
  settings window, crash log with a `crash-*.txt` file.
- `windows/` — build kit: `build_windows.bat` (bootstraps Python, deps,
  PyInstaller, Inno Setup, portable zip in one run), `mandala.spec`,
  `installer/mandala.iss` (per-user installer with Russian UI, shortcuts,
  uninstaller), `make_portable.ps1`, `update_cairo_dlls.ps1` (optional
  cairocffi route), `requirements-win.txt`, `icon.ico`, `version.txt`.
- `.github/workflows/build-windows.yml` — installer built automatically
  in GitHub Actions (manual dispatch or `v*` tags), artifact upload.
- `tests/test_settings.py` — 30 self-contained checks for the settings
  module (defaults, overrides, invalid values, weights, template round-trip).
- The package files moved into the `mandala/` folder, matching the layout
  already documented in the READMEs; `img/` and `log/` moved with it.
- New `README_Windows.md` (English) and `README_Windows_RU.md` (Russian):
  obtaining the installer via GitHub Actions or `build_windows.bat`, installation,
  parameters, data locations, troubleshooting.

---

## 1. Summary of changes

| Area | Previous version | Current version |
| --- | --- | --- |
| Code layout | One file, `mandala.py` | Package `mandala/` with 12 modules |
| Graphics | `turtle` (standard library) | Cairo (`cairocffi`) + Tkinter window |
| Animation | Turtle pen step batches with pauses | Recorded trajectory, pen moving at constant speed, a "bake" layer, merging fill arcs |
| Speed control | `DRAW_SPEED_LEVEL` 0–20 with a special value 9 ("instant"), pauses and batches of steps | Level 1–20 defines the drawing **duration**: 440 s (level 1) … 4 s (level 20), a linear scale with a step of ~23 s |
| PDF export | Through Ghostscript (EPS → PDF) | Directly via `cairo.PDFSurface` — **Ghostscript is no longer required** |
| PNG export | No | Added (`SAVE_FORMAT = "png"`) |
| Running | `python mandala.py` | `python -m mandala` (plus a "Run code" hack for VS Code) |
| Log file | `log/YYYY-MM-log.txt` | `log/YYYY-MM-mandala.log` |
| Python | 3.8+ | 3.9+ |
| Dependencies | `turtle`, `Pillow`, Ghostscript (optional) | `cairocffi`, `Pillow`, Tkinter (Ghostscript — not required) |

Pattern style counts are unchanged: **11 centers, 12 bands,
17 petal layers**. Geometry (`CIRCLE_RADIUS`, band and layer widths)
and the color system (4 palette families, `COLOR_MODE`,
`PALETTE_CHOICE`) remain conceptually the same.

---

## 2. Architecture: one file → package

Previously the whole program lived in a single `mandala.py`. Now it
is a package with clearly separated responsibilities:

```
mandala/
├── __init__.py          # package marker
├── __main__.py          # enables `python -m mandala`
├── main.py              # orchestrator
├── config.py            # Config class — all settings (imports nothing)
├── runtime.py           # Cairo scene, Tkinter window, turtle-like API,
│                        # animation manager, drawing speed, phase timing
├── traj.py              # trajectory elements: Line, Arc, Bezier,
│                        # FillElement (fill), StrokeElement (outline)
├── selection.py         # color and style selection
├── geometry.py          # shared drawing helpers
├── centers.py           # 11 center variants + SVG parser for Om
├── bands.py             # 12 band styles
├── layers.py            # 17 layer styles
├── logging_utils.py     # log formatting and writing
└── export.py            # saving the scene: PDF (Cairo) / PNG, JPG (PIL)
```

Dependency rules are strict: `config.py` does not import anything
from the project; `runtime.py` and `selection.py` depend only on
`config`; all modules are wired together in `main.py`.

---

## 3. Rendering engine: turtle → Cairo

**Before.** The mandala was drawn by the standard `turtle`: the pen
walked step by step, drawing speed was emulated with pauses and
batches (`pause ..., batch N steps`), export went through canvas
postscript → Ghostscript.

**Now.** All drawing goes to a **vector Cairo scene** (`Scene`):
strokes and fills are recorded as operations, and the same scene is
rendered two ways:

1. **In the window** — as an animation (`AnimationManager` +
   a baked layer): smooth Cairo lines, fills appear at the moment
   the pen passes through their point, constant per-frame cost
   (completed elements are baked once, only the current partial
   element is redrawn).
2. **To a file** — direct vector PDF via `cairo.PDFSurface`, or
   raster PNG/JPG via PIL.

`runtime.py` keeps a turtle-compatible API (`goto`, `penup`,
`pendown`, `begin_fill`, `circle`, ...) for compatibility with the
previously developed drawing code.

Additional improvements:

- **Merging consecutive fill arcs** into a single circular contour —
  removes seams between adjacent arcs during fills.
- **Petal bases fixed**: in layer styles 1, 10, 11, 13, 14, 15 the
  base contour now sits exactly on the boundary circle (previously
  it was lifted by a radial padding).

---

## 4. New speed system

The speed control has been reworked and now operates in terms of
**drawing duration**, not steps/batches.

### Before

```python
DRAW_SPEED_LEVEL = 8   # 0–8 (fast), 9 (instant), 10–20 (smooth)
```

- The level meant pauses between pen batches; the log recorded
  `(pause 0.00000 s, batch 15 steps)`.
- Level 9 was a special "instant" value.
- Actual drawing time depended on the pattern.

### Now

```python
DRAW_SPEED_LEVEL = 10        # 1..20, default 10
SPEED_DURATION_MAX_S = 440.0 # duration at level 1 (~7 min 20 s)
SPEED_DURATION_MIN_S = 4.0   # duration at level 20 (~4 s)
SPEED_FPS = 60               # target frame rate
```

- The level defines the **duration** of the drawing: a linear scale
  with a constant step of ≈23 s (level 10 ≈ 3 min 54 s).
- The real speed (px/s) is computed from the actual trajectory
  length before the animation starts, so **the duration does not
  depend on the particular pattern**.
- The pen moves at a constant speed regardless of element type;
  the animation timer starts when the window opens.
- Geometry and colors do not depend on the level — only the display
  tempo changes.

### Migrating speed settings

| Old value | Approximate equivalent now |
| --- | --- |
| 0–8 (fast) | 15–20 |
| 9 (instant) | 20 |
| 10–20 (smooth) | 3–10 (10 ≈ 4 min default; each step ± ≈ 23 s) |

Log line changed accordingly:
`Drawing speed: 10 of 20` (was
`Drawing speed: 8 (pause 0.00000 s, batch 15 steps)`).

---

## 5. Export changes

- **Ghostscript is no longer required.** The PDF is written
  directly by Cairo (`cairo.PDFSurface`) — vector output without
  EPS intermediates.
- **PNG support added**: `SAVE_FORMAT = "png" | "jpg"` via Pillow
  (previously only `"pdf"` / `"jpg"`).
- Output directory and file naming are the same:
  `img/YYYY-MM-DD-mandala-HHMMSS.<ext>`.

Removed the "Ghostscript not found" troubleshooting section —
impossible by design now. Requirements for PDF: only
`pip install cairocffi` (+ `libcairo`, on macOS
`brew install cairo`).

---

## 6. Configuration changes

The `Config` class now lives in `mandala/config.py`. Parameters:

### Added

| Parameter | Default | Purpose |
| --- | --- | --- |
| `SPEED_DURATION_MAX_S` | `440.0` | Drawing duration at speed level 1 |
| `SPEED_DURATION_MIN_S` | `4.0` | Drawing duration at speed level 20 |
| `SPEED_FPS` | `60` | Target screen refresh rate |

### Changed defaults

| Parameter |
| --- | --- | --- |
| `DRAW_SPEED_LEVEL` | `9` (instant) | `10` (≈ 4 min, duration scale) |
| `PALETTE_CHOICE` | `"all"` | `"random"` |

### Removed (internal, no longer documented)

`DRAW_OUTER_RING`, `OUTER_RING_RADIUS`, `BBOX_PADDING`,
`SPEED_STEP_PX` — obsolete after the switch to the Cairo scene and
the duration scale.

### Unchanged

`COLOR_MODE`, `PALETTE_CHOICE` values, `CIRCLE_RADIUS`,
`BAND1..5_WIDTH`, `L1..5_WIDTH`, `WINDOW_SIZE`, `SAVE_FORMAT`,
`TIMING_ENABLED`, `PAINT_LAYER_RINGS` keep the same semantics.

---

## 7. Logging changes

- Log file renamed: `log/YYYY-MM-log.txt` → `log/YYYY-MM-mandala.log`.
- The speed line no longer shows pause/batch:
  `Drawing speed: 10 of 20`.
- The start entry additionally records the speed level (see above);
  everything else — selected styles per area, colors, fallback
  warnings, end status, optional phase timings — is preserved.
- The timing block (`TIMING_ENABLED = True`) has the same purpose;
  phases are recorded with `_tmark(...)` in `main.py`.

---

## 8. Running and development workflow

- The canonical launch is now `python -m mandala` from the project
  root (or `python -m mandala.main`).
- `mandala/main.py` still works **directly** (VS Code "Run code"):
  it re-launches itself as `python -m mandala.main` via
  `subprocess.run` with unbuffered stdio — output remains visible
  in the VS Code terminal (do not replace it with `os.execv`).
- The old dependency `/requirements.txt` install step is gone;
  requirements are: `cairocffi`, `pillow` (`pip install`), Tkinter
  from the Python bundle, and `libcairo` from the system package
  manager on macOS/Linux.

---

## 9. Documentation

The documentation has been rewritten from scratch in `README.md`
and now describes realistically the current architecture:

- project structure and module responsibilities,
- dependency graph,
- the full flow of `main.main()`,
- the new animation and speed section,
- complete parameter tables (defaults),
- pattern style catalogs (11 / 12 / 17),
- color selection rules (hard/soft/recent restrictions, fallback
  warnings),
- saving and logging,
- VS Code launch recipes and FAQ.

---

## 10. Migration checklist

1. Replace the old `mandala.py` with the `mandala/` package.
2. Install dependencies: `pip install cairocffi pillow`
   (on macOS: `brew install cairo`).
3. Uninstall/lgnore Ghostscript — no longer used.
4. Move your `Config` edits into `mandala/config.py`:
   - speeds: use the new duration scale (see the mapping table in
     section 4);
   - `PALETTE_CHOICE` default changed to `"random"` — set it
     explicitly if you relied on `"all"`.
5. Run with `python -m mandala` from the project root. Old log
   files remain valid; new entries go to `log/YYYY-MM-mandala.log`.
