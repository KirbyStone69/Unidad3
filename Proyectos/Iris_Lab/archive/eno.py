import csv
from pathlib import Path

from sklearn.tree import DecisionTreeClassifier, export_text


# Cargar las cuatro medidas de cada flor y su especie.
csv_path = Path(__file__).resolve().parent / "Iris.csv"
feature_names = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]

with csv_path.open(newline="", encoding="utf-8") as archivo:
    filas = list(csv.DictReader(archivo))

X = [[float(fila[nombre]) for nombre in feature_names] for fila in filas]
y = [fila["Species"] for fila in filas]

# Entrenar el árbol antes de consultar sus reglas.
tree = DecisionTreeClassifier(criterion="gini", max_depth=2, random_state=1)
tree.fit(X, y)

rules = export_text(tree, feature_names=feature_names)
print(rules)

