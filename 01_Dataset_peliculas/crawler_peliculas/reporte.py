"""Genera un reporte de calidad del CSV, util antes de entrenar modelos."""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections import Counter
from pathlib import Path

from .config import DATA_DIR, DEFAULT_CSV


def _mean(values: list[float]) -> str:
    return f"{statistics.mean(values):.2f}" if values else "sin datos"


def build_report(path: Path) -> str:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        rows = list(reader)

    lines: list[str] = []
    lines.append("REPORTE DEL DATASET")
    lines.append("=" * 60)
    lines.append(f"Archivo: {path}")
    lines.append(f"Películas (filas): {len(rows)}")
    lines.append(f"Columnas: {len(columns)}")

    urls = [row.get("url", "").strip() for row in rows]
    non_empty_urls = [url for url in urls if url]
    lines.append(f"URLs únicas: {len(set(non_empty_urls))}")
    lines.append(f"URLs repetidas: {len(non_empty_urls) - len(set(non_empty_urls))}")

    titles = [row.get("titulo", "").strip().lower() for row in rows]
    non_empty_titles = [title for title in titles if title]
    repeated_titles = sum(
        count - 1 for count in Counter(non_empty_titles).values() if count > 1
    )
    lines.append(f"Títulos repetidos (posibles remakes): {repeated_titles}")

    lines.append("")
    lines.append("VALORES FALTANTES")
    lines.append("-" * 60)
    for column in columns:
        missing = sum(1 for row in rows if not (row.get(column) or "").strip())
        percent = (missing / len(rows) * 100) if rows else 0.0
        lines.append(f"{column:16s} {missing:5d}  ({percent:5.1f}%)")

    genres: Counter[str] = Counter()
    directors: Counter[str] = Counter()
    years: Counter[str] = Counter()
    ratings: list[float] = []
    votes: list[float] = []
    with_review = 0

    for row in rows:
        for genre in (row.get("genero") or "").split("|"):
            genre = genre.strip()
            if genre:
                genres[genre] += 1
        for director in (row.get("director") or "").split("|"):
            director = director.strip()
            if director:
                directors[director] += 1
        year = (row.get("anio") or "").strip()
        if year.isdigit():
            years[year] += 1
        try:
            ratings.append(float(str(row.get("nota", "")).replace(",", ".")))
        except ValueError:
            pass
        try:
            votes.append(float(str(row.get("votos", "")).replace(",", ".")))
        except ValueError:
            pass
        if (row.get("reseña") or "").strip():
            with_review += 1

    lines.append("")
    lines.append("COBERTURA")
    lines.append("-" * 60)
    if rows:
        lines.append(f"Con reseña:              {with_review} ({with_review / len(rows) * 100:.1f}%)")
        lines.append(f"Con género:             {sum(1 for r in rows if (r.get('genero') or '').strip())}")
        lines.append(f"Con año:                {sum(1 for r in rows if (r.get('anio') or '').strip())}")
    lines.append(f"Nota media:             {_mean(ratings)}")
    if ratings:
        lines.append(f"Nota mínima/máxima:     {min(ratings):.1f} / {max(ratings):.1f}")
    lines.append(f"Votos (media):          {_mean(votes)}")

    lines.append("")
    lines.append("TOP GÉNEROS")
    lines.append("-" * 60)
    for genre, count in genres.most_common(15):
        lines.append(f"{genre:24s} {count:5d}")

    lines.append("")
    lines.append("AÑOS")
    lines.append("-" * 60)
    if years:
        ordered = sorted(years)
        lines.append(f"Rango: {ordered[0]} - {ordered[-1]}")
        for year, count in years.most_common(10):
            lines.append(f"{year:24s} {count:5d}")
    else:
        lines.append("Sin datos de año.")

    lines.append("")
    lines.append("TOP DIRECTORES")
    lines.append("-" * 60)
    for director, count in directors.most_common(10):
        lines.append(f"{director:24s} {count:5d}")

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reporte", description="Reporte de calidad del CSV de películas."
    )
    parser.add_argument(
        "csv", nargs="?", type=Path, default=DEFAULT_CSV, help="CSV a analizar."
    )
    parser.add_argument(
        "-o", "--out", type=Path, default=DATA_DIR / "reporte.txt",
        help="Archivo de salida.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.csv.exists():
        print(f"No existe {args.csv}", file=sys.stderr)
        return 1
    report = build_report(args.csv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"Guardado en {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
