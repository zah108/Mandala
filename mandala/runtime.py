"""Рисование на Cairo: векторное окно и векторный PDF.

Модуль повторяет API turtle (goto / penup / pendown / begin_fill /
fill_color / circle ...), поэтому модули стилей работают без изменений.
Сцена хранит векторные операции: она же рисуется в окне (через Cairo,
со сглаживанием) и она же пишется в PDF — без Ghostscript.
"""
import math
import time

from .cairo_backend import cairo   # noqa: E402  (cairocffi или pycairo)
from PIL import Image, ImageColor, ImageTk   # noqa: E402
import tkinter as tk               # noqa: E402

from .config import Config         # noqa: E402
from ._window_master import WINDOW_MASTER  # noqa: E402
from .traj import Line, Arc, Bezier, FillElement, StrokeElement, TrajectoryElement  # noqa: E402


W = Config.WINDOW_SIZE


def _rgb(color):
    """Цвет turtle -> (r, g, b) в долях единицы."""
    if color is None:
        return (0.0, 0.0, 0.0)
    if isinstance(color, (tuple, list)):
        try:
            return tuple(float(c) / 255.0 for c in list(color)[:3])
        except (TypeError, ValueError):
            # Если в списке оказались строки, пытаемся обработать через ImageColor
            try:
                r, g, b = ImageColor.getrgb(str(color))[:3]
                return r / 255.0, g / 255.0, b / 255.0
            except Exception:
                return (0.0, 0.0, 0.0)
    try:
        r, g, b = ImageColor.getrgb(str(color))[:3]
    except Exception:
        r, g, b = 0, 0, 0
    return r / 255.0, g / 255.0, b / 255.0


class AnimationManager:
    """Управляет прогрессом рисования всей траектории с постоянной скоростью."""
    def __init__(self, speed_px_s):
        self.speed_px_s = speed_px_s
        self.trajectory = []
        self.total_length = 0.0
        self.start_time = None
        self.draw_duration_s = None

    def add_element(self, element):
        self.trajectory.append(element)
        self.total_length += element.length

    def reset(self):
        self.start_time = None

    def get_current_state(self):
        """Возвращает список (элемент, прогресс), который нужно отрисовать.

        Прогресс вычисляется от общего пройденного пути (elapsed * speed),
        поэтому скорость пера одинакова для любых элементов. Заливки имеют
        нулевую длину и появляются мгновенно, когда перо доходит до их точки.
        """
        if not self.trajectory:
            return []

        if self.start_time is None:
            self.start_time = time.perf_counter()

        elapsed = time.perf_counter() - self.start_time
        dist_covered = elapsed * self.speed_px_s

        state = []
        running_len = 0.0
        for elem in self.trajectory:
            end_len = running_len + elem.length
            if elem.length <= 0.0:
                if running_len <= dist_covered:
                    state.append((elem, 1.0))
                else:
                    break
            elif end_len <= dist_covered:
                state.append((elem, 1.0))
            elif running_len < dist_covered:
                state.append((elem, min(1.0, (dist_covered - running_len) / elem.length)))
                break
            else:
                break
            running_len = end_len
        return state

class Scene:
    """Векторные операции рисунка: штрихи и заливки."""

    def __init__(self):
        self.ops = []

    def add_stroke(self, paths, color, width):
        if paths:
            self.ops.append(('stroke', paths, _rgb(color), float(width)))

    def add_fill(self, paths, color):
        if paths:
            self.ops.append(('fill', paths, _rgb(color)))

    @staticmethod
    def _build_path(cr, paths):
        for path in paths:
            if isinstance(path, tuple) and path and path[0] == 'arc':
                if len(path) == 6:
                    _, cx, cy, r, a0, a1 = path
                    cr.new_sub_path()
                    cr.arc(cx, cy, r, a0, a1)
                    continue
                _, cx, cy, r = path
                cr.new_sub_path()
                cr.arc(cx, cy, r, 0.0, 2.0 * math.pi)
                cr.close_path()
                continue
            pts = path
            if len(pts) < 2:
                continue
            cr.move_to(pts[0][0], pts[0][1])
            for x, y in pts[1:]:
                cr.line_to(x, y)

    @classmethod
    def render_ops(cls, cr, ops):
        cr.save()
        cr.translate(W / 2.0, W / 2.0)
        cr.scale(1.0, -1.0)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        for op in ops:
            if op[0] == 'stroke':
                _, paths, rgb, width = op
                cr.set_source_rgb(*rgb)
                cr.set_line_width(max(width, 0.1))
                cr.new_path()
                cls._build_path(cr, paths)
                cr.stroke()
            else:
                _, paths, rgb = op
                cr.set_source_rgb(*rgb)
                cr.new_path()
                cls._build_path(cr, paths)
                cr.fill()
        cr.restore()

    def render(self, cr):
        self.render_ops(cr, self.ops)


class CairoTurtle:
    """Черепаха, записывающая траекторию в AnimationManager и Scene."""

    def __init__(self, scene, anim_manager):
        self.scene = scene
        self.anim_manager = anim_manager
        self._x = 0.0
        self._y = 0.0
        self._heading = 0.0
        self._down = True
        self._color = "black"
        self._fillcolor = "black"
        self._width = Config.LINE_WIDTH
        self._filling = False
        self._fill_paths = []
        self._fill_cur = None
        self._fill_arc = None

    def reset_state(self):
        """Возвращает перо в исходное состояние (перед новым рисованием)."""
        self._x = 0.0
        self._y = 0.0
        self._heading = 0.0
        self._down = True
        self._color = "black"
        self._fillcolor = "black"
        self._width = Config.LINE_WIDTH
        self._filling = False
        self._fill_paths = []
        self._fill_cur = None
        self._fill_arc = None

    def pos(self):
        return (self._x, self._y)

    def isdown(self):
        return self._down

    def filling(self):
        return self._filling

    def pencolor(self, color=None):
        if color is not None:
            self._color = color
        return self._color

    def fillcolor(self, color=None):
        if color is not None:
            self._fillcolor = color
        return self._fillcolor

    def width(self, w=None):
        if w is not None:
            self._width = w
        return self._width

    def setheading(self, angle):
        self._heading = math.radians(angle)

    def speed(self, *args):
        return None

    def hideturtle(self):
        return None

    def showturtle(self):
        return None

    def penup(self):
        self._down = False

    def pendown(self):
        self._down = True

    def flush(self):
        pass

    def goto(self, x, y=None):
        if y is None:
            x, y = x[0], x[1]
        x = float(x)
        y = float(y)

        if self._down:
            # Запас: если черепахе не задали ширину, берём из Config
            current_w = self._width if self._width >= 0.5 else Config.LINE_WIDTH
            self.anim_manager.add_element(Line(
                (self._x, self._y), (x, y),
                color=self._color, width=current_w
            ))
            self.scene.add_stroke([[(self._x, self._y), (x, y)]], self._color, current_w)

        self._x, self._y = x, y

        if self._filling:
            if self._fill_cur is None:
                self._flush_fill_arc()
                self._fill_cur = [(x, y)]
            else:
                self._fill_cur.append((x, y))

    def circle(self, radius, extent=None, steps=None):
        r = abs(float(radius))
        if r <= 0:
            return

        cx = self._x - r * math.sin(self._heading)
        cy = self._y + r * math.cos(self._heading)

        a0 = self._heading - math.pi / 2.0

        if extent is None:
            extent_rad = 2.0 * math.pi
        else:
            extent_rad = math.radians(extent)

        if radius < 0:
            extent_rad = -extent_rad

        a1 = a0 + extent_rad

        if self._down:
            current_w = self._width if self._width >= 0.5 else Config.LINE_WIDTH

            self.anim_manager.add_element(Arc(
                cx, cy, r, a0, a1,
                color=self._color, width=current_w
            ))
            self.scene.add_stroke([('arc', cx, cy, r, a0, a1)], self._color, current_w)

        # Черепаха перемещается всегда, рисует лишь при опущенном пере.
        self._x = cx + r * math.cos(a1)
        self._y = cy + r * math.sin(a1)
        self._heading += extent_rad

        if self._filling:
            if self._fill_cur and len(self._fill_cur) > 2:
                self._fill_paths.append(self._fill_cur)
            self._fill_cur = None
            self._merge_fill_arc(cx, cy, r, a0, a1)

    def _flush_fill_arc(self):
        """Добавляет накопленную дугу в путь заливки.

        Частичная дуга замыкается хордой (регион между хордой и дугой);
        полного оборота добавляет в путь одну окружность.
        """
        fa = getattr(self, "_fill_arc", None)
        if fa is None:
            return
        self._fill_arc = None
        cx, cy, r, a0, span = fa
        if abs(abs(span) - 2.0 * math.pi) < 1e-6:
            self._fill_paths.append(('arc', cx, cy, r))
        else:
            self._fill_paths.append(('arc', cx, cy, r, a0, a0 + span))

    def _merge_fill_arc(self, cx, cy, r, a0, a1):
        """Сливает подряд идущие дуги одной окружности в один контур.

        Полный оборот становится ОДНОЙ окружностью в пути заливки;
        иначе дубликаты полных окружностей при чётном их числе
        отключали заливку even-odd.
        """
        fa = getattr(self, "_fill_arc", None)
        if fa is None:
            self._fill_arc = [cx, cy, r, a0, a1 - a0]
        elif (abs(fa[0] - cx) < 1e-9 and abs(fa[1] - cy) < 1e-9
                and abs(fa[2] - r) < 1e-9 and abs(fa[3] + fa[4] - a0) < 1e-6):
            fa[4] += (a1 - a0)
        else:
            self._flush_fill_arc()
            self._fill_arc = [cx, cy, r, a0, a1 - a0]

        fa = self._fill_arc
        if abs(abs(fa[4]) - 2.0 * math.pi) < 1e-6:
            self._fill_paths.append(('arc', cx, cy, r))
            self._fill_arc = None

    def begin_fill(self):
        self._filling = True
        self._fill_paths = []
        self._fill_cur = []
        self._fill_arc = None

    def end_fill(self):
        if self._filling:
            self._flush_fill_arc()
            if self._fill_cur and len(self._fill_cur) > 2:
                paths = self._fill_paths + [self._fill_cur]
            else:
                paths = self._fill_paths

            self.anim_manager.add_element(FillElement(
                paths, self._fillcolor
            ))
            self.scene.add_fill(paths, self._fillcolor)

            # Заливка съедает половину толщины границы — обводим контур
            # заново полной толщиной поверх заливки (и в окне, и в PDF).
            outline_w = self._width if self._width >= 0.5 else Config.LINE_WIDTH
            self.anim_manager.add_element(StrokeElement(
                paths, color=self._color, width=outline_w
            ))
            self.scene.add_stroke(paths, self._color, outline_w)

        self._filling = False
        self._fill_paths = []
        self._fill_cur = None

class Screen:
    """Окно с векторной сценой (Cairo рисует со сглаживанием).

    Окно — Toplevel скрытого корня сеанса (если master задан) или
    самостоятельный tk.Tk (автономный запуск python -m mandala).
    Закрытие окна крестиком уничтожает только его окно; при следующем
    «Рисовать» оно создаётся заново (_build_window), а сцена/перо живут
    в объекте Screen и переживают пересоздание окна.
    """

    def __init__(self, master=None):
        self.master = master
        self._window_alive = False
        self._on_window_closed = None  # callback сеанса (draw_session)
        self._anim_job = None

        self.anim_manager = AnimationManager(Config._speed_px_s if hasattr(Config, '_speed_px_s') else 500.0)
        self.scene = Scene()
        self.turtle = CairoTurtle(self.scene, self.anim_manager)

        # Векторные слои не зависят от виджетов — живут весь сеанс.
        self._base = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, W)
        self._paint_base()
        self._done = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, W)
        self._cr_done = cairo.Context(self._done)
        self._repaint_done()
        self._baked = 0
        self._anim_finished = False
        self._photo = None
        self._item = None
        self._frame = None
        self._last_upload = 0.0

        self._build_window()

    def _build_window(self):
        """Создаёт (или пересоздаёт после закрытия) окно рисования."""
        root = getattr(self, "root", None)
        if root is not None:
            try:
                if root.winfo_exists():
                    root.destroy()
            except Exception:
                pass
        if self.master is not None:
            self.root = tk.Toplevel(self.master)
        else:
            self.root = tk.Tk()
        self.root.title("Mandala Generator")
        self.canvas = tk.Canvas(self.root, width=W, height=W,
                                bg=Config.BG_COLOR, highlightthickness=0)
        self.canvas.pack()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_window)
        self._photo = None
        self._item = None
        self._window_alive = True

    @staticmethod
    def _apply_view(cr):
        """Единая система координат: центр окна, ось Y вверх.

        Матрица задаётся абсолютно (set_matrix), поэтому вызов идемпотентен:
        повторное применение (reset_animation) не накапливает сдвиг.
        """
        cr.set_matrix(cairo.Matrix(1.0, 0.0, 0.0, -1.0, W / 2.0, W / 2.0))
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)

    def _repaint_done(self):
        """Очищает накопительный слой фоном и наводит систему координат."""
        cr = self._cr_done
        cr.save()
        cr.identity_matrix()
        r, g, b = _rgb(Config.BG_COLOR)
        cr.set_source_rgb(r, g, b)
        cr.paint()
        cr.restore()
        self._apply_view(cr)

    def reset_animation(self):
        """Полный сброс анимации: таймер, кэш и накопительный слой."""
        self.anim_manager.reset()
        self._baked = 0
        self._anim_finished = False
        self._repaint_done()

    def _paint_base(self):
        cr = cairo.Context(self._base)
        r, g, b = _rgb(Config.BG_COLOR)
        cr.set_source_rgb(r, g, b)
        cr.paint()

    def bgcolor(self, *args): return None
    def title(self, *args): return None
    def setup(self, *args, **kwargs): return None
    def delay(self, *args): return None
    def tracer(self, *args): return None

    def _cancel_anim_job(self):
        """Отменяет запланированный кадр анимации (перед сбросом/закрытием)."""
        job = self._anim_job
        if job is not None:
            root = getattr(self, "root", None)
            try:
                if root is not None:
                    root.after_cancel(job)
            except Exception:
                pass
            self._anim_job = None

    def _on_close_window(self):
        """Крестик окна рисования: закрываем только его окно.

        Сцена, траектория и перо остаются в объекте Screen — при следующем
        «Рисовать» окно создаётся заново с тем же содержимым.
        """
        self._cancel_anim_job()
        try:
            self.root.destroy()
        except Exception:
            pass
        self._window_alive = False
        self._photo = None
        self._item = None
        callback = self._on_window_closed
        if callback is not None:
            try:
                callback()
            except Exception:
                pass

    def bye(self):
        self._photo = None
        try:
            self.root.destroy()
        except Exception:
            pass

    def done(self):
        self.update()
        self.root.mainloop()

    def _bake(self, elem):
        """Рисует полностью завершённый элемент на накопительный слой (один раз)."""
        cr = self._cr_done
        if isinstance(elem, FillElement):
            cr.save()
            cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            cr.set_source_rgb(*_rgb(elem.fill_color))
            cr.new_path()
            Scene._build_path(cr, elem.paths)
            cr.fill()
            cr.restore()
            return

        cr.save()
        cr.new_path()
        cr.set_source_rgb(*_rgb(elem.color))
        cr.set_line_width(max(getattr(elem, 'width', Config.LINE_WIDTH), 0.1))
        if isinstance(elem, Line):
            cr.move_to(*elem.p1)
            cr.line_to(*elem.p2)
        elif isinstance(elem, Arc):
            span = elem.a1 - elem.a0
            a_end = elem.a0 + span
            cr.move_to(elem.cx + elem.r * math.cos(elem.a0),
                       elem.cy + elem.r * math.sin(elem.a0))
            if span >= 0:
                cr.arc(elem.cx, elem.cy, elem.r, elem.a0, a_end)
            else:
                cr.arc_negative(elem.cx, elem.cy, elem.r, elem.a0, a_end)
        elif isinstance(elem, StrokeElement):
            Scene._build_path(cr, elem.paths)
        elif isinstance(elem, Bezier):
            pts = [elem.get_point(i / 20.0) for i in range(21)]
            cr.move_to(*pts[0])
            for p in pts[1:]:
                cr.line_to(*p)
        cr.stroke()
        cr.restore()

    def _draw_element_progress(self, cr, elem, prog):
        """Рисует элемент с заданным прогрессом (0..1) — только текущий штрих."""
        prog = max(0.0, min(1.0, prog))
        if isinstance(elem, FillElement):
            return
        cr.new_path()
        cr.set_source_rgb(*_rgb(elem.color))
        cr.set_line_width(max(getattr(elem, 'width', Config.LINE_WIDTH), 0.1))
        if isinstance(elem, Line):
            cr.move_to(*elem.p1)
            p = elem.get_point(prog)
            cr.line_to(p[0], p[1])
        elif isinstance(elem, Arc):
            span = elem.a1 - elem.a0
            a_end = elem.a0 + prog * span
            cr.move_to(elem.cx + elem.r * math.cos(elem.a0),
                       elem.cy + elem.r * math.sin(elem.a0))
            if span >= 0:
                cr.arc(elem.cx, elem.cy, elem.r, elem.a0, a_end)
            else:
                cr.arc_negative(elem.cx, elem.cy, elem.r, elem.a0, a_end)
        elif isinstance(elem, Bezier):
            pts = [elem.get_point((i / 20.0) * prog) for i in range(21)]
            cr.move_to(*pts[0])
            for p in pts[1:]:
                cr.line_to(*p)
        cr.stroke()

    def update(self):
        try:
            if not self._window_alive or self._anim_finished:
                return

            _frame_t0 = time.perf_counter()

            if self._frame is None:
                self._frame = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, W)

            state = self.anim_manager.get_current_state()
            if not state:
                if not self.anim_manager.trajectory:
                    self._anim_finished = True
                return

            # 1) Завершённые элементы выпекаются на накопительный слой
            #    один раз. Каждый кадр дорисовывается только новый «хвост».
            for idx, (elem, t_prog) in enumerate(state):
                if t_prog >= 1.0 and idx >= self._baked:
                    self._bake(elem)
                    self._baked += 1

            # 2) Всё нарисовано — финальный кадр и стоп.
            all_done = (state[-1][1] >= 1.0
                        and self._baked >= len(self.anim_manager.trajectory))
            self._anim_finished = all_done

            # 3) Кадр: накопительный слой + только текущий частичный элемент.
            fc = cairo.Context(self._frame)
            fc.save()
            fc.identity_matrix()
            fc.set_source_surface(self._done, 0, 0)
            fc.paint()
            fc.restore()
            self._apply_view(fc)

            for elem, t_prog in state:
                if t_prog < 1.0:
                    self._draw_element_progress(fc, elem, t_prog)

            # Просадку кадра компенсируем пропуском загрузки в Tk:
            # время-based догонит на следующем кадре (не чаще 1 раза за 100 мс).
            now = time.perf_counter()
            if (not self._anim_finished and now - _frame_t0 > 0.030
                    and now - self._last_upload < 0.100):
                return
            self._last_upload = now

            img = Image.frombytes('RGBA', (W, W), bytes(self._frame.get_data()), 'raw', 'BGRA', self._frame.get_stride())
            self._photo = ImageTk.PhotoImage(img, master=self.root)
            if self._item is None:
                self._item = self.canvas.create_image(0, 0, anchor='nw', image=self._photo)
            else:
                self.canvas.itemconfigure(self._item, image=self._photo)
            self.root.update_idletasks()
        except Exception as exc:
            print(f"Update error: {exc}")



screen = Screen(WINDOW_MASTER["master"])
scene = screen.scene
t = screen.turtle
t.width(Config.LINE_WIDTH)

def _tmark(label, t0):
    if not hasattr(Config, 'TIMING_ENABLED') or not Config.TIMING_ENABLED:
        return
    dt = time.perf_counter() - t0
    if '_timings' not in globals():
        globals()['_timings'] = []
    globals()['_timings'].append((label, dt))

def _timing_report():
    """Генерирует отчет по замеренным фазам рисования."""
    if not hasattr(Config, 'TIMING_ENABLED') or not Config.TIMING_ENABLED:
        return ""
    timings = globals().get('_timings', [])
    if not timings:
        return ""
    lines = ["", "----- Тайминги фаз -----"]
    total = 0.0
    for label, dt in timings:
        lines.append(f"[timing] {label:<24} {dt:6.3f} s")
        total += dt
    lines.append(f"[timing] {'TOTAL (сумма фаз)':<24} {total:6.3f} s")
    lines.append("------------------------")
    return "\n".join(lines) + "\n"

def speed_px_s():
    return screen.anim_manager.speed_px_s

def draw_duration_s(level):
    """Длительность рисования (сек) для уровня 1..20.

    Линейная шкала: постоянный шаг в секундах между уровнями.
    Уровень 1 ≈ SPEED_DURATION_MAX_S, уровень 20 ≈ SPEED_DURATION_MIN_S.
    """
    lvl = max(1, min(20, int(level)))
    span = Config.SPEED_DURATION_MAX_S - Config.SPEED_DURATION_MIN_S
    return Config.SPEED_DURATION_MAX_S - span * (lvl - 1) / 19.0

def apply_draw_speed(level):
    """Запоминает целевую длительность для уровня скорости.

    Скорость (px/с) по этой длительности вычисляется из фактической
    длины траектории: частично уже здесь (если сцена построена — тесты),
    окончательно в runtime.done перед стартом анимации.
    """
    lvl = max(1, min(20, int(level)))
    duration = draw_duration_s(lvl)
    screen.anim_manager.draw_duration_s = duration
    if screen.anim_manager.total_length > 0:
        screen.anim_manager.speed_px_s = (
            screen.anim_manager.total_length / duration)
    Config._speed_level = lvl
    Config._speed_px_s = screen.anim_manager.speed_px_s
    screen.reset_animation()

def move_to(x, y):
    t.goto(x, y)

def clear_scene():
    """Полный сброс перед новым рисованием: сцена, траектория, тайминги, перо."""
    screen._cancel_anim_job()
    screen.scene.ops.clear()
    screen.anim_manager.trajectory.clear()
    screen.anim_manager.reset()
    screen._baked = 0
    screen._anim_finished = False
    if screen._window_alive:
        screen._repaint_done()
    globals()["_timings"] = []
    t.reset_state()


def done(on_finished=None, block=True):
    # Траектория построена — ставим скорость по фактической длине,
    # чтобы реальное время совпало с длительностью уровня.
    duration = screen.anim_manager.draw_duration_s
    if duration and screen.anim_manager.total_length > 0:
        screen.anim_manager.speed_px_s = (
            screen.anim_manager.total_length / duration)
        Config._speed_px_s = screen.anim_manager.speed_px_s

    screen._cancel_anim_job()

    def animate():
        screen.update()
        if screen._anim_finished:
            # Рисование завершено: конечный лог и остановка цикла кадров.
            screen._anim_job = None
            if on_finished is not None:
                on_finished()
            return
        screen._anim_job = screen.root.after(16, animate)
    # Таймер анимации стартует с момента открытия окна,
    # а не с начала построения сцены.
    screen.reset_animation()
    animate()
    if block:
        # Автономный режим (python -m mandala): крутить свой mainloop.
        # В сеансе с окном настроек (block=False) цикл событий обслуживает
        # окно настроек/сеанс — см. draw_session.
        screen.root.mainloop()

def bye():
    screen.bye()
