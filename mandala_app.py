"""Точка входа собранного Windows-приложения (PyInstaller).

Здесь выполняется подготовка до импорта пакета mandala:
  1) DPI-awareness — чтобы окно Tk не было размытым на HiDPI-экранах;
  2) предзагрузка Cairo DLL из каталога сборки (cairocffi на Windows
     ищет libcairo-2.dll сама и без подсказки может её не найти);
  3) окно настроек (если включено) до открытия окна рисования.

Запуск из исходников тоже работает:  python mandala_app.py
"""
import os
import sys
import traceback


def _enable_windows_dpi_awareness():
    """Чёткий текст и интерфейс на HiDPI-экранах Windows."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


def _preload_bundled_dlls():
    """Делает Cairo DLL из сборки видимыми для cairocffi.

    В onedir-сборке PyInstaller DLL лежат в каталоге _internal.
    add_dll_directory добавляет его в поиск загрузчика, а явная
    предзагрузка гарантирует, что ffi.dlopen('libcairo-2.dll')
    найдёт уже загруженную библиотеку.
    """
    if not getattr(sys, "frozen", False) or not sys.platform.startswith("win"):
        return
    base = getattr(sys, "_MEIPASS", None)
    if not base or not os.path.isdir(base):
        return
    try:
        os.add_dll_directory(base)
    except (AttributeError, OSError):
        pass
    import ctypes
    for name in sorted(os.listdir(base)):
        if name.lower().endswith(".dll"):
            try:
                ctypes.WinDLL(os.path.join(base, name))
            except OSError:
                pass  # не все DLL обязательны; ошибка cairo покажется позже


def _show_crash(exc):
    """Сообщает об ошибке запуска: файл + окно (если Tk доступен)."""
    detail = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    crash_path = None
    try:
        from mandala import app_paths
        import datetime
        log_dir = app_paths.logs_dir()
        os.makedirs(log_dir, exist_ok=True)
        crash_path = os.path.join(
            log_dir,
            datetime.datetime.now().strftime("crash-%Y%m%d-%H%M%S.txt"),
        )
        with open(crash_path, "w", encoding="utf-8") as f:
            f.write(detail)
    except Exception:
        pass

    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        text = "Программа не смогла запуститься.\n"
        if crash_path:
            text += f"Подробности сохранены в файле:\n{crash_path}"
        else:
            text = "Программа не смогла запуститься.\nПодробности:\n" + detail[-1200:]
        messagebox.showerror("Mandala Generator", text)
        root.destroy()
    except Exception:
        sys.stderr.write(detail)


def main():
    _enable_windows_dpi_awareness()
    _preload_bundled_dlls()

    from mandala import app_paths, settings
    app_paths.ensure_dirs()
    first_run = settings.write_template_if_missing()
    warnings_ = settings.apply_user_settings()

    # При первом запуске окно настроек показываем всегда —
    # пользователь сразу видит, что можно менять.
    if first_run or settings.show_dialog_requested():
        from mandala import settings_dialog
        if not settings_dialog.run(warnings_):
            return

    from mandala.main import main as mandala_main
    mandala_main()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — наружу идёт понятное окно/лог
        _show_crash(exc)
