import streamlit as st
import sys
import html
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Añadir la carpeta src al path para importar
sys.path.append(str(Path(__file__).parent.parent / "src"))

from predictor import predecir_riesgo_abandono, MAPA_CARRERAS
from database import (
    verificar_login,
    guardar_evaluacion,
    actualizar_evaluacion,
    eliminar_evaluacion,
    obtener_historial,
)

st.set_page_config(page_title="AlertaTemprana", layout="wide", page_icon="🎓")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

:root {
    --ink: #182b3a;
    --muted: #667887;
    --brand: #176b72;
    --brand-dark: #10545a;
    --brand-soft: #e6f3f1;
    --line: #e2e9ec;
    --canvas: #f4f7f8;
    --surface: #ffffff;
    --risk-high: #bd4e45;
    --risk-medium: #c48726;
    --risk-low: #39816a;
}
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
[data-testid="stAppViewContainer"] { background: var(--canvas); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 1380px; padding-top: 2rem; padding-bottom: 3rem; }
h1, h2, h3 { font-family: 'Manrope', sans-serif; color: var(--ink); letter-spacing: -.035em; }
h1 { font-size: 2.15rem !important; font-weight: 800 !important; }
h2 { font-weight: 750 !important; }
p, [data-testid="stCaptionContainer"] { color: var(--muted); }
div[data-testid="stMetric"] {
    min-height: 120px; background: var(--surface); border: 1px solid var(--line); border-radius: 16px;
    padding: 1rem 1.2rem; box-shadow: 0 5px 20px rgba(24, 43, 58, .04);
}
div[data-testid="stMetricLabel"] { color: var(--muted); font-weight: 600; }
div[data-testid="stMetricValue"] { color: var(--ink); font-family: 'Manrope', sans-serif; font-weight: 800; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { font-weight: 600; }
.stButton > button, .stFormSubmitButton > button {
    min-height: 2.8rem; border-radius: 11px; border: 1px solid var(--brand);
    background: var(--brand); color: #fff; font-weight: 700; transition: .18s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: var(--brand-dark); background: var(--brand-dark); color: #fff;
    box-shadow: 0 5px 14px rgba(23, 107, 114, .18);
}
.stButton > button[kind="secondary"] {
    background: transparent; color: var(--ink); border-color: transparent; text-align: left;
}
.stButton > button[kind="secondary"]:hover {
    background: var(--brand-soft); color: var(--brand-dark); border-color: var(--brand-soft); box-shadow: none;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--line); border-radius: 16px; background: var(--surface);
}
.login-panel {
    min-height: 480px; box-sizing: border-box; padding: 3rem; position: relative; overflow: hidden;
    border-radius: 24px; color: #fff;
    background: radial-gradient(circle at 90% 12%, rgba(133, 219, 208, .28), transparent 30%),
                linear-gradient(145deg, #153b4b 0%, #176b72 65%, #348c82 100%);
    box-shadow: 0 22px 65px rgba(24, 43, 58, .14);
}
.login-panel:after {
    content: ''; position: absolute; width: 280px; height: 280px; right: -120px; bottom: -145px;
    border: 1px solid rgba(255,255,255,.2); border-radius: 50%;
    box-shadow: 0 0 0 32px rgba(255,255,255,.04), 0 0 0 66px rgba(255,255,255,.035);
}
.login-icon { font-size: 2.7rem; margin: .5rem 0 2.5rem; }
.login-panel h1 { color: #fff !important; font-size: 2.65rem !important; line-height: 1.14; }
.login-panel p { max-width: 390px; color: rgba(255,255,255,.78); font-size: 1.02rem; line-height: 1.7; }
.login-tag { color: #f5d7c2; font-size: .75rem; font-weight: 800; letter-spacing: .15em; }
.login-card { padding: 2.3rem 1.7rem .5rem; }
.login-card h2 { margin-bottom: .2rem; }
.eyebrow { color: var(--brand); font-size: .73rem; font-weight: 800; letter-spacing: .13em; text-transform: uppercase; }
.risk-symbol { font-size: 3rem; line-height: 1; margin: .4rem 0 .8rem; }
.dashboard-hero {
    padding: 1.8rem 2rem; margin: .5rem 0 1.35rem; border-radius: 21px; color: var(--ink);
    background: radial-gradient(circle at 88% 15%, rgba(103, 188, 176, .14), transparent 27%), #ffffff;
    border: 1px solid var(--line);
    box-shadow: 0 8px 24px rgba(24, 43, 58, .04);
}
.dashboard-hero h1 { color: var(--ink) !important; margin: .3rem 0; }
.dashboard-hero p { color: var(--muted); margin: 0; }
.dashboard-hero .eyebrow { color: var(--brand); }
.section-heading { margin: 1.5rem 0 .25rem; }
.dashboard-empty {
    border: 1px dashed #b7c9cf; border-radius: 16px; padding: 1.5rem;
    background: #ffffff; color: #667887;
}
.dashboard-note { padding: .85rem 1rem; border-left: 3px solid var(--brand); background: #edf5f4; border-radius: 0 10px 10px 0; color: #47636a; font-size: .9rem; }
@media (max-width: 760px) {
    .login-panel { min-height: 320px; padding: 2rem; }
    .login-panel h1 { font-size: 2.1rem !important; }
    .login-card { padding: 1.5rem .4rem .4rem; }
}
</style>
""", unsafe_allow_html=True)

if st.session_state.get("modo_oscuro", False):
    st.markdown("""
    <style>
    :root { --ink:#e6edf2; --muted:#a4b4c1; --brand:#5bc2b5; --brand-dark:#3c9f95; --brand-soft:#1b393d; --line:#2b4050; --canvas:#101b26; --surface:#172633; }
    [data-testid="stAppViewContainer"], .stApp { background:#101b26 !important; color:#e6edf2 !important; }
    [data-testid="stSidebar"] { background:#132230 !important; border-color:#2b4050 !important; }
    [data-testid="stSidebar"] div[style*="#182b3a"] { color:#e6edf2 !important; }
    [data-testid="stSidebar"] div[style*="#667887"] { color:#a4b4c1 !important; }
    .stButton > button[kind="secondary"] { background:transparent; color:#dce6ec; border-color:transparent; }
    .stButton > button[kind="secondary"]:hover { background:#1b393d; color:#8edbd1; border-color:#1b393d; }
    h1,h2,h3,[data-testid="stMarkdownContainer"],label { color:#e6edf2; }
    p,[data-testid="stCaptionContainer"] { color:#a4b4c1 !important; }
    div[data-testid="stMetric"],div[data-testid="stVerticalBlockBorderWrapper"],
    .dashboard-hero,.dashboard-empty { background:#172633 !important; border-color:#2b4050 !important; color:#e6edf2 !important; }
    .dashboard-note { background:#1b393d !important; color:#d0e5e3 !important; }
    input,textarea,[data-baseweb="select"] > div,[data-baseweb="input"] > div {
        background:#1b2d3b !important; color:#e6edf2 !important; border-color:#405666 !important;
    }
    [data-testid="stDataFrame"] { border-color:#2b4050 !important; }
    [data-testid="stAlert"] { background:#1b2d3b; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# --- PANTALLA DE LOGIN ---
if not st.session_state["autenticado"]:
    st.markdown("<div style='height:4vh'></div>", unsafe_allow_html=True)
    login_intro, login_form = st.columns([1.08, 0.92], gap="large", vertical_alignment="center")
    with login_intro:
        st.markdown("""
        <section class="login-panel">
            <div class="login-icon">🎓</div>
            <div class="login-tag">ALERTA TEMPRANA · ACOMPAÑAMIENTO ACADÉMICO</div>
            <h1>Una alerta a tiempo<br>puede cambiarlo todo.</h1>
            <p>Identifica señales de riesgo académico y facilita un acompañamiento oportuno para cada estudiante.</p>
        </section>
        """, unsafe_allow_html=True)
    with login_form:
        st.markdown("""
        <div class="login-card">
            <div class="eyebrow">Plataforma de seguimiento</div>
            <h2>Bienvenido de nuevo</h2>
            <p>Inicia sesión para acceder al espacio de evaluación.</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login"):
            user = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            pwd = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
            if st.form_submit_button("Ingresar", width="stretch"):
                nombre = verificar_login(user, pwd)
                if nombre:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario"] = nombre
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Usa admin / 123")
    st.stop()

# --- MENÚ LATERAL ---
st.sidebar.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin:.2rem 0 1.4rem">
  <div style="width:44px;height:44px;display:grid;place-items:center;border-radius:14px;background:#e6f3f1;font-size:22px">🎓</div>
  <div><div style="font:800 1.05rem Manrope,sans-serif;color:#182b3a">AlertaTemprana</div>
  <div style="font-size:.78rem;color:#667887">Seguimiento académico</div></div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown(f"**👋 Bienvenido, {st.session_state['usuario']}**")
st.sidebar.caption("Versión legacy · el producto vigente es Angular + FastAPI + Supabase")
modo_oscuro = st.sidebar.toggle("Modo oscuro", key="modo_oscuro")
if st.sidebar.button("↪ Cerrar sesión", width="stretch", key="cerrar_sesion"):
    for clave in ["usuario", "pagina", "paso_formulario", "datos_personales_formulario", "datos_academicos_formulario"]:
        st.session_state.pop(clave, None)
    for clave in list(st.session_state):
        if clave.startswith(("form_", "dni_", "nombre_", "carrera_", "riesgo_", "nivel_", "confirmar_eliminar_", "selector_crud_")):
            st.session_state.pop(clave, None)
    st.session_state["autenticado"] = False
    st.rerun()
st.sidebar.divider()

PAGINA_INICIO = "📊 Panel principal"
PAGINA_EVALUAR = "📝 Evaluar estudiante"
PAGINA_HISTORIAL = "📋 Historial de evaluaciones"

def navegar_a(pagina_destino):
    st.session_state["pagina"] = pagina_destino
    if pagina_destino == PAGINA_EVALUAR:
        st.session_state["paso_formulario"] = 1
        st.session_state["datos_personales_formulario"] = {}
        st.session_state["datos_academicos_formulario"] = {}

st.session_state.setdefault("pagina", PAGINA_INICIO)
st.sidebar.markdown("**ESPACIO DE TRABAJO**")
for destino, clave in [
    (PAGINA_INICIO, "nav_inicio"),
    (PAGINA_EVALUAR, "nav_evaluar"),
    (PAGINA_HISTORIAL, "nav_historial"),
]:
    st.sidebar.button(
        destino,
        width="stretch",
        type="primary" if st.session_state["pagina"] == destino else "secondary",
        key=clave,
        on_click=navegar_a,
        args=(destino,),
    )
pagina = st.session_state["pagina"]

# Los indicadores del panel y la tabla de historial usan el mismo registro SQLite.
df_historial = obtener_historial()

# --- PÁGINA PRINCIPAL: DASHBOARD ---
if pagina == PAGINA_INICIO:
    usuario_html = html.escape(str(st.session_state["usuario"]))
    st.markdown(f"""<section class="dashboard-hero"><div class="eyebrow">CENTRO DE SEGUIMIENTO · RESUMEN</div><h1>Hola, {usuario_html}</h1><p>Monitorea las evaluaciones y prioriza el acompañamiento académico.</p></section>""", unsafe_allow_html=True)
    c1, c2, _ = st.columns([1.15, 1.15, 3.7])
    c1.button("＋ Nueva evaluación", type="primary", width="stretch", on_click=navegar_a, args=(PAGINA_EVALUAR,))
    c2.button("Ver historial  →", width="stretch", on_click=navegar_a, args=(PAGINA_HISTORIAL,))
    if df_historial.empty:
        st.markdown('<div class="dashboard-empty"><b>Tu panel está listo.</b><br>Registra la primera evaluación para empezar a ver los indicadores y casos que requieren seguimiento.</div>', unsafe_allow_html=True)
        st.stop()
    df_panel = df_historial.copy()
    df_panel["fecha_evaluacion"] = pd.to_datetime(df_panel["fecha_evaluacion"], errors="coerce")
    carreras = sorted(df_panel["carrera"].dropna().astype(str).unique().tolist())
    filtro, _ = st.columns([1, 3], vertical_alignment="bottom")
    with filtro:
        area_seleccionada = st.selectbox("Área de estudios", ["Todas las Áreas", *carreras])
    if area_seleccionada != "Todas las Áreas":
        df_panel = df_panel[df_panel["carrera"].astype(str) == area_seleccionada]
    # Estado actual: Última evaluación por DNI; filas sin DNI permanecen independientes.
    df_panel["_identidad"] = df_panel.apply(lambda f: f"dni:{str(f['dni']).strip()}" if pd.notna(f.get("dni")) and str(f.get("dni")).strip() else f"evaluacion:{f['id']}", axis=1)
    ultimo = df_panel.sort_values(["fecha_evaluacion", "id"], na_position="first").drop_duplicates("_identidad", keep="last")
    niveles = ultimo["nivel"].fillna("").astype(str).str.strip().str.upper()
    n = len(ultimo); altos = int(niveles.eq("ALTO").sum()); promedio = pd.to_numeric(ultimo["riesgo"], errors="coerce").mean()
    k = st.columns(4, gap="medium")
    k[0].metric("Estudiantes evaluados", f"{n:,}", help="DNI únicos; cuenta la Última evaluación disponible de cada estudiante.")
    k[1].metric("Evaluaciones realizadas", f"{len(df_panel):,}", help="Incluye evaluaciones anteriores de estudiantes revisados más de una vez.")
    k[2].metric("En riesgo alto", f"{altos:,}", f"{altos/n:.0%} del estado actual" if n else None)
    k[3].metric("Probabilidad promedio", f"{promedio:.1%}" if pd.notna(promedio) else "\u2014", help="Promedio estimado en la evaluación más reciente de cada estudiante.")
    desconocidos = int((~niveles.isin(["ALTO", "MEDIO", "BAJO"])).sum())
    if desconocidos: st.caption(f"{desconocidos} estudiante(s) tienen un nivel no reconocido y no aparecen en la distribución.")
    chart_bg = "#172633" if modo_oscuro else "#ffffff"
    chart_text = "#a4b4c1" if modo_oscuro else "#667887"
    chart_grid = "#2b4050" if modo_oscuro else "#edf1f2"
    left, right = st.columns([1, 1.25], gap="large")
    with left:
        st.subheader("Estado actual de riesgo"); st.caption("Última evaluación disponible por estudiante")
        conteos = niveles.value_counts().reindex(["ALTO", "MEDIO", "BAJO"], fill_value=0)
        colores = {"ALTO": "#bd4e45", "MEDIO": "#c48726", "BAJO": "#39816a"}
        fig, ax = plt.subplots(figsize=(6.3, 3.3)); fig.patch.set_facecolor(chart_bg); ax.set_facecolor(chart_bg)
        bars = ax.barh(conteos.index, conteos.values, color=[colores[x] for x in conteos.index], height=.55)
        ax.invert_yaxis(); ax.set_xlabel("Estudiantes", color=chart_text); ax.spines[["top", "right", "left"]].set_visible(False); ax.spines["bottom"].set_color(chart_grid)
        ax.tick_params(axis="both", colors=chart_text, length=0, pad=8); ax.grid(axis="x", color=chart_grid, linewidth=.8); ax.set_axisbelow(True); ax.bar_label(bars, padding=7, color=chart_text, fontweight="bold"); ax.set_xlim(0, max(1, int(conteos.max())*1.2))
        fig.tight_layout(); st.pyplot(fig, width="stretch"); plt.close(fig)
    with right:
        st.subheader("Riesgo por Área de estudios"); st.caption("Estudiantes en riesgo alto según su evaluación más reciente")
        por_area = ultimo.assign(_nivel=ultimo["nivel"].fillna("").astype(str).str.upper().str.strip(), carrera=ultimo["carrera"].fillna("Sin Área"))
        por_area = por_area.assign(_alto=por_area["_nivel"].eq("ALTO")).groupby("carrera")["_alto"].sum().sort_values()
        fig, ax = plt.subplots(figsize=(7.2, 3.3)); fig.patch.set_facecolor(chart_bg); ax.set_facecolor(chart_bg)
        bars = ax.barh(por_area.index, por_area.values, color="#bd4e45", height=.55)
        ax.spines[["top", "right", "left"]].set_visible(False); ax.spines["bottom"].set_color(chart_grid); ax.tick_params(axis="both", colors=chart_text, length=0, pad=8); ax.grid(axis="x", color=chart_grid, linewidth=.8); ax.set_axisbelow(True); ax.set_xlabel("Estudiantes en riesgo alto", color=chart_text); ax.bar_label(bars, padding=7, color=chart_text, fontweight="bold"); ax.set_xlim(0, max(1, int(por_area.max())*1.2))
        fig.tight_layout(); st.pyplot(fig, width="stretch"); plt.close(fig)
    st.subheader("Evaluaciones recientes"); st.caption("Una persona puede aparecer más de una vez si fue evaluada en distintas fechas.")
    cols = [x for x in ["fecha_evaluacion", "nombre", "carrera", "riesgo", "nivel"] if x in df_panel.columns]
    recientes = df_panel.sort_values("fecha_evaluacion", ascending=False)[cols].head(7).copy()
    recientes = recientes.rename(columns={"fecha_evaluacion":"Fecha", "nombre":"Estudiante", "carrera":"Área de estudios", "riesgo":"Probabilidad estimada", "nivel":"Nivel"})
    if "Fecha" in recientes: recientes["Fecha"] = recientes["Fecha"].dt.strftime("%d/%m/%Y %H:%M").fillna("\u2014")
    if "Probabilidad estimada" in recientes: recientes["Probabilidad estimada"] = pd.to_numeric(recientes["Probabilidad estimada"], errors="coerce").map(lambda v: f"{v:.1%}" if pd.notna(v) else "\u2014")
    st.dataframe(recientes, width="stretch", hide_index=True)
    st.markdown('<div class="dashboard-note">Los niveles son una <b>estimación del modelo</b> para apoyar la revisión del orientador; no representan casos confirmados de abandono.</div>', unsafe_allow_html=True)

# --- PÁGINA DE FORMULARIO DE EVALUACIÓN ---
elif pagina == PAGINA_EVALUAR:
    st.title("📝 Evaluación de Riesgo de Abandono")
    st.caption("Completa la información personal y académica para estimar el nivel de riesgo.")

    st.session_state.setdefault("paso_formulario", 1)
    paso = st.session_state["paso_formulario"]
    st.progress(paso / 2, text=f"Paso {paso} de 2 · {'Datos personales' if paso == 1 else 'Rendimiento académico'}")
    datos_personales_guardados = st.session_state.get("datos_personales_formulario", {})
    datos_academicos_guardados = st.session_state.get("datos_academicos_formulario", {})

    with st.form("form_evaluacion"):
        if paso == 1:
            st.subheader("Datos personales")
            st.caption("Identificación y situación socioeconómica del estudiante.")
            col1, col2 = st.columns(2)
            with col1:
                dni = st.text_input("DNI del Estudiante", value=datos_personales_guardados.get("dni", ""), key="form_dni")
                edad = st.number_input("Edad al matricularse", 16, 60, int(datos_personales_guardados.get("edad", 18)), key="form_edad")
                area_opciones = list(MAPA_CARRERAS.keys())
                area_inicial = datos_personales_guardados.get("area", area_opciones[0])
                area = st.selectbox("Área de Estudios", area_opciones, index=area_opciones.index(area_inicial), key="form_area")
                becario = st.selectbox("¿Es becario?", ["No", "Sí"], index=["No", "Sí"].index(datos_personales_guardados.get("becario", "No")), key="form_becario")
                matricula = st.selectbox("¿Matrícula al día?", ["Sí", "No"], index=["Sí", "No"].index(datos_personales_guardados.get("matricula", "Sí")), key="form_matricula")
            with col2:
                nombre = st.text_input("Nombre Completo", value=datos_personales_guardados.get("nombre", ""), key="form_nombre")
                genero = st.selectbox("Género", ["Masculino", "Femenino"], index=["Masculino", "Femenino"].index(datos_personales_guardados.get("genero", "Masculino")), key="form_genero")
                deudor = st.selectbox("¿Tiene deudas?", ["No", "Sí"], index=["No", "Sí"].index(datos_personales_guardados.get("deudor", "No")), key="form_deudor")
                desplazado = st.selectbox("¿Es desplazado?", ["No", "Sí"], index=["No", "Sí"].index(datos_personales_guardados.get("desplazado", "No")), key="form_desplazado")
            continuar = st.form_submit_button(
                "Continuar al rendimiento académico  →",
                width="stretch"
            )
        else:
            st.subheader("Rendimiento académico")
            st.caption("Ingresa los datos de ambos semestres. Selecciona la pestaña correspondiente para completar cada sección.")
            semestre1, semestre2 = st.tabs(["Primer semestre", "Segundo semestre"])
            with semestre1:
                col1, col2, col3 = st.columns(3)
                cu1_matriculadas = col1.number_input("Asignaturas matriculadas", 0, 15, int(datos_academicos_guardados.get("cu1_matriculadas", 5)), key="form_cu1_matriculadas")
                cu1_aprobadas = col2.number_input("Asignaturas aprobadas", 0, 15, int(datos_academicos_guardados.get("cu1_aprobadas", 3)), key="form_cu1_aprobadas")
                cu1_nota = col3.number_input("Nota media [0-20]", 0.0, 20.0, float(datos_academicos_guardados.get("cu1_nota", 12.0)), key="form_cu1_nota")
            with semestre2:
                col1, col2, col3 = st.columns(3)
                cu2_matriculadas = col1.number_input("Asignaturas matriculadas", 0, 15, int(datos_academicos_guardados.get("cu2_matriculadas", 5)), key="form_cu2_matriculadas")
                cu2_aprobadas = col2.number_input("Asignaturas aprobadas", 0, 15, int(datos_academicos_guardados.get("cu2_aprobadas", 3)), key="form_cu2_aprobadas")
                cu2_nota = col3.number_input("Nota media [0-20]", 0.0, 20.0, float(datos_academicos_guardados.get("cu2_nota", 12.0)), key="form_cu2_nota")
            col_back, col_submit = st.columns([1, 2])
            volver = col_back.form_submit_button(
                "← Volver a datos personales",
                width="stretch"
            )
            calcular = col_submit.form_submit_button("Calcular Riesgo", width="stretch")

    if paso == 1 and continuar:
        if not st.session_state.get("form_dni", "").strip() or not st.session_state.get("form_nombre", "").strip():
            st.error("⚠️ DNI y Nombre son obligatorios antes de continuar.")
        else:
            st.session_state["datos_personales_formulario"] = {
                "dni": st.session_state["form_dni"],
                "nombre": st.session_state["form_nombre"],
                "edad": st.session_state["form_edad"],
                "genero": st.session_state["form_genero"],
                "area": st.session_state["form_area"],
                "becario": st.session_state["form_becario"],
                "deudor": st.session_state["form_deudor"],
                "matricula": st.session_state["form_matricula"],
                "desplazado": st.session_state["form_desplazado"]
            }
            st.session_state["paso_formulario"] = 2
            st.rerun()

    if paso == 2 and volver:
        st.session_state["datos_academicos_formulario"] = {
            "cu1_matriculadas": st.session_state["form_cu1_matriculadas"],
            "cu1_aprobadas": st.session_state["form_cu1_aprobadas"],
            "cu1_nota": st.session_state["form_cu1_nota"],
            "cu2_matriculadas": st.session_state["form_cu2_matriculadas"],
            "cu2_aprobadas": st.session_state["form_cu2_aprobadas"],
            "cu2_nota": st.session_state["form_cu2_nota"]
        }
        st.session_state["paso_formulario"] = 1
        st.rerun()

    if paso == 2 and calcular:
        datos_personales_guardados = st.session_state.get("datos_personales_formulario")
        if not datos_personales_guardados:
            st.error("Completa primero los datos personales para continuar.")
            st.session_state["paso_formulario"] = 1
        else:
            dni = datos_personales_guardados["dni"]
            nombre = datos_personales_guardados["nombre"]
            edad = datos_personales_guardados["edad"]
            genero = datos_personales_guardados["genero"]
            area = datos_personales_guardados["area"]
            becario = datos_personales_guardados["becario"]
            deudor = datos_personales_guardados["deudor"]
            matricula = datos_personales_guardados["matricula"]
            desplazado = datos_personales_guardados["desplazado"]
            cu1_matriculadas = st.session_state["form_cu1_matriculadas"]
            cu1_aprobadas = st.session_state["form_cu1_aprobadas"]
            cu1_nota = st.session_state["form_cu1_nota"]
            cu2_matriculadas = st.session_state["form_cu2_matriculadas"]
            cu2_aprobadas = st.session_state["form_cu2_aprobadas"]
            cu2_nota = st.session_state["form_cu2_nota"]

            datos = {
                'edad': edad, 'genero': genero, 'becario': becario,
                'deudor': deudor, 'matricula_al_dia': matricula, 'desplazado': desplazado,
                'area_estudios': area,
                'cu1_matriculadas': cu1_matriculadas, 'cu1_aprobadas': cu1_aprobadas, 'cu1_nota': cu1_nota,
                'cu2_matriculadas': cu2_matriculadas, 'cu2_aprobadas': cu2_aprobadas, 'cu2_nota': cu2_nota
            }

            prob, nivel = predecir_riesgo_abandono(datos)

            st.divider()
            st.subheader("Resultado de la evaluación")
            with st.container(border=True):
                col_r1, col_r2 = st.columns([1, 1.5], vertical_alignment="center")
                col_r1.metric("Probabilidad de abandono", f"{prob:.1%}")
                if nivel == "ALTO":
                    col_r2.markdown('<div class="risk-symbol">🔴</div>', unsafe_allow_html=True)
                    col_r2.error(f"RIESGO {nivel} · Se recomienda intervención prioritaria.")
                elif nivel == "MEDIO":
                    col_r2.markdown('<div class="risk-symbol">🟡</div>', unsafe_allow_html=True)
                    col_r2.warning(f"RIESGO {nivel} · Se recomienda seguimiento.")
                else:
                    col_r2.markdown('<div class="risk-symbol">🟢</div>', unsafe_allow_html=True)
                    col_r2.success(f"RIESGO {nivel} · Mantener el acompañamiento académico.")

            guardar_evaluacion(dni, nombre, area, prob, nivel)
            st.success("Evaluación guardada en el historial.")

# --- PÁGINA DE HISTORIAL ---
elif pagina == PAGINA_HISTORIAL:
    st.title("📋 Historial de Evaluaciones")
    st.caption("Consulta, corrige o elimina evaluaciones registradas.")
    mensaje_historial = st.session_state.pop("mensaje_historial", None)
    if mensaje_historial:
        st.success(mensaje_historial)
    if df_historial.empty:
        st.info("No hay evaluaciones registradas aún.")
    else:
        df = df_historial.copy()
        vista = df.rename(columns={
            "id": "ID",
            "dni": "DNI",
            "nombre": "Estudiante",
            "carrera": "Área de estudios",
            "fecha_evaluacion": "Fecha de evaluación",
            "riesgo": "Probabilidad estimada",
            "nivel": "Nivel de riesgo",
        })
        vista["Fecha de evaluación"] = pd.to_datetime(vista["Fecha de evaluación"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M").fillna("—")
        vista["Probabilidad estimada"] = pd.to_numeric(vista["Probabilidad estimada"], errors="coerce").map(lambda valor: f"{valor:.1%}" if pd.notna(valor) else "—")
        with st.container(border=True):
            st.subheader("Registros")
            fondo_tabla = "#172633" if st.session_state.get("modo_oscuro", False) else "#ffffff"
            texto_tabla = "#e6edf2" if st.session_state.get("modo_oscuro", False) else "#263b49"
            borde_tabla = "#2b4050" if st.session_state.get("modo_oscuro", False) else "#e2e9ec"
            tabla_estilizada = vista.style.set_properties(**{
                "background-color": fondo_tabla,
                "color": texto_tabla,
                "border-color": borde_tabla,
            })
            st.dataframe(tabla_estilizada, width="stretch", hide_index=True)

        st.subheader("Gestionar una evaluación")
        ids = df["id"].astype(int).tolist()
        registros = df.set_index("id").to_dict("index")
        def etiqueta_registro(evaluacion_id):
            registro = registros[evaluacion_id]
            fecha = pd.to_datetime(registro["fecha_evaluacion"], errors="coerce")
            fecha_txt = fecha.strftime("%d/%m/%Y") if pd.notna(fecha) else "Sin fecha"
            return f"#{evaluacion_id} · {registro['nombre']} · {registro['nivel']} · {fecha_txt}"

        llave_selector = "selector_crud_" + "_".join(map(str, ids))
        seleccion = st.selectbox("Selecciona un registro", ids, format_func=etiqueta_registro, key=llave_selector)
        registro = registros[seleccion]
        with st.container(border=True):
            st.caption("Los datos académicos de entrada no se guardan en el historial. Si cambias la probabilidad o el nivel, el modelo no vuelve a calcular el resultado.")
            with st.form(f"form_editar_{seleccion}"):
                st.markdown(f"**Editar evaluación #{seleccion}**")
                c1, c2 = st.columns(2)
                dni_editado = c1.text_input("DNI", value=str(registro.get("dni") or ""), key=f"dni_{seleccion}")
                nombre_editado = c2.text_input("Nombre del estudiante", value=str(registro.get("nombre") or ""), key=f"nombre_{seleccion}")
                carreras_editables = list(dict.fromkeys([*MAPA_CARRERAS.keys(), str(registro.get("carrera") or "Sin área")]))
                carrera_actual = str(registro.get("carrera") or "Sin área")
                carrera_editada = st.selectbox("Área de estudios", carreras_editables, index=carreras_editables.index(carrera_actual), key=f"carrera_{seleccion}")
                riesgo_actual = pd.to_numeric(registro.get("riesgo"), errors="coerce")
                riesgo_editado = st.number_input("Probabilidad estimada", min_value=0.0, max_value=1.0, value=float(riesgo_actual) if pd.notna(riesgo_actual) else 0.0, step=0.01, format="%.2f", key=f"riesgo_{seleccion}")
                niveles_editables = ["BAJO", "MEDIO", "ALTO"]
                nivel_actual = str(registro.get("nivel") or "MEDIO").upper()
                if nivel_actual not in niveles_editables:
                    niveles_editables.append(nivel_actual)
                nivel_editado = st.selectbox("Nivel de riesgo", niveles_editables, index=niveles_editables.index(nivel_actual), key=f"nivel_{seleccion}")
                guardar_cambios = st.form_submit_button("Guardar cambios", type="primary", width="stretch")
                if guardar_cambios:
                    if not dni_editado.strip() or not nombre_editado.strip():
                        st.error("El DNI y el nombre son obligatorios.")
                    else:
                        actualizado = actualizar_evaluacion(seleccion, dni_editado.strip(), nombre_editado.strip(), carrera_editada, riesgo_editado, nivel_editado)
                        if actualizado:
                            st.session_state["mensaje_historial"] = f"La evaluación #{seleccion} se actualizó."
                            st.rerun()
                        st.error("No se encontró el registro para actualizar.")

            with st.form(f"form_eliminar_{seleccion}"):
                confirmar_eliminacion = st.checkbox(f"Confirmo que quiero eliminar la evaluación #{seleccion}", key=f"confirmar_eliminar_{seleccion}")
                eliminar = st.form_submit_button("Eliminar evaluación", type="secondary", width="stretch")
                if eliminar:
                    if not confirmar_eliminacion:
                        st.error("Marca la confirmación para eliminar este registro.")
                    elif eliminar_evaluacion(seleccion):
                        st.session_state["mensaje_historial"] = f"La evaluación #{seleccion} se eliminó."
                        st.rerun()
                    else:
                        st.error("No se encontró el registro para eliminar.")
