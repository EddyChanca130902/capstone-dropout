"""Caso de demostracion para la sustentacion: 5 estudiantes con historico.

Crea un conjunto de casos identificados con los prefijos `DEMO-` que permiten
enseñar los cuatro KPI de impacto con datos reales:

* Las predicciones y las variables en alerta las calcula el **modelo real**
  (`src.predictor`), no se inventan.
* Solo se retrodatizan las fechas, para simular un historial de 30-40 dias.

Casos:
  DEMO-0001  ALTO -> MEDIO  con derivacion e intervencion   (mejora)
  DEMO-0002  ALTO -> MEDIO  con derivacion e intervencion   (mejora)
  DEMO-0003  ALTO -> ALTO   con derivacion e intervencion   (no mejora)
  DEMO-0004  ALTO           sin derivacion                   (baja la cobertura)
  DEMO-0005  ALTO           sin derivacion                   (baja la cobertura)

Uso:
    python scripts/caso_demo.py            # crea el caso
    python scripts/caso_demo.py --limpiar   # lo elimina
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.core.config import obtener_config  # noqa: E402
from src.predictor import explicar_riesgo, predecir_riesgo_abandono  # noqa: E402

PREFIX = "DEMO-"
UTC = timezone.utc

CASOS = [
    {
        "dni": "DEMO-0001",
        "nombre": "Ana Ramírez (caso demo)",
        "area": "Ciencias de la Salud",
        "evaluaciones": [
            {"hace": 40, "datos": {"edad": 19, "genero": "Femenino", "becario": "No", "deudor": "Sí",
                                    "matricula_al_dia": "No", "desplazado": "No",
                                    "cu1_matriculadas": 6, "cu1_aprobadas": 1, "cu1_nota": 6.0,
                                    "cu2_matriculadas": 6, "cu2_aprobadas": 0, "cu2_nota": 5.0}},
            {"hace": 2, "datos": {"edad": 19, "genero": "Femenino", "becario": "No", "deudor": "No",
                                 "matricula_al_dia": "Sí", "desplazado": "No",
                                 "cu1_matriculadas": 6, "cu1_aprobadas": 4, "cu1_nota": 12.5,
                                 "cu2_matriculadas": 6, "cu2_aprobadas": 3, "cu2_nota": 11.0}},
        ],
        "intervencion": {"derivacion": 39, "inicio": 36, "canal": "TUTORIA", "estado": "CERRADA",
                          "accion": "Tutoria de refuerzo en segundo semestre y gestion de deuda educativa",
                          "resultado": "Regulariza la matricula y mejora el rendimiento en 3 asignaturas."},
    },
    {
        "dni": "DEMO-0002",
        "nombre": "Luis Cabrera (caso demo)",
        "area": "Ingeniería y Tecnología",
        "evaluaciones": [
            {"hace": 35, "datos": {"edad": 21, "genero": "Masculino", "becario": "No", "deudor": "No",
                                    "matricula_al_dia": "No", "desplazado": "No",
                                    "cu1_matriculadas": 7, "cu1_aprobadas": 2, "cu1_nota": 8.0,
                                    "cu2_matriculadas": 7, "cu2_aprobadas": 1, "cu2_nota": 7.0}},
            {"hace": 3, "datos": {"edad": 21, "genero": "Masculino", "becario": "No", "deudor": "No",
                                 "matricula_al_dia": "Sí", "desplazado": "No",
                                 "cu1_matriculadas": 7, "cu1_aprobadas": 5, "cu1_nota": 13.0,
                                 "cu2_matriculadas": 7, "cu2_aprobadas": 4, "cu2_nota": 12.0}},
        ],
        "intervencion": {"derivacion": 34, "inicio": 28, "canal": "ORIENTACION", "estado": "CERRADA",
                          "accion": "Plan de recuperacion de asignaturas y acompanamiento vocacional",
                          "resultado": "Aprueba 3 asignaturas del ciclo anterior."},
    },
    {
        "dni": "DEMO-0003",
        "nombre": "Sofia Reyes (caso demo)",
        "area": "Administración y Negocios",
        "evaluaciones": [
            {"hace": 30, "datos": {"edad": 20, "genero": "Femenino", "becario": "No", "deudor": "Sí",
                                    "matricula_al_dia": "No", "desplazado": "No",
                                    "cu1_matriculadas": 6, "cu1_aprobadas": 0, "cu1_nota": 5.0,
                                    "cu2_matriculadas": 6, "cu2_aprobadas": 0, "cu2_nota": 4.5}},
            {"hace": 1, "datos": {"edad": 20, "genero": "Femenino", "becario": "No", "deudor": "Sí",
                                 "matricula_al_dia": "No", "desplazado": "No",
                                 "cu1_matriculadas": 6, "cu1_aprobadas": 1, "cu1_nota": 6.5,
                                 "cu2_matriculadas": 6, "cu2_aprobadas": 1, "cu2_nota": 6.0}},
        ],
        "intervencion": {"derivacion": 29, "inicio": 25, "canal": "TUTORIA", "estado": "EN_PROCESO",
                          "accion": "Tutoria de refuerzo semanal y derivacion a bienestar estudiantil",
                          "resultado": None},
    },
    {
        "dni": "DEMO-0004",
        "nombre": "Diego Flores (caso demo)",
        "area": "Ciencias Sociales y Humanidades",
        "evaluaciones": [
            {"hace": 20, "datos": {"edad": 22, "genero": "Masculino", "becario": "No", "deudor": "Sí",
                                    "matricula_al_dia": "No", "desplazado": "No",
                                    "cu1_matriculadas": 5, "cu1_aprobadas": 1, "cu1_nota": 7.0,
                                    "cu2_matriculadas": 5, "cu2_aprobadas": 0, "cu2_nota": 6.0}},
        ],
        "intervencion": None,
    },
    {
        "dni": "DEMO-0005",
        "nombre": "Lucia Torres (caso demo)",
        "area": "Arte y Diseño",
        "evaluaciones": [
            {"hace": 15, "datos": {"edad": 18, "genero": "Femenino", "becario": "Sí", "deudor": "No",
                                    "matricula_al_dia": "No", "desplazado": "Sí",
                                    "cu1_matriculadas": 6, "cu1_aprobadas": 2, "cu1_nota": 9.0,
                                    "cu2_matriculadas": 6, "cu2_aprobadas": 1, "cu2_nota": 8.0}},
        ],
        "intervencion": None,
    },
]


def cliente_admin(config):
    from api.services.supabase import cliente_admin as _cliente

    return _cliente(config)


def _solo_columnas(config, tabla: str, fila: dict) -> dict:
    """Descarta las claves que la tabla todavia no soporta."""
    from api.services.supabase import columnas_tabla

    columnas = columnas_tabla(config, tabla)
    if not columnas:
        return fila
    return {k: v for k, v in fila.items() if k in columnas}


def main() -> int:
    parser = argparse.ArgumentParser(description="Caso de demostracion de los KPI")
    parser.add_argument("--limpiar", action="store_true", help="Elimina los casos de demostracion")
    args = parser.parse_args()

    config = obtener_config()
    cliente = cliente_admin(config)

    # Usuario propietario de los registros (el usuario de prueba).
    from api.services.supabase import columnas_tabla

    # `columnas_tabla` devuelve las columnas de la tabla: si esta vacia, la tabla
    # todavia no existe (falta aplicar la migracion 0002).
    if not columnas_tabla(config, "intervenciones"):
        print("[X] Falta la tabla `intervenciones`.")
        print("    Aplica supabase/migrations/0002_intervenciones.sql en el SQL Editor de Supabase.")
        return 1

    usuario_id = None
    try:
        with httpx.Client(timeout=20) as http:
            r = http.post(
                f"{config.supabase_base_url}/auth/v1/token?grant_type=password",
                json={"email": config.test_user_email, "password": config.test_user_password},
                headers={"apikey": config.clave_anon},
            )
            if r.status_code == 200:
                token = r.json()["access_token"]
                with httpx.Client(timeout=20) as http:
                    p = http.get(
                        f"{config.supabase_base_url}/auth/v1/user",
                        headers={"apikey": config.clave_anon, "Authorization": f"Bearer {token}"},
                    )
                    if p.status_code == 200:
                        usuario_id = p.json().get("id")
    except Exception as exc:  # pragma: no cover
        print(f"[!] No se pudo resolver el usuario: {exc}")

    if args.limpiar:
        cliente.table("intervenciones").delete().like("dni", f"{PREFIX}%").execute()
        cliente.table("evaluaciones").delete().like("dni", f"{PREFIX}%").execute()
        print("[OK] Casos de demostracion eliminados.")
        return 0

    ahora = datetime.now(UTC)
    resumen = []

    for caso in CASOS:
        # Limpieza previa del caso (idempotencia).
        cliente.table("intervenciones").delete().eq("dni", caso["dni"]).execute()
        cliente.table("evaluaciones").delete().eq("dni", caso["dni"]).execute()

        ids_evaluaciones = []
        for evaluacion in caso["evaluaciones"]:
            probabilidad, nivel = predecir_riesgo_abandono(evaluacion["datos"])
            explicacion = explicar_riesgo(evaluacion["datos"])
            creado = ahora - timedelta(days=evaluacion["hace"])
            fila = {
                "dni": caso["dni"],
                "nombre": caso["nombre"],
                "area_estudios": caso["area"],
                "probabilidad": probabilidad,
                "nivel": nivel,
                "modelo_version": "xgboost-portugal-2026-10",
                "entradas": evaluacion["datos"],
                "factores_clave": explicacion.get("factores", []),
                "variables_en_alerta": explicacion.get("variables_en_alerta", []),
                "created_at": creado.isoformat(),
                "creado_en": creado.isoformat(),
                "actualizado_en": creado.isoformat(),
            }
            if usuario_id:
                fila["user_id"] = usuario_id
            insertada = cliente.table("evaluaciones").insert(_solo_columnas(config, "evaluaciones", fila)).execute()
            if insertada.data:
                ids_evaluaciones.append(insertada.data[0]["id"])

        if caso.get("intervencion"):
            intervencion = caso["intervencion"]
            variables = []
            if ids_evaluaciones:
                # Las variables en alerta se derivan de las contribuciones
                # positivas del modelo (`factores_clave`).
                primera = (
                    cliente.table("evaluaciones")
                    .select("factores_clave")
                    .eq("id", ids_evaluaciones[0])
                    .execute()
                )
                if primera.data:
                    factores = primera.data[0].get("factores_clave") or []
                    variables = [
                        f.get("variable")
                        for f in factores
                        if isinstance(f, dict) and float(f.get("contribucion") or 0) > 0
                    ]
            fila = {
                "dni": caso["dni"],
                "nombre": caso["nombre"],
                "evaluacion_id": ids_evaluaciones[0] if ids_evaluaciones else None,
                "fecha_deteccion": (ahora - timedelta(days=intervencion["derivacion"] + 1)).isoformat(),
                "fecha_derivacion": (ahora - timedelta(days=intervencion["derivacion"])).isoformat(),
                "fecha_inicio": (ahora - timedelta(days=intervencion["inicio"])).isoformat(),
                "responsable": "Orientador de demostración",
                "canal": intervencion["canal"],
                "accion": intervencion["accion"],
                "estado": intervencion["estado"],
                "variables_en_alerta": variables,
                "resultado": intervencion.get("resultado"),
                "creado_en": (ahora - timedelta(days=intervencion["derivacion"])).isoformat(),
            }
            if usuario_id:
                fila["user_id"] = usuario_id
            cliente.table("intervenciones").insert(_solo_columnas(config, "intervenciones", fila)).execute()

        niveles = [predecir_riesgo_abandono(e["datos"])[1] for e in caso["evaluaciones"]]
        resumen.append(
            {
                "dni": caso["dni"],
                "evaluaciones": len(caso["evaluaciones"]),
                "niveles": " -> ".join(niveles),
                "intervencion": "si" if caso.get("intervencion") else "no",
            }
        )

    print("[OK] Caso de demostracion creado:\n")
    for fila in resumen:
        print(f"    {fila['dni']}  {fila['niveles']:<18} intervencion: {fila['intervencion']}")

    # Resultado de los KPI.
    from api.services.kpis import calcular_kpis

    informe = calcular_kpis(config, access_token=None, user_id=usuario_id)
    print("\n[KPI]")
    for clave in (
        "kpi_cobertura_intervencion",
        "kpi_reduccion_riesgo",
        "kpi_resolucion_variables",
        "kpi_tiempo_respuesta",
    ):
        kpi = informe[clave]
        valor = kpi["valor"] if kpi["valor"] is not None else "-"
        print(
            f"    {clave:30s} {valor:>7} {kpi['unidad']:<4} "
            f"({kpi['numerador']:.0f}/{kpi['denominador']:.0f})  {kpi['formula'][:70]}"
        )
    print("\n    Limpiar con: python scripts/caso_demo.py --limpiar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
