# -*- mode: python ; coding: utf-8 -*-
"""Спецификация PyInstaller для Mandala Generator (Windows).

Запуск (из корня проекта):
    pyinstaller windows\\mandala.spec --noconfirm

Результат: dist\\Mandala\\Mandala.exe + каталог _internal.
DLL из windows\\cairo_dlls кладутся в _internal рядом с python312.dll.
"""
import glob
import os

SPEC_DIR = os.path.abspath(SPECPATH)
ROOT = os.path.dirname(SPEC_DIR)

# Необязательный резервный путь: если вдруг понадобится вариант с cairocffi,
# положите DLL в windows\cairo_dlls (скрипт windows\update_cairo_dlls.ps1) —
# они будут включены в сборку рядом с интерпретатором.
cairo_dlls = sorted(glob.glob(os.path.join(SPEC_DIR, "cairo_dlls", "*.dll")))
if cairo_dlls:
    print(f"cairo_dlls: включаю {len(cairo_dlls)} DLL (резервный путь cairocffi).")

binaries = [(path, ".") for path in cairo_dlls]

exe_kwargs = {}
icon_path = os.path.join(SPEC_DIR, "icon.ico")
if os.path.exists(icon_path):
    exe_kwargs["icon"] = icon_path

a = Analysis(
    [os.path.join(ROOT, "mandala_app.py")],
    pathex=[ROOT],
    binaries=binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Mandala",
    debug=False,
    strip=False,
    upx=False,
    console=False,   # окно без консоли; логи пишутся в файлы
    **exe_kwargs,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Mandala",
)
