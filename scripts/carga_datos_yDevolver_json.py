import geopandas as gpd
import osmnx as ox
from shapely.ops import nearest_points
import folium
import json

def cargar_datos_geojson(nombre_archivo_nodos, nombre_archivo_aristas):
    # Cargar datos de nodos y aristas desde archivos GeoJSON
    nodos_gdf = gpd.read_file('nodos_burgos.geojson')
    aristas_gdf = gpd.read_file('aristas_burgos.geojson')
    return nodos_gdf, aristas_gdf

def cargar_datos(nombre_archivo_zonas_verdes):
    zonas_verdes_gdf = gpd.read_file('parques.geojson')
    return zonas_verdes_gdf
    
def obtener_ubicacion_actual(G, latitud, longitud):
    # Retorna el nodo más cercano a la ubicación dada
    return ox.get_nearest_node(G, (latitud, longitud))

def obtener_ubicacion_actual():
    # En un caso real, esta función obtendría la ubicación actual del usuario
    return 42.3439, -3.6969  

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
    
