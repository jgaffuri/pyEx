from shapely.geometry import box
import geopandas as gpd
from datetime import datetime
import networkx as nx
import concurrent.futures

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from lib.utils import cartesian_product_comp
from lib.netutils import graph_from_geodataframe,nodes_spatial_index,distance_to_node
from lib.ome2utils import ome2_duration


def accessibility_grid(pois_loader,
                       cells_loader,
                       road_network_loader,
                             bbox,
                             out_folder,
                             out_file,
                             grid_resolution=1000,
                             partition_size = 100000,
                             extention_buffer = 30000,
                             num_processors_to_use = 1):

    def proceed_partition(xy):
        [x_part,y_part] = xy

        #partition bbox
        bbox = box(x_part, y_part, x_part+partition_size, y_part+partition_size)
        #partition extended bbox
        extended_bbox = box(x_part-extention_buffer, y_part-extention_buffer, x_part+partition_size+extention_buffer, y_part+partition_size+extention_buffer)

        print(datetime.now(),x_part,y_part, "load POIs")
        pois = pois_loader(extended_bbox)
        print(len(pois))
        if(len(pois)==0): return

        print(datetime.now(),x_part,y_part, "load population grid")
        cells = cells_loader(bbox)
        print(len(cells))
        if(len(cells)==0): return

        print(datetime.now(),x_part,y_part, "load and filter network links")
        links = road_network_loader(extended_bbox)
        print(len(links))
        if(len(links)==0): return

        print(datetime.now(),x_part,y_part, "make graph")
        graph = graph_from_geodataframe(links, lambda f:ome2_duration(f))
        del links
        print(graph.number_of_edges())

        print(datetime.now(),x_part,y_part, "keep larger connex component")
        connected_components = list(nx.connected_components(graph))
        largest_component = max(connected_components, key=len)
        graph = graph.subgraph(largest_component)
        print(graph.number_of_edges())

        print(datetime.now(),x_part,y_part, "get POI nodes")

        #make list of nodes
        nodes_ = []
        for node in graph.nodes(): nodes_.append(node)

        #make nodes spatial index
        idx = nodes_spatial_index(graph)

        #get POI nodes
        sources = set()
        for iii, poi in pois.iterrows():
            n = nodes_[next(idx.nearest((poi.geometry.x, poi.geometry.y, poi.geometry.x, poi.geometry.y), 1))]
            sources.add(n)
        del pois

        #TODO check pois are not too far from their node ?

        print(datetime.now(),x_part,y_part, "compute multi source dijkstra")
        duration = nx.multi_source_dijkstra_path_length(graph, sources, weight='weight')

        print(datetime.now(),x_part,y_part, "extract cell accessibility data")
        grd_ids = [] #the cell identifiers
        durations = [] #the durations
        distances_to_node = [] #the cell center distance to its graph node
        for iii, cell in cells.iterrows():
            #ignore unpopulated cells
            #TODO extract
            if(cell.TOT_P_2021==0): continue

            #get cell node
            b = cell.geometry.bounds
            x = b[0] + grid_resolution/2
            y = b[1] + grid_resolution/2
            n = nodes_[next(idx.nearest((x, y, x, y), 1))]

            #store cell id
            grd_ids.append(cell.GRD_ID)

            #store duration, in minutes
            d = round(duration[n]/60)
            durations.append(d)

            #store distance cell center/node
            d = round(distance_to_node(n,x,y))
            distances_to_node.append(d)

        return [grd_ids, durations, distances_to_node]


    #launch parallel computation   
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_processors_to_use) as executor:
        partitions = cartesian_product_comp(bbox[0], bbox[1], bbox[2], bbox[3], partition_size)
        tasks_to_do = {executor.submit(proceed_partition, partition): partition for partition in partitions}

        #out data
        grd_ids = []
        durations = []
        distances_to_node = []

        # merge task outputs
        for task_output in concurrent.futures.as_completed(tasks_to_do):
            out = task_output.result()
            if(out==None): continue
            grd_ids += out[0]
            durations += out[1]
            distances_to_node += out[2]

        print(datetime.now(), len(grd_ids), "cells")

        print(datetime.now(), "save as CSV")
        out = gpd.GeoDataFrame({'GRD_ID': grd_ids, 'duration': durations, "distance_to_node": distances_to_node })
        out.to_csv(out_folder+out_file+".csv", index=False)
