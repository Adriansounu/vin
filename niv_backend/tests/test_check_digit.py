"""Pruebas del algoritmo de dígito verificador (NOM-001-SSP-2008 / ISO 3779)."""
from __future__ import annotations

import pytest

from app.core.check_digit import CheckDigitError, calculate_check_digit, verify_check_digit


def test_calculate_check_digit_known_vector() -> None:
    """Vector calculado a mano: WMI=3M1, VDS=A2B11, VIS=TA100001 -> dígito verificador '1'."""
    niv_sin_check = "3M1" + "A2B11" + "0" + "TA100001"
    assert calculate_check_digit(niv_sin_check) == "1"


def test_verify_check_digit_valid() -> None:
    niv_completo = "3M1" + "A2B11" + "1" + "TA100001"
    assert verify_check_digit(niv_completo) is True


def test_verify_check_digit_invalid() -> None:
    niv_completo = "3M1" + "A2B11" + "2" + "TA100001"
    assert verify_check_digit(niv_completo) is False


def test_verify_check_digit_wrong_length() -> None:
    assert verify_check_digit("3M1A2B111TA10000") is False


def test_check_digit_rejects_prohibited_chars() -> None:
    niv_con_prohibido = "3M1" + "AIB11" + "0" + "TA100001"
    with pytest.raises(CheckDigitError):
        calculate_check_digit(niv_con_prohibido)


def test_check_digit_x_when_remainder_is_ten() -> None:
    """Vector construido para producir residuo 10 (suma ponderada = 791 -> dígito 'X')."""
    niv_sin_check = "9" * 8 + "0" + "9" * 7 + "4"
    assert calculate_check_digit(niv_sin_check) == "X"
