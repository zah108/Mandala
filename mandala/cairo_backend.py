"""Выбор бэкенда Cairo.

Запуск из исходников (macOS): cairocffi + libcairo из Homebrew.
Windows-сборка (PyInstaller): pycairo — Cairo статически вшит в
_cairo.pyd внутри pip-колеса, внешние DLL не нужны.

API у cairocffi и pycairo совместим в используемом объёме
(ImageSurface, Context, Matrix, PDFSurface, константы).
"""
import os

# cairocffi ищет libcairo в стандартных путях; на macOS она из Homebrew.
_LIB_DIRS = ("/opt/homebrew/lib", "/usr/local/lib")
_found = [d for d in _LIB_DIRS if os.path.exists(os.path.join(d, "libcairo.2.dylib"))]
if _found:
    _old = os.environ.get("DYLD_LIBRARY_PATH", "")
    if _found[0] not in _old:
        os.environ["DYLD_LIBRARY_PATH"] = os.pathsep.join(_found + ([_old] if _old else []))

try:
    import cairocffi as cairo
except (ImportError, OSError):  # Windows-сборка: pip install pycairo
    import cairo

__all__ = ["cairo"]
