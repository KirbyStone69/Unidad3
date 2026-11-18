"""Tres pruebas de integración para la función gráfica de 32.py."""
import contextlib
import io
import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import RandomForestClassifier

BASE = Path(__file__).resolve().parent
N_ARBOLES = int(os.environ.get('N_ARBOLES', '25'))
if N_ARBOLES < 1:
    raise ValueError('N_ARBOLES debe ser un entero mayor que cero.')
plot_decision_regions = runpy.run_path(str(BASE / '32.py'))['plot_decision_regions']


class DecisionRegionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            data = runpy.run_path(str(BASE / 'eno.py'))
        cls.x = np.asarray(data['X'])[:, 2:4]
        cls.y = np.asarray(data['y'])
        cls.model = RandomForestClassifier(
            n_estimators=N_ARBOLES, random_state=1, n_jobs=1
        ).fit(cls.x, cls.y)
        print(f'\nPruebas con {N_ARBOLES} árboles.', flush=True)

    def tearDown(self):
        plt.close('all')

    def assert_rendered(self):
        output = io.BytesIO()
        plt.gcf().savefig(output, format='png')
        self.assertTrue(output.getvalue().startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertGreater(len(output.getvalue()), 1000)

    def test_1_especies_de_eno_sin_indices(self):
        plt.figure()
        plot_decision_regions(self.x, self.y, self.model)
        ax = plt.gca()
        self.assertEqual(ax.get_legend_handles_labels()[1], list(np.unique(self.y)))
        self.assertEqual(len(ax.collections), 4)
        for collection, species in zip(ax.collections[1:], np.unique(self.y)):
            np.testing.assert_array_equal(collection.get_offsets(), self.x[self.y == species])
        self.assert_rendered()

    def test_2_bosque_real_de_22_con_45_muestras_de_prueba(self):
        # Solo sustituir show para no abrir una ventana durante la prueba.
        with patch.object(plt, 'show'), contextlib.redirect_stdout(io.StringIO()):
            data = runpy.run_path(str(BASE / '22.py'))
        self.assertEqual(len(data['forest'].estimators_), N_ARBOLES)
        plt.close('all')
        plt.figure()
        plot_decision_regions(
            data['X_combined'], data['y_combined'], data['forest'],
            test_idx=range(len(data['X_train']), len(data['X_combined'])),
        )
        ax = plt.gca()
        self.assertEqual(len(ax.collections), 5)
        self.assertEqual(len(ax.collections[-1].get_offsets()), 45)
        np.testing.assert_array_equal(ax.collections[-1].get_offsets(), data['X_test'])
        self.assertGreater(data['forest'].score(data['X_test'], data['y_test']), 0.9)
        self.assert_rendered()

    def test_3_indices_numpy_y_lista_vacia(self):
        for indices in (np.array([0, 10, 149]), []):
            with self.subTest(indices=repr(indices)):
                plt.figure()
                plot_decision_regions(self.x.tolist(), self.y.tolist(), self.model, test_idx=indices)
                ax = plt.gca()
                if len(indices):
                    self.assertEqual(len(ax.collections), 5)
                    np.testing.assert_array_equal(ax.collections[-1].get_offsets(), self.x[indices])
                else:
                    self.assertEqual(len(ax.collections), 4)
                self.assert_rendered()
                plt.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
