import turtle
import math
import os
import random
import datetime
import subprocess
import time
import re
from PIL import Image, ImageGrab

# =====================================================================
# БЛОК CONFIG (Настроечные параметры мандалы)
# =====================================================================
class Config:
    # --- Цвета линий и фона ---
    BG_COLOR = "white"          # цвет фона холста (любое имя цвета turtle/Tk)
    LINE_COLOR = "black"        # цвет линий по умолчанию
    LINE_WIDTH = 1.5            # толщина пера (в пикселях)

    # --- Скорость отрисовки ---
    # 0..8   — быстрый режим с батчингом (tracer(0), пачками по N шагов);
    # 9      — мгновенно, без задержек;
    # 10..20 — плавный режим с нарастающей паузой между шагами.
    DRAW_SPEED_LEVEL = 8

    # --- Радиусы и ширины (в пикселях), задают геометрию мандалы ---
    CIRCLE_RADIUS = 45          # радиус центрального круга
    BAND1_WIDTH = 12            # ширина разделительной ленты 1
    L1_WIDTH = 55               # высота слоя лепестков 1
    BAND2_WIDTH = 14            # ширина разделительной ленты 2
    L2_WIDTH = 65               # высота слоя лепестков 2
    BAND3_WIDTH = 15            # ширина разделительной ленты 3
    L3_WIDTH = 70               # высота слоя лепестков 3
    BAND4_WIDTH = 15            # ширина разделительной ленты 4
    L4_WIDTH = 75               # высота слоя лепестков 4
    BAND5_WIDTH = 16            # ширина разделительной ленты 5
    L5_WIDTH = 80               # высота слоя лепестков 5

    # --- Внешнее кольцо ---
    DRAW_OUTER_RING = True      # рисовать ли внешнее ограничивающее кольцо
    OUTER_RING_RADIUS = 405     # радиус внешнего кольца (если DRAW_OUTER_RING)

    # --- Формат сохранения ---
    # "pdf" — через Ghostscript; "jpg" — через PIL (из EPS).
    SAVE_FORMAT = "pdf"

    # --- Окно и экспорт ---
    WINDOW_SIZE = 1000          # размер окна turtle (ширина = высота)
    BBOX_PADDING = 60           # отступ вокруг рисунка в EPS/PDF

    # --- Диагностика ---
    TIMING_ENABLED = False      # печатать ли тайминги фаз в лог/консоль

    # --- Раскраска слоёв ---
    PAINT_LAYER_RINGS = True    # заливать ли фоновое кольцо под каждым слоем лепестков

    # --- Режим раскраски ---
    # "yes"    — раскраска всегда включена;
    # "no"     — раскраска всегда выключена;
    # "random" — при каждом запуске случайно: включена или выключена.
    COLOR_MODE = "yes"

    # --- Выбор палитры (семейства) ---
    # Возможные значения:
    #   "random"      — при каждом запуске случайно выбирается одно из семейств
    #                   (warm_soft / cool_soft / warm_bright / cool_bright);
    #   "all"         — все семейства объединяются в один общий пул цветов,
    #                   выбор идёт из суммарного набора;
    #   "warm_soft"   — только тёплые мягкие (пастельные тёплые тона);
    #   "cool_soft"   — только холодные мягкие (пастельные холодные тона);
    #   "warm_bright" — только тёплые яркие (насыщенные тёплые тона);
    #   "cool_bright" — только холодные яркие (насыщенные холодные тона).
    # Любое другое значение приведёт к выбору случайного семейства (как "random").
    PALETTE_CHOICE = "all"

    COLOR_FAMILIES = {
        "warm_soft": {
            "comment": "Тёплое-мягкое (пастельные тёплые тона)",
            "colors": [
                {"hex": "#e8a87c", "weight": 1.0},
                {"hex": "#e6b8b0", "weight": 1.0},
                {"hex": "#f0d8a8", "weight": 1.0},
                {"hex": "#d9b8a3", "weight": 1.0},
                {"hex": "#d4c5a0", "weight": 1.0},
                {"hex": "#c9b7a3", "weight": 1.0},
                {"hex": "#ead4b8", "weight": 1.0},
                {"hex": "#e3c4a8", "weight": 1.0},
                {"hex": "#dcc0a0", "weight": 1.0},
                {"hex": "#e0cbb0", "weight": 1.0},
                {"hex": "#d8c8b0", "weight": 1.0},
            ],
        },
        "cool_soft": {
            "comment": "Холодное-мягкое (пастельные холодные тона)",
            "colors": [
                {"hex": "#a8c5a0", "weight": 1.0},
                {"hex": "#8fbcd4", "weight": 1.0},
                {"hex": "#b8a4c9", "weight": 1.0},
                {"hex": "#9bb8a3", "weight": 1.0},
                {"hex": "#a9a3c9", "weight": 1.0},
                {"hex": "#c3d4c0", "weight": 1.0},
                {"hex": "#a8bfd0", "weight": 1.0},
                {"hex": "#b0c9b8", "weight": 1.0},
                {"hex": "#9fb8c4", "weight": 1.0},
                {"hex": "#bcb0d0", "weight": 1.0},
                {"hex": "#a4bcc9", "weight": 1.0},
            ],
        },
        "warm_bright": {
            "comment": "Тёплое-яркое (насыщенные тёплые тона)",
            "colors": [
                {"hex": "#f4a261", "weight": 1.0},
                {"hex": "#e76f51", "weight": 1.0},
                {"hex": "#e9c46a", "weight": 1.0},
                {"hex": "#bc4749", "weight": 1.0},
                {"hex": "#bc6c25", "weight": 1.0},
                {"hex": "#d97642", "weight": 1.0},
                {"hex": "#c98a3f", "weight": 1.0},
                {"hex": "#d94f2b", "weight": 1.0},
                {"hex": "#e08544", "weight": 1.0},
                {"hex": "#a83e2c", "weight": 1.0},
                {"hex": "#c25a35", "weight": 1.0},
            ],
        },
        "cool_bright": {
            "comment": "Холодное-яркое (насыщенные холодные тона)",
            "colors": [
                {"hex": "#2a9d8f", "weight": 1.0},
                {"hex": "#3a6673", "weight": 1.0},
                {"hex": "#8ab17d", "weight": 1.0},
                {"hex": "#6a994e", "weight": 1.0},
                {"hex": "#3d6a99", "weight": 1.0},
                {"hex": "#7f63a8", "weight": 1.0},
                {"hex": "#4d8fa8", "weight": 1.0},
                {"hex": "#2f7a6b", "weight": 1.0},
                {"hex": "#5a4a8f", "weight": 1.0},
                {"hex": "#3a8fa0", "weight": 1.0},
                {"hex": "#4a7d8f", "weight": 1.0},
            ],
        },
    }

    CENTER_STYLES = {
        1: {"weight": 1.0, "name": "Радиальные лучи"},
        2: {"weight": 1.0, "name": "Концентрические круги"},
        3: {"weight": 1.0, "name": "Спираль"},
        4: {"weight": 1.0, "name": "Внутренние петли"},
        5: {"weight": 1.0, "name": "Мишень (Плотный центр)"},
        6: {"weight": 1.0, "name": "Звезда Давида (внешние лучи)"},
        7: {"weight": 5.0, "name": "Ом"},
        8: {"weight": 1.0, "name": "Цветок"},
        9: {"weight": 1.0, "name": "Лотос"},
        10: {"weight": 1.0, "name": "Солнце"},
        11: {"weight": 1.0, "name": "Узел"},
    }

    BAND_STYLES = {
        1: {"weight": 1.0, "name": "Прямые штрихи"},
        2: {"weight": 1.0, "name": "Малые круги (прореж.)"},
        3: {"weight": 1.0, "name": "Зигзаг"},
        4: {"weight": 1.0, "name": "Двойные круги"},
        5: {"weight": 1.0, "name": "Двойные штрихи"},
        6: {"weight": 1.0, "name": "Круги"},
        7: {"weight": 1.0, "name": "Квадратики"},
        8: {"weight": 1.0, "name": "Полукруги"},
        9: {"weight": 1.0, "name": "Малые круги 2"},
        10: {"weight": 1.0, "name": "Волна"},
        11: {"weight": 1.0, "name": "Ромбы"},
        12: {"weight": 1.0, "name": "Двойная волна"},
    }

    LAYER_STYLES = {
        1:  {"weight": 1.0, "name": "Пламя (Ромб)"},
        2:  {"weight": 1.0, "name": "Кольцо овалов"},
        3:  {"weight": 1.0, "name": "Перо в пере"},
        4:  {"weight": 1.0, "name": "Классический лист"},
        5:  {"weight": 1.0, "name": "Лист с прожилкой (45°)"},
        6:  {"weight": 1.0, "name": "Полулист (поперёк)"},
        7:  {"weight": 1.0, "name": "Двойной лист"},
        8:  {"weight": 1.0, "name": "Лепесток с тремя точками"},
        9:  {"weight": 1.0, "name": "Тройной лист"},
        10: {"weight": 1.0, "name": "Капля (срез)"},
        11: {"weight": 1.0, "name": "Двойной лист (срез)"},
        12: {"weight": 1.0, "name": "Дубовый лист"},
        14: {"weight": 1.0, "name": "Веер (без центра)"},
        15: {"weight": 1.0, "name": "Двойной контур (срез)"},
        16: {"weight": 1.0, "name": "Двойной контур (с точкой)"},
        17: {"weight": 1.0, "name": "Ромб"},
        18: {"weight": 1.0, "name": "Двойной контур"},
    }
# =====================================================================

screen = turtle.Screen()
screen.setup(width=Config.WINDOW_SIZE, height=Config.WINDOW_SIZE)
screen.bgcolor(Config.BG_COLOR)
screen.title("Procedural Modular Mandala Generator")

_timings = []


def _tmark(label, t0):
    if not Config.TIMING_ENABLED:
        return
    dt = time.perf_counter() - t0
    _timings.append((label, dt))


def _timing_report():
    if not Config.TIMING_ENABLED or not _timings:
        return ""
    lines = ["", "----- Тайминги фаз -----"]
    total = 0.0
    for label, dt in _timings:
        lines.append(f"[timing] {label:<24} {dt:6.3f} s")
        total += dt
    lines.append(f"[timing] {'TOTAL (сумма фаз)':<24} {total:6.3f} s")
    lines.append("------------------------")
    return "\n".join(lines) + "\n"

t = turtle.Turtle(visible=False)
t.pencolor(Config.LINE_COLOR)
t.width(Config.LINE_WIDTH)


def _apply_draw_speed(level):
    level = max(0, min(20, int(level)))
    Config._batched_mode = (level < 9)
    _batch_table = {0: 400, 1: 300, 2: 200, 3: 150, 4: 100,
                    5: 70, 6: 50, 7: 30, 8: 15}
    Config._batch_size = _batch_table.get(level, 1)
    Config._move_counter = 0

    if level <= 9:
        t.speed(0)
        Config._effective_pause = 0.0
        _delay_ms = 0
    else:
        k = level - 9
        t.speed(min(10, k))
        Config._effective_pause = 0.0006 * (k ** 1.2)
        _delay_ms = max(0, 20 - level)

    try:
        screen.delay(_delay_ms)
        if Config._batched_mode:
            screen.tracer(0)
        else:
            screen.tracer(1)
    except Exception:
        pass


_apply_draw_speed(Config.DRAW_SPEED_LEVEL)

if Config.COLOR_MODE == "random":
    COLOR_ENABLED = random.choice([False, True])
elif Config.COLOR_MODE == "yes":
    COLOR_ENABLED = True
else:
    COLOR_ENABLED = False

_family_keys = list(Config.COLOR_FAMILIES.keys())

if Config.PALETTE_CHOICE == "random":
    SELECTED_FAMILY = random.choice(_family_keys)
    ACTIVE_PALETTE = Config.COLOR_FAMILIES[SELECTED_FAMILY]["colors"]
elif Config.PALETTE_CHOICE == "all":
    SELECTED_FAMILY = "all"
    ACTIVE_PALETTE = []
    for _k in _family_keys:
        ACTIVE_PALETTE.extend(Config.COLOR_FAMILIES[_k]["colors"])
elif Config.PALETTE_CHOICE in Config.COLOR_FAMILIES:
    SELECTED_FAMILY = Config.PALETTE_CHOICE
    ACTIVE_PALETTE = Config.COLOR_FAMILIES[SELECTED_FAMILY]["colors"]
else:
    SELECTED_FAMILY = random.choice(_family_keys)
    ACTIVE_PALETTE = Config.COLOR_FAMILIES[SELECTED_FAMILY]["colors"]


def pick_color_no_adjacent(recent_colors, palette,
                           forbidden_hard=None, forbidden_soft=None):
    hard = set(forbidden_hard or [])
    soft = set(forbidden_soft or [])
    recent_set = set(recent_colors or [])

    available = [
        c for c in palette
        if c["hex"] not in recent_set
        and c["hex"] not in hard
        and c["hex"] not in soft
    ]
    fallback_stage = 0

    if not available:
        available = [
            c for c in palette
            if c["hex"] not in recent_set
            and c["hex"] not in hard
        ]
        fallback_stage = 1

    if not available:
        available = [
            c for c in palette
            if c["hex"] not in recent_set
        ]
        fallback_stage = 2

    if not available:
        available = list(palette)
        fallback_stage = 2

    weights = [max(0.0, c.get("weight", 1.0)) for c in available]
    if sum(weights) <= 0:
        chosen = random.choice(available)
    else:
        chosen = random.choices(available, weights=weights, k=1)[0]
    return chosen["hex"], fallback_stage


def weighted_choice_styles(style_ids, styles_dict):
    if not style_ids:
        raise ValueError("Нет стилей для выбора")
    weights = [max(0.0, styles_dict[s].get("weight", 1.0)) for s in style_ids]
    if sum(weights) <= 0:
        return random.choice(style_ids)
    return random.choices(style_ids, weights=weights, k=1)[0]


def pick_styles_with_rules(num_slots, styles_dict, max_repeat=2):
    style_ids = list(styles_dict.keys())
    usage = {s: 0 for s in style_ids}
    chosen = []
    prev = None
    for _ in range(num_slots):
        candidates = [
            s for s in style_ids
            if usage[s] < max_repeat and s != prev
        ]
        if not candidates:
            candidates = [s for s in style_ids if s != prev]
        choice = weighted_choice_styles(candidates, styles_dict)
        chosen.append(choice)
        usage[choice] += 1
        prev = choice
    return chosen


def move_to(x, y):
    t.goto(x, y)
    if Config._batched_mode:
        Config._move_counter += 1
        if Config._move_counter >= Config._batch_size:
            Config._move_counter = 0
            try:
                screen.update()
            except Exception:
                pass
        return
    if Config._effective_pause > 0:
        time.sleep(Config._effective_pause)


def draw_circle_from_center(r):
    t.penup()
    t.goto(0, -r)
    t.setheading(0)
    t.pendown()
    t.circle(r)


def fill_ring(inner_r, outer_r, color):
    if not COLOR_ENABLED or not color:
        return
    t.fillcolor(color)
    t.begin_fill()
    steps = 36

    t.penup(); t.goto(inner_r, 0); t.pendown()
    for i in range(1, steps + 1):
        a = -2 * math.pi * i / steps
        t.goto(inner_r * math.cos(a), inner_r * math.sin(a))

    t.penup(); t.goto(outer_r, 0); t.pendown()
    for i in range(1, steps + 1):
        a = -2 * math.pi * i / steps
        t.goto(outer_r * math.cos(a), outer_r * math.sin(a))

    t.penup(); t.goto(inner_r, 0); t.pendown()
    t.end_fill()


# =====================================================================
# SVG ОМ — ПАРСЕР
# =====================================================================
OM_SVG_PATHS = [
    "M1674.7654,364.11l-142.1121,149.3132l149.3608,137.2957l144.4966-146.9288L1674.7654,364.11z",
    "M1383.3402,445.9915c0,0,158.9464,500.9695,618.9987,84.3135c2.4321,2.3845,125.2305,163.7629,127.6626,163.7629c-178.2604,199.9108-722.5786,308.3072-746.6614-248.0764L1383.3402,445.9915L1383.3402,445.9915z",
    "M959.3881,1021.6413L848.6072,821.7305c566.8275-380.5555,873.5131,168.5795,464.869,416.7037l132.4791,52.9821c158.1831-6.4856,135.4357-194.5697,303.4906-346.8397c63.4258-76.3018,512.224-176.6388,522.6676,464.869c-26.2285,582.1245-711.3716,541.9341-597.3484,0c40.1299,209.1467,195.2008,217.5673,316.8134,161.9077c184.0975-86.0382,180.8688-229.8975,181.6078-288.2218c1.814-143.1672-67.2197-350.2632-245.5282-222.9576c-91.4915,65.3215-95.5204,136.4851-113.2128,171.0116c-17.6449,34.5266-73.4406,169.1992-313.1237,127.6626c223.6121,462.3416-146.6904,585.0922-183.0292,592.5315c-93.8989,47.2594-665.6382-3.8627-604.5967-739.4602c48.9763,385.3719,242.7353,591.2438,551.6147,513.0345c233.8176-59.1814,232.8162-480.1293-127.6625-342.0232l-81.8815-255.3248c-3.4813-10.8254,115.9788,30.3777,238.4432-2.3844c99.4309-26.6105,181.5985-220.894-79.4971-221.6093c-114.405-0.2861-170.2009,78.6862-255.3251,118.0293L959.3881,1021.6413z",
]


def _tokenize_path(d):
    tokens = []
    i = 0
    n = len(d)
    num_re = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
    while i < n:
        ch = d[i]
        if ch in "MmLlHhVvCcSsQqTtAaZz":
            tokens.append(ch)
            i += 1
        elif ch in " ,\t\n\r":
            i += 1
        else:
            m = num_re.match(d, i)
            if m:
                tokens.append(float(m.group()))
                i = m.end()
            else:
                i += 1
    return tokens


def _bezier(p0, p1, p2, p3, steps=12):
    pts = []
    for k in range(steps + 1):
        tt = k / steps
        x = ((1 - tt) ** 3) * p0[0] + 3 * ((1 - tt) ** 2) * tt * p1[0] + 3 * (1 - tt) * (tt ** 2) * p2[0] + (tt ** 3) * p3[0]
        y = ((1 - tt) ** 3) * p0[1] + 3 * ((1 - tt) ** 2) * tt * p1[1] + 3 * (1 - tt) * (tt ** 2) * p2[1] + (tt ** 3) * p3[1]
        pts.append((x, y))
    return pts


def parse_svg_path(d):
    tokens = _tokenize_path(d)
    subpaths = []
    cur = []
    i = 0
    x = y = 0.0
    start_x = start_y = 0.0
    last_cmd = None

    def flush():
        nonlocal cur
        if cur:
            subpaths.append(cur)
            cur = []

    while i < len(tokens):
        tk = tokens[i]
        if isinstance(tk, str):
            cmd = tk
            i += 1
        else:
            cmd = last_cmd

        if cmd in "Mm":
            if cur:
                flush()
            x = tokens[i]; y = tokens[i + 1]; i += 2
            if cmd == "m":
                x += start_x; y += start_y
            start_x, start_y = x, y
            cur = [(x, y)]

        elif cmd in "Ll":
            nx = tokens[i]; ny = tokens[i + 1]; i += 2
            if cmd == "l":
                nx += x; ny += y
            x, y = nx, ny
            cur.append((x, y))

        elif cmd in "Cc":
            p1x = tokens[i]; p1y = tokens[i + 1]
            p2x = tokens[i + 2]; p2y = tokens[i + 3]
            ex = tokens[i + 4]; ey = tokens[i + 5]; i += 6
            if cmd == "c":
                p1x += x; p1y += y
                p2x += x; p2y += y
                ex += x; ey += y
            pts = _bezier((x, y), (p1x, p1y), (p2x, p2y), (ex, ey), steps=12)
            cur.extend(pts[1:])
            x, y = ex, ey

        elif cmd in "Zz":
            if cur:
                cur.append((start_x, start_y))
            flush()

        else:
            i += 1

        last_cmd = cmd

    flush()
    return subpaths


def _normalize_om(subpaths):
    all_pts = [p for sp in subpaths for p in sp]
    if not all_pts:
        return []
    min_x = min(p[0] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_y = max(p[1] for p in all_pts)
    w = max_x - min_x
    h = max_y - min_y
    if w == 0 or h == 0:
        return []
    scale = 1.0 / max(w, h)
    cx0 = (min_x + max_x) / 2
    cy0 = (min_y + max_y) / 2
    norm = []
    for sp in subpaths:
        nsp = []
        for (px, py) in sp:
            nx = (px - cx0) * scale
            ny = -(py - cy0) * scale
            nsp.append((nx, ny))
        norm.append(nsp)
    return norm


_t0 = time.perf_counter()
_OM_SUBPATHS = []
for _d in OM_SVG_PATHS:
    _OM_SUBPATHS.extend(parse_svg_path(_d))
_OM_NORM = _normalize_om(_OM_SUBPATHS)
_tmark("parse_svg_om", _t0)


def draw_om_at(center_x, center_y, size, rotation_angle):
    if not _OM_NORM:
        return
    cos_r = math.cos(rotation_angle)
    sin_r = math.sin(rotation_angle)
    for sp in _OM_NORM:
        if not sp:
            continue
        lx, ly = sp[0]
        gx = center_x + (lx * cos_r - ly * sin_r) * size
        gy = center_y + (lx * sin_r + ly * cos_r) * size
        t.penup(); t.goto(gx, gy); t.pendown()
        for (lx, ly) in sp[1:]:
            gx = center_x + (lx * cos_r - ly * sin_r) * size
            gy = center_y + (lx * sin_r + ly * cos_r) * size
            move_to(gx, gy)


# =====================================================================
# ПАРАМЕТРИЧЕСКИЕ ФУНКЦИИ ДЛЯ ЛЕПЕСТКОВ
# =====================================================================

def petal_points(inner_r, outer_r, phi, half_angle, shape_fn, steps=8):
    pts = []
    for k in range(steps + 1):
        tt = k / steps
        r = inner_r + (outer_r - inner_r) * tt
        off = half_angle * shape_fn(tt)
        a = phi - off
        pts.append((r * math.cos(a), r * math.sin(a)))
    for k in range(steps - 1, -1, -1):
        tt = k / steps
        r = inner_r + (outer_r - inner_r) * tt
        off = half_angle * shape_fn(tt)
        a = phi + off
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def draw_polyline(pts, close=True):
    if not pts:
        return
    t.penup(); t.goto(pts[0]); t.pendown()
    for p in pts[1:]:
        move_to(p[0], p[1])
    if close:
        move_to(pts[0][0], pts[0][1])


def shape_leaf(tt):
    return math.sin(math.pi * tt)


def smooth_polyline(pts, iterations=1):
    if not pts or len(pts) < 3:
        return pts
    result = list(pts)
    for _ in range(iterations):
        new_pts = []
        n = len(result)
        for i in range(n):
            p0 = result[i]
            p1 = result[(i + 1) % n]
            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
            new_pts.append(q)
            new_pts.append(r)
        result = new_pts
    return result


# =====================================================================
# ВАРИАНТЫ ЦЕНТРА
# =====================================================================

def center_v1(r):
    for i in range(12):
        angle = math.radians(i * (360 / 12))
        t.penup(); t.goto(0, 0); t.pendown()
        move_to(r * math.cos(angle), r * math.sin(angle))


def center_v2(r, color=None):
    for curr_r in range(10, int(r) + 1, 10):
        if COLOR_ENABLED and color and curr_r == 10:
            t.fillcolor(color)
            t.begin_fill()
            draw_circle_from_center(curr_r)
            t.end_fill()
        else:
            draw_circle_from_center(curr_r)


def center_v3(r):
    turns = 4
    steps = 200
    t.penup()
    for i in range(steps + 1):
        tt = i / steps
        rr = r * tt
        a = -2 * math.pi * turns * tt
        x = rr * math.cos(a)
        y = rr * math.sin(a)
        if i == 0:
            t.goto(x, y); t.pendown()
        else:
            move_to(x, y)


def center_v4(r):
    for i in range(6):
        t.penup(); t.goto(0, 0); t.setheading(i * 60); t.pendown()
        t.circle(r / 2, 360)


def center_v5(r):
    t.penup(); t.goto(0, -5); t.setheading(0); t.pendown()
    t.begin_fill(); t.circle(5); t.end_fill()
    draw_circle_from_center(r * 0.4)
    draw_circle_from_center(r * 0.7)
    draw_circle_from_center(r)


def center_v6(r, color=None):
    outer_pts = []
    for k in range(6):
        a = math.radians(-90 + k * 60)
        outer_pts.append((r * math.cos(a), r * math.sin(a)))
    inner_r = r / math.sqrt(3)
    inner_pts = []
    for k in range(6):
        a = math.radians(-60 + k * 60)
        inner_pts.append((inner_r * math.cos(a), inner_r * math.sin(a)))
    for k in range(6):
        out = outer_pts[k]
        in1 = inner_pts[(k + 5) % 6]
        in2 = inner_pts[k]
        t.penup(); t.goto(out); t.pendown()
        move_to(in1[0], in1[1])
        t.penup(); t.goto(out); t.pendown()
        move_to(in2[0], in2[1])


def center_v7(r):
    size = r * 2 * 0.9 * 0.7
    draw_om_at(0, 0, size, 0.0)


def center_v8(r):
    circle_r = r * 0.35
    petals = 10
    for i in range(petals):
        a = math.radians(i * 360 / petals)
        pts = []
        steps = 12
        half = math.radians(360 / petals / 2) * 0.98
        for k in range(steps + 1):
            tt = k / steps
            rr = r * tt
            off = half * math.sin(math.pi * tt)
            pts.append((rr * math.cos(a - off), rr * math.sin(a - off)))
        for k in range(steps - 1, -1, -1):
            tt = k / steps
            rr = r * tt
            off = half * math.sin(math.pi * tt)
            pts.append((rr * math.cos(a + off), rr * math.sin(a + off)))
        t.penup(); t.goto(pts[0]); t.pendown()
        for p in pts[1:]:
            move_to(p[0], p[1])
        move_to(pts[0][0], pts[0][1])
    t.penup(); t.goto(0, -circle_r); t.setheading(0); t.pendown()
    t.fillcolor(Config.BG_COLOR)
    t.begin_fill()
    t.circle(circle_r)
    t.end_fill()
    draw_circle_from_center(circle_r)


def center_v9(r, inner_color=None):
    circle_r = r * 0.35

    # Сначала заливаем внутренний круг вторым цветом центра.
    if COLOR_ENABLED and inner_color:
        t.penup(); t.goto(0, -circle_r); t.setheading(0); t.pendown()
        t.fillcolor(inner_color)
        t.begin_fill()
        t.circle(circle_r)
        t.end_fill()
    # Обводку внутреннего круга НЕ рисуем — внутри не должно быть чёрных линий.

    petals = 8
    for i in range(petals):
        a = math.radians(i * 360 / petals)
        half = math.radians(360 / petals / 2)
        steps = 14
        pts = []
        # Лепестки начинаются от границы внутреннего круга (circle_r),
        # чтобы внутрь круга не заходили никакие линии.
        for k in range(steps + 1):
            tt = k / steps
            rr = circle_r + (r - circle_r) * tt
            off = half * math.sin(math.pi * tt)
            pts.append((rr * math.cos(a - off), rr * math.sin(a - off)))
        for k in range(steps - 1, -1, -1):
            tt = k / steps
            rr = circle_r + (r - circle_r) * tt
            off = half * math.sin(math.pi * tt)
            pts.append((rr * math.cos(a + off), rr * math.sin(a + off)))
        t.penup(); t.goto(pts[0]); t.pendown()
        for p in pts[1:]:
            move_to(p[0], p[1])
        move_to(pts[0][0], pts[0][1])
        t.penup()
        t.goto(circle_r * math.cos(a), circle_r * math.sin(a))
        t.pendown()
        move_to(r * 0.95 * 0.7 * math.cos(a), r * 0.95 * 0.7 * math.sin(a))


def center_v10(r):
    inner_r = r * 0.45
    draw_circle_from_center(inner_r)
    rays = 16
    ray_len = r * 0.55
    half_base = math.radians(360 / rays / 2) * 0.7
    for i in range(rays):
        a = math.radians(i * 360 / rays)
        base1 = (inner_r * math.cos(a - half_base),
                 inner_r * math.sin(a - half_base))
        base2 = (inner_r * math.cos(a + half_base),
                 inner_r * math.sin(a + half_base))
        tip = ((inner_r + ray_len) * math.cos(a),
               (inner_r + ray_len) * math.sin(a))
        t.penup(); t.goto(base1); t.pendown()
        move_to(tip[0], tip[1])
        move_to(base2[0], base2[1])


def center_v11(r):
    def square(side_r, rotation_deg):
        pts = []
        for k in range(4):
            a = math.radians(rotation_deg + k * 90)
            pts.append((side_r * math.cos(a), side_r * math.sin(a)))
        pts.append(pts[0])
        t.penup(); t.goto(pts[0]); t.pendown()
        for p in pts[1:]:
            move_to(p[0], p[1])
    square(r * 0.95, 0)
    square(r * 0.95, 45)
    draw_circle_from_center(r)


# =====================================================================
# ЛЕНТЫ — 12 СТИЛЕЙ
# =====================================================================

def generic_band(inner_r, width, style_type, num_elements, band_colors=None):
    outer_r = inner_r + width
    mid_r = (inner_r + outer_r) / 2
    band_w = width

    if band_colors is None:
        band_colors = []

    if COLOR_ENABLED and band_colors:
        fill_ring(inner_r, outer_r, band_colors[0])

    draw_circle_from_center(inner_r)
    draw_circle_from_center(outer_r)

    element_color = None
    if band_colors:
        element_color = band_colors[1] if len(band_colors) >= 2 else band_colors[0]

    if style_type in (2, 4, 6):
        if style_type == 6:
            circ_r = (band_w / 2) * 0.9
        elif style_type == 4:
            circ_r = band_w / 2
        else:
            circ_r = band_w / 4
        if circ_r > 0:
            base_n = max(6, int(2 * math.pi * mid_r / (2 * circ_r)))
        else:
            base_n = num_elements
        cur_num_elements = max(4, base_n // 2)
    elif style_type == 11:
        cur_num_elements = max(4, num_elements // 2)
    else:
        cur_num_elements = num_elements

    angle_step = 360 / cur_num_elements

    if style_type == 10:
        steps = 400
        amplitude = band_w * 0.35
        waves = 12
        t.penup()
        for i in range(steps + 1):
            tt = i / steps
            a = 2 * math.pi * tt
            rr = mid_r + amplitude * math.sin(waves * a)
            x = rr * math.cos(a)
            y = rr * math.sin(a)
            if i == 0:
                t.goto(x, y); t.pendown()
            else:
                move_to(x, y)
        return

    if style_type == 12:
        steps = 400        
        amplitude = band_w * 0.25
        waves = 12
        for phase in (0, math.pi):
            t.penup()
            for i in range(steps + 1):
                tt = i / steps
                a = 2 * math.pi * tt
                rr = mid_r + amplitude * math.sin(waves * a + phase)
                x = rr * math.cos(a)
                y = rr * math.sin(a)
                if i == 0:
                    t.goto(x, y); t.pendown()
                else:
                    move_to(x, y)
        return

    for i in range(cur_num_elements):
        angle = math.radians(i * angle_step)
        mid_angle = math.radians((i + 0.5) * angle_step)
        next_angle = math.radians((i + 1) * angle_step)

        x_in = inner_r * math.cos(angle)
        y_in = inner_r * math.sin(angle)
        x_out = outer_r * math.cos(angle)
        y_out = outer_r * math.sin(angle)

        if style_type == 8 and (i % 2 == 1):
            continue

        if style_type == 1:
            t.penup(); t.goto(x_in, y_in); t.pendown(); move_to(x_out, y_out)

        elif style_type == 2:
            circ_r = band_w / 4
            cxc = mid_r * math.cos(angle)
            cyc = mid_r * math.sin(angle)
            if COLOR_ENABLED and element_color:
                t.fillcolor(element_color)
                t.begin_fill()
            t.penup(); t.goto(cxc, cyc - circ_r); t.setheading(0); t.pendown()
            t.circle(circ_r)
            if COLOR_ENABLED and element_color:
                t.end_fill()

        elif style_type == 3:
            x_mid_out = outer_r * math.cos(mid_angle)
            y_mid_out = outer_r * math.sin(mid_angle)
            x_next_in = inner_r * math.cos(next_angle)
            y_next_in = inner_r * math.sin(next_angle)
            t.penup(); t.goto(x_in, y_in); t.pendown()
            move_to(x_mid_out, y_mid_out)
            move_to(x_next_in, y_next_in)

        elif style_type == 4:
            outer_circ_r = band_w / 2
            inner_circ_r = band_w / 4
            cxc = mid_r * math.cos(angle)
            cyc = mid_r * math.sin(angle)
            color_outer = None
            color_inner = None
            if band_colors:
                color_outer = band_colors[1] if len(band_colors) >= 2 else band_colors[0]
                color_inner = band_colors[2] if len(band_colors) >= 3 else color_outer
            if COLOR_ENABLED and color_outer:
                t.fillcolor(color_outer)
                t.begin_fill()
            t.penup(); t.goto(cxc, cyc - outer_circ_r); t.setheading(0); t.pendown()
            t.circle(outer_circ_r)
            if COLOR_ENABLED and color_outer:
                t.end_fill()
            if COLOR_ENABLED and color_inner:
                t.fillcolor(color_inner)
                t.begin_fill()
            t.penup(); t.goto(cxc, cyc - inner_circ_r); t.setheading(0); t.pendown()
            t.circle(inner_circ_r)
            if COLOR_ENABLED and color_inner:
                t.end_fill()

        elif style_type == 5:
            shift = math.radians(angle_step * 0.15)
            for d in (-shift, shift):
                xi = inner_r * math.cos(angle + d)
                yi = inner_r * math.sin(angle + d)
                xo = outer_r * math.cos(angle + d)
                yo = outer_r * math.sin(angle + d)
                t.penup(); t.goto(xi, yi); t.pendown(); move_to(xo, yo)

        elif style_type == 6:
            circ_r = (band_w / 2) * 0.9
            cxc = mid_r * math.cos(angle)
            cyc = mid_r * math.sin(angle)
            if COLOR_ENABLED and element_color:
                t.fillcolor(element_color)
                t.begin_fill()
            t.penup(); t.goto(cxc, cyc - circ_r); t.setheading(0); t.pendown()
            t.circle(circ_r)
            if COLOR_ENABLED and element_color:
                t.end_fill()

        elif style_type == 7:
            half_side = band_w * 0.25
            size_ang = math.radians(angle_step * 0.35)
            corners_polar = [
                (mid_r - half_side, angle - size_ang),
                (mid_r - half_side, angle + size_ang),
                (mid_r + half_side, angle + size_ang),
                (mid_r + half_side, angle - size_ang),
            ]
            pts = [(r * math.cos(a), r * math.sin(a)) for r, a in corners_polar]
            pts.append(pts[0])
            t.penup(); t.goto(pts[0]); t.pendown()
            for p in pts[1:]:
                move_to(p[0], p[1])

        elif style_type == 8:
            R = band_w / 1.5
            base_x = inner_r * math.cos(angle)
            base_y = inner_r * math.sin(angle)
            outward = math.atan2(base_y, base_x)
            steps_arc = 20
            pts = []
            for k in range(steps_arc + 1):
                aa = outward - math.pi / 2 + math.pi * (k / steps_arc)
                px = base_x + R * math.cos(aa)
                py = base_y + R * math.sin(aa)
                pts.append((px, py))
            t.penup(); t.goto(pts[0]); t.pendown()
            for p in pts[1:]:
                move_to(p[0], p[1])

        elif style_type == 9:
            circ_r = band_w / 3
            cxc = mid_r * math.cos(angle)
            cyc = mid_r * math.sin(angle)
            if COLOR_ENABLED and element_color:
                t.fillcolor(element_color)
                t.begin_fill()
            t.penup(); t.goto(cxc, cyc - circ_r); t.setheading(0); t.pendown()
            t.circle(circ_r)
            if COLOR_ENABLED and element_color:
                t.end_fill()

        elif style_type == 11:
            half_long = band_w * 0.4
            half_short = band_w * 0.15
            pts_polar = [
                (mid_r + half_short, angle),
                (mid_r, angle + math.atan2(half_long, mid_r)),
                (mid_r - half_short, angle),
                (mid_r, angle - math.atan2(half_long, mid_r)),
            ]
            pts = [(r * math.cos(a), r * math.sin(a)) for r, a in pts_polar]
            pts.append(pts[0])
            t.penup(); t.goto(pts[0]); t.pendown()
            for p in pts[1:]:
                move_to(p[0], p[1])


def band1_run(r, w, colors=None): generic_band(r, w, style_band1, 36, colors)
def band2_run(r, w, colors=None): generic_band(r, w, style_band2, 48, colors)
def band3_run(r, w, colors=None): generic_band(r, w, style_band3, 64, colors)
def band4_run(r, w, colors=None): generic_band(r, w, style_band4, 80, colors)
def band5_run(r, w, colors=None): generic_band(r, w, style_band5, 96, colors)


# =====================================================================
# 17 СТИЛЕЙ ЛЕПЕСТКОВ (без 13)
# =====================================================================

def draw_layer_core(inner_r, outer_r, num_petals, layer_style_idx, level_colors):
    angle_step = 360 / num_petals
    half_angle = math.radians(angle_step / 2)

    if layer_style_idx == 2:
        mid_r = (inner_r + outer_r) / 2
        fill_frac = 0.6
        a_axis = (outer_r - inner_r) / 2 * fill_frac
        if a_axis > 0:
            n = max(4, int(round(2 * math.pi * mid_r / (2 * a_axis))))
        else:
            n = num_petals
        b_axis = math.pi * mid_r / n

        col_bg = level_colors[0] if len(level_colors) >= 1 else None
        col_outer = level_colors[1] if len(level_colors) >= 2 else col_bg
        col_inner = level_colors[2] if len(level_colors) >= 3 else col_outer

        if Config.PAINT_LAYER_RINGS and COLOR_ENABLED and col_bg:
            fill_ring(inner_r, outer_r, col_bg)

        for k in range(n):
            a = 2 * math.pi * k / n
            cxc = mid_r * math.cos(a)
            cyc = mid_r * math.sin(a)
            draw_oriented_oval(cxc, cyc, a, a_axis, b_axis,
                               fill_color=col_outer, outline_color=Config.LINE_COLOR)
            draw_oriented_oval(cxc, cyc, a, a_axis / 1.5, b_axis / 1.5,
                               fill_color=col_inner, outline_color=Config.LINE_COLOR)
        return

    for i in range(num_petals):
        angle = i * angle_step
        rad = math.radians(angle)

        if layer_style_idx == 1:
            rad_left = rad - half_angle
            rad_right = rad + half_angle
            x_top = outer_r * math.cos(rad); y_top = outer_r * math.sin(rad)
            x_b1 = inner_r * math.cos(rad_left); y_b1 = inner_r * math.sin(rad_left)
            x_b2 = inner_r * math.cos(rad_right); y_b2 = inner_r * math.sin(rad_right)
            x_m1 = ((inner_r + outer_r) / 2) * math.cos(rad_left + 0.05)
            y_m1 = ((inner_r + outer_r) / 2) * math.sin(rad_left + 0.05)
            x_m2 = ((inner_r + outer_r) / 2) * math.cos(rad_right - 0.05)
            y_m2 = ((inner_r + outer_r) / 2) * math.sin(rad_right - 0.05)
            if COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            t.penup(); t.goto(x_b1, y_b1); t.pendown()
            move_to(x_m1, y_m1); move_to(x_top, y_top); move_to(x_m2, y_m2); move_to(x_b2, y_b2)
            if COLOR_ENABLED and level_colors:
                move_to(x_b1, y_b1)
                t.end_fill()

            tip_r = (outer_r - inner_r) * 0.05 * 1.3
            step = 2.0 * tip_r
            r_dot_5 = inner_r + tip_r
            r_dot_4 = r_dot_5 + step
            r_dot_3 = r_dot_4 + step
            r_dot_1 = r_dot_3 + step
            r_dot_2 = r_dot_1 + step
            for r_dot in (r_dot_1, r_dot_2, r_dot_3, r_dot_4, r_dot_5):
                ccx = r_dot * math.cos(rad)
                ccy = r_dot * math.sin(rad)
                t.penup(); t.goto(ccx, ccy - tip_r); t.setheading(0); t.pendown()
                t.pencolor(Config.LINE_COLOR)
                t.fillcolor(Config.BG_COLOR)
                t.begin_fill()
                t.circle(tip_r)
                t.end_fill()
                t.pencolor(Config.LINE_COLOR)

        elif layer_style_idx == 3:
            outer_r2 = inner_r + (outer_r - inner_r) * 0.75
            half2 = half_angle * 0.45
            if COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r, rad, half_angle, shape_leaf))
            if COLOR_ENABLED and level_colors:
                t.end_fill()
            if COLOR_ENABLED and len(level_colors) >= 2:
                t.fillcolor(level_colors[1])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r2, rad, half2, shape_leaf))
            if COLOR_ENABLED and len(level_colors) >= 2:
                t.end_fill()
            r_line_end = inner_r + (outer_r2 - inner_r) * 0.7
            t.penup()
            t.goto(inner_r * math.cos(rad), inner_r * math.sin(rad))
            t.pendown()
            move_to(r_line_end * math.cos(rad), r_line_end * math.sin(rad))

        elif layer_style_idx == 4:
            # --- Классический лист ---
            if COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r, rad, half_angle, shape_leaf))
            if COLOR_ENABLED and level_colors:
                t.end_fill()

            # Белая точка с чёрной обводкой ровно посередине лепестка
            tip_r = (outer_r - inner_r) * 0.05 * 1.3
            r_mid = (inner_r + outer_r) / 2
            ccx = r_mid * math.cos(rad)
            ccy = r_mid * math.sin(rad)
            t.penup(); t.goto(ccx, ccy - tip_r); t.setheading(0); t.pendown()
            t.pencolor(Config.LINE_COLOR)
            t.fillcolor(Config.BG_COLOR)
            t.begin_fill()
            t.circle(tip_r)
            t.end_fill()
            t.pencolor(Config.LINE_COLOR)

            # Отрезок от точки белой окружности, БЛИЖАЙШЕЙ К ЦЕНТРУ МАНДАЛЫ,
            # по направлению к центру мандалы до пересечения
            # с внешней окружностью предыдущего кольца (= на радиусе inner_r).
            # Единичный вектор от центра мандалы к центру белой точки:
            if r_mid > 0:
                ux = ccx / r_mid
                uy = ccy / r_mid
            else:
                ux, uy = 0.0, 0.0
            # Точка на белой окружности, ближайшая к центру мандалы:
            start_x = ccx - ux * tip_r
            start_y = ccy - uy * tip_r
            target_x = inner_r * math.cos(rad)
            target_y = inner_r * math.sin(rad)
            t.penup(); t.goto(start_x, start_y); t.pendown()
            move_to(target_x, target_y)

        elif layer_style_idx == 5:
            if COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r, rad, half_angle, shape_leaf))
            if COLOR_ENABLED and level_colors:
                t.end_fill()
            t.penup()
            t.goto(inner_r * math.cos(rad), inner_r * math.sin(rad))
            t.pendown()
            move_to(outer_r * math.cos(rad), outer_r * math.sin(rad))
            for k in range(1, 4):
                tt = k / 4.5
                r_mid = inner_r + (outer_r - inner_r) * tt
                mx = r_mid * math.cos(rad)
                my = r_mid * math.sin(rad)
                width_at_mid = half_angle * math.sin(math.pi * tt) * r_mid
                coef = 0.85 if k < 3 else 0.51
                side_len = width_at_mid * coef
                lx = mx + side_len * math.cos(rad - math.pi / 4)
                ly = my + side_len * math.sin(rad - math.pi / 4)
                rx = mx + side_len * math.cos(rad + math.pi / 4)
                ry = my + side_len * math.sin(rad + math.pi / 4)
                t.penup(); t.goto(mx, my); t.pendown(); move_to(lx, ly)
                t.penup(); t.goto(mx, my); t.pendown(); move_to(rx, ry)

        elif layer_style_idx == 6:
            if i % 2 == 1:
                outer_r_eff = inner_r + (outer_r - inner_r) * 0.7 * 0.85
                half_sub = half_angle / 2
                for sub_sign in (-1, +1):
                    rad_sub = rad + sub_sign * half_sub
                    steps = 16
                    pts = []
                    for s in range(steps + 1):
                        tt_norm = s / steps
                        tt_leaf = 0.5 + tt_norm * 0.5
                        r = inner_r + (outer_r_eff - inner_r) * tt_norm
                        off = half_sub * math.sin(math.pi * tt_leaf)
                        a = rad_sub - off
                        pts.append((r * math.cos(a), r * math.sin(a)))
                    for s in range(steps, -1, -1):
                        tt_norm = s / steps
                        tt_leaf = 0.5 + tt_norm * 0.5
                        r = inner_r + (outer_r_eff - inner_r) * tt_norm
                        off = half_sub * math.sin(math.pi * tt_leaf)
                        a = rad_sub + off
                        pts.append((r * math.cos(a), r * math.sin(a)))
                    if COLOR_ENABLED and level_colors:
                        t.fillcolor(level_colors[0])
                        t.begin_fill()
                    draw_polyline(pts)
                    if COLOR_ENABLED and level_colors:
                        t.end_fill()
            else:
                outer_r_eff = outer_r
                steps = 16
                pts = []
                for s in range(steps + 1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (outer_r_eff - inner_r) * tt_norm
                    off = half_angle * math.sin(math.pi * tt_leaf)
                    a = rad - off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                for s in range(steps, -1, -1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (outer_r_eff - inner_r) * tt_norm
                    off = half_angle * math.sin(math.pi * tt_leaf)
                    a = rad + off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                if COLOR_ENABLED and level_colors:
                    t.fillcolor(level_colors[0])
                    t.begin_fill()
                draw_polyline(pts)
                if COLOR_ENABLED and level_colors:
                    t.end_fill()

        elif layer_style_idx == 7:
            outer_r2 = inner_r + (outer_r - inner_r) * 0.85
            half2 = half_angle * 0.35
            if COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r, rad, half_angle, shape_leaf))
            if COLOR_ENABLED and level_colors:
                t.end_fill()
            if COLOR_ENABLED and len(level_colors) >= 2:
                t.fillcolor(level_colors[1])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r2, rad, half2, shape_leaf))
            if COLOR_ENABLED and len(level_colors) >= 2:
                t.end_fill()

        elif layer_style_idx == 8:
            def shape_8(tt):
                s = math.sin(math.pi * tt)
                return s * (1 - 0.15 * s)
            if COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r, rad, half_angle, shape_8))
            if COLOR_ENABLED and level_colors:
                t.end_fill()
            tip_r = (outer_r - inner_r) * 0.05 * 1.3
            r_mid = (inner_r + outer_r) / 2
            r_circle_2 = r_mid - (outer_r - inner_r) * 0.2 + (outer_r - inner_r) * 0.22
            r_circle_1 = r_circle_2 - 2 * tip_r
            r_circle_3 = r_circle_2 + 2 * tip_r
            for r_circle in (r_circle_1, r_circle_2, r_circle_3):
                ccx = r_circle * math.cos(rad)
                ccy = r_circle * math.sin(rad)
                t.penup(); t.goto(ccx, ccy - tip_r); t.setheading(0); t.pendown()
                t.fillcolor(Config.BG_COLOR)
                t.begin_fill(); t.circle(tip_r); t.end_fill()
            t.fillcolor(Config.LINE_COLOR)

            r_edge = r_circle_1 - tip_r
            edge_x = r_edge * math.cos(rad)
            edge_y = r_edge * math.sin(rad)
            base_x = inner_r * math.cos(rad)
            base_y = inner_r * math.sin(rad)
            t.penup(); t.goto(edge_x, edge_y); t.pendown()
            move_to(base_x, base_y)

        elif layer_style_idx == 9:
            outer_r2 = inner_r + (outer_r - inner_r) * 0.85
            half2 = half_angle * 0.55
            outer_r3 = inner_r + (outer_r - inner_r) * 0.62
            half3 = half_angle * 0.30
            if COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r, rad, half_angle, shape_leaf))
            if COLOR_ENABLED and level_colors:
                t.end_fill()
            if COLOR_ENABLED and len(level_colors) >= 2:
                t.fillcolor(level_colors[1])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r2, rad, half2, shape_leaf))
            if COLOR_ENABLED and len(level_colors) >= 2:
                t.end_fill()
            if COLOR_ENABLED and len(level_colors) >= 3:
                t.fillcolor(level_colors[2])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r3, rad, half3, shape_leaf))
            if COLOR_ENABLED and len(level_colors) >= 3:
                t.end_fill()

        elif layer_style_idx == 10:
            steps = 16
            pts = []
            for s in range(steps + 1):
                tt_norm = s / steps
                tt_leaf = 0.5 + tt_norm * 0.5
                r = inner_r + (outer_r - inner_r) * tt_norm
                off = half_angle * (math.sin(math.pi * tt_leaf) ** 0.6)
                a = rad - off
                pts.append((r * math.cos(a), r * math.sin(a)))
            for s in range(steps, -1, -1):
                tt_norm = s / steps
                tt_leaf = 0.5 + tt_norm * 0.5
                r = inner_r + (outer_r - inner_r) * tt_norm
                off = half_angle * (math.sin(math.pi * tt_leaf) ** 0.6)
                a = rad + off
                pts.append((r * math.cos(a), r * math.sin(a)))
            if COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(pts)
            if COLOR_ENABLED and level_colors:
                t.end_fill()

            # --- три прожилки: центральная + две боковые ---
            shorten = 0.80
            dot_r = (outer_r - inner_r) * 0.10 * 0.75
            if dot_r < 0.5:
                dot_r = 0.5

            base_x = inner_r * math.cos(rad)
            base_y = inner_r * math.sin(rad)

            r_line_full = inner_r + (outer_r - inner_r) * 0.8
            r_line_end = inner_r + (r_line_full - inner_r) * shorten
            t.penup()
            t.goto(base_x, base_y)
            t.pendown()
            end_c_x = r_line_end * math.cos(rad)
            end_c_y = r_line_end * math.sin(rad)
            move_to(end_c_x, end_c_y)
            dot_cx = end_c_x + dot_r * math.cos(rad)
            dot_cy = end_c_y + dot_r * math.sin(rad)
            t.penup(); t.goto(dot_cx, dot_cy - dot_r); t.setheading(0); t.pendown()
            t.pencolor(Config.LINE_COLOR)
            t.fillcolor(Config.BG_COLOR)
            t.begin_fill(); t.circle(dot_r); t.end_fill()
            t.pencolor(Config.LINE_COLOR)

            line_len_full = (outer_r - inner_r) * 0.4
            line_len = line_len_full * shorten
            for d_ang in (math.radians(20), math.radians(-20)):
                a_new = rad + d_ang
                ex = base_x + line_len * math.cos(a_new)
                ey = base_y + line_len * math.sin(a_new)
                t.penup(); t.goto(base_x, base_y); t.pendown()
                move_to(ex, ey)
                dot_bx = ex + dot_r * math.cos(a_new)
                dot_by = ey + dot_r * math.sin(a_new)
                t.penup(); t.goto(dot_bx, dot_by - dot_r); t.setheading(0); t.pendown()
                t.pencolor(Config.LINE_COLOR)
                t.fillcolor(Config.BG_COLOR)
                t.begin_fill(); t.circle(dot_r); t.end_fill()
                t.pencolor(Config.LINE_COLOR)

        elif layer_style_idx == 11:
            steps = 16
            for idx_s, scale in enumerate((1.0, 0.7)):
                orr = inner_r + (outer_r - inner_r) * scale
                half_scale = half_angle * scale
                pts = []
                for s in range(steps + 1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr - inner_r) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad - off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                for s in range(steps, -1, -1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr - inner_r) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad + off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                if COLOR_ENABLED and level_colors and idx_s < len(level_colors):
                    t.fillcolor(level_colors[idx_s])
                    t.begin_fill()
                draw_polyline(pts)
                if COLOR_ENABLED and level_colors and idx_s < len(level_colors):
                    t.end_fill()

        elif layer_style_idx == 12:
            def drop_halfwidth(tt):
                return 2.0 * math.sqrt(tt * (1.0 - tt))

            steps = 24
            pts_left = []
            pts_right = []
            for s in range(steps + 1):
                tt = s / steps
                rr = inner_r + (outer_r - inner_r) * tt
                off = half_angle * drop_halfwidth(tt)
                if off > half_angle:
                    off = half_angle
                a_l = rad - off
                a_r = rad + off
                pts_left.append((rr * math.cos(a_l), rr * math.sin(a_l)))
                pts_right.append((rr * math.cos(a_r), rr * math.sin(a_r)))
            pts = pts_left + pts_right[::-1]

            if COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(pts)
            if COLOR_ENABLED and level_colors:
                t.end_fill()

            t.pencolor(Config.LINE_COLOR)
            r_tip = inner_r + (outer_r - inner_r) * 0.78
            t.penup()
            t.goto(inner_r * math.cos(rad), inner_r * math.sin(rad))
            t.pendown()
            move_to(r_tip * math.cos(rad), r_tip * math.sin(rad))

            side_fracs = (0.18, 0.34, 0.50, 0.64)
            for frac in side_fracs:
                r_mid = inner_r + (outer_r - inner_r) * frac
                mx = r_mid * math.cos(rad)
                my = r_mid * math.sin(rad)
                width_at_mid = half_angle * math.sin(math.pi * frac) * r_mid
                side_len = width_at_mid * 0.40
                local_hw = half_angle * drop_halfwidth(frac) * r_mid
                if side_len > local_hw * 0.55:
                    side_len = local_hw * 0.55
                lx = mx + side_len * math.cos(rad - math.pi / 3)
                ly = my + side_len * math.sin(rad - math.pi / 3)
                rx = mx + side_len * math.cos(rad + math.pi / 3)
                ry = my + side_len * math.sin(rad + math.pi / 3)
                t.penup(); t.goto(mx, my); t.pendown(); move_to(lx, ly)
                t.penup(); t.goto(mx, my); t.pendown(); move_to(rx, ry)

        elif layer_style_idx == 14:
            rad_left = rad - half_angle
            rad_right = rad + half_angle
            x_b1 = inner_r * math.cos(rad_left); y_b1 = inner_r * math.sin(rad_left)
            x_b2 = inner_r * math.cos(rad_right); y_b2 = inner_r * math.sin(rad_right)
            for idx_s, scale in enumerate((1.0, 0.5)):
                c_out = inner_r + (outer_r - inner_r) * scale
                col = None
                if level_colors:
                    col = level_colors[idx_s] if idx_s < len(level_colors) else level_colors[-1]
                if COLOR_ENABLED and col:
                    t.fillcolor(col)
                    t.begin_fill()
                t.penup(); t.goto(x_b1, y_b1); t.pendown()
                move_to(c_out * math.cos(rad), c_out * math.sin(rad))
                move_to(x_b2, y_b2)
                move_to(x_b1, y_b1)
                if COLOR_ENABLED and col:
                    t.end_fill()

            # Белая точка с чёрной обводкой в центре меньшего (внутреннего)
            # треугольника, сдвинутая к центру мандалы на 1,5 диаметра точки.
            dot_r = (outer_r - inner_r) * 0.10 * 0.75
            if dot_r < 0.5:
                dot_r = 0.5
            r_small_centroid = inner_r + (outer_r - inner_r) * 0.5 * (2.0 / 3.0)
            r_small_centroid -= 3.0 * dot_r
            ccx = r_small_centroid * math.cos(rad)
            ccy = r_small_centroid * math.sin(rad)
            t.penup(); t.goto(ccx, ccy - dot_r); t.setheading(0); t.pendown()
            t.pencolor(Config.LINE_COLOR)
            t.fillcolor(Config.BG_COLOR)
            t.begin_fill(); t.circle(dot_r); t.end_fill()
            t.pencolor(Config.LINE_COLOR)

        elif layer_style_idx == 15:
            steps = 16
            for idx_s, scale in enumerate((1.0, 0.65)):
                orr = inner_r + (outer_r - inner_r) * scale
                half_scale = half_angle * scale
                pts = []
                for s in range(steps + 1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr - inner_r) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad - off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                for s in range(steps, -1, -1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr - inner_r) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad + off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                col = None
                if level_colors:
                    col = level_colors[idx_s] if idx_s < len(level_colors) else level_colors[-1]
                if COLOR_ENABLED and col:
                    t.fillcolor(col)
                    t.begin_fill()
                draw_polyline(pts)
                if COLOR_ENABLED and col:
                    t.end_fill()

            inner_scale = 0.65
            ir = inner_r + (outer_r - inner_r) * (1 - inner_scale) / 2
            orr2 = inner_r + (outer_r - inner_r) * (1 + inner_scale) / 2
            r_mid_inner = (ir + orr2) / 2 - (orr2 - ir) * 0.4
            ccx = r_mid_inner * math.cos(rad)
            ccy = r_mid_inner * math.sin(rad)
            dot_r = (orr2 - ir) * 0.105
            if dot_r < 0.5:
                dot_r = 0.5
            t.penup()
            t.goto(ccx, ccy - dot_r)
            t.setheading(0)
            t.pendown()
            t.pencolor(Config.LINE_COLOR)
            t.fillcolor(Config.BG_COLOR)
            t.begin_fill()
            t.circle(dot_r)
            t.end_fill()
            t.pencolor(Config.LINE_COLOR)

            # Отрезок от ближайшей к центру мандалы точки белой окружности
            # до пересечения с внешней окружностью предыдущего кольца (r = inner_r).
            if r_mid_inner > 0:
                ux = ccx / r_mid_inner
                uy = ccy / r_mid_inner
            else:
                ux, uy = 0.0, 0.0
            start_x = ccx - ux * dot_r
            start_y = ccy - uy * dot_r
            target_x = inner_r * math.cos(rad)
            target_y = inner_r * math.sin(rad)
            t.penup(); t.goto(start_x, start_y); t.pendown()
            move_to(target_x, target_y)

        elif layer_style_idx == 16:
            for idx_s, (scale, half_scale) in enumerate((
                    (1.0, half_angle),
                    (0.65, half_angle * 0.65))):
                orr2 = inner_r + (outer_r - inner_r) * scale
                steps = 16
                pts = []
                for s in range(steps + 1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr2 - inner_r) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad - off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                for s in range(steps, -1, -1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr2 - inner_r) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad + off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                col = None
                if level_colors:
                    col = level_colors[idx_s] if idx_s < len(level_colors) else level_colors[-1]
                if COLOR_ENABLED and col:
                    t.fillcolor(col)
                    t.begin_fill()
                draw_polyline(pts)
                if COLOR_ENABLED and col:
                    t.end_fill()
            inner_scale = 0.65
            ir = inner_r + (outer_r - inner_r) * (1 - inner_scale) / 2
            orr2 = inner_r + (outer_r - inner_r) * (1 + inner_scale) / 2
            r_mid_inner = (ir + orr2) / 2 - (orr2 - ir) * 0.40
            ccx = r_mid_inner * math.cos(rad)
            ccy = r_mid_inner * math.sin(rad)
            dot_r = (orr2 - ir) * 0.125
            t.penup(); t.goto(ccx, ccy - dot_r); t.setheading(0); t.pendown()
            t.fillcolor(Config.BG_COLOR)
            t.begin_fill()
            t.circle(dot_r)
            t.end_fill()

        elif layer_style_idx == 17:
            tip_r = outer_r
            base_r = inner_r
            half_r = half_angle * 0.75
            r_mid_rhombus = (inner_r + outer_r) / 2
            dot_r = (outer_r - inner_r) * 0.10 * 0.85
            if dot_r < 0.5:
                dot_r = 0.5
            offsets = [0.0]
            if i % 2 == 0:
                offsets.append(0.5)
            for offset_frac in offsets:
                rad_off = rad + math.radians(angle_step * offset_frac)
                pts = [
                    (base_r * math.cos(rad_off), base_r * math.sin(rad_off)),
                    (((base_r + tip_r) / 2) * math.cos(rad_off - half_r),
                     ((base_r + tip_r) / 2) * math.sin(rad_off - half_r)),
                    (tip_r * math.cos(rad_off), tip_r * math.sin(rad_off)),
                    (((base_r + tip_r) / 2) * math.cos(rad_off + half_r),
                     ((base_r + tip_r) / 2) * math.sin(rad_off + half_r)),
                ]
                if COLOR_ENABLED and level_colors:
                    t.fillcolor(level_colors[0])
                    t.begin_fill()
                draw_polyline(pts)
                if COLOR_ENABLED and level_colors:
                    t.end_fill()

                ccx = r_mid_rhombus * math.cos(rad_off)
                ccy = r_mid_rhombus * math.sin(rad_off)
                t.penup()
                t.goto(ccx, ccy - dot_r)
                t.setheading(0)
                t.pendown()
                t.pencolor(Config.LINE_COLOR)
                t.fillcolor(Config.BG_COLOR)
                t.begin_fill()
                t.circle(dot_r)
                t.end_fill()
                t.pencolor(Config.LINE_COLOR)

                inner_vx = base_r * math.cos(rad_off)
                inner_vy = base_r * math.sin(rad_off)
                r_dot_near = r_mid_rhombus - dot_r
                dot_near_x = r_dot_near * math.cos(rad_off)
                dot_near_y = r_dot_near * math.sin(rad_off)
                t.penup(); t.goto(inner_vx, inner_vy); t.pendown()
                move_to(dot_near_x, dot_near_y)

        elif layer_style_idx == 18:
            if COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r, rad, half_angle, shape_leaf))
            if COLOR_ENABLED and level_colors:
                t.end_fill()
            inner_scale = 0.65
            ir = inner_r + (outer_r - inner_r) * (1 - inner_scale) / 2
            orr2 = inner_r + (outer_r - inner_r) * (1 + inner_scale) / 2
            inner_col = None
            if level_colors:
                inner_col = level_colors[1] if len(level_colors) >= 2 else level_colors[0]
            if COLOR_ENABLED and inner_col:
                t.fillcolor(inner_col)
                t.begin_fill()
            draw_polyline(petal_points(ir, orr2, rad, half_angle * inner_scale, shape_leaf))
            if COLOR_ENABLED and inner_col:
                t.end_fill()

            # Белая точка с чёрной обводкой в центре внутреннего листа.
            dot_r = (outer_r - inner_r) * 0.10 * 0.75
            if dot_r < 0.5:
                dot_r = 0.5
            r_inner_center = (ir + orr2) / 2
            ccx = r_inner_center * math.cos(rad)
            ccy = r_inner_center * math.sin(rad)
            t.penup(); t.goto(ccx, ccy - dot_r); t.setheading(0); t.pendown()
            t.pencolor(Config.LINE_COLOR)
            t.fillcolor(Config.BG_COLOR)
            t.begin_fill(); t.circle(dot_r); t.end_fill()
            t.pencolor(Config.LINE_COLOR)


def draw_oriented_oval(cx, cy, rotation, a_axis, b_axis,
                       fill_color=None, outline_color=None):
    steps = 60
    cos_r = math.cos(rotation)
    sin_r = math.sin(rotation)
    pts = []
    for k in range(steps):
        theta = 2 * math.pi * k / steps
        lx = a_axis * math.cos(theta)
        ly = b_axis * math.sin(theta)
        gx = cx + lx * cos_r - ly * sin_r
        gy = cy + lx * sin_r + ly * cos_r
        pts.append((gx, gy))

    if fill_color and COLOR_ENABLED:
        t.fillcolor(fill_color)
        t.begin_fill()
    if outline_color:
        t.pencolor(outline_color)
    t.penup(); t.goto(pts[0]); t.pendown()
    for p in pts[1:]:
        move_to(p[0], p[1])
    move_to(pts[0][0], pts[0][1])
    if fill_color and COLOR_ENABLED:
        t.end_fill()
    t.pencolor(Config.LINE_COLOR)


# ---------------------------------------------------------------------
# A4: слои принимают ОТДЕЛЬНО ring_color и petal_colors
# ---------------------------------------------------------------------
def layer1_run(r_in, ring_color, petal_colors):
    r_out = r_in + Config.L1_WIDTH
    if Config.PAINT_LAYER_RINGS and COLOR_ENABLED and ring_color:
        fill_ring(r_in, r_out, ring_color)
    draw_layer_core(r_in, r_out, 16, style_layer1, petal_colors)


def layer2_run(r_in, ring_color, petal_colors):
    r_out = r_in + Config.L2_WIDTH
    if Config.PAINT_LAYER_RINGS and COLOR_ENABLED and ring_color:
        fill_ring(r_in, r_out, ring_color)
    draw_layer_core(r_in, r_out, 14, style_layer2, petal_colors)


def layer3_run(r_in, ring_color, petal_colors):
    r_out = r_in + Config.L3_WIDTH
    if Config.PAINT_LAYER_RINGS and COLOR_ENABLED and ring_color:
        fill_ring(r_in, r_out, ring_color)
    draw_layer_core(r_in, r_out, 24, style_layer3, petal_colors)


def layer4_run(r_in, ring_color, petal_colors):
    r_out = r_in + Config.L4_WIDTH
    if Config.PAINT_LAYER_RINGS and COLOR_ENABLED and ring_color:
        fill_ring(r_in, r_out, ring_color)
    draw_layer_core(r_in, r_out, 32, style_layer4, petal_colors)


def layer5_run(r_in, ring_color, petal_colors):
    r_out = r_in + Config.L5_WIDTH
    if Config.PAINT_LAYER_RINGS and COLOR_ENABLED and ring_color:
        fill_ring(r_in, r_out, ring_color)
    draw_layer_core(r_in, r_out, 40, style_layer5, petal_colors)


# =====================================================================
# ВЫБОР СТИЛЕЙ
# =====================================================================
_t0 = time.perf_counter()
style_center = weighted_choice_styles(
    list(Config.CENTER_STYLES.keys()),
    Config.CENTER_STYLES
)

band_styles = pick_styles_with_rules(5, Config.BAND_STYLES, max_repeat=1)
style_band1, style_band2, style_band3, style_band4, style_band5 = band_styles

layer_styles = pick_styles_with_rules(5, Config.LAYER_STYLES, max_repeat=1)
style_layer1, style_layer2, style_layer3, style_layer4, style_layer5 = layer_styles
_tmark("select_styles", _t0)

# ---------------------------------------------------------------------
# ВЫБОР ЦВЕТОВ
# ---------------------------------------------------------------------
recent_colors = []
_fallback_warnings = []

prev_colors = set()
prev2_colors = set()


def advance_history(area_colors):
    global prev_colors, prev2_colors
    prev2_colors = set(prev_colors)
    prev_colors = set(area_colors)


def colors_count_for_center(style_idx):
    if style_idx in (2, 9):
        return 2
    return 1

def colors_count_for_band(style_idx):
    if style_idx == 4:
        return 3
    if style_idx in (2, 6, 9):
        return 2
    return 1

def colors_count_for_layer(style_idx):
    if style_idx == 2:
        return 3
    if style_idx in (3, 7, 9, 11, 15, 16):
        return 3
    return 2


def pick_colors_for(n, forbidden_hard=None, forbidden_soft=None, area_label=""):
    colors = []
    for _ in range(n):
        c, fb_stage = pick_color_no_adjacent(
            recent_colors, ACTIVE_PALETTE,
            forbidden_hard=forbidden_hard,
            forbidden_soft=forbidden_soft,
        )
        if fb_stage == 1:
            _fallback_warnings.append(
                f"область '{area_label}': ослаблен запрет на позапрошлую область"
            )
        elif fb_stage == 2:
            _fallback_warnings.append(
                f"область '{area_label}': ослаблен запрет на предыдущую область"
            )
        colors.append(c)
        recent_colors.append(c)
        if len(recent_colors) > 2:
            recent_colors.pop(0)
    return colors


_t0 = time.perf_counter()

n_center = colors_count_for_center(style_center) if COLOR_ENABLED else 0
center_colors = pick_colors_for(
    n_center,
    forbidden_hard=prev_colors,
    forbidden_soft=prev2_colors,
    area_label="центр"
) if COLOR_ENABLED else []
advance_history(center_colors)

n_b1 = colors_count_for_band(style_band1) if COLOR_ENABLED else 0
colors_band1 = pick_colors_for(
    n_b1,
    forbidden_hard=prev_colors,
    forbidden_soft=prev2_colors,
    area_label="лента 1"
) if COLOR_ENABLED else []
advance_history(colors_band1)

if COLOR_ENABLED:
    ring_color_layer1 = pick_colors_for(
        1,
        forbidden_hard=prev_colors,
        forbidden_soft=prev2_colors,
        area_label="кольцо слоя 1"
    )[0] if Config.PAINT_LAYER_RINGS else None
else:
    ring_color_layer1 = None
forbidden_hard_layer = set(prev_colors) | ({ring_color_layer1} if ring_color_layer1 else set())
n_l1 = colors_count_for_layer(style_layer1) if COLOR_ENABLED else 0
colors_layer1 = pick_colors_for(
    n_l1,
    forbidden_hard=forbidden_hard_layer,
    forbidden_soft=prev2_colors,
    area_label="слой 1"
) if COLOR_ENABLED else []
advance_history(set(colors_layer1) | ({ring_color_layer1} if ring_color_layer1 else set()))

n_b2 = colors_count_for_band(style_band2) if COLOR_ENABLED else 0
colors_band2 = pick_colors_for(
    n_b2,
    forbidden_hard=prev_colors,
    forbidden_soft=prev2_colors,
    area_label="лента 2"
) if COLOR_ENABLED else []
advance_history(colors_band2)

if COLOR_ENABLED:
    ring_color_layer2 = pick_colors_for(
        1,
        forbidden_hard=prev_colors,
        forbidden_soft=prev2_colors,
        area_label="кольцо слоя 2"
    )[0] if Config.PAINT_LAYER_RINGS else None
else:
    ring_color_layer2 = None
forbidden_hard_layer = set(prev_colors) | ({ring_color_layer2} if ring_color_layer2 else set())
n_l2 = colors_count_for_layer(style_layer2) if COLOR_ENABLED else 0
colors_layer2 = pick_colors_for(
    n_l2,
    forbidden_hard=forbidden_hard_layer,
    forbidden_soft=prev2_colors,
    area_label="слой 2"
) if COLOR_ENABLED else []
advance_history(set(colors_layer2) | ({ring_color_layer2} if ring_color_layer2 else set()))

n_b3 = colors_count_for_band(style_band3) if COLOR_ENABLED else 0
colors_band3 = pick_colors_for(
    n_b3,
    forbidden_hard=prev_colors,
    forbidden_soft=prev2_colors,
    area_label="лента 3"
) if COLOR_ENABLED else []
advance_history(colors_band3)

if COLOR_ENABLED:
    ring_color_layer3 = pick_colors_for(
        1,
        forbidden_hard=prev_colors,
        forbidden_soft=prev2_colors,
        area_label="кольцо слоя 3"
    )[0] if Config.PAINT_LAYER_RINGS else None
else:
    ring_color_layer3 = None
forbidden_hard_layer = set(prev_colors) | ({ring_color_layer3} if ring_color_layer3 else set())
n_l3 = colors_count_for_layer(style_layer3) if COLOR_ENABLED else 0
colors_layer3 = pick_colors_for(
    n_l3,
    forbidden_hard=forbidden_hard_layer,
    forbidden_soft=prev2_colors,
    area_label="слой 3"
) if COLOR_ENABLED else []
advance_history(set(colors_layer3) | ({ring_color_layer3} if ring_color_layer3 else set()))

n_b4 = colors_count_for_band(style_band4) if COLOR_ENABLED else 0
colors_band4 = pick_colors_for(
    n_b4,
    forbidden_hard=prev_colors,
    forbidden_soft=prev2_colors,
    area_label="лента 4"
) if COLOR_ENABLED else []
advance_history(colors_band4)

if COLOR_ENABLED:
    ring_color_layer4 = pick_colors_for(
        1,
        forbidden_hard=prev_colors,
        forbidden_soft=prev2_colors,
        area_label="кольцо слоя 4"
    )[0] if Config.PAINT_LAYER_RINGS else None
else:
    ring_color_layer4 = None
forbidden_hard_layer = set(prev_colors) | ({ring_color_layer4} if ring_color_layer4 else set())
n_l4 = colors_count_for_layer(style_layer4) if COLOR_ENABLED else 0
colors_layer4 = pick_colors_for(
    n_l4,
    forbidden_hard=forbidden_hard_layer,
    forbidden_soft=prev2_colors,
    area_label="слой 4"
) if COLOR_ENABLED else []
advance_history(set(colors_layer4) | ({ring_color_layer4} if ring_color_layer4 else set()))

n_b5 = colors_count_for_band(style_band5) if COLOR_ENABLED else 0
colors_band5 = pick_colors_for(
    n_b5,
    forbidden_hard=prev_colors,
    forbidden_soft=prev2_colors,
    area_label="лента 5"
) if COLOR_ENABLED else []
advance_history(colors_band5)

if COLOR_ENABLED:
    ring_color_layer5 = pick_colors_for(
        1,
        forbidden_hard=prev_colors,
        forbidden_soft=prev2_colors,
        area_label="кольцо слоя 5"
    )[0] if Config.PAINT_LAYER_RINGS else None
else:
    ring_color_layer5 = None
forbidden_hard_layer = set(prev_colors) | ({ring_color_layer5} if ring_color_layer5 else set())
n_l5 = colors_count_for_layer(style_layer5) if COLOR_ENABLED else 0
colors_layer5 = pick_colors_for(
    n_l5,
    forbidden_hard=forbidden_hard_layer,
    forbidden_soft=prev2_colors,
    area_label="слой 5"
) if COLOR_ENABLED else []
advance_history(set(colors_layer5) | ({ring_color_layer5} if ring_color_layer5 else set()))

_tmark("select_colors", _t0)


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


now = datetime.datetime.now()
date_str = now.strftime("%Y-%m-%d")
time_str = now.strftime("%H:%M:%S")
month_str = now.strftime("%Y-%m")
random_id = random.randint(10000, 99999)
mandala_name = f"{date_str}-mandala-{random_id}"

log_dir = "log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file_path = os.path.join(log_dir, f"{month_str}-log.txt")

if SELECTED_FAMILY == "all":
    family_log = "all (все семейства в одном пуле)"
else:
    fam_comment = Config.COLOR_FAMILIES[SELECTED_FAMILY].get("comment", "")
    family_log = f"{SELECTED_FAMILY} ({fam_comment})"

log_report = (
    f"==================================================\n"
    f"Генерация Мандалы\n"
    f"Дата: {date_str} | Время старта: {time_str}\n"
    f"Раскраска: {'включена' if COLOR_ENABLED else 'выключена'} "
    f"(режим: {Config.COLOR_MODE})\n"
    f"Семейство цветов: {family_log}\n"
    f"Скорость рисования: {Config.DRAW_SPEED_LEVEL} "
    f"(пауза {Config._effective_pause:.5f} с, пачка {Config._batch_size} шагов)\n"
    f"--------------------------------------------------\n"
    f" Выбранные узоры по областям:\n"
    f"  1. Центральный круг:      Вариант {style_center} ({Config.CENTER_STYLES[style_center]['name']})"
    f"{format_colors(center_colors)}\n"
    f"  2. Разделительная лента 1: Вариант {style_band1} ({Config.BAND_STYLES[style_band1]['name']})"
    f"{format_colors(colors_band1)}\n"
    f"  3. Уровень 1:              Вариант {style_layer1} ({Config.LAYER_STYLES[style_layer1]['name']})"
    f"{format_layer_colors(colors_layer1, ring_color_layer1)}\n"
    f"  4. Разделительная лента 2: Вариант {style_band2} ({Config.BAND_STYLES[style_band2]['name']})"
    f"{format_colors(colors_band2)}\n"
    f"  5. Уровень 2:              Вариант {style_layer2} ({Config.LAYER_STYLES[style_layer2]['name']})"
    f"{format_layer_colors(colors_layer2, ring_color_layer2)}\n"
    f"  6. Разделительная лента 3: Вариант {style_band3} ({Config.BAND_STYLES[style_band3]['name']})"
    f"{format_colors(colors_band3)}\n"
    f"  7. Уровень 3:              Вариант {style_layer3} ({Config.LAYER_STYLES[style_layer3]['name']})"
    f"{format_layer_colors(colors_layer3, ring_color_layer3)}\n"
    f"  8. Разделительная лента 4: Вариант {style_band4} ({Config.BAND_STYLES[style_band4]['name']})"
    f"{format_colors(colors_band4)}\n"
    f"  9. Уровень 4:              Вариант {style_layer4} ({Config.LAYER_STYLES[style_layer4]['name']})"
    f"{format_layer_colors(colors_layer4, ring_color_layer4)}\n"
    f" 10. Разделительная лента 5: Вариант {style_band5} ({Config.BAND_STYLES[style_band5]['name']})"
    f"{format_colors(colors_band5)}\n"
    f" 11. Уровень 5:              Вариант {style_layer5} ({Config.LAYER_STYLES[style_layer5]['name']})"
    f"{format_layer_colors(colors_layer5, ring_color_layer5)}\n"
    f"--------------------------------------------------\n"
)

if _fallback_warnings:
    log_report += (
        "Предупреждения раскраски (fallback):\n  - "
        + "\n  - ".join(_fallback_warnings)
        + "\n--------------------------------------------------\n"
    )

print(log_report)
with open(log_file_path, "a", encoding="utf-8") as f:
    f.write(log_report)


# =====================================================================
# ЦЕПОЧКА РАСЧЕТОВ И ОТРИСОВКА
# =====================================================================
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

center_ring_color = center_colors[0] if center_colors else None
center_color_single = center_colors[1] if len(center_colors) >= 2 else None

if COLOR_ENABLED and center_ring_color:
    fill_ring(0, Config.CIRCLE_RADIUS, center_ring_color)

_t0 = time.perf_counter()
if style_center == 1: center_v1(Config.CIRCLE_RADIUS)
elif style_center == 2: center_v2(Config.CIRCLE_RADIUS, center_color_single)
elif style_center == 3: center_v3(Config.CIRCLE_RADIUS)
elif style_center == 4: center_v4(Config.CIRCLE_RADIUS)
elif style_center == 5: center_v5(Config.CIRCLE_RADIUS)
elif style_center == 6: center_v6(Config.CIRCLE_RADIUS, center_color_single)
elif style_center == 7: center_v7(Config.CIRCLE_RADIUS)
elif style_center == 8: center_v8(Config.CIRCLE_RADIUS)
elif style_center == 9: center_v9(Config.CIRCLE_RADIUS, center_color_single)
elif style_center == 10: center_v10(Config.CIRCLE_RADIUS)
elif style_center == 11: center_v11(Config.CIRCLE_RADIUS)
_tmark(f"center_v{style_center}", _t0)

_t0 = time.perf_counter(); band1_run(r_band1_start, Config.BAND1_WIDTH, colors_band1); _tmark("band1_run", _t0)
_t0 = time.perf_counter(); layer1_run(r_layer1_start, ring_color_layer1, colors_layer1); _tmark("layer1_run", _t0)
_t0 = time.perf_counter(); band2_run(r_band2_start, Config.BAND2_WIDTH, colors_band2); _tmark("band2_run", _t0)
_t0 = time.perf_counter(); layer2_run(r_layer2_start, ring_color_layer2, colors_layer2); _tmark("layer2_run", _t0)
_t0 = time.perf_counter(); band3_run(r_band3_start, Config.BAND3_WIDTH, colors_band3); _tmark("band3_run", _t0)
_t0 = time.perf_counter(); layer3_run(r_layer3_start, ring_color_layer3, colors_layer3); _tmark("layer3_run", _t0)
_t0 = time.perf_counter(); band4_run(r_band4_start, Config.BAND4_WIDTH, colors_band4); _tmark("band4_run", _t0)
_t0 = time.perf_counter(); layer4_run(r_layer4_start, ring_color_layer4, colors_layer4); _tmark("layer4_run", _t0)
_t0 = time.perf_counter(); band5_run(r_band5_start, Config.BAND5_WIDTH, colors_band5); _tmark("band5_run", _t0)
_t0 = time.perf_counter(); layer5_run(r_layer5_start, ring_color_layer5, colors_layer5); _tmark("layer5_run", _t0)

try:
    screen.update()
except Exception:
    pass

t.hideturtle()


# =====================================================================
# СОХРАНЕНИЕ
# =====================================================================
img_dir = "img"
if not os.path.exists(img_dir):
    os.makedirs(img_dir)
eps_base_path = os.path.join(img_dir, mandala_name)
eps_path = eps_base_path + ".eps"

screen.update()
canvas = screen.getcanvas()
_t0 = time.perf_counter()
canvas.postscript(file=eps_path, colormode='color')
_tmark("eps_write", _t0)

_t0 = time.perf_counter()
try:
    with open(eps_path, "r", encoding="latin-1") as f:
        eps_text = f.read()
    bbox_line_old = None
    for line in eps_text.split("\n"):
        if line.startswith("%%BoundingBox:"):
            bbox_line_old = line.strip()
            break
    if bbox_line_old:
        parts = bbox_line_old.replace("%%BoundingBox:", "").split()
        x1, y1, x2, y2 = map(float, parts)
        pad = Config.BBOX_PADDING
        bbox_new_str = f"%%BoundingBox: {int(x1 - pad)} {int(y1 - pad)} {int(x2 + pad)} {int(y2 + pad)}"
        eps_text = eps_text.replace(bbox_line_old, bbox_new_str)
        eps_text = re.sub(r"%%HiResBoundingBox:.*", "", eps_text)
        with open(eps_path, "w", encoding="latin-1") as f:
            f.write(eps_text)
except Exception as e:
    print(f"Предупреждение: не удалось расширить bbox EPS ({e})")
_tmark("eps_bbox_fix", _t0)

end_time_str = datetime.datetime.now().strftime("%H:%M:%S")
ext = Config.SAVE_FORMAT.lower().strip(".")
jpg_filename = datetime.datetime.now().strftime("%Y-%m-%d-mandala-%H%M%S") + "." + ext
out_path = os.path.join(img_dir, jpg_filename)

_t0 = time.perf_counter()
try:
    if ext == "jpg":
        img = Image.open(eps_path)
        img.convert("RGB").save(out_path, "JPEG", quality=95)
        os.remove(eps_path)
    elif ext == "pdf":
        gs_bin = None
        for candidate in ("gswin64c", "gswin32c", "gs"):
            try:
                subprocess.run([candidate, "--version"], capture_output=True, check=True)
                gs_bin = candidate
                break
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        if gs_bin is None:
            raise RuntimeError("Ghostscript не найден")
        subprocess.run([
            gs_bin, "-q",
            "-dNOPAUSE", "-dBATCH", "-dSAFER",
            "-dEPSCrop",
            "-sDEVICE=pdfwrite",
            "-dPDFSETTINGS=/prepress",
            f"-sOutputFile={out_path}",
            eps_path
        ], check=True)
        os.remove(eps_path)
    else:
        raise ValueError(f"Неизвестный формат: {Config.SAVE_FORMAT}")

    success_msg = f" Статус: Успешно сохранено -> {out_path}\n Время окончания: {end_time_str} #\n==================================================\n\n"
except Exception as e:
    success_msg = f" Статус: Ошибка сохранения ({e})\n Время окончания: {end_time_str}\n==================================================\n\n"

_tmark(f"{ext}_convert", _t0)

timing_msg = _timing_report()

print(success_msg)
print(timing_msg)
with open(log_file_path, "a", encoding="utf-8") as f:
    f.write(success_msg)
    if timing_msg:
        f.write(timing_msg + "\n")

turtle.done()
