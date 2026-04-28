# -*- coding: utf-8 -*-
"""Procesador para descarga e inserción de PERSIANN-CCS hacia PostgreSQL."""

from __future__ import annotations

import gzip
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from psycopg2.extras import execute_values

from .config_loader import get_float, get_int, get_project_root, get_str
from .connections import create_postgres_connection, get_id_usuario, get_schema_name, get_table_name
from .logger import LOGGER


class PersiannPipelineProcessor:
    def __init__(self) -> None:
        self.base_url = get_str("PERSIANN", "base_url")
        self.nrow = get_int("PERSIANN", "nrow", 3000)
        self.ncol = get_int("PERSIANN", "ncol", 9000)
        self.scale_factor = get_float("PERSIANN", "scale_factor", 100.0)
        self.timeout = get_int("PERSIANN", "request_timeout", 30)

        self.project_root = get_project_root()
        self.mask_file = self._resolve_path(get_str("GRID", "mask_file"))

        self.schema = get_schema_name()
        self.table = get_table_name()
        self.id_usuario = get_id_usuario()

    def _resolve_path(self, path_value: str) -> Path:
        path = Path(path_value)
        if path.is_absolute():
            return path
        return self.project_root / path

    @staticmethod
    def build_filename(ts: datetime) -> str:
        yy = str(ts.year)[2:]
        jjj = ts.timetuple().tm_yday
        hh = ts.hour
        return f"rgccs3h{yy}{jjj:03d}{hh:02d}.bin.gz"

    @staticmethod
    def get_download_timestamp(now: datetime | None = None) -> datetime:
        now = now or datetime.now()
        current_window = now.replace(minute=0, second=0, microsecond=0)
        hour_mod3 = current_window.hour - (current_window.hour % 3)
        current_window = current_window.replace(hour=hour_mod3)
        return current_window - timedelta(hours=3)

    def load_mask(self) -> np.ndarray:
        if not self.mask_file.exists():
            LOGGER.error("ERR-MASK-001", f"No existe la máscara espacial: {self.mask_file}")
            raise FileNotFoundError(f"No existe la máscara espacial: {self.mask_file}")

        cell_indices = np.load(self.mask_file)
        LOGGER.info("INF-MASK-001", f"Máscara cargada correctamente: {len(cell_indices)} celdas válidas")
        return cell_indices

    def download_persiann(self, ts: datetime, cell_indices: np.ndarray) -> np.ndarray | None:
        filename = self.build_filename(ts)
        url = f"{self.base_url}/{filename}"

        LOGGER.info("INF-PERS-001", f"Descargando archivo PERSIANN: {url}")

        try:
            response = requests.get(url, timeout=self.timeout)

            if response.status_code != 200:
                LOGGER.warning("WAR-PERS-001", f"Archivo no disponible. HTTP {response.status_code}: {filename}")
                return None

            arr = np.frombuffer(gzip.decompress(response.content), dtype=">h").astype(float)

            expected_size = self.nrow * self.ncol
            if arr.size != expected_size:
                LOGGER.error("ERR-PERS-002", f"Tamaño inválido: {arr.size}. Esperado: {expected_size}")
                return None

            arr = arr.reshape(self.nrow, self.ncol)
            arr = np.flipud(np.hstack((arr[:, self.ncol // 2:], arr[:, : self.ncol // 2]))) / self.scale_factor
            arr[arr < 0] = np.nan

            values = arr.ravel()[cell_indices]
            LOGGER.info("INF-PERS-002", f"Archivo procesado correctamente: {filename}. Valores extraídos: {len(values)}")
            return values

        except Exception as exc:
            LOGGER.error("ERR-PERS-001", f"Error descargando/procesando PERSIANN {ts}: {exc}")
            return None

    def build_rows(self, ts: datetime, values: np.ndarray) -> list[tuple]:
        df = pd.DataFrame(
            {
                "fecha_dato": [ts.date()] * len(values),
                "id_estacion": np.arange(1, len(values) + 1),
                "valor": values,
                "id_usuario": [self.id_usuario] * len(values),
            }
        )

        return [
            (row["fecha_dato"], row["id_estacion"], row["valor"], row["id_usuario"])
            for _, row in df.iterrows()
        ]

    def insert_into_postgres(self, ts: datetime, rows: list[tuple]) -> None:
        column_hour = f'"{ts.hour}h"'

        sql = f"""
        INSERT INTO {self.schema}.{self.table} (fecha_dato, id_estacion, {column_hour}, id_usuario)
        VALUES %s
        ON CONFLICT (fecha_dato, id_estacion)
        DO UPDATE SET {column_hour} = EXCLUDED.{column_hour};
        """

        conn = None
        cur = None

        try:
            conn = create_postgres_connection()
            cur = conn.cursor()
            execute_values(cur, sql, rows, template="(%s,%s,%s,%s)", page_size=1000)
            conn.commit()

            LOGGER.info(
                "INF-DB-001",
                f"Datos insertados/actualizados para {ts.date()} columna {column_hour}. Registros: {len(rows)}",
            )

        except Exception as exc:
            if conn is not None:
                conn.rollback()
            LOGGER.error("ERR-DB-001", f"Error insertando datos en PostgreSQL: {exc}")
            raise

        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                conn.close()

    def run(self) -> None:
        LOGGER.info("INF-MASTER-001", "Inicio de ejecución del pipeline PERSIANN")

        ts_download = self.get_download_timestamp()
        LOGGER.info("INF-PERS-003", f"Ventana de descarga calculada: {ts_download}")

        cell_indices = self.load_mask()
        values = self.download_persiann(ts_download, cell_indices)

        if values is None:
            LOGGER.warning("WAR-MASTER-001", f"No hay datos disponibles para {ts_download}. Proceso finalizado sin inserción")
            return

        rows = self.build_rows(ts_download, values)
        self.insert_into_postgres(ts_download, rows)

        LOGGER.info("INF-MASTER-999", "Proceso PERSIANN completado correctamente")
