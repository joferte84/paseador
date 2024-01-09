import carga_datos_yDevolver_json as carga_datos
import geopandas as gpd
import nodos_rutas_y_pesos as nrp
import geopandas as gpd

# Principal
def main(json_input):
    datos_perro = carga_datos.cargar_datos_perro(json_input)
    if not datos_perro:
        print("No se pudieron cargar los datos del perro.")
        return

    latitud_actual, longitud_actual = datos_perro['latitud'], datos_perro['longitud']
    tamaño, edad, raza = datos_perro['tamaño'], datos_perro['edad'], datos_perro['raza']
    duracion_paseo = datos_perro['duracion']

    # Cargar datos geográficos
    nombre_archivo_nodos = 'nodos_burgos.geojson'
    nombre_archivo_aristas = 'aristas_burgos.geojson'
    nodos_gdf, aristas_gdf = carga_datos.cargar_datos_geojson(nombre_archivo_nodos, nombre_archivo_aristas)
    G = carga_datos.crear_grafo_desde_geojson(nodos_gdf, aristas_gdf)

    # Cargar zonas verdes
    zonas_verdçes_gdf = gpd.read_file('parques.geojson')
    factor_reduccion_general = 0.5
    factor_reduccion_dog_park = 0.7  # Mayor reducción para dog parks
    nrp.aplicar_peso_zonas_verdes(G, carga_datos.zonas_verdes_gdf, distancia_umbral=10, 
                            factor_reduccion=factor_reduccion_general, 
                            factor_reduccion_dog_park=factor_reduccion_dog_park)

    nodo_mas_cercano = carga_datos.obtener_ubicacion_actual(G, latitud_actual, longitud_actual)

    # Generar y visualizar rutas
    perfil_perro = {'tamaño': tamaño, 'edad': edad, 'raza': raza}
    rutas = nrp.generar_rutas(G, nodo_mas_cercano, duracion_paseo, perfil_perro)
    nombre_archivo_mapa = nrp.visualizar_rutas(G, rutas, latitud_actual, longitud_actual)
    nombre_archivo_mapa.save('rutas_paseo.html')
    respuesta_json = carga_datos.generar_json_respuesta(rutas, nombre_archivo_mapa)
    return respuesta_json

if __name__ == "__main__":
    json_input = '{"latitud": 42.3439, "longitud": -3.1007, "tamaño": "mediano", "edad": 5, "raza": "Labrador", "duracion": 30}'
    respuesta = main(json_input)
    print(respuesta)