import osmnx as ox
import networkx as nx
import folium
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

# Configura OSMnx
ox.config(use_cache=True, log_console=True)

# Funciones Auxiliares
def cargar_datos():
    calles_gdf = gpd.read_file('calles.geojson')
    zonas_verdes_gdf = gpd.read_file('zonas_verdes.geojson')
    return calles_gdf, zonas_verdes_gdf

def calcular_distancia_a_zonas_verdes(arista, zonas_verdes_gdf):
    punto_arista = arista.geometry.centroid
    puntos_zonas_verdes = zonas_verdes_gdf.geometry.apply(lambda x: nearest_points(punto_arista, x)[1])
    distancia_minima = min([punto_arista.distance(punto) for punto in puntos_zonas_verdes])
    return distancia_minima

def aplicar_peso_zonas_verdes(G, zonas_verdes_gdf, distancia_umbral, factor_reduccion):
    for u, v, key, data in G.edges(keys=True, data=True):
        arista = gpd.GeoDataFrame([data], geometry=[LineString([Point(G.nodes[u]['x'], G.nodes[u]['y']), 
                                                                Point(G.nodes[v]['x'], G.nodes[v]['y'])])])
        distancia = calcular_distancia_a_zonas_verdes(arista.iloc[0], zonas_verdes_gdf)
        if distancia < distancia_umbral:
            G[u][v][key]['weight'] *= factor_reduccion

def obtener_ubicacion_actual():
    # En un caso real, esta función obtendría la ubicación actual del usuario
    return 42.3439, -3.6969  

def estimar_velocidad(perfil_perro):
    # Simplificación de la lógica
    peso = perfil_perro.get('peso', 0)
    tipo = perfil_perro.get('tipo', '').lower()

    if tipo == 'moloso':
        return 3
    if tipo in ['nervioso', 'caza', 'rastreo']:
        return 4
    if peso <= 7 or (peso <= 18 and tipo == 'tranquilo'):
        return 2
    if peso > 18:
        return 4  

    return 3

def estimar_distancia(duracion, perfil_perro):
    # Calcula la distancia basada en la duración del paseo y el perfil del perro
    velocidad = estimar_velocidad(perfil_perro)
    return duracion * velocidad

# Nuevas funciones para encontrar rutas circulares
def calcular_distancia_entre_nodos(G, nodo1, nodo2):
    y1, x1 = G.nodes[nodo1]['y'], G.nodes[nodo1]['x']
    y2, x2 = G.nodes[nodo2]['y'], G.nodes[nodo2]['x']
    return ox.utils.euclidean_dist_vec(y1, x1, y2, x2)

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
    # Factores de puntuación basados en el perfil del perro
    factor_tamaño = {'pequeño': 1, 'mediano': 2, 'grande': 3}.get(perfil_perro.get('tamaño', 'mediano'), 2)
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
    mejor_ruta = seleccionar_ruta(rutas_posibles, perfil_perro)
    return mejor_ruta

def visualizar_rutas(G, rutas, latitud_actual, longitud_actual):
    mapa = folium.Map(location=[latitud_actual, longitud_actual], zoom_start=15)
    for ruta in rutas:
        ox.plot_route_folium(G, ruta, route_map=mapa)
    return mapa

# Principal
def main():
    # Cargar datos de calles y zonas verdes
    calles_gdf, zonas_verdes_gdf = cargar_datos()
    if calles_gdf is None or zonas_verdes_gdf is None:
            return
    # Obtener ubicación actual
    latitud_actual, longitud_actual = obtener_ubicacion_actual()

    # Crear grafo a partir de los datos geográficos
    G = ox.graph_from_gdfs(calles_gdf, zonas_verdes_gdf)

    # Aplicar pesos a las aristas basándose en las zonas verdes
    aplicar_peso_zonas_verdes(G, zonas_verdes_gdf, distancia_umbral=10, factor_reduccion=0.5)

    nodo_mas_cercano = ox.get_nearest_node(G, (latitud_actual, longitud_actual))

    # Definir perfil del perro y duración del paseo
    perfil_perro = {'tamaño': 'mediano', 'edad': 5}
    duracion_paseo = 30  # Duración en minutos

    # Generar rutas
    rutas = generar_rutas(G, nodo_mas_cercano, duracion_paseo, perfil_perro)

    # Visualizar rutas
    mapa_rutas = visualizar_rutas(G, rutas, latitud_actual, longitud_actual)
    mapa_rutas.save('rutas_paseo.html')

if __name__ == "__main__":
    main()
