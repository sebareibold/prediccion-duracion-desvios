# /// script
# requires-python = ">=3.11"
# dependencies = ["marimo", "polars", "altair", "tzdata", "numpy", "scikit-learn", "python-dotenv"]
#
# [tool.marimo.display]
# theme = "dark"
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", css_file="estilo.css")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Predicción de la duración de desvíos (TP1)

    El notebook tiene tres partes: **explorar** los datos de Tecfield, **armar el corpus**
    (un registro por desvío) y **comparar modelos** que predicen cuánto dura un desvío.

    ## Librerías
    polars para las tablas, altair para los gráficos, marimo para el notebook y
    python-dotenv para leer el archivo `.env`.
    """)
    return


@app.cell
def _():
    import json
    import os

    import altair as alt
    import marimo as mo
    import polars as pl
    from dotenv import load_dotenv

    return alt, json, load_dotenv, mo, os, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Configuración y funciones de ayuda
    Lee de `.env` la carpeta de los datos, fija la zona horaria de Argentina y define funciones
    para leer los JSON de a una línea, aplanar los campos de Mongo (`$oid`, `$date`), pasar
    fechas a hora local y dibujar gráficos de barras.
    """)
    return


@app.cell
def _(alt, json, load_dotenv, mo, os, pl):
    # El notebook vive en notebooks/; .env está en la raíz del proyecto.
    RAIZ = mo.notebook_dir().parent
    load_dotenv(RAIZ / ".env")

    # Los datos de Tecfield no están en el repo: su carpeta se configura en .env.
    # Una ruta relativa se toma desde la raíz del proyecto.
    if not os.environ.get("DATOS_DIR"):
        raise RuntimeError(
            f"Falta DATOS_DIR. Copiá {RAIZ / '.env.example'} como .env y completalo."
        )
    # Si DATOS_DIR es relativa se cuelga de la raíz del proyecto; si es absoluta, Path la respeta tal cual.
    DATOS = RAIZ / os.environ["DATOS_DIR"]

    # Zona horaria para pasar las fechas de UTC a hora de Argentina (UTC−3).
    TZ = "America/Argentina/Buenos_Aires"
    # Gris claro que usan todos los gráficos (combina con el tema oscuro del notebook).
    COLOR = "#d4d4d8"

    # Rectángulo que contiene a la Argentina: deja afuera coordenadas vacías o erróneas.
    EN_ARGENTINA = pl.col("lat").is_between(-56, -20) & pl.col("lon").is_between(-75, -53)

    @alt.theme.register("tp1_oscuro", enable=True)
    def _tema():
        """Tema de Altair para todos los gráficos del notebook.

        Devuelve un ThemeConfig con fondo transparente y ejes, leyendas y títulos en grises,
        para que combinen con el tema oscuro de estilo.css.
        """
        gris_suave = "#a1a1aa"
        gris_linea = "rgba(255, 255, 255, 0.08)"
        # Mismo estilo para etiquetas, títulos y líneas de todos los ejes.
        ejes = {
            "labelColor": gris_suave,
            "titleColor": gris_suave,
            "gridColor": gris_linea,
            "domainColor": gris_linea,
            "tickColor": gris_linea,
        }
        # "transparent" en fondo y borde de la vista deja ver el color de la página.
        return alt.theme.ThemeConfig(
            {
                "config": {
                    "background": "transparent",
                    "view": {"stroke": "transparent"},
                    "axis": ejes,
                    "legend": {"labelColor": gris_suave, "titleColor": gris_suave},
                    "title": {"color": "#fafafa", "fontWeight": 600},
                }
            }
        )

    def iter_docs(nombre):
        """Recorre un export de Mongo y devuelve de a un documento (dict) por vez.

        El archivo es un array JSON con un documento por línea. Se lee línea a línea en vez de
        cargar todo con json.load, porque los archivos pesan hasta 1,5 GB.

        nombre: archivo dentro de la carpeta DATOS (por ejemplo "hojaDeRuta.json").
        """
        with open(DATOS / nombre, encoding="utf-8") as archivo:
            for linea in archivo:
                # Cada línea termina en coma salvo la última: se saca para poder parsearla sola.
                linea = linea.rstrip().rstrip(",")
                # "[" y "]" son los bordes del array y no son documentos.
                if linea in ("[", "]", ""):
                    continue
                yield json.loads(linea)

    def unwrap(valor):
        """Convierte {"$oid": ...} o {"$date": ...} en el valor plano.

        mongoexport guarda ids y fechas envueltos en un diccionario. Cualquier otro valor
        (texto, número, None) vuelve sin cambios.
        """
        if isinstance(valor, dict):
            # Un documento trae "$date" o "$oid", nunca los dos.
            return valor.get("$date") or valor.get("$oid")
        return valor

    def a_hora_local(*columnas):
        """Devuelve una expresión de polars por columna, pasada de UTC a hora de Argentina.

        columnas: nombres de columnas de texto con fechas ISO en UTC. Con strict=False una fecha
        inválida queda como nulo en lugar de cortar la carga.
        """
        expresiones = []
        for columna in columnas:
            # Primero se declara que el texto está en UTC y recién después se convierte a UTC-3.
            fecha_utc = pl.col(columna).str.to_datetime(strict=False, time_zone="UTC")
            expresiones.append(fecha_utc.dt.convert_time_zone(TZ))
        return expresiones

    def barras(df, x, y, titulo, horizontal=False):
        """Gráfico de barras de Altair, con tooltip de las dos columnas.

        df: DataFrame de polars. x e y: columnas con su tipo de Altair (por ejemplo "mes:T").
        titulo: título del gráfico. horizontal: True para categorías con nombres largos,
        que quedan legibles y ordenadas de mayor a menor.
        """
        if horizontal:
            # Se intercambian los ejes: las categorías van en y, ordenadas por el valor de x.
            codificacion = {
                "y": alt.Y(x, sort="-x", title=None),
                "x": alt.X(y, title=None),
            }
            # Alto proporcional a la cantidad de barras, con un tope de 400 px.
            alto = min(400, 22 * df.height)
        else:
            codificacion = {
                "x": alt.X(x, title=None),
                "y": alt.Y(y, title=None),
            }
            alto = 220

        return (
            alt.Chart(df, title=titulo)
            .mark_bar(color=COLOR, cornerRadiusEnd=4)
            .encode(**codificacion, tooltip=[x, y])
            .properties(width=600, height=alto)
        )

    return COLOR, EN_ARGENTINA, a_hora_local, barras, iter_docs, unwrap


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # ¿Qué tiene `datafixed`?

    Tres colecciones exportadas de MongoDB (Extended JSON, un documento por línea), en la carpeta
    `DATOS_DIR` de `.env`. `data-fixed.zip` es exactamente estos mismos tres archivos comprimidos.
    Las fechas vienen en UTC y acá se pasan a hora de Argentina.

    | archivo | qué es |
    |---|---|
    | `hojaDeRuta.json` (1,5 GB) | hojas de ruta: vehículo, obra, pasajeros, paradas y geometría OSRM de ida/vuelta/alternativa |
    | `desviosHojaRuta.json` (98 MB) | puntos GPS en los que un vehículo se salió de su hoja de ruta |
    | `rastreoSatelital.json` (284 MB) | eventos crudos del rastreo satelital (GPS programado, detenido, excesos de velocidad…) |

    > La carga parsea ~1,9 GB línea por línea: tarda alrededor de un minuto.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Carga de las hojas de ruta
    De cada hoja se guardan los datos simples: vehículo, obra, fechas, pasajeros y largo y
    duración de la ruta OSRM. La geometría se descarta: es casi todo el peso del archivo y no se usa.
    """)
    return


@app.cell
def _(iter_docs, pl, unwrap):
    def _contar_elementos(documento, claves):
        """Suma el largo de varias listas del documento (las que falten cuentan 0).

        documento: una hoja de ruta (dict). claves: nombres de los campos que son listas,
        por ejemplo las paradas de ida, vuelta y alternativa.
        """
        total = 0
        for clave in claves:
            # "or []" cubre tanto el campo ausente como el campo en null.
            total += len(documento.get(clave) or [])
        return total

    _filas = []
    # Se recorre hoja por hoja y se guarda solo lo escalar. La geometría OSRM (el 99% del peso)
    # se descarta, así los 1,5 GB entran en memoria.
    for _doc in iter_docs("hojaDeRuta.json"):
        # Los campos anidados pueden faltar o venir en null: "or {}" evita errores al leerlos.
        _geometria = _doc.get("geometriaOSRM") or {}
        _ida = _geometria.get("ida") or {}
        _vehiculo = _doc.get("vehiculo") or {}

        # OSRM da la distancia en metros y la duración en segundos: acá pasan a km y minutos.
        _metros_ida = _ida.get("distancia_osrm")
        if _metros_ida is None:
            _km_ida = None
        else:
            _km_ida = _metros_ida / 1000

        _segundos_ida = _ida.get("duracion_osrm_original")
        if _segundos_ida is None:
            _min_ida = None
        else:
            _min_ida = _segundos_ida / 60

        # Paradas y waypoints: se suman las tres variantes (ida, vuelta, alternativa) en un solo conteo.
        _paradas = _contar_elementos(_doc, ["paradasIda", "paradasVuelta", "paradasAlternativa"])
        _waypoints = _contar_elementos(_doc, ["waypointsIda", "waypointsVuelta", "waypointsAlternativa"])

        _filas.append(
            {
                "id": unwrap(_doc["_id"]),
                "obra_id": _doc.get("obra_id"),
                "desde": unwrap(_doc.get("fechaDesde")),
                "hasta": unwrap(_doc.get("fechaHasta")),
                "estado": _doc.get("estado"),
                "eliminada": _doc.get("eliminada"),
                "tipoHDR": _doc.get("tipoHDR"),
                "vehiculo_id": _vehiculo.get("id"),
                "tipoVehiculo": _vehiculo.get("tipoVehiculo"),
                "plazas": _vehiculo.get("cantidadPlazas"),
                "pasajeros": _doc.get("totalPasajeros"),
                # De la geometría solo importa si la hoja define vuelta o alternativa, no su contenido.
                "tiene_vuelta": "vuelta" in _geometria,
                "tiene_alternativa": "alternativa" in _geometria,
                "km_ida": _km_ida,
                "min_ida": _min_ida,
                # Cantidad de puntos de la geometría de ida (los puntos en sí no se guardan).
                "puntos_ida": len(_ida.get("puntos") or []),
                "paradas": _paradas,
                "waypoints": _waypoints,
            }
        )

    # fechaDesde/Hasta son fechas nominales (medianoche UTC): quedan como fecha, sin pasar a hora local.
    # infer_schema_length=None: polars mira todas las filas para decidir el tipo de cada columna
    # (evita errores cuando los primeros valores de una columna son nulos).
    hdr = pl.from_dicts(_filas, infer_schema_length=None).with_columns(
        pl.col("desde", "hasta").str.to_datetime(strict=False, time_zone="UTC").dt.date()
    )
    hdr
    return (hdr,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Carga de los desvíos
    Un registro por punto fuera de ruta: a qué desvío pertenece (`grupoDesvioId`), distancia
    a la ruta, velocidad, posición y cómo terminó.
    """)
    return


@app.cell
def _(a_hora_local, iter_docs, pl, unwrap):
    _filas = []
    # Un documento = un punto GPS fuera de ruta. Los puntos de un mismo episodio comparten grupoDesvioId.
    for _doc in iter_docs("desviosHojaRuta.json"):
        _retorno = _doc.get("retorno") or {}
        # En desvíos la posición viene como [lat, lon].
        _posicion = _doc.get("posicion") or [None, None]

        _filas.append(
            {
                # "ts" es cuándo se registró el punto; "rastreo_ts" es cuándo el GPS midió esa
                # posición (puede ser bastante antes, ver la demora más abajo).
                "ts": unwrap(_doc["timestamp"]),
                "rastreo_ts": unwrap(_doc.get("fechaHoraRastreo")),
                "flota": _doc.get("flotaId"),
                "hdr_id": _doc.get("hojaDeRutaId"),
                "tipoHDR": _doc.get("tipoHDR"),
                "grupo": unwrap(_doc.get("grupoDesvioId")),
                "distancia_m": _doc.get("distanciaMinima"),
                "ruta_cercana": _doc.get("rutaMasCercana"),
                "velocidad": _doc.get("velocidad"),
                "lat": _posicion[0],
                "lon": _posicion[1],
                # Retorno: si el detector vio volver al vehículo a la ruta, cuándo y con qué motivo.
                "retorno_detectado": _retorno.get("detectado"),
                "retorno_ts": unwrap(_retorno.get("timestamp")),
                "retorno_motivo": _retorno.get("motivo"),
            }
        )

    # Las tres fechas vienen como texto UTC y se pasan a hora de Argentina.
    desv = pl.from_dicts(_filas, infer_schema_length=None).with_columns(
        a_hora_local("ts", "rastreo_ts", "retorno_ts")
    )
    desv
    return (desv,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Carga del rastreo satelital
    Todos los eventos del GPS de cada vehículo: fecha, tipo de evento, velocidad y posición.
    Acá las coordenadas vienen al revés que en desvíos: `[lon, lat]`.
    """)
    return


@app.cell
def _(a_hora_local, iter_docs, pl, unwrap):
    _filas = []
    # Un documento = un evento del GPS (posición programada, detenido, exceso de velocidad…).
    for _doc in iter_docs("rastreoSatelital.json"):
        # GeoJSON: las coordenadas vienen como [lon, lat].
        _ubicacion = _doc.get("location") or {}
        _coordenadas = _ubicacion.get("coordinates") or [None, None]

        _filas.append(
            {
                "fecha": unwrap(_doc["fecha"]),
                "flota": _doc.get("flotaID"),
                "evento": _doc.get("evento"),
                "velocidad": _doc.get("velocidad"),
                "lon": _coordenadas[0],
                "lat": _coordenadas[1],
            }
        )

    # "fecha" viene como texto UTC: se convierte a hora de Argentina.
    ras = pl.from_dicts(_filas, infer_schema_length=None).with_columns(a_hora_local("fecha"))
    ras
    return (ras,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Panorama
    Cuántas filas, qué período y cuántos vehículos tiene cada colección.
    """)
    return


@app.cell
def _(desv, hdr, pl, ras):
    # Una fila por colección: cuántas filas tiene, qué período cubre y cuántos vehículos distintos.
    # Sirve para ver si las tres colecciones cubren el mismo tiempo y los mismos vehículos.
    _resumen = pl.DataFrame(
        {
            "colección": ["hojaDeRuta", "desviosHojaRuta", "rastreoSatelital"],
            "filas": [hdr.height, desv.height, ras.height],
            # En hojas de ruta el período es el de vigencia (desde/hasta); en desvíos y rastreo, el de las fechas del GPS.
            "desde": [
                str(hdr["desde"].min()),
                str(desv["rastreo_ts"].min()),
                str(ras["fecha"].min()),
            ],
            "hasta": [
                str(hdr["hasta"].max()),
                str(desv["rastreo_ts"].max()),
                str(ras["fecha"].max()),
            ],
            "vehículos": [
                hdr["vehiculo_id"].n_unique(),
                desv["flota"].n_unique(),
                ras["flota"].n_unique(),
            ],
        }
    )
    _resumen
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Hojas de ruta
    Cuántas hay por estado, tipo de hoja y tipo de vehículo, cuántas empiezan cada mes y qué
    tan llenos van los vehículos.
    """)
    return


@app.cell
def _(barras, hdr, mo, pl):
    # Hojas por mes de inicio de vigencia (truncate("1mo") lleva cada fecha al día 1 de su mes).
    _mes = pl.col("desde").dt.truncate("1mo").alias("mes")
    _por_mes = hdr.group_by(_mes).len().sort("mes")

    # Ocupación = pasajeros / plazas. Se descartan las hojas sin plazas para no dividir por cero.
    _con_plazas = hdr.filter(pl.col("plazas") > 0)
    _ocupacion = _con_plazas.with_columns(ocupacion=pl.col("pasajeros") / pl.col("plazas"))
    _ocupacion_media = _ocupacion["ocupacion"].mean()
    _sin_pasajeros = (hdr["pasajeros"] == 0).mean()
    _obras = hdr["obra_id"].n_unique()

    # Conteos de las columnas categóricas, uno al lado del otro.
    _conteos = mo.hstack(
        [
            hdr["estado"].value_counts(sort=True),
            hdr["tipoHDR"].value_counts(sort=True),
            hdr["tipoVehiculo"].value_counts(sort=True),
            hdr["eliminada"].value_counts(sort=True),
        ],
        wrap=True,
    )
    # Días de vigencia de cada hoja (hasta − desde).
    _dias_vigencia = (pl.col("hasta") - pl.col("desde")).dt.total_days().alias("dias_vigencia")
    # describe() calcula cantidad, media, desvío, mínimo, cuartiles y máximo de cada columna.
    _estadisticas = hdr.select(
        "km_ida",
        "min_ida",
        "pasajeros",
        "plazas",
        "paradas",
        "waypoints",
        "puntos_ida",
        _dias_vigencia,
    ).describe()

    # La salida de la celda apila los bloques calculados arriba.
    mo.vstack(
        [
            _conteos,
            barras(_por_mes, "mes:T", "len:Q", "Hojas de ruta por mes de inicio"),
            _estadisticas,
            mo.md(
                f"Ocupación media (pasajeros / plazas, sobre {_ocupacion.height} HDR con plazas>0): "
                f"**{_ocupacion_media:.0%}**; HDR sin ningún pasajero: "
                f"**{_sin_pasajeros:.0%}**. "
                f"{_obras} obras distintas."
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Desvíos
    Cuántos episodios hay, cómo terminan, qué tan lejos se van y cuánto tarda en registrarse
    cada punto desde que lo marcó el GPS.
    """)
    return


@app.cell
def _(barras, desv, mo, pl):
    # Resumen preliminar por episodio, solo para explorar. Ojo: acá la duración usa "ts" (hora de
    # registro) y "retorno_ts"; el corpus de más abajo usa la hora del GPS ("rastreo_ts"), que es
    # la que corresponde a T₀.
    _episodios = (
        desv.group_by("grupo")
        .agg(
            puntos=pl.len(),
            inicio=pl.col("ts").min(),
            fin=pl.col("retorno_ts").max(),
            motivo=pl.col("retorno_motivo").first(),
            dist_max_m=pl.col("distancia_m").max(),
        )
        .with_columns(duracion_min=(pl.col("fin") - pl.col("inicio")).dt.total_minutes())
    )

    # Demora entre la posición GPS y el momento en que se registró el punto de desvío.
    _demora_min = (desv["ts"] - desv["rastreo_ts"]).dt.total_minutes()
    _demora_mayor_1h = _demora_min > 60

    _dia = pl.col("rastreo_ts").dt.date().alias("dia")
    _por_dia = desv.group_by(_dia).len().sort("dia")

    _velocidad_nula = desv["velocidad"].is_null().mean()
    _con_tipo_hdr = desv["tipoHDR"].is_not_null().mean()

    # Texto en markdown con los números calculados arriba (f-string).
    _texto = f"""
    {desv.height:,} puntos agrupados en **{_episodios.height:,} episodios** (`grupoDesvioId`),
    de {desv['flota'].n_unique()} vehículos y {desv['hdr_id'].n_unique():,} hojas de ruta.
    Velocidad nula en {_velocidad_nula:.0%} de los puntos;
    `tipoHDR` presente solo en {_con_tipo_hdr:.0%}.

    **Demora entre el GPS (`fechaHoraRastreo`) y el registro del desvío (`timestamp`)**, en minutos:
    mediana {_demora_min.median():.1f}, p95 {_demora_min.quantile(0.95):.1f},
    p99 {_demora_min.quantile(0.99):,.0f}, máx {_demora_min.max():,.0f}.
    {_demora_mayor_1h.sum():,} puntos ({_demora_mayor_1h.mean():.1%}) usan una posición GPS
    de más de 1 h de antigüedad.
    """

    mo.vstack(
        [
            mo.md(_texto),
            mo.hstack(
                [
                    desv["retorno_motivo"].value_counts(sort=True),
                    desv["ruta_cercana"].value_counts(sort=True),
                ],
                wrap=True,
            ),
            _episodios.select("puntos", "duracion_min", "dist_max_m").describe(),
            barras(_por_dia, "dia:T", "len:Q", "Puntos de desvío por día (hora del GPS)"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Rastreo satelital
    Tipos de evento, filas duplicadas y cantidad de eventos por día.
    """)
    return


@app.cell
def _(barras, mo, pl, ras):
    _eventos = ras["evento"].value_counts(sort=True)
    # Filas idénticas en todas las columnas: unique() las junta; la diferencia son los duplicados.
    _duplicadas = ras.height - ras.unique().height

    # Eventos de exceso de velocidad. (?i) hace que la búsqueda ignore mayúsculas y minúsculas.
    _limite = ras.filter(pl.col("evento").str.contains("(?i)limite"))
    # Si el evento dice "límite superado" pero la velocidad es 0, ese dato de velocidad no sirve.
    _limite_sin_velocidad = (_limite["velocidad"] == 0).mean()

    _dia = pl.col("fecha").dt.date().alias("dia")
    _por_dia = ras.group_by(_dia).len().sort("dia")

    _texto = f"""
    {ras.height:,} eventos de {ras['flota'].n_unique()} vehículos y {_eventos.height} tipos de evento.

    - Filas **exactamente duplicadas**: {_duplicadas:,} ({_duplicadas / ras.height:.0%}).
    - Eventos de "Límite de X km/h superado" con `velocidad == 0`:
      {_limite_sin_velocidad:.0%} de {_limite.height:,}.
    - Velocidad: mediana {ras['velocidad'].median()}, máx {ras['velocidad'].max()}.
    """

    mo.vstack(
        [
            mo.md(_texto),
            barras(
                _eventos.head(15),
                "evento:N",
                "count:Q",
                "Tipos de evento (top 15)",
                horizontal=True,
            ),
            barras(_por_dia, "dia:T", "len:Q", "Eventos por día"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## ¿Se cruzan las tres colecciones?
    Revisa si los ids de vehículos y de hojas coinciden entre colecciones y cuántos desvíos
    caen fuera de la vigencia de su hoja de ruta.
    """)
    return


@app.cell
def _(desv, hdr, mo, pl, ras):
    # Hojas de ruta citadas en desvíos que no existen en hojaDeRuta.
    _ids_hojas = hdr["id"].to_list()
    # unique() deja cada id una sola vez; is_in compara contra los ids que sí existen en hojaDeRuta.
    _hojas_en_desvios = desv["hdr_id"].unique()
    _huerfanas = _hojas_en_desvios.filter(~_hojas_en_desvios.is_in(_ids_hojas))
    _puntos_huerfanos = desv["hdr_id"].is_in(_huerfanas.to_list()).sum()

    # Vehículos de cada colección.
    _vehiculos_hdr = set(hdr["vehiculo_id"])
    _vehiculos_desv = set(desv["flota"])
    _vehiculos_ras = set(ras["flota"])

    # Primer día con datos de rastreo: sirve para contar cuántas hojas siguen vigentes en esa ventana.
    _inicio_rastreo = ras["fecha"].min().date()
    _hojas_en_rango = hdr.filter(pl.col("hasta") >= _inicio_rastreo)

    # Puntos de desvío cuya fecha GPS cae fuera de la vigencia de su hoja.
    _fecha_gps = pl.col("rastreo_ts").dt.date()
    _dias_antes = (pl.col("desde") - _fecha_gps).dt.total_days()
    _dias_despues = (_fecha_gps - pl.col("hasta")).dt.total_days()
    # Se cruza cada punto con su hoja (join) y quedan los que caen fuera de fechaDesde–fechaHasta.
    _fuera_vigencia = (
        desv.join(hdr.select("id", "desde", "hasta"), left_on="hdr_id", right_on="id")
        .filter(~_fecha_gps.is_between(pl.col("desde"), pl.col("hasta")))
        .with_columns(
            dias_fuera=pl.when(_fecha_gps < pl.col("desde"))
            .then(_dias_antes)
            .otherwise(_dias_despues)
        )
    )
    _antes = (_fuera_vigencia["rastreo_ts"].dt.date() < _fuera_vigencia["desde"]).sum()
    _despues = _fuera_vigencia.height - _antes
    _dias_fuera = _fuera_vigencia["dias_fuera"]

    # Un mismo GPS puede aparecer en varios puntos de desvío (por ejemplo, medido contra distintas
    # hojas): n_unique de (vehículo, hora del GPS) cuenta las posiciones reales.
    _gps_distintos = desv.select("flota", "rastreo_ts").n_unique()

    mo.md(
        f"""
    El vehículo se llama `vehiculo.id` en hojas de ruta, `flotaId` en desvíos y `flotaID` en rastreo.

    - `hojaDeRutaId` distintos en desvíos: {_hojas_en_desvios.len():,};
      **{_huerfanas.len()}** no existen en hojaDeRuta ({_puntos_huerfanos:,} puntos de desvío huérfanos).
    - Puntos de desvío cuya fecha GPS cae **fuera de la vigencia** (`fechaDesde`–`fechaHasta`)
      de su hoja de ruta: {_fuera_vigencia.height:,} ({_fuera_vigencia.height / desv.height:.0%});
      {_antes:,} antes de `fechaDesde` y {_despues:,} después de `fechaHasta`.
      Días fuera: mediana {_dias_fuera.median():.0f}, p90 {_dias_fuera.quantile(0.9):.0f}, máx {_dias_fuera.max()}.
    - Posiciones GPS distintas (vehículo + `fechaHoraRastreo`) detrás de los {desv.height:,}
      puntos de desvío: {_gps_distintos:,}.
    - Vehículos de desvíos que tienen hoja de ruta: {len(_vehiculos_desv & _vehiculos_hdr)}/{len(_vehiculos_desv)};
      que aparecen en rastreo: {len(_vehiculos_desv & _vehiculos_ras)}/{len(_vehiculos_desv)}.
    - Vehículos de rastreo con hoja de ruta: {len(_vehiculos_ras & _vehiculos_hdr)}/{len(_vehiculos_ras)}.
    - Hojas de ruta vigentes durante la ventana del rastreo: {_hojas_en_rango.height:,} de {hdr.height:,}.
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## ¿Dónde?
    Mapa de los eventos de rastreo. Se agrupan en una grilla de 0,1° para no mandar millones
    de puntos al navegador.
    """)
    return


@app.cell
def _(COLOR, EN_ARGENTINA, alt, mo, pl, ras):
    # Grilla de 0,1° (unos 11 km): se cuentan los eventos por celda para no mandar todos los puntos al navegador.
    _grilla = (
        ras.filter(EN_ARGENTINA)
        .group_by(pl.col("lat").round(1), pl.col("lon").round(1))
        .len()
    )
    _fuera = ras.height - _grilla["len"].sum()

    _mapa = (
        # Cada círculo es una celda de la grilla; su tamaño (escala logarítmica) es la cantidad de eventos.
        alt.Chart(_grilla)
        .mark_circle(color=COLOR, opacity=0.6)
        .encode(
            x=alt.X("lon:Q", scale=alt.Scale(zero=False), title="longitud"),
            y=alt.Y("lat:Q", scale=alt.Scale(zero=False), title="latitud"),
            size=alt.Size("len:Q", scale=alt.Scale(type="log"), title="eventos"),
            tooltip=["lat", "lon", "len"],
        )
        .properties(width=600, height=500)
    )

    mo.vstack(
        [
            mo.md(f"Fuera de Argentina o sin coordenadas: {_fuera:,} eventos."),
            _mapa,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Corpus: un registro por desvío

    Reglas del enunciado de Tecfield:

    - La unidad es el evento (`grupoDesvioId`). *T₀* es su primer `fechaHoraRastreo`.
    - *y* = último `fechaHoraRastreo` − primero, en segundos.
    - Se descartan las lecturas con posición `[0, 0]` o con fecha fuera de 2025–2026.
    - Se entrena solo con eventos de 2 lecturas o más y duración mayor a 0.
      Los que llegan al tope de 4 h del detector van aparte: no son un retorno medido.
    - Solo se usa información disponible en *T₀*. Quedan afuera `retorno.*`, la cantidad de
      lecturas y todo lo posterior a *T₀*.

    Un mismo punto GPS se guarda contra varias hojas de ruta, así que un mismo desvío puede
    aparecer como varios eventos. Se deja uno por vehículo y *T₀*, prefiriendo el de la hoja vigente.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Armado del corpus
    1. Descarta las lecturas inválidas.
    2. Junta las lecturas de cada desvío y calcula *T₀* y la duración *y*.
    3. Suma los datos de la hoja de ruta.
    4. Deja un solo evento cuando el mismo desvío se guardó contra varias hojas.
    5. Calcula qué hizo el vehículo en los 10 minutos previos a *T₀* (velocidad, desplazamiento, rumbo).
    6. Separa los eventos que llegan al tope de 4 h.
    """)
    return


@app.cell
def _(EN_ARGENTINA, desv, hdr, pl, ras):
    # Duración máxima que registra el detector: 4 horas, en segundos.
    TOPE_S = 4 * 3600

    def _distancia_m(lat1, lon1, lat2, lon2):
        """Distancia en metros entre dos puntos (fórmula del haversine).

        Recibe columnas (expresiones de polars) de latitud y longitud en grados y calcula la
        distancia sobre la superficie de la esfera, fila por fila.
        """
        radio_tierra_m = 6_371_000
        # Latitudes en radianes y diferencias entre los dos puntos.
        fi1 = lat1.radians()
        fi2 = lat2.radians()
        delta_fi = fi2 - fi1
        delta_lambda = (lon2 - lon1).radians()

        # "a" es el cuadrado de la mitad de la cuerda entre los dos puntos.
        a = (delta_fi / 2).sin() ** 2 + fi1.cos() * fi2.cos() * (delta_lambda / 2).sin() ** 2
        return 2 * radio_tierra_m * a.sqrt().arcsin()

    def _rumbo(lat1, lon1, lat2, lon2):
        """Rumbo en grados (0 = norte, 90 = este) para ir del punto 1 al punto 2.

        Recibe columnas (expresiones de polars) de latitud y longitud en grados. Es el rumbo
        inicial del círculo máximo entre los dos puntos.
        """
        fi1 = lat1.radians()
        fi2 = lat2.radians()
        delta_lambda = (lon2 - lon1).radians()

        # Componentes este (y) y norte (x) del desplazamiento.
        x = fi1.cos() * fi2.sin() - fi1.sin() * fi2.cos() * delta_lambda.cos()
        y = delta_lambda.sin() * fi2.cos()
        # arctan2 da de -180° a 180°: se suma 360 y se toma el resto para quedar en 0°–360°.
        return (pl.arctan2(y, x).degrees() + 360) % 360

    # 1) Lecturas válidas.
    # Un GPS sin señal suele informar (0, 0): es un punto en el océano, no una posición real.
    _en_origen = (pl.col("lat") == 0) & (pl.col("lon") == 0)
    _lecturas = desv.filter(
        # Se exige grupo (para poder agrupar), año 2025–2026 (descarta fechas basura) y posición válida.
        pl.col("grupo").is_not_null(),
        pl.col("rastreo_ts").dt.year().is_between(2025, 2026),
        ~_en_origen,
    )

    # 2) Un registro por grupoDesvioId: atributos del primer ping y la duración.
    # Atributos que se toman del primer ping del evento: es lo único que se conoce en T₀.
    _atributos_primer_ping = pl.col(
        "flota", "hdr_id", "tipoHDR", "distancia_m", "velocidad", "ruta_cercana", "lat", "lon"
    )
    # Se ordena por hora del GPS y, si hay empate, por distancia y posición, para que "el primero"
    # sea siempre el mismo ping y el resultado no dependa del orden de las filas.
    _primer_ping = _atributos_primer_ping.sort_by("rastreo_ts", "distancia_m", "lat", "lon").first()
    # Duración y = último GPS − primer GPS del evento, en segundos (hora del GPS, no la de registro).
    _duracion = (pl.col("rastreo_ts").max() - pl.col("rastreo_ts").min()).dt.total_seconds()
    # Una fila por evento: atributos del primer ping, T₀ (su hora), cantidad de lecturas y duración.
    _eventos = _lecturas.group_by("grupo").agg(
        _primer_ping,
        t0=pl.col("rastreo_ts").min(),
        lecturas=pl.len(),
        y=_duracion,
    )
    _n_eventos = _eventos.height

    # 3) Datos de la hoja de ruta (si el join alcanza).
    # Datos de la hoja de ruta de cada evento; unique() evita duplicar eventos si una hoja está repetida.
    _hojas = hdr.select(
        pl.col("id").alias("hdr_id"),
        "obra_id",
        "desde",
        "hasta",
        "tipoVehiculo",
        "km_ida",
        "min_ida",
        "plazas",
        "pasajeros",
        pl.col("tipoHDR").alias("tipoHDR_hoja"),
    ).unique("hdr_id")
    # how="left": los eventos cuya hoja no existe se quedan, con esas columnas en nulo.
    _eventos = (
        _eventos.join(_hojas, on="hdr_id", how="left")
        .with_columns(
            # Si el ping no trae tipoHDR se usa el de la hoja (coalesce toma el primero que no sea nulo).
            tipoHDR=pl.coalesce("tipoHDR", "tipoHDR_hoja"),
            # hoja_vigente: T₀ cae entre fechaDesde y fechaHasta de la hoja.
            hoja_vigente=pl.col("t0").dt.date().is_between(pl.col("desde"), pl.col("hasta")),
        )
        # "desde" y "hasta" solo servían para calcular hoja_vigente.
        .drop("tipoHDR_hoja", "desde", "hasta")
    )

    # 4) Mismo desvío medido contra varias hojas: uno por vehículo y T0, prefiriendo la hoja vigente.
    #    "grupo" desempata para que el resultado no dependa del orden interno de polars.
    # El orden deja primero, dentro de cada (vehículo, T₀), la fila con hoja vigente (descending=True
    # en hoja_vigente pone los True antes); unique(keep="first") se queda con esa fila.
    _eventos = _eventos.sort(
        "flota",
        "t0",
        pl.col("hoja_vigente").fill_null(False),
        "grupo",
        descending=[False, False, True, False],
    ).unique(["flota", "t0"], keep="first", maintain_order=True)
    _n_repetidos = _n_eventos - _eventos.height

    # 5) Rastreo de los 10 minutos anteriores a T0 (sin incluir T0).
    #    Se acumulan sumas por vehículo; el tramo [primer GPS, último GPS] sale de dos join_asof.
    # Velocidad como decimal. _hay_velocidad vale 1 en los GPS que traen velocidad, para promediar
    # sin contar los nulos.
    _velocidad = pl.col("velocidad").cast(pl.Float64)
    _hay_velocidad = _velocidad.is_not_null().cast(pl.Int64)
    # Tabla de GPS ordenada por fecha. Por vehículo se guardan acumulados (cantidad de GPS y suma de
    # velocidades): lo ocurrido en una ventana sale de restar dos filas, sin recorrer los GPS en cada evento.
    _gps = (
        ras.filter(pl.col("fecha").is_not_null(), EN_ARGENTINA)
        .select("flota", "fecha", "velocidad", "lat", "lon")
        .unique()
        .sort("fecha", "lat", "lon", "velocidad", nulls_last=True)
        .with_columns(
            n=pl.col("fecha").cum_count().over("flota"),
            v_suma=_velocidad.fill_null(0).cum_sum().over("flota"),
            v_cuenta=_hay_velocidad.cum_sum().over("flota"),
            v_actual=_velocidad.fill_null(0),
            v_hay=_hay_velocidad,
            # k es la clave de tiempo que usa join_asof.
            k=pl.col("fecha"),
        )
    )
    # Una fila por evento con su vehículo y su T₀: son las "preguntas" que se buscan en la tabla de GPS.
    _claves = _eventos.select("grupo", "flota", "t0")

    # Último GPS antes de T0.
    _ultimo = (
        # T₀ − 1 µs: busca hacia atrás el último GPS estrictamente anterior a T₀ (hasta 10 min antes),
        # así no se usa ninguna información del propio T₀.
        _claves.with_columns(k=pl.col("t0") - pl.duration(microseconds=1))
        .sort("k")
        .join_asof(
            _gps,
            on="k",
            by="flota",
            strategy="backward",
            tolerance="10m",
            check_sortedness=False,
        )
        .select(
            "grupo",
            u_fecha="fecha",
            u_lat="lat",
            u_lon="lon",
            u_vel="velocidad",
            u_n="n",
            u_suma="v_suma",
            u_cuenta="v_cuenta",
        )
    )

    # Primer GPS dentro de los 10 minutos previos a T0.
    _primero = (
        # T₀ − 10 min: busca hacia adelante el primer GPS de la ventana. Si ese GPS es posterior a T₀
        # (el vehículo no tenía GPS en la ventana), el evento queda sin rastreo previo.
        _claves.with_columns(k=pl.col("t0") - pl.duration(minutes=10))
        .sort("k")
        .join_asof(
            _gps,
            on="k",
            by="flota",
            strategy="forward",
            tolerance="10m",
            check_sortedness=False,
        )
        .filter(pl.col("fecha") < pl.col("t0"))
        .select(
            "grupo",
            p_lat="lat",
            p_lon="lon",
            p_n="n",
            # Acumulado justo ANTES del primer GPS de la ventana: restarlo al acumulado del último GPS
            # deja la suma de toda la ventana, incluido el primero.
            p_suma=pl.col("v_suma") - pl.col("v_actual"),
            p_cuenta=pl.col("v_cuenta") - pl.col("v_hay"),
        )
    )

    # Suma y cantidad de velocidades dentro de la ventana [primer GPS, último GPS].
    _suma_velocidades = pl.col("u_suma") - pl.col("p_suma")
    _cantidad_velocidades = pl.col("u_cuenta") - pl.col("p_cuenta")
    # Posición del primer y del último GPS de la ventana: de acá salen el desplazamiento y el rumbo.
    _coordenadas = [pl.col("p_lat"), pl.col("p_lon"), pl.col("u_lat"), pl.col("u_lon")]
    # Hora del evento en hora de Argentina (t0 ya viene en esa zona).
    _hora = pl.col("t0").dt.hour()
    _franja = (
        pl.when(_hora < 6)
        .then(pl.lit("madrugada"))
        .when(_hora < 12)
        .then(pl.lit("mañana"))
        .when(_hora < 18)
        .then(pl.lit("tarde"))
        .otherwise(pl.lit("noche"))
    )

    _eventos = (
        _eventos.join(_ultimo, on="grupo", how="left")
        .join(_primero, on="grupo", how="left")
        .with_columns(
            # GPS en la ventana = diferencia de contadores acumulados + 1 (cuenta también el primero); 0 si no hubo.
            gps_previos=(pl.col("u_n") - pl.col("p_n") + 1).fill_null(0),
            # Velocidad media previa = suma / cantidad de GPS que sí traían velocidad.
            vel_media_previa=_suma_velocidades / _cantidad_velocidades,
            vel_ultima=pl.col("u_vel"),
            # Minutos entre el último GPS y T₀: qué tan fresca es la última posición.
            min_desde_ultimo_gps=(pl.col("t0") - pl.col("u_fecha")).dt.total_seconds() / 60,
            # Distancia en línea recta entre el primer y el último GPS de la ventana, y rumbo de ese tramo.
            desplaz_previo_m=_distancia_m(*_coordenadas),
            rumbo_previo=_rumbo(*_coordenadas),
        )
        .with_columns(
            # Con un solo punto previo no hay rumbo.
            rumbo_previo=pl.when(pl.col("gps_previos") >= 2).then("rumbo_previo"),
            velocidad_vacia=pl.col("velocidad").is_null(),
            hora=_hora,
            dia_semana=pl.col("t0").dt.weekday(),
            franja=_franja,
        )
        # Se borran las columnas auxiliares u_* y p_*: solo servían para calcular los atributos.
        .drop(pl.selectors.starts_with("u_", "p_"))
    )

    # 6) Panel final.
    # Válido: al menos 2 lecturas (con una sola no hay duración medible) y duración mayor a 0.
    _valido = (pl.col("lecturas") >= 2) & (pl.col("y") > 0)
    # Corpus: eventos válidos que terminan antes del tope de 4 h (retorno medido), ordenados por T₀.
    corpus = _eventos.filter(_valido & (pl.col("y") < TOPE_S)).sort("t0")
    # Tope: eventos válidos que llegan a 4 h. El detector los cortó, no hay retorno medido: van aparte.
    tope = _eventos.filter(_valido & (pl.col("y") >= TOPE_S))
    # Conteos para explicar de dónde salen los eventos del corpus (se muestran en la celda siguiente).
    resumen_corpus = {
        "eventos": _n_eventos,
        "repetidos": _n_repetidos,
        "una_lectura_o_cero": _eventos.filter(~_valido).height,
        "tope": tope.height,
        "corpus": corpus.height,
        "vehiculos": corpus["flota"].n_unique(),
    }
    return TOPE_S, corpus, resumen_corpus, tope


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## El corpus
    Cuántos eventos quedan después de cada filtro y cómo se reparte la duración.
    """)
    return


@app.cell
def _(COLOR, TOPE_S, alt, corpus, mo, pl, resumen_corpus):
    # Histograma ya agregado (60 barras hasta el tope): altair no acepta más de 5000 filas.
    # Barras de _ancho_min minutos (4) entre 0 y el tope de 4 h: 60 barras en total.
    _ancho_min = TOPE_S / 60 / 60
    # Cada duración se lleva al inicio de su barra (piso del múltiplo del ancho).
    _inicio_barra = (pl.col("y") / 60 / _ancho_min).floor() * _ancho_min
    # Eventos por barra.
    _barras = corpus.group_by(minutos=_inicio_barra).len("eventos").sort("minutos")

    _histograma = (
        alt.Chart(_barras)
        .mark_bar(color=COLOR)
        .encode(
            x=alt.X(
                "minutos:Q",
                bin=alt.Bin(binned=True, step=_ancho_min),
                title="duración (minutos)",
            ),
            x2=alt.X2("hasta:Q"),
            # Escala symlog: hay muchísimos más eventos cortos que largos; symlog muestra ambos y admite el 0.
            y=alt.Y("eventos:Q", title="eventos", scale=alt.Scale(type="symlog")),
        )
        # Fin de cada barra, para dibujarla de "minutos" a "hasta".
        .transform_calculate(hasta=f"datum.minutos + {_ancho_min}")
        .properties(width=600, height=220, title="Duración de los desvíos del corpus")
    )

    _resumen = resumen_corpus
    # La duración y está en segundos: mediana y percentil 90 pasan a minutos.
    _mediana_min = corpus["y"].median() / 60
    _p90_min = corpus["y"].quantile(0.9) / 60
    _texto = f"""
    - Eventos (`grupoDesvioId`) con lecturas válidas: **{_resumen['eventos']:,}**.
    - Repetidos contra otra hoja (mismo vehículo y *T₀*): {_resumen['repetidos']:,}.
    - Con una sola lectura o duración 0: {_resumen['una_lectura_o_cero']:,}.
    - Llegan al tope de 4 h (aparte): {_resumen['tope']:,}.
    - **Corpus para entrenar: {_resumen['corpus']:,} eventos de {_resumen['vehiculos']} vehículos.**
    - Duración: mediana {_mediana_min:.1f} min, p90 {_p90_min:.1f} min.
    """

    mo.vstack(
        [
            mo.md(_texto),
            _histograma,
            corpus.drop("grupo", "hdr_id").describe(),
        ]
    )
    return


@app.cell
def _(mo):
    # Atributos candidatos, agrupados por su origen. Todos se conocen en T₀.
    ATRIBUTOS = {
        "Primer ping": [
            "distancia_m",
            "velocidad",
            "velocidad_vacia",
            "ruta_cercana",
            "lat",
            "lon",
            "hora",
            "dia_semana",
            "franja",
        ],
        "Hoja de ruta": [
            "tipoVehiculo",
            "tipoHDR",
            "obra_id",
            "km_ida",
            "min_ida",
            "hoja_vigente",
            "plazas",
            "pasajeros",
        ],
        "Rastreo previo": [
            "gps_previos",
            "vel_media_previa",
            "vel_ultima",
            "min_desde_ultimo_gps",
            "desplaz_previo_m",
            "rumbo_previo",
        ],
    }
    # Atributos que son categorías (texto o ids), no números: los modelos no deben tratarlos como orden.
    CATEGORICOS = {"ruta_cercana", "franja", "tipoVehiculo", "tipoHDR", "obra_id"}

    # Lista plana con todos los atributos, para el selector.
    _todos = []
    for _grupo in ATRIBUTOS.values():
        _todos.extend(_grupo)

    # Selector interactivo: al cambiarlo, marimo vuelve a correr las celdas que dependen de él.
    elegidos = mo.ui.multiselect(
        options=_todos,
        value=_todos,
        label="Atributos que usan los modelos",
    )

    mo.vstack(
        [
            mo.md(
                """
    # Modelos

    Se comparan contra la **mediana** (*baseline*): un árbol de decisión, un Random Forest y
    *gradient boosting*. Los tres aprenden log(1 + *y*), porque la duración tiene cola larga.

    Validación cruzada de 5 particiones **por vehículo**: un mismo móvil nunca queda en
    entrenamiento y prueba a la vez. Métricas en minutos, sobre las predicciones fuera de muestra:
    **MAE** (error absoluto medio) y **error mediano**.

    Sacá atributos de la lista para ver si con menos ya alcanza.
    """
            ),
            elegidos,
        ]
    )
    return ATRIBUTOS, CATEGORICOS, elegidos


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Entrenamiento y evaluación
    Pasa los atributos a números, entrena los tres modelos y los compara con la mediana.
    Cada modelo se prueba con vehículos que no vio al entrenar.
    """)
    return


@app.cell
def _(CATEGORICOS, corpus, pl):
    import numpy as np
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.model_selection import GroupKFold
    from sklearn.tree import DecisionTreeRegressor

    # Modelo de referencia: predice siempre la mediana de duración del entrenamiento.
    BASELINE = "Mediana (baseline)"

    def _matriz(atributos):
        """Corpus como matriz numérica: categóricos a códigos 0..k-1 y booleanos a 0/1.

        atributos: lista de nombres de columnas del corpus. Devuelve un arreglo de NumPy con una
        fila por evento y una columna por atributo, en el mismo orden que la lista.
        """
        columnas = []
        for atributo in atributos:
            if atributo in CATEGORICOS:
                # rank("dense") numera las categorías 1..k; se resta 1 para tener 0..k-1.
                # Los nulos quedan como NaN.
                codigo = pl.col(atributo).cast(pl.String).rank("dense") - 1
                columnas.append(codigo.cast(pl.Float64))
            else:
                # Los booleanos pasan a 0/1 y los enteros a decimal.
                columnas.append(pl.col(atributo).cast(pl.Float64))
        return corpus.select(columnas).to_numpy()

    def _modelos(atributos):
        """Modelos nuevos (sin entrenar), con semilla fija para que los resultados se repitan.

        atributos: lista de columnas usadas, para avisarle al gradient boosting cuáles son
        categóricas. Devuelve un diccionario {nombre: modelo}.
        """
        # Una marca por columna, en el mismo orden que la matriz de _matriz.
        es_categorico = []
        for atributo in atributos:
            es_categorico.append(atributo in CATEGORICOS)

        return {
            # Profundidad y hoja mínima limitadas para que el árbol no memorice.
            "Árbol de decisión": DecisionTreeRegressor(
                max_depth=8,
                min_samples_leaf=30,
                random_state=0,
            ),
            # Promedio de 200 árboles; n_jobs=-1 usa todos los núcleos.
            "Random Forest": RandomForestRegressor(
                n_estimators=200,
                min_samples_leaf=10,
                n_jobs=-1,
                random_state=0,
            ),
            # Con categorical_features el modelo trata esas columnas como categorías, no como orden.
            "Gradient boosting": HistGradientBoostingRegressor(
                categorical_features=es_categorico,
                random_state=0,
            ),
        }

    def evaluar(atributos, solo=None):
        """Predicciones fuera de muestra (GroupKFold por vehículo) y métricas en minutos.

        atributos: lista de columnas del corpus que usan los modelos. Con `solo` se evalúa un
        único modelo además del baseline. Devuelve un DataFrame con una fila por modelo y las
        columnas MAE, error mediano y mejora del MAE respecto de la mediana.
        """
        # X: matriz de atributos. y: duración en segundos. vehiculos: vehículo de cada evento,
        # que define las particiones de la validación cruzada.
        X = _matriz(atributos)
        y = corpus["y"].to_numpy()
        vehiculos = corpus["flota"].to_numpy()

        if solo is None:
            nombres = list(_modelos(atributos))
        else:
            nombres = [solo]

        # Un arreglo por modelo, con una predicción por evento: cada evento se predice una sola
        # vez, cuando su vehículo cae en la partición de prueba.
        predicciones = {BASELINE: np.empty_like(y, dtype=float)}
        for nombre in nombres:
            predicciones[nombre] = np.empty_like(y, dtype=float)

        # GroupKFold reparte los vehículos (no los eventos) en 5 particiones.
        particiones = GroupKFold(n_splits=5).split(X, y, vehiculos)
        for entrenamiento, prueba in particiones:
            # Baseline: la mediana de duración del entrenamiento, igual para todos.
            predicciones[BASELINE][prueba] = np.median(y[entrenamiento])

            # Modelos nuevos en cada partición, para no arrastrar lo aprendido de la anterior.
            modelos = _modelos(atributos)
            for nombre in nombres:
                modelo = modelos[nombre]
                # Se entrena sobre log(1 + y) y se vuelve a segundos al predecir.
                modelo.fit(X[entrenamiento], np.log1p(y[entrenamiento]))
                predicciones[nombre][prueba] = np.expm1(modelo.predict(X[prueba]))

        # MAE del baseline, para calcular la mejora de cada modelo.
        error_baseline = np.abs(predicciones[BASELINE] - y).mean()

        # Métricas por modelo, en minutos. La mejora es 1 - MAE del modelo / MAE de la mediana.
        filas = []
        for nombre, prediccion in predicciones.items():
            error = np.abs(prediccion - y)
            filas.append(
                {
                    "modelo": nombre,
                    "MAE (min)": error.mean() / 60,
                    "error mediano (min)": np.median(error) / 60,
                    "mejora MAE vs. mediana": 1 - error.mean() / error_baseline,
                }
            )
        return pl.DataFrame(filas)

    return (evaluar,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Resultados
    Error de cada modelo con los atributos elegidos arriba. Cuanto más bajo, mejor.
    """)
    return


@app.cell
def _(COLOR, alt, elegidos, evaluar, mo):
    mo.stop(not elegidos.value, mo.md("Elegí al menos un atributo."))

    # Validación cruzada con los atributos del selector (con Random Forest tarda un rato).
    resultados = evaluar(list(elegidos.value))

    # Barras con el MAE de cada modelo; sort="x" las ordena de menor a mayor error.
    _grafico = (
        alt.Chart(resultados)
        .mark_bar(color=COLOR, cornerRadiusEnd=4)
        .encode(
            y=alt.Y("modelo:N", sort="x", title=None),
            x=alt.X("MAE (min):Q"),
            tooltip=["modelo", "MAE (min)", "error mediano (min)"],
        )
        .properties(width=600, height=160)
    )

    mo.vstack(
        [
            mo.md(f"Con **{len(elegidos.value)}** atributos elegidos."),
            resultados,
            _grafico,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## ¿Cuánto aporta cada grupo de atributos?
    Se agregan los grupos de a uno (primer ping, hoja de ruta, rastreo previo) y se mide el
    error de *gradient boosting* cada vez.
    """)
    return


@app.cell
def _(ATRIBUTOS, evaluar, pl):
    _filas = []
    _acumulados = []
    # Cada vuelta suma un grupo más a los anteriores: primer ping, + hoja de ruta, + rastreo previo.
    for _grupo, _atributos in ATRIBUTOS.items():
        _acumulados = _acumulados + _atributos

        # solo="Gradient boosting": entrena únicamente ese modelo, para ir más rápido.
        _resultado = evaluar(_acumulados, solo="Gradient boosting")
        # Se queda con la fila del modelo y deja afuera la del baseline.
        _resultado = _resultado.filter(pl.col("modelo") == "Gradient boosting")

        if _filas:
            _etiqueta = "+ " + _grupo
        else:
            _etiqueta = _grupo
        _filas.append(_resultado.with_columns(atributos=pl.lit(_etiqueta)))

    _tabla = pl.concat(_filas).select(
        "atributos",
        "MAE (min)",
        "error mediano (min)",
        "mejora MAE vs. mediana",
    )
    _tabla
    return


if __name__ == "__main__":
    app.run()
