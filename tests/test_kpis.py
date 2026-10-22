"""Tests de los KPI de impacto del acompanamiento."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from api.services.kpis import calcular_kpis_desde_datos

FECHA = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)


def evaluacion(
    dni: str,
    nivel: str,
    probabilidad: float,
    entradas: dict,
    variables_en_alerta: list[str] | None = None,
    dias: int = 0,
    factores: list[dict] | None = None,
) -> dict:
    return {
        "id": abs(hash((dni, dias))) % 10000,
        "dni": dni,
        "nombre": f"Estudiante {dni}",
        "nivel": nivel,
        "probabilidad": probabilidad,
        "creado_en": (FECHA + timedelta(days=dias)).isoformat(),
        "entradas": entradas,
        "variables_en_alerta": variables_en_alerta or [],
        "factores_clave": factores
        or [{"variable": v, "contribucion": 0.5} for v in (variables_en_alerta or [])],
    }


def intervencion(dni: str, dias_inicio: int = 2, fecha_inicio: bool = True) -> dict:
    return {
        "id": abs(hash(dni)) % 10000,
        "dni": dni,
        "fecha_derivacion": FECHA.isoformat(),
        "fecha_inicio": (FECHA + timedelta(days=dias_inicio)).isoformat() if fecha_inicio else None,
        "estado": "DERIVADA",
    }


# --------------------------------------------------------------------------- #
def test_sin_datos_los_kpi_no_estan_disponibles():
    informe = calcular_kpis_desde_datos([], [])
    for clave in (
        "kpi_cobertura_intervencion",
        "kpi_reduccion_riesgo",
        "kpi_resolucion_variables",
        "kpi_tiempo_respuesta",
    ):
        assert informe[clave]["disponible"] is False
        assert informe[clave]["valor"] is None
        assert informe[clave]["formula"]


# --------------------------------------------------------------------------- #
def test_kpi1_cobertura_de_intervencion():
    """2 de 3 estudiantes en alto riesgo fueron derivados -> 66,7 %."""
    filas = [
        evaluacion("111", "ALTO", 0.9, {}),
        evaluacion("222", "ALTO", 0.8, {}),
        evaluacion("333", "ALTO", 0.85, {}),
        evaluacion("444", "BAJO", 0.1, {}),
    ]
    informe = calcular_kpis_desde_datos(filas, [intervencion("111"), intervencion("222")])
    kpi = informe["kpi_cobertura_intervencion"]
    assert kpi["numerador"] == 2
    assert kpi["denominador"] == 3
    assert kpi["valor"] == 66.7
    assert kpi["disponible"] is True


def test_kpi1_un_estudiante_que_mejora_sigue_contando_en_el_denominador():
    """La cobertura se mide sobre los detectados alguna vez en ALTO.

    Un estudiante que bajo de ALTO a BAJO tras la intervencion no puede salir
    del denominador: si saliera, la cobertura caeria precisamente porque la
    intervencion funciono.
    """
    filas = [
        evaluacion("111", "ALTO", 0.9, {}, dias=0),
        evaluacion("111", "BAJO", 0.2, {}, dias=30),
        evaluacion("222", "ALTO", 0.9, {}, dias=0),
        evaluacion("222", "MEDIO", 0.5, {}, dias=30),
        evaluacion("333", "ALTO", 0.9, {}, dias=0),
        evaluacion("333", "ALTO", 0.9, {}, dias=30),
    ]
    informe = calcular_kpis_desde_datos(filas, [intervencion("111")])
    kpi = informe["kpi_cobertura_intervencion"]
    assert kpi["denominador"] == 3
    assert kpi["numerador"] == 1
    assert kpi["valor"] == 33.3


# --------------------------------------------------------------------------- #
def test_kpi2_reduccion_del_nivel_de_riesgo():
    """El nivel de riesgo (ordinal) debe bajar entre la primera y la ultima evaluacion."""
    filas = [
        evaluacion("111", "ALTO", 0.9, {}, dias=0),
        evaluacion("111", "MEDIO", 0.5, {}, dias=30),
        evaluacion("222", "ALTO", 0.9, {}, dias=0),
        evaluacion("222", "ALTO", 0.8, {}, dias=30),  # no bajo de nivel
    ]
    informe = calcular_kpis_desde_datos(filas, [intervencion("111"), intervencion("222")])
    kpi = informe["kpi_reduccion_riesgo"]
    assert kpi["numerador"] == 1
    assert kpi["denominador"] == 2
    assert kpi["valor"] == 50.0
    assert informe["detalle"]["disminucion_media_probabilidad"] is not None


# --------------------------------------------------------------------------- #
def test_kpi3_resolucion_de_variables_modificables():
    """Las variables en alerta que mejoran cuentan; las no modificables, no."""
    alerta = ["Curricular units 2nd sem (approved)", "Debtor", "Age at enrollment"]
    filas = [
        evaluacion(
            "111",
            "ALTO",
            0.9,
            {
                "cu2_aprobadas": 0,
                "deudor": "Sí",
                "edad": 19,
                "cu2_nota": 5.0,
            },
            variables_en_alerta=alerta,
            dias=0,
        ),
        evaluacion(
            "111",
            "MEDIO",
            0.4,
            {
                "cu2_aprobadas": 4,
                "deudor": "No",
                "edad": 19,
                "cu2_nota": 14.0,
            },
            variables_en_alerta=alerta,
            dias=30,
        ),
    ]
    informe = calcular_kpis_desde_datos(filas, [intervencion("111")])
    kpi = informe["kpi_resolucion_variables"]
    # Denominador: solo las 2 variables modificables en alerta (no la edad).
    assert kpi["denominador"] == 2
    # Numerador: las dos mejoraron (aprobadas 0 -> 4 y deuda Si -> No).
    assert kpi["numerador"] == 2
    assert kpi["valor"] == 100.0


# --------------------------------------------------------------------------- #
def test_kpi3_no_cuenta_variables_no_mejoradas():
    alerta = ["Curricular units 2nd sem (approved)"]
    filas = [
        evaluacion("111", "ALTO", 0.9, {"cu2_aprobadas": 3}, variables_en_alerta=alerta, dias=0),
        evaluacion("111", "ALTO", 0.85, {"cu2_aprobadas": 1}, variables_en_alerta=alerta, dias=30),
    ]
    informe = calcular_kpis_desde_datos(filas, [intervencion("111")])
    kpi = informe["kpi_resolucion_variables"]
    assert kpi["numerador"] == 0
    assert kpi["valor"] == 0.0


# --------------------------------------------------------------------------- #
def test_kpi4_tiempo_de_respuesta():
    """Promedio de dias entre derivacion e inicio de la intervencion."""
    filas = [evaluacion("111", "ALTO", 0.9, {}), evaluacion("222", "ALTO", 0.8, {})]
    informe = calcular_kpis_desde_datos(
        filas, [intervencion("111", dias_inicio=2), intervencion("222", dias_inicio=4)]
    )
    kpi = informe["kpi_tiempo_respuesta"]
    assert kpi["unidad"] == "días"
    assert kpi["denominador"] == 2
    assert kpi["valor"] == 3.0  # (2 + 4) / 2


def test_kpi4_ignora_intervenciones_sin_fecha_de_inicio():
    filas = [evaluacion("111", "ALTO", 0.9, {})]
    informe = calcular_kpis_desde_datos(filas, [intervencion("111", fecha_inicio=False)])
    kpi = informe["kpi_tiempo_respuesta"]
    assert kpi["disponible"] is False
