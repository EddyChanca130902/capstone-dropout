"""Contratos de salida de la API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Nivel = Literal["BAJO", "MEDIO", "ALTO"]


class PrediccionOut(BaseModel):
    """Resultado de la inferencia."""

    probabilidad: float = Field(ge=0, le=1)
    nivel: Nivel
    modelo_version: str
    umbrales: dict[str, float]
    tiempo_ms: float | None = Field(default=None, description="Latencia de la inferencia")


class EvaluacionOut(BaseModel):
    """Evaluacion persistida."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    dni: str
    nombre: str
    area_estudios: str
    probabilidad: float
    nivel: str
    modelo_version: str | None = None
    entradas: dict[str, Any] | None = None
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None


class EvaluacionIn(BaseModel):
    """Cabecera de una evaluacion tal como la envia el cliente."""

    dni: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1, max_length=120)
    area_estudios: str = Field(min_length=1, max_length=120)


class EvaluacionPatch(BaseModel):
    """Correccion manual de una evaluacion (no recalcula el modelo)."""

    dni: str | None = Field(default=None, min_length=1, max_length=20)
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    area_estudios: str | None = Field(default=None, min_length=1, max_length=120)
    probabilidad: float | None = Field(default=None, ge=0, le=1)
    nivel: Nivel | None = None


class ResumenDashboard(BaseModel):
    """Indicadores del panel principal."""

    estudiantes_evaluados: int
    evaluaciones_realizadas: int
    en_riesgo_alto: int
    probabilidad_promedio: float | None
    por_nivel: dict[str, int]
    por_area: list[dict[str, Any]]
    recientes: list[EvaluacionOut]
