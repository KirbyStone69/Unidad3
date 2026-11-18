"""Exporta películas completas sin alterar el CSV recolectado. No usa la red."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from .config import DEFAULT_CSV
from .scraper import canonical_movie_url

REQUIRED = ('titulo', 'resumen', 'reseña', 'genero', 'url')


def export_complete(source: Path, output: Path, minimum: int = 500) -> dict:
    if source.resolve() == output.resolve():
        raise ValueError('La entrega debe tener una ruta distinta al original')
    stats = {'leidas': 0, 'entregadas': 0, 'incompletas': 0, 'duplicadas': 0}
    rows, seen = [], set()
    with source.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        if not set(REQUIRED).issubset(columns):
            raise ValueError('Faltan columnas requeridas en el CSV de origen')
        for row in reader:
            stats['leidas'] += 1
            if None in row:
                raise ValueError('Fila con columnas sobrantes; revisar CSV de origen')
            row = {key: (value or '').strip() for key, value in row.items()}
            url = canonical_movie_url(row['url'])
            if not all(row.get(key) for key in REQUIRED) or not url:
                stats['incompletas'] += 1
                continue
            if url in seen:
                stats['duplicadas'] += 1
                continue
            seen.add(url)
            row['url'] = url
            rows.append(row)
    if not minimum <= len(rows) <= 1000:
        raise ValueError(f'Se requieren entre {minimum} y 1000 películas completas; hay {len(rows)}')
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(output)
    stats['entregadas'] = len(rows)
    stats['sha256_origen'] = hashlib.sha256(source.read_bytes()).hexdigest()
    stats['sha256_entrega'] = hashlib.sha256(output.read_bytes()).hexdigest()
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT_CSV)
    parser.add_argument('--out', type=Path, default=DEFAULT_CSV.parent/'peliculas_entrega.csv')
    args = parser.parse_args()
    stats = export_complete(args.input, args.out)
    args.out.with_suffix('.validacion.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f'CSV: {args.out}')


if __name__ == '__main__':
    main()
