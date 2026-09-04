"""Punto de entrada de la aplicación FastAPI - Sistema Generador de NIV."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.endpoints import export, niv, search
from app.config import get_settings
from app.core.niv_generator import NIVGeneratorError
from app.core.rate_limit import limiter

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = f"/api/{settings.api_version}"
app.include_router(niv.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(export.router, prefix=API_PREFIX)


@app.exception_handler(NIVGeneratorError)
async def niv_generator_error_handler(request: Request, exc: NIVGeneratorError) -> JSONResponse:
    """Convierte errores de negocio de generación de NIV en respuestas 400 consistentes."""
    logger.warning("Error de negocio en %s: %s", request.url.path, exc)
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "error": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura cualquier error no controlado y responde 500 sin exponer detalles internos."""
    logger.exception("Error no controlado en %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": "Error interno del servidor."},
    )


@app.get("/health", tags=["Sistema"])
def health_check() -> dict[str, str]:
    """Endpoint de verificación de salud del servicio."""
    return {"status": "ok"}
