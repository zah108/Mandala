"""Точка входа и оркестратор генерации мандалы.

Запуск: python -m mandala из родительской папки либо python mandala/main.py
по полному пути из любого каталога (тогда скрипт сам перезапускает себя
как пакет — см. «хак» вверху модуля).

Модули проекта:
    config.py        — все настроечные параметры: скорости, стили, цвета, радиусы;
    selection.py     — взвешенный выбор стилей и цветов с запретом повторов;
    logging_utils.py — папка лога и текстовый отчёт о запуске/завершении;
    runtime.py       — сцена рисования на Cairo (API как у turtle) и тайминги;
    geometry.py      — общие геометрические утилиты (окружности, кольца, лепестки);
    centers.py       — центральный узор, включая SVG-парсер для «Ом»;
    bands.py         — разделительные ленты (12 стилей);
    layers.py        — слои лепестков (стили 1–5);
    traj.py          — элементы траектории с постоянной скоростью пера;
    export.py        — сохранение готового вектора в PDF (img/).

Тяжёлые библиотеки (cairocffi, PIL) импортируются внутри export.py и
подключаются только на этапе сохранения — рисование от них не зависит.
"""
import os
import sys

# --- Хак для запуска напрямую (Run code / python mandala/main.py) ---
if __name__ == "__main__" and __package__ in (None, ""):
    _this_file = os.path.abspath(__file__)
    _pkg_dir = os.path.dirname(_this_file)
    _pkg_parent = os.path.dirname(_pkg_dir)
    _pkg_name = os.path.basename(_pkg_dir)

    if os.environ.get("_MANDALA_RELAUNCHED") == "1":
        sys.exit(
            "Не удалось перезапустить mandala как пакет. "
            "Запустите из терминала: python -m mandala"
        )

    sys.stdout.flush()
    sys.stderr.flush()

    env = os.environ.copy()
    env["_MANDALA_RELAUNCHED"] = "1"
    env["PYTHONPATH"] = _pkg_parent + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONUNBUFFERED"] = "1"        # без буферизации дочернего процесса

    import subprocess
    rc = subprocess.run(
        [sys.executable, "-u", "-m", f"{_pkg_name}.main"],
        env=env,
        cwd=os.getcwd(),
    ).returncode
    sys.exit(rc)

# --- Обычные импорты ---
import datetime
import random
import time

from .config import Config
from . import settings

# Пользовательские настройки (config.ini) применяются ДО импорта runtime:
# тот при импорте создаёт окно и фиксирует Config.WINDOW_SIZE.
# Если точка входа уже применяла их — повторного чтения не будет.
_settings_warnings = settings.ensure_applied()

from . import runtime, selection, centers, bands, layers, export, logging_utils
from .runtime import screen, t, _tmark


def _pick_all_colors(style_center, band_styles, layer_styles):
    """Полный проход выбора цветов по областям."""
    pal = {}
    cb1, cb2, cb3, cb4, cb5 = band_styles
    cl1, cl2, cl3, cl4, cl5 = layer_styles

    n_center = selection.colors_count_for_center(style_center) if selection.COLOR_ENABLED else 0
    pal["center"] = (selection.pick_colors_for(
        n_center,
        forbidden_hard=selection.prev_colors,
        forbidden_soft=selection.prev2_colors,
        area_label="центр",
    ) if selection.COLOR_ENABLED else [])
    selection.advance_history(pal["center"])

    def _band(style_idx, label):
        n = selection.colors_count_for_band(style_idx) if selection.COLOR_ENABLED else 0
        cols = (selection.pick_colors_for(
            n,
            forbidden_hard=selection.prev_colors,
            forbidden_soft=selection.prev2_colors,
            area_label=label,
        ) if selection.COLOR_ENABLED else [])
        selection.advance_history(cols)
        return cols

    def _layer(style_idx, label):
        ring_color = None
        if selection.COLOR_ENABLED and Config.PAINT_LAYER_RINGS:
            ring_color = selection.pick_colors_for(
                1,
                forbidden_hard=selection.prev_colors,
                forbidden_soft=selection.prev2_colors,
                area_label=f"кольцо {label}",
            )[0]
        forbidden_hard_layer = set(selection.prev_colors) | ({ring_color} if ring_color else set())
        n = selection.colors_count_for_layer(style_idx) if selection.COLOR_ENABLED else 0
        petal_colors = (selection.pick_colors_for(
            n,
            forbidden_hard=forbidden_hard_layer,
            forbidden_soft=selection.prev2_colors,
            area_label=label,
        ) if selection.COLOR_ENABLED else [])
        selection.advance_history(set(petal_colors) | ({ring_color} if ring_color else set()))
        return petal_colors, ring_color

    pal["band1"] = _band(cb1, "лента 1")
    pal["layer1"], pal["ring1"] = _layer(cl1, "слой 1")
    pal["band2"] = _band(cb2, "лента 2")
    pal["layer2"], pal["ring2"] = _layer(cl2, "слой 2")
    pal["band3"] = _band(cb3, "лента 3")
    pal["layer3"], pal["ring3"] = _layer(cl3, "слой 3")
    pal["band4"] = _band(cb4, "лента 4")
    pal["layer4"], pal["ring4"] = _layer(cl4, "слой 4")
    pal["band5"] = _band(cb5, "лента 5")
    pal["layer5"], pal["ring5"] = _layer(cl5, "слой 5")
    return pal


def _family_log():
    if selection.SELECTED_FAMILY == "all":
        return "all (все семейства в одном пуле)"
    fam_comment = Config.COLOR_FAMILIES[selection.SELECTED_FAMILY].get("comment", "")
    return f"{selection.SELECTED_FAMILY} ({fam_comment})"


def _compute_radii():
    r_band1_start = Config.CIRCLE_RADIUS
    r_layer1_start = r_band1_start + Config.BAND1_WIDTH
    r_band2_start = r_layer1_start + Config.L1_WIDTH
    r_layer2_start = r_band2_start + Config.BAND2_WIDTH
    r_band3_start = r_layer2_start + Config.L2_WIDTH
    r_layer3_start = r_band3_start + Config.BAND3_WIDTH
    r_band4_start = r_layer3_start + Config.L3_WIDTH
    r_layer4_start = r_band4_start + Config.BAND4_WIDTH
    r_band5_start = r_layer4_start + Config.L4_WIDTH
    r_layer5_start = r_band5_start + Config.BAND5_WIDTH
    return {
        "band1": r_band1_start, "layer1": r_layer1_start,
        "band2": r_band2_start, "layer2": r_layer2_start,
        "band3": r_band3_start, "layer3": r_layer3_start,
        "band4": r_band4_start, "layer4": r_layer4_start,
        "band5": r_band5_start, "layer5": r_layer5_start,
    }


def _mandala_name():
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    random_id = random.randint(10000, 99999)
    return f"{date_str}-mandala-{random_id}"


def main(block=True):
    """Полный цикл: новая мандала от выбора стилей до окна с готовым рисунком.

    block=True — автономный режим (python -m mandala): рисующее окно
    обслуживается своим mainloop до закрытия. block=False — окно обслуживается
    внешним циклом событий сеанса (окно настроек остаётся открытым,
    см. draw_session).
    """
    # Новый рисунок всегда с чистой сцены (при первом запуске — безвредно).
    runtime.clear_scene()
    runtime.apply_draw_speed(Config.DRAW_SPEED_LEVEL)
    selection.init()

    # --- Выбор стилей ---
    _t0 = time.perf_counter()
    style_center = selection.weighted_choice_styles(
        list(Config.CENTER_STYLES.keys()), Config.CENTER_STYLES
    )
    band_styles = selection.pick_styles_with_rules(5, Config.BAND_STYLES, max_repeat=1)
    layer_styles = selection.pick_styles_with_rules(5, Config.LAYER_STYLES, max_repeat=1)
    _tmark("select_styles", _t0)

    bands.set_styles(band_styles)
    layers.set_styles(layer_styles)

    # --- Выбор цветов ---
    _t0 = time.perf_counter()
    palette = _pick_all_colors(style_center, band_styles, layer_styles)
    _tmark("select_colors", _t0)

    # --- Лог старта ---
    mandala_name = _mandala_name()
    log_path = logging_utils.setup_log_path()
    report = logging_utils.build_start_log(
        style_center=style_center,
        band_styles=band_styles,
        layer_styles=layer_styles,
        palette=palette,
        color_enabled=selection.COLOR_ENABLED,
        color_mode=Config.COLOR_MODE,
        family_log=_family_log(),
        draw_speed_level=Config.DRAW_SPEED_LEVEL,
        draw_duration_s=runtime.draw_duration_s(Config.DRAW_SPEED_LEVEL),
        fallback_warnings=selection._fallback_warnings,
    )
    logging_utils.write_start_log(log_path, report)

    if _settings_warnings:
        logging_utils.write_start_log(
            log_path,
            "Предупреждения настроек (config.ini):\n  - "
            + "\n  - ".join(_settings_warnings) + "\n",
        )

    # --- Отрисовка ---
    r = _compute_radii()

    _t0 = time.perf_counter()
    centers.draw(style_center, Config.CIRCLE_RADIUS, palette["center"])
    _tmark(f"center_v{style_center}", _t0)

    _t0 = time.perf_counter(); bands.draw_band(1, r["band1"], Config.BAND1_WIDTH, palette["band1"]); _tmark("band1_run", _t0)
    _t0 = time.perf_counter(); layers.draw_layer(1, r["layer1"], palette["ring1"], palette["layer1"]); _tmark("layer1_run", _t0)
    _t0 = time.perf_counter(); bands.draw_band(2, r["band2"], Config.BAND2_WIDTH, palette["band2"]); _tmark("band2_run", _t0)
    _t0 = time.perf_counter(); layers.draw_layer(2, r["layer2"], palette["ring2"], palette["layer2"]); _tmark("layer2_run", _t0)
    _t0 = time.perf_counter(); bands.draw_band(3, r["band3"], Config.BAND3_WIDTH, palette["band3"]); _tmark("band3_run", _t0)
    _t0 = time.perf_counter(); layers.draw_layer(3, r["layer3"], palette["ring3"], palette["layer3"]); _tmark("layer3_run", _t0)
    _t0 = time.perf_counter(); bands.draw_band(4, r["band4"], Config.BAND4_WIDTH, palette["band4"]); _tmark("band4_run", _t0)
    _t0 = time.perf_counter(); layers.draw_layer(4, r["layer4"], palette["ring4"], palette["layer4"]); _tmark("layer4_run", _t0)
    _t0 = time.perf_counter(); bands.draw_band(5, r["band5"], Config.BAND5_WIDTH, palette["band5"]); _tmark("band5_run", _t0)
    _t0 = time.perf_counter(); layers.draw_layer(5, r["layer5"], palette["ring5"], palette["layer5"]); _tmark("layer5_run", _t0)

    try:
        screen.update()
    except Exception:
        pass
    t.hideturtle()

    # Конечный лог (и время окончания) фиксируются в момент, когда
    # анимация завершила рисование всей мандалы — см. runtime.done().
    def _on_drawing_finished():
        end_time_str = datetime.datetime.now().strftime("%H:%M:%S")

        # --- Сохранение: PDF создаётся только после завершения рисования ---
        out_path, error = export.save_mandala(runtime.scene, mandala_name)

        if error is None:
            status = (f"Успешно сохранено -> "
                      f"{os.path.join('img', os.path.basename(out_path))}")
        else:
            status = f"Ошибка сохранения ({error})"

        end_report = logging_utils.build_end_log(status, end_time_str)
        timing_msg = runtime._timing_report()
        logging_utils.write_end_log(log_path, end_report, timing_msg)

    runtime.done(_on_drawing_finished, block=block)


if __name__ == "__main__":
    main()