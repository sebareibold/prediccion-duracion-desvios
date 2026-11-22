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
- `presentacion.pdf` (16 láminas)
- `01_exploracion_y_modelos.py` (notebook de marimo, igual al de `notebooks/`)

Fuentes LaTeX para Overleaf en `reports/overleaf/` (un zip por parte; compilar con pdfLaTeX).
La presentación se compila desde `reports/presentacion/presentacion.tex`.

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

## Reparto de la presentación

| Orden | Quién | Láminas | Qué cuenta |
|---|---|---|---|
| 1º | Bautista | 1 a 5 | Portada, índice, problema, objetivo, datos de Tecfield |
| 2º | Sebastián | 6 a 10 | Corpus (7 pasos), de 37.720 a 13.632 eventos, atributos, evaluación, árbol de decisión |
| 3º | Davor | 11 a 16 | Random Forest, XGBoost, importancia, resultados, grupos de atributos, conclusión |

El reparto es interno: no figura en la presentación.

## Mensajes

- `reports/overleaf/mensajes.txt` tiene el mensaje para los profes (Germán y Sandra) y uno para Manu.
- **El mensaje a Manu no se envía.**
- Germán sugirió reenviarle a Manu el mail del 10/11 para pedir feedback; quedó descartado.

## Pendiente / a revisar

- Leer los tres informes completos antes de entregar (se revisaron cifras y referencias, no la redacción entera).
- La fecha de portada de los informes dice "7 de noviembre de 2026".
- `README.md` y `docs/guias/03-modelo-arbol-de-decision.md` tienen cambios locales sin subir que no son de esta tanda.
