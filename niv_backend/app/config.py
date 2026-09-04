"""Configuración de la aplicación cargada desde variables de entorno (.env)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración centralizada del sistema, con valores por defecto seguros para desarrollo."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Base de datos
    database_url: str = "postgresql://user:password@localhost:5432/niv_db"

    # API
    api_version: str = "v1"
    api_title: str = "Sistema Generador de NIV"
    api_description: str = "API para generación y gestión de NIV según NOM-001-SSP-2008"

    # Configuración NIV
    # Nota: se usa "anio" (ASCII) en lugar de "año" para evitar problemas de
    # codificación de nombres de variables de entorno entre plataformas/shells.
    wmi: str = "3M1"
    planta_default: str = "A"
    anio_inicio: int = 2026

    # Exportación DXF
    dxf_altura_texto: float = 3.0
    dxf_espaciado: float = 0.5
    dxf_fuente: str = "Arial"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Retorna la instancia (cacheada) de configuración de la aplicación."""
    return Settings()
