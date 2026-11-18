import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


def plot_decision_regions(x, y, classifier, test_idx=None, resolution=0.02):
    """Dibuja un clasificador entrenado con dos características y marca la prueba."""
    x = np.asarray(x)
    y = np.asarray(y)
    markers = ('s', 'X', 'o', '^', 'v')
    colors = ('red', 'blue', 'lightgreen', 'gray', 'cyan')
    classes = np.unique(y)
    cmap = ListedColormap([colors[i % len(colors)] for i in range(len(classes))])

    x1_min, x1_max = x[:, 0].min() - 1, x[:, 0].max() + 1
    x2_min, x2_max = x[:, 1].min() - 1, x[:, 1].max() + 1
    xx1, xx2 = np.meshgrid(
        np.arange(x1_min, x1_max, resolution),
        np.arange(x2_min, x2_max, resolution),
    )
    predictions = classifier.predict(np.column_stack((xx1.ravel(), xx2.ravel())))
    # Convertir también las especies de eno.py a índices para colorearlas.
    z = np.searchsorted(classes, predictions).reshape(xx1.shape)
    plt.contourf(
        xx1, xx2, z, alpha=0.3, cmap=cmap,
        levels=np.arange(len(classes) + 1) - 0.5,
    )
    plt.xlim(x1_min, x1_max)
    plt.ylim(x2_min, x2_max)

    for idx, cl in enumerate(classes):
        plt.scatter(
            x=x[y == cl, 0],
            y=x[y == cl, 1],
            alpha=0.8,
            color=colors[idx % len(colors)],
            marker=markers[idx % len(markers)],
            label=str(cl),
            edgecolors='black',
        )

    if test_idx is not None:
        x_test = x[test_idx, :]
        if len(x_test):
            plt.scatter(
                x_test[:, 0], x_test[:, 1],
                facecolors='none', edgecolors='black',
                alpha=1.0, linewidths=1, marker='o',
                s=100, label='Datos de prueba',
            )
