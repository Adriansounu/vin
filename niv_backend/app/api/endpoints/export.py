"""Endpoints de exportación de datos NIV a Excel y DXF."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import NIV
from app.schemas import ExportDXFRequest, ExportExcelRequest
from app.utils.exporters import export_niv_to_dxf, export_niv_to_excel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export", tags=["Exportación"])


@router.post("/excel")
def export_excel(payload: ExportExcelRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    """Exporta a Excel (.xlsx) los NIV que cumplan los filtros dados."""
    filtros = payload.filters
    stmt = select(NIV)

    if filtros.niv:
        stmt = stmt.where(NIV.niv.ilike(f"%{filtros.niv.upper()}%"))
    if filtros.tipo_remolque:
        stmt = stmt.where(NIV.tipo_remolque.ilike(f"%{filtros.tipo_remolque}%"))
    if filtros.anio_modelo is not None:
        stmt = stmt.where(NIV.anio_modelo == filtros.anio_modelo)
    if filtros.linea_produccion is not None:
        stmt = stmt.where(NIV.linea_produccion == filtros.linea_produccion)
    if filtros.fecha_desde is not None:
        stmt = stmt.where(NIV.fecha_generacion >= filtros.fecha_desde)
    if filtros.fecha_hasta is not None:
        stmt = stmt.where(NIV.fecha_generacion <= filtros.fecha_hasta)

    registros = db.execute(stmt.order_by(NIV.fecha_generacion.desc())).scalars().all()

    try:
        buffer = export_niv_to_excel(registros)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error al generar archivo Excel")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al generar el archivo Excel."
        ) from exc

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="remolques_niv.xlsx"'},
    )


@router.post("/dxf")
def export_dxf(
    payload: ExportDXFRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """Exporta uno o varios NIV a un archivo DXF listo para grabado láser."""
    nivs_normalizados = [n.upper() for n in payload.nivs]
    registros = db.execute(select(NIV).where(NIV.niv.in_(nivs_normalizados))).scalars().all()

    encontrados = {r.niv for r in registros}
    faltantes = [n for n in nivs_normalizados if n not in encontrados]
    if faltantes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NIV no encontrados en base de datos: {', '.join(faltantes)}",
        )

    orden = {n: i for i, n in enumerate(nivs_normalizados)}
    registros = sorted(registros, key=lambda r: orden[r.niv])

    try:
        buffer = export_niv_to_dxf(
            nivs=[r.niv for r in registros],
            altura_texto=payload.config.altura_texto,
            espaciado=payload.config.espaciado,
            fuente=settings.dxf_fuente,
            batch=payload.config.batch,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error al generar archivo DXF")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al generar el archivo DXF."
        ) from exc

    filename = "niv_batch.dxf" if len(registros) > 1 and payload.config.batch else f"{registros[0].niv}.dxf"
    return StreamingResponse(
        buffer,
        media_type="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
