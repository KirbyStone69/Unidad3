# Iris Lab · Machine Learning en Python

Dos versiones independientes que usan el mismo CSV local `archive/Iris.csv`.
El notebook descargado y los datos originales se conservan.

## Preparar el entorno

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

`requirements-lock.txt` contiene las versiones exactas utilizadas en este equipo.

## Versión sencilla de terminal

```bash
.venv/bin/python analisis_iris.py
```

El código y la salida explican, en español, los fundamentos y diez pasos:

1. Carga del dataset: filas como instancias y columnas como atributos.
2. Revisión de calidad: tipos, faltantes, medidas inválidas y duplicados.
3. Exploración: estadísticas, balance de etiquetas y gráficas.
4. Separación de características X y etiqueta y; se excluye Id.
5. Partición estratificada de entrenamiento y prueba.
6. Aprendizaje supervisado: entrenamiento del árbol.
7. Predicción y evaluación con métricas de clasificación.
8. Interpretación de reglas e importancia de características.
9. Generalización, subajuste, sobreajuste y comparación por validación cruzada.
10. Uso de f(X), conservación de resultados y ejercicio para practicar.

También distingue computación tradicional de machine learning, clasificación de regresión,
y aprendizaje supervisado de no supervisado y por refuerzo. Explica el ciclo de vida y
las herramientas utilizadas. La práctica implementada es clasificación supervisada.

En `resultados/` quedan nueve gráficas, estadísticas, métricas, predicciones, particiones,
reglas y `reporte.txt`, con todas las explicaciones y resultados. El script funciona
independientemente del directorio desde el que se ejecuta. Para experimentar están las
constantes `PROFUNDIDAD_MAXIMA`, `PORCENTAJE_PRUEBA` y `SEMILLA` al inicio.

## Aplicación gráfica PyQt6

```bash
./iniciar_iris.sh
# O directamente:
.venv/bin/python app_iris.py
```

Necesita una sesión gráfica de escritorio. En Linux utiliza el backend Qt de la sesión;
para entornos sin pantalla se puede usar `QT_QPA_PLATFORM=offscreen` en las pruebas.

- **Resumen:** indicadores reales, flor vectorial animada y vista general del dataset.
- **Dataset:** tabla ordenable, búsqueda, filtro por especie, estadísticas y exportación CSV.
- **Exploración:** dispersión con ejes seleccionables, histogramas, correlación y cajas;
  controles de zoom, desplazamiento y guardado de gráficas.
- **Entrenamiento:** profundidad, criterio, semilla y porcentaje de prueba; cálculo en
  segundo plano, matriz de confusión, árbol, generalización, importancia, métricas y predicciones.
- **Predicción:** cuatro medidas, ejemplos por especie y distribución de probabilidades
  del último árbol entrenado. Se indica cuando una medida sale del rango observado.

Las animaciones se pueden desactivar en la barra lateral. Al abrir la aplicación se
entrena automáticamente el modelo inicial. Cambiar parámetros marca los cambios pendientes;
las métricas siguen correspondiendo al último modelo hasta volver a entrenar. Cargar otro
CSV válido invalida el modelo anterior; un archivo inválido conserva los datos actuales.

`Ctrl+O` abre otro CSV con el esquema de Iris (las cuatro medidas y Species). Se requieren
las tres especies, al menos cinco flores por especie y medidas positivas y finitas.
`Ctrl+E` exporta un ZIP con dataset, parámetros, huella SHA-256, índices de partición,
métricas, predicciones, validación y reglas; las gráficas se guardan desde su barra individual.
La importación de archivos de otros problemas de clasificación no está contemplada.

## Metodología

Por defecto: 70 % entrenamiento y 30 % prueba, estratificación, semilla 1, entropía,
profundidad 3. La validación cruzada usa solo entrenamiento. El conjunto de prueba no
se usa para escoger parámetros. No se confunden probabilidades del árbol con confianza calibrada.

Los registros con medidas repetidas se informan y conservan: pueden ser flores distintas.
Si fueran la misma observación, habría que agruparlos antes de partir para evitar fuga de datos.
Una partición de prueba pequeña no garantiza el rendimiento futuro.

Correcciones respecto al notebook original: usar el CSV local sin sustituirlo por `load_iris`,
calcular métricas con las predicciones de Iris, excluir R²/MSE/RMSE porque las especies son
categorías y calcular la exactitud en lugar de escribir un porcentaje fijo.

## Pruebas

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
```

Las pruebas cubren validación de datos, particiones, métricas, reproducibilidad,
parámetros, predicción, exportación, navegación, filtros, orden numérico, estados de error,
animaciones, ventana pequeña, invalidación del modelo y cierre durante entrenamiento.
`capturas/` contiene imágenes renderizadas de la aplicación para revisión visual.

## Referencias

Adaptado del notebook de Nourah, publicado con licencia Apache 2.0:
https://www.kaggle.com/code/engnoura2/simple-eda-decision-tree-classification

Documentación oficial consultada para señales y conexiones entre hilos de PyQt6:
https://www.riverbankcomputing.com/static/Docs/PyQt6/signals_slots.html
