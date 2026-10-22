"""Registro de las intervenciones de acompanamiento (origen de los KPI de impacto)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.core.config import Settings, obtener_config
from api.core.security import UsuarioActual, usuario_actual
from api.schemas.intervencion import IntervencionIn, IntervencionOut, IntervencionPatch
from api.services import evaluaciones as repo_evaluaciones
from api.services.supabase import cliente_usuario, columnas_tabla, filtrar_columnas

router = APIRouter(prefix="/api/v1/intervenciones", tags=["intervenciones"])


def _tabla_disponible(config: Settings) -> bool:
    """`columnas_tabla` devuelve las columnas de la tabla: si la lista esta
    vacia, la tabla no existe todavia (falta aplicar la migracion 0002)."""
    return bool(columnas_tabla(config, "intervenciones"))


def _sin_tabla() -> HTTPException:
    return HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "La tabla de intervenciones no existe. Aplica supabase/migrations/0002_intervenciones.sql",
    )


def _serializable(fila: dict[str, Any]) -> dict[str, Any]:
    """PostgREST solo acepta JSON: las fechas viajan como ISO-8601."""
    return {
        clave: (valor.isoformat() if isinstance(valor, datetime) else valor)
        for clave, valor in fila.items()
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=IntervencionOut,
    summary="Registra la derivacion a acompanamiento de un estudiante",
)
def crear_intervencion(
    datos: IntervencionIn,
    config: Settings = Depends(obtener_config),
    usuario: UsuarioActual = Depends(usuario_actual),
) -> dict[str, Any]:
    if not _tabla_disponible(config):
        raise _sin_tabla()
    cliente = cliente_usuario(config, usuario.token)
    fila = {
        "dni": datos.dni,
        "nombre": datos.nombre,
        "evaluacion_id": datos.evaluacion_id,
        "fecha_deteccion": datos.fecha_deteccion,
        "fecha_derivacion": datos.fecha_derivacion,
        "fecha_inicio": datos.fecha_inicio,
        "responsable": datos.responsable or usuario.email,
        "canal": datos.canal,
        "accion": datos.accion,
        "estado": datos.estado,
        "variables_en_alerta": datos.variables_en_alerta,
        "resultado": datos.resultado,
    }

    # La derivacion nace de una evaluacion: si viene informada, se valida que
    # exista, se heredan sus datos y se evita duplicar la misma derivacion.
    if datos.evaluacion_id is not None:
        evaluacion = repo_evaluaciones.obtener(
            config, datos.evaluacion_id, access_token=usuario.token, user_id=usuario.id
        )
        if evaluacion is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "La evaluacion indicada no existe o no pertenece al usuario.",
            )
        fila["dni"] = fila["dni"] or evaluacion.get("dni")
        fila["nombre"] = fila["nombre"] or evaluacion.get("nombre")
        if fila["fecha_deteccion"] is None:
            fila["fecha_deteccion"] = evaluacion.get("creado_en") or evaluacion.get("created_at")
        if not fila["variables_en_alerta"]:
            fila["variables_en_alerta"] = list(evaluacion.get("variables_en_alerta") or [])

        existentes = (
            cliente.table("intervenciones")
            .select("id,estado,evaluacion_id")
            .eq("dni", datos.dni)
            .execute()
        )
        for previa in list(existentes.data or []):
            # Un estudiante no puede estar en dos acompanamientos a la vez.
            # Si el anterior se cerro, se admite una nueva derivacion.
            sigue_activa = str(previa.get("estado") or "").upper() in (
                "DERIVADA",
                "EN_PROCESO",
            )
            if sigue_activa:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"{datos.dni} ya tiene una derivacion activa (id {previa['id']}, "
                    f"estado {previa.get('estado')}). Actualiza su estado en la tabla "
                    "en lugar de crear otra.",
                )

    fila = filtrar_columnas(
        _serializable({k: v for k, v in fila.items() if v is not None}),
        columnas_tabla(config, "intervenciones"),
    )
    respuesta = cliente.table("intervenciones").insert(fila).execute()
    insertadas = list(respuesta.data or [])
    if not insertadas:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "No se pudo registrar la intervencion")
    return insertadas[0]


@router.get("", summary="Lista las intervenciones registradas")
def listar_intervenciones(
    limite: int = Query(100, ge=1, le=500),
    dni: str | None = None,
    estado: str | None = None,
    config: Settings = Depends(obtener_config),
    usuario: UsuarioActual = Depends(usuario_actual),
) -> dict[str, Any]:
    if not _tabla_disponible(config):
        return {"total": 0, "datos": []}
    cliente = cliente_usuario(config, usuario.token)
    consulta = cliente.table("intervenciones").select("*")
    if dni:
        consulta = consulta.eq("dni", dni)
    if estado:
        consulta = consulta.eq("estado", estado)
    respuesta = consulta.order("fecha_derivacion", desc=True).limit(limite).execute()
    datos = list(respuesta.data or [])
    return {"total": len(datos), "datos": datos}


@router.patch("/{intervencion_id}", summary="Actualiza el estado o el resultado de una intervencion")
def actualizar_intervencion(
    intervencion_id: int,
    cambios: IntervencionPatch,
    config: Settings = Depends(obtener_config),
    usuario: UsuarioActual = Depends(usuario_actual),
) -> dict[str, Any]:
    if not _tabla_disponible(config):
        raise _sin_tabla()
    datos = _serializable(cambios.model_dump(exclude_none=True))
    if not datos:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No hay cambios que aplicar")
    cliente = cliente_usuario(config, usuario.token)
    respuesta = cliente.table("intervenciones").update(datos).eq("id", intervencion_id).execute()
    filas = list(respuesta.data or [])
    if not filas:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Intervencion no encontrada")
    return filas[0]


@router.delete("/{intervencion_id}", summary="Elimina el registro de una intervencion")
def eliminar_intervencion(
    intervencion_id: int,
    config: Settings = Depends(obtener_config),
    usuario: UsuarioActual = Depends(usuario_actual),
) -> dict[str, Any]:
    if not _tabla_disponible(config):
        raise _sin_tabla()
    cliente = cliente_usuario(config, usuario.token)
    respuesta = cliente.table("intervenciones").delete().eq("id", intervencion_id).execute()
    if not list(respuesta.data or []):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Intervencion no encontrada")
    return {"eliminado": True, "id": intervencion_id}
