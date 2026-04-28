# -*- coding: utf-8 -*-
"""Logger estructurado en formato ELF para el pipeline PERSIANN."""

from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path

import pytz

from .config_loader import get_str


class ELFLogger:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[2]
        self.log_dir = self.project_root / "main" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "app.log"

        self.usuario = get_str("GENERAL", "usuario_app", "persiann_pipeline")
        self.ip = get_str("GENERAL", "ip", "N/A")
        self.timezone = pytz.timezone(get_str("GENERAL", "timezone", "America/Guayaquil"))

    def _write(self, tipo: str, codigo: str, mensaje: str) -> None:
        now = datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")

        frame = inspect.currentframe()
        caller = frame.f_back.f_back if frame and frame.f_back and frame.f_back.f_back else None

        if caller:
            archivo = Path(caller.f_code.co_filename).name
            metodo = caller.f_code.co_name
            linea = caller.f_lineno
        else:
            archivo = "N/A"
            metodo = "N/A"
            linea = "N/A"

        contexto = f"archivo: {archivo}, clase: N/A, metodo: {metodo}, linea: {linea}"
        mensaje = str(mensaje).replace("\n", " ")[:300]

        line = f"{now} | {tipo} | {self.ip} | {codigo} | {mensaje} | {self.usuario} | {contexto}"

        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

        print(line)

    def info(self, codigo: str, mensaje: str) -> None:
        self._write("INFO", codigo, mensaje)

    def warning(self, codigo: str, mensaje: str) -> None:
        self._write("WARNING", codigo, mensaje)

    def error(self, codigo: str, mensaje: str) -> None:
        self._write("ERROR", codigo, mensaje)

    def debug(self, codigo: str, mensaje: str) -> None:
        self._write("DEBUG", codigo, mensaje)


LOGGER = ELFLogger()
