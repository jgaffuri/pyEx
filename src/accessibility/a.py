from shapely.geometry import box
import geopandas as gpd
from datetime import datetime
import networkx as nx
import math

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from lib.netutils import shortest_path_geometry,graph_from_geodataframe,nodes_spatial_index,a_star_euclidian_dist
from lib.ome2utils import ome2_duration

#TODO filter by country
#TODO parallel

poi_dataset = '/home/juju/geodata/gisco/healthcare_EU_3035.gpkg'
OME_dataset = '/home/juju/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'
pop_grid_dataset = '/home/juju/geodata/grids/grid_1km_surf.gpkg'
grid_resolution = 1000
#the network layer to validate
layer = "tn_road_link"



#define partition
x_part = 4000000
y_part = 2800000
partition_size = 100000
extention_buffer = 50000 #on each side

#2900000  3700000



def proceed_partition(xy):
    [x_part,y_part] = xy

    bbox = box(x_part, y_part, x_part+partition_size, y_part+partition_size)
    #make extended bbox around partition
    extended_bbox = box(x_part-extention_buffer, y_part-extention_buffer, x_part+partition_size+extention_buffer, y_part+partition_size+extention_buffer)

    print(datetime.now(), "load and filter pois")
    pois = gpd.read_file(poi_dataset, bbox=extended_bbox)
    print(len(pois))
    if(len(pois)==0): return

    print(datetime.now(), "load population grid")
    cells = gpd.read_file(pop_grid_dataset, bbox=bbox)
    print(len(cells))
    if(len(cells)==0): return

    print(datetime.now(), "load and filter network links")
    links = gpd.read_file(OME_dataset, layer=layer, bbox=extended_bbox)
    print(len(links))
    if(len(links)==0): return
    #rn = ome2_filter_road_links(links)
    #print(len(links))
    #if(len(links)==0): continue

    print(datetime.now(), "make graph")
    graph = graph_from_geodataframe(links, lambda f:ome2_duration(f))
    #del links
    print(graph.number_of_edges())

    print(datetime.now(), "keep larger connex component")
    connected_components = list(nx.connected_components(graph))
    largest_component = max(connected_components, key=len)
    graph = graph.subgraph(largest_component)
    print(graph.number_of_edges())

    print(datetime.now(), "get POI nodes")

    #make list of nodes
    nodes_ = []
    for node in graph.nodes(): nodes_.append(node)

    #make nodes spatial index
    idx = nodes_spatial_index(graph)

    #get poi nodes
    sources = set()
    for iii, poi in pois.iterrows():
        n = nodes_[next(idx.nearest((poi.geometry.x, poi.geometry.y, poi.geometry.x, poi.geometry.y), 1))]
        sources.add(n)
    #del pois

    #TODO check pois are not too far from their node

    print(datetime.now(), "compute multi source dijkstra")
    duration = nx.multi_source_dijkstra_path_length(graph, sources, weight='weight')

    grd_ids = []
    durations = []
    for iii, cell in cells.iterrows():
        if(cell.TOT_P_2021==0): continue
        #get cell node
        b = cell.geometry.bounds
        x = b[0] + grid_resolution/2
        y = b[1] + grid_resolution/2
        n = nodes_[next(idx.nearest((x, y, x, y), 1))]
        #TODO store distance node/center
        d = math.round(duration[n]/60)
        grd_ids.append(cell.GRD_ID)
        durations.append(d)

    return [grd_ids, durations]


[grd_ids, durations] = proceed_partition(x_part, y_part, partition_size)

print(datetime.now(), "save as CSV")
out = gpd.GeoDataFrame({'GRD_ID': grd_ids, 'duration': durations })
out.to_csv("/home/juju/gisco/grid_accessibility_quality/out.csv", index=False)

