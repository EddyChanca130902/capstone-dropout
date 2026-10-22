"""Informe de los KPI de impacto del acompanamiento."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from api.core.config import Settings, obtener_config
from api.core.security import UsuarioActual, usuario_actual
from api.schemas.intervencion import KpiInforme
from api.services.kpis import calcular_kpis

router = APIRouter(prefix="/api/v1/kpis", tags=["kpis"])


@router.get(
    "/impacto",
    response_model=KpiInforme,
    summary="KPI de impacto del acompanamiento (cobertura, reduccion de riesgo, "
    "resolucion de variables y tiempo de respuesta)",
)
def informe_impacto(
    config: Settings = Depends(obtener_config),
    usuario: UsuarioActual = Depends(usuario_actual),
) -> dict[str, Any]:
    return calcular_kpis(config, access_token=usuario.token, user_id=usuario.id)
