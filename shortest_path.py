import requests
from heapq import nsmallest
from math import asin, cos, radians, sin, sqrt
import folium
import networkx as nx
import osmnx as ox

def get_long_lat_by_text(street, number):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': 'Москва, ' + street + ', ' + number,
        'format': 'json',
        'polygon': 1,
        'addressdetails': 1
    }
    r = requests.get(url, params=params)
    result = r.json()[0]
    return float(result['lat']), float(result['lon'])

    
### FROM: https://stackoverflow.com/questions/59736682/find-nearest-location-coordinates-in-land-using-python
def dist_between_two_points(name, *args):
    lat1, lat2, long1, long2 = map(radians, args)
    dist_lats = abs(lat2 - lat1) 
    dist_longs = abs(long2 - long1) 
    a = sin(dist_lats/2)**2 + cos(lat1) * cos(lat2) * sin(dist_longs/2)**2
    c = asin(sqrt(a)) * 2
    radius_earth = 6378
    return { name : c * radius_earth }
### END FROM

def get_nearest(location, data):
    result = {}
    distance = [dist_between_two_points(p[0] + ". " + p[1], location[0], p[2], location[1], p[3]) for p in data]
    for i in distance:
        result.update(i)
    return nsmallest(3, result, key = result.get)

def plot_path(start, end):
    latitude_start, longitude_start = start
    latitude_end, longitude_end = end
    
    # инициализируем граф
    G = ox.graph_from_point(start, network_type='walk')

    # Ищем ближайшие узлы в графе к начальной и конечной точкам
    start_node = ox.distance.nearest_nodes(G, longitude_start, latitude_start)
    end_node = ox.distance.nearest_nodes(G, longitude_end, latitude_end)

    # Ищем самый короткий путь при помощи алгоритма Дейкстры
    shortest_path = nx.shortest_path(G, start_node, end_node, weight='time')

    # Создаем Folium map с центром в старте
    m = folium.Map(location=start, zoom_start=13)

    # Добавлением маркера на стартовую и конечную метки
    folium.Marker(location=start, icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(location=end, icon=folium.Icon(color='red')).add_to(m)

    # Отрисовка короткого пути
    path_coordinates = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in shortest_path]
    folium.PolyLine(locations=path_coordinates, color='blue', weight=5).add_to(m)
    
    # Масштбирование
    bounds = path_coordinates
    m.fit_bounds(bounds)

    return G, m
