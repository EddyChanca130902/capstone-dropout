"""Calculo de los KPI de impacto del acompanamiento.

Los cuatro indicadores se calculan **desde los datos del sistema**, no a mano:

1. Tasa de cobertura de intervencion
   (estudiantes derivados / estudiantes detectados en alto riesgo) x 100
2. Tasa de variacion del nivel de riesgo
   (estudiantes que disminuyeron su nivel de riesgo en una segunda evaluacion /
    estudiantes en riesgo que recibieron acompanamiento) x 100
3. Indice de resolucion de variables modificables
   (variables independientes en alerta mejoradas post-intervencion /
    total de variables en alerta inicial) x 100
4. Tiempo de respuesta para acompanamiento
   sumatoria (fecha de inicio de intervencion - fecha de evaluacion) / total de casos
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from api.core.config import Settings
from api.services import evaluaciones as repo_evaluaciones
from api.services.supabase import cliente_usuario, columnas_tabla

# Orden de los niveles de riesgo: BAJO < MEDIO < ALTO
NIVELES = {"BAJO": 1, "MEDIO": 2, "ALTO": 3}

# Variables que la institucion puede ayudar a cambiar y como se define que
# "mejoran". Se excluyen las no modificables (edad, genero, area, desplazado,
# beca) porque no son objeto de ninguna accion correctiva.
VARIABLES_MODIFICABLES: dict[str, tuple[str, str]] = {
    # variable del modelo -> (campo del formulario, regla de mejora)
    "Curricular units 1st sem (approved)": ("cu1_aprobadas", "mas"),
    "Curricular units 1st sem (grade)": ("cu1_nota", "mas"),
    "Curricular units 2nd sem (approved)": ("cu2_aprobadas", "mas"),
    "Curricular units 2nd sem (grade)": ("cu2_nota", "mas"),
    "Tuition fees up to date": ("matricula_al_dia", "binario_si"),
    "Debtor": ("deudor", "binario_no"),
}


def _mejorado(valor_inicial: Any, valor_final: Any, regla: str) -> bool:
    """Indica si una variable modificables mejoro entre dos evaluaciones."""
    if valor_inicial is None or valor_final is None:
        return False
    if regla == "mas":
        try:
            return float(valor_final) > float(valor_inicial)
        except (TypeError, ValueError):
            return False
    if regla == "binario_si":
        # "matricula al dia": pasar de No a Si es mejorar.
        return str(valor_final).strip() == "Sí" and str(valor_inicial).strip() != "Sí"
    if regla == "binario_no":
        # "deudor": pasar de Si a No es mejorar.
        return str(valor_final).strip() == "No" and str(valor_inicial).strip() != "No"
    return False


def _evaluaciones_por_dni(filas: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    agrupadas: dict[str, list[dict[str, Any]]] = {}
    for fila in filas:
        dni = str(fila.get("dni") or "").strip()
        if not dni:
            continue
        agrupadas.setdefault(dni, []).append(fila)
    for dni in agrupadas:
        agrupadas[dni].sort(key=lambda f: str(f.get("creado_en") or f.get("created_at") or ""))
    return agrupadas


def _a_datetime(valor: Any) -> datetime | None:
    """Acepta datetime o texto ISO (PostgREST devuelve texto)."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except ValueError:
        return None


def _dias(inicio: Any, fin: Any) -> float | None:
    """Dias transcurridos entre dos marcas de tiempo."""
    desde = _a_datetime(inicio)
    hasta = _a_datetime(fin)
    if desde is None or hasta is None:
        return None
    try:
        return (hasta - desde).total_seconds() / 86400
    except TypeError:  # zonas horarias incompatibles
        return None


def calcular_kpis(
    config: Settings,
    *,
    access_token: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Recoge los datos del usuario y calcula los cuatro KPI de impacto."""
    evaluacion_filas = repo_evaluaciones.listar(
        config, access_token=access_token, user_id=user_id, limite=1000, orden="asc"
    )
    intervenciones: list[dict[str, Any]] = []
    if "intervenciones" in columnas_tabla(config, "intervenciones"):
        cliente = cliente_usuario(config, access_token)
        respuesta = cliente.table("intervenciones").select("*").execute()
        intervenciones = list(respuesta.data or [])
    return calcular_kpis_desde_datos(evaluacion_filas, intervenciones)


def calcular_kpis_desde_datos(
    evaluacion_filas: list[dict[str, Any]],
    intervenciones: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calcula los cuatro KPI a partir de filas ya obtenidas (logica pura)."""
    por_dni = _evaluaciones_por_dni(evaluacion_filas)

    derivadas = {
        str(i.get("dni") or "").strip()
        for i in intervenciones
        if str(i.get("dni") or "").strip()
    }

    # --- KPI 1: tasa de cobertura de intervencion ---------------------------
    en_alto_riesgo = {
        dni
        for dni, filas in por_dni.items()
        if str(filas[-1].get("nivel") or "").upper() == "ALTO"
    }
    derivadas_en_alto = derivadas & en_alto_riesgo
    kpi1_num = float(len(derivadas_en_alto))
    kpi1_den = float(len(en_alto_riesgo))

    # --- KPI 2: variacion del nivel de riesgo -------------------------------
    con_intervencion_y_reevaluacion = [dni for dni in derivadas if len(por_dni.get(dni, [])) >= 2]
    redujeron = 0
    diferencias_probabilidad: list[float] = []
    for dni in con_intervencion_y_reevaluacion:
        filas = por_dni[dni]
        inicial, final = filas[0], filas[-1]
        nivel_inicial = NIVELES.get(str(inicial.get("nivel") or "").upper(), 0)
        nivel_final = NIVELES.get(str(final.get("nivel") or "").upper(), 0)
        if nivel_final < nivel_inicial:
            redujeron += 1
        try:
            diferencias_probabilidad.append(
                float(inicial.get("probabilidad") or 0) - float(final.get("probabilidad") or 0)
            )
        except (TypeError, ValueError):
            pass
    kpi2_num = float(redujeron)
    kpi2_den = float(len(con_intervencion_y_reevaluacion))

    # --- KPI 3: indice de resolucion de variables modificables --------------
    variables_alerta_total = 0
    variables_alerta_mejoradas = 0
    detalle_variables: dict[str, dict[str, int]] = {}
    for dni in con_intervencion_y_reevaluacion:
        filas = por_dni[dni]
        inicial, final = filas[0], filas[-1]
        entradas_inicial = inicial.get("entradas") or {}
        entradas_final = final.get("entradas") or {}

        alerta = inicial.get("factores_clave") or []
        nombres_alerta = [a.get("variable") for a in alerta if isinstance(a, dict) and a.get("variable")]
        if not nombres_alerta:
            nombres_alerta = [v for v in (inicial.get("variables_en_alerta") or [])]

        for variable in nombres_alerta:
            if variable not in VARIABLES_MODIFICABLES:
                continue  # variable no modificable: fuera del denominador
            campo, regla = VARIABLES_MODIFICABLES[variable]
            variables_alerta_total += 1
            detalle_variables.setdefault(variable, {"alerta": 0, "mejoradas": 0})
            detalle_variables[variable]["alerta"] += 1
            if _mejorado(entradas_inicial.get(campo), entradas_final.get(campo), regla):
                variables_alerta_mejoradas += 1
                detalle_variables[variable]["mejoradas"] += 1
    kpi3_num = float(variables_alerta_mejoradas)
    kpi3_den = float(variables_alerta_total)

    # --- KPI 4: tiempo de respuesta para acompanamiento ---------------------
    tiempos: list[float] = []
    for intervencion in intervenciones:
        inicio = intervencion.get("fecha_inicio")
        referencia = intervencion.get("fecha_derivacion") or intervencion.get("fecha_deteccion")
        dias = _dias(referencia, inicio)
        if dias is not None:
            tiempos.append(max(dias, 0.0))
    kpi4_den = float(len(tiempos))
    kpi4_num = float(sum(tiempos))

    # --- Resultado ----------------------------------------------------------
    def porcentaje(num: float, den: float) -> float | None:
        return round(100.0 * num / den, 1) if den > 0 else None

    return {
        "generado_en": datetime.now().astimezone(),
        "kpi_cobertura_intervencion": {
            "valor": porcentaje(kpi1_num, kpi1_den),
            "unidad": "%",
            "numerador": kpi1_num,
            "denominador": kpi1_den,
            "formula": "(estudiantes derivados a acompanamiento / estudiantes detectados en alto riesgo) x 100",
            "disponible": kpi1_den > 0,
            "nota": None if kpi1_den > 0 else "Aun no hay estudiantes en riesgo alto registrados.",
        },
        "kpi_reduccion_riesgo": {
            "valor": porcentaje(kpi2_num, kpi2_den),
            "unidad": "%",
            "numerador": kpi2_num,
            "denominador": kpi2_den,
            "formula": "(estudiantes que disminuyeron su nivel de riesgo en una segunda evaluacion / estudiantes en riesgo que recibieron acompanamiento) x 100",
            "disponible": kpi2_den > 0,
            "nota": None if kpi2_den > 0 else "Se necesita al menos un estudiante con intervencion y dos evaluaciones.",
        },
        "kpi_resolucion_variables": {
            "valor": porcentaje(kpi3_num, kpi3_den),
            "unidad": "%",
            "numerador": kpi3_num,
            "denominador": kpi3_den,
            "formula": "(variables independientes modificables mejoradas post-intervencion / total de variables en alerta inicial) x 100",
            "disponible": kpi3_den > 0,
            "nota": None
            if kpi3_den > 0
            else "Se necesita al menos un estudiante con intervencion, dos evaluaciones y variables en alerta.",
        },
        "kpi_tiempo_respuesta": {
            "valor": round(kpi4_num / kpi4_den, 2) if kpi4_den > 0 else None,
            "unidad": "días",
            "numerador": kpi4_num,
            "denominador": kpi4_den,
            "formula": "sumatoria (fecha de inicio de intervencion - fecha de evaluacion) / total de casos en riesgo",
            "disponible": kpi4_den > 0,
            "nota": None if kpi4_den > 0 else "Se necesitan intervenciones con fecha de inicio registrada.",
        },
        "detalle": {
            "estudiantes_con_intervencion": len(derivadas),
            "estudiantes_en_alto_riesgo": len(en_alto_riesgo),
            "estudiantes_reevaluados": len(con_intervencion_y_reevaluacion),
            "disminucion_media_probabilidad": round(
                sum(diferencias_probabilidad) / len(diferencias_probabilidad), 4
            )
            if diferencias_probabilidad
            else None,
            "variables_modificables": detalle_variables,
        },
    }
