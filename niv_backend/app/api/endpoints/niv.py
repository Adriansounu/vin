"""Endpoints para generación y consulta individual de un NIV."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.core.niv_generator import NIVGenerator, NIVGeneratorError
from app.core.rate_limit import limiter
from app.database import get_db
from app.models import NIV
from app.schemas import APIResponse, NIVDesglose, NIVDetalles, NIVGenerateData, NIVGenerateRequest, NIVOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/niv", tags=["NIV"])


@router.post("/generate", response_model=APIResponse[NIVGenerateData], status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
def generate_niv(
    request: Request,
    payload: NIVGenerateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> APIResponse[NIVGenerateData]:
    """Genera un nuevo NIV a partir de las características del remolque."""
    generator = NIVGenerator(db=db, settings=settings)
    try:
        registro = generator.generate(
            tipo_remolque=payload.tipo_remolque,
            num_ejes=payload.num_ejes,
            capacidad=payload.capacidad,
            tipo_frenos=payload.tipo_frenos,
            version=payload.version,
            anio_modelo=payload.anio_modelo,
            linea_produccion=payload.linea_produccion,
            planta=payload.planta,
        )
    except NIVGeneratorError as exc:
        logger.warning("Solicitud de generación de NIV rechazada: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - error inesperado, se registra y responde 500
        logger.exception("Error inesperado al generar NIV")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al generar el NIV."
        ) from exc

    data = NIVGenerateData(
        niv=registro.niv,
        desglose=NIVDesglose(
            wmi=registro.wmi,
            vds=registro.vds,
            check_digit=registro.digito_verificador,
            vis=registro.vis,
        ),
        detalles=NIVDetalles(
            tipo_remolque=registro.tipo_remolque,
            num_ejes=registro.num_ejes,
            capacidad=registro.capacidad,
            tipo_frenos=registro.tipo_frenos,
            version=registro.version,
            anio_modelo=registro.anio_modelo,
            linea_produccion=registro.linea_produccion,
            numero_serie=registro.numero_serie,
        ),
        timestamp=registro.fecha_generacion,
    )
    return APIResponse(success=True, data=data)


@router.get("/{niv}", response_model=APIResponse[NIVOut])
def get_niv(niv: str, db: Session = Depends(get_db)) -> APIResponse[NIVOut]:
    """Obtiene el detalle completo de un NIV específico ya registrado."""
    registro = db.execute(select(NIV).where(NIV.niv == niv.upper())).scalar_one_or_none()
    if registro is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"NIV '{niv}' no encontrado.")
    return APIResponse(success=True, data=NIVOut.model_validate(registro))
