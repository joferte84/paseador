import osmnx as ox
import folium
import pandas as pd
import geopandas as gpd
import json

def buscar_calles(lugar):
    calles = ox.features_from_place(lugar, {
        'highway': ['footway', 'path', 'pedestrian', 'living_street', 'track', 'trunk']
    })
    return calles

def filtrar_columnas(gdf):
    columnas = ['name', 'highway', 'geometry']
    return gdf[columnas]

def visualizar_calles(gdf_calles):
    mapa = folium.Map(location=[42.3439, -3.6969], zoom_start=13)
    for _, calle in gdf_calles.iterrows():
        if calle.geometry is None or calle.geometry.is_empty:
            continue
        folium.GeoJson(calle.geometry.__geo_interface__).add_to(mapa)
    return mapa

def guardar_datos(gdf_calles):
    gdf_calles.to_csv('calles1.csv', index=False)
    gdf_calles.to_file('calles1.geojson', driver='GeoJSON')

# Función principal
def main():
    lugar = "Burgos, Spain"
    gdf_calles = buscar_calles(lugar)
    gdf_calles = filtrar_columnas(gdf_calles)

    mapa_calles = visualizar_calles(gdf_calles)
    mapa_calles.save('mapa_calles1.html')

    guardar_datos(gdf_calles)

if __name__ == "__main__":
    main()