"""Componentes Qt, animaciones y estilo visual de Iris Lab."""
import math
import numpy as np
import pandas as pd
from PyQt6.QtCore import (QAbstractTableModel, QEasingCurve, QModelIndex, QPointF,
                          QRectF, QSize, Qt, QTimer, QVariantAnimation)
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
                             QWidget)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from .core import SPECIES, COLORS

INK = '#18283b'
MUTED = '#7a8390'
PURPLE = '#7860dc'

STYLE = '''
QWidget { color: #18283b; font-family: 'Inter', 'DejaVu Sans', sans-serif; font-size: 13px; }
QMainWindow, QWidget#workspace, QWidget#page { background: #f5f5f1; }
QFrame#sidebar { background: #18283b; border: none; }
QFrame#sidebar QLabel { color: #b0bbca; background: transparent; }
QFrame#sidebar QLabel#brand { color: #fff; font-size: 25px; font-weight: 700; }
QPushButton#nav { text-align: left; padding: 15px 18px; color: #aab6c6;
 background: transparent; border: none; border-radius: 9px; font-size: 13px; }
QPushButton#nav:hover { background: #24364c; color: white; }
QPushButton#nav:checked { background: #d7ed9e; color: #18283b; font-weight: 700; }
QFrame#sideCard { background: #23354a; border: 1px solid #34465b; border-radius: 12px; }
QFrame#panel, QFrame#stat { background: #ffffff; border: 1px solid #e5e7e5; border-radius: 14px; }
QFrame#hero { background: #202f45; border: none; border-radius: 17px; }
QFrame#hero QLabel { color: #f6f7f5; background: transparent; }
QLabel#eyebrow { color: #858e9a; font-size: 10px; font-weight: 700; letter-spacing: 2px; }
QLabel#pageTitle { font-size: 29px; font-weight: 700; letter-spacing: -1px; }
QLabel#subtitle, QLabel#muted { color: #7a8390; }
QLabel#sectionTitle { font-size: 17px; font-weight: 700; }
QLabel#statValue { font-size: 31px; font-weight: 700; letter-spacing: -1px; }
QLabel#tag { background: #efebfb; color: #7054cb; border-radius: 6px; padding: 5px 10px; font-size: 11px; }
QPushButton { background: white; border: 1px solid #dfe3e6; border-radius: 8px; padding: 10px 15px; font-weight: 600; }
QPushButton:hover { border-color: #9a87e0; background: #f6f3ff; }
QPushButton:pressed { background: #e9e1fa; }
QPushButton:disabled { color: #9ca4ad; background: #eef0ee; border-color: #e2e5e3; }
QPushButton#primary { background: #7860dc; color: white; border: none; padding: 12px 18px; }
QPushButton#primary:hover { background: #6750ca; }
QPushButton#primary:disabled { background: #cbc3e8; color: #f6f4fc; }
QPushButton#heroButton { background: #d7ed9e; color: #18283b; border: none; padding: 12px 20px; }
QPushButton#heroButton:hover { background: #e5f6be; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #fff; border: 1px solid #dfe3e6;
 border-radius: 7px; padding: 8px 10px; min-height: 20px; selection-background-color: #7860dc; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #7860dc; }
QComboBox { padding-right: 28px; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: white; selection-background-color: #eee8fb; selection-color: #18283b; border: 1px solid #ddd; }
QSlider::groove:horizontal { background: #e7e9e4; height: 5px; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #8871df; border-radius: 2px; }
QSlider::handle:horizontal { background: #7860dc; width: 16px; margin: -6px 0; border-radius: 8px; }
QTableView { background: white; alternate-background-color: #f8f9f7; gridline-color: #eef0ed;
 border: none; selection-background-color: #eae4fb; selection-color: #18283b; outline: 0; }
QTableView::item { padding: 9px; border-bottom: 1px solid #eef0ed; }
QHeaderView::section { background: #f5f6f3; color: #798390; border: none;
 border-bottom: 1px solid #e4e7e2; padding: 12px 9px; font-size: 11px; font-weight: 600; }
QTableCornerButton::section { background: #f5f6f3; border: none; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 4px 0; }
QScrollBar::handle:vertical { background: #d1d7d7; border-radius: 4px; min-height: 35px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: #f1f2ef; height: 8px; }
QScrollBar::handle:horizontal { background: #d1d7d7; border-radius: 4px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QTabWidget::pane { border: none; background: white; }
QTabBar::tab { color: #818b95; background: transparent; padding: 13px 16px; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #7860dc; border-bottom: 2px solid #7860dc; font-weight: 700; }
QProgressBar { border: none; background: #eeeaf8; border-radius: 4px; height: 7px; text-align: center; }
QProgressBar::chunk { border-radius: 4px; background: #8871df; }
QToolBar { border: none; background: white; spacing: 3px; }
QToolButton { border: none; padding: 5px; border-radius: 5px; background: transparent; }
QToolButton:hover { background: #eee9fa; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 15px; height: 15px; border-radius: 4px; border: 1px solid #9da7b3; }
QCheckBox::indicator:checked { background: #7860dc; border-color: #7860dc; }
QToolTip { background: #18283b; color: white; border: none; padding: 6px; }
'''


def label(text, name=None, wrap=False):
    widget = QLabel(text)
    if name:
        widget.setObjectName(name)
    widget.setWordWrap(wrap)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    return widget


def panel(title=None, subtitle=None):
    frame = QFrame()
    frame.setObjectName('panel')
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 18)
    layout.setSpacing(12)
    if title:
        layout.addWidget(label(title, 'sectionTitle'))
    if subtitle:
        layout.addWidget(label(subtitle, 'muted', True))
    return frame, layout


def icon(kind, color=INK):
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(color), 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                        Qt.PenJoinStyle.RoundJoin))
    if kind == 'overview':
        for x, y in [(4, 4), (14, 4), (4, 14), (14, 14)]:
            painter.drawRoundedRect(QRectF(x, y, 6, 6), 1.5, 1.5)
    elif kind == 'data':
        painter.drawRoundedRect(QRectF(3, 4, 18, 16), 2, 2)
        painter.drawLine(3, 10, 21, 10)
        painter.drawLine(3, 15, 21, 15)
        painter.drawLine(10, 4, 10, 20)
    elif kind == 'explore':
        painter.drawLine(4, 3, 4, 20)
        painter.drawLine(4, 20, 22, 20)
        for x, y in [(8, 15), (12, 10), (17, 13), (19, 5)]:
            painter.drawEllipse(QPointF(x, y), 1.5, 1.5)
    elif kind == 'model':
        painter.drawLine(12, 7, 12, 12)
        painter.drawLine(6, 12, 18, 12)
        painter.drawLine(6, 12, 6, 17)
        painter.drawLine(18, 12, 18, 17)
        for x, y in [(12, 5), (6, 19), (18, 19)]:
            painter.drawEllipse(QPointF(x, y), 2.5, 2.5)
    elif kind == 'predict':
        path = QPainterPath(QPointF(12, 2))
        for x, y in [(15, 9), (22, 12), (15, 15), (12, 22), (9, 15), (2, 12), (9, 9)]:
            path.lineTo(x, y)
        path.closeSubpath()
        painter.drawPath(path)
    elif kind == 'upload':
        painter.drawRoundedRect(QRectF(3, 8, 18, 12), 2, 2)
        painter.drawLine(12, 15, 12, 3)
        painter.drawLine(8, 7, 12, 3)
        painter.drawLine(16, 7, 12, 3)
    elif kind == 'export':
        painter.drawLine(12, 2, 12, 15)
        painter.drawLine(8, 11, 12, 15)
        painter.drawLine(16, 11, 12, 15)
        painter.drawLine(4, 14, 4, 21)
        painter.drawLine(4, 21, 20, 21)
        painter.drawLine(20, 21, 20, 14)
    else:
        painter.drawLine(4, 12, 20, 12)
        painter.drawLine(15, 7, 20, 12)
        painter.drawLine(15, 17, 20, 12)
    painter.end()
    return QIcon(pixmap)


class StatCard(QFrame):
    def __init__(self, title, hint, color=PURPLE):
        super().__init__()
        self.setObjectName('stat')
        self.setMinimumHeight(128)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 17, 20, 16)
        title_row = QHBoxLayout()
        title_row.addWidget(label(title.upper(), 'eyebrow'))
        dot = label('●')
        dot.setStyleSheet(f'color:{color}; font-size:13px;')
        title_row.addStretch()
        title_row.addWidget(dot)
        layout.addLayout(title_row)
        self.value = label('—', 'statValue')
        layout.addWidget(self.value)
        self.hint = label(hint, 'muted')
        self.hint.setStyleSheet('font-size:11px; color:#7a8390;')
        layout.addWidget(self.hint)
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(700)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(self._update)
        self.decimals = 0
        self.suffix = ''
        self.animations = True

    def set_value(self, value, decimals=0, suffix=''):
        self.animation.stop()
        self.decimals, self.suffix = decimals, suffix
        if self.animations:
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(float(value))
            self.animation.start()
        else:
            self._update(float(value))

    def _update(self, value):
        self.value.setText(f'{value:.{self.decimals}f}{self.suffix}')


class Bloom(QWidget):
    """Ilustración vectorial propia; la animación se pausa cuando no es visible."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(240, 215)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.phase = 0.0
        self.enabled = True
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.advance)

    def advance(self):
        self.phase += .018
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if self.enabled:
            self.timer.start()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def animate(self, enabled):
        self.enabled = enabled
        self.timer.setInterval(40)
        if enabled and self.isVisible():
            self.timer.start()
        else:
            self.timer.stop()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        scale = min(self.width() / 290, self.height() / 250)
        p.scale(scale, scale)
        p.setPen(QPen(QColor('#3a4960'), 1))
        for radius in [61, 96, 119]:
            p.drawEllipse(QPointF(0, 0), radius, radius)
        p.save()
        p.rotate(7 * math.sin(self.phase / 2))
        for i in range(6):
            p.save()
            p.rotate(i * 60)
            path = QPainterPath(QPointF(0, -5))
            path.cubicTo(-50, -43, -42, -105, 0, -100)
            path.cubicTo(42, -105, 50, -43, 0, -5)
            color = QColor(['#b3a0f0', '#8f78d6', '#ccbdf8'][i % 3])
            color.setAlpha(205)
            p.setBrush(color)
            p.setPen(QPen(QColor('#d8cdf4'), 1))
            p.drawPath(path)
            p.drawLine(0, -15, 0, -86)
            p.restore()
        p.restore()
        p.setBrush(QColor('#daeea2'))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(0, 0), 15, 15)
        p.setBrush(QColor('#24354b'))
        p.drawEllipse(QPointF(0, 0), 5, 5)
        for i in range(3):
            angle = self.phase * .35 + i * 2.094
            point = QPointF(119 * math.cos(angle), 119 * math.sin(angle))
            p.setBrush(QColor(['#d7ed9e', '#b3a0f0', '#f0be77'][i]))
            p.drawEllipse(point, 4, 4)
        p.end()


class DataFrameModel(QAbstractTableModel):
    def __init__(self, frame=None, parent=None):
        super().__init__(parent)
        self.frame = frame if frame is not None else pd.DataFrame()

    def set_frame(self, frame):
        self.beginResetModel()
        self.frame = frame.copy()
        self.endResetModel()

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        if not 0 <= column < len(self.frame.columns):
            return
        self.beginResetModel()
        self.frame = self.frame.sort_values(
            self.frame.columns[column], ascending=order == Qt.SortOrder.AscendingOrder,
            kind='stable').reset_index(drop=True)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.frame)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.frame.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        value = self.frame.iloc[index.row(), index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            if isinstance(value, (bool, np.bool_)):
                return 'Sí' if value else 'No'
            if isinstance(value, (float, np.floating)):
                return f'{value:.3f}'.rstrip('0').rstrip('.')
            return str(value)
        if role == Qt.ItemDataRole.UserRole:
            if isinstance(value, np.generic):
                return value.item()
            return value
        if role == Qt.ItemDataRole.ForegroundRole and str(value) in SPECIES:
            return QColor(COLORS[SPECIES.index(str(value))])
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self.frame.columns[section]) if orientation == Qt.Orientation.Horizontal else str(section + 1)
        return None


class Toolbar(NavigationToolbar2QT):
    toolitems = [item for item in NavigationToolbar2QT.toolitems
                 if item[0] in ('Home', 'Back', 'Forward', 'Pan', 'Zoom', 'Save', None)]

    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)
        self.setIconSize(QSize(17, 17))
        translations = {'Home': 'Restablecer', 'Back': 'Anterior', 'Forward': 'Siguiente',
                        'Pan': 'Desplazar', 'Zoom': 'Acercar', 'Save': 'Guardar gráfica'}
        for action in self.actions():
            if action.text() in translations:
                action.setToolTip(translations[action.text()])


class Chart(QWidget):
    def __init__(self, toolbar=False):
        super().__init__()
        self.figure = Figure(figsize=(6, 4), dpi=100, facecolor='white', layout='constrained')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if toolbar:
            self.toolbar = Toolbar(self.canvas, self)
            layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def axes(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        return ax

    def finish(self):
        for ax in self.figure.axes:
            ax.tick_params(colors='#7a8390', labelsize=9, length=0, pad=7)
            ax.xaxis.label.set_color('#6a7583')
            ax.yaxis.label.set_color('#6a7583')
            ax.xaxis.label.set_size(10)
            ax.yaxis.label.set_size(10)
            ax.spines[['top', 'right']].set_visible(False)
            ax.spines[['left', 'bottom']].set_color('#e7e9e6')
            ax.set_axisbelow(True)
        if hasattr(self, 'toolbar'):
            self.toolbar.update()
        self.canvas.draw_idle()

    def empty(self, text='Entrena un modelo para ver los resultados'):
        ax = self.axes()
        ax.text(.5, .5, text, ha='center', va='center', color='#8b94a0',
                fontsize=12, transform=ax.transAxes, wrap=True)
        ax.set_axis_off()
        self.finish()
