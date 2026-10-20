"""Servicio del modelo: carga unica del `.joblib` y ejecucion de la inferencia."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.core.config import Settings  # noqa: E402

_cargador = threading.Lock()
_modelo: Any = None
_versiones: dict[str, Any] = {}


def cargar_modelo(config: Settings):
    """Carga el pipeline (preprocesado + clasificador) una sola vez."""
    global _modelo
    if _modelo is not None:
        return _modelo
    with _cargador:
        if _modelo is None:
            import joblib

            if not config.model_path.exists():
                raise FileNotFoundError(
                    f"No se encuentra el modelo en {config.model_path}. "
                    "Entrena el modelo con notebooks/02_modeling.ipynb."
                )
            _modelo = joblib.load(config.model_path)
    return _modelo


def predecir(datos_formulario: dict[str, Any], config: Settings) -> dict[str, Any]:
    """Ejecuta la inferencia y devuelve probabilidad, nivel y metadatos."""
    from src.predictor import MODEL_VERSION, UMBRAL_ALTO, UMBRAL_MEDIO, predecir_riesgo_abandono

    inicio = time.perf_counter()
    probabilidad, nivel = predecir_riesgo_abandono(datos_formulario)
    duracion_ms = (time.perf_counter() - inicio) * 1000
    return {
        "probabilidad": float(probabilidad),
        "nivel": nivel,
        "modelo_version": MODEL_VERSION,
        "umbrales": {"alto": UMBRAL_ALTO, "medio": UMBRAL_MEDIO},
        "tiempo_ms": round(duracion_ms, 3),
    }


def informacion_modelo(config: Settings) -> dict[str, Any]:
    """Metadatos del modelo para el endpoint /health."""
    from src.predictor import MODEL_VERSION

    modelo = cargar_modelo(config)
    return {
        "modelo_version": MODEL_VERSION,
        "variables": len(getattr(modelo, "feature_names_in_", [])),
        "ruta": str(config.model_path),
        "existe_defaults": config.defaults_path.exists(),
    }
