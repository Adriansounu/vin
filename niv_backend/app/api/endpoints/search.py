"""Endpoint de búsqueda y filtrado paginado de NIV registrados."""
from __future__ import annotations

from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NIV
from app.schemas import APIResponse, NIVOut, PaginatedNIV

router = APIRouter(prefix="/niv", tags=["Búsqueda"])

_SORTABLE_COLUMNS = {
    "fecha_generacion": NIV.fecha_generacion,
    "niv": NIV.niv,
    "anio_modelo": NIV.anio_modelo,
    "numero_serie": NIV.numero_serie,
}


@router.get("/search", response_model=APIResponse[PaginatedNIV])
def search_niv(
    niv: str | None = Query(default=None, description="NIV completo o parcial"),
    tipo_remolque: str | None = Query(default=None, description="Tipo de remolque (descripción o código)"),
    anio_modelo: int | None = Query(default=None, alias="año_modelo"),
    linea_produccion: int | None = Query(default=None),
    serie_desde: int | None = Query(default=None, ge=1),
    serie_hasta: int | None = Query(default=None, ge=1),
    fecha_desde: datetime | None = Query(default=None),
    fecha_hasta: datetime | None = Query(default=None),
    order_by: str = Query(default="fecha_generacion"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> APIResponse[PaginatedNIV]:
    """Busca NIVs registrados aplicando múltiples filtros opcionales, con paginación."""
    stmt = select(NIV)

    if niv:
        stmt = stmt.where(NIV.niv.ilike(f"%{niv.upper()}%"))
    if tipo_remolque:
        stmt = stmt.where(NIV.tipo_remolque.ilike(f"%{tipo_remolque}%"))
    if anio_modelo is not None:
        stmt = stmt.where(NIV.anio_modelo == anio_modelo)
    if linea_produccion is not None:
        stmt = stmt.where(NIV.linea_produccion == linea_produccion)
    if serie_desde is not None:
        stmt = stmt.where(NIV.numero_serie >= serie_desde)
    if serie_hasta is not None:
        stmt = stmt.where(NIV.numero_serie <= serie_hasta)
    if fecha_desde is not None:
        stmt = stmt.where(NIV.fecha_generacion >= fecha_desde)
    if fecha_hasta is not None:
        stmt = stmt.where(NIV.fecha_generacion <= fecha_hasta)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    column = _SORTABLE_COLUMNS.get(order_by, NIV.fecha_generacion)
    stmt = stmt.order_by(column.desc() if order_dir == "desc" else column.asc())
    stmt = stmt.limit(limit).offset(offset)

    items = db.execute(stmt).scalars().all()

    page = (offset // limit) + 1 if limit else 1
    pages = ceil(total / limit) if limit and total else 0

    data = PaginatedNIV(
        total=total,
        items=[NIVOut.model_validate(item) for item in items],
        page=page,
        pages=pages,
    )
    return APIResponse(success=True, data=data)
