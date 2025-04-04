from pygridmap import gridtiler
from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.gridutils import get_cell_xy_from_id

transform = False
aggregation = True
tiling = False

folder = "/home/juju/geodata/census/"
input_file = folder + "ESTAT_Census_2021_V2_csv_export.csv"


def transform_fun(c):
    #GRD_ID,T,M,F,Y_LT15,Y_1564,Y_GE65,EMP,NAT,EU_OTH,OTH,SAME,CHG_IN,CHG_OUT

    #filter out cells with no population
    t = c["T"]
    if t=="0" or t=="" or t == None: return False

    #del c["fid"]

    #get x and y
    [x, y] = get_cell_xy_from_id(c['GRD_ID'])
    c["x"] = x
    c["y"] = y
    del c['GRD_ID']

    #remove zeros
    for p in "T","M","F","Y_LT15","Y_1564","Y_GE65","EMP","NAT","EU_OTH","OTH","SAME","CHG_IN","CHG_OUT":
        v = c[p]
        if v == "0": c[p] = ""

    c["NB"] = 1
    #del c['CONFIDENTIALSTATUS']
    #del c['POPULATED']
    #del c['LAND_SURFACE']
    #print(c)


#apply transform
if transform:
    print("transform")
    gridtiler.grid_transformation(input_file=input_file, output_file=folder+"out/ESTAT_Census_2021_V2_1000.csv", function=transform_fun)




#aggregation
if aggregation:
    for a in [2,5,10]:
        print(datetime.now(), "aggregation to", a*1000, "m")
        gridtiler.grid_aggregation(input_file=folder+"out/ESTAT_Census_2021_V2_1000.csv", resolution=1000, output_file=folder+"out/ESTAT_Census_2021_V2_"+str(a*1000)+".csv", a=a)
    for a in [2,5,10]:
        print(datetime.now(), "aggregation to", a*10000, "m")
        gridtiler.grid_aggregation(input_file=folder+"out/ESTAT_Census_2021_V2_10000.csv", resolution=10000, output_file=folder+"out/ESTAT_Census_2021_V2_"+str(a*10000)+".csv", a=a)



#tiling
if tiling:
    for resolution in [1000, 2000, 5000, 10000, 20000, 50000, 100000]:
        print("tiling for resolution", resolution)

        #create output folder
        out_folder = folder + 'out/' + str(resolution)
        if not os.path.exists(folder): os.makedirs(folder)

        gridtiler.grid_tiling(
            folder+"out/ESTAT_Census_2021_V2_"+str(resolution)+'.csv',
            out_folder,
            resolution,
            tile_size_cell = 256,
            x_origin = 0,
            y_origin = 0,
            crs = "EPSG:3035",
            format = "parquet"
        )
