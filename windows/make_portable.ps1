# Собирает portable-zip из dist\Mandala (после шага PyInstaller).
# Вызывается из build_windows.bat или вручную:
#   powershell -NoProfile -ExecutionPolicy Bypass -File windows\make_portable.ps1
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$version = (Get-Content "windows\version.txt" -Raw).Trim()
$src = "dist\Mandala"
$tmp = "dist\Mandala-portable"
$zip = "dist\Mandala-portable-$version.zip"

if (-not (Test-Path "$src\Mandala.exe")) {
    throw "Не найдено $src\Mandala.exe — сначала выполните шаг PyInstaller."
}

if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
robocopy $src $tmp /E /NFL /NDL /NJH /NJS | Out-Null
# robocopy: коды 0..7 — норма (1 = файлы скопированы), 8+ — ошибка.
if ($LASTEXITCODE -ge 8) { throw "robocopy завершился с ошибкой: код $LASTEXITCODE" }
$global:LASTEXITCODE = 0

# Метка портативного режима: данные хранятся рядом с exe, а не в AppData.
New-Item -ItemType File -Path "$tmp\portable.ini" -Force | Out-Null
Copy-Item "README_Windows.md" $tmp -Force

if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path "$tmp\*" -DestinationPath $zip -Force
Remove-Item $tmp -Recurse -Force

Write-Host "Portable-версия: $zip"
exit 0
