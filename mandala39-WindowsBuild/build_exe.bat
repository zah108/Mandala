@echo off
REM =====================================================================
REM Сборка MandalaGenerator.exe (Windows, PyInstaller, окно без консоли)
REM Использование: 1) установить Python 3.9+  2) дважды щёлкнуть этот файл
REM =====================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo --- [1/4] Python и зависимости ---
python --version
if errorlevel 1 (
    echo ОШИБКА: python не найден. Установите Python 3.9+ с python.org
    echo и при установке отметьте "Add python.exe to PATH".
    pause & exit /b 1
)

echo --- [2/4] Зависимости: pyinstaller, cairocffi, pillow ---
python -m pip install --upgrade -r requirements.txt || goto :err

echo --- [3/4] Поиск libcairo-2.dll (нужна для cairocffi) ---
set "CAIRO_DIR="
for /f "delims=" %%F in ('where libcairo-2.dll 2^>nul') do (
    if not defined CAIRO_DIR set "CAIRO_DIR=%%~dpF"
)
if not defined CAIRO_DIR (
    echo.
    echo ВНИМАНИЕ: libcairo-2.dll не найдена в PATH.
    echo Установите GTK-3 Runtime ^(64-bit^):
    echo   https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
    echo после установки ^- запустите этот файл заново ^(при установке отметьте галочку "Set up PATH"^).
    echo.
    echo Попробуем собрать без DLL - на чужих машинах cairo не заработает,
    echo exe будет искать libcairo в системном PATH.
    pause
)
set "DLL_DIR=%~dp0cairo_dll"

echo --- [4/4] PyInstaller ---
python -m PyInstaller --noconfirm --clean build_exe.spec || goto :err

REM DLL копируем вместе с зависимостями cairo рядом с exe (для работы на машинах без GTK runtime)
if defined CAIRO_DIR (
    if exist "dist\MandalaGenerator" (
        mkdir "dist\MandalaGenerator\cairo_dll" 2>nul
        copy /y "%CAIRO_DIR%libcairo-2.dll" "dist\MandalaGenerator\cairo_dll\" >nul
        copy /y "%CAIRO_DIR%libfontconfig-1.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        copy /y "%CAIRO_DIR%libfreetype-6.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        copy /y "%CAIRO_DIR%libharfbuzz-0.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        copy /y "%CAIRO_DIR%libpixman-1-0.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        copy /y "%CAIRO_DIR%libpng16-16.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        copy /y "%CAIRO_DIR%libcairo-gobject-2.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        copy /y "%CAIRO_DIR%libwoff2-1.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        copy /y "%CAIRO_DIR%libbrotlidec.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        copy /y "%CAIRO_DIR%libbrotlicommon.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        copy /y "%CAIRO_DIR%zlib1.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        copy /y "%CAIRO_DIR%liblzma-5.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        copy /y "%CAIRO_DIR%libintl-8.dll" "dist\MandalaGenerator\cairo_dll\" >nul 2>&1
        echo DLL Cairo скопированы в dist\MandalaGenerator\cairo_dll
    )
)

echo.
echo =====================================================================
echo ГОТОВО:  dist\MandalaGenerator\MandalaGenerator.exe
echo Можно запустить сразу; для раздачи пользователям - архивировать ВЕСЬ
echo каталог dist\MandalaGenerator (или через Inno Setup: MandalaInstaller.iss)
echo =====================================================================
pause
exit /b 0

:err
echo.
echo СБОРКА ПРОШЛА С ОШИБКОЙ - прочитайте текст выше.
pause
exit /b 1
