"""Tests de los candidatos a derivacion (la derivacion nace de una evaluacion)."""

from __future__ import annotations

from typing import Any

from api.services import evaluaciones as repo


def evaluacion(dni: str, nivel: str, probabilidad: float, creado: str, id_: int) -> dict[str, Any]:
    return {
        "id": id_,
        "dni": dni,
        "nombre": f"Estudiante {dni}",
        "nivel": nivel,
        "probabilidad": probabilidad,
        "creado_en": creado,
        "area_estudios": "Ingeniería y Tecnología",
        "variables_en_alerta": ["Tuition fees up to date"],
        "factores_clave": [
            {"variable": "Tuition fees up to date", "contribucion": 0.4, "direccion": "aumenta_riesgo"},
            {"variable": "Curricular units 1st sem (approved)", "contribucion": 0.3},
            {"variable": "Debtor", "contribucion": 0.2},
            {"variable": "Age at enrollment", "contribucion": 0.1},
        ],
    }


class _Respuesta:
    def __init__(self, datos: list[dict[str, Any]]) -> None:
        self.data = datos


class _Consulta:
    def __init__(self, datos: list[dict[str, Any]]) -> None:
        self._datos = datos

    def select(self, *_args: Any, **_kwargs: Any) -> "_Consulta":
        return self

    def execute(self) -> _Respuesta:
        return _Respuesta(self._datos)


class _Cliente:
    def __init__(self, datos: list[dict[str, Any]]) -> None:
        self._datos = datos

    def table(self, _nombre: str) -> _Consulta:
        return _Consulta(self._datos)


def test_ultimas_por_dni_se_queda_con_la_mas_reciente():
    filas = [
        evaluacion("111", "ALTO", 0.9, "2026-10-01T10:00:00+00:00", 1),
        evaluacion("111", "MEDIO", 0.5, "2026-10-10T10:00:00+00:00", 2),
        evaluacion("222", "BAJO", 0.1, "2026-10-02T10:00:00+00:00", 3),
    ]
    ultimas = repo.ultimas_por_dni(filas)
    por_dni = {f["dni"]: f for f in ultimas}
    assert len(ultimas) == 2
    assert por_dni["111"]["id"] == 2
    assert por_dni["111"]["nivel"] == "MEDIO"


def test_candidatos_excluye_bajo_y_ordena_alto_primero(monkeypatch):
    filas = [
        evaluacion("111", "MEDIO", 0.55, "2026-10-10T10:00:00+00:00", 2),
        evaluacion("222", "ALTO", 0.91, "2026-10-10T10:00:00+00:00", 3),
        evaluacion("333", "BAJO", 0.10, "2026-10-10T10:00:00+00:00", 4),
    ]
    monkeypatch.setattr(repo, "listar", lambda *a, **k: filas)
    monkeypatch.setattr(repo, "columnas_tabla", lambda *a, **k: ["id", "dni", "estado"])
    monkeypatch.setattr(repo, "cliente_usuario", lambda *a, **k: _Cliente([]))

    candidatos = repo.candidatos(None)  # type: ignore[arg-type]
    assert [c["dni"] for c in candidatos] == ["222", "111"]
    assert candidatos[0]["evaluacion_id"] == 3
    assert candidatos[0]["derivado"] is False
    assert len(candidatos[0]["factores_clave"]) == 3  # solo los 3 primeros

    con_bajo = repo.candidatos(None, incluir_bajo=True)  # type: ignore[arg-type]
    assert [c["dni"] for c in con_bajo] == ["222", "111", "333"]


def test_candidatos_marca_derivacion_activa_pero_no_la_cerrada(monkeypatch):
    filas = [
        evaluacion("111", "ALTO", 0.9, "2026-10-10T10:00:00+00:00", 1),
        evaluacion("222", "ALTO", 0.8, "2026-10-10T10:00:00+00:00", 2),
    ]
    intervenciones = [
        {"dni": "111", "estado": "EN_PROCESO", "fecha_derivacion": "2026-10-11T10:00:00+00:00"},
        {"dni": "222", "estado": "CERRADA", "fecha_derivacion": "2026-10-11T10:00:00+00:00"},
    ]
    monkeypatch.setattr(repo, "listar", lambda *a, **k: filas)
    monkeypatch.setattr(repo, "columnas_tabla", lambda *a, **k: ["id", "dni", "estado"])
    monkeypatch.setattr(repo, "cliente_usuario", lambda *a, **k: _Cliente(intervenciones))

    candidatos = {c["dni"]: c for c in repo.candidatos(None)}  # type: ignore[arg-type]
    assert candidatos["111"]["derivado"] is True
    assert candidatos["111"]["intervencion_estado"] == "EN_PROCESO"
    # Una intervencion cerrada no bloquea una derivacion nueva.
    assert candidatos["222"]["derivado"] is False
    assert candidatos["222"]["intervencion_estado"] == "CERRADA"
