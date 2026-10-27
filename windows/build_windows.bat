@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Сборка Mandala Generator для Windows

rem Сборка выполняется на Windows-машине с интернетом.
rem Результат: dist\MandalaSetup-<версия>.exe и dist\Mandala-portable-<версия>.zip
rem На целевом компьютере Python не нужен — всё уже внутри.

cd /d "%~dp0.."

set "VENV=.venv-win"
set "VPY=%VENV%\Scripts\python.exe"
set "REQ=windows\requirements-win.txt"
set "PYVER=3.12.8"
set "PYURL=https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-amd64.exe"

echo ==============================================================
echo   Сборка Mandala Generator для Windows
echo   1/5 Python   2/5 библиотеки   3/5 PyInstaller
echo   4/5 инсталлятор   5/5 portable-zip
echo ==============================================================
echo.

rem ---------------- 1. Python ----------------
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1 && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1 && set "PY=python"
if defined PY goto :have_python

echo [1/5] Python не найден. Скачиваю Python %PYVER% ...
set "PYPKG=%TEMP%\python-%PYVER%-amd64.exe"
call :download "%PYURL%" "%PYPKG%" || goto :fail
echo [1/5] Устанавливаю Python %PYVER% (без прав администратора) ...
"%PYPKG%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 || goto :fail
py -3 -c "import sys" >nul 2>&1 && set "PY=py -3"
if not defined PY goto :fail

:have_python
echo [1/5] Python найден: %PY%
echo.

rem ---------------- 2. Окружение и зависимости ----------------
if not exist "%VPY%" (
  echo [2/5] Создаю виртуальное окружение %VENV% ...
  %PY% -m venv "%VENV%" || goto :fail
)
echo [2/5] Устанавливаю зависимости ...
"%VPY%" -m pip install --upgrade pip >nul || goto :fail
"%VPY%" -m pip install -r "%REQ%" || goto :fail
echo.

rem ---------------- 3. Приложение (PyInstaller) ----------------
echo [3/5] Собираю приложение ...
"%VPY%" -m PyInstaller windows\mandala.spec --noconfirm --distpath dist --workpath build\pyinstaller || goto :fail
if not exist "dist\Mandala\Mandala.exe" goto :fail
dir /s /b "dist\Mandala\_internal\*cairo*.pyd" >nul 2>&1 || dir /s /b "dist\Mandala\_internal\libcairo*.dll" >nul 2>&1 || echo ВНИМАНИЕ: Cairo не найден в сборке (_cairo.pyd) — сохранение PDF не заработает.
echo.

rem ---------------- 4. Инсталлятор (Inno Setup) ----------------
set "ISCC="
set "INNO_OK="
call :find_iscc
if not defined ISCC (
  echo [4/5] Inno Setup не найден. Устанавливаю ...
  for %%V in (6.3.3 6.2.1) do call :try_inno %%V
  call :find_iscc
)
if defined ISCC (
  echo [4/5] Компилирую инсталлятор ...
  "%ISCC%" windows\installer\mandala.iss || goto :fail
) else (
  echo [4/5] Предупреждение: Inno Setup недоступен, инсталлятор пропущен.
)
echo.

rem ---------------- 5. Portable-zip ----------------
echo [5/5] Собираю portable-zip ...
powershell -NoProfile -ExecutionPolicy Bypass -File "windows\make_portable.ps1" || goto :fail

echo.
echo ==============================================================
echo   Готово. Результаты в каталоге dist\ :
dir /b dist\MandalaSetup-*.exe 2>nul
dir /b dist\Mandala-portable-*.zip 2>nul
echo ==============================================================
start "" "dist"
pause
exit /b 0

:fail
echo.
echo ОШИБКА: сборка прервана. Смотрите сообщения выше.
pause
exit /b 1

rem ---------------- подпрограммы ----------------

:download
rem %1 = URL, %2 = куда сохранить
where curl >nul 2>&1
if not errorlevel 1 (
  curl -L --retry 2 -sS -o "%~2" "%~1" && if exist "%~2" exit /b 0
)
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%~1' -OutFile '%~2'" && if exist "%~2" exit /b 0
echo Не удалось скачать: %~1
exit /b 1

:find_iscc
for %%D in ("%ProgramFiles(x86)%\Inno Setup 6" "%ProgramFiles%\Inno Setup 6" "%LocalAppData%\Programs\Inno Setup 6") do (
  if exist "%%~D\ISCC.exe" set "ISCC=%%~D\ISCC.exe"
)
exit /b 0

:try_inno
if defined INNO_OK exit /b 0
set "INNO_TMP=%TEMP%\innosetup-%1.exe"
call :download "https://files.jrsoftware.org/is/6/innosetup-%1.exe" "%INNO_TMP%" || exit /b 0
"%INNO_TMP%" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CURRENTUSER && set "INNO_OK=1"
exit /b 0
