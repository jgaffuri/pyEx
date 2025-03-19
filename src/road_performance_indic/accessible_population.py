from shapely.geometry import box,Polygon
import geopandas as gpd
from datetime import datetime
import networkx as nx
#import concurrent.futures
#import threading
import fiona
import fiona.transform
from shapely.geometry import shape, mapping
from rtree import index
import csv
#from utils.featureutils import loadFeatures

# bbox - set to None to compute on the entire space
bbox = (3750000, 2720000, 3960000, 2970000)


# population grid
population_grid = "/home/juju/geodata/census/2021/ESTAT_Census_2021_V2.gpkg"

# tomtom road network
tomtom = "/home/juju/geodata/tomtom/tomtom_202312.gpkg"
tomtom_loader = lambda bbox: gpd.read_file('/home/juju/geodata/tomtom/2021/nw.gpkg', 'r', driver='GPKG', bbox=bbox),

# output CSV
accessible_population_csv = "/home/juju/gisco/road_transport_performance/accessible_population_2021.csv"


def compute_accessible_population(population_grid, layer, nearby_population_csv, only_populated_cells=True, bbox=None, radius_m = 120000):

    print(datetime.now(), "Loading population grid...", population_grid)
    gpkg = fiona.open(population_grid, 'r', driver='GPKG')
    where = "T > 0" if only_populated_cells else None
    cells = list(gpkg.items(bbox=bbox, layer=layer, where=where))

    print(datetime.now(), len(cells), "cells loaded")

    print(datetime.now(), "index cells...")
    spatial_index = index.Index()
    cells_ = []

    # feed index
    i = 0
    for c in cells:
        c = c[1]
        geom = shape(c["geometry"])
        pt = geom.centroid
        spatial_index.insert(i, geom.bounds)
        cells_.append( {"pop":c["properties"]["T"], "x":pt.x, "y":pt.y, "GRD_ID": c["properties"]["GRD_ID"]} )
        i += 1

    #free memory
    del cells

    #precompute
    radius_m_s = radius_m * radius_m

    print(datetime.now(), "compute indicator for each cell...")

    #lock = threading.Lock()
    def compute_cell_indicator(c):
        x=c["x"]
        y=c["y"]

        #get close cells using spatial index
        close_cells = None
        #with lock:
        close_cells = list(spatial_index.intersection((x-radius_m, y-radius_m, x+radius_m, y+radius_m)))

        #compute population total
        pop_tot = 0
        for i2 in close_cells:
            c2 = cells_[i2]
            dx = x-c2["x"]
            dy = y-c2["y"]

            #too far: skip
            if dx*dx+dy*dy>radius_m_s :continue

            #sum population
            pop_tot += c2["pop"]

        return { "pop":pop_tot, "GRD_ID":c["GRD_ID"] }

    #compute, not in parallel
    output = []
    for c in cells_: output.append(compute_cell_indicator(c))

    # Run in parallel
    #executor = concurrent.futures.ThreadPoolExecutor()
    #output = list(executor.map(compute_cell_indicator, cells_))

    print(datetime.now(), "Free memory")
    del spatial_index
    del cells_

    print(datetime.now(), "Save as CSV")
    file = open(nearby_population_csv, mode="w", newline="", encoding="utf-8")
    writer = csv.DictWriter(file, fieldnames=output[0].keys())
    writer.writeheader()
    writer.writerows(output)

    print(datetime.now(), "Done.")

#
compute_nearby_population(population_grid, "census2021", nearby_population_csv, bbox=bbox)

