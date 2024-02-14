# Paseador de Perros

## Descripción del Proyecto
Este proyecto está diseñado para planificar rutas de paseo para perros, optimizando el trayecto según las características específicas de la raza del perro y utilizando datos geoespaciales. El sistema calcula la ruta más eficiente teniendo en cuenta la ubicación actual, tamaño, edad, y raza del perro, así como la identificación de zonas verdes o áreas de interés cercanas.

## Estructura del Repositorio
El repositorio consta de varios scripts Python, cada uno con un propósito específico dentro del proyecto:

### `caracter_perro.py`
Define un diccionario con características de diferentes razas de perros, como su comportamiento y tamaño, para personalizar las rutas de paseo.

### `carga_datos_yDevolver_json.py`
Maneja la carga de datos geoespaciales desde archivos GeoJSON y trabaja con zonas verdes. Esencial para el manejo de información geográfica del proyecto.

### `main.py`
El script principal que coordina las operaciones del programa, incluyendo el manejo de datos del perro y la generación de rutas.

### `nodos_rutas_y_pesos.py`
Procesa datos geográficos para crear grafos, convertir líneas en nodos y calcular distancias y pesos para las rutas.

### `TSP.py`
Implementa la solución al problema del viajante de comercio (TSP) para calcular la ruta más eficiente a través de una serie de puntos.

### `velocidad_y_distancia.py`
Calcula la velocidad de paseo estimada basada en la raza del perro, ajustando las rutas a las necesidades específicas de diferentes razas.

### `llamada_api_con_radios.py`
Interactúa con APIs externas para identificar zonas verdes o áreas de interés para el paseo de perros, utilizando datos geoespaciales.

## Cómo Utilizar

En desarrollo...

## Dependencias

- geopandas: Extiende Pandas para el manejo eficiente de datos geoespaciales, facilitando análisis y operaciones espaciales.
- shapely: Biblioteca para la manipulación y análisis de figuras geométricas, ofreciendo herramientas para operaciones espaciales.
- osmnx: Permite descargar y analizar redes de calles de OpenStreetMap, ideal para trabajar con datos de mapas y redes urbanas.
- folium: Crea mapas interactivos con Python, integrando capacidades de Leaflet.js para visualizaciones geoespaciales enriquecidas.
- overpy: Interfaz para consultar datos de OpenStreetMap a través de la API de Overpass, facilitando el acceso a datos espaciales específicos.
- ortools: Proporciona soluciones a problemas de optimización combinatoria como el TSP, optimizando rutas y asignaciones.


Este README proporciona una visión general del proyecto Paseador de Perros, diseñado para ayudar en la planificación y optimización de rutas de paseo para perros, teniendo en cuenta una variedad de factores importantes.
