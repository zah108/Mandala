"""Окно настроек перед рисованием (только стандартный Tkinter).

Модуль НЕ импортирует runtime — его можно открывать до рабочего окна:
рисующее окно создаётся позже, в mandala.main.

Окно читает текущие значения Config (после применения config.ini),
по кнопке «Рисовать»/«Сохранить» пишет их в config.ini и заново
применяет к Config. Весов стилей в окне нет — они правятся в файле.
"""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

from . import app_paths, settings

_COLOR_MODE_LABELS = (
    ("yes", "Всегда раскрашивать"),
    ("no", "Только контуры"),
    ("random", "Случайно при запуске"),
)
_PALETTE_LABELS = (
    ("random", "Случайно при запуске"),
    ("all", "Все семейства вместе"),
    ("warm_soft", "Тёплое мягкое (пастель)"),
    ("cool_soft", "Холодное мягкое (пастель)"),
    ("warm_bright", "Тёплое яркое"),
    ("cool_bright", "Холодное яркое"),
)
_FORMAT_LABELS = (("pdf", "PDF (вектор)"), ("png", "PNG"), ("jpg", "JPG"))

_RING_FIELDS = (
    ("CIRCLE_RADIUS", "Радиус центра"),
    ("BAND1_WIDTH", "Лента 1"),
    ("L1_WIDTH", "Слой 1"),
    ("BAND2_WIDTH", "Лента 2"),
    ("L2_WIDTH", "Слой 2"),
    ("BAND3_WIDTH", "Лента 3"),
    ("L3_WIDTH", "Слой 3"),
    ("BAND4_WIDTH", "Лента 4"),
    ("L4_WIDTH", "Слой 4"),
    ("BAND5_WIDTH", "Лента 5"),
    ("L5_WIDTH", "Слой 5"),
)


def _open_in_explorer(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass
    if hasattr(os, "startfile"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


class SettingsDialog(tk.Tk):
    """result=True — пользователь попросил рисовать."""

    def __init__(self, warnings=()):
        super().__init__()
        self.title("Мандала — настройки рисования")
        self.resizable(False, False)
        self.result = False
        self._vars = {}

        outer = ttk.Frame(self, padding=(12, 10))
        outer.grid(row=0, column=0, sticky="nsew")

        main = ttk.LabelFrame(outer, text=" Основное ", padding=(10, 6))
        main.grid(row=0, column=0, sticky="ew")
        rings = ttk.LabelFrame(outer, text=" Размеры колец (продвинутые) ",
                               padding=(10, 6))
        rings.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        self._build_main(main)
        self._build_rings(rings)
        self._build_bottom(outer, warnings)

        self._load_values()
        self._center()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    # ------------------------------------------------ построение
    def _build_main(self, frame):
        row = 0
        ttk.Label(frame, text="Скорость рисования:").grid(
            row=row, column=0, sticky="w")
        speed_box = ttk.Frame(frame)
        speed_box.grid(row=row, column=1, sticky="ew", padx=(8, 0))
        # Сначала лейбл: scale.set() ниже сразу вызывает command-обратный вызов.
        self._speed_value = ttk.Label(speed_box, text="", width=16)
        self._speed_value.grid(row=0, column=1, padx=(8, 0))
        self._speed_scale = ttk.Scale(
            speed_box, from_=1, to=20, orient="horizontal", length=230,
            command=self._on_speed_change)
        self._speed_scale.set(15)
        self._speed_scale.grid(row=0, column=0)
        row += 1

        ttk.Label(frame, text="Раскраска:").grid(row=row, column=0, sticky="w")
        self._combo("COLOR_MODE", _COLOR_MODE_LABELS, frame, row)
        row += 1

        ttk.Label(frame, text="Палитра:").grid(row=row, column=0, sticky="w")
        self._combo("PALETTE_CHOICE", _PALETTE_LABELS, frame, row)
        row += 1

        ttk.Label(frame, text="Сохранять как:").grid(row=row, column=0, sticky="w")
        self._combo("SAVE_FORMAT", _FORMAT_LABELS, frame, row)
        row += 1

        ttk.Label(frame, text="Окно, px (400–2000):").grid(
            row=row, column=0, sticky="w")
        self._spin("WINDOW_SIZE", 400, 2000, 50, frame, row)
        row += 1

        ttk.Label(frame, text="Толщина линии (0.1–20):").grid(
            row=row, column=0, sticky="w")
        self._spin("LINE_WIDTH", 0.1, 20.0, 0.5, frame, row)

        frame.columnconfigure(1, weight=1)

    def _combo(self, key, pairs, frame, row):
        label_of = {value: label for value, label in pairs}
        value_of = {label: value for value, label in pairs}
        var = tk.StringVar()
        combo = ttk.Combobox(
            frame, textvariable=var, values=[label for _v, label in pairs],
            state="readonly", width=28)
        combo.grid(row=row, column=1, sticky="w", padx=(8, 0))
        var._values = value_of
        var._labels = label_of
        self._vars[key] = var

    def _spin(self, key, low, high, increment, frame, row):
        var = tk.StringVar()
        spin = ttk.Spinbox(
            frame, from_=low, to=high, increment=increment,
            textvariable=var, width=8)
        spin.grid(row=row, column=1, sticky="w", padx=(8, 0))
        self._vars[key] = var

    def _build_rings(self, frame):
        for index, (key, label) in enumerate(_RING_FIELDS):
            row, col = divmod(index, 3)
            ttk.Label(frame, text=f"{label}:").grid(
                row=row, column=col * 2, sticky="e", padx=(0 if col == 0 else 12, 3),
                pady=2)
            var = tk.StringVar()
            ttk.Entry(frame, textvariable=var, width=7).grid(
                row=row, column=col * 2 + 1, sticky="w", pady=2)
            self._vars[key] = var

    def _build_bottom(self, outer, warnings):
        self._show_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            outer, text="Показывать это окно при каждом запуске",
            variable=self._show_var).grid(row=2, column=0, sticky="w", pady=(10, 0))

        buttons = ttk.Frame(outer)
        buttons.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        draw = ttk.Button(buttons, text="Рисовать", command=self._on_draw)
        draw.grid(row=0, column=0)
        self.bind("<Return>", lambda event: self._on_draw())
        ttk.Button(buttons, text="Сохранить", command=self._on_save).grid(
            row=0, column=1, padx=6)
        ttk.Button(buttons, text="Отмена", command=self._on_cancel).grid(
            row=0, column=2)

        links = ttk.Frame(outer)
        links.grid(row=4, column=0, sticky="w", pady=(10, 0))
        ttk.Button(links, text="Открыть папку с мандалами", style="Link.TButton",
                   command=lambda: _open_in_explorer(app_paths.images_dir())
                   ).grid(row=0, column=0)
        ttk.Button(links, text="Открыть config.ini", style="Link.TButton",
                   command=self._open_config).grid(row=0, column=1, padx=(10, 0))

        self._status = tk.Label(outer, text="", fg="#555555",
                                wraplength=460, justify="left")
        self._status.grid(row=5, column=0, sticky="w", pady=(8, 0))
        if warnings:
            self._set_status(
                "Замечания по config.ini (применены значения по умолчанию):\n- "
                + "\n- ".join(warnings), "#a05000")

    # ------------------------------------------------ значения
    def _load_values(self):
        values = settings.current_values()
        for key, var in self._vars.items():
            if key == "DRAW_SPEED_LEVEL":
                self._speed_scale.set(float(values.get(key, "15")))
                self._refresh_speed_label()
                continue
            if key == "SHOW_SETTINGS_DIALOG":
                self._show_var.set(values.get(key, "true").lower() == "true")
                continue
            raw = values.get(key, "")
            if hasattr(var, "_labels"):
                var.set(var._labels.get(raw.lower(), raw))
            else:
                var.set(raw)

    def _refresh_speed_label(self):
        level = int(round(float(self._speed_scale.get())))
        seconds = settings.duration_for_level(level)
        self._speed_value.config(text=f"уровень {level}  ≈ {seconds:.0f} c")

    def _on_speed_change(self, _value):
        self._refresh_speed_label()

    def _collect(self):
        """Собирает и локально проверяет значения. -> (dict, ошибки)."""
        values, errors = {}, []
        for key, var in self._vars.items():
            if hasattr(var, "_values"):
                raw = var.get().strip()
                mapped = var._values.get(raw)
                if mapped is None:
                    errors.append(f"{key}: выбрано неверное значение")
                else:
                    values[key] = mapped
                continue
            raw = str(var.get()).strip()
            rule = settings._PARAMS[key][1]
            if rule == "bool":
                parsed = settings._parse_bool(raw)
                if parsed is None:
                    errors.append(f"{key}: ожидалось true/false")
                else:
                    values[key] = "true" if parsed else "false"
                continue
            if rule == "color":
                if settings._parse_color(raw) is None:
                    errors.append(f"{key}: некорректный цвет «{raw}»")
                else:
                    values[key] = raw
                continue
            if isinstance(rule, tuple) and rule[0] == "choice":
                parsed = settings._parse_choice(raw, rule[1])
                if parsed is None:
                    errors.append(f"{key}: допустимо {', '.join(rule[1])}")
                else:
                    values[key] = parsed
                continue
            _, low, high = rule
            try:
                parsed, _corrected = settings._clamp(raw, rule[0], low, high)
                values[key] = settings.fmt_value(parsed)
            except (TypeError, ValueError):
                errors.append(f"{key}: ожидалось число, получено «{raw}»")

        values["DRAW_SPEED_LEVEL"] = str(
            max(1, min(20, int(round(float(self._speed_scale.get()))))))
        values["SHOW_SETTINGS_DIALOG"] = (
            "true" if self._show_var.get() else "false")
        return values, errors

    # ------------------------------------------------ действия
    def _save(self):
        values, errors = self._collect()
        if errors:
            self._set_status("Не сохранено:\n- " + "\n- ".join(errors), "#b02020")
            return False
        try:
            path = settings.save_values(values)
            settings.apply_user_settings()
        except OSError as exc:
            self._set_status(f"Не удалось записать config.ini: {exc}", "#b02020")
            return False
        self._set_status(f"Сохранено: {path}", "#207040")
        return True

    def _on_draw(self):
        if self._save():
            self.result = True
            self.destroy()

    def _on_save(self):
        self._save()

    def _on_cancel(self):
        self.result = False
        self.destroy()

    def _open_config(self):
        path = app_paths.config_path()
        if not os.path.exists(path):
            try:
                path = settings.write_template(path)
            except OSError as exc:
                self._set_status(f"Не удалось создать config.ini: {exc}", "#b02020")
                return
        if hasattr(os, "startfile"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _set_status(self, text, color):
        self._status.config(text=text, fg=color)

    def _center(self):
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 3)
        self.geometry(f"+{x}+{y}")


def run(warnings=()):
    """Показывает окно. True — рисовать, False — завершить приложение."""
    try:
        dialog = SettingsDialog(warnings)
        dialog.mainloop()
        return bool(dialog.result)
    except tk.TclError as exc:
        # Нет дисплея или сломан Tk — не мешаем рисовать.
        print(f"Окно настроек недоступно: {exc}")
        return True
