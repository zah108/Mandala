"""Сеанс рисования: окно рисования живёт независимо от окна настроек.

Оба окна — Toplevel одного скрытого корня (app_root, tk.Tk), поэтому все
события обслуживает ОДИН цикл: отдельная «прокачка» чужого интерпретатора
не нужна. Крестик окна рисования уничтожает только его окно
(runtime.Screen._on_close_window); при следующем «Рисовать» окно создаётся
заново (_build_window). Приложение завершается, когда закрыты оба окна.
"""
import sys
import tkinter as tk

from ._window_master import WINDOW_MASTER

_app_root = None
_dialog_closed = False


def set_app_root(root):
    """Регистрирует скрытый корень сеанса (вызывается из settings_dialog.run)."""
    global _app_root
    _app_root = root
    WINDOW_MASTER["master"] = root


def note_dialog_closed():
    """Диалог настроек закрылся: если окно рисования тоже закрыто — выход."""
    global _dialog_closed
    _dialog_closed = True
    _exit_if_all_closed()


def launch_or_restart():
    """Рисует новую мандалу, создавая/пересоздавая окно рисования."""
    if "mandala.runtime" not in sys.modules:
        # Первый запуск: master уже зарегистрирован, импорт mandala.main
        # (через runtime) создаст окно рисования как Toplevel корня сеанса.
        from . import main as mandala_main  # noqa: F401
    else:
        from . import runtime
        if not runtime.screen._window_alive:
            runtime.screen._build_window()
        from . import main as mandala_main  # noqa: F401

    from . import runtime
    runtime.screen._on_window_closed = _handle_window_closed
    try:
        runtime.screen.root.lift()
    except Exception:
        pass

    mandala_main.main(block=False)


def _handle_window_closed():
    """Окно рисования закрыто своим крестиком (callback из runtime)."""
    _exit_if_all_closed()


def _drawing_open():
    if "mandala.runtime" not in sys.modules:
        return False
    from . import runtime
    return bool(getattr(runtime.screen, "_window_alive", False))


def _exit_if_all_closed():
    if _app_root is None:
        return
    if _dialog_closed and not _drawing_open():
        try:
            _app_root.destroy()
        except tk.TclError:
            pass
