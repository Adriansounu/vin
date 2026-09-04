"""Script de inicialización de base de datos: crea tablas y siembra datos iniciales.

Uso:
    python scripts/init_db.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Configuracion, MapeoVDS  # noqa: E402

CONFIGURACION_INICIAL = [
    ("wmi", None, "Identificador Mundial del Fabricante", "string"),
    ("planta_default", None, "Código de planta por defecto", "string"),
    ("anio_inicio", None, "Año de inicio de operaciones", "integer"),
    ("dxf_altura_texto", "3", "Altura de texto en DXF (mm)", "float"),
    ("dxf_espaciado", "0.5", "Espaciado entre caracteres DXF (mm)", "float"),
]

MAPEO_INICIAL = [
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


def main() -> None:
    """Crea todas las tablas (si no existen) y siembra configuración y mapeo VDS iniciales."""
    settings = get_settings()
    print(f"Creando tablas en: {settings.database_url}")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        valores_dinamicos = {
            "wmi": settings.wmi,
            "planta_default": settings.planta_default,
            "anio_inicio": str(settings.anio_inicio),
        }
        for clave, valor_default, descripcion, tipo in CONFIGURACION_INICIAL:
            existente = db.execute(select(Configuracion).where(Configuracion.clave == clave)).scalar_one_or_none()
            if existente is not None:
                continue
            valor = valores_dinamicos.get(clave, valor_default)
            db.add(Configuracion(clave=clave, valor=valor, descripcion=descripcion, tipo=tipo))

        for posicion, codigo, descripcion, categoria in MAPEO_INICIAL:
            existente = db.execute(
                select(MapeoVDS).where(MapeoVDS.posicion == posicion, MapeoVDS.codigo == codigo)
            ).scalar_one_or_none()
            if existente is not None:
                continue
            db.add(MapeoVDS(posicion=posicion, codigo=codigo, descripcion=descripcion, categoria=categoria))

        db.commit()
        print("Base de datos inicializada correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
