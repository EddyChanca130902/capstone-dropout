"""Indicadores del panel principal."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from api.core.config import Settings, obtener_config
from api.core.security import UsuarioActual, usuario_actual
from api.services import evaluaciones as repo

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/resumen", summary="Metricas del panel para el usuario autenticado")
def resumen(
    config: Settings = Depends(obtener_config),
    usuario: UsuarioActual = Depends(usuario_actual),
) -> dict[str, Any]:
    return repo.resumen(config, access_token=usuario.token, user_id=usuario.id)
