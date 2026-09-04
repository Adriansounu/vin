"""Fixtures compartidas para las pruebas del sistema NIV."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.database import Base
from app.models import MapeoVDS

# Semilla mínima de mapeo VDS necesaria para que el generador funcione en pruebas.
MAPEO_SEED = [
    (4, "A", "Caja seca", "tipo_remolque"),
    (4, "B", "Plataforma", "tipo_remolque"),
    (4, "C", "Tolva", "tipo_remolque"),
    (4, "D", "Refrigerado", "tipo_remolque"),
    (6, "A", "Menos de 20 toneladas", "capacidad"),
    (6, "B", "20-30 toneladas", "capacidad"),
    (6, "C", "30-40 toneladas", "capacidad"),
    (6, "D", "Más de 40 toneladas", "capacidad"),
    (7, "1", "Neumático", "tipo_frenos"),
    (7, "2", "Hidráulico", "tipo_frenos"),
    (7, "3", "Eléctrico", "tipo_frenos"),
    (8, "1", "Estándar", "version"),
    (8, "2", "Premium", "version"),
    (8, "3", "Especial", "version"),
]


@pytest.fixture()
def db_session() -> Session:
    """Provee una sesión SQLAlchemy sobre una base de datos SQLite en memoria, ya sembrada."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = session_local()

    for posicion, codigo, descripcion, categoria in MAPEO_SEED:
        session.add(MapeoVDS(posicion=posicion, codigo=codigo, descripcion=descripcion, categoria=categoria))
    session.commit()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def test_settings() -> Settings:
    """Configuración de prueba con valores fijos (WMI, planta, etc.)."""
    return Settings(wmi="3M1", planta_default="A", anio_inicio=2026, database_url="sqlite:///:memory:")
