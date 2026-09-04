"""Validador de estructura y contenido de un NIV según NOM-001-SSP-2008."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.check_digit import CHECK_DIGIT_POSITION, NIV_LENGTH, PROHIBITED_CHARS, verify_check_digit

# Permite A-Z excepto I, O, Q (caracteres prohibidos), más dígitos 0-9.
_VALID_CHAR_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


@dataclass
class ValidationResult:
    """Resultado de una validación de NIV, con lista de errores descriptivos en español."""

    valido: bool
    errores: list[str] = field(default_factory=list)


def validar_formato(niv: str) -> ValidationResult:
    """Valida longitud, caracteres permitidos y dígito verificador de un NIV completo."""
    errores: list[str] = []

    if not niv:
        return ValidationResult(False, ["El NIV no puede estar vacío."])

    niv = niv.upper()

    if len(niv) != NIV_LENGTH:
        errores.append(f"El NIV debe tener exactamente {NIV_LENGTH} caracteres (tiene {len(niv)}).")

    prohibidos = sorted({c for c in niv if c in PROHIBITED_CHARS})
    if prohibidos:
        errores.append(f"Caracteres prohibidos encontrados: {', '.join(prohibidos)}.")

    formato_valido = bool(_VALID_CHAR_PATTERN.match(niv))
    if not formato_valido:
        errores.append("El NIV contiene caracteres no permitidos (solo A-Z sin I, O, Q, y 0-9).")

    if formato_valido and not verify_check_digit(niv):
        errores.append(f"Dígito verificador inválido en la posición {CHECK_DIGIT_POSITION}.")

    return ValidationResult(valido=not errores, errores=errores)
