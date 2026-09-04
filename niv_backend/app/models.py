"""Modelos SQLAlchemy: tablas del sistema de generación de NIV."""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)

from app.database import Base


class NIV(Base):
    """Registro histórico de cada Número de Identificación Vehicular generado."""

    __tablename__ = "niv"

    id = Column(Integer, primary_key=True, index=True)
    niv = Column(String(17), unique=True, nullable=False, index=True)
    wmi = Column(String(3), nullable=False)
    vds = Column(String(5), nullable=False)
    digito_verificador = Column(String(1), nullable=False)
    vis = Column(String(8), nullable=False)

    tipo_remolque = Column(String(50), nullable=False, index=True)
    num_ejes = Column(Integer, nullable=False)
    capacidad = Column(String(10), nullable=False)
    tipo_frenos = Column(String(20), nullable=False)
    version = Column(String(20), nullable=False)

    anio_modelo = Column(Integer, nullable=False, index=True)
    codigo_anio = Column(String(1), nullable=False)
    planta = Column(String(1), nullable=False)
    linea_produccion = Column(Integer, nullable=False)
    numero_serie = Column(Integer, nullable=False)

    fecha_generacion = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("linea_produccion", "anio_modelo", "numero_serie", name="uq_linea_anio_serie"),
        CheckConstraint("num_ejes BETWEEN 1 AND 9", name="ck_num_ejes_rango"),
    )


class Configuracion(Base):
    """Parámetros configurables del sistema (WMI, planta, año de inicio, DXF, etc.)."""

    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True)
    clave = Column(String(50), unique=True, nullable=False)
    valor = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    tipo = Column(String(20), default="string")
    fecha_modificacion = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MapeoVDS(Base):
    """Tabla de mapeo configurable para las posiciones del VDS (4, 6, 7, 8)."""

    __tablename__ = "mapeo_vds"

    id = Column(Integer, primary_key=True)
    posicion = Column(Integer, nullable=False)
    codigo = Column(String(10), nullable=False)
    descripcion = Column(String(100), nullable=False)
    categoria = Column(String(50), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)

    __table_args__ = (UniqueConstraint("posicion", "codigo", name="uq_posicion_codigo"),)


class SerieContador(Base):
    """Contador atómico de serie secuencial, independiente por línea de producción y año modelo."""

    __tablename__ = "serie_contador"

    id = Column(Integer, primary_key=True)
    linea_produccion = Column(Integer, nullable=False)
    anio_modelo = Column(Integer, nullable=False)
    ultimo_numero = Column(Integer, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("linea_produccion", "anio_modelo", name="uq_linea_anio"),)
