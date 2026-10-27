import math

class TrajectoryElement:
    """Базовый класс для элемента траектории с поддержкой постоянной скорости."""
    def __init__(self, color="black", width=1.5):
        self.color = color
        self.width = width
        self.length = 0.0

    def get_point(self, t):
        """Возвращает точку (x, y) для параметра t от 0 до 1."""
        raise NotImplementedError

class Line(TrajectoryElement):
    def __init__(self, p1, p2, **kwargs):
        super().__init__(**kwargs)
        self.p1 = p1
        self.p2 = p2
        self.length = math.hypot(p2[0] - p1[0], p2[1] - p1[1])

    def get_point(self, t):
        t = max(0.0, min(1.0, t))
        return (
            self.p1[0] + t * (self.p2[0] - self.p1[0]),
            self.p1[1] + t * (self.p2[1] - self.p1[1])
        )

class Arc(TrajectoryElement):
    def __init__(self, cx, cy, r, a0, a1, **kwargs):
        super().__init__(**kwargs)
        self.cx, self.cy, self.r = cx, cy, r
        self.a0, self.a1 = a0, a1
        self.length = abs(r * (a1 - a0))

    def get_point(self, t):
        t = max(0.0, min(1.0, t))
        angle = self.a0 + t * (self.a1 - self.a0)
        return (
            self.cx + self.r * math.cos(angle),
            self.cy + self.r * math.sin(angle)
        )

class Bezier(TrajectoryElement):
    """Кривая Безье с параметризацией по длине дуги (LUT)."""
    def __init__(self, p0, p1, p2, p3, **kwargs):
        super().__init__(**kwargs)
        self.points = [p0, p1, p2, p3]
        self._lut = []
        self._build_lut()

    def _sample_bezier(self, t):
        p0, p1, p2, p3 = self.points
        cx = (1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t**2*p2[0] + t**3*p3[0]
        cy = (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t**2*p2[1] + t**3*p3[1]
        return (cx, cy)

    def _build_lut(self):
        samples = 200
        prev_p = self._sample_bezier(0)
        self._lut = [(0.0, 0.0)]
        total_len = 0.0
        for i in range(1, samples + 1):
            t = i / samples
            curr_p = self._sample_bezier(t)
            total_len += math.hypot(curr_p[0] - prev_p[0], curr_p[1] - prev_p[1])
            self._lut.append((t, total_len))
            prev_p = curr_p
        self.length = total_len

    def get_point(self, t):
        t = max(0.0, min(1.0, t))
        target_len = t * self.length
        low = 0
        high = len(self._lut) - 1
        while low < high - 1:
            mid = (low + high) // 2
            if self._lut[mid][1] < target_len:
                low = mid
            else:
                high = mid
        t0, l0 = self._lut[low]
        t1, l1 = self._lut[high]
        if l1 == l0:
            return self._sample_bezier(t0)
        local_t = (target_len - l0) / (l1 - l0)
        actual_t = t0 + local_t * (t1 - t0)
        return self._sample_bezier(actual_t)

class StrokeElement(TrajectoryElement):
    """Мгновенный обвод готового контура.

    Добавляется в конце заливки: заливка перекрывает половину толщины
    границы, поэтому контур штрихуется заново полной толщиной поверх.
    """
    def __init__(self, paths, color="black", width=1.5):
        super().__init__(color=color, width=width)
        self.paths = paths
        self.length = 0.0

    def get_point(self, t):
        return None

class FillElement(TrajectoryElement):
    """Элемент-заливка. Выполняется мгновенно при достижении данной точки траектории."""
    def __init__(self, paths, color, **kwargs):
        super().__init__(**kwargs)
        self.paths = paths
        self.fill_color = color
        self.length = 0.0 # Заливка мгновенна

    def get_point(self, t):
        return None
