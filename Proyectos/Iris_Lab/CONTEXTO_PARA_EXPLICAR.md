# Contexto del proyecto: fundamentos de Machine Learning con Iris

## Para el chat que lea este documento

Quiero que me expliques este proyecto desde cero, con lenguaje sencillo, ejemplos y visuales. Estoy aprendiendo fundamentos de Machine Learning. No quiero que solo describas el código: quiero entender qué hace cada paso, por qué se hace y cómo se conecta con los demás.

Explícame por bloques cortos y comprueba mi comprensión con preguntas. Distingue los conceptos generales de las decisiones específicas de este ejercicio. No necesitas rehacer la aplicación.

## 1. Qué se hizo

Se tomó como referencia el notebook de Kaggle **Simple EDA & Decision Tree Classification**, de Nourah:

https://www.kaggle.com/code/engnoura2/simple-eda-decision-tree-classification

Se revisó su copia descargada, `simple-eda-decision-tree-classification.ipynb`, y se adaptó a un dataset local de flores Iris. Después se crearon dos versiones en Python:

- **Terminal:** `analisis_iris.py`. Ejecuta el análisis y muestra diez pasos con explicaciones breves.
- **Interfaz gráfica:** `app_iris.py`, con PyQt6. Permite explorar datos, configurar el entrenamiento y predecir especies.

Los datos y el notebook original se conservaron.

## 2. Qué problema se quiere resolver

**Predecir la especie de una flor a partir de cuatro medidas.**

Es un problema de **aprendizaje supervisado de clasificación**: los ejemplos de entrenamiento incluyen tanto las medidas como la especie correcta.

No es regresión, aprendizaje no supervisado ni aprendizaje por refuerzo. Esos conceptos se mencionaron para distinguir los tipos de aprendizaje, pero no se implementaron.

## 3. Qué contiene el dataset

Archivo: `archive/Iris.csv`.

- 150 filas: cada fila representa una observación de una flor.
- 50 flores de cada especie: Iris-setosa, Iris-versicolor e Iris-virginica.
- Cuatro características numéricas, expresadas en centímetros.
- Una etiqueta de especie y un identificador.

| Columna | Significado | Uso |
|---|---|---|
| Id | Identificador de la fila | Se excluye del entrenamiento |
| SepalLengthCm | Largo del sépalo | Característica X |
| SepalWidthCm | Ancho del sépalo | Característica X |
| PetalLengthCm | Largo del pétalo | Característica X |
| PetalWidthCm | Ancho del pétalo | Característica X |
| Species | Especie conocida | Etiqueta y |

**X** es la matriz de características, con forma `(150, 4)`. **y** es el vector de 150 etiquetas.

La idea es aprender una función `f(X)` que produzca una predicción `y_hat`. La etiqueta verdadera `y` y la predicción `y_hat` no siempre coinciden.

Ejemplo:

```text
[5.1, 3.5, 1.4, 0.2] -> modelo -> Iris-setosa
```

## 4. Los diez pasos de la versión de terminal

### Paso 1. Carga del dataset

Se lee el CSV local con pandas. Se muestra su tamaño y una vista de las primeras filas.

### Paso 2. Revisión y preparación

Se comprueba que existan las columnas necesarias, que las medidas sean numéricas, positivas y finitas, y que no falten valores en las características o etiquetas.

Se cuentan los duplicados. Hay **3 filas repetidas al comparar medidas y especie sin Id**. Se conservan porque podrían corresponder a flores distintas. El árbol no requiere normalización de las características.

### Paso 3. Análisis exploratorio de datos (EDA)

Se calculan estadísticas y se revisa la distribución de las especies. Se generan:

- Correlaciones entre características.
- Histogramas de medidas.
- Relaciones entre pares de características, coloreadas por especie.
- Conteos por especie.
- Diagramas de caja por especie.

Estas gráficas ayudan a entender los datos; no prueban causalidad.

### Paso 4. Separación de características y etiqueta

Se define:

```python
X = df[['SepalLengthCm', 'SepalWidthCm', 'PetalLengthCm', 'PetalWidthCm']]
y = df['Species']
```

Id no se usa como característica.

### Paso 5. Partición de datos

Se usa `train_test_split` con:

- 70 % para entrenamiento: **105 flores**.
- 30 % para prueba: **45 flores**.
- `stratify=y`: mantiene la proporción de especies.
- `random_state=1`: permite repetir la misma partición.

Cada especie tiene 35 observaciones en entrenamiento y 15 en prueba. Las filas de entrenamiento y prueba son distintas.

**Limitación:** 2 flores de prueba tienen medidas idénticas a alguna de entrenamiento. Si fueran registros de la misma flor, habría que agruparlos antes de partir. Aquí se tratan como observaciones distintas.

### Paso 6. Entrenamiento

Se construye un `DecisionTreeClassifier` de scikit-learn con:

```python
criterion='entropy'
max_depth=3
random_state=1
```

`fit(X_train, y_train)` aprende preguntas sobre las medidas y produce reglas que llevan a una especie.

Es importante explicar qué son un nodo, un umbral, una rama, una hoja, la profundidad y la entropía.

### Paso 7. Predicción y evaluación

`predict(X_test)` genera las especies predichas. Se comparan con `y_test` mediante:

- Exactitud (accuracy).
- Precisión (precision).
- Sensibilidad o recuperación (recall).
- F1.
- Matriz de confusión.

También se compara con una referencia que siempre predice una especie mayoritaria.

No se usan R², MSE ni RMSE para evaluar las especies, porque son categorías.

### Paso 8. Interpretación del modelo

Se guardan la visualización del árbol, sus reglas y la importancia de las características.

Una de las reglas aprendidas es:

```text
Si el ancho del pétalo es <= 0.75 cm -> Iris-setosa.
```

La importancia de una característica describe su uso en ese árbol; no demuestra causalidad.

### Paso 9. Generalización, subajuste y sobreajuste

Se comparan profundidades 1, 2, 3, 4, 5 y sin límite mediante validación cruzada de cinco particiones, **solo sobre las 105 flores de entrenamiento**.

En cada ronda se entrena con cuatro partes y se valida con una. Se calculan la media y la desviación de la exactitud de validación, además del rendimiento de entrenamiento.

| Profundidad | Exactitud de entrenamiento CV | Exactitud de validación CV |
|---|---:|---:|
| 1 | 66.67 % | 66.67 % |
| 2 | 95.71 % | 92.38 % |
| 3 | 96.19 % | 95.24 % |
| 4 | 98.10 % | 92.38 % |
| 5 | 98.33 % | 93.33 % |
| Sin límite | 100.00 % | 92.38 % |

Lectura orientativa:

- Profundidad 1: señales de subajuste; el modelo resulta demasiado simple.
- Sin límite: señales de sobreajuste; logra 100 % en entrenamiento, pero valida peor.
- Profundidad 3: mejor media de validación entre estas opciones en este experimento.

La comparación es didáctica: no cambia automáticamente la profundidad del modelo final. El conjunto de prueba no se usa para elegir parámetros.

**Importante:** entrenamiento CV, validación CV y prueba final son resultados de evaluaciones distintas; sus porcentajes no se deben confundir.

### Paso 10. Uso del modelo y guardado

Se predice la especie de una flor de ejemplo. Se conservan métricas, tablas, predicciones, particiones, reglas y nueve gráficas en `resultados/`.

El programa incluye un pequeño ejercicio: comparar profundidades y explicar por qué un 100 % en entrenamiento no garantiza generalización.

## 5. Resultados del modelo inicial

Árbol de profundidad 3, entropía, semilla 1 y prueba del 30 %:

- Exactitud sobre las 105 flores de entrenamiento: **95.24 %**.
- Exactitud sobre las 45 flores de prueba: **95.56 %**.
- Aciertos en prueba: **43 de 45**.
- Referencia de clase mayoritaria en prueba: **33.33 %**.

Matriz de confusión: filas = especie real; columnas = especie predicha.

| Real / Predicha | Setosa | Versicolor | Virginica |
|---|---:|---:|---:|
| Setosa | 15 | 0 | 0 |
| Versicolor | 0 | 14 | 1 |
| Virginica | 0 | 1 | 14 |

Son resultados de una partición concreta de un dataset pequeño; no garantizan el mismo rendimiento con datos futuros.

## 6. Qué ofrece la interfaz PyQt6

Cinco secciones:

1. **Resumen:** indicadores, gráfica general y una ilustración de flor animada.
2. **Dataset:** tabla ordenable, búsqueda, filtro por especie, estadísticas y exportación CSV.
3. **Exploración:** dispersión, histogramas, correlaciones y cajas, con controles para visualizar y guardar.
4. **Entrenamiento:** profundidad, criterio, semilla y porcentaje de prueba configurables; métricas, árbol, matriz de confusión y comparación de profundidades.
5. **Predicción:** entrada de cuatro medidas y probabilidades de las especies.

El entrenamiento se ejecuta en segundo plano. Cambiar parámetros marca cambios pendientes; cargar otro dataset válido invalida el modelo anterior. Las animaciones pueden desactivarse.

Las probabilidades del árbol representan la distribución de clases en una hoja: **no equivalen a confianza calibrada**.

Se ejecutaron **20 pruebas automáticas** de análisis e interfaz, además de revisión de capturas. Las pruebas comprueban funcionamiento del software; no certifican su rendimiento con cualquier población de flores.

## 7. Correcciones frente al notebook de referencia

En el original, la sección de Iris sustituía el CSV por `load_iris` y reutilizaba predicciones/métricas del ejemplo de diabetes. La adaptación:

- Trabaja con el CSV local.
- Separa y evalúa los datos de Iris correctamente.
- Calcula la exactitud desde sus propias predicciones.
- Usa métricas de clasificación.
- Excluye Id de las características.

## 8. Archivos y ejecución

Carpeta del proyecto en el equipo original:

```text
/home/kirby/Descargas/kaggle
```

```text
analisis_iris.py       Versión sencilla de terminal
app_iris.py            Entrada de la aplicación gráfica
iniciar_iris.sh        Lanzador gráfico
iris_lab/core.py      Motor de análisis de la interfaz
iris_lab/widgets.py   Componentes visuales
iris_lab/window.py    Ventana y coordinación de la interfaz
archive/Iris.csv      Dataset utilizado
resultados/           Reportes, tablas, métricas y gráficas
capturas/             Capturas de la interfaz
tests/                Pruebas automáticas
README.md             Instrucciones
```

Desde la carpeta del proyecto:

```bash
# Terminal
.venv/bin/python analisis_iris.py

# Interfaz gráfica
./iniciar_iris.sh

# Pruebas
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
```

Herramientas: Python, pandas y NumPy para datos; Matplotlib y seaborn para gráficas; scikit-learn para aprendizaje y evaluación; PyQt6 para la interfaz.

## 9. Temas que quiero entender mejor

- Computación tradicional frente al paradigma de Machine Learning.
- Dataset, instancia, característica, etiqueta y función f(X).
- Ciclo de vida: problema, obtención de datos, calidad, exploración, preparación, partición, entrenamiento, validación, prueba, uso y monitoreo.
- Aprendizaje supervisado: clasificación frente a regresión.
- Aprendizaje no supervisado: estructuras ocultas y agrupamientos.
- Aprendizaje por refuerzo: agentes, acciones y recompensas.
- Generalización, subajuste, sobreajuste y equilibrio entre sesgo y varianza.
- Diferencia entre ajustar hiperparámetros y calibrar probabilidades.
- Diferencia entre entrenamiento, validación y prueba; prevención de fuga de datos.

El proyecto implementa principalmente el recorrido desde cargar datos existentes hasta evaluar y predecir. No implementa recolección de datos, despliegue productivo ni monitoreo.

## Petición para continuar la explicación

Explícame primero el recorrido de una sola flor desde una fila del CSV hasta su predicción. Después recorre los diez pasos, con pequeños ejemplos y diagramas. Usa los resultados reales de este documento y aclara qué aprende el árbol, qué decisiones toma el programador y qué se mide al evaluar. Al terminar cada bloque, hazme una pregunta breve antes de avanzar.
