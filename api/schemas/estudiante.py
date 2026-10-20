"""Contrato de entrada: los datos que captura el formulario del orientador."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Area = Literal[
    "Ingeniería y Tecnología",
    "Ciencias de la Salud",
    "Ciencias Sociales y Humanidades",
    "Administración y Negocios",
    "Arte y Diseño",
]

_SI = {"si", "sí", "s", "yes", "y", "1", "true"}
_NO = {"no", "n", "0", "false"}


def _normalizar_si_no(valor: Any) -> Any:
    """Acepta 'Sí', 'Si', 'si', 'yes'... y devuelve la forma canonica 'Sí'/'No'."""
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, str):
        texto = valor.strip().lower()
        if texto in _SI:
            return "Sí"
        if texto in _NO:
            return "No"
    return valor


def _normalizar_genero(valor: Any) -> Any:
    if isinstance(valor, str):
        texto = valor.strip().lower()
        if texto in {"masculino", "male", "m"}:
            return "Masculino"
        if texto in {"femenino", "female", "f"}:
            return "Femenino"
    return valor


class EstudianteIn(BaseModel):
    """Datos personales y academicos de un estudiante."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dni": "70123456",
                "nombre": "María Quispe",
                "edad": 19,
                "genero": "Femenino",
                "area_estudios": "Ciencias de la Salud",
                "becario": "No",
                "deudor": "No",
                "matricula_al_dia": "Sí",
                "desplazado": "No",
                "cu1_matriculadas": 6,
                "cu1_aprobadas": 4,
                "cu1_nota": 13.5,
                "cu2_matriculadas": 6,
                "cu2_aprobadas": 3,
                "cu2_nota": 11.0,
            }
        }
    )

    dni: str = Field(min_length=5, max_length=20, description="Documento de identidad")
    nombre: str = Field(min_length=2, max_length=120)
    edad: int = Field(ge=16, le=60, description="Edad al matricularse")
    genero: Literal["Masculino", "Femenino"]
    area_estudios: Area
    becario: Literal["Sí", "No"]
    deudor: Literal["Sí", "No"]
    matricula_al_dia: Literal["Sí", "No"]
    desplazado: Literal["Sí", "No"]

    cu1_matriculadas: int = Field(ge=0, le=30)
    cu1_aprobadas: int = Field(ge=0, le=30)
    cu1_nota: float = Field(ge=0, le=20, description="Promedio del primer semestre (0-20)")
    cu2_matriculadas: int = Field(ge=0, le=30)
    cu2_aprobadas: int = Field(ge=0, le=30)
    cu2_nota: float = Field(ge=0, le=20, description="Promedio del segundo semestre (0-20)")

    @field_validator("dni", "nombre")
    @classmethod
    def _sin_espacios_extremos(cls, valor: str) -> str:
        return valor.strip()

    @field_validator("becario", "deudor", "matricula_al_dia", "desplazado", mode="before")
    @classmethod
    def _si_no(cls, valor: Any) -> Any:
        return _normalizar_si_no(valor)

    @field_validator("genero", mode="before")
    @classmethod
    def _genero(cls, valor: Any) -> Any:
        return _normalizar_genero(valor)

    @model_validator(mode="after")
    def _aprobadas_no_superan_matriculadas(self):
        for sem in ("cu1", "cu2"):
            matriculadas = getattr(self, f"{sem}_matriculadas")
            aprobadas = getattr(self, f"{sem}_aprobadas")
            if aprobadas > matriculadas:
                raise ValueError(
                    f"En el semestre {sem[2:]} no se pueden aprobar ({aprobadas}) "
                    f"mas asignaturas de las matriculadas ({matriculadas})."
                )
        return self

    def a_formulario(self) -> dict:
        """Diccionario con las claves que espera `src.predictor`."""
        return {
            "edad": self.edad,
            "genero": self.genero,
            "becario": self.becario,
            "deudor": self.deudor,
            "matricula_al_dia": self.matricula_al_dia,
            "desplazado": self.desplazado,
            "area_estudios": self.area_estudios,
            "cu1_matriculadas": self.cu1_matriculadas,
            "cu1_aprobadas": self.cu1_aprobadas,
            "cu1_nota": self.cu1_nota,
            "cu2_matriculadas": self.cu2_matriculadas,
            "cu2_aprobadas": self.cu2_aprobadas,
            "cu2_nota": self.cu2_nota,
        }
