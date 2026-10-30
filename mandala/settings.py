"""Пользовательские настройки поверх config.py.

Принцип: значения по умолчанию всегда берутся из ``config.py``.
Дополнительно читается ``config.ini`` (см. ``app_paths.config_path()``)
и корректные значения применяются к атрибутам класса ``Config``.
Некорректные значения игнорируются с предупреждением — приложение
запускается всегда.

В собранном приложении шаблон ``config.ini`` с русскими комментариями
создаётся автоматически при первом запуске; тот же файл правит
окно настроек (``settings_dialog.py``).
"""
import configparser
import copy
import os
import re

from . import app_paths
from .config import Config

# Снимок значений по умолчанию из config.py. Делается один раз при импорте
# модуля — до того, как какие-либо настройки будут применены.
_DEFAULTS = {
    key: copy.deepcopy(value)
    for key, value in vars(Config).items()
    if not (key.startswith("__") and key.endswith("__"))
}

_PALETTES = ("random", "all", "warm_soft", "cool_soft", "warm_bright", "cool_bright")

# ключ -> (секция файла, правило проверки)
#   ("int", min, max) / ("float", min, max) / ("choice", (варианты...))
#   "bool" / "color"
_PARAMS = {
    "WINDOW_SIZE": ("Общие", ("int", 400, 2000)),
    "PAINT_LAYER_RINGS": ("Общие", "bool"),
    "TIMING_ENABLED": ("Общие", "bool"),

    "BG_COLOR": ("Рисование", "color"),
    "LINE_COLOR": ("Рисование", "color"),
    "LINE_WIDTH": ("Рисование", ("float", 0.1, 20.0)),
    "DRAW_SPEED_LEVEL": ("Рисование", ("int", 1, 20)),

    "COLOR_MODE": ("Раскраска", ("choice", ("yes", "no", "random"))),
    "PALETTE_CHOICE": ("Раскраска", ("choice", _PALETTES)),

    "CIRCLE_RADIUS": ("Размеры", ("float", 1.0, 300.0)),
    "BAND1_WIDTH": ("Размеры", ("float", 0.5, 100.0)),
    "L1_WIDTH": ("Размеры", ("float", 1.0, 300.0)),
    "BAND2_WIDTH": ("Размеры", ("float", 0.5, 100.0)),
    "L2_WIDTH": ("Размеры", ("float", 1.0, 300.0)),
    "BAND3_WIDTH": ("Размеры", ("float", 0.5, 100.0)),
    "L3_WIDTH": ("Размеры", ("float", 1.0, 300.0)),
    "BAND4_WIDTH": ("Размеры", ("float", 0.5, 100.0)),
    "L4_WIDTH": ("Размеры", ("float", 1.0, 300.0)),
    "BAND5_WIDTH": ("Размеры", ("float", 0.5, 100.0)),
    "L5_WIDTH": ("Размеры", ("float", 1.0, 300.0)),

    "SAVE_FORMAT": ("Сохранение", ("choice", ("pdf", "png", "jpg", "jpeg"))),
}

_SECTION_ORDER = ("Общие", "Рисование", "Раскраска", "Размеры", "Сохранение")
_WEIGHT_SECTION = "Веса стилей"
_COLOR_WEIGHT_SECTION = "Веса цветов"

# префикс ключа веса -> словарь стилей Config
_WEIGHT_TARGETS = (
    ("CENTER_", "CENTER_STYLES"),
    ("BAND_", "BAND_STYLES"),
    ("LAYER_", "LAYER_STYLES"),
)

_COMMENTS = {
    "WINDOW_SIZE": "Размер окна рисования в пикселях (400..2000)",
    "PAINT_LAYER_RINGS": "Раскрашивать кольца вокруг слоёв лепестков (true/false)",
    "TIMING_ENABLED": "Подробные замеры времени фаз в логе (true/false)",
    "BG_COLOR": "Цвет фона: имя (white, black, ...) или #rrggbb",
    "LINE_COLOR": "Цвет контуров: имя или #rrggbb",
    "LINE_WIDTH": "Толщина пера в пикселях (0.1..20)",
    "DRAW_SPEED_LEVEL": "Скорость: 1 — медленно (~440 c), 20 — быстро (~4 c)",
    "COLOR_MODE": "Раскраска: yes — всегда, no — только контуры, random — случайно",
    "PALETTE_CHOICE": "Палитра: random, all, warm_soft, cool_soft, warm_bright, cool_bright",
    "CIRCLE_RADIUS": "Радиус центрального круга",
    "BAND1_WIDTH": "Ширина разделительной ленты 1",
    "L1_WIDTH": "Ширина слоя лепестков 1",
    "BAND2_WIDTH": "Ширина разделительной ленты 2",
    "L2_WIDTH": "Ширина слоя лепестков 2",
    "BAND3_WIDTH": "Ширина разделительной ленты 3",
    "L3_WIDTH": "Ширина слоя лепестков 3",
    "BAND4_WIDTH": "Ширина разделительной ленты 4",
    "L4_WIDTH": "Ширина слоя лепестков 4",
    "BAND5_WIDTH": "Ширина разделительной ленты 5",
    "L5_WIDTH": "Ширина слоя лепестков 5",
    "SAVE_FORMAT": "Формат сохранения: pdf (вектор), png или jpg",
}

_warnings = []
_applied = False


# ---------------------------------------------------------------
# Значения по умолчанию и текущие значения
# ---------------------------------------------------------------
def restore_defaults():
    """Возвращает Config к значениям из config.py."""
    for key, value in _DEFAULTS.items():
        setattr(Config, key, copy.deepcopy(value))


def fmt_value(value):
    """Значение Config -> строка для config.ini."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def current_values():
    """Текущие значения всех управляемых параметров (для окна настроек)."""
    return {key: fmt_value(getattr(Config, key)) for key in _PARAMS}


def duration_for_level(level):
    """Длительность рисования (сек) для уровня 1..20 — как в runtime."""
    lvl = max(1, min(20, int(level)))
    span = Config.SPEED_DURATION_MAX_S - Config.SPEED_DURATION_MIN_S
    return Config.SPEED_DURATION_MAX_S - span * (lvl - 1) / 19.0


def last_warnings():
    return list(_warnings)


# ---------------------------------------------------------------
# Разбор значений
# ---------------------------------------------------------------
def _parse_bool(raw):
    value = str(raw).strip().lower()
    if value in ("true", "1", "yes", "on", "да"):
        return True
    if value in ("false", "0", "no", "off", "нет"):
        return False
    return None


def _parse_color(raw):
    value = str(raw).strip()
    if not value or len(value) > 64:
        return None
    try:
        from PIL import ImageColor
        ImageColor.getrgb(value)
        return value
    except Exception:
        return None


def _clamp(raw, kind, low, high):
    if kind == "int":
        value = int(str(raw).strip())
    else:
        value = float(str(raw).strip().replace(",", "."))
    if value < low or value > high:
        return max(low, min(high, value)), True
    return value, False


def _parse_choice(raw, choices):
    value = str(raw).strip().lower()
    return value if value in choices else None


def _apply_one(key, raw):
    """Применяет один параметр; возвращает предупреждение или None."""
    section, rule = _PARAMS[key]

    display = fmt_value(getattr(Config, key))

    if rule == "bool":
        parsed = _parse_bool(raw)
        if parsed is None:
            return f"{key} = {raw!r}: ожидалось true/false"
        setattr(Config, key, parsed)
        return None

    if rule == "color":
        parsed = _parse_color(raw)
        if parsed is None:
            return f"{key} = {raw!r}: неизвестный цвет, оставлено {display}"
        setattr(Config, key, parsed)
        return None

    if isinstance(rule, tuple) and rule and rule[0] == "choice":
        parsed = _parse_choice(raw, rule[1])
        if parsed is None:
            allowed = ", ".join(rule[1])
            return f"{key} = {raw!r}: допустимо {allowed}; оставлено {display}"
        setattr(Config, key, parsed)
        return None

    if isinstance(rule, tuple) and len(rule) == 3:
        _, low, high = rule
        try:
            parsed, corrected = _clamp(raw, rule[0], low, high)
        except (TypeError, ValueError):
            return f"{key} = {raw!r}: ожидалось число, оставлено {display}"
        setattr(Config, key, parsed)
        if corrected:
            return (f"{key} = {raw!r}: вне диапазона {low}..{high}, "
                    f"использовано {fmt_value(parsed)}")
        return None

    return f"{key} = {raw!r}: внутренняя ошибка описания параметра"


def _apply_weight(key, raw):
    """Вес стиля: CENTER_3 = 2.0 и т. п."""
    for prefix, attr in _WEIGHT_TARGETS:
        if not key.startswith(prefix):
            continue
        styles = getattr(Config, attr)
        try:
            index = int(key[len(prefix):])
        except ValueError:
            return f"{key}: ожидался номер стиля после {prefix}"
        if index not in styles:
            return f"{key}: стиля с номером {index} нет"
        try:
            weight = float(str(raw).strip().replace(",", "."))
        except ValueError:
            return f"{key} = {raw!r}: ожидалось число"
        if weight < 0:
            weight = 0.0
        if weight > 100:
            weight = 100.0
        styles[index]["weight"] = weight
        return None
    return f"{key}: неизвестный вес стиля"


def _apply_color_weight(key_upper, raw):
    """Вес цвета: WARM_SOFT_#E8A87C = 0 и т. п. (регистр hex не важен)."""
    for family in Config.COLOR_FAMILIES:
        prefix = family.upper() + "_"
        if not key_upper.startswith(prefix):
            continue
        hex_part = key_upper[len(prefix):].strip()
        if not hex_part.startswith("#"):
            hex_part = "#" + hex_part
        for color in Config.COLOR_FAMILIES[family]["colors"]:
            if color["hex"].lower() == hex_part.lower():
                try:
                    weight = float(str(raw).strip().replace(",", "."))
                except ValueError:
                    return f"{key_upper} = {raw!r}: ожидалось число"
                color["weight"] = max(0.0, min(100.0, weight))
                return None
        return f"{key_upper}: цвета {hex_part} нет в палитре {family}"
    return f"{key_upper}: неизвестный вес цвета (формат <СЕМЕЙСТВО>_<#hex>)"


# ---------------------------------------------------------------
# Чтение config.ini
# ---------------------------------------------------------------
def apply_user_settings(overrides=None, ini_path=None):
    """Сбрасывает Config к умолчаниям и применяет config.ini.

    overrides — словарь {ключ: значение} для тестов/отладки,
    ini_path  — явный путь к файлу (по умолчанию app_paths.config_path()).
    Возвращает список предупреждений.
    """
    global _warnings, _applied
    app_paths.ensure_dirs()
    restore_defaults()
    _warnings = []

    path = ini_path or app_paths.config_path()
    raw = {}

    if os.path.exists(path):
        parser = configparser.ConfigParser(
            interpolation=None,
            strict=False,
            comment_prefixes=("#", ";"),
            # Инлайн-комментарии разрешены только с «;» (с «#» нельзя —
            # иначе обрежется значение цвета вида #e8a87c).
            inline_comment_prefixes=(";",),
        )
        parser.optionxform = str  # сохраняем регистр ключей
        try:
            parser.read(path, encoding="utf-8-sig")
        except (configparser.Error, OSError, UnicodeDecodeError) as exc:
            _warnings.append(
                f"Не удалось прочитать {path}: {exc}. "
                f"Используются значения из config.py."
            )
            parser = None

        if parser is not None:
            known = {key.upper() for key in _PARAMS}
            for section in _SECTION_ORDER:
                if not parser.has_section(section):
                    continue
                for option in parser.options(section):
                    upper = option.upper()
                    if upper == "SHOW_SETTINGS_DIALOG":
                        continue  # устаревший ключ старых версий — игнорируем молча
                    if upper not in known:
                        _warnings.append(
                            f"[{section}] {option}: неизвестный параметр, пропущен"
                        )
            for key in _PARAMS:
                section = _PARAMS[key][0]
                if parser.has_option(section, key):
                    raw[key] = parser.get(section, key)

            if parser.has_section(_WEIGHT_SECTION):
                for option, value in parser.items(_WEIGHT_SECTION):
                    warning = _apply_weight(option.strip().upper(), value)
                    if warning:
                        _warnings.append(warning)

            if parser.has_section(_COLOR_WEIGHT_SECTION):
                for option, value in parser.items(_COLOR_WEIGHT_SECTION):
                    warning = _apply_color_weight(option.strip().upper(), value)
                    if warning:
                        _warnings.append(warning)

    if overrides:
        raw.update({key: str(value) for key, value in overrides.items()})

    for key, value in raw.items():
        warning = _apply_one(key, value)
        if warning:
            _warnings.append(warning)

    _applied = True
    return list(_warnings)


def ensure_applied():
    """Применяет настройки один раз за запуск программы.

    Точка входа применяет настройки до окна настроек; main.py вызывает
    эту функцию при импорте — повторного чтения/сброса не происходит.
    """
    if not _applied:
        apply_user_settings()
    return last_warnings()


# ---------------------------------------------------------------
# Запись config.ini
# ---------------------------------------------------------------
def _split_inline_comment(raw):
    """'1.0    ; имя' -> ('1.0', '    ; имя'); без комментария -> (raw, '')."""
    pos = raw.find(";")
    if pos < 0:
        return raw, ""
    head, tail = raw[:pos], raw[pos:]
    spaces = head[len(head.rstrip()):]
    if not spaces:
        spaces = "    "
    return head.rstrip(), spaces + tail


def _style_display_name(key):
    """Имя узора для ключа веса CENTER_7 / BAND_3 / LAYER_5 (или '')."""
    for prefix, attr in _WEIGHT_TARGETS:
        if not key.startswith(prefix):
            continue
        try:
            index = int(key[len(prefix):])
        except ValueError:
            return ""
        return getattr(Config, attr).get(index, {}).get("name", "")
    return ""


def _color_family_comment(key):
    """Комментарий семейства для ключа веса цвета (или '')."""
    upper = key.upper()
    for family, data in Config.COLOR_FAMILIES.items():
        if upper.startswith(family.upper() + "_"):
            return data.get("comment", "")
    return ""


def _color_weight_section_lines(extra=None):
    """Секция [Веса цветов]: все цвета активными строками с пояснением."""
    lines = [
        f"[{_COLOR_WEIGHT_SECTION}]",
        "; Выберите вес цвета: 0 — не используется, чем больше цифра —",
        "; тем выше вероятность использования.",
        "; Формат ключа: <СЕМЕЙСТВО>_<#hex>,",
        "; семейство цвета — в комментарии справа от значения.",
    ]
    values = _all_color_weights()
    if extra:
        values.update({k: str(v) for k, v in extra.items()})
    for family, data in Config.COLOR_FAMILIES.items():
        comment = data.get("comment", "")
        for color in data["colors"]:
            key = f"{family.upper()}_{color['hex']}"
            suffix = f"    ; {comment}" if comment else ""
            lines.append(f"{key} = {values[key]}{suffix}")
    return lines


def _split_weights(weights):
    """{ключ: значение} -> (веса стилей, веса цветов)."""
    style_prefixes = tuple(prefix for prefix, _attr in _WEIGHT_TARGETS)
    color_prefixes = tuple(family.upper() + "_" for family in Config.COLOR_FAMILIES)
    styles, colors = {}, {}
    for key, value in (weights or {}).items():
        upper = key.upper()
        if upper.startswith(color_prefixes):
            colors[key] = value
        elif upper.startswith(style_prefixes):
            styles[key] = value
    return styles, colors


def _weight_lines(extra=None):
    """Строки секции весов: все узоры активными строками, название — в комментарии."""
    lines = [
        f"[{_WEIGHT_SECTION}]",
        "; Выберите вес стиля: 0 — не используется, чем больше цифра —",
        "; тем выше вероятность использования.",
        "; Название узора — в комментарии справа от значения.",
    ]
    values = _all_style_weights()
    if extra:
        values.update({k: str(v) for k, v in extra.items()})
    for key in sorted(values, key=_weight_sort_key):
        name = _style_display_name(key)
        suffix = f"    ; {name}" if name else ""
        lines.append(f"{key} = {values[key]}{suffix}")
    return lines


def template_text(values=None, weights=None):
    """Текст config.ini с комментариями.

    values  — {ключ: значение} вместо текущих значений Config;
    weights — {ключ: значение} активных весов (по умолчанию пусто).
    """
    values = values or {}

    lines = [
        "; ============================================================",
        ";  Mandala Generator — настройки рисования",
        "; ============================================================",
        ";  Меняйте значения после знака «=». Строки, начинающиеся",
        ";  с «;» или «#», — комментарии.",
        ";",
        ";  Можно писать комментарий после значения через «;» (с пробелом),",
        ";  но НЕ используйте в комментарии «#» — иначе пострадает цвет",
        ";  вида #e8a87c, который должен остаться частью значения.",
        ";",
        ";  Если удалить параметр или весь файл — вернётся значение",
        ";  по умолчанию из config.py.",
        "; ============================================================",
        "",
    ]

    for section in _SECTION_ORDER:
        lines.append(f"[{section}]")
        for key, (key_section, _rule) in _PARAMS.items():
            if key_section != section:
                continue
            comment = _COMMENTS.get(key)
            if comment:
                lines.append(f"; {comment}")
            value = values[key] if key in values else fmt_value(getattr(Config, key))
            lines.append(f"{key} = {value}")
        lines.append("")

    style_extra, color_extra = _split_weights(weights) if weights else ({}, {})
    lines.extend(_weight_lines(style_extra))
    lines.append("")
    lines.extend(_color_weight_section_lines(color_extra))
    lines.append("")
    return "\n".join(lines)


def write_template(path=None, values=None, weights=None):
    """Записывает config.ini (UTF-8 с BOM — Блокнот Windows читает корректно)."""
    path = path or app_paths.config_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    text = template_text(values=values, weights=weights)
    with open(path, "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write(text)
    return path


def write_template_if_missing(path=None):
    """Создаёт config.ini при первом запуске собранного приложения."""
    path = path or app_paths.config_path()
    if not os.path.exists(path):
        write_template(path)
        return True
    return False


def _all_style_weights():
    """Все веса стилей (CENTER_/BAND_/LAYER_) текущего состояния Config."""
    return {
        f"{prefix}{index}": fmt_value(float(style.get("weight", 1.0)))
        for prefix, attr in _WEIGHT_TARGETS
        for index, style in getattr(Config, attr).items()
    }


def _all_color_weights():
    """Все веса цветов палитр текущего состояния Config."""
    return {
        f"{family.upper()}_{color['hex']}": fmt_value(float(color.get("weight", 1.0)))
        for family, data in Config.COLOR_FAMILIES.items()
        for color in data["colors"]
    }


def _weight_sort_key(key):
    """Порядок строк весов: CENTER_, BAND_, LAYER_, внутри — по номеру."""
    for pos, prefix in enumerate(("CENTER_", "BAND_", "LAYER_")):
        if key.startswith(prefix):
            tail = key[len(prefix):]
            try:
                return (pos, int(tail), key)
            except ValueError:
                return (pos, 10 ** 6, key)
    return (9, 0, key)


def save_values(values, path=None):
    """Сохраняет значения в config.ini, не теряя правки пользователя.

    Файл правится построчно: у известных ключей обновляется значение после
    «=», недостающие известные ключи дописываются в конец, а комментарии,
    порядок строк и незнакомые записи остаются как есть. Если файла нет —
    создаётся полный шаблон. Веса стилей и цветов при записи перечисляются
    полностью, активными строками.
    """
    path = path or app_paths.config_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    targets = current_values()
    for key, value in (values or {}).items():
        if key in _PARAMS:
            targets[key] = str(value)
    style_weights = _all_style_weights()
    color_weights = _all_color_weights()
    style_upper = {k.upper(): v for k, v in style_weights.items()}
    color_upper = {k.upper(): v for k, v in color_weights.items()}
    targets_upper = {k.upper(): k for k in targets}

    if not os.path.exists(path) or os.path.getsize(path) == 0:
        write_template(path, values=targets)
        return path

    with open(path, encoding="utf-8-sig") as f:
        lines = f.read().splitlines()

    section_re = re.compile(r"^\s*\[(.+?)\]\s*$")
    kv_re = re.compile(r"^(\s*)([A-Za-z_][^=;]*?)(\s*=\s*)(.*)$")

    seen_params, style_seen, color_seen = set(), set(), set()
    style_section = color_section = False
    out = []
    for line in lines:
        stripped = line.strip()
        header = section_re.match(stripped) if stripped else None
        if header:
            name = header.group(1).strip().upper()
            style_section = name == _WEIGHT_SECTION.upper()
            color_section = name == _COLOR_WEIGHT_SECTION.upper()
            out.append(line)
            continue
        if stripped and not stripped.startswith((";", "#")):
            match = kv_re.match(line)
            if match:
                key = match.group(2).strip().upper()
                if key in targets_upper:
                    seen_params.add(key)
                    _value, comment = _split_inline_comment(match.group(4))
                    out.append(f"{match.group(1)}{match.group(2)}{match.group(3)}"
                               f"{targets[targets_upper[key]]}{comment}")
                    continue
                if style_section and key in style_upper:
                    style_seen.add(key)
                    _value, comment = _split_inline_comment(match.group(4))
                    out.append(f"{match.group(1)}{match.group(2)}{match.group(3)}"
                               f"{style_upper[key]}{comment}")
                    continue
                if color_section and key in color_upper:
                    color_seen.add(key)
                    _value, comment = _split_inline_comment(match.group(4))
                    out.append(f"{match.group(1)}{match.group(2)}{match.group(3)}"
                               f"{color_upper[key]}{comment}")
                    continue
        out.append(line)

    # Недостающие обычные параметры — дописываем в конец своими секциями.
    for section in _SECTION_ORDER:
        block = [f"{key} = {targets[key]}"
                 for key in _PARAMS
                 if _PARAMS[key][0] == section and key.upper() not in seen_params]
        if block:
            out.append("")
            out.append(f"[{section}]")
            out.extend(block)

    missing_styles = {k: v for k, v in style_weights.items()
                      if k.upper() not in style_seen}
    if missing_styles:
        if not style_section:
            out.append("")
            out.append(f"[{_WEIGHT_SECTION}]")
        for key in sorted(missing_styles, key=_weight_sort_key):
            name = _style_display_name(key)
            suffix = f"    ; {name}" if name else ""
            out.append(f"{key} = {missing_styles[key]}{suffix}")

    missing_colors = {k: v for k, v in color_weights.items()
                      if k.upper() not in color_seen}
    if missing_colors:
        if not color_section:
            out.append("")
            out.append(f"[{_COLOR_WEIGHT_SECTION}]")
        for key in sorted(missing_colors):
            family_comment = _color_family_comment(key)
            suffix = f"    ; {family_comment}" if family_comment else ""
            out.append(f"{key} = {missing_colors[key]}{suffix}")

    with open(path, "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write("\n".join(out) + "\n")
    return path
