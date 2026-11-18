"""Parseo de HTML de SensaCine.

Se apoya en el JSON-LD schema.org/Movie que publica el sitio, y usa
selectores CSS solo como respaldo o para las resenas de prensa.
"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .config import BASE_URL

_MOVIE_RE = re.compile(r"/peliculas/pelicula-(\d+)(?:/|$)")
_YEAR_RE = re.compile(r"Pel[ií]cula\s+(\d{4})", re.IGNORECASE)
_DURATION_RE = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def movie_id(url: str) -> str | None:
    match = _MOVIE_RE.search(url)
    return match.group(1) if match else None


def canonical_movie_url(href: str, page_url: str = BASE_URL) -> str | None:
    absolute = urljoin(page_url, href)
    if urlparse(absolute).netloc != urlparse(BASE_URL).netloc or urlparse(absolute).scheme not in ("http", "https"):
        return None
    ident = movie_id(urlparse(absolute).path)
    if ident is None:
        return None
    return f"{BASE_URL}/peliculas/pelicula-{ident}/"


def is_movie_url(url: str) -> bool:
    return canonical_movie_url(url) is not None


def review_url_for(url: str, soup: BeautifulSoup | None = None) -> str:
    if soup is not None:
        for anchor in soup.select('a[href*="/criticas-prensa/"]'):
            href = anchor.get("href")
            if href and canonical_movie_url(href, url) == canonical_movie_url(url):
                return urljoin(url, href)
    ident = movie_id(url)
    if ident is None:
        return ""
    return f"{BASE_URL}/peliculas/pelicula-{ident}/criticas-prensa/"


def _iter_jsonld(soup: BeautifulSoup):
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            yield from data
        else:
            yield data


def _find_movie_jsonld(soup: BeautifulSoup) -> dict[str, Any] | None:
    for data in _iter_jsonld(soup):
        if not isinstance(data, dict):
            continue
        kind = data.get("@type")
        if kind == "Movie" or (isinstance(kind, list) and "Movie" in kind):
            return data
    return None


def _names(value: Any) -> list[str]:
    if isinstance(value, dict):
        name = value.get("name")
        return [clean_text(name)] if name else []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, dict):
                inner = item.get("actor") if "actor" in item else item
                if isinstance(inner, dict):
                    name = inner.get("name")
                else:
                    name = item.get("name")
            else:
                name = item
            name = clean_text(name)
            if name:
                result.append(name)
        return result
    if isinstance(value, str):
        return [clean_text(value)]
    return []


def _genres(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, list):
        candidates = [clean_text(item) for item in value]
    else:
        candidates = []
    return [genre for genre in candidates if genre]


def _duration_minutes(value: Any) -> str:
    match = _DURATION_RE.search(clean_text(value))
    if not match:
        return ""
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    total = hours * 60 + minutes
    return str(total) if total else ""


def parse_similar(html_text: str, page_url: str) -> list[str]:
    """Solo tarjetas de la sección de similares; excluye cabecera y anuncios."""
    soup = BeautifulSoup(html_text, "lxml")
    current = canonical_movie_url(page_url)
    found = {}
    for anchor in soup.select(".entity-card .meta-title-link[href]"):
        candidate = canonical_movie_url(anchor.get("href", ""), page_url)
        if candidate and candidate != current:
            found.setdefault(candidate, None)
    return list(found)


def parse_movie(html_text: str, url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text, "lxml")
    data = _find_movie_jsonld(soup) or {}

    title = clean_text(data.get("name"))
    if not title and soup.title:
        title = clean_text(soup.title.get_text()).split(" - ")[0]

    synopsis = clean_text(data.get("description"))
    if not synopsis:
        meta = soup.find("meta", attrs={"name": "description"})
        synopsis = clean_text(meta.get("content") if meta else "")

    genres = _genres(data.get("genre"))
    directors = _names(data.get("director"))
    actors = _names(data.get("actor"))

    rating = data.get("aggregateRating") or {}
    if not isinstance(rating, dict):
        rating = {}

    page_title = clean_text(soup.title.get_text()) if soup.title else ""
    year_match = _YEAR_RE.search(page_title)
    year = year_match.group(1) if year_match else ""
    if not year:
        published = clean_text(data.get("datePublished"))
        if published[:4].isdigit():
            year = published[:4]

    image = data.get("image")
    if isinstance(image, dict):
        image = image.get("url", "")
    image = clean_text(image)

    return {
        "titulo": title,
        "resumen": synopsis,
        "reseña": "",
        "genero": "|".join(genres),
        "url": canonical_movie_url(url, url) or url,
        "anio": year,
        "director": "|".join(directors),
        "duracion_min": _duration_minutes(data.get("duration")),
        "nota": clean_text(rating.get("ratingValue")),
        "votos": clean_text(rating.get("ratingCount")),
        "actores": "|".join(actors),
        "imagen": image,
        "reseña_medio": "",
        "reseña_autor": "",
        "_review_url": review_url_for(url, soup),
        "_similar": [],
        "_similar_url": (canonical_movie_url(url) or url) + "similares/",
    }


def parse_reviews(html_text: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html_text, "lxml")
    reviews: list[dict[str, str]] = []

    for item in soup.select(".reviews-press-comment .item"):
        text_node = item.select_one("p.text") or item.select_one(".text")
        text = clean_text(text_node.get_text(" ", strip=True) if text_node else "")
        if not text:
            continue
        title_node = item.select_one(".title")
        author_node = item.select_one(".author")
        reviews.append(
            {
                "texto": text,
                "medio": clean_text(title_node.get_text(" ", strip=True)) if title_node else "",
                "autor": clean_text(author_node.get_text(" ", strip=True)) if author_node else "",
            }
        )

    if not reviews:
        wrapper = soup.select_one(".reviews-press-comment")
        if wrapper is not None:
            text_node = wrapper.select_one("p.text") or wrapper.select_one(".text")
            text = clean_text(text_node.get_text(" ", strip=True) if text_node else "")
            if text:
                reviews.append({"texto": text, "medio": "", "autor": ""})

    # Quitar duplicados conservando el orden.
    unique = {}
    for review in reviews:
        unique.setdefault(review["texto"], review)
    return list(unique.values())


def parse_listing(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text, "lxml")

    movies: dict[str, None] = {}
    genres: dict[str, None] = {}
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "")
        candidate = canonical_movie_url(href, page_url)
        if candidate:
            movies.setdefault(candidate, None)
            continue
        absolute = urljoin(page_url, href)
        parsed_genre = urlparse(absolute)
        # Solo los listados principales de genero, sin query ni fragmento.
        # Si no, cada enlace de paginacion (?page=20, ?page=30...) se
        # encolaria como si fuera otro genero y multiplicaria el rastreo.
        if parsed_genre.netloc == urlparse(BASE_URL).netloc and "/peliculas/todas-peliculas/genero-" in parsed_genre.path:
            clean = f"{parsed_genre.scheme}://{parsed_genre.netloc}{parsed_genre.path}"
            genres.setdefault(clean, None)

    parsed = urlparse(page_url)
    query = parse_qs(parsed.query)
    try:
        current_page = int(query.get("page", ["1"])[0])
    except ValueError:
        current_page = 1

    # SensaCine pagina con enlaces <a href="?page=N"> en la primera pagina,
    # pero en las siguientes usa <span class="...button-right">Siguiente</span>
    # con la URL codificada en la clase. Detectar el boton "Siguiente" es
    # mucho mas estable que intentar decodificar esa clase.
    has_next = False
    for node in soup.select(".pagination .button-right"):
        if "siguiente" in node.get_text(" ", strip=True).lower():
            has_next = True
            break

    page_numbers: list[int] = []
    for anchor in soup.select('a[href*="page="]'):
        href = anchor.get("href", "")
        numbers = parse_qs(urlparse(urljoin(page_url, href)).query).get("page", [])
        for number in numbers:
            if number.isdigit():
                page_numbers.append(int(number))

    next_url = ""
    if has_next or (page_numbers and current_page < max(page_numbers)):
        next_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?page={current_page + 1}"

    return {
        "movies": list(movies),
        "genres": list(genres),
        "next_url": next_url,
        "current_page": current_page,
    }
