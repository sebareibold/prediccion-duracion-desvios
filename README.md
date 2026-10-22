# Predicción de la duración de desvíos de ruta

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![marimo](https://img.shields.io/badge/marimo-notebook-1C7361)
![Polars](https://img.shields.io/badge/Polars-CD792C?logo=polars&logoColor=white)
![scikit--learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?logo=numpy&logoColor=white)
![Altair](https://img.shields.io/badge/Altair-Vega--Lite-4C78A8)
![MongoDB](https://img.shields.io/badge/datos-MongoDB%20export-47A248?logo=mongodb&logoColor=white)

Trabajo de la materia **Laboratorio de Inteligencia Artificial** (Facultad de Informática, UNComa),
hecho junto con **Tecfield**, que opera flotas de transporte de personal.

Cuando un vehículo se aleja más de 500 m de su hoja de ruta, el sistema empieza a registrar un
desvío. Con el **primer ping** no se sabe si va a durar un minuto o una hora. El objetivo es
predecir en ese momento (*T₀*) **cuántos segundos va a durar el desvío**, como alerta temprana.

**Grupo 5:** Sebastián Alejandro Reibold · Bautista Fernandez Gramajo · Davor Kissner

## Estructura del proyecto

```
.
├── README.md
├── requirements.txt                 dependencias de Python
├── .env.example                     plantilla de configuración (dónde están los datos)
├── Abrir notebook.bat               doble clic: prepara el entorno y abre el notebook (Windows)
├── notebooks/
│   ├── 01_exploracion_y_modelos.py  notebook marimo: exploración, corpus y modelos
│   └── estilo.css                   tema oscuro del notebook
├── data/                            datos (no se suben; ver data/README.md)
│   └── raw/                         los tres JSON de Tecfield, sin modificar
├── docs/
│   ├── enunciados/                  consigna de la cátedra y enunciado de Tecfield
│   └── diagramas/                   modelo de datos, cómo nace un desvío, línea de tiempo
├── reports/                         entregas: primera entrega, informe de avance, plan de trabajo
└── references/                      papers de trabajos relacionados (no se suben)
```

Los diagramas `.excalidraw` se abren en [excalidraw.com](https://excalidraw.com).

## Datos (no están en el repo)

El dataset es de Tecfield y es privado: tres colecciones exportadas de MongoDB (≈ 1,9 GB).
Detalle de los archivos y cómo extraerlos en [`data/README.md`](data/README.md).

El código no tiene rutas fijas. La carpeta de los datos se configura en un `.env` en la raíz del
proyecto, que no se sube al repo:

```
copy .env.example .env      # y completar DATOS_DIR (por defecto data/raw)
```

## Cómo correrlo

**Windows:** doble clic en `Abrir notebook.bat`. La primera vez crea `.venv` e instala
`requirements.txt`; si falta `.env`, lo crea a partir de `.env.example`. Después abre marimo en
http://localhost:2718.

**A mano** (cualquier sistema operativo), desde la raíz del proyecto:

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt      # en Windows: .venv\Scripts\pip
.venv/bin/marimo edit notebooks/01_exploracion_y_modelos.py
```

Con [uv](https://github.com/astral-sh/uv) alcanza
`uvx marimo edit --sandbox notebooks/01_exploracion_y_modelos.py`, porque el notebook declara sus
dependencias en el encabezado.

## Cómo se arma el corpus

- La unidad es el **evento** (`grupoDesvioId`), no la lectura. *T₀* es su primer ping y la
  duración *y* va del primero al último, en segundos.
- Se descartan las lecturas con posición `[0, 0]` o con fechas fuera de 2025–2026.
- Se entrena solo con eventos de 2 lecturas o más y duración mayor a 0. Los que llegan al tope de
  4 h del detector van aparte: no son un retorno medido.
- El sistema guarda un mismo desvío contra varias hojas de ruta. Se deja uno por vehículo y *T₀*,
  y se prefiere el de la hoja vigente.
- Solo se usa información disponible en *T₀*, en tres grupos de atributos:
  - **Primer ping:** distancia a la ruta, velocidad, ruta más cercana, posición, hora, día y franja.
  - **Hoja de ruta:** tipo de vehículo y de hoja, obra, largo y duración OSRM, plazas, pasajeros y
    si la hoja estaba vigente.
  - **Rastreo previo:** cantidad de GPS, velocidad media y última, desplazamiento y rumbo en los
    10 minutos anteriores a *T₀*.

De 37.720 eventos quedan **13.632 para entrenar, de 556 vehículos**. Se descartan 19.240 por tener
una sola lectura o duración 0, otros 2.841 llegan al tope y 2.007 son repetidos. Duración en el
corpus: mediana 20 min, cuartiles 10 y 53 min.

## Modelos y resultados

Tres modelos de scikit-learn contra la **mediana** como *baseline*: árbol de decisión, Random
Forest y *gradient boosting* (`HistGradientBoostingRegressor`). Los tres aprenden log(1 + *y*)
porque la duración tiene cola larga. La validación cruzada es de 5 particiones **por vehículo**
(`GroupKFold`): un móvil nunca está en entrenamiento y prueba a la vez.

| modelo | MAE (min) | error mediano (min) | mejora del MAE vs. mediana |
|---|---|---|---|
| Mediana (*baseline*) | 32,1 | 15,0 | — |
| Árbol de decisión | 28,8 | 14,4 | 10 % |
| **Random Forest** | **27,0** | **13,0** | **16 %** |
| Gradient boosting | 27,3 | 13,1 | 15 % |

Aporte de cada grupo de atributos, sumándolos de a uno (*gradient boosting*):

| atributos | MAE (min) | mejora vs. mediana |
|---|---|---|
| Primer ping | 29,4 | 8 % |
| + Hoja de ruta | 27,3 | 15 % |
| + Rastreo previo | 27,3 | 15 % |

Primeras conclusiones: los modelos le ganan a la mediana, pero por poco. La hoja de ruta aporta
casi lo mismo que el primer ping y el rastreo previo no suma nada: falta GPS previo en el 42 % de
los eventos. En el notebook se pueden sacar atributos de la lista y ver cómo cambia el error.

## Trabajos relacionados

Los papers no están en el repo porque tienen derechos de las editoriales.

- Konovalenko et al. (2026). *Predicting last-mile delivery route deviations using machine learning.*
- Grigorev et al. (2024). *Traffic Incident Duration Prediction: A Systematic Review of Techniques.*
- Grigorev et al. (2022). *Incident duration prediction using a bi-level machine learning framework
  with outlier removal and intra–extra joint optimisation.*
- Hojati et al. (2013). *Hazard based models for freeway traffic incident duration.*
- Chen et al. (2013). *iBOAT: Isolation-Based Online Anomalous Trajectory Detection.*
