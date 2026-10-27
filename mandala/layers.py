"""Слои лепестков — draw_layer_core + layer1_run..layer5_run."""
import math

from .config import Config
from . import selection
from .runtime import t
from .geometry import (
    fill_ring, draw_polyline, petal_points, shape_leaf,
    draw_oriented_oval, draw_small_circle, _steps_for_circle,
)

# Радиальный отступ базового радиуса листов (полтолщины линии).
_BASE = Config.LINE_WIDTH / 2.0

def _arc_between(r_arc, a_from, a_to, steps_arc=None):
    """Обход дуги радиуса r_arc от a_from к a_to."""
    if r_arc <= 0:
        return
    
    N = _steps_for_circle(r_arc)
    i_from = int(round(-a_from * N / (2 * math.pi)))
    i_to = int(round(-a_to * N / (2 * math.pi)))
    if i_to <= i_from:
        i_to += N
    
    if i_to - i_from > 1:
        for idx in range(i_from + 1, i_to):
            a = -2 * math.pi * (idx % N) / N
            t.pendown(); t.goto(r_arc * math.cos(a), r_arc * math.sin(a))
    t.pendown(); t.goto(r_arc * math.cos(a_to), r_arc * math.sin(a_to))
    

def shape_leaf_base(tt):
    return math.cos(math.pi / 2 * tt)

def _leaf_outline_with_arc_ends(inner_leaf_r, outer_leaf_r, phi,
                                half_span, steps, shape_fn=None):
    if shape_fn is None:
        shape_fn = shape_leaf_base
    steps = min(steps, 8)
    
    pts = []
    for k in range(steps + 1):
        tt = k / steps
        r = inner_leaf_r + (outer_leaf_r - inner_leaf_r) * tt
        off = half_span * shape_fn(tt)
        a = phi - off
        pts.append((r * math.cos(a), r * math.sin(a)))
    for k in range(steps - 1, -1, -1):
        tt = k / steps
        r = inner_leaf_r + (outer_leaf_r - inner_leaf_r) * tt
        off = half_span * shape_fn(tt)
        a = phi + off
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts

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

        col_outer = level_colors[0] if len(level_colors) >= 1 else None
        col_inner = level_colors[1] if len(level_colors) >= 2 else col_outer

        for k in range(n):
            a = 2 * math.pi * k / n
            cxc = mid_r * math.cos(a)
            cyc = mid_r * math.sin(a)
            draw_oriented_oval(cxc, cyc, a, a_axis, b_axis,
                               fill_color=col_outer, outline_color=Config.LINE_COLOR)
            draw_oriented_oval(cxc, cyc, a, a_axis / 1.5, b_axis / 1.5,
                               fill_color=col_inner, outline_color=Config.LINE_COLOR)
        t.width(Config.LINE_WIDTH)
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

            if selection.COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            t.penup(); t.goto(x_b1, y_b1)
            t.pendown()
            t.goto(x_m1, y_m1); t.goto(x_top, y_top); t.goto(x_m2, y_m2); t.goto(x_b2, y_b2)
            _arc_between(inner_r, rad_right, rad_left)
            t.penup()
            if selection.COLOR_ENABLED and level_colors:
                t.end_fill()

            tip_r = (outer_r - inner_r) * 0.05 * 1.3
            step = 2.0 * tip_r
            r_dot_5 = inner_r + tip_r
            r_dot_4 = r_dot_5 + step
            r_dot_3 = r_dot_4 + step
            r_dot_1 = r_dot_3 + step
            r_dot_2 = r_dot_1 + step
            # Рисуем снизу вверх: сначала точка, ближняя к центру мандалы
            for r_dot in (r_dot_5, r_dot_4, r_dot_3, r_dot_1, r_dot_2):
                ccx = r_dot * math.cos(rad)
                ccy = r_dot * math.sin(rad)
                draw_small_circle(ccx, ccy, tip_r,
                                  fill_color=Config.BG_COLOR,
                                  outline_color=Config.LINE_COLOR)

        elif layer_style_idx == 3:
            outer_r2 = inner_r + (outer_r - inner_r) * 0.75
            half2 = half_angle * 0.45
            steps_smooth = 96

            if selection.COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            pts_outer = _leaf_outline_with_arc_ends(inner_r, outer_r, rad,
                                                    half_angle, steps_smooth)
            draw_polyline(pts_outer, close=False)
            _arc_between(inner_r, rad + half_angle, rad - half_angle)
            if selection.COLOR_ENABLED and level_colors:
                t.end_fill()

            if selection.COLOR_ENABLED and len(level_colors) >= 2:
                t.fillcolor(level_colors[1])
                t.begin_fill()
            pts_inner = _leaf_outline_with_arc_ends(inner_r, outer_r2, rad,
                                                    half2, steps_smooth)
            draw_polyline(pts_inner, close=False)
            _arc_between(inner_r, rad + half2, rad - half2)
            if selection.COLOR_ENABLED and len(level_colors) >= 2:
                t.end_fill()

            r_line_end = inner_r + (outer_r2 - inner_r) * 0.7
            t.penup(); t.goto(inner_r * math.cos(rad), inner_r * math.sin(rad))
            t.pendown(); t.goto(r_line_end * math.cos(rad), r_line_end * math.sin(rad))
            t.penup()

        elif layer_style_idx == 4:
            steps_smooth = 96
            if selection.COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            pts = _leaf_outline_with_arc_ends(inner_r, outer_r, rad,
                                              half_angle, steps_smooth)
            draw_polyline(pts, close=False)
            _arc_between(inner_r, rad + half_angle, rad - half_angle)
            if selection.COLOR_ENABLED and level_colors:
                t.end_fill()

            tip_r = (outer_r - inner_r) * 0.05 * 1.3
            r_mid = (inner_r + outer_r) / 2
            ccx = r_mid * math.cos(rad)
            ccy = r_mid * math.sin(rad)
            draw_small_circle(ccx, ccy, tip_r,
                              fill_color=Config.BG_COLOR,
                              outline_color=Config.LINE_COLOR)

            if r_mid > 0:
                ux = ccx / r_mid
                uy = ccy / r_mid
            else:
                ux, uy = 0.0, 0.0
            start_x = ccx - ux * tip_r
            start_y = ccy - uy * tip_r
            target_x = inner_r * math.cos(rad)
            target_y = inner_r * math.sin(rad)
            t.penup(); t.goto(start_x, start_y)
            t.pendown(); t.goto(target_x, target_y)

        elif layer_style_idx == 5:
            steps_smooth = 96
            if selection.COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            pts = _leaf_outline_with_arc_ends(inner_r, outer_r, rad,
                                              half_angle, steps_smooth)
            draw_polyline(pts, close=False)
            _arc_between(inner_r, rad + half_angle, rad - half_angle)
            if selection.COLOR_ENABLED and level_colors:
                t.end_fill()
            h = outer_r - inner_r
            t.penup(); t.goto(inner_r * math.cos(rad), inner_r * math.sin(rad))
            t.pendown(); t.goto((inner_r + h * 0.85) * math.cos(rad),
                    (inner_r + h * 0.85) * math.sin(rad))
            t.penup()
            shift = h * 0.85 * 0.15
            for k in range(1, 4):
                tt = k / 4.5
                r_mid = inner_r + (outer_r - inner_r) * tt - shift
                mx = r_mid * math.cos(rad)
                my = r_mid * math.sin(rad)
                width_at_mid = half_angle * math.cos(math.pi / 2 * tt) * r_mid
                coef = 0.85 if k < 3 else 0.51
                side_len = width_at_mid * coef
                lx = mx + side_len * math.cos(rad - math.pi / 4)
                ly = my + side_len * math.sin(rad - math.pi / 4)
                rx = mx + side_len * math.cos(rad + math.pi / 4)
                ry = my + side_len * math.sin(rad + math.pi / 4)
                t.penup(); t.goto(mx, my); t.pendown(); t.goto(lx, ly); t.penup()
                t.penup(); t.goto(mx, my); t.pendown(); t.goto(rx, ry); t.penup()

        elif layer_style_idx == 6:
            steps = 48
            if i % 2 == 1:
                outer_r_eff = inner_r + (outer_r - inner_r) * 0.7 * 0.85
                half_sub = half_angle / 2
                for sub_sign in (-1, +1):
                    rad_sub = rad + sub_sign * half_sub
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
                    if selection.COLOR_ENABLED and level_colors:
                        t.fillcolor(level_colors[0])
                        t.begin_fill()
                    draw_polyline(pts, close=False)
                    _arc_between(inner_r, rad_sub + half_sub, rad_sub - half_sub)
                    if selection.COLOR_ENABLED and level_colors:
                        t.end_fill()
            else:
                outer_r_eff = outer_r
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
                if selection.COLOR_ENABLED and level_colors:
                    t.fillcolor(level_colors[0])
                    t.begin_fill()
                draw_polyline(pts, close=False)
                _arc_between(inner_r, rad + half_angle, rad - half_angle)
                if selection.COLOR_ENABLED and level_colors:
                    t.end_fill()

        elif layer_style_idx == 7:
            outer_r2 = inner_r + (outer_r - inner_r) * 0.85
            half2 = half_angle * 0.35
            steps_smooth = 96
            if selection.COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r, rad, half_angle,
                                       shape_leaf, steps=steps_smooth))
            if selection.COLOR_ENABLED and level_colors:
                t.end_fill()
            if selection.COLOR_ENABLED and len(level_colors) >= 2:
                t.fillcolor(level_colors[1])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r2, rad, half2,
                                       shape_leaf, steps=steps_smooth))
            if selection.COLOR_ENABLED and len(level_colors) >= 2:
                t.end_fill()

        elif layer_style_idx == 8:
            def shape_8(tt):
                s = math.sin(math.pi * tt)
                return s * (1 - 0.15 * s)
            steps_smooth = 96
            if selection.COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r, rad, half_angle,
                                       shape_leaf, steps=steps_smooth))
            if selection.COLOR_ENABLED and level_colors:
                t.end_fill()
            tip_r = (outer_r - inner_r) * 0.05 * 1.3
            r_mid = (inner_r + outer_r) / 2
            r_circle_2 = r_mid - (outer_r - inner_r) * 0.2 + (outer_r - inner_r) * 0.22
            r_circle_1 = r_circle_2 - 2 * tip_r
            r_circle_3 = r_circle_2 + 2 * tip_r
            for r_circle in (r_circle_1, r_circle_2, r_circle_3):
                ccx = r_circle * math.cos(rad)
                ccy = r_circle * math.sin(rad)
                draw_small_circle(ccx, ccy, tip_r,
                                  fill_color=Config.BG_COLOR,
                                  outline_color=Config.LINE_COLOR)
            t.fillcolor(Config.LINE_COLOR)

            r_edge = r_circle_1 - tip_r
            edge_x = r_edge * math.cos(rad)
            edge_y = r_edge * math.sin(rad)
            base_x = inner_r * math.cos(rad)
            base_y = inner_r * math.sin(rad)
            t.penup(); t.goto(edge_x, edge_y)
            t.pendown(); t.goto(base_x, base_y)
            t.penup()

        elif layer_style_idx == 9:
            outer_r2 = inner_r + (outer_r - inner_r) * 0.85
            half2 = half_angle * 0.55
            outer_r3 = inner_r + (outer_r - inner_r) * 0.62
            half3 = half_angle * 0.30
            steps_smooth = 96

            # Внешний лепесток
            if selection.COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            pts1 = _leaf_outline_with_arc_ends(inner_r, outer_r, rad,
                                               half_angle, steps_smooth)
            draw_polyline(pts1, close=False)
            _arc_between(inner_r, rad + half_angle, rad - half_angle)
            if selection.COLOR_ENABLED and level_colors:
                t.end_fill()

            # Средний лепесток
            if selection.COLOR_ENABLED and len(level_colors) >= 2:
                t.fillcolor(level_colors[1])
                t.begin_fill()
            pts2 = _leaf_outline_with_arc_ends(inner_r, outer_r2, rad,
                                               half2, steps_smooth)
            draw_polyline(pts2, close=False)
            _arc_between(inner_r, rad + half2, rad - half2)
            if selection.COLOR_ENABLED and len(level_colors) >= 2:
                t.end_fill()

            # Внутренний лепесток
            if selection.COLOR_ENABLED and len(level_colors) >= 3:
                t.fillcolor(level_colors[2])
                t.begin_fill()
            pts3 = _leaf_outline_with_arc_ends(inner_r, outer_r3, rad,
                                               half3, steps_smooth)
            draw_polyline(pts3, close=False)
            _arc_between(inner_r, rad + half3, rad - half3)
            if selection.COLOR_ENABLED and len(level_colors) >= 3:
                t.end_fill()

        elif layer_style_idx == 10:
            steps = 96
            pts = []
            for s in range(steps + 1):
                tt_norm = s / steps
                tt_leaf = 0.5 + tt_norm * 0.5
                r = inner_r + (outer_r - inner_r - Config.LINE_WIDTH / 2.0) * tt_norm
                off = half_angle * (math.sin(math.pi * tt_leaf) ** 0.6)
                a = rad - off
                pts.append((r * math.cos(a), r * math.sin(a)))
            for s in range(steps, -1, -1):
                tt_norm = s / steps
                tt_leaf = 0.5 + tt_norm * 0.5
                r = inner_r + (outer_r - inner_r - Config.LINE_WIDTH / 2.0) * tt_norm
                off = half_angle * (math.sin(math.pi * tt_leaf) ** 0.6)
                a = rad + off
                pts.append((r * math.cos(a), r * math.sin(a)))
            if selection.COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(pts, close=False)
            _arc_between(inner_r, rad + half_angle, rad - half_angle)
            if selection.COLOR_ENABLED and level_colors:
                t.end_fill()

            shorten = 0.80
            dot_r = (outer_r - inner_r) * 0.10 * 0.75
            if dot_r < 0.5:
                dot_r = 0.5

            base_x = inner_r * math.cos(rad)
            base_y = inner_r * math.sin(rad)

            r_line_full = inner_r + (outer_r - inner_r) * 0.8
            r_line_end = inner_r + (r_line_full - inner_r) * shorten
            
            t.penup(); t.goto(base_x, base_y)
            t.pendown()
            end_c_x = r_line_end * math.cos(rad)
            end_c_y = r_line_end * math.sin(rad)
            t.goto(end_c_x, end_c_y)
            t.penup()
            dot_cx = end_c_x + dot_r * math.cos(rad)
            dot_cy = end_c_y + dot_r * math.sin(rad)
            draw_small_circle(dot_cx, dot_cy, dot_r,
                              fill_color=Config.BG_COLOR,
                              outline_color=Config.LINE_COLOR)

            line_len_full = (outer_r - inner_r) * 0.4
            line_len = line_len_full * shorten
            for d_ang in (math.radians(20), math.radians(-20)):
                a_new = rad + d_ang
                ex = base_x + line_len * math.cos(a_new)
                ey = base_y + line_len * math.sin(a_new)
                t.penup(); t.goto(base_x, base_y)
                t.pendown(); t.goto(ex, ey)
                t.penup()
                dot_bx = ex + dot_r * math.cos(a_new)
                dot_by = ey + dot_r * math.sin(a_new)
                draw_small_circle(dot_bx, dot_by, dot_r,
                                  fill_color=Config.BG_COLOR,
                                  outline_color=Config.LINE_COLOR)

        elif layer_style_idx == 11:
            steps = 96
            for idx_s, scale in enumerate((1.0, 0.7)):
                orr = inner_r + (outer_r - inner_r) * scale
                half_scale = half_angle * scale
                pts = []
                for s in range(steps + 1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr - inner_r - _BASE) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad - off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                for s in range(steps, -1, -1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr - inner_r - _BASE) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad + off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                if selection.COLOR_ENABLED and level_colors and idx_s < len(level_colors):
                    t.fillcolor(level_colors[idx_s])
                    t.begin_fill()
                draw_polyline(pts, close=False)
                _arc_between(inner_r, rad + half_scale, rad - half_scale)
                if selection.COLOR_ENABLED and level_colors and idx_s < len(level_colors):
                    t.end_fill()

        elif layer_style_idx == 12:
            def drop_halfwidth(tt):
                return 2.0 * math.sqrt(tt * (1.0 - tt))

            steps = 96
            pts_left = []
            pts_right = []
            for s in range(steps + 1):
                tt = s / steps
                rr = inner_r + _BASE + (outer_r - inner_r - _BASE) * tt
                off = half_angle * drop_halfwidth(tt)
                if off > half_angle:
                    off = half_angle
                a_l = rad - off
                a_r = rad + off
                pts_left.append((rr * math.cos(a_l), rr * math.sin(a_l)))
                pts_right.append((rr * math.cos(a_r), rr * math.sin(a_r)))
            pts = pts_left + pts_right[::-1]

            if selection.COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(pts)
            if selection.COLOR_ENABLED and level_colors:
                t.end_fill()

            t.pencolor(Config.LINE_COLOR)
            r_tip = inner_r + (outer_r - inner_r) * 0.78
            
            t.penup(); t.goto(inner_r * math.cos(rad), inner_r * math.sin(rad))
            t.pendown(); t.goto(r_tip * math.cos(rad), r_tip * math.sin(rad))
            t.penup()

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
                t.penup(); t.goto(mx, my); t.pendown(); t.goto(lx, ly); t.penup()
                t.penup(); t.goto(mx, my); t.pendown(); t.goto(rx, ry); t.penup()
            t.width(Config.LINE_WIDTH)

        elif layer_style_idx == 13:
            rad_left = rad - half_angle
            rad_right = rad + half_angle
            x_b1 = inner_r * math.cos(rad_left); y_b1 = inner_r * math.sin(rad_left)
            x_b2 = inner_r * math.cos(rad_right); y_b2 = inner_r * math.sin(rad_right)
            for idx_s, scale in enumerate((1.0, 0.5)):
                c_out = inner_r + (outer_r - inner_r) * scale
                col = None
                if level_colors:
                    col = level_colors[idx_s] if idx_s < len(level_colors) else level_colors[-1]
                if selection.COLOR_ENABLED and col:
                    t.fillcolor(col)
                    t.begin_fill()
                t.penup(); t.goto(x_b1, y_b1)
                t.pendown()
                t.goto(c_out * math.cos(rad), c_out * math.sin(rad))
                t.goto(x_b2, y_b2)
                _arc_between(inner_r, rad_right, rad_left)
                if selection.COLOR_ENABLED and col:
                    t.end_fill()

            dot_r = (outer_r - inner_r) * 0.10 * 0.75
            if dot_r < 0.5:
                dot_r = 0.5
            r_small_centroid = inner_r + (outer_r - inner_r) * 0.5 * (2.0 / 3.0)
            r_small_centroid -= 3.0 * dot_r
            ccx = r_small_centroid * math.cos(rad)
            ccy = r_small_centroid * math.sin(rad)
            draw_small_circle(ccx, ccy, dot_r,
                              fill_color=Config.BG_COLOR,
                              outline_color=Config.LINE_COLOR)
            t.width(Config.LINE_WIDTH)

        elif layer_style_idx == 14:
            steps = 96
            for idx_s, scale in enumerate((1.0, 0.65)):
                orr = inner_r + (outer_r - inner_r) * scale
                half_scale = half_angle * scale
                pts = []
                for s in range(steps + 1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr - inner_r - _BASE) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad - off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                for s in range(steps, -1, -1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr - inner_r - _BASE) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad + off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                col = None
                if level_colors:
                    col = level_colors[idx_s] if idx_s < len(level_colors) else level_colors[-1]
                if selection.COLOR_ENABLED and col:
                    t.fillcolor(col)
                    t.begin_fill()
                draw_polyline(pts, close=False)
                _arc_between(inner_r, rad + half_scale, rad - half_scale)
                if selection.COLOR_ENABLED and col:
                    t.end_fill()

            inner_scale = 0.65
            ir = inner_r + (outer_r - inner_r) * (1 - inner_scale) / 2
            orr2 = inner_r + (outer_r - inner_r) / 2
            r_mid_inner = (ir + orr2) / 2 - (orr2 - ir) * 0.4
            ccx = r_mid_inner * math.cos(rad)
            ccy = r_mid_inner * math.sin(rad)
            dot_r = (orr2 - ir) * 0.105 * 2
            if dot_r < 0.5:
                dot_r = 0.5
            draw_small_circle(ccx, ccy, dot_r,
                              fill_color=Config.BG_COLOR,
                              outline_color=Config.LINE_COLOR)
            if r_mid_inner > 0:
                ux = ccx / r_mid_inner
                uy = ccy / r_mid_inner
            else:
                ux, uy = 0.0, 0.0
            start_x = ccx - ux * dot_r
            start_y = ccy - uy * dot_r
            target_x = inner_r * math.cos(rad)
            target_y = inner_r * math.sin(rad)
            t.penup(); t.goto(start_x, start_y)
            t.pendown(); t.goto(target_x, target_y)
            t.width(Config.LINE_WIDTH)

        elif layer_style_idx == 15:
            steps = 96
            for idx_s, (scale, half_scale) in enumerate((
                    (1.0, half_angle),
                    (0.65, half_angle * 0.65))):
                orr2 = inner_r + (outer_r - inner_r) * scale
                pts = []
                for s in range(steps + 1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr2 - inner_r - _BASE) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad - off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                for s in range(steps, -1, -1):
                    tt_norm = s / steps
                    tt_leaf = 0.5 + tt_norm * 0.5
                    r = inner_r + (orr2 - inner_r - _BASE) * tt_norm
                    off = half_scale * math.sin(math.pi * tt_leaf)
                    a = rad + off
                    pts.append((r * math.cos(a), r * math.sin(a)))
                col = None
                if level_colors:
                    col = level_colors[idx_s] if idx_s < len(level_colors) else level_colors[-1]
                if selection.COLOR_ENABLED and col:
                    t.fillcolor(col)
                    t.begin_fill()
                draw_polyline(pts, close=False)
                _arc_between(inner_r, rad + half_scale, rad - half_scale)
                if selection.COLOR_ENABLED and col:
                    t.end_fill()
            inner_scale = 0.65
            ir = inner_r + (outer_r - inner_r) * (1 - inner_scale) / 2
            orr2 = inner_r + (outer_r - inner_r) * (1 + inner_scale) / 2
            r_mid_inner = (ir + orr2) / 2 - (orr2 - ir) * 0.40
            ccx = r_mid_inner * math.cos(rad)
            ccy = r_mid_inner * math.sin(rad)
            dot_r = (orr2 - ir) * 0.125
            draw_small_circle(ccx, ccy, dot_r,
                              fill_color=Config.BG_COLOR,
                              outline_color=Config.LINE_COLOR)
            t.width(Config.LINE_WIDTH)

        elif layer_style_idx == 16:
            tip_r = outer_r
            base_r = inner_r + _BASE
            half_r = half_angle * 0.75
            r_mid_rhombus = (inner_r + outer_r) / 2
            dot_r = (outer_r - inner_r) * 0.10 * 0.85 * 0.75
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
                if selection.COLOR_ENABLED and level_colors:
                    t.fillcolor(level_colors[0])
                    t.begin_fill()
                draw_polyline(pts)
                if selection.COLOR_ENABLED and level_colors:
                    t.end_fill()

                ccx = r_mid_rhombus * math.cos(rad_off)
                ccy = r_mid_rhombus * math.sin(rad_off)
                draw_small_circle(ccx, ccy, dot_r,
                                  fill_color=Config.BG_COLOR,
                                  outline_color=Config.LINE_COLOR)
                # Линия к пестику: только до ближнего к центру края точки,
                # с отступом на полтолщины пера, чтобы не перечёркивать её.
                line_end_r = r_mid_rhombus - dot_r - Config.LINE_WIDTH / 2.0
                t.penup(); t.goto(inner_r * math.cos(rad_off), inner_r * math.sin(rad_off))
                t.pendown(); t.goto(line_end_r * math.cos(rad_off), line_end_r * math.sin(rad_off))
                t.penup()
            t.width(Config.LINE_WIDTH)

        elif layer_style_idx == 17:
            steps_smooth = 96
            if selection.COLOR_ENABLED and level_colors:
                t.fillcolor(level_colors[0])
                t.begin_fill()
            draw_polyline(petal_points(inner_r, outer_r, rad, half_angle,
                                       shape_leaf, steps=steps_smooth))
            if selection.COLOR_ENABLED and level_colors:
                t.end_fill()
            inner_scale = 0.65
            ir = inner_r + (outer_r - inner_r) * (1 - inner_scale) / 2
            orr2 = inner_r + (outer_r - inner_r) * (1 + inner_scale) / 2
            inner_col = None
            if level_colors:
                inner_col = level_colors[1] if len(level_colors) >= 2 else level_colors[0]
            if selection.COLOR_ENABLED and inner_col:
                t.fillcolor(inner_col)
                t.begin_fill()
            draw_polyline(petal_points(ir, orr2, rad, half_angle * inner_scale,
                                       shape_leaf, steps=steps_smooth))
            if selection.COLOR_ENABLED and inner_col:
                t.end_fill()

            dot_r = (outer_r - inner_r) * 0.10 * 0.75
            if dot_r < 0.5:
                dot_r = 0.5
            r_inner_center = (ir + orr2) / 2
            ccx = r_inner_center * math.cos(rad)
            ccy = r_inner_center * math.sin(rad)
            draw_small_circle(ccx, ccy, dot_r,
                              fill_color=Config.BG_COLOR,
                              outline_color=Config.LINE_COLOR)
            t.width(Config.LINE_WIDTH)

    t.width(Config.LINE_WIDTH)

def layer1_run(r_in, ring_color, petal_colors):
    r_out = r_in + Config.L1_WIDTH
    if Config.PAINT_LAYER_RINGS and selection.COLOR_ENABLED and ring_color:
        fill_ring(r_in, r_out, ring_color)
    draw_layer_core(r_in, r_out, 16, _style_layer1, petal_colors)

def layer2_run(r_in, ring_color, petal_colors):
    r_out = r_in + Config.L2_WIDTH
    if Config.PAINT_LAYER_RINGS and selection.COLOR_ENABLED and ring_color:
        fill_ring(r_in, r_out, ring_color)
    draw_layer_core(r_in, r_out, 14, _style_layer2, petal_colors)

def layer3_run(r_in, ring_color, petal_colors):
    r_out = r_in + Config.L3_WIDTH
    if Config.PAINT_LAYER_RINGS and selection.COLOR_ENABLED and ring_color:
        fill_ring(r_in, r_out, ring_color)
    draw_layer_core(r_in, r_out, 24, _style_layer3, petal_colors)

def layer4_run(r_in, ring_color, petal_colors):
    r_out = r_in + Config.L4_WIDTH
    if Config.PAINT_LAYER_RINGS and selection.COLOR_ENABLED and ring_color:
        fill_ring(r_in, r_out, ring_color)
    draw_layer_core(r_in, r_out, 32, _style_layer4, petal_colors)

def layer5_run(r_in, ring_color, petal_colors):
    r_out = r_in + Config.L5_WIDTH
    if Config.PAINT_LAYER_RINGS and selection.COLOR_ENABLED and ring_color:
        fill_ring(r_in, r_out, ring_color)
    draw_layer_core(r_in, r_out, 40, _style_layer5, petal_colors)

_style_layer1 = 1
_style_layer2 = 1
_style_layer3 = 1
_style_layer4 = 1
_style_layer5 = 1

def set_styles(styles):
    global _style_layer1, _style_layer2, _style_layer3, _style_layer4, _style_layer5
    _style_layer1, _style_layer2, _style_layer3, _style_layer4, _style_layer5 = styles

def draw_layer(index, r, ring_color, petal_colors):
    if index == 1: layer1_run(r, ring_color, petal_colors)
    elif index == 2: layer2_run(r, ring_color, petal_colors)
    elif index == 3: layer3_run(r, ring_color, petal_colors)
    elif index == 4: layer4_run(r, ring_color, petal_colors)
    elif index == 5: layer5_run(r, ring_color, petal_colors)
    t.flush()
