# Guía: cómo se arma el corpus

El corpus es la tabla con la que se entrenan los modelos: **una fila por desvío (evento)**, con
los atributos conocidos en *T₀* (el primer ping) y la duración *y* que se quiere predecir.

Se arma en una sola celda del notebook `notebooks/01_exploracion_y_modelos.py`, la que sigue al
título "Armado del corpus". Parte de tres tablas ya cargadas: `desv` (lecturas de desvío), `hdr`
(hojas de ruta) y `ras` (GPS crudo).

## Resumen en una línea

Lecturas válidas → un registro por evento → datos de la hoja → sin repetidos → rastreo previo →
atributos de fecha → filtro final.

## Paso a paso

### 0. Limpieza previa (al cargar los JSON)

- Las fechas pasan de UTC a hora de Argentina.
- Las coordenadas se normalizan: en desvíos vienen como `[lat, lon]` y en rastreo como
  `[lon, lat]`.
- El vehículo se unifica bajo el nombre `flota` (en los archivos es `flotaId`, `flotaID` y
  `vehiculo.id`).

### 1. Lecturas válidas

Se descartan las lecturas sin `grupoDesvioId`, con año fuera de 2025–2026 o con posición
`[0, 0]`.

### 2. De lecturas a eventos

Se agrupa por `grupoDesvioId` y queda una fila por evento con:

| Campo | Qué es |
|---|---|
| `t0` | Fecha mínima de las lecturas (el primer ping) |
| atributos del primer ping | Vehículo, hoja, tipo de hoja, distancia a la ruta, velocidad, ruta más cercana, latitud y longitud |
| `lecturas` | Cuántas lecturas tiene el evento. **Solo se usa para filtrar**, nunca como atributo (sería una fuga) |
| `y` | Duración: fecha máxima menos fecha mínima, en segundos |

El primer ping se elige ordenando por fecha y desempatando por distancia y posición, para que el
resultado no dependa del orden interno de polars.

### 3. Datos de la hoja de ruta

*Left join* por `hdr_id`: si el desvío no tiene hoja, se mantiene con nulos. Se agregan obra, tipo
de vehículo, plazas, pasajeros, kilómetros y minutos de la ida (OSRM) y `hoja_vigente` (si la
fecha de T₀ cae entre el inicio y el fin de la hoja).

Los desvíos contra hojas vencidas **no se descartan**: quedan marcados con `hoja_vigente = False`.

### 4. Desvíos repetidos

El sistema guarda un mismo desvío contra varias hojas, con distinto `grupoDesvioId`. Se deja uno
por **vehículo y T₀**, prefiriendo el de la hoja vigente. El `grupoDesvioId` desempata para que el
resultado se repita siempre.

### 5. Rastreo previo

Se usa el GPS de los **10 minutos anteriores a T₀**, sin incluir T₀:

| Atributo | Qué es |
|---|---|
| `gps_previos` | Cantidad de puntos GPS en la ventana |
| `vel_media_previa` | Velocidad media en la ventana |
| `vel_ultima` | Velocidad del último punto antes de T₀ |
| `min_desde_ultimo_gps` | Minutos entre el último punto y T₀ |
| `desplaz_previo_m` | Distancia entre el primer y el último punto (haversine) |
| `rumbo_previo` | Dirección del movimiento; vacío si hay menos de 2 puntos |

Si el vehículo no tiene GPS en esa ventana, estos atributos quedan vacíos. Pasa en el 42 % de los
eventos.

### 6. Atributos de fecha

Se derivan de T₀ en hora local: `hora`, `dia_semana` y `franja` (madrugada antes de las 6,
mañana hasta las 12, tarde hasta las 18, noche). Además, `velocidad_vacia` marca si el primer ping
venía sin velocidad.

### 7. Filtro final

- **Evento válido:** 2 lecturas o más y duración mayor a 0.
- **Corpus:** eventos válidos con duración menor a **4 horas**.
- **Tope:** eventos válidos de 4 horas o más. Se guardan aparte (variable `tope`) y no se usan para
  entrenar, porque el detector corta en 4 h y no hay un retorno medido.

## Cuentas

| Paso | Eventos |
|---|---|
| Eventos de partida | 37.720 |
| Repetidos eliminados | − 2.007 |
| Con una sola lectura o duración 0 | − 19.240 |
| En el tope de 4 h (aparte) | − 2.841 |
| **Corpus final** | **13.632** (556 vehículos) |

Duración en el corpus: mediana 20 min, cuartiles 10 y 53 min.

## Lo que hay que saber

- **Sin fugas:** solo se usa información de T₀ y anterior. `retorno.*`, el número de lecturas y el
  GPS posterior a T₀ quedan afuera.
- **El corpus no tiene los eventos más largos.** Al sacar los de 4 h o más, el error que se mide
  es optimista respecto del uso real.
- **Hojas vencidas:** el 61 % de los desvíos cae fuera de la vigencia de su hoja. Se mantienen y se
  marcan; si la cátedra o Tecfield dicen que no son válidos, hay que filtrarlos.
