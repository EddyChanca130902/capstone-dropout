"""CRUD de evaluaciones (persistencia en Supabase)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.core.config import Settings, obtener_config
from api.core.security import UsuarioActual, usuario_actual
from api.schemas.estudiante import EstudianteIn
from api.schemas.evaluacion import EvaluacionPatch
from api.services import evaluaciones as repo
from api.services.model import predecir
from src.predictor import explicar_riesgo

router = APIRouter(prefix="/api/v1/evaluaciones", tags=["evaluaciones"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Evalua un estudiante y guarda el resultado",
)
def crear_evaluacion(
    estudiante: EstudianteIn,
    config: Settings = Depends(obtener_config),
    usuario: UsuarioActual = Depends(usuario_actual),
) -> dict[str, Any]:
    resultado = predecir(estudiante.a_formulario(), config)
    # Explicabilidad: que variablesResponsible de la alerta (base del KPI 3).
    try:
        explicacion = explicar_riesgo(estudiante.a_formulario())
    except Exception:  # pragma: no cover - la explicacion no es critica
        explicacion = {"factores": [], "variables_en_alerta": []}
    fila: dict[str, Any] = {
        "dni": estudiante.dni,
        "nombre": estudiante.nombre,
        "area_estudios": estudiante.area_estudios,
        "probabilidad": resultado["probabilidad"],
        "nivel": resultado["nivel"],
        "modelo_version": resultado["modelo_version"],
        "entradas": estudiante.model_dump(),
        "factores_clave": explicacion.get("factores", []),
        "variables_en_alerta": explicacion.get("variables_en_alerta", []),
        "created_at": None,
    }
    fila = {k: v for k, v in fila.items() if v is not None}
    guardada = repo.crear(config, fila, access_token=usuario.token, user_id=usuario.id)
    return {
        "id": guardada.get("id"),
        "dni": guardada.get("dni"),
        "nombre": guardada.get("nombre"),
        "area_estudios": guardada.get("area_estudios"),
        "probabilidad": float(guardada.get("probabilidad", resultado["probabilidad"])),
        "nivel": guardada.get("nivel", resultado["nivel"]),
        "modelo_version": resultado["modelo_version"],
        "tiempo_ms": resultado["tiempo_ms"],
    }


@router.get("", summary="Lista las evaluaciones del usuario")
def listar_evaluaciones(
    limite: int = Query(50, ge=1, le=500),
    desplazamiento: int = Query(0, ge=0),
    area: str | None = None,
    nivel: str | None = None,
    orden: str = Query("desc", pattern="^(asc|desc)$"),
    config: Settings = Depends(obtener_config),
    usuario: UsuarioActual = Depends(usuario_actual),
) -> dict[str, Any]:
    filas = repo.listar(
        config,
        access_token=usuario.token,
        user_id=usuario.id,
        limite=limite,
        desplazamiento=desplazamiento,
        area=area,
        nivel=nivel,
        orden=orden,
    )
    return {"total": len(filas), "datos": filas}


@router.get("/{evaluacion_id}", summary="Detalle de una evaluacion")
def obtener_evaluacion(
    evaluacion_id: int,
    config: Settings = Depends(obtener_config),
    usuario: UsuarioActual = Depends(usuario_actual),
) -> dict[str, Any]:
    fila = repo.obtener(config, evaluacion_id, access_token=usuario.token, user_id=usuario.id)
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evaluacion no encontrada")
    return fila


@router.patch("/{evaluacion_id}", summary="Corrige manualmente una evaluacion")
def actualizar_evaluacion(
    evaluacion_id: int,
    cambios: EvaluacionPatch,
    config: Settings = Depends(obtener_config),
    usuario: UsuarioActual = Depends(usuario_actual),
) -> dict[str, Any]:
    datos = cambios.model_dump(exclude_none=True)
    if not datos:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No hay cambios que aplicar")
    fila = repo.actualizar(config, evaluacion_id, datos, access_token=usuario.token, user_id=usuario.id)
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evaluacion no encontrada")
    return fila


@router.delete("/{evaluacion_id}", summary="Elimina una evaluacion")
def eliminar_evaluacion(
    evaluacion_id: int,
    config: Settings = Depends(obtener_config),
    usuario: UsuarioActual = Depends(usuario_actual),
) -> dict[str, Any]:
    if not repo.eliminar(config, evaluacion_id, access_token=usuario.token, user_id=usuario.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evaluacion no encontrada")
    return {"eliminado": True, "id": evaluacion_id}
