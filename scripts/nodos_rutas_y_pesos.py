from shapely.geometry import Point, LineString
import geopandas as gpd
from geopy.distance import distance
from shapely.ops import nearest_points
import networkx as nx
import caracter_perro as cp
import velocidad_y_distancia as vd
import carga_datos_yDevolver_json as carga_datos

def lineas_a_nodos(calles_gdf):
    nodos = set()
    for linea in calles_gdf.geometry:
        if isinstance(linea, LineString):
            nodos.add(linea.coords[0])
            nodos.add(linea.coords[-1])

    nodos_gdf = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in nodos])
    nodos_gdf['x'] = nodos_gdf.geometry.x
    nodos_gdf['y'] = nodos_gdf.geometry.y

    nodos_gdf['osmid'] = range(len(nodos_gdf))
    return nodos_gdf

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
                
def calcular_distancia_entre_nodos(G, nodo1, nodo2):
    y1, x1 = G.nodes[nodo1]['y'], G.nodes[nodo1]['x']
    y2, x2 = G.nodes[nodo2]['y'], G.nodes[nodo2]['x']
    return distance((y1, x1), (y2, x2)).meters

def calcular_distancia_a_zonas_verdes(arista, zonas_verdes_gdf):
    punto_arista = arista.geometry.centroid
    puntos_zonas_verdes = zonas_verdes_gdf.geometry.apply(lambda x: nearest_points(punto_arista, x)[1])
    distancia_minima = min([punto_arista.distance(punto) for punto in puntos_zonas_verdes])
    return distancia_minima

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
    tamaño_raza = cp.caracteristicas_perros.get(raza, {"Tamaño": "Mediano"})["Tamaño"].lower()
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

def estimar_distancia(duracion, perfil_perro):
    # Obtiene la raza del perro desde el perfil
    raza = perfil_perro.get('raza')
    # Calcula la velocidad basada en la raza del perro
    velocidad = vd.estimar_velocidad(raza)
    # Calcula la distancia basada en la duración del paseo y la velocidad
    return duracion * velocidad

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
    mejor_ruta = seleccionar_ruta(rutas_posibles, G, carga_datos.zonas_verdes_gdf, perfil_perro)  
    return mejor_ruta

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

