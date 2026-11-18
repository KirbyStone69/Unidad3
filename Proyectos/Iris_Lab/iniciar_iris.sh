#!/usr/bin/env bash
set -euo pipefail
IRIS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$IRIS_DIR/.venv/bin/python" "$IRIS_DIR/app_iris.py" "$@"
