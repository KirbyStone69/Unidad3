"""Crawler BFS: descubre listados, peliculas y similares hasta el limite."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass

from .config import BASE_URL, GENRE_SEEDS, Settings
from .http_client import BlockedError, HttpError, HttpClient
from .scraper import (
    is_movie_url,
    parse_listing,
    parse_movie,
    parse_reviews,
    parse_similar,
)
from .storage import Storage


@dataclass(slots=True)
class CrawlStats:
    movies_saved: int = 0
    listing_pages: int = 0
    errors: int = 0
    blocked: bool = False


class Crawler:
    def __init__(
        self,
        client: HttpClient,
        storage: Storage,
        settings: Settings,
        logger: logging.Logger | None = None,
    ) -> None:
        self.client = client
        self.storage = storage
        self.settings = settings
        self.log = logger or logging.getLogger("crawler")
        self.queue: deque[str] = deque()
        self.queued: set[str] = set()
        self.stats = CrawlStats()
        self._last_reported = storage.count
        if storage.count < settings.max_movies:
            self._seed()

    def _seed(self) -> None:
        for _label, path in GENRE_SEEDS:
            self._enqueue(f"{BASE_URL}{path}")

    def _enqueue(self, url: str) -> None:
        if not url or url in self.queued:
            return
        if is_movie_url(url) and self.storage.has_url(url):
            return
        self.queued.add(url)
        self.queue.append(url)

    def run(self) -> CrawlStats:
        max_movies = self.settings.max_movies
        self.log.info(
            "Inicio: objetivo=%s peliculas, delay=%.2fs, en cola=%s",
            max_movies,
            self.settings.delay,
            len(self.queue),
        )

        while self.queue and self.storage.count < max_movies:
            url = self.queue.popleft()
            try:
                if is_movie_url(url):
                    self._process_movie(url)
                else:
                    self._process_listing(url)
            except BlockedError as exc:
                self.stats.blocked = True
                self.log.error("Bloqueo detectado, se detiene el rastreo: %s", exc)
                break
            except HttpError as exc:
                self.stats.errors += 1
                self.log.warning("No se pudo procesar %s: %s", url, exc)
            except Exception as exc:  # noqa: BLE001 - un fallo no debe perder el CSV
                self.stats.errors += 1
                self.log.exception("Error inesperado en %s: %s", url, exc)

            if self.storage.count >= max_movies:
                break
            if self.storage.count - self._last_reported >= 10:
                self._last_reported = self.storage.count
                self.log.info(
                    "Progreso: %s/%s peliculas | listados=%s | errores=%s | cola=%s",
                    self.storage.count,
                    max_movies,
                    self.stats.listing_pages,
                    self.stats.errors,
                    len(self.queue),
                )

        self.stats.movies_saved = self.storage.count
        self.log.info(
            "Fin: %s peliculas en CSV | listados=%s | errores=%s | bloqueo=%s",
            self.stats.movies_saved,
            self.stats.listing_pages,
            self.stats.errors,
            self.stats.blocked,
        )
        return self.stats

    # ------------------------------------------------------------- listados
    def _process_listing(self, url: str) -> None:
        if self.stats.listing_pages >= self.settings.max_listing_pages:
            return

        html = self.client.get_html(url)
        data = parse_listing(html, url)
        self.stats.listing_pages += 1

        self.storage.save_links(url, data["movies"], "genero_pelicula")
        self.storage.save_links(url, data["genres"], "genero")
        for movie_url in data["movies"]:
            self._enqueue(movie_url)
        for genre_url in data["genres"]:
            self._enqueue(genre_url)
        if data["next_url"]:
            self._enqueue(data["next_url"])

        self.log.info(
            "Listado %s: %s peliculas, %s generos, siguiente=%s",
            url,
            len(data["movies"]),
            len(data["genres"]),
            data["next_url"] or "no",
        )

    # ------------------------------------------------------------ peliculas
    def _process_movie(self, url: str) -> None:
        html = self.client.get_html(url)
        record = parse_movie(html, url)
        review_url = record.pop("_review_url", "")
        similar = record.pop("_similar", [])
        similar_url = record.pop("_similar_url", "")

        if not record["reseña"] and review_url:
            record["reseña"], record["reseña_medio"], record["reseña_autor"] = (
                self._fetch_first_review(review_url)
            )

        added = self.storage.add(record)
        if added:
            self.log.info(
                "[%s] %s (%s) | genero=%s | resena=%s",
                self.storage.count,
                record["titulo"] or "?",
                record["anio"] or "?",
                record["genero"] or "?",
                "si" if record["reseña"] else "no",
            )

        if self.settings.similar_limit and similar_url:
            try:
                similar = parse_similar(self.client.get_html(similar_url), similar_url)
            except BlockedError:
                raise
            except HttpError as exc:
                self.log.debug("Sin similares en %s: %s", similar_url, exc)

        self.storage.save_links(similar_url, similar[: self.settings.similar_limit], "similar")
        for candidate in similar[: self.settings.similar_limit]:
            self._enqueue(candidate)

    def _fetch_first_review(self, review_url: str) -> tuple[str, str, str]:
        try:
            html = self.client.get_html(review_url)
        except BlockedError:
            raise
        except HttpError as exc:
            self.log.debug("Sin resena para %s: %s", review_url, exc)
            return "", "", ""
        reviews = parse_reviews(html)
        if not reviews:
            return "", "", ""
        first = reviews[0]
        return first["texto"], first["medio"], first["autor"]
