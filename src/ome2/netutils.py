import networkx as nx
from shapely.geometry import LineString
import math

def shortest_path_geometry(sp):
    coordinates_tuples = [tuple(map(float, coord.split('_'))) for coord in sp]
    return LineString(coordinates_tuples)

def node_coordinate(node):
    c = node.split('_')
    x=float(c[0]); y=float(c[1])
    return [x,y]

def graph_from_geodataframe(gdf, weight = lambda f:f.geometry.length, coord_simp=round):
    graph = nx.Graph()
    for i, f in gdf.iterrows():
        g = f.geometry
        pi = g.coords[0]
        pi = str(coord_simp(pi[0])) +'_'+ str(coord_simp(pi[1]))
        pf = g.coords[-1]
        pf = str(coord_simp(pf[0])) +'_'+ str(coord_simp(pf[1]))
        w = weight(f)
        graph.add_edge(pi, pf, weight=w)
    return graph





def a_star_euclidian_dist(n1, n2):
    [x1, y1] = node_coordinate(n1)
    [x2, y2] = node_coordinate(n2)
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

def a_star_manhattan_dist(n1, n2):
    [x1, y1] = node_coordinate(n1)
    [x2, y2] = node_coordinate(n2)
    return math.abs(x1-x2)+math.abs(y1-y2)