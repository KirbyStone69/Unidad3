# Crawler de películas — entrega revisada

## Qué entregar

**`data/peliculas_entrega.csv`: 718 películas únicas con título, resumen, reseña, género y URL.**

Se obtuvo del CSV de 1,000 películas que ya estaba en el proyecto. Se excluyeron 282 filas sin reseña; no se inventó texto para completarlas. El original `data/peliculas.csv` se conserva. La entrega usa UTF-8 con BOM para conservar los acentos al abrirla en Excel y comas como separador.

La fuente es [SensaCine](https://www.sensacine.com/). `reseña` es el extracto de una crítica de prensa mostrado por el sitio; `resumen` es la descripción de la película. No son el mismo campo. Los géneros múltiples se separan con `|`.

## Pasos del programa

1. Comienza por las URL de 15 géneros.
2. Descarga el HTML y extrae enlaces de películas y páginas siguientes.
3. Visita cada película y lee sus datos estructurados JSON-LD dentro del HTML.
4. Visita `criticas-prensa/` y toma la primera crítica publicada, con medio y autor cuando existen.
5. Visita `similares/` y extrae solo las tarjetas de películas recomendadas.
6. Añade esas URL a la cola, evitando visitar otra vez la misma película.
7. Guarda filas progresivamente en CSV y enlaces de navegación en un archivo `*.enlaces.csv`.
8. Filtra registros incompletos para producir la entrega final.

```text
Géneros → listados HTML → fichas de películas → datos
                              ├→ críticas → reseña
                              └→ similares → nuevas fichas
Datos → CSV original → validación → CSV de entrega
```

El código anterior confundía enlaces del encabezado con similares. Se corrigió utilizando la sección real, por ejemplo [similares a Searching](https://www.sensacine.com/peliculas/pelicula-261667/similares/). Algunas películas no tienen esa sección: el sitio devuelve un error o redirección y no se inventan relaciones.

## Ejecutar

Desde la carpeta principal del proyecto:

```bash
.venv/bin/python -m pip install -r crawler_peliculas/requirements.txt

# La ejecución se reanuda si ya hay CSV; no descarga de nuevo 1,000 películas.
.venv/bin/python -m crawler_peliculas --max 1000 --delay 1.5

# Prueba pequeña en un archivo distinto.
.venv/bin/python -m crawler_peliculas --max 5 --delay 1.5 --out crawler_peliculas/data/mi_prueba.csv

# Preparar nuevamente la entrega, sin usar Internet.
.venv/bin/python -m crawler_peliculas.preparar_entrega

# Unir entregas de compañeros. Conviene indicar archivos concretos.
.venv/bin/python -m crawler_peliculas.unir_csvs entrega1.csv entrega2.csv -o todos.csv

# Pruebas sin Internet.
.venv/bin/python -m unittest discover -s crawler_peliculas/tests -v
```

`--fresh` borra el CSV de salida indicado. No hace falta usarlo para reanudar. `--max` limita películas guardadas, incluyendo las que no tienen crítica; el paso de preparación selecciona las completas. Si no se alcanza el objetivo, el programa devuelve código 3 y conserva el archivo parcial. Un bloqueo devuelve 2; una interrupción, 130.

## Tráfico y bloqueos

Solo se recorren URL de SensaCine. Se consulta `robots.txt` antes de descargar y se respeta su `Crawl-delay` cuando existe. Si no puede comprobarse, se detiene. Se conserva caché HTML y se realizan peticiones secuenciales con pausa; no se descargan imágenes ni videos.

Un 403, 429 o indicio de CAPTCHA detiene el crawler, también al consultar reseñas o similares. No se evaden bloqueos ni se siguen redirecciones automáticamente. No hay garantía de que el sitio nunca bloquee; estas medidas reducen tráfico y permiten detenerse correctamente. `robots.txt` es una indicación de rastreo, no una licencia sobre el contenido.

## Evidencia y límites

- `data/peliculas_entrega.validacion.json`: conteos y huellas SHA-256 de origen y entrega.
- `data/auditoria_muestra.json`: contraste de 12 filas equidistantes con páginas reales; indica discrepancias y disponibilidad de similares.
- `data/prueba_real.csv` y `data/prueba_real.log`: ejecución real de cinco películas.
- `data/prueba_real.enlaces.csv`: enlaces de géneros y similares recuperados durante la auditoría; es una muestra, no el mapa de las 718 películas.
- `data/pruebas.txt`: resultados de las pruebas automáticas.
- `data/raw_html/`: HTML conservado para inspección y repetición sin red.

Se validó la estructura de todas las filas y se contrastó una muestra con la web. No se volvieron a descargar las 1,000 películas originales: OpenCode no dejó su caché. Coincidir con el HTML prueba fidelidad de extracción, no que cada afirmación editorial del sitio sea correcta. Los datos pueden cambiar y el conjunto favorece películas con críticas de prensa.

## Archivos del programa

| Archivo | Función |
|---|---|
| `config.py` | URL, géneros, columnas y parámetros |
| `http_client.py` | Descarga, pausas, caché y bloqueos |
| `scraper.py` | Extrae datos y enlaces del HTML |
| `crawler.py` | Recorre la cola de páginas |
| `storage.py` | Guarda CSV y evidencia de enlaces |
| `preparar_entrega.py` | Selecciona filas completas y valida cantidad |
| `unir_csvs.py` | Une archivos y normaliza columnas |
| `main.py` | Opciones de terminal |

El unificador elimina duplicados identificados por URL o identificador; cuando no existe URL usa título y año. No identifica automáticamente todas las equivalencias entre películas de sitios distintos. Al repetir una película conserva la primera fila: pasar primero el archivo más completo.
