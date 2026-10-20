"""Tests del nucleo de inferencia.

Objetivo: blindar el contrato entre el formulario del orientador y el modelo
entrenado. El fallo historico era que las variables categoricas se enviaban
como "1"/"0" o codigos numericos de carrera y el `OneHotEncoder` las descartaba
en silencio; estos tests fallan si vuelve a ocurrir.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

from predictor import (
    DEFAULTS,
    MAPA_CARRERAS,
    MODEL_VERSION,
    UMBRAL_ALTO,
    UMBRAL_MEDIO,
    construir_dataframe,
    modelo,
    predecir_riesgo_abandono,
)

SI = "Sí"


def formulario_base() -> dict:
    return {
        "edad": 18,
        "genero": "Masculino",
        "becario": "No",
        "deudor": "No",
        "matricula_al_dia": SI,
        "desplazado": "No",
        "area_estudios": "Administración y Negocios",
        "cu1_matriculadas": 5,
        "cu1_aprobadas": 3,
        "cu1_nota": 12.0,
        "cu2_matriculadas": 5,
        "cu2_aprobadas": 3,
        "cu2_nota": 12.0,
    }


# --------------------------------------------------------------------------- #
# Estructura del DataFrame
# --------------------------------------------------------------------------- #
def test_dataframe_tiene_las_mismas_variables_que_el_modelo():
    df = construir_dataframe(formulario_base())
    assert list(df.columns) == list(modelo.feature_names_in_)
    assert len(df) == 1


def test_las_categoricas_usan_las_etiquetas_del_entrenamiento():
    df = construir_dataframe(formulario_base())
    assert df.loc[0, "Gender"] == "Male"
    assert df.loc[0, "Tuition fees up to date"] == "Yes"
    assert df.loc[0, "Debtor"] == "No"
    assert df.loc[0, "Course"] == MAPA_CARRERAS["Administración y Negocios"]


@pytest.mark.parametrize(
    "campo,valor,esperado",
    [
        ("genero", "Femenino", "Female"),
        ("genero", "Masculino", "Male"),
        ("becario", SI, "Yes"),
        ("becario", "No", "No"),
        ("deudor", SI, "Yes"),
        ("matricula_al_dia", "No", "No"),
        ("desplazado", SI, "Yes"),
    ],
)
def test_normalizacion_de_categoricas(campo, valor, esperado):
    datos = formulario_base()
    datos[campo] = valor
    df = construir_dataframe(datos)
    columna = {
        "genero": "Gender",
        "becario": "Scholarship holder",
        "deudor": "Debtor",
        "matricula_al_dia": "Tuition fees up to date",
        "desplazado": "Displaced",
    }[campo]
    assert df.loc[0, columna] == esperado


def test_las_variables_no_capturadas_se_imputan_con_el_perfil_de_entrenamiento():
    df = construir_dataframe(formulario_base())
    for columna in ("Application mode", "Admission grade", "GDP", "Unemployment rate"):
        assert df.loc[0, columna] == DEFAULTS[columna]
    # Ninguna variable queda en "0" salvo que la mediana real sea 0.
    assert df.loc[0, "Admission grade"] > 0


# --------------------------------------------------------------------------- #
# Cada campo del formulario debe mover la prediccion
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "cambios",
    [
        {"genero": "Femenino"},
        {"becario": SI},
        {"deudor": SI},
        {"matricula_al_dia": "No"},
        {"desplazado": SI},
        {"edad": 25},
        {"cu1_matriculadas": 1, "cu1_aprobadas": 0},
        # El arbol parte 'Curricular units 1st sem (approved)' por 3.5: 0..3 son
        # equivalentes, por eso se prueba un valor que cruza la division.
        {"cu1_aprobadas": 5},
        {"cu1_nota": 6.0},
        {"cu2_matriculadas": 1, "cu2_aprobadas": 0},
        {"cu2_aprobadas": 0},
        {"cu2_nota": 4.0},
    ],
    ids=[
        "genero",
        "becario",
        "deudor",
        "matricula_al_dia",
        "desplazado",
        "edad",
        "cu1_matriculadas",
        "cu1_aprobadas",
        "cu1_nota",
        "cu2_matriculadas",
        "cu2_aprobadas",
        "cu2_nota",
    ],
)
def test_cada_campo_altera_la_probabilidad(cambios):
    base, _ = predecir_riesgo_abandono(formulario_base())
    datos = formulario_base()
    datos.update(cambios)
    alterada, _ = predecir_riesgo_abandono(datos)
    assert not math.isclose(base, alterada, abs_tol=1e-6), (
        f"'{cambios}' no influyo en la prediccion (sigue en {base:.4f})"
    )


def test_el_area_de_estudios_altera_la_probabilidad():
    base, _ = predecir_riesgo_abandono(formulario_base())
    datos = formulario_base()
    datos["area_estudios"] = "Arte y Diseño"  # -> Animation & Multimedia (importancia alta)
    alterada, _ = predecir_riesgo_abandono(datos)
    assert not math.isclose(base, alterada, abs_tol=1e-6)


def test_un_rendimiento_malo_sube_el_riesgo_y_uno_bueno_lo_baja():
    malo = formulario_base()
    malo.update(
        cu1_matriculadas=6,
        cu1_aprobadas=0,
        cu1_nota=4.0,
        cu2_matriculadas=6,
        cu2_aprobadas=0,
        cu2_nota=4.0,
    )
    bueno = formulario_base()
    bueno.update(
        cu1_matriculadas=6,
        cu1_aprobadas=6,
        cu1_nota=18.0,
        cu2_matriculadas=6,
        cu2_aprobadas=6,
        cu2_nota=18.0,
    )
    p_malo, nivel_malo = predecir_riesgo_abandono(malo)
    p_bueno, nivel_bueno = predecir_riesgo_abandono(bueno)
    assert p_malo > p_bueno
    assert nivel_malo == "ALTO"
    assert nivel_bueno in {"BAJO", "MEDIO"}


# --------------------------------------------------------------------------- #
# Validaciones de entrada
# --------------------------------------------------------------------------- #
def test_rechaza_aprobadas_mayores_que_matriculadas():
    datos = formulario_base()
    datos["cu1_aprobadas"] = 9
    with pytest.raises(ValueError, match="no se pueden aprobar"):
        predecir_riesgo_abandono(datos)


def test_rechaza_nota_fuera_de_rango():
    datos = formulario_base()
    datos["cu1_nota"] = 25.0
    with pytest.raises(ValueError):
        predecir_riesgo_abandono(datos)


def test_rechaza_edad_fuera_de_rango():
    datos = formulario_base()
    datos["edad"] = 5
    with pytest.raises(ValueError):
        predecir_riesgo_abandono(datos)


def test_rechaza_area_desconocida():
    datos = formulario_base()
    datos["area_estudios"] = "Carrera inventada"
    with pytest.raises(ValueError, match="Area de estudios no reconocida"):
        predecir_riesgo_abandono(datos)


def test_rechaza_valor_booleano_invalido():
    datos = formulario_base()
    datos["becario"] = "Quizá"
    with pytest.raises(ValueError, match="Valor invalido"):
        predecir_riesgo_abandono(datos)


# --------------------------------------------------------------------------- #
# Salida
# --------------------------------------------------------------------------- #
def test_probabilidad_en_rango_y_nivel_coherente():
    probabilidad, nivel = predecir_riesgo_abandono(formulario_base())
    assert 0.0 <= probabilidad <= 1.0
    assert nivel in {"BAJO", "MEDIO", "ALTO"}
    if probabilidad > UMBRAL_ALTO:
        assert nivel == "ALTO"
    elif probabilidad > UMBRAL_MEDIO:
        assert nivel == "MEDIO"
    else:
        assert nivel == "BAJO"


def test_umbral_alto_más_estricto_que_el_medio():
    assert UMBRAL_ALTO > UMBRAL_MEDIO


def test_version_del_modelo_disponible():
    assert isinstance(MODEL_VERSION, str) and MODEL_VERSION


# --------------------------------------------------------------------------- #
# La ruta rapida debe ser equivalente al pipeline original de sklearn
# --------------------------------------------------------------------------- #
def test_la_ruta_rapida_coincide_con_el_pipeline_original():
    import numpy as np
    import pandas as pd

    from predictor import TRANSFORMADOR_RAPIDO, construir_valores

    if not TRANSFORMADOR_RAPIDO.disponible:
        pytest.skip("La ruta rapida no aplica a este preprocesado")

    df = pd.read_csv(ROOT / "data" / "processed" / "data_clean.csv")
    muestra = df.sample(n=40, random_state=42)

    for _, fila in muestra.iterrows():
        valores = {c: fila[c] for c in df.columns if c not in ("Target", "target_bin")}
        fila_formulario = {
            "edad": int(fila["Age at enrollment"]),
            "genero": "Masculino" if fila["Gender"] == "Male" else "Femenino",
            "becario": SI if fila["Scholarship holder"] == "Yes" else "No",
            "deudor": SI if fila["Debtor"] == "Yes" else "No",
            "matricula_al_dia": SI if fila["Tuition fees up to date"] == "Yes" else "No",
            "desplazado": SI if fila["Displaced"] == "Yes" else "No",
            "area_estudios": "Arte y Diseño"
            if fila["Course"] == "Animation & Multimedia"
            else "Administración y Negocios",
            "cu1_matriculadas": int(fila["Curricular units 1st sem (enrolled)"]),
            "cu1_aprobadas": int(fila["Curricular units 1st sem (approved)"]),
            "cu1_nota": float(fila["Curricular units 1st sem (grade)"]),
            "cu2_matriculadas": int(fila["Curricular units 2nd sem (enrolled)"]),
            "cu2_aprobadas": int(fila["Curricular units 2nd sem (approved)"]),
            "cu2_nota": float(fila["Curricular units 2nd sem (grade)"]),
        }
        construido = construir_valores(fila_formulario)
        vector = TRANSFORMADOR_RAPIDO.transformar(construido)
        esperado = modelo.named_steps["prep"].transform(
            pd.DataFrame([construido], columns=list(modelo.feature_names_in_))
        )
        assert np.allclose(vector, esperado, atol=1e-9)


def test_la_ruta_rapida_da_la_misma_probabilidad_que_el_pipeline():
    import pandas as pd

    from predictor import TRANSFORMADOR_RAPIDO, construir_valores

    if not TRANSFORMADOR_RAPIDO.disponible:
        pytest.skip("La ruta rapida no aplica a este preprocesado")

    datos = formulario_base()
    fila = construir_valores(datos)
    dataframe = pd.DataFrame([fila], columns=list(modelo.feature_names_in_))
    con_pipeline = float(modelo.predict_proba(dataframe)[0, 1])
    con_ruta_rapida = TRANSFORMADOR_RAPIDO.probabilidad(fila)
    assert abs(con_pipeline - con_ruta_rapida) < 1e-9
