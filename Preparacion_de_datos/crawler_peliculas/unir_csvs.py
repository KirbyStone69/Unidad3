"""Une los CSV de todo el equipo en un solo archivo, con columnas comunes.

Uso:
    python3 -m crawler_peliculas.unir_csvs carpeta_o_archivos... -o data/todos.csv

- Acepta archivos sueltos o directorios (busca *.csv).
- Normaliza nombres de columna equivalentes (resena/reseña, año/anio, etc.).
- Garantiza las cinco columnas pedidas en el encargo, en ese orden.
- Deduplica por id de pelicula, URL o titulo+año.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Iterable

from .config import CSV_COLUMNS

REQUIRED = ("titulo", "resumen", "reseña", "genero", "url")

ALIASES = {
    "title": "titulo",
    "titulo": "titulo",
    "título": "titulo",
    "name": "titulo",
    "summary": "resumen",
    "sinopsis": "resumen",
    "resumen": "resumen",
    "description": "resumen",
    "review": "reseña",
    "resena": "reseña",
    "reseña": "reseña",
    "critica": "reseña",
    "crítica": "reseña",
    "genre": "genero",
    "generos": "genero",
    "género": "genero",
    "genero": "genero",
    "link": "url",
    "url": "url",
    "year": "anio",
    "año": "anio",
    "anio": "anio",
}

_MOVIE_RE = re.compile(r"/peliculas/pelicula-(\d+)")


def normalize_header(name: str) -> str:
    key = name.strip().lstrip("\ufeff").lower()
    key = re.sub(r"\s+", " ", key)
    return ALIASES.get(key, key)


def dedupe_key(row: dict[str, str]) -> str:
    url = (row.get("url") or "").strip()
    match = _MOVIE_RE.search(url)
    if match:
        return f"pelicula:{match.group(1)}"
    if url:
        return f"url:{url.lower().rstrip('/')}"
    title = (row.get("titulo") or "").strip().lower()
    year = (row.get("anio") or "").strip()
    return f"titulo:{title}|{year}" if title else ""


def expand_inputs(inputs: Iterable[str], output: Path) -> list[Path]:
    files: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.glob("*.csv")))
        elif path.exists():
            files.append(path)
        else:
            print(f"Aviso: no existe {path}", file=sys.stderr)
    return [path for path in files if path.resolve() != output.resolve()]


def merge(files: list[Path], output: Path, deduplicate: bool = True) -> dict[str, int]:
    rows: "OrderedDict[str, dict[str, str]]" = OrderedDict()
    extra_columns: list[str] = []
    stats = {"files": 0, "read": 0, "kept": 0, "duplicates": 0}

    for path in files:
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                continue
            stats["files"] += 1
            mapping = {name: normalize_header(name) for name in reader.fieldnames}
            for raw in reader:
                stats["read"] += 1
                row: dict[str, str] = {}
                for original, value in raw.items():
                    if original is None:
                        continue
                    key = mapping.get(original, normalize_header(original))
                    text = (value or "").strip()
                    if key and text and key not in row:
                        row[key] = text
                if not row.get("titulo") and not row.get("url"):
                    continue
                for key in row:
                    if key not in REQUIRED and key not in extra_columns:
                        extra_columns.append(key)

                key = dedupe_key(row) if deduplicate else f"{path}:{stats['read']}"
                if key and key in rows:
                    stats["duplicates"] += 1
                    continue
                rows[key or f"fila:{stats['read']}"] = row
                stats["kept"] += 1

    columns = list(REQUIRED)
    for column in list(CSV_COLUMNS) + extra_columns:
        if column not in columns:
            columns.append(column)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows.values():
            writer.writerow({column: row.get(column, "") for column in columns})

    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="unir_csvs",
        description="Une y deduplica los CSV del equipo.",
    )
    parser.add_argument("inputs", nargs="+", help="Archivos o directorios con CSV.")
    parser.add_argument("-o", "--out", type=Path, required=True, help="CSV de salida.")
    parser.add_argument(
        "--no-dedupe", action="store_true", help="No eliminar peliculas repetidas."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    files = expand_inputs(args.inputs, args.out)
    if not files:
        print("No se encontraron CSV de entrada.", file=sys.stderr)
        return 1
    stats = merge(files, args.out, deduplicate=not args.no_dedupe)
    print(
        f"Archivos: {stats['files']} | filas leidas: {stats['read']} | "
        f"guardadas: {stats['kept']} | duplicadas: {stats['duplicates']}"
    )
    print(f"Salida: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
