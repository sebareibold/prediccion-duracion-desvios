# Guía: Árbol de decisión

## Qué es

Un solo árbol que hace una serie de preguntas sobre los atributos ("¿la distancia a la ruta es
mayor a 800 m?", "¿es de madrugada?") y termina en una hoja con la **duración promedio** de los
eventos de entrenamiento que llegaron hasta ahí. Esa es su predicción.

## Para qué está

- Es el modelo simple y fácil de explicar, y lo pidió la cátedra en la reunión del 15/10: comparar
  un árbol de decisión con otro algoritmo contra un *benchmark*.
- Sirve de punto intermedio entre la mediana y los ensambles.

## Cómo está configurado

`DecisionTreeRegressor` de scikit-learn:

| Parámetro | Valor | Para qué |
|---|---|---|
| `max_depth` | 8 | Limita la profundidad para que no memorice |
| `min_samples_leaf` | 30 | Cada hoja necesita al menos 30 eventos |
| `random_state` | 0 | Resultados repetibles |

## Cómo se entrena y se evalúa

- Aprende **log(1 + y)**, porque la duración tiene cola larga. Al predecir se vuelve a segundos
  con `expm1`.
- Validación cruzada de 5 particiones **por vehículo** (`GroupKFold`): un móvil nunca está en
  entrenamiento y prueba a la vez.
- Los atributos categóricos (`ruta_cercana`, `franja`, `tipoVehiculo`, `tipoHDR`, `obra_id`) se
  pasan como códigos numéricos 0..k-1. El árbol los trata como si tuvieran un orden, y no lo
  tienen. Es una limitación.
- Los valores vacíos (por ejemplo, el rastreo previo faltante) los maneja el propio árbol. Esto
  requiere scikit-learn 1.3 o superior.

## Resultado

| MAE (min) | Error mediano (min) | Mejora del MAE vs. mediana |
|---|---|---|
| 28,8 | 14,4 | 10 % |

## Ventajas y límites

- **Ventaja:** se puede dibujar y explicar. Es fácil mostrar qué atributo usó para decidir.
- **Límite:** un solo árbol es inestable. Un cambio chico en los datos puede cambiar la
  estructura. Por eso los ensambles lo superan.

## Qué decir en la reunión

> "El árbol mejora un 10 % a la mediana. Es el modelo más interpretable, pero un solo árbol es
> inestable; por eso probamos también ensambles."
