"""Configuracion de la API (variables de entorno)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Supabase ---
    supabase_url: str = ""
    # `SUPABASE_KEY` es el alias historico del proyecto: se acepta como respaldo
    # de ambas claves para no romper la configuracion existente.
    supabase_anon_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_ANON_KEY", "SUPABASE_KEY"),
    )
    supabase_service_role_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY"),
    )
    # Solo para proyectos Supabase antiguos que firman con HS256.
    supabase_jwt_secret: str | None = None

    # --- API ---
    api_env: str = "development"
    cors_origins: list[str] = ["http://localhost:4200", "http://localhost:8501"]

    # --- Modelo ---
    model_path: Path = ROOT / "models" / "modelo_final.joblib"
    defaults_path: Path = ROOT / "models" / "defaults.json"

    # Tolerancia de reloj al validar JWT (desfase entre el reloj local y Supabase).
    jwt_leeway_seconds: int = 300

    # --- Usuario de prueba (solo desarrollo / pruebas de carga) ---
    test_user_email: str | None = None
    test_user_password: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _partir_origenes(cls, valor):
        if isinstance(valor, str):
            return [o.strip() for o in valor.split(",") if o.strip()]
        return valor

    @property
    def supabase_base_url(self) -> str:
        """URL base del proyecto, sin el sufijo /rest/v1 (que es lo que espera el SDK)."""
        return self.supabase_url.rstrip("/").removesuffix("/rest/v1")

    @property
    def es_produccion(self) -> bool:
        return self.api_env.lower() in {"prod", "production"}

    @property
    def clave_admin(self) -> str:
        """Clave con permisos de servicio. Solo para migraciones y scripts de semilla."""
        return self.supabase_service_role_key or self.supabase_anon_key or ""

    @property
    def clave_anon(self) -> str:
        return self.supabase_anon_key or self.supabase_service_role_key or ""


@lru_cache
def obtener_config() -> Settings:
    return Settings()
