"""Schemas Pydantic para validación de entrada/salida de la API REST."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class NIVGenerateRequest(BaseModel):
    """Datos requeridos para generar un nuevo NIV."""

    model_config = ConfigDict(populate_by_name=True)

    tipo_remolque: str = Field(..., min_length=1, max_length=1, description="Código de tipo de remolque (ej. 'A')")
    num_ejes: int = Field(..., ge=1, le=9, description="Número de ejes del remolque")
    capacidad: str = Field(..., min_length=1, max_length=1, description="Código de capacidad de carga")
    tipo_frenos: str = Field(..., min_length=1, max_length=1, description="Código de tipo de frenos")
    version: str = Field(..., min_length=1, max_length=1, description="Código de versión del modelo")
    anio_modelo: int = Field(..., alias="año_modelo", ge=2000, le=2100, description="Año modelo del vehículo")
    linea_produccion: int = Field(..., ge=1, le=9, description="Línea de producción")
    planta: str | None = Field(default=None, min_length=1, max_length=1, description="Código de planta (opcional)")

    @field_validator("tipo_remolque", "capacidad", "tipo_frenos", "version", "planta")
    @classmethod
    def _upper(cls, v: str | None) -> str | None:
        return v.upper() if v else v


class NIVDesglose(BaseModel):
    """Desglose de las secciones que componen un NIV (WMI, VDS, dígito, VIS)."""

    wmi: str
    vds: str
    check_digit: str
    vis: str


class NIVDetalles(BaseModel):
    """Detalles descriptivos (legibles) de las características codificadas en el NIV."""

    model_config = ConfigDict(populate_by_name=True)

    tipo_remolque: str
    num_ejes: int
    capacidad: str
    tipo_frenos: str
    version: str
    anio_modelo: int = Field(..., serialization_alias="año_modelo")
    linea_produccion: int
    numero_serie: int


class NIVGenerateData(BaseModel):
    """Datos de respuesta tras generar exitosamente un NIV."""

    niv: str
    desglose: NIVDesglose
    detalles: NIVDetalles
    timestamp: datetime


class NIVOut(BaseModel):
    """Representación completa de un registro NIV almacenado en base de datos."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    niv: str
    wmi: str
    vds: str
    digito_verificador: str
    vis: str
    tipo_remolque: str
    num_ejes: int
    capacidad: str
    tipo_frenos: str
    version: str
    anio_modelo: int = Field(..., serialization_alias="año_modelo")
    codigo_anio: str
    planta: str
    linea_produccion: int
    numero_serie: int
    fecha_generacion: datetime


class PaginatedNIV(BaseModel):
    """Resultado paginado de una búsqueda de NIV."""

    total: int
    items: list[NIVOut]
    page: int
    pages: int


class APIResponse(BaseModel, Generic[T]):
    """Envoltura estándar de respuesta JSON usada por todos los endpoints."""

    success: bool = True
    data: T | None = None
    error: str | None = None


class ExportExcelFilters(BaseModel):
    """Filtros opcionales para la exportación a Excel."""

    model_config = ConfigDict(populate_by_name=True)

    niv: str | None = None
    tipo_remolque: str | None = None
    anio_modelo: int | None = Field(default=None, alias="año_modelo")
    linea_produccion: int | None = None
    fecha_desde: datetime | None = None
    fecha_hasta: datetime | None = None


class ExportExcelRequest(BaseModel):
    """Cuerpo de la solicitud de exportación a Excel."""

    filters: ExportExcelFilters = Field(default_factory=ExportExcelFilters)


class DXFConfig(BaseModel):
    """Parámetros de generación del archivo DXF para grabado láser."""

    altura_texto: float = Field(default=3.0, gt=0, description="Altura de texto en mm")
    espaciado: float = Field(default=0.5, ge=0, description="Espaciado entre caracteres en mm")
    batch: bool = Field(default=True, description="Si es True, incluye todos los NIV en un solo archivo")


class ExportDXFRequest(BaseModel):
    """Cuerpo de la solicitud de exportación a DXF."""

    nivs: list[str] = Field(..., min_length=1)
    config: DXFConfig = Field(default_factory=DXFConfig)
