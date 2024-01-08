import osmnx as ox
from osmnx import settings
import networkx as nx
import folium
import geopandas as gpd
import json
import pandas as pd
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from caracter_perro import caracteristicas_perros
from geopy.distance import distance

# Configuración de OSMnx utilizando el módulo settings
settings.use_cache = True
settings.log_console = True

def cargar_datos_geojson(nombre_archivo_nodos, nombre_archivo_aristas):
    # Cargar datos de nodos y aristas desde archivos GeoJSON
    nodos_gdf = gpd.read_file('nodos_burgos.geojson')
    aristas_gdf = gpd.read_file('aristas_burgos.geojson')
    return nodos_gdf, aristas_gdf

def lineas_a_nodos(calles_gdf):
    nodos = set()
    for linea in calles_gdf.geometry:
        if isinstance(linea, LineString):
            nodos.add(linea.coords[0])
            nodos.add(linea.coords[-1])

    nodos_gdf = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in nodos])
    nodos_gdf['x'] = nodos_gdf.geometry.x
    nodos_gdf['y'] = nodos_gdf.geometry.y

    # Agregar una columna 'osmid' como identificador único
    nodos_gdf['osmid'] = range(len(nodos_gdf))

    return nodos_gdf

def cargar_datos():
    # calles_gdf = gpd.read_file('calles_nodo.geojson')
    zonas_verdes_gdf = gpd.read_file('parques.geojson')

    # Convertir calles_gdf en un GeoDataFrame de nodos
    # nodos_gdf = lineas_a_nodos(calles_gdf)

    return zonas_verdes_gdf
    # return nodos_gdf, zonas_verdes_gdf

def calcular_distancia_a_zonas_verdes(arista, zonas_verdes_gdf):
    punto_arista = arista.geometry.centroid
    puntos_zonas_verdes = zonas_verdes_gdf.geometry.apply(lambda x: nearest_points(punto_arista, x)[1])
    distancia_minima = min([punto_arista.distance(punto) for punto in puntos_zonas_verdes])
    return distancia_minima

def calcular_distancia_y_tipo_zonas_verdes(arista, zonas_verdes_gdf):
    punto_arista = arista.geometry.centroid
    distancia_minima = float('inf')
    es_dog_park = False
    for _, zona_verde in zonas_verdes_gdf.iterrows():
        distancia = punto_arista.distance(zona_verde.geometry)
        if distancia < distancia_minima:
            distancia_minima = distancia
            # Considera un dog park si cumple con ciertas condiciones en 'leisure' o 'tipo_jardin'
            es_dog_park = zona_verde['leisure'] == 'dog_park' or zona_verde['tipo_jardin'] == 'dog_park'
    return distancia_minima, es_dog_park

def aplicar_peso_zonas_verdes(G, zonas_verdes_gdf, distancia_umbral, factor_reduccion, factor_reduccion_dog_park):
    for u, v, data in G.edges(data=True):
        arista = gpd.GeoDataFrame([data], geometry=[LineString([Point(G.nodes[u]['x'], G.nodes[u]['y']), 
                                                                Point(G.nodes[v]['x'], G.nodes[v]['y'])])])
        distancia, es_dog_park = calcular_distancia_y_tipo_zonas_verdes(arista.iloc[0], zonas_verdes_gdf)
        if distancia < distancia_umbral:
            if es_dog_park:
                data['weight'] *= factor_reduccion_dog_park
            else:
                data['weight'] *= factor_reduccion

def obtener_ubicacion_actual():
    # En un caso real, esta función obtendría la ubicación actual del usuario
    return 42.3439, -3.6969  

def estimar_velocidad(raza):
    # Obtener el perfil de la raza del perro
    perfil_raza = caracteristicas_perros.get(raza, {"Comportamiento": "Desconocido", "Tamaño": "Mediano"})

    # Obtener el comportamiento de la raza del perro
    comportamiento = perfil_raza["Comportamiento"].lower()

    # Velocidades ajustadas para los tres comportamientos
    if comportamiento == 'tranquilo':
        return 2  # Velocidad más lenta para perros tranquilos
    elif comportamiento == 'curioso':
        return 3  # Velocidad media
    elif comportamiento == 'energético':
        return 4  # Velocidad más alta para perros energéticos

    return 3  # Velocidad por defecto si no hay suficiente información

def estimar_distancia(duracion, perfil_perro):
    # Obtiene la raza del perro desde el perfil
    raza = perfil_perro.get('raza')
    # Calcula la velocidad basada en la raza del perro
    velocidad = estimar_velocidad(raza)
    # Calcula la distancia basada en la duración del paseo y la velocidad
    return duracion * velocidad

# Nuevas funciones para encontrar rutas circulares
def calcular_distancia_entre_nodos(G, nodo1, nodo2):
    y1, x1 = G.nodes[nodo1]['y'], G.nodes[nodo1]['x']
    y2, x2 = G.nodes[nodo2]['y'], G.nodes[nodo2]['x']
    return distance((y1, x1), (y2, x2)).meters

def buscar_rutas(G, nodo_actual, nodo_inicio, ruta_actual, distancia_actual, distancia_max, rutas, visitados):
    # Comprobación de límites: detiene la búsqueda si se excede la distancia máxima o se revisita un nodo en una ruta menos eficiente
    if distancia_actual > distancia_max or (nodo_actual in visitados and visitados[nodo_actual] <= distancia_actual):
        return

    # Comprobar si hemos vuelto al nodo de inicio y la ruta tiene más de un nodo, en cuyo caso, se añade a la lista de rutas
    if nodo_actual == nodo_inicio and len(ruta_actual) > 1:
        rutas.append(ruta_actual.copy())
        return

    # Marcar el nodo actual como visitado con la distancia actual
    visitados[nodo_actual] = distancia_actual

    # Explorar todos los vecinos del nodo actual
    for vecino in G.neighbors(nodo_actual):
        # Comprobar si el vecino no está en la ruta actual o es el nodo de inicio (para cerrar la ruta)
        if vecino not in ruta_actual or (vecino == nodo_inicio and len(ruta_actual) > 1):
            # Añadir el vecino a la ruta actual y actualizar la distancia
            ruta_actual.append(vecino)
            nueva_distancia = distancia_actual + calcular_distancia_entre_nodos(G, nodo_actual, vecino)

            # Llamada recursiva para continuar buscando desde el vecino
            buscar_rutas(G, vecino, nodo_inicio, ruta_actual, nueva_distancia, distancia_max, rutas, visitados)

            # Quitar el vecino de la ruta actual (backtracking)
            ruta_actual.pop()

def encontrar_rutas_circulares(G, nodo_inicio, distancia_max):
    # Lista para almacenar todas las rutas encontradas
    rutas = []
    # Iniciar la búsqueda de rutas con la función de backtracking
    buscar_rutas(G, nodo_inicio, nodo_inicio, [nodo_inicio], 0, distancia_max, rutas, {})
    # Devolver las rutas encontradas
    return rutas

def puntuar_ruta(ruta, G, zonas_verdes_gdf, perfil_perro):
    # Obtener el tamaño de la raza del perro del diccionario
    raza = perfil_perro.get('raza')
    tamaño_raza = caracteristicas_perros.get(raza, {"Tamaño": "Mediano"})["Tamaño"].lower()
    # Factores de puntuación basados en el tamaño del perro
    factor_tamaño = {'pequeño': 1, 'mediano': 2, 'grande': 3}.get(tamaño_raza, 2)
    # Factor de edad
    factor_edad = 1 if perfil_perro.get('edad', 5) < 8 else 1.5  # Mayor puntaje para perros mayores
    # Calcular la longitud total de la ruta
    longitud_ruta = sum(calcular_distancia_entre_nodos(G, ruta[i], ruta[i+1]) for i in range(len(ruta)-1))
    # Calcular la proximidad a zonas verdes
    proximidad_zonas_verdes = sum(calcular_distancia_a_zonas_verdes(gpd.GeoDataFrame([{'geometry': Point(G.nodes[n]['x'], G.nodes[n]['y'])}]), zonas_verdes_gdf) for n in ruta) / len(ruta)
    # Calcular la puntuación de la ruta
    puntuacion = (longitud_ruta * factor_tamaño + proximidad_zonas_verdes) * factor_edad
    return puntuacion

def seleccionar_ruta(rutas, G, zonas_verdes_gdf, perfil_perro):
    if not rutas:
        return None
    # Evaluar y puntuar cada ruta
    puntuaciones_rutas = [(ruta, puntuar_ruta(ruta, G, zonas_verdes_gdf, perfil_perro)) for ruta in rutas]
    # Ordenar las rutas por puntuación (menor es mejor)
    puntuaciones_rutas.sort(key=lambda x: x[1])
    # Devolver la ruta con la mejor puntuación
    return puntuaciones_rutas[0][0] if puntuaciones_rutas else None

def generar_rutas(G, nodo_inicio, duracion, perfil_perro):
    distancia_estimada = estimar_distancia(duracion, perfil_perro)
    rutas_posibles = encontrar_rutas_circulares(G, nodo_inicio, distancia_estimada)
    mejor_ruta = seleccionar_ruta(rutas_posibles, G, zonas_verdes_gdf, perfil_perro)  
    return mejor_ruta


def visualizar_rutas(G, rutas, latitud_actual, longitud_actual):
    mapa = folium.Map(location=[latitud_actual, longitud_actual], zoom_start=15)
    for ruta in rutas:
        ox.plot_route_folium(G, ruta, route_map=mapa)
    # Guardar el mapa en un archivo HTML
    nombre_archivo_mapa = 'rutas_paseo.html'
    mapa.save(nombre_archivo_mapa)
    return nombre_archivo_mapa

def generar_json_respuesta(rutas, nombre_archivo_mapa):
    # Aquí puedes incluir más detalles sobre las rutas si lo necesitas
    info_rutas = {
        "mapa_html": nombre_archivo_mapa,
        "detalles_rutas": rutas  # Puedes incluir detalles como coordenadas o nodos
    }
    return json.dumps(info_rutas)

def cargar_datos_perro(json_input):
    try:
        # Decodificar el JSON y convertirlo en un diccionario de Python
        datos_perro = json.loads(json_input)
        return datos_perro
    except json.JSONDecodeError as e:
        print(f"Error al decodificar el JSON: {e}")
        return None
    
def crear_grafo_desde_geojson(nodos_gdf, aristas_gdf):
    G = nx.Graph()
    for _, nodo in nodos_gdf.iterrows():
        G.add_node(nodo['osmid'], x=nodo['geometry'].x, y=nodo['geometry'].y)
    for _, arista in aristas_gdf.iterrows():
        # Usar longitud como peso, o un valor predeterminado si no está disponible
        longitud = arista.get('length', 1.0)
        G.add_edge(arista['u'], arista['v'], weight=longitud)
        G.graph['crs'] = 'epsg:4326'  # Establecer el CRS aquí
    return G

def obtener_ubicacion_actual(G, latitud, longitud):
    # Retorna el nodo más cercano a la ubicación dada
    return ox.nearest_nodes(G, X=longitud, Y=latitud)

# Principal
def main(json_input):
    datos_perro = cargar_datos_perro(json_input)
    if not datos_perro:
        print("No se pudieron cargar los datos del perro.")
        return

    latitud_actual, longitud_actual = datos_perro['latitud'], datos_perro['longitud']
    tamaño, edad, raza = datos_perro['tamaño'], datos_perro['edad'], datos_perro['raza']
    duracion_paseo = datos_perro['duracion']

    # Cargar datos geográficos
    nombre_archivo_nodos = 'nodos_burgos.geojson'
    nombre_archivo_aristas = 'aristas_burgos.geojson'
    nodos_gdf, aristas_gdf = cargar_datos_geojson(nombre_archivo_nodos, nombre_archivo_aristas)
    G = crear_grafo_desde_geojson(nodos_gdf, aristas_gdf)

    # Cargar zonas verdes
    zonas_verdçes_gdf = gpd.read_file('parques.geojson')
    factor_reduccion_general = 0.5
    factor_reduccion_dog_park = 0.7  # Mayor reducción para dog parks
    aplicar_peso_zonas_verdes(G, zonas_verdes_gdf, distancia_umbral=10, 
                            factor_reduccion=factor_reduccion_general, 
                            factor_reduccion_dog_park=factor_reduccion_dog_park)

    nodo_mas_cercano = obtener_ubicacion_actual(G, latitud_actual, longitud_actual)

    # Generar y visualizar rutas
    perfil_perro = {'tamaño': tamaño, 'edad': edad, 'raza': raza}
    rutas = generar_rutas(G, nodo_mas_cercano, duracion_paseo, perfil_perro)
    nombre_archivo_mapa = visualizar_rutas(G, rutas, latitud_actual, longitud_actual)
    nombre_archivo_mapa.save('rutas_paseo.html')
    respuesta_json = generar_json_respuesta(rutas, nombre_archivo_mapa)
    return respuesta_json

if __name__ == "__main__":
    json_input = '{"latitud": 42.3439, "longitud": -3.1007, "tamaño": "mediano", "edad": 5, "raza": "Labrador", "duracion": 30}'
    respuesta = main(json_input)
    print(respuesta)
