#!/usr/bin/env bash
set -euo pipefail
CARPETA="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Primero usa el entorno propio; en este equipo puede reutilizar el de Iris Lab.
for PYTHON_KNN in "$CARPETA/.venv/bin/python" /home/kirby/Descargas/kaggle/.venv/bin/python python3; do
    if "$PYTHON_KNN" -c 'import matplotlib' 2>/dev/null; then
        exec "$PYTHON_KNN" "$CARPETA/knn_iris.py" "$@"
    fi
done
printf 'Falta Matplotlib. Consulta la instalación en README.md.\n' >&2
exit 1
