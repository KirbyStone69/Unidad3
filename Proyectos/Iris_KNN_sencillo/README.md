# Iris KNN sencillo

Una gráfica para entender **K vecinos más cercanos**. Cada punto representa una flor del CSV Iris. La estrella roja representa una flor nueva, y las líneas negras unen sus K vecinos más cercanos.

## Abrir en este equipo

Desde esta carpeta:

```bash
./iniciar.sh
```

El iniciador usa el entorno propio si existe o reutiliza el entorno de Iris Lab que ya está instalado en este equipo.

## Cómo usarlo

1. Mueve **Largo pétalo** y **Ancho pétalo** para cambiar la estrella.
2. Cambia **Vecinos K**, entre 1 y 15.
3. Observa las conexiones, los votos de las tres especies y la predicción.

Puedes probar estas medidas con K = 5:

| Largo (cm) | Ancho (cm) | Predicción |
|---|---|---|
| 1.4 | 0.2 | setosa |
| 4.5 | 1.5 | versicolor |
| 6.0 | 2.2 | virginica |

## Algoritmo, paso a paso

Está en `clasificar()` dentro de `knn_iris.py`, escrito sin scikit-learn:

1. Calcula la distancia de la estrella a cada flor: `sqrt((x1-x2)**2 + (y1-y2)**2)`.
2. Ordena las flores por distancia y toma las primeras K.
3. Cuenta los votos de cada especie.
4. Predice la especie con más votos. Si empatan, usa la clase empatada cuyo vecino está más cerca; si las distancias también empatan, usa el orden del Id del CSV.

Solo utiliza **largo y ancho del pétalo**, en centímetros, sin normalizar. La gráfica representa exactamente esas dos características y conserva la misma escala en ambos ejes. Algunos nodos se superponen porque varias flores tienen las mismas medidas.

Es una demostración de clasificación con las 150 flores como referencia. No calcula una precisión de prueba ni realiza una evaluación de generalización.

## Instalar en otro equipo

Requiere Python 3.10 o posterior y una sesión gráfica:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./iniciar.sh
```

## Pruebas y captura

```bash
.venv/bin/python -m unittest discover -v
./iniciar.sh --guardar vista_previa.png
```

`Iris.csv` es una copia del dataset local usado en Iris Lab, con 150 flores y sus cuatro medidas; esta práctica usa las dos columnas de pétalos y excluye `Id` de la distancia. Procedencia conservada de Iris Lab: [notebook de Kaggle](https://www.kaggle.com/code/engnoura2/simple-eda-decision-tree-classification).

Referencia para los controles: [Slider de Matplotlib](https://matplotlib.org/stable/gallery/widgets/slider_demo.html).
