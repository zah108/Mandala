"""Формирование лога генерации мандалы и запись в файл."""
import datetime
import os


def format_colors(colors):
    if not colors:
        return ""
    if len(colors) == 1:
        return f" [цвет: {colors[0]}]"
    return " [цвета: " + " ".join(colors) + "]"


def format_layer_colors(petal_colors, ring_color):
    parts = []
    if petal_colors:
        if len(petal_colors) == 1:
            parts.append(f"лепесток: {petal_colors[0]}")
        else:
            parts.append("лепестки: " + " ".join(petal_colors))
    if ring_color:
        parts.append(f"кольцо: {ring_color}")
    if not parts:
        return ""
    return " [" + "; ".join(parts) + "]"


def setup_log_path():
    import sys
    # Windows build (PyInstaller) adaptation: log/ рядом с exe вместо _internal
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    month_str = datetime.datetime.now().strftime("%Y-%m")
    return os.path.join(log_dir, f"{month_str}-mandala.log")


def build_start_log(style_center, band_styles, layer_styles, palette,
                    color_enabled, color_mode, family_log, draw_speed_level,
                    draw_duration_s, fallback_warnings):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.datetime.now().strftime("%H:%M:%S")

    sb1, sb2, sb3, sb4, sb5 = band_styles
    sl1, sl2, sl3, sl4, sl5 = layer_styles

    from .config import Config

    report = (
        f"==================================================\n"
        f"Генерация Мандалы\n"
        f"Дата: {date_str} | Время старта: {time_str}\n"
        f"Раскраска: {'включена' if color_enabled else 'выключена'} "
        f"(режим: {color_mode})\n"
        f"Семейство цветов: {family_log}\n"
        f"Скорость рисования: {draw_speed_level} из 20\n"
        f"--------------------------------------------------\n"
        f" Выбранные узоры по областям:\n"
        f"  1. Центральный круг:      Вариант {style_center} ({Config.CENTER_STYLES[style_center]['name']})"
        f"{format_colors(palette['center'])}\n"
        f"  2. Разделительная лента 1: Вариант {sb1} ({Config.BAND_STYLES[sb1]['name']})"
        f"{format_colors(palette['band1'])}\n"
        f"  3. Уровень 1:              Вариант {sl1} ({Config.LAYER_STYLES[sl1]['name']})"
        f"{format_layer_colors(palette['layer1'], palette['ring1'])}\n"
        f"  4. Разделительная лента 2: Вариант {sb2} ({Config.BAND_STYLES[sb2]['name']})"
        f"{format_colors(palette['band2'])}\n"
        f"  5. Уровень 2:              Вариант {sl2} ({Config.LAYER_STYLES[sl2]['name']})"
        f"{format_layer_colors(palette['layer2'], palette['ring2'])}\n"
        f"  6. Разделительная лента 3: Вариант {sb3} ({Config.BAND_STYLES[sb3]['name']})"
        f"{format_colors(palette['band3'])}\n"
        f"  7. Уровень 3:              Вариант {sl3} ({Config.LAYER_STYLES[sl3]['name']})"
        f"{format_layer_colors(palette['layer3'], palette['ring3'])}\n"
        f"  8. Разделительная лента 4: Вариант {sb4} ({Config.BAND_STYLES[sb4]['name']})"
        f"{format_colors(palette['band4'])}\n"
        f"  9. Уровень 4:              Вариант {sl4} ({Config.LAYER_STYLES[sl4]['name']})"
        f"{format_layer_colors(palette['layer4'], palette['ring4'])}\n"
        f" 10. Разделительная лента 5: Вариант {sb5} ({Config.BAND_STYLES[sb5]['name']})"
        f"{format_colors(palette['band5'])}\n"
        f" 11. Уровень 5:              Вариант {sl5} ({Config.LAYER_STYLES[sl5]['name']})"
        f"{format_layer_colors(palette['layer5'], palette['ring5'])}\n"
        f"--------------------------------------------------\n"
    )
    if fallback_warnings:
        report += (
            "Предупреждения раскраски (fallback):\n  - "
            + "\n  - ".join(fallback_warnings)
            + "\n--------------------------------------------------\n"
        )
    return report


def write_start_log(log_path, report):
    print(report)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(report)


def build_end_log(out_path_or_error, end_time_str):
    return (f" Статус: {out_path_or_error}\n"
            f" Время окончания: {end_time_str} #\n"
            f"==================================================\n\n")


def write_end_log(log_path, report, timing_msg=""):
    print(report)
    if timing_msg:
        print(timing_msg)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(report)
        if timing_msg:
            f.write(timing_msg + "\n")