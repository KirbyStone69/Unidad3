from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from crawler_peliculas.unir_csvs import REQUIRED, merge


class TestMergeCsvs(unittest.TestCase):
    def test_merge_normalizes_and_dedupes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "a.csv"
            second = root / "b.csv"
            output = root / "todos.csv"

            first.write_text(
                "title,summary,review,genre,url,year\n"
                "Peli Uno,Resumen uno,Reseña uno,Drama,"
                "https://www.sensacine.com/peliculas/pelicula-1/,2020\n",
                encoding="utf-8",
            )
            second.write_text(
                "titulo,resumen,reseña,genero,url,anio,director\n"
                "Peli Uno,Otro resumen,Otra reseña,Drama,"
                "https://www.sensacine.com/peliculas/pelicula-1/?x=1,2020,Dir A\n"
                "Peli Dos,Resumen dos,,Comedia,"
                "https://www.sensacine.com/peliculas/pelicula-2/,2021,Dir B\n",
                encoding="utf-8",
            )

            stats = merge([first, second], output)
            self.assertEqual(stats["read"], 3)
            self.assertEqual(stats["kept"], 2)
            self.assertEqual(stats["duplicates"], 1)

            with output.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                columns = reader.fieldnames or []

            self.assertEqual(tuple(columns[:5]), REQUIRED)
            self.assertIn("director", columns)
            self.assertEqual(len(rows), 2)
            self.assertEqual({row["url"] for row in rows}, {
                "https://www.sensacine.com/peliculas/pelicula-1/",
                "https://www.sensacine.com/peliculas/pelicula-2/",
            })
            self.assertEqual(rows[0]["reseña"], "Reseña uno")


if __name__ == "__main__":
    unittest.main()
