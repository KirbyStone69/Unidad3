"""Guardado incremental en CSV, con reanudacion y deduplicacion por URL."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

from .config import CSV_COLUMNS
from .scraper import movie_id


class Storage:
    def __init__(
        self,
        path: Path,
        fresh: bool = False,
        logger: logging.Logger | None = None,
    ) -> None:
        self.path = path
        self.log = logger or logging.getLogger("crawler")
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if fresh and self.path.exists():
            self.path.unlink()

        self._urls: set[str] = set()
        self._ids: set[str] = set()
        self._count = 0

        exists = self.path.exists() and self.path.stat().st_size > 0
        if exists:
            self._load_existing()

        self._handle = self.path.open("a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(
            self._handle,
            fieldnames=CSV_COLUMNS,
            quoting=csv.QUOTE_MINIMAL,
            extrasaction="ignore",
        )
        if not exists:
            self._writer.writeheader()
            self._handle.flush()

    def _load_existing(self) -> None:
        with self.path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                url = (row.get("url") or "").strip()
                if not url:
                    continue
                self._urls.add(url)
                ident = movie_id(url)
                if ident:
                    self._ids.add(ident)
                self._count += 1
        self.log.info("CSV existente: %s peliculas ya guardadas", self._count)

    @property
    def count(self) -> int:
        return self._count

    def has_url(self, url: str) -> bool:
        if url in self._urls:
            return True
        ident = movie_id(url)
        return bool(ident and ident in self._ids)

    def add(self, record: dict[str, Any]) -> bool:
        url = str(record.get("url", "")).strip()
        if not url or self.has_url(url):
            return False

        row = {column: record.get(column, "") for column in CSV_COLUMNS}
        row["url"] = url
        self._writer.writerow(row)
        self._handle.flush()

        self._urls.add(url)
        ident = movie_id(url)
        if ident:
            self._ids.add(ident)
        self._count += 1
        return True

    def save_links(self, source: str, targets: list[str], kind: str) -> None:
        """Evidencia de navegación separada del CSV de películas."""
        path = self.path.with_suffix(".enlaces.csv")
        columns = ("origen", "destino", "tipo")
        existing = set()
        if path.exists():
            with path.open(encoding="utf-8", newline="") as handle:
                existing = {tuple(row.get(c, "") for c in columns) for row in csv.DictReader(handle)}
        new = [(source, target, kind) for target in dict.fromkeys(targets)
               if (source, target, kind) not in existing]
        if not new:
            return
        needs_header = not path.exists() or not path.stat().st_size
        with path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            if needs_header:
                writer.writerow(columns)
            writer.writerows(new)

    def close(self) -> None:
        try:
            self._handle.flush()
        finally:
            self._handle.close()

    def __enter__(self) -> "Storage":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
