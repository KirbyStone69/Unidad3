from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from crawler_peliculas.config import CSV_COLUMNS
from crawler_peliculas.storage import Storage

BASE_RECORD = {
    "titulo": "Película de prueba",
    "resumen": "Sinopsis, con coma.",
    "reseña": "Una reseña con \"comillas\".",
    "genero": "Drama|Crimen",
    "url": "https://www.sensacine.com/peliculas/pelicula-1/",
    "anio": "2024",
    "director": "Alguien",
    "duracion_min": "100",
    "nota": "4.0",
    "votos": "10",
    "actores": "A|B",
    "imagen": "https://img.test/x.jpg",
    "reseña_medio": "Medio",
    "reseña_autor": "Autor",
}


class TestStorage(unittest.TestCase):
    def test_add_dedupe_and_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "peliculas.csv"
            storage = Storage(path, fresh=True)
            self.assertTrue(storage.add(BASE_RECORD))
            self.assertFalse(storage.add(BASE_RECORD))
            self.assertEqual(storage.count, 1)
            storage.close()

            resumed = Storage(path)
            self.assertEqual(resumed.count, 1)
            self.assertTrue(resumed.has_url(BASE_RECORD["url"]))
            self.assertFalse(
                resumed.add({**BASE_RECORD, "url": BASE_RECORD["url"], "titulo": "Otro"})
            )
            resumed.close()

            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(tuple(rows[0].keys()), CSV_COLUMNS)
            self.assertEqual(rows[0]["reseña"], BASE_RECORD["reseña"])
            self.assertEqual(rows[0]["genero"], "Drama|Crimen")


if __name__ == "__main__":
    unittest.main()
