"""Punto de entrada del crawler.

Uso:
    python3 -m crawler_peliculas --max 1000 --delay 1.0
    python3 -m crawler_peliculas --max 10 --fresh --out data/muestra.csv
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
from pathlib import Path

from .config import DEFAULT_CSV, DEFAULT_LOG, Settings
from .crawler import Crawler
from .http_client import HttpClient
from .storage import Storage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crawler_peliculas",
        description="Crawler academico de metadatos de peliculas de SensaCine.",
    )
    parser.add_argument(
        "--max", dest="max_movies", type=int, default=1000,
        help="Numero maximo de peliculas a guardar (default: 1000).",
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Segundos entre peticiones (default: 1.0).",
    )
    parser.add_argument(
        "--max-listing-pages", type=int, default=200,
        help="Maximo de paginas de listado/genero a visitar (default: 200).",
    )
    parser.add_argument(
        "--similar-limit", type=int, default=20,
        help="Maximo de peliculas similares a encolar por pelicula (default: 20).",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_CSV,
        help="Ruta del CSV de salida.",
    )
    parser.add_argument(
        "--log", type=Path, default=DEFAULT_LOG,
        help="Ruta del archivo de log.",
    )
    parser.add_argument(
        "--fresh", action="store_true",
        help="Empezar de cero: borra el CSV de salida si existe.",
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="No leer/escribir la cache de HTML.",
    )
    parser.add_argument(
        "--timeout", type=float, default=25.0,
        help="Timeout por peticion en segundos (default: 25).",
    )
    parser.add_argument(
        "--retries", type=int, default=4,
        help="Reintentos por peticion (default: 4).",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Mostrar mensajes de depuracion.",
    )
    return parser


def configure_logging(log_path: Path, verbose: bool) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("crawler")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
    return logger


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_movies <= 0:
        print("--max debe ser mayor que 0", file=sys.stderr)
        return 1
    if not math.isfinite(args.delay) or args.delay < 0:
        print("--delay debe ser finito y no negativo", file=sys.stderr)
        return 1

    if not math.isfinite(args.timeout) or args.timeout <= 0 or args.retries < 1 or args.max_listing_pages < 1 or args.similar_limit < 0:
        print("Límites inválidos: timeout, reintentos y páginas deben ser positivos; similares no negativo", file=sys.stderr)
        return 1

    settings = Settings(
        max_movies=args.max_movies,
        delay=args.delay,
        max_listing_pages=args.max_listing_pages,
        similar_limit=args.similar_limit,
        use_cache=not args.no_cache,
        fresh=args.fresh,
        csv_path=args.out,
        log_path=args.log,
        timeout=args.timeout,
        retries=args.retries,
    )
    logger = configure_logging(settings.log_path, args.verbose)

    storage = Storage(settings.csv_path, fresh=settings.fresh, logger=logger)
    client = HttpClient(
        delay=settings.delay,
        timeout=settings.timeout,
        retries=settings.retries,
        use_cache=settings.use_cache,
        logger=logger,
    )
    crawler = Crawler(client, storage, settings, logger=logger)

    interrupted = False
    try:
        stats = crawler.run()
    except KeyboardInterrupt:
        interrupted = True
        stats = crawler.stats
        logger.warning("Interrumpido por el usuario. CSV parcial conservado.")
    finally:
        storage.close()
        client.close()

    logger.info(
        "Resumen: %s peliculas en %s | errores=%s | bloqueo=%s",
        storage.count,
        settings.csv_path,
        stats.errors,
        stats.blocked,
    )
    if stats.blocked:
        return 2
    if interrupted:
        return 130
    if storage.count < settings.max_movies:
        logger.error("Objetivo no alcanzado; CSV parcial conservado")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
