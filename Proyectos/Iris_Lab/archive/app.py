import importlib.util
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import tempfile
import time
import unittest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QSignalSpy, QTest
from PyQt6.QtWidgets import QApplication


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('iris_lab.window'), 'Falta la interfaz gráfica')
        from iris_lab.window import MainWindow
        self.window = MainWindow(autotrain=False)
        self.window.resize(1440, 960)
        self.window.show()
        self.app.processEvents()
        self.window.set_animations(False)

    def tearDown(self):
        if hasattr(self, 'window'):
            self.window.close()
            self.app.processEvents()

    def wait_result(self):
        deadline = time.monotonic() + 20
        while self.window.result is None and time.monotonic() < deadline:
            QTest.qWait(30)
        self.assertIsNotNone(self.window.result, self.window.status.text())
        while self.window.worker and self.window.worker.isRunning():
            QTest.qWait(20)
        self.app.processEvents()

    def test_navigation_and_filter(self):
        QTest.mouseClick(self.window.nav_buttons[1], Qt.MouseButton.LeftButton)
        self.assertEqual(self.window.stack.currentIndex(), 1)
        self.window.species_filter.setCurrentText('Iris-setosa')
        self.assertEqual(self.window.proxy.rowCount(), 50)
        self.window.search.setText('5.1')
        self.assertGreater(self.window.proxy.rowCount(), 0)
        self.assertLess(self.window.proxy.rowCount(), 50)
        self.window.search.setText('inexistente')
        self.assertEqual(self.window.proxy.rowCount(), 0)

    def test_train_predict_and_export(self):
        self.window.navigate(3)
        self.window.depth.setValue(2)
        QTest.mouseClick(self.window.train_button, Qt.MouseButton.LeftButton)
        self.wait_result()
        self.assertEqual(self.window.result.settings.depth, 2)
        self.assertTrue(self.window.predict_button.isEnabled())
        self.window.navigate(4)
        for control, value in zip(self.window.measurements, [5.1, 3.5, 1.4, .2]):
            control.setValue(value)
        QTest.mouseClick(self.window.predict_button, Qt.MouseButton.LeftButton)
        self.assertIn('setosa', self.window.prediction_title.text().lower())
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'experiment.zip'
            self.window.export_to(path)
            self.assertTrue(path.exists())
        self.window.depth.setValue(4)
        self.assertIn('pendientes', self.window.model_status.text().lower())

    def test_charts_and_small_window(self):
        self.window.navigate(2)
        for i in range(self.window.plot_kind.count()):
            self.window.plot_kind.setCurrentIndex(i)
            self.app.processEvents()
            self.assertGreater(len(self.window.explore_plot.figure.axes), 0)
        self.window.resize(1100, 760)
        self.app.processEvents()
        self.assertLessEqual(self.window.minimumWidth(), 1100)

    def test_invalid_import_preserves_data(self):
        original = len(self.window.df)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.csv'
            path.write_text('a,b\n1,2\n')
            with self.assertRaises(ValueError):
                self.window.load_path(path)
        self.assertEqual(len(self.window.df), original)

    def test_new_dataset_invalidates_model(self):
        self.window.start_training()
        self.wait_result()
        from iris_lab.core import BASE
        self.window.load_path(BASE / 'archive/Iris.csv')
        self.assertIsNone(self.window.result)
        self.assertFalse(self.window.predict_button.isEnabled())
        self.assertFalse(self.window.export_button.isEnabled())

    def test_animations_finish_and_stop_when_disabled(self):
        self.window.set_animations(True)
        self.window.navigate(0)
        finished = QSignalSpy(self.window.row_card.animation.finished)
        self.window.row_card.set_value(150)
        self.assertTrue(finished.wait(2500), 'La animación no terminó')
        self.assertEqual(self.window.row_card.value.text(), '150')
        self.assertTrue(self.window.bloom.timer.isActive())
        self.window.navigate(1)
        self.assertFalse(self.window.bloom.timer.isActive())
        self.window.set_animations(False)
        self.window.navigate(0)
        self.assertFalse(self.window.bloom.timer.isActive())

    def test_table_models_sort_numeric_values(self):
        from iris_lab.widgets import DataFrameModel
        model = DataFrameModel(self.window.df)
        model.sort(0, Qt.SortOrder.DescendingOrder)
        self.assertEqual(int(model.frame.iloc[0].Id), 150)
        model.sort(1, Qt.SortOrder.AscendingOrder)
        self.assertEqual(float(model.frame.iloc[0].SepalLengthCm), 4.3)

    def test_worker_error_restores_controls(self):
        self.window.df = self.window.df.drop(columns='Species')
        self.window.start_training()
        deadline = time.monotonic() + 10
        while self.window.worker.isRunning() and time.monotonic() < deadline:
            QTest.qWait(20)
        self.app.processEvents()
        self.assertIsNone(self.window.result)
        self.assertTrue(self.window.train_button.isEnabled())
        self.assertIn('No se pudo entrenar', self.window.model_status.text())

    def test_pages_fit_small_viewport(self):
        self.window.resize(1100, 760)
        for index in range(5):
            self.window.navigate(index)
            self.app.processEvents()
            scroll = self.window.stack.widget(index)
            self.assertLessEqual(scroll.widget().width(), scroll.viewport().width(),
                                 f'Contenido horizontal cortado en página {index}')

    def test_safe_close_while_training(self):
        self.window.start_training()
        self.window.close()
        self.assertFalse(self.window.worker.isRunning())


if __name__ == '__main__':
    unittest.main()
