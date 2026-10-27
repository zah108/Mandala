"""Точка входа для сборки PyInstaller: MandalaGenerator.exe

Используется ТОЛЬКО при сборке exe (build_exe.bat -> build_exe.spec).
Обычный запуск из исходников остаётся прежним: python -m mandala
"""
import os
import sys

if getattr(sys, "frozen", False):
    # Рабочая папка = папка exe (туда пишутся img/ и log/)
    os.chdir(os.path.dirname(sys.executable))

    # Папка cairo_dll рядом с exe (если сборщик её положил) —
    # чтобы libcairo-2.dll и её зависимости были найдены до импорта export.py
    dll_dir = os.path.join(os.path.dirname(sys.executable), "cairo_dll")
    if os.path.isdir(dll_dir):
        os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
        try:
            os.add_dll_directory(dll_dir)
        except OSError:
            pass

from mandala.main import main

if __name__ == "__main__":
    main()
