import osmnx as ox
import folium
import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import Polygon, MultiPolygon

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

# Función optimizada para preparar los datos
def preparar_datos(gdf):
    columnas_relevantes = ['name', 'type', 'surface', 'landuse', 'leisure', 'geometry', 'area', 'wheelchair']
    gdf_filtrado = gdf[columnas_relevantes].copy()

    return gdf_filtrado

# Funciones Específicas para Parques
def buscar_parques_jardines(lugar):
    parques_y_jardines = ox.features_from_place(lugar, {
        'leisure': ['park', 'nature_reserve', 'dog_park'],
        'landuse': ['forest', "village_green", "grass"],
        'natural': ['scrub', 'heath']
    })

    jardines = ox.features_from_place(lugar, {'leisure': 'garden'})
    jardines_con_nombre = jardines[jardines['name'].notna()]
    parques_y_jardines = gpd.GeoDataFrame(pd.concat([parques_y_jardines, jardines_con_nombre], ignore_index=True))
    
    return parques_y_jardines

def agregar_columna_tipo_y_id_parques(dataframe):
    dataframe['tipo_jardin'] = dataframe.apply(lambda x: x['leisure'] if pd.notna(x['leisure']) else 
                                            (x['landuse'] if pd.notna(x['landuse']) else x['natural']), axis=1)
    dataframe['id'] = range(1, len(dataframe) + 1)
    return dataframe

def agregar_poligonos_al_mapa(mapa, dataframe, color, opacidad):
    for area in dataframe.itertuples():
        if not isinstance(area.geometry, (Polygon, MultiPolygon)) or area.geometry.is_empty:
            continue

        nombre = getattr(area, 'name', 'Sin nombre')
        popup_text = f"ID: {area.id}<br>Nombre: {nombre}<br>Área: {area.area:.2f} m²"
        popup = folium.Popup(popup_text, parse_html=True)
        geojson = folium.GeoJson(
            area.geometry.__geo_interface__,
            style_function=lambda feature: {
                'fillColor': color,
                'color': color,
                'weight': 1,
                'fillOpacity': opacidad
            }
        )
        geojson.add_child(popup)
        geojson.add_to(mapa)

def guardar_parques_en_csv_y_geojson(parques_y_jardines):
    parques_y_jardines_preparados = preparar_para_geojson(parques_y_jardines.copy())
    parques_y_jardines_preparados.to_csv('parques_y_jardines.csv', index=False)
    parques_y_jardines_preparados.to_file('parques_y_jardines.geojson', driver='GeoJSON')

# Función Principal
def main():
    lugar = "Burgos, Spain"
    parques_y_jardines = buscar_parques_jardines(lugar)
    parques_y_jardines_gdf = gpd.GeoDataFrame(parques_y_jardines, crs="EPSG:4326")
    parques_y_jardines_gdf = agregar_columna_tipo_y_id_parques(parques_y_jardines_gdf)

    parques_y_jardines_gdf = preparar_datos(parques_y_jardines_gdf)

    guardar_parques_en_csv_y_geojson(parques_y_jardines_gdf)

    mapa_parques = folium.Map(location=[42.3439, -3.6969], zoom_start=13)
    agregar_poligonos_al_mapa(mapa_parques, parques_y_jardines_gdf, 'green', 0.4)
    mapa_parques.save('mapa_parques.html')

if __name__ == "__main__":
    main()
