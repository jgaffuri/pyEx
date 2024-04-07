import geopandas as gpd
from shapely.geometry import LineString,MultiPoint,Point
from datetime import datetime
from geomutils import decompose_line
import math

folder = '/home/juju/Bureau/gisco/OME2_analysis/'
file_path = '/home/juju/Bureau/gisco/geodata/OME2_HVLSP_v1/gpkg/ome2.gpkg'

print(datetime.now(), "load nodes to get boundaries")
nodes = gpd.read_file(folder+"xborder_nodes_stamped.gpkg")
print(str(len(nodes)) + " nodes")

window = 30000
bbox = nodes.total_bounds
rnd = lambda x: int(window*math.ceil(x/window))
bbox = [rnd(x) for x in bbox]
[xmin, ymin, xmax, ymax] = bbox
nbx = int((xmax-xmin)/window)
nby = int((ymax-ymin)/window)
print(nbx,nby, bbox)

for i in range(nbx):
    for j in range(nby):
        bbox = [xmin+i*window,ymin+j*window,xmin+(i+1)*window,ymin+(j+1)*window]
        print("******" ,bbox)
        print(datetime.now(), "load nodes")
        nodes = gpd.read_file(folder+"xborder_nodes_stamped.gpkg", bbox=bbox)
        print(len(nodes))
        if(len(nodes)==0): continue
        print(datetime.now(), "load network links")
        rn = gpd.read_file(file_path, layer='tn_road_link', bbox=bbox)
        print(len(rn))
