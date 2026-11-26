# Notas de la entrega — Lab. de IA, Grupo 5 (Tecfield)

Integrantes: Sebastián Reibold, Bautista Fernandez Gramajo, Davor Kissner.
Repositorio: https://github.com/sebareibold/prediccion-duracion-desvios

## Fechas de cierre (mensajes de Germán)

- **Jueves 26/11, 14 a 16 h:** presentación del trabajo al resto de los grupos (~20 min, informal, hablan los tres).
- **Viernes 27/11:** entrega del informe final por tarea en Pedco (PDF + artefactos sin datos sensibles + link del repo en el informe).

## Qué hay para entregar (`reports/entrega/`)

- `informe-p1-problema-y-trabajos-relacionados.pdf`
- `informe-p2-exploracion-y-corpus.pdf`
- `informe-p3-modelos-y-resultados.pdf`
- `presentacion-formal.pdf` (22 láminas): **la presentación que se usa el 26/11**
- `presentacion-version-inicial.pdf` (16 láminas): primera versión, informal
- `01_exploracion_y_modelos.py` (notebook de marimo, igual al de `notebooks/`)
- `Notebooks e Informes.zip`: el notebook y los tres informes juntos (sin datos)

Fuentes LaTeX para Overleaf en `reports/overleaf/` (un zip por documento; compilar con pdfLaTeX).

## Presentación formal (`reports/presentacion-formal/`)

- `main.tex` (láminas) y `tema-formal.sty` (diseño: barra de título azul, pie con autores y número).
- `figuras/*.pdf`: 11 gráficos hechos con los datos reales; `img/`: logos y diagrama de colecciones.
- `figuras/generar_figuras.py` corre el notebook y vuelve a dibujar los gráficos
  (`.venv/Scripts/python.exe reports/presentacion-formal/figuras/generar_figuras.py`). Guarda las
  cifras intermedias en `privado/cache/` (no se sube); con `--rehacer` las recalcula (~6 min).
- Overleaf: subir `reports/overleaf/presentacion-formal.zip` (New Project → Upload Project, pdfLaTeX).
- Compilación local con MiKTeX: el mapa de la fuente Source Sans no está activo, hay que compilar con
  `pdflatex -jobname=main "\pdfmapfile{+SourceSansThree.map}\input{main.tex}"`. En Overleaf no hace falta.
- Criterio pedido por el grupo: textos en palabras simples y cortos; sin correos en la portada, sin
  lámina de referencias, sin columna "qué se toma" en trabajos relacionados, sin "sin fuga de información",
  sin la lámina de ubicación y rastreo previo (el 42 % sin GPS previo se cuenta en "Aporte de cada grupo").
- Correcciones respecto de la versión inicial: el Random Forest no sortea atributos en cada pregunta
  (con la configuración usada mira todos; solo sortea la muestra de eventos); Random Forest queda por
  debajo de XGBoost en las 5 particiones, por 0,3 min, con 1,3 min de variación entre particiones.
- Otras cifras de las láminas: mediana de la duración 20,4 min, percentil 90 116 min, 22 % de los
  desvíos dura más de 1 h y concentra el 64 % del error del Random Forest, 9 de cada 10 desvíos
  ocurre entre las 6 y las 19 h.

## Cambios pedidos en la reunión con Tecfield (aplicados)

- Métrica nueva: **RMSE** (además de MAE y error mediano).
- **Importancia de variables** en los tres modelos y **primeras bifurcaciones del árbol**.
- Modelo nuevo recomendado: **XGBoost** (solo XGBoost; LightGBM se probó y se sacó).

## Resultados (validación cruzada por vehículo, 5 particiones, 13.632 eventos, 556 vehículos)

| Modelo | MAE (min) | RMSE (min) | Error mediano (min) | Mejora MAE |
|---|---|---|---|---|
| Mediana | 32,1 | 54,2 | 15,0 | — |
| Árbol de decisión | 28,8 | 47,5 | 14,3 | 10 % |
| Random Forest | 27,0 | 45,8 | 13,0 | 16 % |
| XGBoost | 27,3 | 46,1 | 13,1 | 15 % |

- Ablación (Random Forest): primer ping 29,4 → + hoja de ruta 27,0 → + rastreo previo 27,0.
- Variable más importante en los tres modelos: tipo de hoja (29–51 %). Rastreo previo pesa 3–10 %.
- Raíz del árbol: ¿tipoHDR informado? (con tipo: 6.828 eventos, mediana 40 min; sin tipo: 6.804, 14 min). Segundo nivel: distancia a la ruta.
- 42 % de los eventos no tiene GPS previo.
- Random Forest y XGBoost casi empatan; parámetros sin ajustar.
- El notebook final (solo XGBoost) se ejecutó completo y reproduce estas cifras.

## Reparto de la presentación (formal; números del pie de cada lámina)

| Orden | Quién | Láminas | Qué cuenta |
|---|---|---|---|
| 1º | Bautista | Portada, 1 a 6 | Índice, contexto y T₀, objetivo, trabajos relacionados, fuentes de datos, problemas de calidad |
| 2º | Sebastián | 7 a 13 | Corpus (7 pasos), de 37.720 a 13.632 desvíos, duración, atributos, tipo de hoja y hora, modelos, evaluación |
| 3º | Davor | 14 a 22 y "Gracias" | Resultados, particiones, dónde se equivocan, predicción vs. real, importancia, árbol, grupos de atributos, conclusiones, limitaciones |

Si la parte de Davor queda larga, Sebastián sigue con la 14 y la 15. El reparto es interno: no figura
en la presentación.

## Mensajes

- `reports/overleaf/mensajes.txt` tiene el mensaje para los profes (Germán y Sandra) y uno para Manu.
- **El mensaje a Manu no se envía.**
- Germán sugirió reenviarle a Manu el mail del 10/11 para pedir feedback; quedó descartado.

## Pendiente / a revisar

- Leer los tres informes completos antes de entregar (se revisaron cifras y referencias, no la redacción entera).
- La fecha de portada de los informes dice "7 de noviembre de 2026".
- Si se quiere el guion del orador en la presentación formal, falta agregarlo como notas.
