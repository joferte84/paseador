import osmnx as ox
import folium
import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import Polygon, MultiPolygon

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
    columnas_relevantes = ['name', 'natural', 'landuse', 'leisure', 'geometry', 'area']
    gdf_filtrado = gdf[columnas_relevantes].copy()

    return gdf_filtrado

# Funciones Específicas para Parques
def buscar_parques(lugar):
    parques_y_jardines = ox.features_from_place(lugar, {
        'leisure': ['park', 'nature_reserve', 'dog_park'],
        'landuse': ['forest', "village_green", "grass"],
        'natural': ['scrub', 'heath']
    })

    jardines = ox.features_from_place(lugar, {'leisure': 'garden'})
    jardines_con_nombre = jardines[jardines['name'].notna()]
    parques_y_jardines = gpd.GeoDataFrame(pd.concat([parques_y_jardines, jardines_con_nombre], ignore_index=True))
    
    return parques_y_jardines

def agregar_columna_tipo_y_id(dataframe, tipo_columna='tipo_jardin'):
    # Verificar si las columnas existen antes de acceder a ellas y asignar el tipo de área
    dataframe[tipo_columna] = dataframe.apply(lambda x: x['leisure'] if 'leisure' in x and pd.notna(x['leisure']) else 
                                            (x['landuse'] if 'landuse' in x and pd.notna(x['landuse']) else 
                                            (x['natural'] if 'natural' in x and pd.notna(x['natural']) else None)), axis=1)
    
    # Asignar un ID incremental a cada fila
    dataframe['id'] = range(1, len(dataframe) + 1)
    
    # Calcular el área de los polígonos en metros cuadrados y asignarla a una nueva columna
    # Hacer una copia para cambiar el CRS solo para el cálculo del área
    dataframe_crs = dataframe.copy().to_crs(epsg=3857)
    dataframe['area'] = dataframe_crs.area
    dataframe_crs = None  # Eliminar la copia para liberar memoria

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

def crear_mapa_de_dog_parks(dataframe, color_dog_park='red', opacidad=0.4, archivo_mapa='mapa_dog_parks.html'):
    # Filtrar para obtener solo dog parks
    dog_parks = dataframe[dataframe['leisure'] == 'dog_park']

    # Crear un mapa centrado en las coordenadas promedio de los dog parks
    if not dog_parks.empty:
        centro = dog_parks.geometry.unary_union.centroid
        mapa_dog_parks = folium.Map(location=[centro.y, centro.x], zoom_start=15)
    else:
        print("No se encontraron dog parks en el DataFrame proporcionado.")
        return

    for index, area in dog_parks.iterrows():
        if not isinstance(area.geometry, (Polygon, MultiPolygon)) or area.geometry.is_empty:
            continue

        nombre = area['name'] if pd.notna(area['name']) else 'Parque para Perros'
        id_area = area['id']
        area_m2 = area['area'] if 'area' in area else None

        popup_text = f"ID: {id_area}<br>Nombre: {nombre}<br>Área: {area_m2:.2f} m²" if area_m2 else f"ID: {id_area}<br>Nombre: {nombre}"
        popup = folium.Popup(popup_text, parse_html=True)
        geojson = folium.GeoJson(
            area.geometry.__geo_interface__,
            style_function=lambda feature: {
                'fillColor': color_dog_park,
                'color': color_dog_park,
                'weight': 1,
                'fillOpacity': opacidad
            }
        )
        geojson.add_child(popup)
        geojson.add_to(mapa_dog_parks)

    # Guardar el mapa en un archivo HTML
    mapa_dog_parks.save(archivo_mapa)

def guardar_parques_en_csv_y_geojson(parques_y_jardines):
    parques_y_jardines_preparados = preparar_para_geojson(parques_y_jardines.copy())
    parques_y_jardines_preparados.to_csv('parques.csv', index=False)
    parques_y_jardines_preparados.to_file('parques.geojson', driver='GeoJSON')
    
def main():
    lugar = "Burgos, Spain"
    parques_y_jardines = buscar_parques(lugar)
    parques_y_jardines_gdf = gpd.GeoDataFrame(parques_y_jardines, crs="EPSG:4326")
    
    parques_y_jardines_gdf = preparar_datos(parques_y_jardines_gdf)
    parques_y_jardines_gdf = agregar_columna_tipo_y_id(parques_y_jardines_gdf, 'tipo_jardin')
    
    # Crear el mapa
    mapa_parques = folium.Map(location=[42.3439, -3.6969], zoom_start=13)

    # Agregar polígonos al mapa asegurándote de que solo se agregan una vez con el color correcto
    agregar_poligonos_al_mapa(mapa_parques, parques_y_jardines_gdf, 'green', 0.4)

    # Guardar el mapa
    mapa_parques.save('mapa_parques.html')
    
    # Crear un mapa específico para dog parks
    crear_mapa_de_dog_parks(parques_y_jardines_gdf)

if __name__ == "__main__":
    main()