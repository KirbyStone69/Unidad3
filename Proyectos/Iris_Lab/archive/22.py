import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from eno import X, y


try:
    n_arboles = int(os.environ.get("N_ARBOLES", "25"))
except ValueError:
    raise ValueError("N_ARBOLES debe ser un entero mayor que cero.") from None
if n_arboles < 1:
    raise ValueError("N_ARBOLES debe ser un entero mayor que cero.")

# eno.py carga las cuatro medidas; la gráfica usa las dos del pétalo.
X_petal = np.asarray(X)[:, 2:4]
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)
X_train, X_test, y_train, y_test = train_test_split(
    X_petal, y_encoded, test_size=0.3, random_state=1, stratify=y_encoded
)

forest = RandomForestClassifier(
    criterion="gini", n_estimators=n_arboles, random_state=1, n_jobs=1
)
forest.fit(X_train, y_train)
print(f"Exactitud en prueba: {forest.score(X_test, y_test):.2%}")

X_combined = np.vstack((X_train, X_test))
y_combined = np.concatenate((y_train, y_test))
colors = ["#e57373", "#64b5f6", "#81c784"]
cmap = ListedColormap(colors)
xx, yy = np.meshgrid(
    np.linspace(X_combined[:, 0].min() - 0.5, X_combined[:, 0].max() + 0.5, 250),
    np.linspace(X_combined[:, 1].min() - 0.5, X_combined[:, 1].max() + 0.5, 250),
)
regions = forest.predict(np.column_stack((xx.ravel(), yy.ravel()))).reshape(xx.shape)

plt.figure(figsize=(8, 5))
plt.contourf(xx, yy, regions, levels=[-0.5, 0.5, 1.5, 2.5], alpha=0.3, cmap=cmap)
for index, species in enumerate(encoder.classes_):
    selected = y_combined == index
    plt.scatter(
        X_combined[selected, 0], X_combined[selected, 1],
        color=colors[index], edgecolors="black", label=species,
    )
plt.scatter(
    X_test[:, 0], X_test[:, 1], facecolors="none", edgecolors="black",
    s=100, linewidths=1.2, label="Datos de prueba",
)
plt.xlabel("Longitud del pétalo (cm)")
plt.ylabel("Ancho del pétalo (cm)")
plt.title(f"Random Forest — Iris ({n_arboles} árboles)")
plt.legend()
plt.tight_layout()
plt.show()
