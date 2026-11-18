"""Ventana principal y coordinación de las vistas de Iris Lab."""
from pathlib import Path
import numpy as np
import pandas as pd
from PyQt6.QtCore import (QEasingCurve, QPropertyAnimation, QSortFilterProxyModel,
                          QThread, Qt, QTimer, pyqtSignal)
from PyQt6.QtGui import QAction, QColor, QKeySequence
from PyQt6.QtWidgets import (QAbstractItemView, QButtonGroup, QCheckBox, QComboBox,
    QDoubleSpinBox, QFileDialog, QFrame, QGraphicsOpacityEffect, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy, QSlider, QSpinBox,
    QStackedWidget, QTableView, QTabWidget, QVBoxLayout, QWidget)
from sklearn.tree import plot_tree

from . import core
from .widgets import (Bloom, Chart, COLORS, DataFrameModel, INK, MUTED, PURPLE,
                       STYLE, StatCard, icon, label, panel)


class DatasetProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.species = 'Todas las especies'
        self.query = ''
        self.setSortRole(Qt.ItemDataRole.UserRole)

    def filterAcceptsRow(self, row, parent):
        frame = self.sourceModel().frame
        record = frame.iloc[row]
        species_ok = self.species == 'Todas las especies' or record.Species == self.species
        query_ok = not self.query or any(self.query in str(v).lower() for v in record)
        return species_ok and query_ok

    def update_filter(self, species, query):
        self.beginFilterChange()
        self.species, self.query = species, query.lower().strip()
        self.endFilterChange()


class TrainingWorker(QThread):
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, frame, settings, parent=None):
        super().__init__(parent)
        self.frame, self.settings = frame.copy(), settings

    def run(self):
        try:
            result = core.train(self.frame, self.settings, self.progress.emit)
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, autotrain=True):
        super().__init__()
        self.setWindowTitle('Iris Lab · Laboratorio de Machine Learning')
        self.setWindowIcon(icon('predict', PURPLE))
        self.resize(1440, 960)
        self.setMinimumSize(1050, 720)
        self.setStyleSheet(STYLE)
        self.df = core.load_dataset(core.BASE / 'archive/Iris.csv')
        self.dataset_path = core.BASE / 'archive/Iris.csv'
        self.result = None
        self.worker = None
        self.animations = True
        self.cards = []
        self.page_effects = []
        self.fade = None
        root = QWidget()
        root.setObjectName('workspace')
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        shell.addWidget(self.make_sidebar())
        content = QVBoxLayout()
        content.setContentsMargins(32, 23, 32, 16)
        content.setSpacing(18)
        shell.addLayout(content, 1)
        content.addLayout(self.make_header())
        self.stack = QStackedWidget()
        content.addWidget(self.stack, 1)
        builders = [self.make_overview, self.make_dataset, self.make_exploration,
                    self.make_training, self.make_prediction]
        for builder in builders:
            page = QWidget()
            page.setObjectName('page')
            layout = QVBoxLayout(page)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(18)
            builder(layout)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.stack.addWidget(scroll)
            effect = QGraphicsOpacityEffect(scroll)
            scroll.setGraphicsEffect(effect)
            effect.setOpacity(1)
            self.page_effects.append(effect)
        footer = QHBoxLayout()
        self.status = label('Dataset local listo · Entrena tu primer modelo', 'muted')
        self.status.setStyleSheet('font-size:11px; color:#7a8390;')
        footer.addWidget(self.status, 1)
        footer.addWidget(label('PYTHON  /  PYQT6  /  SCIKIT-LEARN', 'eyebrow'))
        content.addLayout(footer)
        self.refresh_dataset()
        self.navigate(0)
        for key, slot in [('Ctrl+O', self.import_csv), ('Ctrl+E', self.export_dialog)]:
            action = QAction(self)
            action.setShortcut(QKeySequence(key))
            action.triggered.connect(slot)
            self.addAction(action)
        if autotrain:
            QTimer.singleShot(250, self.start_training)

    def make_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(230)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(22, 28, 22, 23)
        layout.setSpacing(12)
        brand = QHBoxLayout()
        mark = QLabel()
        mark.setPixmap(icon('predict', '#d7ed9e').pixmap(32, 32))
        brand.addWidget(mark)
        brand.addWidget(label('iris lab', 'brand'))
        brand.addStretch()
        layout.addLayout(brand)
        sub = label('MACHINE LEARNING STUDIO')
        sub.setStyleSheet('color:#8595aa; font-size:9px; letter-spacing:2px;')
        layout.addWidget(sub)
        layout.addSpacing(35)
        section = label('ESPACIO DE TRABAJO')
        section.setStyleSheet('font-size:9px; color:#718399; letter-spacing:1px;')
        layout.addWidget(section)
        self.nav_buttons = []
        self.nav_group = QButtonGroup(self)
        entries = [('overview', 'Resumen'), ('data', 'Dataset'), ('explore', 'Exploración'),
                   ('model', 'Entrenamiento'), ('predict', 'Predicción')]
        for i, (kind, text) in enumerate(entries):
            button = QPushButton(f'   {text}')
            button.setObjectName('nav')
            button.setIcon(icon(kind, '#aab6c6'))
            button.setCheckable(True)
            button.setMinimumHeight(48)
            self.nav_group.addButton(button, i)
            button.clicked.connect(lambda checked, idx=i: self.navigate(idx))
            self.nav_buttons.append(button)
            layout.addWidget(button)
        layout.addStretch()
        sidecard = QFrame()
        sidecard.setObjectName('sideCard')
        sidecard.setMinimumHeight(110)
        card_layout = QVBoxLayout(sidecard)
        card_layout.setContentsMargins(16, 17, 16, 17)
        side_title = label('UN DATASET. MUCHAS IDEAS.', wrap=True)
        side_title.setStyleSheet('font-size:9px; color:#c4ceda; font-weight:600;')
        card_layout.addWidget(side_title)
        text = label('De una flor a una predicción.\nExplora, aprende y experimenta.', wrap=True)
        text.setMinimumHeight(45)
        text.setStyleSheet('color:#96a7ba; font-size:11px; line-height:150%;')
        card_layout.addWidget(text)
        layout.addWidget(sidecard)
        self.animation_check = QCheckBox('Animaciones')
        self.animation_check.setChecked(True)
        self.animation_check.setStyleSheet('color:#a8b5c5; font-size:11px; padding:8px 0;')
        self.animation_check.toggled.connect(self.set_animations)
        layout.addWidget(self.animation_check)
        layout.addWidget(label('IRIS LAB  /  01', 'eyebrow'))
        return sidebar

    def make_header(self):
        row = QHBoxLayout()
        text = QVBoxLayout()
        self.breadcrumb = label('LABORATORIO  /  RESUMEN', 'eyebrow')
        self.page_title = label('Pequeños datos, grandes ideas.', 'pageTitle')
        self.page_subtitle = label('Tu laboratorio visual para entender el aprendizaje automático.', 'subtitle')
        text.addWidget(self.breadcrumb)
        text.addWidget(self.page_title)
        text.addWidget(self.page_subtitle)
        text.setSpacing(7)
        row.addLayout(text, 1)
        buttons = QVBoxLayout()
        self.import_button = QPushButton(' Abrir CSV')
        self.import_button.setIcon(icon('upload'))
        self.import_button.setToolTip('Importar CSV con las cuatro medidas de Iris y Species (Ctrl+O)')
        self.import_button.clicked.connect(self.import_csv)
        self.export_button = QPushButton(' Exportar experimento')
        self.export_button.setIcon(icon('export'))
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_dialog)
        self.export_button.setToolTip('Guardar datos, parámetros, predicciones y métricas en ZIP (Ctrl+E)')
        buttons.addWidget(self.import_button)
        buttons.addWidget(self.export_button)
        row.addLayout(buttons)
        return row

    def make_overview(self, layout):
        hero = QFrame()
        hero.setObjectName('hero')
        hero.setMinimumHeight(240)
        row = QHBoxLayout(hero)
        row.setContentsMargins(30, 17, 15, 17)
        text = QVBoxLayout()
        eyebrow = label('LA NATURALEZA TAMBIÉN TIENE PATRONES')
        eyebrow.setStyleSheet('color:#c0d793; font-size:10px; letter-spacing:2px; font-weight:600;')
        text.addWidget(eyebrow)
        title = label('De los datos\na las decisiones.')
        title.setStyleSheet('font-size:35px; font-weight:700; letter-spacing:-1px;')
        text.addWidget(title)
        subtitle = label('Cuatro medidas. Tres especies.\nDescubre lo que un árbol puede aprender de una flor.')
        subtitle.setStyleSheet('color:#b4bfd0; font-size:12px;')
        text.addWidget(subtitle)
        button = QPushButton('Explorar el dataset   →')
        button.setObjectName('heroButton')
        button.clicked.connect(lambda: self.navigate(1))
        text.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
        text.setSpacing(12)
        row.addLayout(text, 3)
        self.bloom = Bloom()
        row.addWidget(self.bloom, 2)
        layout.addWidget(hero)
        stats = QHBoxLayout()
        self.row_card = self.add_card(stats, 'Observaciones', 'flores en el dataset', COLORS[0])
        self.feature_card = self.add_card(stats, 'Características', 'medidas en centímetros', COLORS[1])
        self.class_card = self.add_card(stats, 'Especies', 'clases para predecir', COLORS[2])
        self.accuracy_card = self.add_card(stats, 'Exactitud', 'en el conjunto de prueba', '#8ca955')
        layout.addLayout(stats)
        bottom = QHBoxLayout()
        scatter_panel, box = panel('Un mapa de tus flores', 'Cada punto es una observación. El color indica su especie.')
        self.overview_plot = Chart()
        self.overview_plot.setMinimumHeight(235)
        self.overview_plot.setMaximumHeight(255)
        box.addWidget(self.overview_plot)
        bottom.addWidget(scatter_panel, 3)
        side, sidebox = panel('Un dataset equilibrado', 'Cómo se distribuyen las etiquetas')
        self.class_bars = []
        for species, color in zip(core.SPECIES, COLORS):
            group = QVBoxLayout()
            row = QHBoxLayout()
            row.addWidget(label('● ' + species.replace('Iris-', '').capitalize()))
            count = label('50', 'muted')
            row.addStretch()
            row.addWidget(count)
            group.addLayout(row)
            bar = QProgressBar()
            bar.setTextVisible(False)
            bar.setMaximumHeight(7)
            bar.setStyleSheet(f'QProgressBar::chunk {{ background:{color}; }}')
            group.addWidget(bar)
            sidebox.addLayout(group)
            sidebox.addSpacing(9)
            self.class_bars.append((count, bar))
        sidebox.addStretch()
        self.quality_label = label('', 'muted', True)
        self.quality_label.setStyleSheet('color:#7a8390; font-size:11px;')
        sidebox.addWidget(self.quality_label)
        link = QPushButton('Configurar un experimento  →')
        link.clicked.connect(lambda: self.navigate(3))
        sidebox.addWidget(link)
        bottom.addWidget(side, 2)
        layout.addLayout(bottom, 1)

    def add_card(self, layout, title, hint, color=PURPLE):
        card = StatCard(title, hint, color)
        self.cards.append(card)
        layout.addWidget(card)
        return card

    def table(self, model):
        view = QTableView()
        view.setModel(model)
        view.setAlternatingRowColors(True)
        view.setSortingEnabled(True)
        view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        view.verticalHeader().setVisible(False)
        view.verticalHeader().setDefaultSectionSize(43)
        view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        view.setMinimumHeight(220)
        return view

    def make_dataset(self, layout):
        frame, box = panel('La materia prima', 'Una fila = una flor. Cuatro características X → una etiqueta y (Species).')
        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText('Buscar en todas las columnas…')
        self.search.setClearButtonEnabled(True)
        self.species_filter = QComboBox()
        self.species_filter.addItems(['Todas las especies'] + core.SPECIES)
        self.species_filter.setMinimumWidth(200)
        controls.addWidget(self.search, 1)
        controls.addWidget(self.species_filter)
        export = QPushButton('Exportar vista CSV')
        export.clicked.connect(self.export_filtered)
        controls.addWidget(export)
        box.addLayout(controls)
        self.data_model = DataFrameModel(self.df, self)
        self.proxy = DatasetProxy(self)
        self.proxy.setSourceModel(self.data_model)
        self.data_table = self.table(self.proxy)
        self.data_table.setMinimumHeight(380)
        self.data_table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        box.addWidget(self.data_table, 1)
        self.table_count = label('', 'muted')
        box.addWidget(self.table_count)
        self.search.textChanged.connect(self.filter_data)
        self.species_filter.currentTextChanged.connect(self.filter_data)
        layout.addWidget(frame, 3)
        stats, statsbox = panel('Estadísticas descriptivas', 'Resumen de las cuatro características numéricas; Id no se utiliza para aprender.')
        self.stats_model = DataFrameModel()
        self.stats_table = self.table(self.stats_model)
        self.stats_table.setMinimumHeight(260)
        statsbox.addWidget(self.stats_table)
        layout.addWidget(stats, 2)

    def make_exploration(self, layout):
        frame, box = panel('Encuentra las relaciones', 'Cambia la visualización y las medidas. Usa la barra para acercar, mover o guardar.')
        row = QHBoxLayout()
        self.plot_kind = QComboBox()
        self.plot_kind.addItems(['Dispersión', 'Histogramas', 'Correlaciones', 'Distribución por especie'])
        row.addWidget(self.plot_kind, 2)
        self.x_axis = QComboBox()
        self.y_axis = QComboBox()
        for combo in [self.x_axis, self.y_axis]:
            combo.addItems(core.NAMES)
            combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.x_axis.setCurrentIndex(2)
        self.y_axis.setCurrentIndex(3)
        row.addWidget(label('X', 'eyebrow'))
        row.addWidget(self.x_axis, 2)
        row.addWidget(label('Y', 'eyebrow'))
        row.addWidget(self.y_axis, 2)
        box.addLayout(row)
        self.explore_plot = Chart(toolbar=True)
        self.explore_plot.setMinimumHeight(480)
        box.addWidget(self.explore_plot, 1)
        self.explore_insight = label('', 'muted', True)
        box.addWidget(self.explore_insight)
        layout.addWidget(frame, 1)
        for combo in [self.plot_kind, self.x_axis, self.y_axis]:
            combo.currentIndexChanged.connect(self.draw_exploration)

    def make_training(self, layout):
        top = QHBoxLayout()
        controls, box = panel('Diseña tu experimento', 'Configura, entrena y compara.')
        controls.setMinimumWidth(255)
        controls.setMaximumWidth(330)
        depth_row = QHBoxLayout()
        depth_row.addWidget(label('Profundidad máxima'))
        self.depth_value = label('3', 'tag')
        depth_row.addStretch()
        depth_row.addWidget(self.depth_value)
        box.addLayout(depth_row)
        self.depth = QSlider(Qt.Orientation.Horizontal)
        self.depth.setRange(1, 12)
        self.depth.setValue(3)
        self.depth.setToolTip('Limita los niveles de decisiones: 1 a 12')
        box.addWidget(self.depth)
        complexity = QHBoxLayout()
        complexity.addWidget(label('Simple', 'muted'))
        complexity.addStretch()
        complexity.addWidget(label('Complejo', 'muted'))
        box.addLayout(complexity)
        box.addSpacing(10)
        split_row = QHBoxLayout()
        split_row.addWidget(label('Datos para prueba'))
        self.split_value = label('30 %', 'tag')
        split_row.addStretch()
        split_row.addWidget(self.split_value)
        box.addLayout(split_row)
        self.split = QSlider(Qt.Orientation.Horizontal)
        self.split.setRange(15, 40)
        self.split.setValue(30)
        box.addWidget(self.split)
        self.split_description = label('105 entrenamiento · 45 prueba', 'muted')
        box.addWidget(self.split_description)
        box.addSpacing(10)
        row = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(label('Criterio'))
        self.criterion = QComboBox()
        self.criterion.addItem('Entropía', 'entropy')
        self.criterion.addItem('Gini', 'gini')
        left.addWidget(self.criterion)
        right = QVBoxLayout()
        right.addWidget(label('Semilla'))
        self.seed = QSpinBox()
        self.seed.setRange(0, 99999)
        self.seed.setValue(1)
        right.addWidget(self.seed)
        row.addLayout(left)
        row.addLayout(right)
        box.addLayout(row)
        box.addSpacing(12)
        self.train_button = QPushButton('Entrenar modelo   →')
        self.train_button.setObjectName('primary')
        self.train_button.clicked.connect(self.start_training)
        box.addWidget(self.train_button)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(7)
        box.addWidget(self.progress)
        self.model_status = label('Listo para tu primer experimento.', 'muted', True)
        self.model_status.setMinimumHeight(36)
        box.addWidget(self.model_status)
        box.addStretch()
        top.addWidget(controls, 1)
        score_panel, scorebox = panel('¿Qué aprendió el árbol?', 'Evaluación sobre flores que no se utilizaron para entrenar.')
        self.score_grid = QGridLayout()
        self.train_score = StatCard('Entrenamiento', 'exactitud al entrenar', COLORS[1])
        self.test_score = StatCard('Prueba', 'exactitud sobre prueba', COLORS[0])
        self.f1_score = StatCard('F1 macro', 'promedio entre especies', COLORS[2])
        self.score_cards = [self.train_score, self.test_score, self.f1_score]
        self.cards.extend(self.score_cards)
        for index, card in enumerate(self.score_cards):
            self.score_grid.addWidget(card, 0, index)
        self.compact_scores = False
        scorebox.addLayout(self.score_grid)
        self.partition_plot = Chart()
        self.partition_plot.canvas.setMinimumHeight(110)
        self.partition_plot.canvas.setMaximumHeight(130)
        scorebox.addWidget(self.partition_plot)
        self.baseline_label = label('Referencia y diagnóstico disponibles al entrenar.', 'muted', True)
        scorebox.addWidget(self.baseline_label)
        scorebox.addStretch()
        top.addWidget(score_panel, 3)
        layout.addLayout(top)
        frame, box = panel()
        self.model_tabs = QTabWidget()
        self.confusion_plot = Chart(toolbar=True)
        self.tree_plot = Chart(toolbar=True)
        self.cv_plot = Chart(toolbar=True)
        self.importance_plot = Chart(toolbar=True)
        self.report_model = DataFrameModel()
        self.predictions_model = DataFrameModel()
        self.report_table = self.table(self.report_model)
        self.predictions_table = self.table(self.predictions_model)
        for widget, title in [(self.confusion_plot, 'Matriz de confusión'), (self.tree_plot, 'Árbol'),
                              (self.cv_plot, 'Generalización'), (self.importance_plot, 'Importancia'),
                              (self.report_table, 'Métricas por clase'), (self.predictions_table, 'Predicciones')]:
            self.model_tabs.addTab(widget, title)
        self.model_tabs.setMinimumHeight(385)
        box.addWidget(self.model_tabs, 1)
        self.evaluation_note = label('La validación cruzada se realiza exclusivamente sobre entrenamiento.', 'muted', True)
        box.addWidget(self.evaluation_note)
        layout.addWidget(frame, 1)
        for control in [self.depth, self.split, self.seed]:
            control.valueChanged.connect(self.settings_changed)
        self.criterion.currentIndexChanged.connect(self.settings_changed)
        for chart in [self.confusion_plot, self.tree_plot, self.cv_plot, self.importance_plot]:
            chart.empty()

    def make_prediction(self, layout):
        frame, box = panel('Una flor que el modelo aún no conoce', 'Introduce cuatro medidas en centímetros para predecir su especie.')
        row = QHBoxLayout()
        inputs = QVBoxLayout()
        self.measurements = []
        grid = QGridLayout()
        grid.setHorizontalSpacing(22)
        grid.setVerticalSpacing(18)
        for i, (name, value) in enumerate(zip(core.NAMES, [5.1, 3.5, 1.4, .2])):
            group = QVBoxLayout()
            group.addWidget(label(name))
            control = QDoubleSpinBox()
            control.setRange(.01, 30)
            control.setDecimals(2)
            control.setSingleStep(.1)
            control.setSuffix(' cm')
            control.setValue(value)
            control.setMinimumHeight(42)
            control.valueChanged.connect(self.measurements_changed)
            group.addWidget(control)
            self.measurements.append(control)
            grid.addLayout(group, i // 2, i % 2)
        inputs.addLayout(grid)
        inputs.addSpacing(17)
        presets = QHBoxLayout()
        presets.addWidget(label('Ejemplos:', 'muted'))
        for i, name in enumerate(['Setosa', 'Versicolor', 'Virginica']):
            button = QPushButton(name)
            button.clicked.connect(lambda checked, idx=i: self.use_preset(idx))
            presets.addWidget(button)
        inputs.addLayout(presets)
        self.predict_button = QPushButton('Predecir especie   ✦')
        self.predict_button.setObjectName('primary')
        self.predict_button.setEnabled(False)
        self.predict_button.clicked.connect(self.make_prediction_result)
        inputs.addWidget(self.predict_button)
        self.predict_note = label('Primero entrena un modelo en la sección Entrenamiento.', 'muted', True)
        inputs.addWidget(self.predict_note)
        row.addLayout(inputs, 3)
        plant = Bloom()
        plant.setMinimumSize(240, 260)
        plant.setStyleSheet('background:#202f45; border-radius:15px;')
        self.prediction_bloom = plant
        row.addSpacing(25)
        row.addWidget(plant, 2)
        box.addLayout(row)
        layout.addWidget(frame)
        output, outputbox = panel('El resultado', 'La predicción usa el último modelo entrenado.')
        self.prediction_title = label('Tu próxima predicción empieza aquí.')
        self.prediction_title.setStyleSheet('font-size:28px; font-weight:700; color:#7860dc;')
        outputbox.addWidget(self.prediction_title)
        self.probability_bars = []
        for species, color in zip(core.SPECIES, COLORS):
            line = QHBoxLayout()
            name = label(species)
            name.setFixedWidth(160)
            line.addWidget(name)
            bar = QProgressBar()
            bar.setRange(0, 1000)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setStyleSheet(f'QProgressBar {{ height:14px; }} QProgressBar::chunk {{ background:{color}; }}')
            line.addWidget(bar, 1)
            percentage = label('—', 'muted')
            percentage.setFixedWidth(65)
            percentage.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            line.addWidget(percentage)
            outputbox.addLayout(line)
            self.probability_bars.append((bar, percentage))
        self.probability_note = label('Las probabilidades representan la distribución de clases en la hoja del árbol; no son confianza calibrada.', 'muted', True)
        outputbox.addWidget(self.probability_note)
        layout.addWidget(output, 1)
        self.probability_animations = []

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'score_grid'):
            compact = self.width() < 1280
            if compact != self.compact_scores:
                self.compact_scores = compact
                while self.score_grid.count():
                    self.score_grid.takeAt(0)
                if compact:
                    self.score_grid.addWidget(self.train_score, 0, 0)
                    self.score_grid.addWidget(self.test_score, 0, 1)
                    self.score_grid.addWidget(self.f1_score, 1, 0, 1, 2)
                else:
                    for index, card in enumerate(self.score_cards):
                        self.score_grid.addWidget(card, 0, index)

    def navigate(self, index):
        if not hasattr(self, 'stack') or not self.stack.count():
            return
        self.stack.setCurrentIndex(index)
        titles = [
            ('RESUMEN', 'Pequeños datos, grandes ideas.', 'Tu laboratorio visual para entender el aprendizaje automático.'),
            ('DATASET', 'Conoce cada observación.', 'Explora las flores que hacen posible el aprendizaje.'),
            ('EXPLORACIÓN', 'Los patrones se hacen visibles.', 'Compara medidas, distribuciones y relaciones entre especies.'),
            ('ENTRENAMIENTO', 'Deja que el árbol aprenda.', 'Experimenta con la complejidad y evalúa la generalización.'),
            ('PREDICCIÓN', '¿Qué flor tienes en mente?', 'Transforma cuatro medidas en una predicción explicable.')]
        tag, title, subtitle = titles[index]
        self.breadcrumb.setText('LABORATORIO  /  ' + tag)
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
            kind = ['overview', 'data', 'explore', 'model', 'predict'][i]
            button.setIcon(icon(kind, INK if i == index else '#aab6c6'))
        if self.fade:
            self.fade.stop()
        for effect in self.page_effects:
            effect.setOpacity(1)
        if self.animations:
            self.fade = QPropertyAnimation(self.page_effects[index], b'opacity', self)
            self.fade.setDuration(240)
            self.fade.setStartValue(.25)
            self.fade.setEndValue(1.)
            self.fade.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.fade.start()

    def set_animations(self, enabled):
        self.animations = enabled
        for card in self.cards:
            card.animations = enabled
            if not enabled and card.animation.state() == QPropertyAnimation.State.Running:
                value = card.animation.endValue()
                card.animation.stop()
                card._update(value)
        for name in ['bloom', 'prediction_bloom']:
            if hasattr(self, name):
                getattr(self, name).animate(enabled)
        if not enabled and self.fade:
            self.fade.stop()
            for effect in self.page_effects:
                effect.setOpacity(1)
        if hasattr(self, 'animation_check') and self.animation_check.isChecked() != enabled:
            self.animation_check.setChecked(enabled)

    def refresh_dataset(self):
        self.data_model.set_frame(self.df)
        self.filter_data()
        stats = self.df[core.FEATURES].describe().round(3)
        stats.index = ['Cantidad', 'Media', 'Desviación', 'Mínimo', '25 %', 'Mediana', '75 %', 'Máximo']
        self.stats_model.set_frame(stats.rename_axis('Estadístico').reset_index())
        self.row_card.set_value(len(self.df))
        self.feature_card.set_value(4)
        self.class_card.set_value(3)
        counts = self.df.Species.value_counts()
        for species, (count, bar) in zip(core.SPECIES, self.class_bars):
            n = int(counts[species])
            count.setText(f'{n}  ·  {n / len(self.df):.1%}')
            bar.setValue(round(n / counts.max() * 100))
        duplicates = int(self.df.duplicated(subset=core.FEATURES + ['Species']).sum())
        self.quality_label.setText(f'0 valores faltantes · {duplicates} medidas repetidas\nFuente: {self.dataset_path.name}')
        self.draw_scatter(self.overview_plot, 2, 3, compact=True)
        self.draw_exploration()
        self.settings_changed()

    def filter_data(self):
        self.proxy.update_filter(self.species_filter.currentText(), self.search.text())
        self.table_count.setText(f'{self.proxy.rowCount()} de {len(self.df)} observaciones  ·  Clic en un encabezado para ordenar  ·  Medidas en cm')

    def draw_scatter(self, chart, x, y, compact=False):
        ax = chart.axes()
        for species, color in zip(core.SPECIES, COLORS):
            group = self.df[self.df.Species == species]
            ax.scatter(group[core.FEATURES[x]], group[core.FEATURES[y]], c=color, s=32 if compact else 52,
                       alpha=.78, edgecolors='white', linewidths=.6, label=species.replace('Iris-', '').capitalize(), picker=5)
        ax.set_xlabel(core.NAMES[x] + ' (cm)')
        ax.set_ylabel(core.NAMES[y] + ' (cm)')
        ax.grid(True, color='#edf0eb', linewidth=.8)
        ax.legend(frameon=False, fontsize=8, loc='upper left')
        chart.finish()

    def draw_exploration(self):
        kind = self.plot_kind.currentIndex()
        x, y = self.x_axis.currentIndex(), self.y_axis.currentIndex()
        self.x_axis.setEnabled(kind in (0, 1, 3))
        self.y_axis.setEnabled(kind == 0)
        if kind == 0:
            self.draw_scatter(self.explore_plot, x, y)
            self.explore_insight.setText('Cada punto representa una flor. Los grupos separados sugieren características útiles para clasificar; los solapamientos muestran casos más difíciles.')
            return
        ax = self.explore_plot.axes()
        if kind == 1:
            for species, color in zip(core.SPECIES, COLORS):
                values = self.df.loc[self.df.Species == species, core.FEATURES[x]]
                ax.hist(values, bins=12, alpha=.5, color=color, label=species.replace('Iris-', '').capitalize(), edgecolor='white')
            ax.set_xlabel(core.NAMES[x] + ' (cm)')
            ax.set_ylabel('Número de flores')
            ax.legend(frameon=False)
            self.explore_insight.setText('Los histogramas muestran la frecuencia de las medidas por especie. Las áreas superpuestas ayudan a detectar distribuciones similares.')
        elif kind == 2:
            corr = self.df[core.FEATURES].corr().to_numpy()
            image = ax.imshow(corr, cmap='PuOr', vmin=-1, vmax=1)
            names = ['Largo sépalo', 'Ancho sépalo', 'Largo pétalo', 'Ancho pétalo']
            ax.set_xticks(range(4), names, rotation=12)
            ax.set_yticks(range(4), names)
            for i in range(4):
                for j in range(4):
                    ax.text(j, i, f'{corr[i,j]:.2f}', ha='center', va='center',
                            color='white' if abs(corr[i,j]) > .65 else INK, fontsize=13)
            self.explore_plot.figure.colorbar(image, ax=ax, shrink=.8, label='Correlación de Pearson')
            self.explore_insight.setText('La correlación va de −1 a 1 y mide asociación lineal. No demuestra causalidad. Species e Id se excluyen del cálculo.')
        else:
            groups = [self.df.loc[self.df.Species == s, core.FEATURES[x]] for s in core.SPECIES]
            boxes = ax.boxplot(groups, patch_artist=True, tick_labels=['Setosa', 'Versicolor', 'Virginica'],
                               widths=.45, medianprops={'color': INK, 'linewidth': 2})
            for patch, color in zip(boxes['boxes'], COLORS):
                patch.set_facecolor(color)
                patch.set_alpha(.55)
            rng = np.random.default_rng(1)
            for i, (values, color) in enumerate(zip(groups, COLORS), 1):
                ax.scatter(rng.normal(i, .045, len(values)), values, color=color, alpha=.5, s=13)
            ax.set_ylabel(core.NAMES[x] + ' (cm)')
            self.explore_insight.setText('La caja contiene el 50 % central de las observaciones; la línea indica la mediana. Los puntos permiten ver cada medida real.')
        self.explore_plot.finish()

    def current_settings(self):
        return core.Settings(self.depth.value(), self.split.value(),
                             self.criterion.currentData(), self.seed.value())

    def settings_changed(self):
        self.depth_value.setText(str(self.depth.value()))
        self.split_value.setText(f'{self.split.value()} %')
        n_test = int(np.ceil(len(self.df) * self.split.value() / 100))
        self.split_description.setText(f'{len(self.df)-n_test} entrenamiento · {n_test} prueba')
        if self.result and self.current_settings() != self.result.settings:
            self.model_status.setText('Cambios pendientes. Vuelve a entrenar para aplicarlos.')
        elif self.result:
            self.model_status.setText('Modelo actualizado · experimento reproducible')
        ax = self.partition_plot.axes()
        ax.barh([0], [len(self.df)-n_test], color=PURPLE, height=.4, label='Entrenamiento')
        ax.barh([0], [n_test], left=[len(self.df)-n_test], color='#d7ed9e', height=.4, label='Prueba')
        ax.set_xlim(0, len(self.df))
        ax.set_yticks([])
        ax.set_xlabel('Partición configurada · número de observaciones')
        ax.legend(loc='lower center', bbox_to_anchor=(.5, 1), ncol=2, frameon=False, fontsize=8)
        self.partition_plot.finish()

    def start_training(self):
        if self.worker and self.worker.isRunning():
            return
        self.train_button.setEnabled(False)
        self.import_button.setEnabled(False)
        self.export_button.setEnabled(False)
        for control in [self.depth, self.split, self.criterion, self.seed]:
            control.setEnabled(False)
        self.progress.setValue(0)
        self.worker = TrainingWorker(self.df, self.current_settings(), self)
        self.worker.progress.connect(self.training_progress)
        self.worker.completed.connect(self.training_complete)
        self.worker.failed.connect(self.training_failed)
        self.worker.finished.connect(self.training_finished)
        self.worker.start()

    def training_progress(self, value, message):
        self.progress.setValue(value)
        self.model_status.setText(message)
        self.status.setText(message)

    def training_complete(self, result):
        self.result = result
        self.accuracy_card.set_value(result.accuracy * 100, 2, ' %')
        self.train_score.set_value(result.train_accuracy * 100, 2, ' %')
        self.test_score.set_value(result.accuracy * 100, 2, ' %')
        self.f1_score.set_value(result.macro_f1 * 100, 2, ' %')
        self.progress.setValue(100)
        self.predict_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.predict_note.setText(f'Modelo activo: profundidad {result.settings.depth} · '
                                  f'{result.settings.criterion} · semilla {result.settings.seed}')
        self.model_status.setText('Modelo actualizado · experimento reproducible')
        hits = int(result.predictions.acierto.sum())
        self.status.setText(f'Experimento listo · {hits}/{len(result.test_indices)} aciertos en prueba · semilla {result.settings.seed}')
        self.baseline_label.setText(f'Referencia mayoritaria: {result.baseline:.1%}  ·  '
                                    f'{len(result.train_indices)} entrenamiento / {len(result.test_indices)} prueba\n'
                                    f'Último modelo: profundidad {result.settings.depth} · {result.settings.criterion}')
        self.report_model.set_frame(result.report.rename(columns={
            'precision': 'Precisión', 'recall': 'Sensibilidad', 'f1-score': 'F1', 'support': 'Muestras'}))
        self.predictions_model.set_frame(result.predictions)
        self.predictions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.draw_model(result)
        self.evaluation_note.setText(f'Validación cruzada solo en entrenamiento. {result.overlap} flores de prueba tienen medidas '
            'idénticas a alguna de entrenamiento: se conservan como observaciones distintas. '
            'Si son la misma flor, deben agruparse antes de partir.')
        self.clear_prediction('Modelo actualizado. Vuelve a predecir con las medidas actuales.')

    def training_finished(self):
        self.train_button.setEnabled(True)
        self.import_button.setEnabled(True)
        self.export_button.setEnabled(self.result is not None)
        for control in [self.depth, self.split, self.criterion, self.seed]:
            control.setEnabled(True)

    def training_failed(self, message):
        self.progress.setValue(0)
        self.model_status.setText('No se pudo entrenar: ' + message)
        self.status.setText('Entrenamiento fallido · revisa el dataset y la configuración')

    def draw_model(self, result):
        ax = self.confusion_plot.axes()
        ax.imshow(result.confusion, cmap='Purples', vmin=0)
        for i in range(3):
            for j in range(3):
                count = result.confusion[i,j]
                ax.text(j, i, str(count), ha='center', va='center', fontsize=20,
                        color='white' if count > result.confusion.max()/2 else INK)
        names = ['Setosa', 'Versicolor', 'Virginica']
        ax.set_xticks(range(3), names)
        ax.set_yticks(range(3), names)
        ax.set_xlabel('Especie predicha')
        ax.set_ylabel('Especie real')
        self.confusion_plot.finish()
        ax = self.tree_plot.axes()
        depth = result.model.get_depth()
        plot_tree(result.model, ax=ax, feature_names=['Largo sépalo', 'Ancho sépalo', 'Largo pétalo', 'Ancho pétalo'],
                  class_names=[s.replace('Iris-', '') for s in result.model.classes_],
                  filled=True, rounded=True, fontsize=8 if depth < 5 else 6,
                  max_depth=4 if depth > 4 else None, proportion=False)
        if depth > 4:
            ax.set_title('Vista hasta nivel 4 · las ramas (…) continúan en las reglas exportadas', fontsize=9, color=MUTED)
        self.tree_plot.finish()
        ax = self.cv_plot.axes()
        table = result.validation
        ax.plot(table.profundidad, table.entrenamiento * 100, 'o-', color='#239e93', linewidth=2, label='Entrenamiento CV')
        ax.errorbar(table.profundidad, table.validacion * 100, yerr=table.desviacion * 100,
                    fmt='o-', color=PURPLE, linewidth=2, capsize=4, label='Validación CV ± desviación')
        ax.set_xlabel('Profundidad máxima')
        ax.set_ylabel('Exactitud (%)')
        ax.grid(axis='y', color='#edf0eb')
        ax.legend(frameon=False, fontsize=9)
        self.cv_plot.finish()
        ax = self.importance_plot.axes()
        values = result.model.feature_importances_
        order = np.argsort(values)
        ax.barh(np.array(core.NAMES)[order], values[order], color=PURPLE, height=.55)
        ax.set_xlabel('Reducción de impureza acumulada (importancia en este árbol)')
        ax.set_xlim(0, max(.1, values.max() * 1.18))
        for i, value in enumerate(values[order]):
            ax.text(value + .008, i, f'{value:.1%}', va='center', fontsize=10, color=INK)
        self.importance_plot.finish()

    def measurements_changed(self):
        if hasattr(self, 'prediction_title'):
            self.clear_prediction('Medidas modificadas. Pulsa «Predecir especie».')

    def clear_prediction(self, message):
        self.prediction_title.setText(message)
        for animation in self.probability_animations:
            animation.stop()
        self.probability_animations.clear()
        for bar, percentage in self.probability_bars:
            bar.setValue(0)
            percentage.setText('—')

    def use_preset(self, index):
        values = self.df.loc[self.df.Species == core.SPECIES[index], core.FEATURES].iloc[0]
        for control, value in zip(self.measurements, values):
            control.setValue(float(value))
        if self.result:
            self.make_prediction_result()

    def make_prediction_result(self):
        if not self.result:
            return
        values = [control.value() for control in self.measurements]
        try:
            species, probabilities = core.predict(self.result, values)
        except ValueError as exc:
            self.status.setText(str(exc))
            return
        self.prediction_title.setText(species.replace('Iris-', '').capitalize())
        for animation in self.probability_animations:
            animation.stop()
        self.probability_animations.clear()
        for s, (bar, percentage) in zip(core.SPECIES, self.probability_bars):
            value = probabilities[s]
            percentage.setText(f'{value:.1%}')
            if self.animations:
                animation = QPropertyAnimation(bar, b'value', self)
                animation.setStartValue(bar.value())
                animation.setEndValue(round(value*1000))
                animation.setDuration(550)
                animation.setEasingCurve(QEasingCurve.Type.OutCubic)
                self.probability_animations.append(animation)
                animation.start()
            else:
                bar.setValue(round(value*1000))
        outside = any(value < self.df[col].min() or value > self.df[col].max()
                      for col, value in zip(core.FEATURES, values))
        text = ('Alguna medida está fuera del rango observado. La predicción puede ser poco fiable. '
                if outside else '')
        self.probability_note.setText(text + 'Probabilidades de las clases en la hoja del árbol; no son confianza calibrada.')

    def load_path(self, path):
        if self.worker and self.worker.isRunning():
            raise ValueError('Espera a que termine el entrenamiento antes de abrir otro dataset.')
        frame = core.load_dataset(path)  # Validar antes de reemplazar el estado visible.
        self.df, self.dataset_path = frame, Path(path)
        self.result = None
        self.predict_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.progress.setValue(0)
        self.model_status.setText('Dataset nuevo. Entrena un modelo para continuar.')
        self.predict_note.setText('Primero entrena el modelo con el nuevo dataset.')
        for card in [self.accuracy_card, self.train_score, self.test_score, self.f1_score]:
            card.animation.stop()
            card.value.setText('—')
        for chart in [self.confusion_plot, self.tree_plot, self.cv_plot, self.importance_plot]:
            chart.empty()
        self.report_model.set_frame(pd.DataFrame())
        self.predictions_model.set_frame(pd.DataFrame())
        self.baseline_label.setText('Referencia y diagnóstico disponibles al entrenar.')
        self.evaluation_note.setText('La validación cruzada se realiza exclusivamente sobre entrenamiento.')
        self.clear_prediction('Entrena el modelo con el nuevo dataset.')
        self.refresh_dataset()
        self.status.setText(f'Dataset cargado · {self.dataset_path.name} · {len(self.df)} observaciones')

    def import_csv(self):
        if self.worker and self.worker.isRunning():
            self.status.setText('Espera a que termine el entrenamiento antes de importar.')
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir dataset Iris', str(core.BASE / 'archive'), 'CSV (*.csv)')
        if path:
            try:
                self.load_path(path)
            except (ValueError, OSError, pd.errors.ParserError) as exc:
                QMessageBox.warning(self, 'No se pudo abrir el dataset', str(exc))

    def export_to(self, path):
        if self.result is None:
            raise ValueError('Primero entrena un modelo.')
        core.export_experiment(path, self.df, self.result)
        self.status.setText(f'Experimento exportado · {Path(path).name}')

    def export_dialog(self):
        if self.result is None:
            self.status.setText('Entrena un modelo antes de exportar.')
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Exportar experimento',
                                              str(core.BASE / 'experimento_iris.zip'), 'ZIP (*.zip)')
        if path:
            if not path.lower().endswith('.zip'):
                path += '.zip'
            try:
                self.export_to(path)
            except OSError as exc:
                QMessageBox.warning(self, 'No se pudo exportar', str(exc))

    def export_filtered(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Exportar filas visibles',
                                              str(core.BASE / 'iris_filtrado.csv'), 'CSV (*.csv)')
        if path:
            indices = [self.proxy.mapToSource(self.proxy.index(row, 0)).row()
                       for row in range(self.proxy.rowCount())]
            try:
                self.df.iloc[indices].to_csv(path, index=False)
                self.status.setText(f'{len(indices)} filas exportadas · {Path(path).name}')
            except OSError as exc:
                QMessageBox.warning(self, 'No se pudo exportar', str(exc))

    def closeEvent(self, event):
        # El trabajo está acotado al dataset local; esperar evita destruir un QThread activo.
        if self.worker and self.worker.isRunning():
            self.worker.wait()
        self.bloom.timer.stop()
        self.prediction_bloom.timer.stop()
        super().closeEvent(event)
