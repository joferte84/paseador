import geopandas as gpd
from shapely.ops import nearest_points
import json
from nodos_rutas_y_pesos import crear_grafo_desde_geojson
import osmnx as ox

def cargar_datos_geojson(nombre_archivo_nodos, nombre_archivo_aristas):
    # Cargar datos de nodos y aristas desde archivos GeoJSON
    nodos_gdf = gpd.read_file('nodos_burgos.geojson')
    aristas_gdf = gpd.read_file('aristas_burgos.geojson')
    return nodos_gdf, aristas_gdf

def zonas_verdes_gdf(nombre_archivo_zonas_verdes):
    zonas_verdes_gdf = gpd.read_file('parques.geojson')
    return zonas_verdes_gdf
    
def obtener_ubicacion_actual(G, latitud, longitud):
    return ox.nearest_nodes(G, longitud, latitud)

def generar_json_respuesta(rutas, nombre_archivo_mapa, json_input):
    # Convertir la ruta en una lista de diccionarios
    ruta = [{'lat': nodo[0], 'lon': nodo[1]} for nodo in rutas]

    # Cargar los datos del perro
    datos_perro = cargar_datos_perro(json_input)

    # Añadir la ruta a los datos del perro
    datos_perro['ruta'] = ruta

    # Convertir los datos a JSON
    respuesta_json = json.dumps(datos_perro)

    return respuesta_json

def cargar_datos_perro(json_input):
    try:
        # Decodificar el JSON y convertirlo en un diccionario de Python
        datos_perro = json.loads(json_input)
        return datos_perro
    except json.JSONDecodeError as e:
        print(f"Error al decodificar el JSON: {e}")
        return None
    
