"""Contratos de las intervenciones de acompanamiento."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Estado = Literal["DERIVADA", "EN_PROCESO", "CERRADA"]
Canal = Literal["TUTORIA", "ORIENTACION", "BECATEO", "DERIVACION", "OTRO"]


class IntervencionIn(BaseModel):
    """Registro de la derivacion a acompanamiento."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dni": "70123456",
                "nombre": "María Quispe",
                "fecha_deteccion": "2026-10-01T10:00:00Z",
                "fecha_derivacion": "2026-10-01T10:00:00Z",
                "fecha_inicio": "2026-10-03T09:00:00Z",
                "responsable": "Orientador Ana",
                "canal": "TUTORIA",
                "accion": "Tutoria de refuerzo en cursos de segundo semestre y gestion de deuda",
                "variables_en_alerta": ["Tuition fees up to date", "Curricular units 2nd sem (approved)"],
            }
        }
    )

    dni: str = Field(min_length=5, max_length=20)
    nombre: str | None = Field(default=None, max_length=120)
    evaluacion_id: int | None = None
    fecha_deteccion: datetime | None = None
    fecha_derivacion: datetime | None = None
    fecha_inicio: datetime | None = None
    responsable: str | None = Field(default=None, max_length=120)
    canal: Canal = "TUTORIA"
    accion: str = Field(min_length=3, max_length=1000)
    estado: Estado = "DERIVADA"
    variables_en_alerta: list[str] = Field(default_factory=list)
    resultado: str | None = Field(default=None, max_length=1000)


class IntervencionPatch(BaseModel):
    """Correccion de una intervencion."""

    fecha_inicio: datetime | None = None
    responsable: str | None = Field(default=None, max_length=120)
    canal: Canal | None = None
    accion: str | None = Field(default=None, min_length=3, max_length=1000)
    estado: Estado | None = None
    resultado: str | None = Field(default=None, max_length=1000)


class IntervencionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dni: str
    nombre: str | None = None
    evaluacion_id: int | None = None
    fecha_deteccion: datetime | None = None
    fecha_derivacion: datetime | None = None
    fecha_inicio: datetime | None = None
    responsable: str | None = None
    canal: str | None = None
    accion: str | None = None
    estado: str = "DERIVADA"
    variables_en_alerta: list[str] = Field(default_factory=list)
    resultado: str | None = None
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None


class KpiInforme(BaseModel):
    """Informe de los KPI de impacto del acompanamiento."""

    generado_en: datetime
    kpi_cobertura_intervencion: KpiValor
    kpi_reduccion_riesgo: KpiValor
    kpi_resolucion_variables: KpiValor
    kpi_tiempo_respuesta: KpiValor
    detalle: dict[str, Any] = Field(default_factory=dict)


class KpiValor(BaseModel):
    """Un KPI con su formula resuelta."""

    valor: float | None = None
    unidad: str = "%"
    numerador: float = 0
    denominador: float = 0
    formula: str
    disponible: bool = True
    nota: str | None = None
