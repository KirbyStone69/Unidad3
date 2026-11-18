from __future__ import annotations

import unittest
from pathlib import Path

from crawler_peliculas.scraper import (
    canonical_movie_url,
    is_movie_url,
    movie_id,
    parse_listing,
    parse_movie,
    parse_reviews,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestMovieParser(unittest.TestCase):
    def setUp(self) -> None:
        self.url = "https://www.sensacine.com/peliculas/pelicula-317554/"
        self.record = parse_movie(fixture("pelicula.html"), self.url)

    def test_required_fields(self) -> None:
        self.assertEqual(self.record["titulo"], "Parthenope")
        self.assertIn("Drama", self.record["genero"])
        self.assertIn("Romántico", self.record["genero"])
        self.assertGreater(len(self.record["resumen"]), 80)
        self.assertEqual(self.record["url"], self.url)

    def test_extra_fields(self) -> None:
        self.assertEqual(self.record["anio"], "2025")
        self.assertEqual(self.record["director"], "Paolo Sorrentino")
        self.assertEqual(self.record["duracion_min"], "137")
        self.assertEqual(self.record["nota"], "3.1")
        self.assertEqual(self.record["votos"], "21")
        self.assertIn("Gary Oldman", self.record["actores"])

    def test_review_and_similar_links(self) -> None:
        self.assertTrue(self.record["_review_url"].endswith("/criticas-prensa/"))
        # Las recomendaciones se consultan en la página /similares/.
        # La cabecera de la ficha no constituye una recomendación.
        self.assertEqual(self.record["_similar"], [])
        self.assertTrue(self.record["_similar_url"].endswith("/similares/"))
        self.assertNotIn(self.url, self.record["_similar"])


class TestReviewParser(unittest.TestCase):
    def test_first_press_review(self) -> None:
        reviews = parse_reviews(fixture("criticas.html"))
        self.assertGreaterEqual(len(reviews), 1)
        first = reviews[0]
        self.assertGreater(len(first["texto"]), 40)
        self.assertEqual(first["medio"], "El País")
        self.assertIn("Carlos Boyero", first["autor"])


class TestListingParser(unittest.TestCase):
    def test_genre_page(self) -> None:
        url = "https://www.sensacine.com/peliculas/todas-peliculas/genero-13001/"
        data = parse_listing(fixture("genero.html"), url)
        self.assertGreaterEqual(len(data["movies"]), 15)
        self.assertTrue(all(is_movie_url(movie) for movie in data["movies"]))
        self.assertEqual(data["current_page"], 1)
        self.assertTrue(data["next_url"].endswith("?page=2"))
        # Los enlaces de paginacion no deben tratarse como generos nuevos.
        self.assertTrue(all("?page=" not in genre for genre in data["genres"]))
        self.assertTrue(all("/peliculas/todas-peliculas/genero-" in genre for genre in data["genres"]))

    def test_second_page_uses_next_button(self) -> None:
        url = "https://www.sensacine.com/peliculas/todas-peliculas/genero-13001/?page=2"
        data = parse_listing(fixture("genero_pagina2.html"), url)
        self.assertEqual(data["current_page"], 2)
        self.assertGreaterEqual(len(data["movies"]), 15)
        self.assertTrue(data["next_url"].endswith("?page=3"))
        self.assertTrue(all("?page=" not in genre for genre in data["genres"]))


class TestUrls(unittest.TestCase):
    def test_canonical(self) -> None:
        self.assertEqual(
            canonical_movie_url("/peliculas/pelicula-123/?foo=bar", "https://www.sensacine.com/a/"),
            "https://www.sensacine.com/peliculas/pelicula-123/",
        )
        self.assertIsNone(canonical_movie_url("/peliculas/genero-1/"))

    def test_movie_id(self) -> None:
        self.assertEqual(movie_id("https://www.sensacine.com/peliculas/pelicula-9/"), "9")


if __name__ == "__main__":
    unittest.main()
