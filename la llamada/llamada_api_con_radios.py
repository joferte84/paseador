import folium
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point, Polygon
import overpy

def obtener_grafo_de_osm(lat, lon, radio_km):
    punto_central = Point(lon, lat)
    poligono = punto_central.buffer(radio_km / 111.32)  # Aproximación de 1 grado de latitud ~= 111.32 km
    graph = ox.graph_from_polygon(poligono, network_type='all_private', simplify=False, retain_all=True)
    return graph

def buscar_zonas_verdes(lat, lon, radio_km):
    api = overpy.Overpass()
    radio_m = radio_km * 1000
    consulta = f"""
    [out:json];
    (
        // Buscar por varias etiquetas de zonas verdes
        way["leisure"~"park|nature_reserve|dog_park|garden"]["access"!="no"](around:{radio_m},{lat},{lon});
        way["landuse"~"forest|village_green|grass"]["access"!="no"](around:{radio_m},{lat},{lon});
        way["natural"~"scrub|heath"]["access"!="no"](around:{radio_m},{lat},{lon});
        relation["leisure"~"park|nature_reserve|dog_park|garden"]["access"!="no"](around:{radio_m},{lat},{lon});
        relation["landuse"~"forest|village_green|grass"]["access"!="no"](around:{radio_m},{lat},{lon});
        relation["natural"~"scrub|heath"]["access"!="no"](around:{radio_m},{lat},{lon});
    );
    (._;>;);
    out body;
    """
    try:
        resultado = api.query(consulta)
    except overpy.exception.OverpassBadRequest as e:
        print(f"Error en la consulta Overpass: {e}")
        return gpd.GeoDataFrame()

    zonas_verdes = []
    for elem in resultado.ways + resultado.relations:
        tags = elem.tags
        if tags.get('garden:type') != "private" and tags.get('barrier') is None and tags.get('access') != "no":
            if isinstance(elem, overpy.Way):
                nodos = elem.nodes
            elif isinstance(elem, overpy.Relation):
                nodos = [nodo.resolve() for nodo in elem.members if isinstance(nodo, overpy.RelationNode)]
            else:
                continue

            if len(nodos) > 2:
                poligono = Polygon([(float(nodo.lon), float(nodo.lat)) for nodo in nodos])
                zonas_verdes.append(poligono)

    return gpd.GeoDataFrame(geometry=zonas_verdes, crs="EPSG:4326")

def crear_mapa(lat, lon, radio_km, zonas_verdes, grafo):
    m = folium.Map(location=[lat, lon], zoom_start=15)
    for index, zona_verde in zonas_verdes.iterrows():
        folium.GeoJson(zona_verde.geometry, style_function=lambda feature: {
            'fillColor': 'green',
            'color': 'green',
            'weight': 2,
            'fillOpacity': 0.5
        }).add_to(m)

    for u, v, key, data in grafo.edges(keys=True, data=True):
        if 'geometry' in data:
            xs, ys = data['geometry'].xy
            puntos = list(zip(ys, xs))
            folium.PolyLine(puntos, color='blue').add_to(m)
        else:
            punto_inicio = grafo.nodes[u]['y'], grafo.nodes[u]['x']
            punto_final = grafo.nodes[v]['y'], grafo.nodes[v]['x']
            folium.PolyLine([punto_inicio, punto_final], color='blue').add_to(m)

    m.save('mapa.html')
    print("Mapa generado exitosamente en mapa.html")

# Ejemplo de uso de las funciones
lat, lon = 40.4168, -3.7038  # Coordenadas de Madrid, España
radio_km = 1

grafo = obtener_grafo_de_osm(lat, lon, radio_km)
zonas_verdes = buscar_zonas_verdes(lat, lon, radio_km)
crear_mapa(lat, lon, radio_km, zonas_verdes, grafo)
