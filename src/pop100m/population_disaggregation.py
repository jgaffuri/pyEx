import fiona
from fiona.crs import CRS
from datetime import datetime
import os

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import loadFeatures, keep_attributes, get_schema_from_feature



def disaggregate_population_100m(x_min, y_min, nb_decimal = 2, cnt_codes = []):

    input_budem_file = "/home/juju/gisco/building_demography/out_partition/eurobudem_100m_"+str(x_min)+"_"+str(y_min)+".gpkg"
    if not os.path.isfile(input_budem_file): return

    #load 100m budem cells in tile
    print(datetime.now(), x_min, y_min, "load 100m budem cells")
    budem_grid = loadFeatures(input_budem_file)
    print(datetime.now(), x_min, y_min, len(budem_grid), "budem cells loaded")
    if(len(budem_grid)==0): return

    #filter population cell data
    for c100 in budem_grid:
        keep_attributes(c100, ["GRD_ID", "residential_floor_area"])
        #extract LLC position
        a = c100['GRD_ID'].split('mN')[1].split('E')
        c100['X_LLC'] = int(a[1])
        c100['Y_LLC'] = int(a[0])
        #initialise population
        c100['TOT_P_2021'] = 0

    #load 1000m population cells in tile
    print(datetime.now(), x_min, y_min, "load 1000m population cells")
    pop_grid = loadFeatures("/home/juju/geodata/grids/grid_1km_surf.gpkg", bbox=[x_min, y_min, x_min+500000, y_min+500000])
    print(datetime.now(), x_min, y_min, len(pop_grid), "pop cells loaded")
    pop_grid = [pc for pc in pop_grid if pc["NUTS2021_0"] in cnt_codes]
    print(datetime.now(), x_min, y_min, len(pop_grid), "pop cells, after filtering on " + str(cnt_codes))

    #filter population cell data
    for c1000 in pop_grid:
        keep_attributes(c1000, ["Y_LLC", "X_LLC", "TOT_P_2021"])



    #index 100m cells by x and then y
    index = {}
    for c100 in budem_grid:
        x100 = c100["X_LLC"]
        if not x100 in index: index[x100]={}
        index[x100][c100["Y_LLC"]] = c100


    #for each 1000m population cell
    for c1000 in pop_grid:

        #skip non populated cell
        pop1000 = c1000["TOT_P_2021"]
        if pop1000 == None or pop1000 == "" or pop1000 == 0: continue

        #get cell position
        x1000 = c1000["X_LLC"]
        y1000 = c1000["Y_LLC"]

        #get 100m cells inside 1000m cell using index
        cs100 = []

        for x100 in range(x1000, x1000+1000, 100):
            if not x100 in index: continue
            a = index[x100]
            for y100 in range(y1000, y1000+1000, 100):
                if not y100 in a: continue

                #get 100m cell
                c100 = a[y100]
                res_area = c100["residential_floor_area"]

                #exclude the 100m cells without residential area
                if res_area==None or res_area==0: continue

                cs100.append(c100)

        if len(cs100)==0:
            print(datetime.now(), x_min, y_min, "found population cell without residential area",x1000,y1000, "population loss:", pop1000)
            #TODO store the lost population on 1000m cells and analyse...
            #TODO assign population equally to all cells ? or a central one ?
            continue

        #compute total bu_res
        res_area = 0
        for c100 in cs100: res_area+=c100["residential_floor_area"]

        if res_area == 0:
            print(datetime.now(), x_min, y_min, "Unexpectect null building residence area around",x1000,y1000)
            continue

        #assign 100m population as pop*bu_res/tot_bu_res
        for c100 in cs100:
            c100["TOT_P_2021"] = round(pop1000 * c100["residential_floor_area"] / res_area, nb_decimal)

    print(datetime.now(), x_min, y_min, "save as GPKG")

    #build output data
    #TODO extract that ? as reverse of loadFeatures ? with 'mapping' function
    outd = []
    for cell in budem_grid:
        o = {"properties":{}}
        x1000 = cell["X_LLC"]; y1000 = cell["Y_LLC"]
        del cell["X_LLC"]; del cell["Y_LLC"]
        for k in cell: o["properties"][k] = cell[k]
        o["geometry"] = {'type': 'Polygon', 'coordinates': [[(x1000,y1000),(x1000+100,y1000),(x1000+100,y1000+100),(x1000,y1000+100),(x1000,y1000)]]}
        outd.append(o)

    #save it as gpkg
    schema = get_schema_from_feature(outd[0])
    #force type of TOT_P_2021 to be float
    schema["properties"]["TOT_P_2021"] = "float"
    outf = fiona.open("/home/juju/gisco/grid_pop_100m/out_partition/pop_2021_100m_"+str(x_min)+"_"+str(y_min)+".gpkg", 'w', driver='GPKG', crs=CRS.from_epsg(3035), schema=schema)
    outf.writerecords(outd)


#TODO parallel ?
#define country list
cnt_codes = ["FR", "NL", "PL", "IT", "LU"]
for x_min in range(3000000, 5500000, 500000):
    for y_min in range(1000000, 4000000, 500000):
        print(datetime.now(), x_min, y_min, "disaggregation ************")
        disaggregate_population_100m(x_min, y_min, cnt_codes=cnt_codes)
