"""KNN sencillo: nodos Iris en dos dimensiones, sin scikit-learn."""
import argparse
import csv
import math
import random
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
COLORES = {'Iris-setosa': '#2374ab', 'Iris-versicolor': '#d98218',
           'Iris-virginica': '#7b4ab5'}


def cargar_iris():
    """Cada fila devuelve (Id, largo de pétalo, ancho de pétalo, especie)."""
    with (BASE / 'Iris.csv').open(encoding='utf-8-sig', newline='') as archivo:
        return [(int(f['Id']), float(f['PetalLengthCm']),
                 float(f['PetalWidthCm']), f['Species'])
                for f in csv.DictReader(archivo)]


def clasificar(datos, largo, ancho, k):
    """Distancia euclidiana y voto mayoritario; empate: vecino más cercano."""
    if type(k) is not int or not 1 <= k <= len(datos):
        raise ValueError('K debe ser un entero entre 1 y el número de flores.')
    if not math.isfinite(largo) or not math.isfinite(ancho):
        raise ValueError('Las medidas deben ser números finitos.')
    distancias = sorted(
        ((math.hypot(largo - fila[1], ancho - fila[2]), fila) for fila in datos),
        key=lambda par: (par[0], par[1][0]))
    vecinos = distancias[:k]
    votos = Counter(fila[3] for distancia, fila in vecinos)
    # En empate gana la clase empatada cuyo primer vecino es más cercano.
    especie = max(votos, key=votos.get)
    return especie, vecinos, dict(votos)


def crear_ventana():
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Slider, Button

    datos = cargar_iris()
    fig = plt.figure(figsize=(11, 7), facecolor='#fafaf7')
    fig.canvas.manager.set_window_title('Iris · K vecinos más cercanos')
    ax = fig.add_axes([.09, .36, .57, .53])
    fig.suptitle('Iris · K vecinos más cercanos', fontsize=19, fontweight='bold', y=.97)
    fig.text(.09, .915, 'Cada nodo es una flor. La estrella es la flor que quieres clasificar.', fontsize=10)
    resumen = fig.text(.71, .83, '', va='top', fontsize=11, linespacing=1.6)
    detalle = fig.text(.71, .57, '', va='top', fontsize=10, linespacing=1.5)
    inicial = (random.randint(10, 69) / 10, random.randint(1, 25) / 10)
    controles = [
        Slider(fig.add_axes([.25, .24, .38, .035]), 'Largo pétalo (cm)', .1, 7.5, valinit=inicial[0], valstep=.1),
        Slider(fig.add_axes([.25, .17, .38, .035]), 'Ancho pétalo (cm)', .1, 3.0, valinit=inicial[1], valstep=.1),
        Slider(fig.add_axes([.25, .10, .38, .035]), 'Vecinos K', 1, 15, valinit=5, valstep=1, valfmt='%0.0f'),
    ]
    boton = Button(fig.add_axes([.73, .10, .22, .065]), 'Punto aleatorio',
                   color='#e3edf5', hovercolor='#c5dfef')
    fig.text(.09, .035, 'Mueve las medidas o K: cambia al instante. Usa el botón para generar otra flor.', fontsize=10)

    def actualizar(_=None):
        x, y, k = controles[0].val, controles[1].val, int(controles[2].val)
        especie, vecinos, votos = clasificar(datos, x, y, k)
        ax.clear()
        for clase, color in COLORES.items():
            flores = [f for f in datos if f[3] == clase]
            ax.scatter([f[1] for f in flores], [f[2] for f in flores],
                       c=color, s=32, alpha=.65, label=clase.removeprefix('Iris-'))
        for distancia, fila in vecinos:
            ax.plot([x, fila[1]], [y, fila[2]], color='#333333', lw=1.3, alpha=.8)
            ax.scatter(fila[1], fila[2], s=115, facecolors='none', edgecolors='#222222', lw=1.4)
        ax.scatter([x], [y], marker='*', s=270, c='#e63946', edgecolors='black',
                   zorder=5, label='Flor nueva')
        ax.set(xlabel='Largo del pétalo (cm)', ylabel='Ancho del pétalo (cm)',
               xlim=(0, 7.6), ylim=(0, 3.1))
        # La misma escala en ambos ejes conserva visualmente las distancias.
        ax.set_aspect('equal', adjustable='box')
        ax.grid(alpha=.18)
        ax.legend(loc='upper left', fontsize=9)
        resumen.set_text('PREDICCIÓN\n' + especie.removeprefix('Iris-') +
                         f'\n\nVOTOS · K = {k}\n' +
                         '\n'.join(f'{c.removeprefix("Iris-")}: {votos.get(c, 0)}' for c in COLORES))
        resumen.set_color(COLORES[especie])
        filas = ['VECINOS · ID / distancia']
        filas += [f'#{f[0]:03d}   {d:.3f} cm' for d, f in vecinos[:5]]
        if k > 5:
            filas.append(f'… y {k - 5} vecinos más')
        filas += ['', 'Distancia: euclidiana.', 'Solo usa las 2 medidas', 'que muestra la gráfica.', '',
                  'Si hay empate: clase del', 'vecino empatado más cercano.']
        detalle.set_text('\n'.join(filas))
        fig.canvas.draw_idle()

    def generar_punto(_):
        # Actualizar las dos coordenadas juntas y recalcular una sola vez.
        anterior = tuple(round(c.val, 1) for c in controles[:2])
        nuevo = anterior
        while nuevo == anterior:
            nuevo = (random.randint(10, 69) / 10, random.randint(1, 25) / 10)
        for control, valor in zip(controles[:2], nuevo):
            control.eventson = False
            control.set_val(valor)
            control.eventson = True
        actualizar()

    boton.on_clicked(generar_punto)
    for control in controles:
        control.on_changed(actualizar)
    actualizar()
    # Mantener vivos los controles y permitir explorar la ventana interactivamente.
    fig.controles_knn = controles
    fig.boton_aleatorio = boton
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--guardar', type=Path, help='Guarda una imagen sin abrir la ventana.')
    args = parser.parse_args()
    if args.guardar:
        import matplotlib
        matplotlib.use('Agg')
    fig = crear_ventana()
    if args.guardar:
        fig.savefig(args.guardar, dpi=150, facecolor=fig.get_facecolor())
        print(f'Gráfica guardada: {args.guardar.resolve()}')
    else:
        import matplotlib.pyplot as plt
        plt.show()


if __name__ == '__main__':
    main()
