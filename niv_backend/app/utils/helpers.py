"""Funciones auxiliares para el sistema de generación de NIV."""
from __future__ import annotations

from app.core.check_digit import PROHIBITED_CHARS

# Secuencia estándar (ISO 3779) de códigos de año-modelo, ciclo de 30 años.
YEAR_CODE_SEQUENCE: tuple[str, ...] = (
    "A", "B", "C", "D", "E", "F", "G", "H", "J", "K",
    "L", "M", "N", "P", "R", "S", "T", "V", "W", "X",
    "Y", "1", "2", "3", "4", "5", "6", "7", "8", "9",
)

_YEAR_CYCLE_ANCHOR = 2010  # año 2010 == código "A" en el ciclo vigente (2010-2039)
_YEAR_CYCLE_LENGTH = len(YEAR_CODE_SEQUENCE)


def year_to_code(anio: int) -> str:
    """Convierte un año modelo (ej. 2026) a su código de una letra/dígito (ej. 'T')."""
    index = (anio - _YEAR_CYCLE_ANCHOR) % _YEAR_CYCLE_LENGTH
    return YEAR_CODE_SEQUENCE[index]


def code_to_years(codigo: str, anio_min: int = 2010, anio_max: int = 2100) -> list[int]:
    """Devuelve los años posibles (dentro del rango dado) para un código de año dado."""
    codigo = codigo.upper()
    if codigo not in YEAR_CODE_SEQUENCE:
        raise ValueError(f"Código de año inválido: '{codigo}'.")
    target_index = YEAR_CODE_SEQUENCE.index(codigo)
    return [
        year
        for year in range(anio_min, anio_max + 1)
        if (year - _YEAR_CYCLE_ANCHOR) % _YEAR_CYCLE_LENGTH == target_index
    ]


def format_serie(numero: int, longitud: int = 5) -> str:
    """Formatea el número de serie con ceros a la izquierda (ej. 1 -> '00001')."""
    limite = 10**longitud - 1
    if not 1 <= numero <= limite:
        raise ValueError(f"Número de serie fuera de rango (1-{limite}): {numero}.")
    return str(numero).zfill(longitud)


def has_prohibited_chars(texto: str) -> list[str]:
    """Retorna la lista de caracteres prohibidos encontrados en el texto (I, O, Q, Ñ)."""
    return [c for c in texto.upper() if c in PROHIBITED_CHARS]
