"""Repositorio de evaluaciones sobre Supabase.

La tabla puede funcionar con dos esquemas:

* **Completo** (tras aplicar `supabase/migrations/0001_init.sql`): incluye
  `user_id`, `modelo_version`, `entradas`, `creado_en` y `actualizado_en`.
* **Minimo** (el que existia antes): `id, created_at, dni, nombre,
  area_estudios, probabilidad, nivel`.

El codigo detecta las columnas reales y se adapta, de modo que la API funciona
antes y despues de aplicar la migracion.
"""

from __future__ import annotations

from typing import Any

from api.core.config import Settings
from api.services.supabase import cliente_admin, cliente_usuario, columnas_tabla, filtrar_columnas

TABLA = "evaluaciones"


def _preparar_fila(config: Settings, fila: dict[str, Any]) -> dict[str, Any]:
    columnas = columnas_tabla(config, TABLA)
    return filtrar_columnas(fila, columnas)


def _aplicar_filtro_usuario(consulta, config: Settings, user_id: str | None):
    """Aplica el filtro por usuario cuando la tabla tiene `user_id` y no hay RLS."""
    if not user_id:
        return consulta
    if "user_id" in columnas_tabla(config, TABLA):
        return consulta.eq("user_id", user_id)
    return consulta


def listar(
    config: Settings,
    *,
    access_token: str | None = None,
    user_id: str | None = None,
    limite: int = 50,
    desplazamiento: int = 0,
    area: str | None = None,
    nivel: str | None = None,
    orden: str = "desc",
) -> list[dict[str, Any]]:
    cliente = cliente_usuario(config, access_token)
    consulta = cliente.table(TABLA).select("*")
    consulta = _aplicar_filtro_usuario(consulta, config, user_id)
    if area:
        consulta = consulta.eq("area_estudios", area)
    if nivel:
        consulta = consulta.eq("nivel", nivel)
    columna_orden = "creado_en" if "creado_en" in columnas_tabla(config, TABLA) else "created_at"
    consulta = consulta.order(columna_orden, desc=(orden == "desc"))
    consulta = consulta.range(desplazamiento, desplazamiento + max(0, limite) - 1)
    respuesta = consulta.execute()
    return list(respuesta.data or [])


def obtener(
    config: Settings,
    evaluacion_id: int,
    *,
    access_token: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any] | None:
    cliente = cliente_usuario(config, access_token)
    consulta = cliente.table(TABLA).select("*").eq("id", evaluacion_id)
    consulta = _aplicar_filtro_usuario(consulta, config, user_id)
    respuesta = consulta.limit(1).execute()
    datos = list(respuesta.data or [])
    return datos[0] if datos else None


def crear(
    config: Settings,
    fila: dict[str, Any],
    *,
    access_token: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    cliente = cliente_usuario(config, access_token)
    datos = _preparar_fila(config, fila)
    if user_id and "user_id" in columnas_tabla(config, TABLA) and "user_id" not in datos:
        datos["user_id"] = user_id
    respuesta = cliente.table(TABLA).insert(datos).execute()
    insertados = list(respuesta.data or [])
    return insertados[0] if insertados else datos


def actualizar(
    config: Settings,
    evaluacion_id: int,
    cambios: dict[str, Any],
    *,
    access_token: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any] | None:
    cliente = cliente_usuario(config, access_token)
    consulta = cliente.table(TABLA).update(cambios).eq("id", evaluacion_id)
    consulta = _aplicar_filtro_usuario(consulta, config, user_id)
    respuesta = consulta.execute()
    datos = list(respuesta.data or [])
    return datos[0] if datos else None


def eliminar(
    config: Settings,
    evaluacion_id: int,
    *,
    access_token: str | None = None,
    user_id: str | None = None,
) -> bool:
    cliente = cliente_usuario(config, access_token)
    consulta = cliente.table(TABLA).delete().eq("id", evaluacion_id)
    consulta = _aplicar_filtro_usuario(consulta, config, user_id)
    respuesta = consulta.execute()
    return bool(respuesta.data)


def resumen(
    config: Settings,
    *,
    access_token: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Calcula los indicadores del panel a partir de las filas del usuario."""
    filas = listar(config, access_token=access_token, user_id=user_id, limite=1000, orden="desc")

    # Identidad: un mismo DNI puede tener varias evaluaciones; el estado actual
    # es el de la ultima.
    por_dni: dict[str, dict[str, Any]] = {}
    sueltos: list[dict[str, Any]] = []
    for fila in filas:
        dni = str(fila.get("dni") or "").strip()
        if dni:
            clave = f"dni:{dni}"
            actual = por_dni.get(clave)
            if actual is None or _fecha(fila) >= _fecha(actual):
                por_dni[clave] = fila
        else:
            sueltos.append(fila)

    actuales = list(por_dni.values()) + sueltos
    niveles = [str(f.get("nivel") or "").strip().upper() for f in actuales]
    conteo = {"ALTO": 0, "MEDIO": 0, "BAJO": 0}
    for nivel in niveles:
        if nivel in conteo:
            conteo[nivel] += 1

    probabilidades = [float(f["probabilidad"]) for f in actuales if f.get("probabilidad") is not None]
    por_area: dict[str, int] = {}
    for fila in actuales:
        if str(fila.get("nivel") or "").strip().upper() == "ALTO":
            area = str(fila.get("area_estudios") or "Sin área")
            por_area[area] = por_area.get(area, 0) + 1

    return {
        "estudiantes_evaluados": len(actuales),
        "evaluaciones_realizadas": len(filas),
        "en_riesgo_alto": conteo["ALTO"],
        "probabilidad_promedio": (sum(probabilidades) / len(probabilidades)) if probabilidades else None,
        "por_nivel": conteo,
        "por_area": [{"area": a, "total": n} for a, n in sorted(por_area.items(), key=lambda x: -x[1])],
        "recientes": filas[:7],
    }


def _fecha(fila: dict[str, Any]) -> str:
    return str(fila.get("creado_en") or fila.get("created_at") or "")
