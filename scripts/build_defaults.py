"""Genera `models/defaults.json` con los valores por defecto del entrenamiento.

El predictor recibe un formulario corto (13 campos) pero el modelo espera las 36
variables del dataset de entrenamiento (UCI Portugal). Las variables que el
formulario no captura se imputan con la mediana (numéricas) o la moda
(categóricas) del entrenamiento: es la imputación más neutra posible, porque
deja al estudiante en la posición promedio de la población de referencia.

Uso:
    python scripts/build_defaults.py
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_CLEAN = ROOT / "data" / "processed" / "data_clean.csv"
MODELS_DIR = ROOT / "models"
MODELO = MODELS_DIR / "modelo_final.joblib"
SALIDA = MODELS_DIR / "defaults.json"

# Variables que el formulario NO captura: se imputan con el perfil del entrenamiento.
CATEGORICAS = [
    "Marital status",
    "Daytime/evening attendance",
    "Gender",
    "Course",
    "Displaced",
    "Educational special needs",
    "Debtor",
    "Tuition fees up to date",
    "Scholarship holder",
    "International",
]


def main() -> None:
    modelo = joblib.load(MODELO)
    features = list(modelo.feature_names_in_)
    df = pd.read_csv(DATA_CLEAN)

    defaults: dict[str, object] = {}
    for col in features:
        if col not in df.columns:
            raise KeyError(f"El dataset de entrenamiento no contiene la variable '{col}'")
        serie = df[col]
        if col in CATEGORICAS:
            modo = serie.mode()
            if modo.empty:
                raise ValueError(f"La variable categórica '{col}' no tiene moda")
            defaults[col] = str(modo.iloc[0])
        else:
            defaults[col] = float(pd.to_numeric(serie, errors="coerce").median())

    payload = {
        "descripcion": (
            "Perfil de imputacion del dataset de entrenamiento (UCI Portugal). "
            "Se usa para las variables que el formulario no solicita."
        ),
        "dataset": str(DATA_CLEAN.relative_to(ROOT)).replace("\\", "/"),
        "n_filas": int(len(df)),
        "categoricas": CATEGORICAS,
        "defaults": defaults,
    }
    SALIDA.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Defaults guardados en {SALIDA} ({len(defaults)} variables, {len(df)} filas de entrenamiento).")


if __name__ == "__main__":
    main()
