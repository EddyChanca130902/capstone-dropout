"""Registro de las intervenciones de acompanamiento (origen de los KPI de impacto)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.core.config import Settings, obtener_config
from api.core.security import UsuarioActual, usuario_actual
from api.schemas.intervencion import IntervencionIn, IntervencionOut, IntervencionPatch
from api.services.supabase import cliente_usuario, columnas_tabla, filtrar_columnas

router = APIRouter(prefix="/api/v1/intervenciones", tags=["intervenciones"])


def _tabla_disponible(config: Settings) -> bool:
    return "intervenciones" in columnas_tabla(config, "intervenciones")


def _sin_tabla() -> HTTPException:
    return HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "La tabla de intervenciones no existe. Aplica supabase/migrations/0002_intervenciones.sql",
    )


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
    fila = filtrar_columnas({k: v for k, v in fila.items() if v is not None}, columnas_tabla(config, "intervenciones"))
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
    datos = cambios.model_dump(exclude_none=True)
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
