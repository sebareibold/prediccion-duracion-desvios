"""Genera los gráficos (PDF vectorial) de la presentación formal.

Corre el notebook de marimo (notebooks/01_exploracion_y_modelos.py) para armar el corpus con los
mismos pasos y modelos, calcula las predicciones fuera de muestra y dibuja cada figura en esta
carpeta. Los números intermedios se guardan en privado/cache/ (no se sube al repo, porque sale del
dataset de Tecfield); con --rehacer se vuelven a calcular.

Uso, desde la raíz del proyecto:
    .venv/Scripts/python.exe reports/presentacion-formal/figuras/generar_figuras.py [--rehacer]
"""

import pickle
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
CACHE = RAIZ / "privado" / "cache" / "figuras-presentacion.pkl"

# Paleta de la presentación (misma que define main.tex).
AZUL = "#0A2A5E"
AZUL_MEDIO = "#2F5F9E"
CELESTE = "#8FB3DE"
GRIS = "#9AA3AF"
GRIS_OSCURO = "#4B5563"
ROJO = "#B23A3A"
AMBAR = "#C27C0E"
VERDE = "#2E7D4F"

MODELOS = ["Mediana (baseline)", "Árbol de decisión", "Random Forest", "XGBoost"]
COLORES = {
    "Mediana (baseline)": GRIS,
    "Árbol de decisión": CELESTE,
    "Random Forest": AZUL_MEDIO,
    "XGBoost": AZUL,
}
NOMBRE_CORTO = {
    "Mediana (baseline)": "Mediana",
    "Árbol de decisión": "Árbol",
    "Random Forest": "Random Forest",
    "XGBoost": "XGBoost",
}
NOMBRE_ATRIBUTO = {
    "tipoHDR": "Tipo de hoja",
    "distancia_m": "Distancia a la ruta",
    "lat": "Latitud",
    "lon": "Longitud",
    "velocidad": "Velocidad",
    "hora": "Hora",
    "obra_id": "Obra",
    "dia_semana": "Día de la semana",
    "km_ida": "Km del recorrido",
    "min_ida": "Min. del recorrido",
    "tipoVehiculo": "Tipo de vehículo",
    "pasajeros": "Pasajeros",
    "plazas": "Plazas",
    "ruta_cercana": "Ruta cercana",
    "franja": "Franja horaria",
    "velocidad_vacia": "Velocidad vacía",
    "hoja_vigente": "Hoja vigente",
    "gps_previos": "GPS previos",
    "vel_media_previa": "Vel. media previa",
    "vel_ultima": "Última velocidad",
    "min_desde_ultimo_gps": "Min. desde último GPS",
    "desplaz_previo_m": "Desplaz. previo",
    "rumbo_previo": "Rumbo previo",
}


def coma(x, decimales=1):
    """Número con coma decimal y punto de miles (formato argentino)."""
    texto = f"{x:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


# --------------------------------------------------------------------------- datos
def calcular_datos():
    """Corre el notebook y devuelve un diccionario con todo lo que usan los gráficos."""
    sys.path.insert(0, str(RAIZ / "notebooks"))
    from importlib import import_module

    notebook = import_module("01_exploracion_y_modelos")
    print("Corriendo el notebook (carga los JSON y entrena los modelos)...", flush=True)
    _, defs = notebook.app.run()

    corpus = defs["corpus"]
    matriz = defs["matriz"]
    crear_modelos = defs["crear_modelos"]
    evaluar = defs["evaluar"]
    atributos_por_grupo = defs["ATRIBUTOS"]
    from sklearn.model_selection import GroupKFold

    atributos = [a for lista in atributos_por_grupo.values() for a in lista]
    X = matriz(atributos)
    y = corpus["y"].to_numpy()
    vehiculos = corpus["flota"].to_numpy()

    # Predicciones fuera de muestra, igual que evaluar(), pero guardando cada predicción y el
    # MAE de cada partición.
    print("Validación cruzada con predicciones fuera de muestra...", flush=True)
    pred = {m: np.empty_like(y, dtype=float) for m in MODELOS}
    mae_particion = {m: [] for m in MODELOS}
    for entrenamiento, prueba in GroupKFold(n_splits=5).split(X, y, vehiculos):
        pred[MODELOS[0]][prueba] = np.median(y[entrenamiento])
        modelos = crear_modelos()
        for nombre, modelo in modelos.items():
            modelo.fit(X[entrenamiento], np.log1p(y[entrenamiento]))
            pred[nombre][prueba] = np.expm1(modelo.predict(X[prueba]))
        for nombre in MODELOS:
            mae_particion[nombre].append(np.abs(pred[nombre][prueba] - y[prueba]).mean() / 60)

    # Importancia de variables: cada modelo entrenado con todo el corpus (como en el notebook).
    importancias = {}
    for nombre, modelo in crear_modelos().items():
        modelo.fit(X, np.log1p(y))
        valores = modelo.feature_importances_ / modelo.feature_importances_.sum()
        importancias[nombre] = dict(zip(atributos, map(float, valores)))

    # Ablación: Random Forest sumando grupos de atributos.
    print("Ablación por grupos de atributos...", flush=True)
    ablacion = []
    acumulados = []
    for grupo, lista in atributos_por_grupo.items():
        acumulados = acumulados + lista
        fila = evaluar(acumulados, solo="Random Forest").row(1, named=True)
        ablacion.append((grupo, fila["MAE (min)"], fila["RMSE (min)"]))

    columnas = ["y", "tipoHDR", "hora", "dia_semana", "gps_previos", "distancia_m", "lat", "lon"]
    return {
        "corpus": corpus.select(columnas).to_dict(as_series=False),
        "resumen": defs["resumen_corpus"],
        "tope_y": defs["tope"]["y"].to_list(),
        "pred": pred,
        "mae_particion": mae_particion,
        "importancias": importancias,
        "grupos": {a: g for g, lista in atributos_por_grupo.items() for a in lista},
        "ablacion": ablacion,
    }


def cargar_datos(rehacer):
    if CACHE.exists() and not rehacer:
        return pickle.loads(CACHE.read_bytes())
    datos = calcular_datos()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(pickle.dumps(datos))
    return datos


# ------------------------------------------------------------------------ gráficos
CM = 1 / 2.54


def estilo():
    """Tipografía (Source Sans 3, la misma de las láminas) y ejes sobrios."""
    from matplotlib import font_manager

    for carpeta in [Path("C:/Program Files/MiKTeX/fonts/opentype/adobe/sourcesans")]:
        for archivo in carpeta.glob("SourceSans3-*.otf"):
            font_manager.fontManager.addfont(str(archivo))
    plt.rcParams.update(
        {
            "font.family": "Source Sans 3",
            "font.size": 8,
            "axes.titlesize": 8.5,
            "axes.titleweight": "semibold",
            "axes.labelsize": 8,
            "axes.labelcolor": GRIS_OSCURO,
            "axes.edgecolor": GRIS,
            "axes.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": "#E5E7EB",
            "grid.linewidth": 0.5,
            "axes.axisbelow": True,
            "xtick.color": GRIS_OSCURO,
            "ytick.color": GRIS_OSCURO,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "legend.fontsize": 7.5,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "axes.formatter.use_locale": False,
        }
    )


def miles(x, _=None):
    return coma(x, 0)


def guardar(fig, nombre):
    fig.savefig(AQUI / f"{nombre}.pdf", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("  ", nombre)


def fig_embudo(d):
    r = d["resumen"]
    pasos = [
        ("Desvíos registrados", 0, r["eventos"], GRIS, coma(r["eventos"], 0)),
        ("Repetidos", None, r["repetidos"], GRIS, "−" + coma(r["repetidos"], 0)),
        ("Sin duración medible", None, r["una_lectura_o_cero"], GRIS,
         "−" + coma(r["una_lectura_o_cero"], 0)),
        ("Cortados a las 4 h (aparte)", None, r["tope"], AMBAR, "−" + coma(r["tope"], 0)),
        ("Corpus final", 0, r["corpus"], AZUL, coma(r["corpus"], 0)),
    ]
    fig, ax = plt.subplots(figsize=(9.2 * CM, 4.0 * CM))
    restante = r["eventos"]
    for i, (rotulo, inicio, ancho, color, texto) in enumerate(pasos):
        if inicio is None:
            restante -= ancho
            inicio = restante
        ax.barh(i, ancho, left=inicio, color=color, height=0.62)
        ax.text(inicio + ancho + 400, i, texto, va="center", fontsize=7.5, color=GRIS_OSCURO,
                fontweight="semibold" if color == AZUL else "normal")
    ax.set_yticks(range(len(pasos)), [p[0] for p in pasos])
    ax.invert_yaxis()
    ax.set_xlim(0, r["eventos"] * 1.17)
    ax.xaxis.set_major_formatter(FuncFormatter(miles))
    ax.set_xlabel("desvíos")
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    guardar(fig, "fig-embudo")


def fig_duracion(d):
    y = np.array(d["corpus"]["y"]) / 60
    mediana, p90 = np.median(y), np.quantile(y, 0.9)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14.2 * CM, 4.0 * CM), gridspec_kw={"wspace": 0.28})
    a1.hist(y, bins=np.arange(0, 244, 4), color=AZUL_MEDIO, edgecolor="white", linewidth=0.3)
    a1.set_xlim(0, 240)
    a1.set_xticks(range(0, 241, 30))
    a1.set_xlabel("duración (minutos)")
    a1.set_ylabel("desvíos")
    a1.yaxis.set_major_formatter(FuncFormatter(miles))
    a1.set_title("Duración de los desvíos", loc="left")
    a2.hist(y, bins=np.logspace(np.log10(0.1), np.log10(240), 26),
            color=AZUL_MEDIO, edgecolor="white", linewidth=0.3)
    a2.set_xscale("log")
    a2.set_xticks([0.1, 1, 5, 20, 60, 240], ["0,1", "1", "5", "20", "60", "240"])
    a2.set_xlabel("duración (minutos, escala log.)")
    a2.set_ylabel("desvíos")
    a2.yaxis.set_major_formatter(FuncFormatter(miles))
    a2.set_title("La misma duración, en escala logarítmica", loc="left")
    for ax in (a1, a2):
        ax.axvline(mediana, color=AMBAR, lw=0.9, ls="--")
        ax.axvline(p90, color=ROJO, lw=0.9, ls="--")
        ax.text(0.98, 0.95, f"mediana {coma(mediana)} min\npercentil 90: {coma(p90, 0)} min",
                transform=ax.transAxes, ha="right", va="top", fontsize=7, color=GRIS_OSCURO,
                bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": "#E5E7EB", "lw": 0.5})
    guardar(fig, "fig-duracion")


def fig_tipohdr(d):
    y = np.array(d["corpus"]["y"]) / 60
    def nombre(t):
        return "Sin informar" if t is None else t.capitalize()

    tipos = np.array([nombre(t) for t in d["corpus"]["tipoHDR"]], dtype=object)
    valores, cuentas = np.unique(tipos, return_counts=True)
    orden = [v for _, v in sorted(zip(-cuentas, valores)) if v != "Sin informar"][:4]
    orden = ["Sin informar"] + orden
    fig, ax = plt.subplots(figsize=(7.0 * CM, 4.4 * CM))
    datos = [y[tipos == v] for v in orden]
    caja = ax.boxplot(datos, orientation="horizontal", widths=0.55, showfliers=False,
                      patch_artist=True, medianprops={"color": AMBAR, "lw": 1.4},
                      whiskerprops={"color": GRIS, "lw": 0.7}, capprops={"color": GRIS, "lw": 0.7})
    for i, parche in enumerate(caja["boxes"]):
        parche.set(facecolor=GRIS if i == 0 else CELESTE, edgecolor="none")
    ax.set_xscale("log")
    ax.set_xticks([0.5, 2, 5, 20, 60, 240], ["0,5", "2", "5", "20", "60", "240"])
    etiquetas = [f"{v}\nn = {coma(len(x), 0)}" for v, x in zip(orden, datos)]
    ax.set_yticks(range(1, len(orden) + 1), etiquetas, fontsize=7)
    for i, x in enumerate(datos, start=1):
        m = np.median(x)
        print(f"     mediana {orden[i - 1]}: {m:.1f} min")
        ax.text(m, i + 0.33, f"{coma(m, 0)}", ha="center", va="bottom", fontsize=6.8, color=AMBAR,
                fontweight="semibold")
    ax.set_xlabel("duración (minutos, escala log.)")
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    guardar(fig, "fig-tipohdr")


def fig_hora(d):
    y = np.array(d["corpus"]["y"]) / 60
    hora = np.array(d["corpus"]["hora"])
    horas = np.arange(24)
    n = np.array([(hora == h).sum() for h in horas])
    med = np.array([np.median(y[hora == h]) if (hora == h).any() else np.nan for h in horas])
    fig, ax = plt.subplots(figsize=(7.0 * CM, 4.4 * CM))
    ax.bar(horas, n, color=CELESTE, width=0.8, label="desvíos")
    ax.set_xlabel("hora de \u2009T\u2080 (Argentina)")
    ax.set_ylabel("desvíos")
    ax.set_xticks(range(0, 24, 3))
    ax.yaxis.set_major_formatter(FuncFormatter(miles))
    ax2 = ax.twinx()
    ax2.plot(horas, med, color=AZUL, lw=1.3, marker="o", ms=2.4, label="duración mediana")
    ax2.set_ylabel("duración mediana (min)", color=AZUL)
    ax2.tick_params(axis="y", colors=AZUL)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(AZUL)
    ax2.grid(False)
    ax2.set_ylim(0, np.nanmax(med) * 1.35)
    ax.set_ylim(0, n.max() * 1.35)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", ncols=2)
    guardar(fig, "fig-hora")


def metricas(d):
    y = np.array(d["corpus"]["y"])
    filas = {}
    for m in MODELOS:
        e = np.abs(d["pred"][m] - y) / 60
        filas[m] = {"MAE": e.mean(), "RMSE": np.sqrt((e**2).mean()), "mediano": np.median(e)}
    return filas


def fig_metricas(d):
    met = metricas(d)
    claves = [("MAE", "MAE"), ("RMSE", "RMSE"), ("mediano", "Error mediano")]
    fig, ax = plt.subplots(figsize=(8.4 * CM, 5.0 * CM))
    ancho = 0.2
    for j, m in enumerate(MODELOS):
        xs = np.arange(len(claves)) + (j - 1.5) * ancho
        vals = [met[m][k] for k, _ in claves]
        ax.bar(xs, vals, width=ancho * 0.92, color=COLORES[m], label=NOMBRE_CORTO[m])
        for x, v in zip(xs, vals):
            ax.text(x, v + 0.8, coma(v), ha="center", va="bottom", fontsize=6, color=GRIS_OSCURO,
                    rotation=90)
    ax.set_xticks(range(len(claves)), [c[1] for c in claves])
    ax.set_ylabel("minutos")
    ax.set_ylim(0, max(met[MODELOS[0]]["RMSE"], 1) * 1.22)
    ax.legend(ncols=4, loc="upper left", bbox_to_anchor=(0, 1.13), handlelength=1, columnspacing=1)
    ax.tick_params(axis="x", length=0)
    guardar(fig, "fig-metricas")


def fig_particiones(d):
    fig, ax = plt.subplots(figsize=(7.0 * CM, 4.8 * CM))
    for i, m in enumerate(MODELOS):
        vals = np.array(d["mae_particion"][m])
        ax.scatter(np.full(len(vals), i) + np.linspace(-0.12, 0.12, len(vals)), vals, s=14,
                   color=COLORES[m], edgecolor="white", linewidth=0.4, zorder=3)
        ax.plot([i - 0.25, i + 0.25], [vals.mean()] * 2, color=GRIS_OSCURO, lw=1.1)
        ax.text(i + 0.28, vals.mean(), coma(vals.mean()), va="center", fontsize=7, color=GRIS_OSCURO)
    nombres = {**NOMBRE_CORTO, "Random Forest": "Random\nForest"}
    ax.set_xticks(range(len(MODELOS)), [nombres[m] for m in MODELOS])
    ax.set_xlim(-0.5, len(MODELOS) - 0.3)
    ax.set_ylabel("MAE por partición (min)")
    ax.tick_params(axis="x", length=0)
    guardar(fig, "fig-particiones")


def fig_error_por_duracion(d):
    y = np.array(d["corpus"]["y"]) / 60
    cortes = [0, 5, 15, 30, 60, 120, 240]
    rotulos = ["< 5", "5–15", "15–30", "30–60", "60–120", "120–240"]
    tramo = np.digitize(y, cortes[1:-1])
    fig, ax = plt.subplots(figsize=(8.4 * CM, 5.0 * CM))
    for m in MODELOS:
        e = np.abs(d["pred"][m] / 60 - y)
        mae = [e[tramo == k].mean() for k in range(len(rotulos))]
        ax.plot(range(len(rotulos)), mae, marker="o", ms=3, lw=1.3, color=COLORES[m],
                label=NOMBRE_CORTO[m], ls="--" if m == MODELOS[0] else "-")
    n = [(tramo == k).sum() for k in range(len(rotulos))]
    ax.set_xticks(range(len(rotulos)),
                  [f"{r}\n{coma(100 * c / len(y), 0)} %" for r, c in zip(rotulos, n)])
    ax.set_xlabel("duración real del desvío (min) · % de los eventos")
    ax.set_ylabel("MAE del tramo (min)")
    ax.legend(ncols=2, loc="upper left")
    ax.set_ylim(bottom=0)
    guardar(fig, "fig-error-por-duracion")


def fig_real_vs_pred(d):
    y = np.array(d["corpus"]["y"]) / 60
    p = d["pred"]["Random Forest"] / 60
    fig, ax = plt.subplots(figsize=(6.0 * CM, 5.4 * CM))
    lo, hi = 0.05, 240
    hb = ax.hexbin(np.clip(y, lo, hi), np.clip(p, lo, hi), xscale="log", yscale="log", gridsize=34,
                   bins="log", cmap="Blues", mincnt=1, linewidths=0.1, extent=(np.log10(lo),
                   np.log10(hi), np.log10(lo), np.log10(hi)))
    ax.plot([lo, hi], [lo, hi], color=ROJO, lw=0.9, ls="--", label="predicción perfecta")
    ticks = [0.1, 1, 5, 20, 60, 240]
    nombres = ["0,1", "1", "5", "20", "60", "240"]
    ax.set_xticks(ticks, nombres)
    ax.set_yticks(ticks, nombres)
    ax.set_xlabel("duración real (min)")
    ax.set_ylabel("predicción Random Forest (min)")
    ax.grid(False)
    ax.legend(loc="upper left")
    barra = fig.colorbar(hb, ax=ax, shrink=0.8, pad=0.03)
    barra.set_label("desvíos")
    barra.outline.set_visible(False)
    barra.ax.tick_params(labelsize=6.5)
    guardar(fig, "fig-real-vs-pred")


def fig_importancia(d):
    imp = d["importancias"]
    modelos = ["Árbol de decisión", "Random Forest", "XGBoost"]
    promedio = {a: np.mean([imp[m][a] for m in modelos]) for a in imp["Random Forest"]}
    top = sorted(promedio, key=promedio.get, reverse=True)[:7]
    fig, ax = plt.subplots(figsize=(8.6 * CM, 5.6 * CM))
    alto = 0.26
    for j, m in enumerate(modelos):
        ys = np.arange(len(top)) + (j - 1) * alto
        vals = [imp[m][a] * 100 for a in top]
        ax.barh(ys, vals, height=alto * 0.9, color=COLORES[m], label=NOMBRE_CORTO[m])
        for yy, v in zip(ys, vals):
            if v >= 10:
                ax.text(v + 0.6, yy, f"{coma(v, 0)} %", va="center", fontsize=6, color=GRIS_OSCURO)
    ax.set_yticks(range(len(top)), [NOMBRE_ATRIBUTO.get(a, a) for a in top])
    ax.invert_yaxis()
    ax.set_xlabel("importancia (% del total de cada modelo)")
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="lower right")
    guardar(fig, "fig-importancia")


def fig_importancia_grupos(d):
    imp, grupos = d["importancias"], d["grupos"]
    modelos = ["Árbol de decisión", "Random Forest", "XGBoost"]
    nombres_grupo = ["Primer ping", "Hoja de ruta", "Rastreo previo"]
    colores = [AZUL_MEDIO, CELESTE, AMBAR]
    fig, ax = plt.subplots(figsize=(5.4 * CM, 3.6 * CM))
    for i, m in enumerate(modelos):
        izq = 0
        for g, c in zip(nombres_grupo, colores):
            v = 100 * sum(val for a, val in imp[m].items() if grupos[a] == g)
            ax.barh(i, v, left=izq, color=c, height=0.6, label=g if i == 0 else None)
            if v >= 6:
                ax.text(izq + v / 2, i, f"{coma(v, 0)}", ha="center", va="center", fontsize=6.5,
                        color="white" if c != CELESTE else AZUL)
            izq += v
    ax.set_yticks(range(len(modelos)), [NOMBRE_CORTO[m] for m in modelos])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("% de la importancia")
    ax.grid(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(ncols=3, loc="upper left", bbox_to_anchor=(-0.32, 1.28), handlelength=0.8,
              columnspacing=0.8, fontsize=6.5)
    guardar(fig, "fig-importancia-grupos")


def fig_ablacion(d):
    base = metricas(d)[MODELOS[0]]["MAE"]
    rotulos = ["Primer ping", "+ Hoja de ruta", "+ Rastreo previo"]
    vals = [fila[1] for fila in d["ablacion"]]
    fig, ax = plt.subplots(figsize=(6.6 * CM, 4.8 * CM))
    ax.bar(range(3), vals, color=[CELESTE, AZUL_MEDIO, AZUL_MEDIO], width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v - 0.8, f"{coma(v)}", ha="center", va="top", fontsize=8.5, color="white",
                fontweight="semibold")
        ax.text(i, v - 4.0, f"{coma(100 * (1 - v / base), 0)} %\nmejor", ha="center", va="top",
                fontsize=6.5, color="white")
    ax.axhline(base, color=GRIS_OSCURO, ls="--", lw=0.9)
    ax.text(2.4, base + 0.6, f"mediana (referencia): {coma(base)}", ha="right", va="bottom",
            fontsize=7, color=GRIS_OSCURO)
    ax.set_xticks(range(3), rotulos)
    ax.set_ylabel("MAE Random Forest (min)")
    ax.set_ylim(0, base + 5)
    ax.tick_params(axis="x", length=0)
    guardar(fig, "fig-ablacion")


def resumen_numeros(d):
    """Cifras que se citan en el texto de las láminas, para controlarlas."""
    y = np.array(d["corpus"]["y"]) / 60
    print("mediana", np.median(y), "p90", np.quantile(y, 0.9), "media", y.mean())
    print("gps previo 0:", (np.array(d["corpus"]["gps_previos"]) == 0).mean())
    for m, v in metricas(d).items():
        print(m, {k: round(x, 2) for k, x in v.items()}, "folds", np.round(d["mae_particion"][m], 2))
    print("ablación", d["ablacion"])
    tipos = d["corpus"]["tipoHDR"]
    valores, cuentas = np.unique([str(t) for t in tipos], return_counts=True)
    print("tipoHDR", dict(zip(valores, cuentas)))
    g = np.array(d["corpus"]["gps_previos"])
    print("gps previos", dict(zip(*np.unique(g, return_counts=True))))
    p = d["pred"]["Random Forest"] / 60
    e = np.abs(p - y)
    print("RF: % eventos ≥ 60 min", (y >= 60).mean(), "· % del error", e[y >= 60].sum() / e.sum())
    print("RF: predicciones p5/p95", np.quantile(p, [0.05, 0.95]))
    print("RF: sobreestima < 5 min", (p > y)[y < 5].mean(), "· subestima ≥ 60", (p < y)[y >= 60].mean())


if __name__ == "__main__":
    datos = cargar_datos("--rehacer" in sys.argv)
    estilo()
    resumen_numeros(datos)
    for funcion in [fig_embudo, fig_duracion, fig_tipohdr, fig_hora,
                    fig_metricas, fig_particiones, fig_error_por_duracion, fig_real_vs_pred,
                    fig_importancia, fig_importancia_grupos, fig_ablacion]:
        funcion(datos)
