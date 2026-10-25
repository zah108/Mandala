"""Общие геометрические утилиты рисования."""
import math

from .config import Config
from . import selection
from .runtime import t, move_to


def _steps_for_circle(r):
    """Число шагов, при котором хорда окружности радиуса r ≈ 6 px."""
    if r <= 0:
        return 36
    return max(36, int(math.ceil(2 * math.pi * r / 12.0)))


def draw_circle_from_center(r):
    """Окружность радиуса r с центром в (0,0).
    Рисуем сегментами для плавности.
    """
    if r <= 0:
        return
    t.penup()
    t.goto(0, -r)
    t.setheading(0)
    t.pendown()

    circ = 2.0 * math.pi * r
    seg = max(1, int(circ / 20.0))
    for k in range(seg):
        t.circle(r, 360.0 / seg)


def draw_small_circle(cx, cy, r, fill_color=None, outline_color=None,
                      min_steps=24):
    """Маленькая окружность — рисуем сегментами для плавности,
    если радиус достаточно велик.
    """
    if r <= 0:
        return

    if fill_color and selection.COLOR_ENABLED:
        t.fillcolor(fill_color)
        t.begin_fill()
    if outline_color:
        t.pencolor(outline_color)

    t.penup()
    t.goto(cx, cy - r)
    t.setheading(0)
    t.pendown()

    # Малые круги рисуем одним махом — без посегментных вызовов.
    if r < 15.0:
        t.circle(r)
    else:
        circ = 2.0 * math.pi * r
        seg = max(1, int(circ / 20.0))
        for k in range(seg):
            t.circle(r, 360.0 / seg)

    if fill_color and selection.COLOR_ENABLED:
        t.end_fill()
    if outline_color:
        t.pencolor(Config.LINE_COLOR)


def fill_ring(inner_r, outer_r, color):
    """Заливка кольца. Границы рисуем одним махом для стабильности контура."""
    if not selection.COLOR_ENABLED or not color:
        return
    half = max(0.0, Config.LINE_WIDTH / 2.0 - 0.15)
    fi = inner_r + half if inner_r > 0 else 0.0

    t.fillcolor(color)
    t.begin_fill()

    if fi > 0:
        t.penup()
        t.goto(0, -fi)
        t.setheading(0)
        t.circle(fi)

    t.penup()
    t.goto(0, -outer_r)
    t.setheading(0)
    t.pendown()
    t.circle(outer_r)

    t.penup()
    t.end_fill()


def petal_points(inner_r, outer_r, phi, half_angle, shape_fn, steps=8):
    inner_r = inner_r + Config.LINE_WIDTH / 2.0
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

    if fill_color and selection.COLOR_ENABLED:
        t.fillcolor(fill_color)
        t.begin_fill()
    if outline_color:
        t.pencolor(outline_color)
    t.penup(); t.goto(pts[0]); t.pendown()
    for p in pts[1:]:
        move_to(p[0], p[1])
    move_to(pts[0][0], pts[0][1])
    if fill_color and selection.COLOR_ENABLED:
        t.end_fill()
    t.pencolor(Config.LINE_COLOR)
