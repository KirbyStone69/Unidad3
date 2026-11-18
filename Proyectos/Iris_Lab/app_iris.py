#!/usr/bin/env python3
"""Inicia Iris Lab. Ejecutar con .venv/bin/python app_iris.py."""
import os
from pathlib import Path
import sys

os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent / '.mplconfig'))


def main():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    from iris_lab.window import MainWindow
    app = QApplication(sys.argv)
    app.setApplicationName('Iris Lab')
    app.setOrganizationName('Iris Lab')
    app.setFont(QFont('DejaVu Sans', 10))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
