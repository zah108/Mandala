"""Проверки модуля настроек mandala.settings.

Запуск из корня проекта:  python3 tests/test_settings.py
Зависимостей не требует (кроме PIL для проверки цветов — опционально).
"""
import copy
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mandala import settings          # noqa: E402
from mandala.config import Config     # noqa: E402

FAILED = []


def check(condition, message):
    if condition:
        print(f"  ok    {message}")
    else:
        FAILED.append(message)
        print(f"  FAIL  {message}")


def temp_ini(text):
    fd, path = tempfile.mkstemp(suffix=".ini")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def section(title):
    print(f"\n=== {title} ===")


# 1. Значения по умолчанию -------------------------------------------------
section("Значения по умолчанию (config.py, без config.ini)")
missing = os.path.join(tempfile.mkdtemp(), "net-faila.ini")
warn = settings.apply_user_settings(ini_path=missing)
check(warn == [], "без файла нет предупреждений")
check(Config.BG_COLOR == "white" and Config.LINE_COLOR == "black", "цвета по умолчанию")
check(Config.DRAW_SPEED_LEVEL == 15, "скорость по умолчанию 15")
check(Config.WINDOW_SIZE == 1000, "окно 1000")

# 2. Корректные переопределения -------------------------------------------
section("Корректные переопределения")
good = {
    "DRAW_SPEED_LEVEL": 7,
    "WINDOW_SIZE": 800,
    "COLOR_MODE": "no",
    "PALETTE_CHOICE": "warm_bright",
    "SAVE_FORMAT": "png",
    "LINE_COLOR": "#123456",
    "BG_COLOR": "black",
    "LINE_WIDTH": 2.5,
    "PAINT_LAYER_RINGS": "false",
    "TIMING_ENABLED": "TRUE",
}
warn = settings.apply_user_settings(overrides=good, ini_path=missing)
check(warn == [], f"нет предупреждений (получено: {warn})")
check(Config.DRAW_SPEED_LEVEL == 7, "скорость 7")
check(Config.WINDOW_SIZE == 800, "окно 800")
check(Config.COLOR_MODE == "no" and Config.PALETTE_CHOICE == "warm_bright", "режим раскраски и палитра")
check(Config.SAVE_FORMAT == "png", "формат png")
check(Config.LINE_COLOR == "#123456", "цвет линии применён")
check(Config.LINE_WIDTH == 2.5, "толщина линии")
check(Config.PAINT_LAYER_RINGS is False and Config.TIMING_ENABLED is True, "логические флаги (регистр не важен)")

# 3. Некорректные значения -------------------------------------------------
section("Некорректные значения")
warn = settings.apply_user_settings(
    overrides={"DRAW_SPEED_LEVEL": "abc", "WINDOW_SIZE": "3000",
               "COLOR_MODE": "sometimes", "BG_COLOR": "darker"},
    ini_path=missing)
check(len(warn) == 4, f"четыре предупреждения (получено {len(warn)}: {warn})")
check(Config.DRAW_SPEED_LEVEL == 15, "скорость откатилась к 15")
check(Config.WINDOW_SIZE == 2000, "окно обрезано до 2000")
check(Config.COLOR_MODE == "yes", "режим раскраски по умолчанию")
check(Config.BG_COLOR == "white", "цвет фона по умолчанию")

# 4. Веса стилей из ini ----------------------------------------------------
section("Веса стилей")
ini = temp_ini(
    "[Веса стилей]\n"
    "CENTER_7 = 0\n"
    "band_3 = 2.5\n"
    "LAYER_99 = 1\n"
    "CENTER_X = abc\n"
)
warn = settings.apply_user_settings(ini_path=ini)
check(any("LAYER_99" in w for w in warn), "несуществующий стиль даёт предупреждение")
check(any("CENTER_X" in w for w in warn), "нечисловой вес даёт предупреждение")
check(Config.CENTER_STYLES[7]["weight"] == 0.0, "вес центра 7 = 0 (узор выключен)")
check(Config.BAND_STYLES[3]["weight"] == 2.5, "вес ленты 3 = 2.5 (регистр не важен)")
check(len(settings._DEFAULTS) > 20, "снимок умолчаний сделан")

# 5. Шаблон config.ini: обратная совместимость -----------------------------
section("Шаблон config.ini")
settings.apply_user_settings(ini_path=missing)  # сброс
tpl = temp_ini(settings.template_text())
warn = settings.apply_user_settings(ini_path=tpl)
check(warn == [], f"шаблон читается без предупреждений (получено: {warn})")
check(Config.DRAW_SPEED_LEVEL == 15 and Config.BG_COLOR == "white", "значения из шаблона совпали с умолчаниями")
text = open(tpl, encoding="utf-8-sig").read()
check("[Общие]" in text and "[Веса стилей]" in text, "в шаблоне есть все секции")
check("DRAW_SPEED_LEVEL = 15" in text, "в шаблоне есть активные параметры")
check("Радиальные лучи" in text and "Солнце" in text, "в шаблоне есть справочник центров")
check("[Веса цветов]" in text, "в шаблоне есть секция весов цветов")
check("SHOW_SETTINGS_DIALOG" not in text, "устаревший параметр в шаблон не пишется")
check(any(l.startswith("CENTER_1 = 1") and "Радиальные лучи" in l for l in text.splitlines()),
      "в шаблоне названия узоров стоят в комментариях справа от весов")
weight_lines = [l for l in text.splitlines()
                if l and not l.startswith((";", "#"))
                and any(l.startswith(p) for p in ("CENTER_", "BAND_", "LAYER_"))]
total_styles = (len(Config.CENTER_STYLES) + len(Config.BAND_STYLES)
                + len(Config.LAYER_STYLES))
check(len(weight_lines) == total_styles,
      f"все {total_styles} весов узоров в шаблоне активны (найдено {len(weight_lines)})")
total_colors = sum(len(d["colors"]) for d in Config.COLOR_FAMILIES.values())
color_lines = [l for l in text.splitlines()
               if l and not l.startswith((";", "#")) and "_#" in l and " = " in l]
check(len(color_lines) == total_colors,
      f"все {total_colors} цветов в шаблоне активны (найдено {len(color_lines)})")
check("WARM_SOFT_#e8a87c = 1" in text and "; WARM_SOFT_" not in text,
      "цвета перечислены активными строками, без закомментированных примеров")
check(any(l.startswith("CENTER_1 = 1") and "Радиальные лучи" in l
          for l in text.splitlines()),
      "у веса центра указано название узора (инлайн-комментарий)")
check(any(l.startswith("WARM_SOFT_#e8a87c = 1") and "Тёплое-мягкое" in l
          for l in text.splitlines()),
      "у веса цвета указано семейство (инлайн-комментарий)")

# 5a. Устаревший ключ игнорируется молча ----------------------------------
legacy = temp_ini("[Общие]\nSHOW_SETTINGS_DIALOG = true\n")
warn = settings.apply_user_settings(ini_path=legacy)
check(warn == [],
      f"устаревший SHOW_SETTINGS_DIALOG игнорируется молча (получено: {warn})")

# 5b. Инлайн-комментарий «;» после значения --------------------------------
ini_inline = temp_ini("[Рисование]\nDRAW_SPEED_LEVEL = 9 ; девять\n"
                      "BG_COLOR = black ; тёмный фон\n")
warn = settings.apply_user_settings(ini_path=ini_inline)
check(warn == [] and Config.DRAW_SPEED_LEVEL == 9 and Config.BG_COLOR == "black",
      f"инлайн-комментарий «;» после значения корректен (получено: {warn})")

# 6. save_values сохраняет и восстанавливает -------------------------------
section("save_values")
out = temp_ini("")
settings.apply_user_settings(overrides={"DRAW_SPEED_LEVEL": 3, "PALETTE_CHOICE": "cool_bright"},
                             ini_path=missing)
settings.save_values({"DRAW_SPEED_LEVEL": "3", "PALETTE_CHOICE": "cool_bright",
                      "WINDOW_SIZE": "700", "COLOR_MODE": "yes"}, path=out)
warn = settings.apply_user_settings(ini_path=out)
check(warn == [], f"сохранённый файл читается без предупреждений (получено: {warn})")
check(Config.DRAW_SPEED_LEVEL == 3 and Config.WINDOW_SIZE == 700, "значения после перечитывания")
check(Config.CENTER_STYLES[7]["weight"] == 1.0, "веса вернулись к 1.0 (не сохранялись)")

# 7. app_paths -------------------------------------------------------------
section("app_paths (dev-режим)")
from mandala import app_paths  # noqa: E402
check(app_paths.is_frozen() is False, "dev: not frozen")
check(app_paths.images_dir().endswith("img"), "dev: img внутри пакета")
check(app_paths.logs_dir().endswith("log"), "dev: log внутри пакета")
check(app_paths.config_path().endswith("config.ini"), "путь config.ini корректен")

# 8. Веса цветов -----------------------------------------------------------
section("Веса цветов")
ini_colors = temp_ini(
    "[Веса цветов]\n"
    "WARM_SOFT_#E8A87C = 0\n"
    "COOL_BRIGHT_#2a9d8f = 2.5\n"
    "WARM_BRIGHT_#неттакого = 2\n"
)
warn = settings.apply_user_settings(ini_path=ini_colors)
check(any("неттакого" in w.lower() for w in warn), "несуществующий цвет даёт предупреждение")
target = [c for c in Config.COLOR_FAMILIES["warm_soft"]["colors"]
          if c["hex"] == "#e8a87c"][0]
check(target["weight"] == 0.0, "вес цвета применён (hex без учёта регистра)")
check(Config.COLOR_FAMILIES["cool_bright"]["colors"][0]["weight"] == 2.5,
      "вес 2.5 применён к другому семейству")
warn = settings.apply_user_settings(ini_path=missing)
check(Config.COLOR_FAMILIES["warm_soft"]["colors"][0]["weight"] == 1.0,
      "сброс к умолчаниям возвращает вес цвета")

# 9. Недеструктивное сохранение -------------------------------------------
section("Недеструктивная запись (save_values)")
work = temp_ini("")
custom = (
    "[Общие]\n"
    "WINDOW_SIZE = 900\n"
    "; мой любимый комментарий\n"
    "MY_EXPERIMENT = hello\n"
    "\n"
    "[Веса стилей]\n"
    "CENTER_2 = 3.0\n"
    "BAND_1 = 2   ; мой узор\n"
    "; CENTER_3 = 1.0\n"
)
with open(work, "w", encoding="utf-8") as f:
    f.write(custom)
warn = settings.apply_user_settings(ini_path=work)
check(any("MY_EXPERIMENT" in w for w in warn),
      "незнакомый ключ даёт предупреждение при чтении")
settings.save_values({"DRAW_SPEED_LEVEL": "9"}, path=work)
text2 = open(work, encoding="utf-8-sig").read()
check("; мой любимый комментарий" in text2, "комментарий пользователя сохранён")
check("MY_EXPERIMENT = hello" in text2, "незнакомый ключ сохранён")
check("WINDOW_SIZE = 900" in text2, "нетронутое значение не изменено")
check("DRAW_SPEED_LEVEL = 9" in text2, "новое значение дописано")
check(any(line.strip() in ("CENTER_2 = 3", "CENTER_2 = 3.0")
          for line in text2.splitlines()), "активный вес стиля сохранён")
check("; CENTER_3 = 1.0" in text2, "закомментированный пример не тронут")
check(any(l.startswith("BAND_1 = 2") and "мой узор" in l for l in text2.splitlines()),
      "инлайн-комментарий пользователя сохранён при записи")
check("\nCENTER_3 = 1    ; Спираль" in text2,
      "дописанным весам добавлены названия узоров")
warn = settings.apply_user_settings(ini_path=work)
check(Config.DRAW_SPEED_LEVEL == 9 and Config.WINDOW_SIZE == 900,
      "всё перечитывается после сохранения")
check(Config.CENTER_STYLES[2]["weight"] == 3.0,
      "вес стиля перечитался после сохранения")

print("\n" + "=" * 50)
if FAILED:
    print(f"ПРОВАЛЕНО: {len(FAILED)}")
    for m in FAILED:
        print(" -", m)
    sys.exit(1)
print("ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
