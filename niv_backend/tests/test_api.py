"""Pruebas de integración de la API REST (FastAPI TestClient)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import app
from app.models import MapeoVDS
from tests.conftest import MAPEO_SEED

_PAYLOAD_BASE = {
    "tipo_remolque": "A",
    "num_ejes": 2,
    "capacidad": "B",
    "tipo_frenos": "1",
    "version": "1",
    "año_modelo": 2026,
    "linea_produccion": 1,
}


@pytest.fixture()
def client():
    """Cliente de pruebas con base de datos SQLite en memoria y configuración fija."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    seed_session = session_local()
    for posicion, codigo, descripcion, categoria in MAPEO_SEED:
        seed_session.add(MapeoVDS(posicion=posicion, codigo=codigo, descripcion=descripcion, categoria=categoria))
    seed_session.commit()
    seed_session.close()

    def override_get_db():
        session = session_local()
        try:
            yield session
        finally:
            session.close()

    def override_get_settings() -> Settings:
        return Settings(wmi="3M1", planta_default="A", anio_inicio=2026, database_url="sqlite:///:memory:")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_generate_niv_endpoint(client: TestClient) -> None:
    response = client.post("/api/v1/niv/generate", json=_PAYLOAD_BASE)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["niv"]) == 17
    assert body["data"]["desglose"]["wmi"] == "3M1"
    assert body["data"]["detalles"]["año_modelo"] == 2026


def test_generate_niv_invalid_code_returns_400(client: TestClient) -> None:
    payload = {**_PAYLOAD_BASE, "tipo_remolque": "Z"}
    response = client.post("/api/v1/niv/generate", json=payload)
    assert response.status_code == 400
    assert response.json()["success"] is False


def test_get_niv_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/niv/3M1A2B111TA199999")
    assert response.status_code == 404


def test_search_niv_endpoint(client: TestClient) -> None:
    client.post("/api/v1/niv/generate", json=_PAYLOAD_BASE)
    response = client.get("/api/v1/niv/search", params={"año_modelo": 2026, "limit": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total"] >= 1
    assert body["data"]["items"][0]["año_modelo"] == 2026


def test_export_excel_endpoint(client: TestClient) -> None:
    client.post("/api/v1/niv/generate", json=_PAYLOAD_BASE)
    response = client.post("/api/v1/export/excel", json={"filters": {"año_modelo": 2026}})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats")


def test_export_dxf_endpoint(client: TestClient) -> None:
    generate_response = client.post("/api/v1/niv/generate", json=_PAYLOAD_BASE)
    niv = generate_response.json()["data"]["niv"]
    response = client.post("/api/v1/export/dxf", json={"nivs": [niv]})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/dxf"
