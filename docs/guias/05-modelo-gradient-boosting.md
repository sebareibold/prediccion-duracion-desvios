# Guía: Gradient boosting

## Qué es

Otro ensamble de árboles, pero construido distinto. Los árboles se entrenan **en secuencia**: el
primero hace una predicción, el segundo aprende a corregir el error del primero, el tercero el
del segundo, y así. La predicción final suma todos los aportes.

Random Forest promedia árboles independientes. *Gradient boosting* acumula árboles que se
corrigen entre sí.

## Para qué está

Es el segundo ensamble de la comparación (la cátedra pidió "un ensamble, Random Forest o
*gradient boosting*"). Se probaron los dos para ver si el tipo de ensamble cambia algo.

## Cómo está configurado

`HistGradientBoostingRegressor` de scikit-learn, que agrupa los valores de cada atributo en
intervalos para entrenar más rápido:

| Parámetro | Valor | Para qué |
|---|---|---|
| `categorical_features` | Marca de qué columnas son categóricas | Trata `ruta_cercana`, `franja`, `tipoVehiculo`, `tipoHDR` y `obra_id` como categorías de verdad |
| `random_state` | 0 | Resultados repetibles |
| resto | Valores por defecto | No se ajustaron |

## Cómo se entrena y se evalúa

- Aprende **log(1 + y)** y se vuelve a segundos al predecir.
- Validación cruzada de 5 particiones **por vehículo** (`GroupKFold`).
- Es el único de los tres modelos que usa los categóricos como categorías. Los otros dos los ven
  como números con orden.
- Maneja los valores vacíos directamente.
- También se usó para la tabla de aporte por grupo de atributos (primer ping, hoja de ruta,
  rastreo previo).

## Resultado

| MAE (min) | Error mediano (min) | Mejora del MAE vs. mediana |
|---|---|---|
| 27,3 | 13,1 | 15 % |

Casi igual que Random Forest (27,0).

### Aporte de cada grupo de atributos (con este modelo)

| Atributos | MAE (min) | Mejora vs. mediana |
|---|---|---|
| Primer ping | 29,4 | 8 % |
| + Hoja de ruta | 27,3 | 15 % |
| + Rastreo previo | 27,3 | 15 % |

La hoja de ruta aporta casi tanto como el primer ping. El rastreo previo no suma nada, porque
falta GPS previo en el 42 % de los eventos.

## Ventajas y límites

- **Ventaja:** suele rendir muy bien con datos tabulares y usa bien los categóricos.
- **Límite:** es más sensible a los parámetros que Random Forest, y acá no se ajustaron.
- **Límite:** con tanta cola larga, el error absoluto medio lo dominan pocos eventos muy largos.

## Qué decir en la reunión

> "Gradient boosting queda prácticamente empatado con Random Forest (27,3 contra 27,0 minutos).
> Con él medimos qué aporta cada grupo de atributos: la hoja de ruta ayuda y el rastreo previo no,
> por la falta de GPS."
