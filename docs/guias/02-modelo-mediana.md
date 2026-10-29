# Guía: Mediana (*baseline*)

## Qué es

Es la referencia más simple posible: **predice siempre la misma duración**, la mediana de los
eventos de entrenamiento, sin mirar ningún atributo.

## Para qué está

Es lo que pide el enunciado de Tecfield ("un baseline simple, la mediana de duración"). Un modelo
solo sirve si le gana. Todas las mejoras del proyecto se miden contra este.

## Cómo se usa en el notebook

- Está en la función `evaluar`, dentro de la validación cruzada.
- En cada partición calcula `np.median(y[entrenamiento])` y se lo asigna a todos los eventos de
  prueba.
- No usa log(1+y): trabaja directamente en segundos.
- Se evalúa con las mismas particiones por vehículo (`GroupKFold`, 5 particiones) que los otros
  modelos, para que la comparación sea justa.

## Resultado

| MAE (min) | Error mediano (min) |
|---|---|
| 32,1 | 15,0 |

## Por qué es una buena referencia

- Es lo que haría el operador sin ningún modelo: suponer que un desvío "típico" dura unos 20 min.
- No puede sobreajustar ni tener fugas: no usa atributos.

## Qué decir en la reunión

> "Si siempre predijéramos la mediana, nos equivocaríamos en promedio 32 minutos. Los modelos
> bajan ese error, pero no tanto: llegan a unos 27 minutos."
