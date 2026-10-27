# Обновляет windows\cairo_dlls свежими Cairo DLL из MSYS2.
#
# ОБЫЧНО НЕ НУЖНО: DLL уже лежат в репозитории и попадают в сборку сами.
# Скрипт нужен, только если захочется обновить Cairo (например, из-за
# уязвимости). Требует интернет.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File windows\update_cairo_dlls.ps1
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$dest = "windows\cairo_dlls"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$work = Join-Path $env:TEMP "mandala-cairo-dlls"
New-Item -ItemType Directory -Force -Path $work | Out-Null

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# 1) zstd.exe (для распаковки .pkg.tar.zst)
$zstdExe = Join-Path $work "zstd\zstd.exe"
if (-not (Test-Path $zstdExe)) {
    Write-Host "Скачиваю zstd ..."
    $zip = Join-Path $work "zstd.zip"
    Invoke-WebRequest "https://github.com/facebook/zstd/releases/download/v1.5.6/zstd-v1.5.6-win64.zip" -OutFile $zip
    Expand-Archive $zip (Join-Path $work "zstd") -Force
}

# 2) Список пакетов и последние версии
Write-Host "Читаю список пакетов repo.msys2.org ..."
$index = Invoke-WebRequest "https://repo.msys2.org/mingw/mingw64/" -UseBasicParsing

# Пакеты, чьи DLL нужны libcairo-2.dll (и её зависимостям).
$packages = @(
    "cairo", "pixman", "libpng", "zlib", "freetype", "fontconfig", "expat",
    "harfbuzz", "glib2", "libiconv", "gettext-runtime", "gettext",
    "gcc-libs", "brotli", "bzip2", "libffi", "pcre2", "graphite2"
)

$manifest = @()
foreach ($pkg in $packages) {
    $pattern = "^" + $pkg + "-([\d\.]+)-(\d+)-any\.pkg\.tar\.zst$"
    $candidates = @($index.Links.href | Where-Object { $_ -match $pattern })
    if ($candidates.Count -eq 0) {
        Write-Warning "Пакет не найден: $pkg"
        continue
    }
    # Выбираем максимальную версию (сравнение как System.Version).
    $best = $candidates | Sort-Object {
        if ($_ -match $pattern) { [version]$Matches[1] } else { [version]"0.0" }
    } | Select-Object -Last 1

    $fileUrl = "https://repo.msys2.org/mingw/mingw64/$best"
    $pkgZst = Join-Path $work $best
    $pkgTar = [IO.Path]::ChangeExtension($pkgZst, ".tar")
    Write-Host "Качаю $best ..."
    if (-not (Test-Path $pkgZst)) {
        Invoke-WebRequest $fileUrl -OutFile $pkgZst
    }
    if (-not (Test-Path $pkgTar)) {
        & $zstdExe -d -f -q $pkgZst -o $pkgTar
    }
    $extract = Join-Path $work ([IO.Path]::GetFileNameWithoutExtension($best))
    New-Item -ItemType Directory -Force -Path $extract | Out-Null
    tar -xf $pkgTar -C $extract "mingw64/bin/*.dll"
    Get-ChildItem (Join-Path $extract "mingw64\bin") -Filter *.dll -ErrorAction SilentlyContinue |
        ForEach-Object {
            Copy-Item $_.FullName $dest -Force
            $manifest += "$best -> $($_.Name)"
        }
}

$manifest | Set-Content (Join-Path $dest "SOURCES.txt") -Encoding UTF8
Write-Host "Готово. DLL в $dest :"
Get-ChildItem $dest -Filter *.dll | ForEach-Object { Write-Host "  $($_.Name)" }
