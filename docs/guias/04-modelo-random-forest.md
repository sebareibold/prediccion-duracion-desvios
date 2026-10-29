# Guía: Random Forest

## Qué es

Un ensamble de muchos árboles de decisión. Cada árbol se entrena con una muestra distinta de los
eventos y de los atributos, y la predicción final es el **promedio** de todos. Un solo árbol se
equivoca de maneras distintas a otro, y al promediar esos errores se cancelan en parte.

## Para qué está

- El proyecto compara un árbol contra un ensamble. Los trabajos relacionados (Grigorev et al.,
  2022) usan ensambles de árboles como línea principal para predecir duración de incidentes.
- En este proyecto es el modelo con mejor resultado.

## Cómo está configurado

`RandomForestRegressor` de scikit-learn:

| Parámetro | Valor | Para qué |
|---|---|---|
| `n_estimators` | 200 | Cantidad de árboles |
| `min_samples_leaf` | 10 | Cada hoja necesita al menos 10 eventos |
| `n_jobs` | -1 | Usa todos los núcleos del procesador |
| `random_state` | 0 | Resultados repetibles |

## Cómo se entrena y se evalúa

- Aprende **log(1 + y)** y se vuelve a segundos al predecir.
- Validación cruzada de 5 particiones **por vehículo** (`GroupKFold`).
- Igual que el árbol, recibe los categóricos como códigos numéricos 0..k-1, con un orden que no
  significa nada. Es una limitación.
- Para aceptar valores vacíos necesita scikit-learn 1.4 o superior. `requirements.txt` no fija
  versiones.

## Resultado

| MAE (min) | Error mediano (min) | Mejora del MAE vs. mediana |
|---|---|---|
| **27,0** | **13,0** | **16 %** |

Es el mejor de los tres modelos, aunque por poco: *gradient boosting* queda a 0,3 minutos.

## Ventajas y límites

- **Ventaja:** más estable que un árbol y casi no hace falta ajustar parámetros.
- **Límite:** es más difícil de explicar que un solo árbol (son 200).
- **Límite:** no se ajustaron hiperparámetros. Los valores son una elección inicial.

## Qué decir en la reunión

> "Random Forest es el mejor modelo: baja el error un 16 % respecto de la mediana, de 32 a 27
> minutos. Es una mejora, pero con un error que sigue siendo alto."
