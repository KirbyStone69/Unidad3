"""Iris Lab — laboratorio visual de aprendizaje supervisado."""
import os
from pathlib import Path

# También se aplica al importar la interfaz desde pruebas o desde otra aplicación.
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1] / '.mplconfig'))
