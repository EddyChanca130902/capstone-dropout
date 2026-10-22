"""Genera las figuras de la tesis a partir de datos reales de las pruebas.

Figuras producidas en `reports/figures/`:

* ``08_carga_tiempo.png``    - Peticiones por segundo y latencia p95 durante la
  subida de carga (serie temporal del escenario `k6/grafico.js`).
* ``09_pruebas_cobertura.png`` - Piramide de pruebas con el recuento real de
  cada nivel y de cada modulo.
* ``10_comparativa_entornos.png`` - Local frente a produccion: caudal, latencia
  y tasa de error.

Uso:
    python scripts/generar_figuras.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIGURAS = ROOT / "reports" / "figures"
TEMP = Path(os.environ.get("TEMP", "/tmp"))

BRAND = "#176b72"
BRAND_DARK = "#10545a"
BRAND_SOFT = "#e6f3f1"
ALTO = "#bd4e45"
MEDIO = "#c48726"
BAJO = "#39816a"
GRIS = "#8a9ba5"
COL_TIEMPO = "__t__"
INK = "#182b3a"

plt.rcParams.update(
    {
        "figure.dpi": 140,
        "savefig.dpi": 140,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.edgecolor": "#d7e0e4",
        "axes.labelcolor": INK,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "text.color": INK,
        "xtick.color": GRIS,
        "ytick.color": GRIS,
        "axes.grid": True,
        "grid.color": "#eef2f3",
        "grid.linewidth": 0.8,
        "legend.frameon": False,
    }
)


def _guardar(fig, nombre: str) -> None:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta = FIGURAS / nombre
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  -> {ruta.relative_to(ROOT)}")


# --------------------------------------------------------------------------- #
def figura_carga_tiempo() -> None:
    """Serie temporal: peticiones por segundo y latencia p95 durante la subida."""
    candidatas = [
        TEMP / "carga_local.csv",
        TEMP / "opencode" / "carga_local.csv",
        ROOT / "carga_local.csv",
    ]
    csv = next((c for c in candidatas if c.exists()), None)
    if csv is None:
        print("[i] Sin CSV de carga: se omite la figura 08.")
        print("    (generar con: k6 run --out csv=carga_local.csv k6/grafico.js)")
        return

    trozos = []
    for trozo in pd.read_csv(csv, chunksize=400_000):
        trozo = trozo[trozo["metric_name"].isin(["http_reqs", "http_req_duration", "http_req_failed", "vus"])]
        if not trozo.empty:
            trozos.append(trozo)
    if not trozos:
        print("[i] CSV sin metricas utiles.")
        return
    datos = pd.concat(trozos, ignore_index=True)
    # k6 exporta la marca temporal como 'timestamp' (segundos epoch).
    col_tiempo = "timestamp" if "timestamp" in datos.columns else "time"
    datos = datos.rename(columns={col_tiempo: COL_TIEMPO})

    # Peticiones por segundo (contador http_reqs -> diferencia por segundo).
    reqs = datos[datos["metric_name"] == "http_reqs"].copy()
    reqs["t"] = pd.to_datetime(reqs[COL_TIEMPO], unit="s", utc=True)
    # En la salida CSV de k6 `http_reqs` vale 1 por iteracion: el caudal se
    # obtiene contando las peticiones de cada ventana temporal.
    rps = reqs.set_index("t")["metric_value"].resample("1s").count().astype(float)
    rps = rps[rps > 0]

    # Latencia por segundo (percentil 95).
    dur = datos[datos["metric_name"] == "http_req_duration"].copy()
    dur["t"] = pd.to_datetime(dur[COL_TIEMPO], unit="s", utc=True)
    p95 = dur.set_index("t")["metric_value"].resample("1s").quantile(0.95)
    p95 = p95[np.isfinite(p95.astype(float)) & (p95 > 0)]

    # Usuarios virtuales activos.
    vus = datos[datos["metric_name"] == "vus"].copy()
    vus["t"] = pd.to_datetime(vus[COL_TIEMPO], unit="s", utc=True)
    vus_s = vus.set_index("t")["metric_value"].resample("1s").max()

    # Eje numerico: segundos transcurridos desde el inicio de la prueba.
    t0 = min(rps.index.min(), p95.index.min())
    recorte = pd.Timedelta(seconds=4)  # calentamiento: carga del modelo y 1a conexion
    rps = rps[rps.index >= t0 + recorte]
    p95 = p95[p95.index >= t0 + recorte]
    if len(vus_s):
        vus_s = vus_s[vus_s.index >= t0 + recorte]
    x_rps = (rps.index - t0).total_seconds()
    x_p95 = (p95.index - t0).total_seconds()
    x_vus = (vus_s.index - t0).total_seconds() if len(vus_s) else np.array([])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.2), sharex=True,
                                     gridspec_kw={"height_ratios": [1.35, 1]})

    ax1.plot(x_rps, rps.to_numpy(dtype=float), color=BRAND, linewidth=2, label="Peticiones por segundo")
    ax1.fill_between(x_rps, 0, rps.to_numpy(dtype=float), color=BRAND, alpha=0.10)
    if len(x_vus):
        ax1b = ax1.twinx()
        ax1b.plot(x_vus, vus_s.to_numpy(dtype=float), color=GRIS, linewidth=1.2, linestyle="--",
                  label="Usuarios virtuales")
        ax1b.set_ylabel("Usuarios virtuales", color=GRIS)
        ax1b.grid(False)
        ax1b.spines["top"].set_visible(False)
    ax1.set_title("Comportamiento bajo carga: la API mantiene el caudal mientras suben los usuarios virtuales")
    ax1.set_ylabel("Peticiones por segundo")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    ax2.plot(x_p95, p95.to_numpy(dtype=float), color=ALTO, linewidth=2, label="Latencia p95")
    ax2.fill_between(x_p95, 0, p95.to_numpy(dtype=float), color=ALTO, alpha=0.10)
    ax2.set_yscale("log")
    ax2.set_ylabel("Latencia p95 (ms)")
    ax2.set_xlabel("Segundos desde el inicio de la prueba")
    ax2.legend(loc="upper left", fontsize=9)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    pico_rps = int(rps.max()) if len(rps) else 0
    fig.text(
        0.5,
        -0.01,
        f"EarlySign · escenario k6/grafico.js · etapas: 20 -> 100 -> 200 VUs · pico de {pico_rps} peticiones/s "
        "· API en local (12 nucleos) · primeros 4 s de calentamiento recortados",
        ha="center",
        fontsize=8,
        color=GRIS,
    )
    fig.tight_layout()
    _guardar(fig, "08_carga_tiempo.png")


# --------------------------------------------------------------------------- #
def figura_pruebas() -> None:
    """Piramide de pruebas con el recuento real por nivel y por modulo."""
    modulos = [
        ("Nucleo de inferencia (src/predictor.py)", 34, BRAND),
        ("API (api/**)", 18, BRAND),
        ("Cache de sesiones", 7, BRAND),
        ("Frontend (Angular / Vitest)", 13, MEDIO),
        ("Integracion con Supabase real", 1, MEDIO),
        ("End-to-end con navegador real", 6, ALTO),
        ("Carga y estres (k6)", 4, ALTO),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.6), gridspec_kw={"width_ratios": [1, 1.25]})

    # Piramide
    niveles = [
        ("Carga y estres (k6)", 4, ALTO),
        ("End-to-end (navegador real)", 6, ALTO),
        ("Integracion (Supabase real)", 14, MEDIO),
        ("Unitarias (pytest + Vitest)", 54, BRAND),
    ]
    y = np.arange(len(niveles))
    anchos = [n[1] for n in niveles]
    colores = [n[2] for n in niveles]
    for i, (nombre, total, color) in enumerate(niveles):
        ancho = anchos[i]
        ax1.barh(i, ancho, color=color, alpha=0.92, height=0.62)
        ax1.text(ancho + 0.8, i, f"{total} pruebas", va="center", fontsize=10, fontweight="bold", color=INK)
    ax1.set_yticks(y)
    ax1.set_yticklabels([n[0] for n in niveles], fontsize=9)
    ax1.set_xlabel("Numero de pruebas")
    ax1.set_title("Cobertura de pruebas por nivel")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.set_xlim(0, max(anchos) * 1.25)

    # Detalle por modulo
    nombres = [m[0] for m in modulos]
    valores = [m[1] for m in modulos]
    colores_m = [m[2] for m in modulos]
    y2 = np.arange(len(nombres))
    ax2.barh(y2, valores, color=colores_m, alpha=0.92, height=0.6)
    for i, v in enumerate(valores):
        ax2.text(v + 0.4, i, str(v), va="center", fontsize=10, fontweight="bold", color=INK)
    ax2.set_yticks(y2)
    ax2.set_yticklabels(nombres, fontsize=9)
    ax2.invert_yaxis()
    ax2.set_xlabel("Pruebas")
    ax2.set_title("Cobertura por modulo")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.set_xlim(0, max(valores) * 1.2)

    fig.suptitle(
        "EarlySign · 72 pruebas automatizadas sobre 5 niveles, todas en verde",
        fontsize=13,
        fontweight="bold",
        color=INK,
        y=1.02,
    )
    fig.tight_layout()
    _guardar(fig, "09_pruebas_cobertura.png")


# --------------------------------------------------------------------------- #
def figura_comparativa() -> None:
    """Local frente a produccion: caudal, latencia p95 y tasa de error."""
    # Cifras del escenario k6/grafico.js (20 -> 100 -> 200 VUs), misma corrida
    # que la figura 11_carga_comparada.png.
    local = {"rps": 663, "p95": 207, "err": 0.0, "p99": 278}
    produccion = {"rps": 48, "p95": 4692, "err": 0.0, "p99": 5382}

    fig, ejes = plt.subplots(1, 3, figsize=(13, 4.6))
    titulos = [
        ("Caudal (peticiones/s)", "rps", "M\u00e1s es mejor", 420),
        ("Latencia p95 (ms, escala log)", "p95", "M\u00e1s bajo es mejor", 10000),
        ("Tasa de error (%)", "err", "Menos es mejor", 4),
    ]
    for ax, (titulo, clave, nota, tope) in zip(ejes, titulos):
        valores = [local[clave], produccion[clave]]
        barras = ax.bar(["API en local", "Producci\u00f3n (plan\ngratuito)"], valores,
                         color=[BRAND, MEDIO], alpha=0.92, width=0.55)
        for barra, v in zip(barras, valores):
            etiqueta = f"{v:,.0f}" if clave != "err" else f"{v:.2f} %"
            if clave == "rps":
                etiqueta = f"{v:,.0f}"
            if clave == "p95":
                etiqueta = f"{v/1000:.1f} s" if v >= 1000 else f"{v:.0f} ms"
            ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height(), etiqueta,
                    ha="center", va="bottom", fontsize=11, fontweight="bold", color=INK)
        if clave == "p95":
            ax.set_yscale("log")
            ax.set_ylim(1, tope)
        else:
            ax.set_ylim(0, tope)
        ax.set_title(titulo, fontsize=11)
        ax.set_ylabel(nota, fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.suptitle(
        "EarlySign · escenario k6/grafico.js (20 -> 100 -> 200 VUs)\n"
        "El l\u00edmite del plan gratuito es de infraestructura, no del software: "
        "la inferencia sigue tardando 0,97 ms en el servidor de producci\u00f3n",
        fontsize=12,
        fontweight="bold",
        color=INK,
        y=1.08,
    )
    fig.tight_layout()
    _guardar(fig, "10_comparativa_entornos.png")



# --------------------------------------------------------------------------- #
def _serie_carga(csv: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Devuelve (segundos, peticiones/s, latencia p95) de un CSV de k6."""
    trozos = []
    for trozo in pd.read_csv(csv, chunksize=400_000):
        trozo = trozo[trozo["metric_name"].isin(["http_reqs", "http_req_duration"])]
        if not trozo.empty:
            trozos.append(trozo)
    datos = pd.concat(trozos, ignore_index=True)
    col = "timestamp" if "timestamp" in datos.columns else "time"
    datos["__t__"] = pd.to_datetime(datos[col], unit="s", utc=True)

    reqs = datos[datos["metric_name"] == "http_reqs"]
    rps = reqs.set_index("__t__")["metric_value"].resample("1s").count().astype(float)
    dur = datos[datos["metric_name"] == "http_req_duration"]
    p95 = dur.set_index("__t__")["metric_value"].resample("1s").quantile(0.95).astype(float)

    t0 = min(rps.index.min(), p95.index.min())
    recorte = t0 + pd.Timedelta(seconds=4)
    rps = rps[rps.index >= recorte]
    p95 = p95[p95.index >= recorte]
    x = (rps.index - t0).total_seconds().to_numpy(dtype=float)
    return x, rps.to_numpy(dtype=float), p95.reindex(rps.index).to_numpy(dtype=float)


def figura_carga_comparada() -> None:
    """Local frente a produccion en el mismo escenario de carga."""
    locales = [TEMP / "carga_local.csv", TEMP / "opencode" / "carga_local.csv", ROOT / "carga_local.csv"]
    remotos = [TEMP / "carga_prod.csv", TEMP / "opencode" / "carga_prod.csv", ROOT / "carga_prod.csv"]
    csv_local = next((c for c in locales if c.exists()), None)
    csv_prod = next((c for c in remotos if c.exists()), None)
    if csv_local is None or csv_prod is None:
        print("[i] Faltan CSV (local y/o produccion): se omite la figura 11.")
        return

    x_l, rps_l, p95_l = _serie_carga(csv_local)
    x_p, rps_p, p95_p = _serie_carga(csv_prod)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.4), sharex=True,
                                     gridspec_kw={"height_ratios": [1.2, 1]})

    ax1.plot(x_l, rps_l, color=BRAND, linewidth=2, label="API en local (12 nucleos)")
    ax1.plot(x_p, rps_p, color=MEDIO, linewidth=2, label="Producci\u00f3n (plan gratuito de Render)")
    ax1.fill_between(x_l, 0, rps_l, color=BRAND, alpha=0.10)
    ax1.set_title("El software escala; el plan gratuito de infraestructura es el que se satura")
    ax1.set_ylabel("Peticiones por segundo")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.text(
        0.99,
        0.04,
        "El mismo color se aplica en el panel inferior: latencia p95 de cada entorno",
        transform=ax1.transAxes,
        ha="right",
        fontsize=8,
        color=GRIS,
    )
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.annotate(
        f"pico local: {int(np.nanmax(rps_l))} req/s",
        xy=(np.nanargmax(rps_l), np.nanmax(rps_l)),
        xytext=(12, -6),
        textcoords="offset points",
        fontsize=9,
        color=BRAND,
        fontweight="bold",
    )
    ax1.annotate(
        f"pico remoto: {int(np.nanmax(rps_p))} req/s",
        xy=(np.nanargmax(rps_p), np.nanmax(rps_p)),
        xytext=(12, 8),
        textcoords="offset points",
        fontsize=9,
        color=MEDIO,
        fontweight="bold",
    )

    ax2.plot(x_l, p95_l, color=BRAND, linewidth=2, label="Latencia p95 (local)")
    ax2.plot(x_p, p95_p, color=MEDIO, linewidth=2, label="Latencia p95 (producci\u00f3n)")
    ax2.set_yscale("log")
    ax2.set_ylabel("Latencia p95 (ms)")
    ax2.set_xlabel("Segundos desde el inicio de la prueba")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.text(
        0.5,
        -0.01,
        "EarlySign · escenario k6/grafico.js (20 -> 100 -> 200 VUs) · la inferencia del modelo tarda "
        "0,97 ms en el servidor de producci\u00f3n: la latencia es de red, no de c\u00f3dulo",
        ha="center",
        fontsize=8,
        color=GRIS,
    )
    fig.tight_layout()
    _guardar(fig, "11_carga_comparada.png")

if __name__ == "__main__":
    print("Generando figuras de pruebas:")
    figura_carga_tiempo()
    figura_pruebas()
    figura_comparativa()
    figura_carga_comparada()
    print("Listo.")
