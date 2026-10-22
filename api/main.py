"""API EarlySign: prediccion de senales tempranas de abandono universitario.

Ejecucion en desarrollo:
    uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.core.config import obtener_config
from api.routers import auth, dashboard, evaluaciones, intervenciones, kpis, predict
from api.services.model import cargar_modelo, informacion_modelo
from api.services.supabase import estado_supabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("earlysign")


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = obtener_config()
    try:
        cargar_modelo(config)
        logger.info("Modelo cargado: %s", config.model_path)
    except Exception:  # pragma: no cover
        logger.exception("No se pudo cargar el modelo")
    yield


def crear_app() -> FastAPI:
    config = obtener_config()
    app = FastAPI(
        title="API EarlySign",
        description=(
            "EarlySign: prediccion de señales tempranas de abandono academico. El modelo esta "
            "entrenado con el dataset de la UCI (Portugal) y se expone como servicio para "
            "el frontend Angular."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_origin_regex=config.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(predict.router)
    app.include_router(evaluaciones.router)
    app.include_router(dashboard.router)
    app.include_router(intervenciones.router)
    app.include_router(kpis.router)

    @app.get("/health", tags=["sistema"], summary="Estado del servicio")
    def health() -> dict[str, Any]:
        info: dict[str, Any] = {"estado": "ok", "version": app.version}
        try:
            info["modelo"] = informacion_modelo(config)
        except Exception as exc:  # pragma: no cover
            info["estado"] = "degradado"
            info["modelo"] = {"error": str(exc)}
        info["supabase_configurado"] = bool(config.supabase_base_url)
        info["supabase"] = estado_supabase(config)
        if info["supabase"].get("estado") != "ok":
            info["estado"] = "degradado"
        return info

    @app.get("/api/v1", tags=["sistema"], summary="Indice de la API")
    def indice() -> dict[str, Any]:
        return {
            "servicio": "API EarlySign",
            "documentacion": "/docs",
            "endpoints": {
                "login": "POST /api/v1/auth/login",
                "perfil": "GET /api/v1/auth/me",
                "predecir": "POST /api/v1/predict",
                "evaluaciones": "POST|GET /api/v1/evaluaciones",
                "panel": "GET /api/v1/dashboard/resumen",
                "intervenciones": "POST|GET /api/v1/intervenciones",
                "kpis": "GET /api/v1/kpis/impacto",
            },
        }

    @app.exception_handler(ValueError)
    async def manejar_value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    return app


app = crear_app()
