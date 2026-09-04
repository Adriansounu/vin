"""Pruebas del generador de NIV (lógica de negocio y persistencia)."""
from __future__ import annotations

import pytest

from app.config import Settings
from app.core.check_digit import verify_check_digit
from app.core.niv_generator import NIVGenerator, NIVGeneratorError


def _generate(db_session, test_settings: Settings, **overrides):
    payload = {
        "tipo_remolque": "A",
        "num_ejes": 2,
        "capacidad": "B",
        "tipo_frenos": "1",
        "version": "1",
        "anio_modelo": 2026,
        "linea_produccion": 1,
    }
    payload.update(overrides)
    generator = NIVGenerator(db=db_session, settings=test_settings)
    return generator.generate(**payload)


def test_generate_niv_structure(db_session, test_settings: Settings) -> None:
    registro = _generate(db_session, test_settings)
    assert len(registro.niv) == 17
    assert registro.niv.startswith("3M1")
    assert registro.numero_serie == 1
    assert registro.codigo_anio == "T"  # 2026 -> 'T' según ciclo de 30 años
    assert verify_check_digit(registro.niv) is True


def test_generate_niv_increments_serie_per_linea_anio(db_session, test_settings: Settings) -> None:
    primero = _generate(db_session, test_settings)
    segundo = _generate(db_session, test_settings)
    assert primero.numero_serie == 1
    assert segundo.numero_serie == 2
    assert segundo.niv != primero.niv


def test_generate_niv_serie_independiente_por_linea(db_session, test_settings: Settings) -> None:
    linea1 = _generate(db_session, test_settings, linea_produccion=1)
    linea2 = _generate(db_session, test_settings, linea_produccion=2)
    assert linea1.numero_serie == 1
    assert linea2.numero_serie == 1


def test_generate_niv_codigo_invalido(db_session, test_settings: Settings) -> None:
    with pytest.raises(NIVGeneratorError):
        _generate(db_session, test_settings, tipo_remolque="Z")


def test_generate_niv_ejes_fuera_de_rango(db_session, test_settings: Settings) -> None:
    with pytest.raises(NIVGeneratorError):
        _generate(db_session, test_settings, num_ejes=10)
