# -*- coding: utf-8 -*-
"""Utilidades para lectura de configuración externa."""

from __future__ import annotations

import configparser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.ini"


def load_config() -> configparser.ConfigParser:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {CONFIG_PATH}")

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")
    return config


def get_project_root() -> Path:
    return PROJECT_ROOT


def get_str(section: str, option: str, default: str | None = None) -> str:
    config = load_config()

    if config.has_option(section, option):
        return config.get(section, option)

    if default is not None:
        return default

    raise KeyError(f"No existe la opción [{section}] {option} en config.ini")


def get_int(section: str, option: str, default: int | None = None) -> int:
    value = get_str(section, option, None if default is None else str(default))
    return int(value)


def get_float(section: str, option: str, default: float | None = None) -> float:
    value = get_str(section, option, None if default is None else str(default))
    return float(value)
