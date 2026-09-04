"""Algoritmo de dígito verificador para NIV según NOM-001-SSP-2008 (base ISO 3779).

Referencia normativa (posición 9 del NIV):
  - Pesos por posición: [8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2]
  - Transliteración de letras a valores numéricos (ver TRANSLITERATION)
  - Suma ponderada módulo 11; si el residuo es 10, el dígito verificador es 'X'
  - Caracteres prohibidos: I, O, Q (y Ñ, fuera del alfabeto latino estándar usado)
"""
from __future__ import annotations

NIV_LENGTH = 17
CHECK_DIGIT_POSITION = 9  # posición 1-indexada dentro del NIV

# Tabla de transliteración oficial NOM-001-SSP-2008 / ISO 3779.
TRANSLITERATION: dict[str, int] = {
    **{str(d): d for d in range(10)},
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
}

PROHIBITED_CHARS: frozenset[str] = frozenset({"I", "O", "Q", "Ñ"})

WEIGHTS: tuple[int, ...] = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)


class CheckDigitError(ValueError):
    """Error al calcular o validar el dígito verificador de un NIV."""


def _char_value(char: str) -> int:
    """Convierte un carácter del NIV a su valor numérico de transliteración."""
    if char in PROHIBITED_CHARS:
        raise CheckDigitError(f"Carácter prohibido en NIV: '{char}'.")
    try:
        return TRANSLITERATION[char]
    except KeyError as exc:
        raise CheckDigitError(f"Carácter inválido en NIV: '{char}'.") from exc


def calculate_check_digit(niv_17: str) -> str:
    """Calcula el dígito verificador (posición 9) de una cadena NIV de 17 caracteres.

    El carácter ubicado en la posición 9 puede ser cualquier valor (placeholder),
    ya que su peso es 0 y no contribuye a la suma ponderada.
    """
    if len(niv_17) != NIV_LENGTH:
        raise CheckDigitError(f"El NIV debe tener {NIV_LENGTH} caracteres, recibido: {len(niv_17)}.")

    total = 0
    for index, char in enumerate(niv_17):
        weight = WEIGHTS[index]
        if weight == 0:
            continue
        total += _char_value(char) * weight

    remainder = total % 11
    return "X" if remainder == 10 else str(remainder)


def verify_check_digit(niv_17: str) -> bool:
    """Verifica que el dígito verificador (posición 9) de un NIV completo sea correcto."""
    if len(niv_17) != NIV_LENGTH:
        return False
    expected = calculate_check_digit(niv_17)
    return niv_17[CHECK_DIGIT_POSITION - 1] == expected
