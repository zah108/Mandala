"""Каталоги данных приложения: готовые мандалы, логи, настройки.

Три режима работы:

1. Запуск из исходников (dev): всё по-прежнему внутри пакета —
   ``img/`` и ``log/`` рядом с кодом, настройки по желанию в
   ``config.ini`` в корне проекта (файл не создаётся автоматически).

2. Собранное приложение (PyInstaller), обычная установка:
   мандалы -> ``Изображения\\Mandala`` (в домашней папке пользователя),
   логи    -> ``%LOCALAPPDATA%\\Mandala\\logs``,
   конфиг  -> ``%APPDATA%\\Mandala\\config.ini`` (создаётся автоматически).

3. Портативный режим: если рядом с exe лежит файл-метка ``portable.ini``,
   всё хранится рядом с exe (``img/``, ``log/``, ``config.ini``).

Физический путь ``%USERPROFILE%\\Pictures`` в русской Windows в
проводнике отображается как «Изображения» — это одна и та же папка.
"""
import os
import sys

PORTABLE_MARKER = "portable.ini"
CONFIG_FILENAME = "config.ini"
APP_DIR_NAME = "Mandala"


def is_frozen():
    """True, если код запущен из сборки PyInstaller."""
    return getattr(sys, "frozen", False)


def package_dir():
    """Каталог пакета mandala (в dev-режиме — сама папка пакета)."""
    return os.path.dirname(os.path.abspath(__file__))


def exe_dir():
    """Каталог exe (сборка) или корень проекта (dev)."""
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(package_dir())


def is_portable():
    """Портативный режим: метка portable.ini рядом с exe."""
    return os.path.exists(os.path.join(exe_dir(), PORTABLE_MARKER))


def images_dir():
    """Куда сохранять готовые мандалы."""
    if not is_frozen():
        return os.path.join(package_dir(), "img")
    if is_portable():
        return os.path.join(exe_dir(), "img")
    return os.path.join(os.path.expanduser("~"), "Pictures", APP_DIR_NAME)


def logs_dir():
    """Куда писать журнал запусков."""
    if not is_frozen():
        return os.path.join(package_dir(), "log")
    if is_portable():
        return os.path.join(exe_dir(), "log")
    base = os.environ.get("LOCALAPPDATA") or os.path.join(
        os.path.expanduser("~"), ".mandala")
    return os.path.join(base, APP_DIR_NAME, "logs")


def config_dir():
    """Где искать/создавать config.ini."""
    if not is_frozen():
        return exe_dir()
    if is_portable():
        return exe_dir()
    base = os.environ.get("APPDATA") or os.path.join(
        os.path.expanduser("~"), ".mandala")
    return os.path.join(base, APP_DIR_NAME)


def config_path():
    return os.path.join(config_dir(), CONFIG_FILENAME)


def ensure_dirs():
    """Создаёт все нужные каталоги (безопасно вызывать многократно)."""
    for d in (images_dir(), logs_dir(), config_dir()):
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass
