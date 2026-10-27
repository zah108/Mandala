# -*- mode: python ; coding: utf-8 -*-
# Спека PyInstaller для MandalaGenerator (Windows, onedir, окно без консоли).
# Сборка: pyinstaller build_exe.spec   (или build_exe.bat)

a = Analysis(
    ["run_mandala.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # Пример переопределения параметров — попадает рядом с exe, пользователь
        # переименует его в mandala_config_override.py и отредактирует
        ("config_override_example.py", "."),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "scipy", "IPython", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MandalaGenerator",
    console=False,          # окно Tkinter, без консоли
    disable_windowed_traceback=False,
    upx=True,
    icon=None,              # можно задать .ico: icon="mandala.ico"
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="MandalaGenerator",
)
