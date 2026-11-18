"""Configuracion central del crawler.

Todo lo que puede cambiar si el sitio se rediseña vive aqui: URL base,
semillas de generos, selectores y limites de cortesia.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

BASE_URL = "https://www.sensacine.com"

# Identificarse siempre. Un crawler anonimo y agresivo es lo primero que bloquean.
USER_AGENT = (
    "TareaAcademicaCrawler/1.1 (proyecto escolar de recoleccion de datos)"
)

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
RAW_HTML_DIR = DATA_DIR / "raw_html"
DEFAULT_CSV = DATA_DIR / "peliculas.csv"
DEFAULT_LOG = DATA_DIR / "crawler.log"

# Paginas de genero semilla. Cada una lista ~19 peliculas por pagina y
# acepta ?page=N. Se usan varias para que el dataset no quede sesgado.
GENRE_SEEDS: tuple[tuple[str, str], ...] = (
    ("Aventura", "/peliculas/todas-peliculas/genero-13001/"),
    ("Comedia dramatica", "/peliculas/todas-peliculas/genero-13002/"),
    ("Comedia", "/peliculas/todas-peliculas/genero-13005/"),
    ("Drama", "/peliculas/todas-peliculas/genero-13008/"),
    ("Terror", "/peliculas/todas-peliculas/genero-13009/"),
    ("Fantasia", "/peliculas/todas-peliculas/genero-13012/"),
    ("Historico", "/peliculas/todas-peliculas/genero-13015/"),
    ("Crimen", "/peliculas/todas-peliculas/genero-13018/"),
    ("Ciencia ficcion", "/peliculas/todas-peliculas/genero-13021/"),
    ("Suspense", "/peliculas/todas-peliculas/genero-13023/"),
    ("Romantico", "/peliculas/todas-peliculas/genero-13024/"),
    ("Accion", "/peliculas/todas-peliculas/genero-13025/"),
    ("Animacion", "/peliculas/todas-peliculas/genero-13026/"),
    ("Biopic", "/peliculas/todas-peliculas/genero-13027/"),
    ("Familia", "/peliculas/todas-peliculas/genero-13036/"),
)

# Columnas del CSV. Las cinco primeras son las que pidio el encargo, en ese
# orden. Las siguientes son utiles para analisis y entrenamiento de modelos.
CSV_COLUMNS: tuple[str, ...] = (
    "titulo",
    "resumen",
    "reseña",
    "genero",
    "url",
    "anio",
    "director",
    "duracion_min",
    "nota",
    "votos",
    "actores",
    "imagen",
    "reseña_medio",
    "reseña_autor",
)


@dataclass(slots=True)
class Settings:
    """Parametros ajustables desde la linea de comandos."""

    max_movies: int = 1000
    delay: float = 1.0
    max_listing_pages: int = 200
    similar_limit: int = 20
    max_reviews_per_movie: int = 3
    use_cache: bool = True
    fresh: bool = False
    csv_path: Path = DEFAULT_CSV
    log_path: Path = DEFAULT_LOG
    timeout: float = 25.0
    retries: int = 4
