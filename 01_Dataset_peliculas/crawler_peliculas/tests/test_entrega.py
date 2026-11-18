import csv
import tempfile
import unittest
from pathlib import Path
from crawler_peliculas import preparar_entrega

class DeliveryTests(unittest.TestCase):
    def test_export_excludes_incomplete_and_duplicate_rows(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'original.csv';out=Path(d)/'entrega.csv'
            columns=['titulo','resumen','reseña','genero','url']
            complete=dict(zip(columns,['Título','Texto, con coma','Crítica "buena"','Drama','https://www.sensacine.com/peliculas/pelicula-1/']))
            with src.open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows([complete,complete,{**complete,'url':'https://www.sensacine.com/peliculas/pelicula-2/','reseña':''}])
            original=src.read_bytes()
            stats=preparar_entrega.export_complete(src,out,minimum=1)
            self.assertEqual(stats['entregadas'],1)
            self.assertEqual(stats['incompletas'],1)
            self.assertEqual(stats['duplicadas'],1)
            self.assertEqual(src.read_bytes(),original)
            with out.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            self.assertEqual(rows[0],complete)
            with self.assertRaises(ValueError):preparar_entrega.export_complete(src,src,minimum=1)
            with self.assertRaises(ValueError):preparar_entrega.export_complete(src,out,minimum=500)
