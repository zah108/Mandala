"""Сохранение мандалы: вектор прямо в PDF (Cairo)."""
import datetime
import os
import time

import cairocffi as cairo
from PIL import Image

from .config import Config
from .runtime import W, _rgb, _tmark


_IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


def save_mandala(scene, mandala_name):
    """Пишет сцену в <проект>/img/…pdf (вектор). Возвращает (путь, ошибка|None)."""
    img_dir = _IMG_DIR
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    ext = Config.SAVE_FORMAT.lower().strip(".")
    filename = (datetime.datetime.now().strftime("%Y-%m-%d-mandala-%H%M%S")
                + "." + ext)
    out_path = os.path.join(img_dir, filename)

    _t0 = time.perf_counter()
    try:
        if ext == "pdf":
            surface = cairo.PDFSurface(out_path, W, W)
            cr = cairo.Context(surface)
            cr.set_source_rgb(*_rgb(Config.BG_COLOR))
            cr.paint()
            scene.render(cr)
            surface.finish()
        elif ext in ("png", "jpg", "jpeg"):
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, W)
            cr = cairo.Context(surface)
            cr.set_source_rgb(*_rgb(Config.BG_COLOR))
            cr.paint()
            scene.render(cr)
            surface.flush()
            img = Image.frombuffer('RGBA', (W, W), surface.get_data(),
                                   'raw', 'BGRA', surface.get_stride())
            if ext == "png":
                img.save(out_path, "PNG")
            else:
                img.convert("RGB").save(out_path, "JPEG", quality=95)
        else:
            raise ValueError(f"Неизвестный формат: {Config.SAVE_FORMAT}")
        error = None
    except Exception as exc:
        error = str(exc)
    _tmark(f"{ext}_save", _t0)

    return out_path, error
