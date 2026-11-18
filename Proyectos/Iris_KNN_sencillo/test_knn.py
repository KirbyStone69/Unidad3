import unittest
import math
from knn_iris import cargar_iris, clasificar


class KNNTests(unittest.TestCase):
    def test_distancia_y_mayoria(self):
        # Los tres primeros distan 1, 2 y 3; el punto lejano no debe votar.
        datos = [(1, 1.0, 0.0, 'A'), (2, 0.0, 2.0, 'B'),
                 (3, 3.0, 0.0, 'B'), (4, 9.0, 0.0, 'A')]
        especie, vecinos, votos = clasificar(datos, 0.0, 0.0, 3)
        self.assertEqual(especie, 'B')
        self.assertEqual([v[0] for v in vecinos], [1.0, 2.0, 3.0])
        self.assertEqual(votos, {'A': 1, 'B': 2})

    def test_empate_prefiere_clase_del_vecino_mas_cercano(self):
        datos = [(1, 2.0, 0.0, 'A'), (2, 1.0, 0.0, 'B')]
        self.assertEqual(clasificar(datos, 0, 0, 2)[0], 'B')

    def test_limites_y_valores_invalidos(self):
        datos = [(1, 1.0, 1.0, 'A')]
        for k in [0, 2, 1.5, True]:
            with self.assertRaises(ValueError):
                clasificar(datos, 1, 1, k)
        for x in [math.nan, math.inf]:
            with self.assertRaises(ValueError):
                clasificar(datos, x, 1, 1)
        with self.assertRaises(ValueError):
            clasificar([], 1, 1, 1)

    def test_csv_real_y_ejemplos_de_tres_especies(self):
        datos = cargar_iris()
        self.assertEqual(len(datos), 150)
        for x, y, especie in [(1.4, .2, 'Iris-setosa'),
                               (4.5, 1.5, 'Iris-versicolor'),
                               (6.0, 2.2, 'Iris-virginica')]:
            self.assertEqual(clasificar(datos, x, y, 5)[0], especie)


class VentanaTests(unittest.TestCase):
    def test_controles_actualizan_vecinos_y_prediccion(self):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from knn_iris import crear_ventana
        fig = crear_ventana()
        try:
            largo, ancho, k = fig.controles_knn
            self.assertEqual(len(fig.axes[0].lines), 5)
            k.set_val(15)
            self.assertEqual(len(fig.axes[0].lines), 15)
            largo.set_val(1.4)
            ancho.set_val(.2)
            self.assertIn('PREDICCIÓN\nsetosa', fig.texts[2].get_text())
            largo.set_val(6.0)
            ancho.set_val(2.2)
            self.assertIn('PREDICCIÓN\nvirginica', fig.texts[2].get_text())
        finally:
            plt.close(fig)


if __name__ == '__main__':
    unittest.main()
