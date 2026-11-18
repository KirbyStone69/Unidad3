# Revisión final

- Entrega: **718 películas únicas**, sin vacíos en título, resumen, reseña, género y URL.
- Original: 1,000 filas conservadas sin modificación. Se excluyeron 282 sin reseña.
- Prueba real: cinco películas descargadas, cero errores de procesamiento.
- Auditoría: 12 filas equidistantes; los cuatro campos solicitados coinciden con el HTML.
- Evidencia: 180 relaciones de similares y 285 enlaces desde 15 géneros. Es una muestra de navegación.
- Pruebas automáticas: 24 del crawler y 20 del proyecto Iris aprobadas.
- Unión de CSV: 1,436 filas de entrada, 718 únicas de salida.

## Correcciones

Se sustituyeron enlaces generales por las tarjetas de la sección real de similares. Se rechazaron enlaces a otros dominios, se corrigió la eliminación de críticas repetidas y se detuvo el rastreo ante 403, 429, CAPTCHA o imposibilidad de verificar robots.txt. Los bloqueos en reseñas ya no se ocultan. Reanudar una entrega terminada no genera tráfico. Se validan parámetros de terminal y se informa cuando el objetivo queda incompleto.

## Alcance

El CSV de 718 filas proviene del archivo original, con validación completa de estructura y revisión web de una muestra de 12. No se afirma haber verificado editorialmente las 718 películas ni disponer de similares para todas. Las páginas que redirigen o no tienen similares se registran sin relaciones inventadas.

Consulta README.md para ejecutar, reproducir la entrega y unir CSV. El ZIP contiene código, pruebas y resultados; la caché de las descargas de esta revisión permanece en la carpeta local data/raw_html y se excluye del ZIP para reducir tamaño.
