# Datos

El dataset es privado (Tecfield) y no está en el repo. Va en `data/raw/`:

| archivo | qué es |
|---|---|
| `hojaDeRuta.json` (1,5 GB) | hojas de ruta: vehículo, obra, pasajeros, paradas y ruta OSRM |
| `desviosHojaRuta.json` (98 MB) | puntos GPS a más de 500 m de la ruta, agrupados por `grupoDesvioId` |
| `rastreoSatelital.json` (284 MB) | eventos crudos del GPS: posición, velocidad, tipo de evento |

Los tres vienen en `data-fixed.zip`, cifrado. La contraseña se pide al grupo y se guarda en
`DATOS_ZIP_CLAVE` del `.env`. Para extraerlo con 7-Zip, desde la raíz del proyecto:

```
7z x -p<contraseña> -odata/raw data/raw/data-fixed.zip
```

Si los datos están en otra carpeta, se indica en `DATOS_DIR` del `.env`.
