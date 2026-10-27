"""Разделительные ленты — 12 стилей."""
import math

from .config import Config
from . import selection
from .runtime import t
from .geometry import (
    draw_circle_from_center, fill_ring, draw_small_circle,
)


def generic_band(inner_r, width, style_type, num_elements, band_colors=None):
    outer_r = inner_r + width
    mid_r = (inner_r + outer_r) / 2
    band_w = width

    if band_colors is None:
        band_colors = []

    filled = selection.COLOR_ENABLED and bool(band_colors)
    if filled:
        fill_ring(inner_r, outer_r, band_colors[0])
    else:
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
        
        for i in range(steps + 1):
            tt = i / steps
            a = 2 * math.pi * tt
            rr = mid_r + amplitude * math.sin(waves * a)
            x = rr * math.cos(a)
            y = rr * math.sin(a)
            if i == 0:
                t.penup(); t.goto(x, y)
            else:
                t.pendown(); t.goto(x, y)
        t.width(Config.LINE_WIDTH)
        return

    if style_type == 12:
        steps = 400
        amplitude = band_w * 0.25
        waves = 12
        for phase in (0, math.pi):
            
            for i in range(steps + 1):
                tt = i / steps
                a = 2 * math.pi * tt
                rr = mid_r + amplitude * math.sin(waves * a + phase)
                x = rr * math.cos(a)
                y = rr * math.sin(a)
                if i == 0:
                    t.penup(); t.goto(x, y)
                else:
                    t.pendown(); t.goto(x, y)
        t.width(Config.LINE_WIDTH)
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
            t.penup(); t.goto(x_in, y_in)
            t.pendown(); t.goto(x_out, y_out)
            t.penup()

        elif style_type == 2:
            circ_r = band_w / 4
            cxc = mid_r * math.cos(angle)
            cyc = mid_r * math.sin(angle)
            draw_small_circle(
                cxc, cyc, circ_r,
                fill_color=element_color if (selection.COLOR_ENABLED and element_color) else None,
                outline_color=Config.LINE_COLOR,
            )

        elif style_type == 3:
            x_mid_out = outer_r * math.cos(mid_angle)
            y_mid_out = outer_r * math.sin(mid_angle)
            x_next_in = inner_r * math.cos(next_angle)
            y_next_in = inner_r * math.sin(next_angle)
            t.penup(); t.goto(x_in, y_in)
            t.pendown()
            t.goto(x_mid_out, y_mid_out)
            t.goto(x_next_in, y_next_in)
            t.penup()

        elif style_type == 4:
            outer_circ_r = band_w / 2 - Config.LINE_WIDTH
            inner_circ_r = band_w / 4 - Config.LINE_WIDTH / 2
            cxc = mid_r * math.cos(angle)
            cyc = mid_r * math.sin(angle)
            color_outer = None
            color_inner = None
            if band_colors:
                color_outer = band_colors[1] if len(band_colors) >= 2 else band_colors[0]
                color_inner = band_colors[2] if len(band_colors) >= 3 else color_outer
            draw_small_circle(
                cxc, cyc, outer_circ_r,
                fill_color=color_outer if (selection.COLOR_ENABLED and color_outer) else None,
                outline_color=Config.LINE_COLOR,
            )
            draw_small_circle(
                cxc, cyc, inner_circ_r,
                fill_color=color_inner if (selection.COLOR_ENABLED and color_inner) else None,
                outline_color=Config.LINE_COLOR,
            )

        elif style_type == 5:
            shift = math.radians(angle_step * 0.15)
            for d in (-shift, shift):
                xi = inner_r * math.cos(angle + d)
                yi = inner_r * math.sin(angle + d)
                xo = outer_r * math.cos(angle + d)
                yo = outer_r * math.sin(angle + d)
                t.penup(); t.goto(xi, yi)
                t.pendown(); t.goto(xo, yo)
                t.penup()

        elif style_type == 6:
            circ_r = (band_w / 2) * 0.9 - Config.LINE_WIDTH
            cxc = mid_r * math.cos(angle)
            cyc = mid_r * math.sin(angle)
            draw_small_circle(
                cxc, cyc, circ_r,
                fill_color=element_color if (selection.COLOR_ENABLED and element_color) else None,
                outline_color=Config.LINE_COLOR,
            )

        elif style_type == 7:
            # Прямоугольник с центром ровно в середине ленты:
            # короткая сторона — радиальная (низкая), длинная —
            # тангенциальная (вдоль ленты).
            half_radial = band_w * 0.15
            size_ang = math.radians(angle_step * 0.35)
            cxc = mid_r * math.cos(angle)
            cyc = mid_r * math.sin(angle)
            ux, uy = math.cos(angle), math.sin(angle)      #радиально (наружу)
            tx, ty = -math.sin(angle), math.cos(angle)     #вдоль ленты
            half_tang = mid_r * math.sin(size_ang)
            rx = ux * half_radial
            ry = uy * half_radial
            sx = tx * half_tang
            sy = ty * half_tang
            pts = [
                (cxc - rx - sx, cyc - ry - sy),
                (cxc - rx + sx, cyc - ry + sy),
                (cxc + rx + sx, cyc + ry + sy),
                (cxc + rx - sx, cyc + ry - sy),
            ]
            pts.append(pts[0])
            t.penup(); t.goto(pts[0][0], pts[0][1])
            t.pendown()
            for p in pts[1:]:
                t.goto(p[0], p[1])
            t.penup()

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
            t.penup(); t.goto(pts[0][0], pts[0][1])
            t.pendown()
            for p in pts[1:]:
                t.goto(p[0], p[1])
            t.penup()

        elif style_type == 9:
            circ_r = band_w / 3
            cxc = mid_r * math.cos(angle)
            cyc = mid_r * math.sin(angle)
            draw_small_circle(
                cxc, cyc, circ_r,
                fill_color=element_color if (selection.COLOR_ENABLED and element_color) else None,
                outline_color=Config.LINE_COLOR,
            )

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
            t.penup(); t.goto(pts[0][0], pts[0][1])
            t.pendown()
            for p in pts[1:]:
                t.goto(p[0], p[1])
            t.penup()

    t.width(Config.LINE_WIDTH)

def band1_run(r, w, colors_): generic_band(r, w, _style_band1, 36, colors_)
def band2_run(r, w, colors_): generic_band(r, w, _style_band2, 48, colors_)
def band3_run(r, w, colors_): generic_band(r, w, _style_band3, 64, colors_)
def band4_run(r, w, colors_): generic_band(r, w, _style_band4, 80, colors_)
def band5_run(r, w, colors_): generic_band(r, w, _style_band5, 96, colors_)


_style_band1 = 1
_style_band2 = 1
_style_band3 = 1
_style_band4 = 1
_style_band5 = 1


def set_styles(styles):
    global _style_band1, _style_band2, _style_band3, _style_band4, _style_band5
    _style_band1, _style_band2, _style_band3, _style_band4, _style_band5 = styles


def draw_band(index, r, w, colors_):
    if index == 1: band1_run(r, w, colors_)
    elif index == 2: band2_run(r, w, colors_)
    elif index == 3: band3_run(r, w, colors_)
    elif index == 4: band4_run(r, w, colors_)
    elif index == 5: band5_run(r, w, colors_)
    t.flush()
