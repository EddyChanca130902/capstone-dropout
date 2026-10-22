"""Nucleo de inferencia: traduce el formulario del orientador a las variables
que espera el modelo entrenado con el dataset de la UCI (Portugal).

Reglas de diseno
-----------------
1. Las variables categoricas se pasan con las ETIQUETAS que vio el
   `OneHotEncoder` durante el entrenamiento ("Male"/"Female", "Yes"/"No",
   nombre del curso). Si se pasan codigos ("1"/"0"), el encoder las descarta en
   silencio (`handle_unknown="ignore"`) y la variable deja de influir.
2. Las variables que el formulario no captura se imputan con la mediana (o la
   moda) del entrenamiento, guardadas en `models/defaults.json`. Antes se
   rellenaban con "0", lo que sesgaba la prediccion.
3. El modelo se carga una sola vez al importar el modulo.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "modelo_final.joblib"
DEFAULTS_PATH = ROOT / "models" / "defaults.json"

# Umbrales de clasificacion (ver README: se recalibraron sobre el test split).
UMBRAL_ALTO = 0.60
UMBRAL_MEDIO = 0.35

# Version del modelo para trazabilidad de cada evaluacion guardada.
MODEL_VERSION = "xgboost-portugal-2026-10"

# Mapeo de las areas del formulario a las carreras del dataset de Portugal.
# Es una simplificacion explicita: el modelo esta entrenado con Portugal y el
# producto se presenta para el contexto peruano.
MAPA_CARRERAS = {
    "Ingeniería y Tecnología": "Informatics Eng",
    "Ciencias de la Salud": "Nursing",
    "Ciencias Sociales y Humanidades": "Social Service",
    "Administración y Negocios": "Management",
    "Arte y Diseño": "Animation & Multimedia",
}

_SI = {"si", "sí", "s", "yes", "y", "1", "true"}
_NO = {"no", "n", "0", "false"}

modelo = joblib.load(MODEL_PATH)

if DEFAULTS_PATH.exists():
    _payload = json.loads(DEFAULTS_PATH.read_text(encoding="utf-8"))
    DEFAULTS: dict[str, Any] = _payload["defaults"]
else:  # pragma: no cover - solo si se ejecuta build_defaults.py
    DEFAULTS = {}

# Variables categoricas del modelo (se codifican con One-Hot).
VARIABLES_CATEGORICAS = [
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


class TransformadorRapido:
    """Replica `ColumnTransformer` + `OneHotEncoder` de forma vectorizada.

    El preprocesado de sklearn sobre una fila cuesta ~5 ms (validaciones de
    pandas/numpy), que es casi toda la latencia de una prediccion. Como el
    transformador es lineal (StandardScaler) mas una busqueda de one-hot, se
    puede calcular directamente sobre el diccionario de valores.

    `tests/test_predictor.py` verifica que esta ruta produce exactamente el
    mismo resultado que el pipeline original.
    """

    def __init__(self, pipeline) -> None:
        self.disponible = False
        try:
            prep = pipeline.named_steps["prep"]
            transformadores = {nombre: trans for nombre, trans, _ in prep.transformers_}
            num_cols = list(prep.transformers_[0][2])
            cat_cols = list(prep.transformers_[1][2])
            scaler = transformadores["num"]
            encoder = transformadores["cat"]

            if not isinstance(scaler, StandardScaler) or not isinstance(encoder, OneHotEncoder):
                return
            if encoder.sparse_output:
                return

            self.num_cols = num_cols
            self.mean = np.asarray(scaler.mean_, dtype=np.float64)
            self.scale = np.asarray(scaler.scale_, dtype=np.float64)
            self.cat_cols = cat_cols
            self.categorias = [list(c) for c in encoder.categories_]
            self.indices = [{c: i for i, c in enumerate(cats)} for cats in self.categorias]
            self.n_num = len(num_cols)
            self.n_cat = sum(len(c) for c in self.categorias)
            self.n_total = self.n_num + self.n_cat
            self.clasificador = pipeline.named_steps["clf"]

            # Mapa: indice de columna transformada -> variable original.
            # Las numericas conservan su nombre; las one-hot se agregan a su
            # variable categorica de origen.
            self.mapa_variables: list[str] = list(num_cols)
            for col, cats in zip(cat_cols, self.categorias):
                for _ in cats:
                    self.mapa_variables.append(col)
            self.disponible = True
        except Exception:  # pragma: no cover - estructura inesperada -> ruta lenta
            self.disponible = False

    def transformar(self, fila: Mapping[str, Any]) -> np.ndarray:
        vector = np.zeros(self.n_total, dtype=np.float64)
        for i, columna in enumerate(self.num_cols):
            vector[i] = (float(fila[columna]) - self.mean[i]) / self.scale[i]
        offset = self.n_num
        for j, columna in enumerate(self.cat_cols):
            indice = self.indices[j].get(fila[columna])
            if indice is not None:
                vector[offset + indice] = 1.0
            offset += len(self.categorias[j])
        return vector

    def probabilidad(self, fila: Mapping[str, Any]) -> float:
        vector = self.transformar(fila).reshape(1, -1)
        return float(self.clasificador.predict_proba(vector)[0, 1])

    def contribuciones(self, fila: Mapping[str, Any]) -> dict[str, float]:
        """Contribucion de cada variable original sobre la prediccion.

        Positivo = aumenta el riesgo; negativo = lo reduce. Se usa
        `pred_contribs` de XGBoost (TreeSHAP), que no requiere la libreria
        shap en tiempo de ejecucion.
        """
        vector = self.transformar(fila).reshape(1, -1)
        try:
            import xgboost as xgb

            booster = self.clasificador.get_booster()
            # En XGBoost 3.x las contribuciones (TreeSHAP) se piden sobre un
            # DMatrix; `inplace_predict` no admite `pred_contribs`.
            matriz = xgb.DMatrix(vector)
            contribs = booster.predict(matriz, pred_contribs=True)[0]
        except Exception:  # pragma: no cover - booster sin TreeSHAP
            return {}
        acumulado: dict[str, float] = {}
        for i, valor in enumerate(contribs[:-1]):
            variable = self.mapa_variables[i]
            acumulado[variable] = acumulado.get(variable, 0.0) + float(valor)
        return acumulado


TRANSFORMADOR_RAPIDO = TransformadorRapido(modelo)


def _booleano(valor: Any, campo: str) -> str:
    """Normaliza 'Sí'/'No' (o variantes) a 'Yes'/'No'."""
    if valor is None:
        raise ValueError(f"Falta el campo '{campo}'")
    if isinstance(valor, bool):
        return "Yes" if valor else "No"
    texto = str(valor).strip().lower()
    if texto in _SI:
        return "Yes"
    if texto in _NO:
        return "No"
    raise ValueError(f"Valor invalido para '{campo}': {valor!r} (se espera 'Sí' o 'No')")


def _genero(valor: Any) -> str:
    texto = str(valor or "").strip().lower()
    if texto in {"masculino", "male", "m"}:
        return "Male"
    if texto in {"femenino", "female", "f"}:
        return "Female"
    raise ValueError(f"Valor invalido para 'genero': {valor!r}")


def _float(valor: Any, campo: str, minimo: float | None = None, maximo: float | None = None) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Valor numerico invalido para '{campo}': {valor!r}") from exc
    if minimo is not None and numero < minimo:
        raise ValueError(f"'{campo}' no puede ser menor que {minimo} (valor: {numero})")
    if maximo is not None and numero > maximo:
        raise ValueError(f"'{campo}' no puede ser mayor que {maximo} (valor: {numero})")
    return numero


def _validar(datos: Mapping[str, Any]) -> None:
    for sem in ("cu1", "cu2"):
        matriculadas = float(datos.get(f"{sem}_matriculadas", 0) or 0)
        aprobadas = float(datos.get(f"{sem}_aprobadas", 0) or 0)
        if aprobadas > matriculadas:
            raise ValueError(
                f"En el semestre {'1' if sem == 'cu1' else '2'} no se pueden aprobar "
                f"({aprobadas}) mas asignaturas de las matriculadas ({matriculadas})."
            )


def construir_valores(datos_formulario: Mapping[str, Any]) -> dict[str, Any]:
    """Devuelve el diccionario con las 36 variables del modelo y sus tipos."""
    _validar(datos_formulario)

    columnas = list(modelo.feature_names_in_)
    fila: dict[str, Any] = {}

    # --- Variables que sí llegan desde el formulario -------------------------------
    fila["Age at enrollment"] = _float(datos_formulario.get("edad", 18), "edad", 16, 60)
    fila["Gender"] = _genero(datos_formulario.get("genero"))
    fila["Scholarship holder"] = _booleano(datos_formulario.get("becario", "No"), "becario")
    fila["Debtor"] = _booleano(datos_formulario.get("deudor", "No"), "deudor")
    fila["Tuition fees up to date"] = _booleano(datos_formulario.get("matricula_al_dia", "Sí"), "matricula_al_dia")
    fila["Displaced"] = _booleano(datos_formulario.get("desplazado", "No"), "desplazado")

    area = str(datos_formulario.get("area_estudios", "Administración y Negocios"))
    if area not in MAPA_CARRERAS:
        raise ValueError(
            f"Area de estudios no reconocida: {area!r}. Opciones: {sorted(MAPA_CARRERAS)}"
        )
    fila["Course"] = MAPA_CARRERAS[area]

    for sem, prefijo in (("1st", "cu1"), ("2nd", "cu2")):
        matriculadas = int(_float(datos_formulario.get(f"{prefijo}_matriculadas", 0), f"{prefijo}_matriculadas", 0, 30))
        aprobadas = int(_float(datos_formulario.get(f"{prefijo}_aprobadas", 0), f"{prefijo}_aprobadas", 0, 30))
        nota = _float(datos_formulario.get(f"{prefijo}_nota", 0), f"{prefijo}_nota", 0, 20)
        fila[f"Curricular units {sem} sem (enrolled)"] = float(matriculadas)
        fila[f"Curricular units {sem} sem (approved)"] = float(aprobadas)
        fila[f"Curricular units {sem} sem (grade)"] = nota

    # --- Variables que el formulario no captura: perfil del entrenamiento ---------
    for columna in columnas:
        if columna in fila:
            continue
        if columna not in DEFAULTS:
            raise KeyError(
                f"Falta el valor por defecto de '{columna}'. Ejecuta: python scripts/build_defaults.py"
            )
        valor = DEFAULTS[columna]
        fila[columna] = str(valor) if columna in VARIABLES_CATEGORICAS else float(valor)

    return fila


def construir_dataframe(datos_formulario: Mapping[str, Any]) -> pd.DataFrame:
    """Construye el DataFrame con la misma estructura y tipos que el entrenamiento."""
    fila = construir_valores(datos_formulario)
    columnas = list(modelo.feature_names_in_)
    df = pd.DataFrame([fila], columns=columnas)
    tipos = {c: ("object" if c in VARIABLES_CATEGORICAS else "float64") for c in columnas}
    return df.astype(tipos)


def predecir_riesgo_abandono(datos_formulario: Mapping[str, Any]) -> tuple[float, str]:
    """Recibe los datos del formulario y devuelve (probabilidad, nivel)."""
    if TRANSFORMADOR_RAPIDO.disponible:
        fila = construir_valores(datos_formulario)
        probabilidad = TRANSFORMADOR_RAPIDO.probabilidad(fila)
    else:  # pragma: no cover - estructura de preprocesado inesperada
        probabilidad = float(modelo.predict_proba(construir_dataframe(datos_formulario))[0, 1])

    if probabilidad > UMBRAL_ALTO:
        nivel = "ALTO"
    elif probabilidad > UMBRAL_MEDIO:
        nivel = "MEDIO"
    else:
        nivel = "BAJO"
    return probabilidad, nivel


def explicar_riesgo(datos_formulario: Mapping[str, Any], top: int = 5) -> dict[str, Any]:
    """Explica la prediccion: variables que mas influyen y en que direccion.

    Devuelve los factores ordenados por contribucion absoluta. Se usan para
    (a) mostrar al orientador por que se marca al estudiante y (b) calcular el
    KPI de indice de resolucion de variables modificables.
    """
    fila = construir_valores(datos_formulario)
    if not TRANSFORMADOR_RAPIDO.disponible:
        return {"factores": []}
    contribuciones = TRANSFORMADOR_RAPIDO.contribuciones(fila)
    if not contribuciones:
        return {"factores": []}

    factores = []
    for variable, contribucion in contribuciones.items():
        factores.append(
            {
                "variable": variable,
                "contribucion": round(contribucion, 5),
                "direccion": "aumenta_riesgo" if contribucion > 0 else "reduce_riesgo",
                "valor": fila.get(variable),
            }
        )
    factores.sort(key=lambda f: abs(f["contribucion"]), reverse=True)
    return {"factores": factores[:top], "variables_en_alerta": [
        f["variable"] for f in factores if f["contribucion"] > 0
    ]}


def explicar(datos_formulario: Mapping[str, Any]) -> dict[str, Any]:
    """Devuelve la prediccion junto al detalle de las variables del formulario."""
    probabilidad, nivel = predecir_riesgo_abandono(datos_formulario)
    return {
        "probabilidad": probabilidad,
        "nivel": nivel,
        "modelo_version": MODEL_VERSION,
        "umbrales": {"alto": UMBRAL_ALTO, "medio": UMBRAL_MEDIO},
        "entradas": dict(datos_formulario),
    }


# Alias retrocompatible con las versiones previas del dashboard y de la API.
predecir_riesgo_portugal = predecir_riesgo_abandono
