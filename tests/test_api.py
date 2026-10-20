"""Tests de la API.

* Tests unitarios: validacion del contrato, health, autenticacion y prediccion.
  No requieren red.
* Tests de integracion (`-m integration`): login real contra Supabase Auth y
  CRUD de evaluaciones. Se activan si hay credenciales en el `.env`.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in os.sys.path:  # type: ignore[attr-defined]
    import sys

    sys.path.insert(0, str(ROOT))

from api.main import app  # noqa: E402

ESTUDIANTE = {
    "dni": "70123456",
    "nombre": "María Quispe",
    "edad": 19,
    "genero": "Femenino",
    "area_estudios": "Ciencias de la Salud",
    "becario": "No",
    "deudor": "No",
    "matricula_al_dia": "Sí",
    "desplazado": "No",
    "cu1_matriculadas": 6,
    "cu1_aprobadas": 1,
    "cu1_nota": 6.0,
    "cu2_matriculadas": 6,
    "cu2_aprobadas": 0,
    "cu2_nota": 5.0,
}


@pytest.fixture(scope="module")
def cliente() -> TestClient:
    return TestClient(app)


# --------------------------------------------------------------------------- #
# Sistema
# --------------------------------------------------------------------------- #
def test_health(cliente: TestClient):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["modelo"]["variables"] == 36


def test_indice_documenta_los_endpoints(cliente: TestClient):
    cuerpo = cliente.get("/api/v1").json()
    assert "predecir" in cuerpo["endpoints"]


def test_openapi_se_genera(cliente: TestClient):
    respuesta = cliente.get("/openapi.json")
    assert respuesta.status_code == 200
    assert "/api/v1/predict" in respuesta.json()["paths"]


# --------------------------------------------------------------------------- #
# Prediccion
# --------------------------------------------------------------------------- #
def test_predict_devuelve_probabilidad_y_nivel(cliente: TestClient):
    respuesta = cliente.post("/api/v1/predict", json=ESTUDIANTE)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert 0.0 <= cuerpo["probabilidad"] <= 1.0
    assert cuerpo["nivel"] in {"BAJO", "MEDIO", "ALTO"}
    assert cuerpo["modelo_version"]
    assert cuerpo["tiempo_ms"] >= 0


def test_predict_rechaza_aprobadas_superiores_a_matriculadas(cliente: TestClient):
    datos = {**ESTUDIANTE, "cu1_aprobadas": 9}
    respuesta = cliente.post("/api/v1/predict", json=datos)
    assert respuesta.status_code == 422


def test_predict_rechaza_nota_fuera_de_rango(cliente: TestClient):
    datos = {**ESTUDIANTE, "cu1_nota": 25}
    assert cliente.post("/api/v1/predict", json=datos).status_code == 422


def test_predict_rechaza_edad_invalida(cliente: TestClient):
    datos = {**ESTUDIANTE, "edad": 12}
    assert cliente.post("/api/v1/predict", json=datos).status_code == 422


def test_predict_rechaza_area_desconocida(cliente: TestClient):
    datos = {**ESTUDIANTE, "area_estudios": "Filosofia"}
    assert cliente.post("/api/v1/predict", json=datos).status_code == 422


def test_predict_rechaza_campos_faltantes(cliente: TestClient):
    datos = {k: v for k, v in ESTUDIANTE.items() if k != "edad"}
    assert cliente.post("/api/v1/predict", json=datos).status_code == 422


def test_prediccion_cambia_con_el_rendimiento(cliente: TestClient):
    malo = cliente.post("/api/v1/predict", json=ESTUDIANTE).json()["probabilidad"]
    bueno = {
        **ESTUDIANTE,
        "cu1_aprobadas": 6,
        "cu1_nota": 18.0,
        "cu2_aprobadas": 6,
        "cu2_nota": 18.0,
    }
    p_bueno = cliente.post("/api/v1/predict", json=bueno).json()["probabilidad"]
    assert p_bueno < malo


# --------------------------------------------------------------------------- #
# Autenticacion
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "ruta",
    [
        "/api/v1/evaluaciones",
        "/api/v1/evaluaciones/1",
        "/api/v1/dashboard/resumen",
        "/api/v1/auth/me",
    ],
)
def test_rutas_protegidas_exigen_token(cliente: TestClient, ruta: str):
    assert cliente.get(ruta).status_code == 401


def test_token_invalido_es_rechazado(cliente: TestClient):
    respuesta = cliente.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer no-es-un-jwt"}
    )
    assert respuesta.status_code == 401


# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #
def test_cors_permite_los_origenes_configurados():
    """La variable CORS_ORIGINS llega como texto separado por comas.

    Sin `NoDecode`, pydantic-settings intenta parsearla como JSON y la API
    no arranca: este test blinda ese caso.
    """
    from api.core.config import Settings

    config = Settings(cors_origins="https://a.vercel.app, https://b.vercel.app/")
    assert config.cors_origins == ["https://a.vercel.app", "https://b.vercel.app"]


def test_cors_responde_al_origin_permitido_y_lo_bloquea_a_otros(monkeypatch):
    import api.core.config as modulo_config
    from fastapi.testclient import TestClient

    from api.main import crear_app

    monkeypatch.setenv("CORS_ORIGINS", "https://capstone-dropout.vercel.app")
    monkeypatch.setenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app")
    modulo_config.obtener_config.cache_clear()
    try:
        cliente = TestClient(crear_app())

        permitido = cliente.get(
            "/api/v1", headers={"Origin": "https://capstone-dropout.vercel.app"}
        )
        assert permitido.headers.get("access-control-allow-origin") == (
            "https://capstone-dropout.vercel.app"
        )

        # Previsualizacion de Vercel: permitida por la expresion regular.
        previsualizacion = cliente.get(
            "/api/v1", headers={"Origin": "https://capstone-dropout-abc123.vercel.app"}
        )
        assert previsualizacion.headers.get("access-control-allow-origin") == (
            "https://capstone-dropout-abc123.vercel.app"
        )

        prohibido = cliente.get("/api/v1", headers={"Origin": "https://sitio-malicioso.com"})
        assert "access-control-allow-origin" not in prohibido.headers
    finally:
        modulo_config.obtener_config.cache_clear()


# --------------------------------------------------------------------------- #
# Integracion (requiere Supabase configurado)
# --------------------------------------------------------------------------- #
def _credenciales() -> tuple[str, str] | None:
    from api.core.config import obtener_config

    config = obtener_config()
    email = os.environ.get("TEST_USER_EMAIL") or config.test_user_email
    password = os.environ.get("TEST_USER_PASSWORD") or config.test_user_password
    if not email or not password:
        return None
    return email, password


@pytest.mark.integration
def test_login_y_crud_completo_evaluaciones():
    credenciales = _credenciales()
    if credenciales is None:
        pytest.skip("Sin credenciales de prueba en el .env")
    email, password = credenciales

    with TestClient(app) as cliente:
        login = cliente.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        cabeceras = {"Authorization": f"Bearer {token}"}

        perfil = cliente.get("/api/v1/auth/me", headers=cabeceras)
        assert perfil.status_code == 200
        assert perfil.json()["email"] == email

        creado = cliente.post("/api/v1/evaluaciones", json=ESTUDIANTE, headers=cabeceras)
        assert creado.status_code == 201, creado.text
        evaluacion = creado.json()
        assert evaluacion["nivel"] in {"BAJO", "MEDIO", "ALTO"}
        assert evaluacion["id"]

        listado = cliente.get("/api/v1/evaluaciones", headers=cabeceras)
        assert listado.status_code == 200
        assert listado.json()["total"] >= 1

        detalle = cliente.get(f"/api/v1/evaluaciones/{evaluacion['id']}", headers=cabeceras)
        assert detalle.status_code == 200
        assert detalle.json()["dni"] == ESTUDIANTE["dni"]

        panel = cliente.get("/api/v1/dashboard/resumen", headers=cabeceras)
        assert panel.status_code == 200
        assert panel.json()["estudiantes_evaluados"] >= 1

        corregida = cliente.patch(
            f"/api/v1/evaluaciones/{evaluacion['id']}",
            json={"nombre": "Nombre corregido"},
            headers=cabeceras,
        )
        assert corregida.status_code == 200
        assert corregida.json()["nombre"] == "Nombre corregido"

        borrada = cliente.delete(f"/api/v1/evaluaciones/{evaluacion['id']}", headers=cabeceras)
        assert borrada.status_code == 200
