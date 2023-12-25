import osmnx as ox
import folium
import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import LineString, MultiLineString

# Funciones Auxiliares (Comunes en ambos scripts)
def convertir_a_string_si_es_necesario(valor):
    if isinstance(valor, (list, dict)):
        return json.dumps(valor)
    return valor

def preparar_para_geojson(dataframe):
    for columna in dataframe.columns:
        if columna != 'geometry':  
            dataframe[columna] = dataframe[columna].apply(convertir_a_string_si_es_necesario)
    return dataframe

# Función para preparar los datos para la recomendación de rutas
def preparar_datos(gdf):
    columnas = ['name', 'highway', 'sidewalk', 'lit', 'smoothness', 'surface', 'geometry']
    gdf_filtrado = gdf[columnas].copy()
    gdf_filtrado = gdf_filtrado[gdf_filtrado['highway'].isin(['residential', 'pedestrian', 'path'])]
    return gdf_filtrado

# Funciones Específicas para Calles
def buscar_calles(lugar):
    calles = ox.features_from_place(lugar, {
        'highway': ['footway', 'path', 'pedestrian', 'living_street', 'track', 'trunk']
    })
    return calles

def agrupar_calles_por_nombre(gdf):
    # Separar calles con nombre y sin nombre
    gdf_con_nombre = gdf.dropna(subset=['name'])
    gdf_sin_nombre = gdf[gdf['name'].isna()]

    # Agrupar y combinar calles con nombre
    gdf = gdf_con_nombre.dissolve(by='name', aggfunc='first')

    # Concatenar con calles sin nombre
    gdf = pd.concat([gdf, gdf_sin_nombre])

    return gdf

def agregar_columna_tipo_y_id_calles(dataframe):
    dataframe['tipo_calle'] = dataframe['highway']
    dataframe['id'] = range(1, len(dataframe) + 1)
    return dataframe

def agregar_lineas_al_mapa(mapa, dataframe, color):
    for _, calle in dataframe.iterrows():
        if calle.geometry is None or calle.geometry.is_empty:
            continue

        if calle.geometry.geom_type in ['LineString', 'MultiLineString']:
            folium.GeoJson(
                calle.geometry.__geo_interface__,
                style_function=lambda feature: {
                    'color': color,
                    'weight': 2
                }
            ).add_to(mapa)

def guardar_calles_en_csv_y_geojson(calles):
    calles_preparados = preparar_para_geojson(calles.copy())
    calles_preparados.to_csv('calles.csv', index=False)
    calles_preparados.to_file('calles.geojson', driver='GeoJSON')

# Función Principal
def main():
    lugar = "Burgos, Spain"
    calles = buscar_calles(lugar)
    calles_gdf = gpd.GeoDataFrame(calles, crs="EPSG:4326")
    calles_gdf = agregar_columna_tipo_y_id_calles(calles_gdf)

    calles_gdf = preparar_datos(calles_gdf)
    calles_gdf = agrupar_calles_por_nombre(calles_gdf)
    
    guardar_calles_en_csv_y_geojson(calles_gdf)
    
    mapa_calles = folium.Map(location=[42.3439, -3.6969], zoom_start=13)
    agregar_lineas_al_mapa(mapa_calles, calles_gdf, 'blue')
    mapa_calles.save('mapa_calles.html')

if __name__ == "__main__":
    main()