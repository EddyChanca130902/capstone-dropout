"""Inferencia: prediccion de riesgo sin persistir nada.

`POST /api/v1/predict` no toca la base de datos, lo que lo hace ideal para las
pruebas de carga de k6 (no genera registros ni ruido en Supabase).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from api.core.config import Settings, obtener_config
from api.core.security import UsuarioActual, usuario_opcional
from api.schemas.estudiante import EstudianteIn
from api.schemas.evaluacion import PrediccionOut
from api.services.model import predecir

router = APIRouter(prefix="/api/v1", tags=["prediccion"])


@router.post(
    "/predict",
    response_model=PrediccionOut,
    summary="Estima el riesgo de abandono a partir de los datos del formulario",
)
def predecir_riesgo(
    estudiante: EstudianteIn,
    config: Settings = Depends(obtener_config),
    _usuario: UsuarioActual | None = Depends(usuario_opcional),
) -> dict[str, Any]:
    return predecir(estudiante.a_formulario(), config)
