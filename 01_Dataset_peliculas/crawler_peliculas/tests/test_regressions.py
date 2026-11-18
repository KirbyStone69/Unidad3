import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import requests

from crawler_peliculas.config import BASE_URL, Settings
from crawler_peliculas.crawler import Crawler
from crawler_peliculas.http_client import HttpClient, HttpError, BlockedError
from crawler_peliculas.scraper import canonical_movie_url, parse_movie, parse_reviews, parse_listing
from crawler_peliculas.storage import Storage

URL = BASE_URL + '/peliculas/pelicula-261667/'
FIXTURES = Path(__file__).parent / 'fixtures'

class RegressionTests(unittest.TestCase):
    def test_external_movie_link_is_rejected(self):
        self.assertIsNone(canonical_movie_url('https://otro.test/peliculas/pelicula-1/'))

    def test_review_duplicates_removed(self):
        item='<div class="item"><p class="text">Una crítica.</p></div>'
        self.assertEqual(len(parse_reviews('<div class="reviews-press-comment">'+item*2+'</div>')),1)

    def test_unrelated_header_is_not_similar(self):
        record=parse_movie('<header><a href="/peliculas/pelicula-1/">Estreno</a></header>',URL)
        self.assertEqual(record['_similar'], [])
        self.assertEqual(record['_similar_url'], URL+'similares/')

    def test_real_similar_cards_only(self):
        from crawler_peliculas import scraper
        self.assertTrue(hasattr(scraper, 'parse_similar'))
        links=scraper.parse_similar((FIXTURES/'similares.html').read_text(),URL+'similares/')
        self.assertEqual(len(links),20)
        self.assertEqual(links[0],BASE_URL+'/peliculas/pelicula-217882/')
        self.assertNotIn(URL,links)

    def test_external_genre_rejected(self):
        data=parse_listing('<a href="https://otro.test/peliculas/todas-peliculas/genero-1/">A</a>',BASE_URL)
        self.assertEqual(data['genres'],[])

    def test_plain_403_stops(self):
        response=requests.Response(); response.status_code=403; response._content=b'Forbidden'
        client=HttpClient(delay=0,use_cache=False)
        with patch.object(client,'allowed',return_value=True),patch.object(client.session,'get',return_value=response):
            with self.assertRaises(BlockedError):client.get_html(URL)
        client.close()

    def test_429_stops_without_hammering(self):
        response=requests.Response(); response.status_code=429; response._content=b'Slow down';response.headers['Retry-After']='120'
        client=HttpClient(delay=0,use_cache=False)
        with patch.object(client,'allowed',return_value=True),patch.object(client.session,'get',return_value=response),patch('time.sleep'):
            with self.assertRaises(BlockedError):client.get_html(URL)
        client.close()

    def test_robots_unavailable_fails_closed(self):
        client=HttpClient(use_cache=False)
        with patch.object(client,'_load_robots',return_value=None):
            with self.assertRaises(BlockedError):client.allowed(URL)
        client.close()

    def test_review_block_propagates(self):
        client=HttpClient(use_cache=False)
        with tempfile.TemporaryDirectory() as d, Storage(Path(d)/'a.csv') as storage:
            with patch.object(client,'allowed',return_value=True):crawler=Crawler(client,storage,Settings())
            with patch.object(client,'get_html',side_effect=BlockedError('403')):
                with self.assertRaises(BlockedError):crawler._fetch_first_review(URL+'criticas-prensa/')
        client.close()

    def test_complete_resume_never_uses_network(self):
        client=HttpClient(use_cache=False)
        with tempfile.TemporaryDirectory() as d, Storage(Path(d)/'a.csv') as storage:
            storage.add({'url':URL,'titulo':'Searching'})
            with patch.object(client.session,'get',side_effect=AssertionError('No debe usar red')):
                crawler=Crawler(client,storage,Settings(max_movies=1))
                self.assertEqual(crawler.run().movies_saved,1)
        client.close()

class EndToEndTests(unittest.TestCase):
    def test_crawl_saves_movie_and_real_link_evidence(self):
        import csv
        client=HttpClient(use_cache=False)
        genre=BASE_URL+'/peliculas/todas-peliculas/genero-13001/'
        movie=BASE_URL+'/peliculas/pelicula-317554/'
        pages={genre:f'<a href="{movie}">Parthenope</a>', movie:(FIXTURES/'pelicula.html').read_text(), movie+'criticas-prensa/':(FIXTURES/'criticas.html').read_text(), movie+'similares/':(FIXTURES/'similares.html').read_text()}
        with tempfile.TemporaryDirectory() as d,Storage(Path(d)/'movies.csv') as storage:
            with patch('crawler_peliculas.crawler.GENRE_SEEDS',[('Aventura','/peliculas/todas-peliculas/genero-13001/')]),patch.object(client,'get_html',side_effect=lambda u:pages[u]):
                crawler=Crawler(client,storage,Settings(max_movies=1));stats=crawler.run()
            self.assertEqual(stats.errors,0)
            self.assertEqual(stats.movies_saved,1)
            evidence=Path(d)/'movies.enlaces.csv'
            self.assertTrue(evidence.exists())
            with evidence.open() as f:edges=list(csv.DictReader(f))
            self.assertIn({'origen':genre,'destino':movie,'tipo':'genero_pelicula'},edges)
            self.assertIn({'origen':movie+'similares/','destino':BASE_URL+'/peliculas/pelicula-217882/','tipo':'similar'},edges)
        client.close()

    def test_cli_rejects_nonfinite_delay(self):
        from crawler_peliculas.main import main
        self.assertEqual(main(['--delay','nan']),1)

    def test_cli_unmet_target_is_failure(self):
        from crawler_peliculas.main import main
        with tempfile.TemporaryDirectory() as d,patch('crawler_peliculas.crawler.GENRE_SEEDS',[]):
            self.assertEqual(main(['--max','1','--out',d+'/a.csv','--log',d+'/a.log']),3)
