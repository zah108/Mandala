"""Все варианты центрального узора + SVG-парсер для Ом."""
import math
import re
import time

from .config import Config
from . import selection
from .runtime import t, _tmark
from .geometry import draw_circle_from_center, draw_small_circle


# =====================================================================
# SVG ОМ — ПАРСЕР (перенесено из svg_om.py)
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


def _parse_svg_path(d):
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
    _OM_SUBPATHS.extend(_parse_svg_path(_d))
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
        t.penup(); t.goto(gx, gy)
        t.pendown()
        for (lx, ly) in sp[1:]:
            gx = center_x + (lx * cos_r - ly * sin_r) * size
            gy = center_y + (lx * sin_r + ly * cos_r) * size
            t.goto(gx, gy)
        t.penup()
    t.width(Config.LINE_WIDTH)


# =====================================================================
# ЦЕНТРЫ — варианты v1..v11
# =====================================================================
def center_v1(r):
    for i in range(12):
        angle = math.radians(i * (360 / 12))
        t.penup(); t.goto(0, 0)
        t.pendown(); t.goto(r * math.cos(angle), r * math.sin(angle))
        t.penup()

def center_v2(r, color=None):
    for curr_r in range(10, int(r) + 1, 10):
        if selection.COLOR_ENABLED and color and curr_r == 10:
            t.fillcolor(color)
            t.begin_fill()
            draw_circle_from_center(curr_r)
            t.end_fill()
        else:
            draw_circle_from_center(curr_r)

def center_v3(r):
    turns = 4
    steps = 200
    
    for i in range(steps + 1):
        tt = i / steps
        rr = r * tt
        a = -2 * math.pi * turns * tt
        x = rr * math.cos(a)
        y = rr * math.sin(a)
        if i == 0:
            t.penup(); t.goto(x, y)
            t.pendown()
        else:
            t.goto(x, y)

def center_v4(r):
    circ_r = r / 2
    for i in range(6):
        a = math.radians(i * 60)
        cx = -circ_r * math.cos(a)
        cy = -circ_r * math.sin(a)
        draw_small_circle(cx, cy, circ_r,
                          fill_color=None,
                          outline_color=Config.LINE_COLOR,
                          min_steps=64)

def center_v5(r):
    t.fillcolor(Config.LINE_COLOR)
    t.begin_fill()
    draw_circle_from_center(5)
    t.end_fill()
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
        t.penup(); t.goto(out[0], out[1])
        t.pendown(); t.goto(in1[0], in1[1])
        t.penup(); t.goto(out[0], out[1])
        t.pendown(); t.goto(in2[0], in2[1])

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
        t.penup(); t.goto(pts[0][0], pts[0][1])
        t.pendown()
        for p in pts[1:]:
            t.goto(p[0], p[1])
        t.penup()
    t.fillcolor(Config.BG_COLOR)
    t.begin_fill()
    draw_circle_from_center(circle_r)
    t.end_fill()
    draw_circle_from_center(circle_r)

def center_v9(r, inner_color=None):
    circle_r = r * 0.35
    if selection.COLOR_ENABLED and inner_color:
        t.fillcolor(inner_color)
        t.begin_fill()
        draw_circle_from_center(circle_r)
        t.end_fill()
    petals = 8
    for i in range(petals):
        a = math.radians(i * 360 / petals)
        half = math.radians(360 / petals / 2)
        steps = 14
        pts = []
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
        t.penup(); t.goto(pts[0][0], pts[0][1])
        t.pendown()
        for p in pts[1:]:
            t.goto(p[0], p[1])
        t.goto(pts[0][0], pts[0][1])
        t.penup()

        t.goto(circle_r * math.cos(a), circle_r * math.sin(a))

        t.penup(); t.goto(r * 0.95 * 0.7 * math.cos(a), r * 0.95 * 0.7 * math.sin(a))

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
        t.penup(); t.goto(base1[0], base1[1])
        t.pendown(); t.goto(tip[0], tip[1])
        t.goto(base2[0], base2[1])
        t.penup()

def center_v11(r):
    def square(side_r, rotation_deg):
        pts = []
        for k in range(4):
            a = math.radians(rotation_deg + k * 90)
            pts.append((side_r * math.cos(a), side_r * math.sin(a)))
        pts.append(pts[0])
        t.penup(); t.goto(pts[0][0], pts[0][1])
        t.pendown()
        for p in pts[1:]:
            t.goto(p[0], p[1])
        t.penup()
    square(r * 0.95, 0)
    square(r * 0.95, 45)
    draw_circle_from_center(r)

# --- Диспетчер ---

def draw(style_idx, r, center_colors):
    ring_color = center_colors[0] if center_colors else None
    single_color = center_colors[1] if len(center_colors) >= 2 else None

    if selection.COLOR_ENABLED and ring_color:
        from .geometry import fill_ring
        fill_ring(0, Config.CIRCLE_RADIUS, ring_color)

    if style_idx == 1: center_v1(r)
    elif style_idx == 2: center_v2(r, single_color)
    elif style_idx == 3: center_v3(r)
    elif style_idx == 4: center_v4(r)
    elif style_idx == 5: center_v5(r)
    elif style_idx == 6: center_v6(r, single_color)
    elif style_idx == 7: center_v7(r)
    elif style_idx == 8: center_v8(r)
    elif style_idx == 9: center_v9(r, single_color)
    elif style_idx == 10: center_v10(r)
    elif style_idx == 11: center_v11(r)

    t.flush()
