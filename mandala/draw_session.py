"""Сеанс рисования: окно рисования живёт независимо от окна настроек.

Пока открыто окно настроек (settings_dialog), оно по кнопке «Рисовать»
вызывает launch_or_restart(); тот при первом вызове импортирует
mandala.main (импорт runtime создаёт окно рисования) и запускает новое
рисование, а окно настроек продолжает обслуживать цикл событий окна
рисования через pump(). После закрытия окна настроек run_until_closed()
обслуживает окно рисования до его закрытия — приложение завершается,
когда закрыты оба окна.

Крестик окна рисования не уничтожает окно, а прячет его (см.
runtime.Screen._hide_window), поэтому повторное «Рисовать» просто
показывает окно снова.
"""
import tkinter as tk


def _drawing_root():
    """Корень окна рисования или None (не создано / уничтожено)."""
    import sys
    if "mandala.runtime" not in sys.modules:
        return None  # рисование ещё не запускалось — окно не создаём
    try:
        from . import runtime
    except Exception:
        return None
    root = getattr(getattr(runtime, "screen", None), "root", None)
    if root is None:
        return None
    try:
        root.winfo_exists()
    except tk.TclError:
        return None
    return root


def pump():
    """Один шаг обслуживания окна рисования из чужого цикла событий.

    Безопасно вызывать в любой момент: если окна нет — ничего не делает.
    """
    root = _drawing_root()
    if root is None:
        return
    try:
        root.update()
    except tk.TclError:
        pass


def launch_or_restart():
    """Рисует новую мандалу, показывая/переиспользуя окно рисования."""
    from . import main as mandala_main  # первый импорт создаёт окно рисования

    mandala_main.main(block=False)
    root = _drawing_root()
    if root is not None:
        try:
            root.deiconify()
        except tk.TclError:
            pass


def run_until_closed():
    """Обслуживает окно рисования до его закрытия (после окна настроек)."""
    root = _drawing_root()
    if root is None:
        return
    try:
        if root.state() == "withdrawn":
            root.destroy()
            return
        root.mainloop()
    except tk.TclError:
        pass
    try:
        root.destroy()
    except tk.TclError:
        pass
