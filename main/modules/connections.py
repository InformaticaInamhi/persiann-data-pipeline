# -*- coding: utf-8 -*-
"""Conexiones del pipeline PERSIANN."""

from __future__ import annotations

import psycopg2

from .config_loader import get_int, get_str
from .logger import LOGGER


def create_postgres_connection():
    host = get_str("POSTGRES", "host")
    port = get_int("POSTGRES", "port", 5432)
    database = get_str("POSTGRES", "database")
    user = get_str("POSTGRES", "user")
    password = get_str("POSTGRES", "password")

    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
    )

    LOGGER.info("INF-CONN-001", f"Conexión PostgreSQL establecida con {host}:{port}")
    return conn


def get_schema_name() -> str:
    return get_str("POSTGRES", "schema")


def get_table_name() -> str:
    return get_str("POSTGRES", "table")


def get_id_usuario() -> int:
    return get_int("GENERAL", "id_usuario", 1)
