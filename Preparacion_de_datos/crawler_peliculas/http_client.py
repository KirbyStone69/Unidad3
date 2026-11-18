"""Cliente HTTP cortes, con cache en disco, reintentos y respeto de robots.txt."""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

import requests

from .config import BASE_URL, RAW_HTML_DIR, USER_AGENT


class HttpError(RuntimeError):
    """Error recuperable o definitivo al descargar una pagina."""


class NotFound(HttpError):
    """La pagina devolvio 404."""


class BlockedError(HttpError):
    """El sitio nos bloqueo (CAPTCHA, Cloudflare o 403)."""


_BLOCK_MARKERS = (
    "just a moment",
    "attention required",
    "cf-error",
    "unusual traffic",
    "captcha",
    "access denied",
)


class HttpClient:
    def __init__(
        self,
        delay: float = 1.0,
        timeout: float = 25.0,
        retries: int = 4,
        use_cache: bool = True,
        cache_dir: Path = RAW_HTML_DIR,
        logger: logging.Logger | None = None,
    ) -> None:
        self.delay = max(0.0, delay)
        self.timeout = timeout
        self.retries = retries
        self.use_cache = use_cache
        self.cache_dir = cache_dir
        self.log = logger or logging.getLogger("crawler")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.7",
                "Connection": "keep-alive",
            }
        )
        self._last_request = 0.0
        self._robots: RobotFileParser | None | bool = None
        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ cache
    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.html"

    def _read_cache(self, url: str) -> str | None:
        if not self.use_cache:
            return None
        path = self._cache_path(url)
        if path.exists() and path.stat().st_size > 0:
            try:
                return path.read_text(encoding="utf-8")
            except OSError:
                return None
        return None

    def _write_cache(self, url: str, text: str) -> None:
        if not self.use_cache:
            return
        path = self._cache_path(url)
        tmp = path.with_suffix(".tmp")
        try:
            tmp.write_text(text, encoding="utf-8")
            tmp.replace(path)
        except OSError as exc:  # la cache no debe romper el crawler
            self.log.debug("No se pudo escribir cache %s: %s", url, exc)

    # ----------------------------------------------------------------- robots
    def _load_robots(self) -> RobotFileParser | None:
        parser = RobotFileParser()
        try:
            self._throttle()
            self._last_request = time.monotonic()
            resp = self.session.get(f"{BASE_URL}/robots.txt", timeout=self.timeout, allow_redirects=False)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
                return parser
        except requests.RequestException as exc:
            self.log.warning("No se pudo leer robots.txt: %s", exc)
        return None

    def allowed(self, url: str) -> bool:
        if urlparse(url).netloc != urlparse(BASE_URL).netloc or urlparse(url).scheme != "https":
            return False
        if self._robots is None:
            self._robots = self._load_robots() or False
        if self._robots is False:
            raise BlockedError("No se pudo verificar robots.txt; rastreo detenido")
        crawl_delay = self._robots.crawl_delay(USER_AGENT) or self._robots.crawl_delay("*")
        if crawl_delay:
            self.delay = max(self.delay, crawl_delay)
        return self._robots.can_fetch(USER_AGENT, url)

    # ------------------------------------------------------------------ ritmo
    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)

    @staticmethod
    def _decode(resp: requests.Response) -> str:
        try:
            return resp.content.decode("utf-8")
        except UnicodeDecodeError:
            encoding = resp.apparent_encoding or "latin-1"
            return resp.content.decode(encoding, errors="replace")

    @staticmethod
    def _looks_blocked(text: str) -> bool:
        head = text[:4000].lower()
        return any(marker in head for marker in _BLOCK_MARKERS)

    # ------------------------------------------------------------------- get
    def get_html(self, url: str) -> str:
        cached = self._read_cache(url)
        if cached is not None:
            self.log.debug("Cache: %s", url)
            return cached

        if not self.allowed(url):
            raise HttpError(f"robots.txt no permite rastrear {url}")

        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            self._throttle()
            self._last_request = time.monotonic()
            try:
                resp = self.session.get(url, timeout=self.timeout, allow_redirects=False)
            except requests.RequestException as exc:
                last_error = exc
                wait = min(2 ** attempt, 20)
                self.log.warning(
                    "Error de red (%s/%s) en %s: %s. Reintento en %ss",
                    attempt,
                    self.retries,
                    url,
                    exc,
                    wait,
                )
                time.sleep(wait)
                continue

            status = resp.status_code
            text = self._decode(resp)

            if status == 200:
                if self._looks_blocked(text):
                    raise BlockedError(f"Posible bloqueo/CAPTCHA en {url}")
                self._write_cache(url, text)
                return text

            if status == 404:
                raise NotFound(f"404 en {url}")

            if status in (403, 429):
                raise BlockedError(
                    f"HTTP {status} en {url}; se detiene. Retry-After: "
                    f"{resp.headers.get('Retry-After', 'no indicado')}"
                )

            elif status == 503 and self._looks_blocked(text):
                raise BlockedError(f"Bloqueo HTTP {status} en {url}")

            elif 500 <= status < 600:
                wait = min(2 ** attempt, 30)
                self.log.warning(
                    "HTTP %s en %s. Reintento en %ss", status, url, wait
                )
                time.sleep(wait)

            else:
                raise HttpError(f"HTTP {status} en {url}")

            last_error = HttpError(f"HTTP {status} en {url}")

        raise HttpError(f"No se pudo descargar {url}: {last_error}")

    def close(self) -> None:
        self.session.close()
