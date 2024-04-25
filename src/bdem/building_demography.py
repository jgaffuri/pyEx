import geopandas as gpd
from shapely.geometry import Polygon,box
from datetime import datetime
import concurrent.futures
import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from lib.utils import cartesian_product_comp

def building_demography_grid(buildings_loader,
                             bbox,
                             out_folder,
                             out_file,
                             resolution=1000,
                             partition_size = 50000,
                             nb_floors_fun=lambda f:1,
                             residential_fun=lambda f:0,
                             cultural_value_fun=lambda f:0,
                             crs = 'EPSG:3035',
                             num_processors_to_use = 1):

    #process on a partition
    def proceed_partition(xy):
        [x_,y_] = xy

        print(datetime.now(), x_, y_, "load buildings")
        buildings = buildings_loader(box(x_, y_, x_+partition_size, y_+partition_size))
        print(datetime.now(), x_, y_, len(buildings), "buildings loaded")
        if len(buildings)==0: return

        #print(datetime.now(), "spatial index buildings")
        buildings.sindex

        #out data
        cell_geometries = []
        tot_nbs = []
        tot_ground_areas = []
        tot_floor_areas = []
        tot_res_floor_areas = []
        tot_cult_ground_areas = []
        tot_cult_floor_areas = []
        grd_ids = []

        #go through cells
        for x in range(x_, x_+partition_size, resolution):
            for y in range(y_, y_+partition_size, resolution):

                #make grid cell geometry
                cell_geometry = Polygon([(x, y), (x+resolution, y), (x+resolution, y+resolution), (x, y+resolution)])

                #get buildings intersecting cell, using spatial index
                buildings_ = buildings.sindex.intersection(cell_geometry.bounds)
                if len(buildings_)==0: continue

                #initialise totals
                tot_nb = 0
                tot_ground_area = 0
                tot_floor_area = 0
                tot_res_floor_area = 0
                tot_cult_ground_area = 0
                tot_cult_floor_area = 0

                #go through buildings
                for i_ in buildings_:
                    bu = buildings.iloc[i_]
                    if not cell_geometry.intersects(bu.geometry): continue
                    bug = bu.geometry.buffer(0)
                    a = cell_geometry.intersection(bug).area
                    if a == 0: continue

                    #building number
                    nb = a/bug.area
                    if nb>1: nb=1
                    tot_nb += nb

                    #building area
                    tot_ground_area += a
                    floor_area = a * nb_floors_fun(bu)
                    tot_floor_area += floor_area

                    #residential buildings
                    tot_res_floor_area += residential_fun(bu) * floor_area

                    #cultural buildings
                    cult = cultural_value_fun(bu)
                    tot_cult_ground_area += cult * a
                    tot_cult_floor_area += cult * floor_area

                #round values
                tot_ground_area = round(tot_ground_area)
                tot_floor_area = round(tot_floor_area)
                tot_res_floor_area = round(tot_res_floor_area)
                tot_cult_ground_area = round(tot_cult_ground_area)
                tot_cult_floor_area = round(tot_cult_floor_area)

                if(tot_ground_area == 0): continue

                #store cell values
                cell_geometries.append(cell_geometry)
                tot_nbs.append(tot_nb)
                tot_ground_areas.append(tot_ground_area)
                tot_floor_areas.append(tot_floor_area)
                tot_res_floor_areas.append(tot_res_floor_area)
                tot_cult_ground_areas.append(tot_cult_ground_area)
                tot_cult_floor_areas.append(tot_cult_floor_area)

                #cell code
                grd_ids.append("CRS3035RES"+str(resolution)+"mN"+str(int(y))+"E"+str(int(x)))

        return [
            cell_geometries ,tot_nbs , tot_ground_areas , tot_floor_areas ,  tot_res_floor_areas , tot_cult_ground_areas , tot_cult_floor_areas , grd_ids
        ]

    #launch parallel computation   
    #with concurrent.futures.ThreadPoolExecutor(max_workers=num_processors_to_use) as executor:
    #    executor.map(proceed_partition, cartesian_product_comp(bbox[0], bbox[1], bbox[2], bbox[3], partition_size))

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_processors_to_use) as executor:
        partitions = cartesian_product_comp(bbox[0], bbox[1], bbox[2], bbox[3], partition_size)
        tasks_to_do = {executor.submit(proceed_partition, partition): partition for partition in partitions}

        #out data
        cell_geometries = []
        tot_nbs = []
        tot_ground_areas = []
        tot_floor_areas = []
        tot_res_floor_areas = []
        tot_cult_ground_areas = []
        tot_cult_floor_areas = []
        grd_ids = []

        # merge task outputs
        for task_output in concurrent.futures.as_completed(tasks_to_do):
            out = task_output.result()
            cell_geometries += out[0]
            tot_nbs += out[1]
            tot_ground_areas += out[2]
            tot_floor_areas += out[3]
            tot_res_floor_areas += out[4]
            tot_cult_ground_areas += out[5]
            tot_cult_floor_areas += out[6]
            grd_ids += out[7]


        print(datetime.now(), len(cell_geometries), "cells")

        print(datetime.now(), "save as GPKG")
        buildings = gpd.GeoDataFrame({'geometry': cell_geometries, 'GRD_ID': grd_ids, 'number': tot_nbs, 'ground_area': tot_ground_areas, 'floor_area': tot_floor_areas, 'residential_floor_area': tot_res_floor_areas, 'cultural_ground_area': tot_cult_ground_areas, 'cultural_floor_area': tot_cult_floor_areas })
        buildings.crs = crs
        buildings.to_file(out_folder+out_file+".gpkg", driver="GPKG")

        print(datetime.now(), "save as CSV")
        buildings = buildings.drop(columns=['geometry'])
        buildings.to_csv(out_folder+out_file+".csv", index=False)
        print(datetime.now(), "save as parquet")
        buildings.to_parquet(out_folder+out_file+".parquet")