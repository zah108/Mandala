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
    "SHOW_SETTINGS_DIALOG": ("Общие", "bool"),
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

# префикс ключа веса -> словарь стилей Config
_WEIGHT_TARGETS = (
    ("CENTER_", "CENTER_STYLES"),
    ("BAND_", "BAND_STYLES"),
    ("LAYER_", "LAYER_STYLES"),
)

_COMMENTS = {
    "SHOW_SETTINGS_DIALOG": "Показывать окно настроек при каждом запуске (true/false)",
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

_dialog_pref = {"show": app_paths.is_frozen()}
_warnings = []
_applied = False


# ---------------------------------------------------------------
# Значения по умолчанию и текущие значения
# ---------------------------------------------------------------
def restore_defaults():
    """Возвращает Config к значениям из config.py."""
    for key, value in _DEFAULTS.items():
        setattr(Config, key, copy.deepcopy(value))
    _dialog_pref["show"] = app_paths.is_frozen()


def fmt_value(value):
    """Значение Config -> строка для config.ini."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def current_values():
    """Текущие значения всех управляемых параметров (для окна настроек)."""
    values = {key: fmt_value(getattr(Config, key)) for key in _PARAMS
              if key != "SHOW_SETTINGS_DIALOG"}
    values["SHOW_SETTINGS_DIALOG"] = "true" if _dialog_pref["show"] else "false"
    return values


def duration_for_level(level):
    """Длительность рисования (сек) для уровня 1..20 — как в runtime."""
    lvl = max(1, min(20, int(level)))
    span = Config.SPEED_DURATION_MAX_S - Config.SPEED_DURATION_MIN_S
    return Config.SPEED_DURATION_MAX_S - span * (lvl - 1) / 19.0


def show_dialog_requested():
    return bool(_dialog_pref["show"])


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

    if key == "SHOW_SETTINGS_DIALOG":
        parsed = _parse_bool(raw)
        if parsed is None:
            return f"{key} = {raw!r}: ожидалось true/false"
        _dialog_pref["show"] = parsed
        return None

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
            inline_comment_prefixes=None,
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
                    if option.upper() not in known:
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
def _weight_lines(active_values=None):
    """Строки секции весов.

    active_values — {ключ: значение}, которые надо записать активными;
    иначе в шаблоне остаются только пояснения и примеры в комментариях.
    """
    lines = [
        f"[{_WEIGHT_SECTION}]",
        "; Вероятности выбора узоров: 0 — узор не используется, 1 — обычная,",
        "; 2 — вдвое чаще. Формат ключа: CENTER_<номер>, BAND_<номер>, LAYER_<номер>.",
        "; Ниже примеры (раскомментируйте и поменяйте значение):",
        "; CENTER_1 = 1.0",
        "; BAND_3 = 0",
        "; LAYER_5 = 2.0",
    ]
    if active_values:
        for key in sorted(active_values):
            lines.append(f"{key} = {active_values[key]}")
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
        ";  ВАЖНО: не пишите комментарий в одной строке со значением —",
        ";  цвет вида #e8a87c должен остаться частью значения.",
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
            if key in values:
                value = values[key]
            elif key == "SHOW_SETTINGS_DIALOG":
                value = "true" if _dialog_pref["show"] else "false"
            else:
                value = fmt_value(getattr(Config, key))
            lines.append(f"{key} = {value}")
        lines.append("")

    lines.extend(_weight_lines(weights))
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


def save_values(values, path=None):
    """Сохраняет значения из окна настроек, не теряя правки весов.

    Файл перегенерируется по шаблону; текущие веса стилей записываются
    активными значениями, чтобы ручные правки не пропали.
    """
    weights = {}
    for prefix, attr in _WEIGHT_TARGETS:
        for index, style in getattr(Config, attr).items():
            weight = float(style.get("weight", 1.0))
            if weight != 1.0:
                weights[f"{prefix}{index}"] = fmt_value(weight)
    return write_template(path=path, values=values, weights=weights)
