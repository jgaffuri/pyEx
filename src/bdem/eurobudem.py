import fiona
from math import ceil,isnan,floor
from building_demography import building_demography_grid
from shapely.geometry import shape
import random

#TODO
# other countries: NL, BE, PL, IT... see eubc
# test GPKG writing with fiona
# FR date of creation
# other years


bbox = [3000001, 3000001, 3000001, 3000001]
#bbox = [3000000, 2000000, 4313621, 3162995]
grid_resolution = 100
file_size_m = 500000
out_folder = '/home/juju/gisco/building_demography/out_partition/'

clamp = lambda v:floor(v/file_size_m)*file_size_m
[xmin,ymin,xmax,ymax] = [clamp(v) for v in bbox]


#TODO extract
def loadFeatures(file, bbox):
    features = []
    gpkg = fiona.open(file, 'r')
    data = list(gpkg.items(bbox=bbox))
    for d in data:
        d = d[1]
        f = { "geometry": shape(d['geometry']) }
        properties = d['properties']
        for key, value in properties.items(): f[key] = value
        features.append(f)
    return features

#TODO extract
def keepOnlyGeometry(feature):
    for attribute in list(feature.keys()):
        if attribute != 'geometry': feature.pop(attribute)




def loadBuildings(bbox):
    buildings = []

    #FR
    buildings_FR = loadFeatures('/home/juju/geodata/FR/BD_TOPO/BATI/batiment_3035.gpkg', bbox)
    for bu in buildings_FR: formatBuildingFR(bu)
    buildings += buildings_FR
    
    #IT
    #TODO

    #LU
    #TODO

    return buildings




def formatBuildingFR(bu):
    h = bu["hauteur"]
    u1 = bu["usage_1"]
    u2 = bu["usage_2"]
    n = bu["nature"]

    keepOnlyGeometry(bu)

    floor_nb = 1 if h==None or isnan(h) else ceil(h/3)
    bu["floor_nb"] = floor_nb
    residential = 1 if u1=="Résidentiel" else 0.3 if u2=="Résidentiel" else 0.1 if u1=="Indifférencié" else 0
    bu["residential"] = residential
    activity = 1 if u1=="Agricole" or u1=="Commercial et services" or u1=="Industriel" else 0.3 if u2=="Agricole" or u2=="Commercial et services" or u2=="Industriel" else 0.1 if u1=="Indifférencié" else 0
    bu["activity"] = activity
    cultural_value = 1 if u1=="Religieux" or n=="Tour, donjon" or n=="Monument" or n=="Moulin à vent" or n=="Arc de triomphe" or n=="Fort, blockhaus, casemate" or n=="Eglise" or n=="Château" or n=="Chapelle" or n=="Arène ou théâtre antique" else 0
    bu["cultural_value"] = cultural_value





for x in range(xmin, xmax+1, file_size_m):
    for y in range(ymin, ymax+1, file_size_m):
        print(x,y)

        building_demography_grid(
            loadBuildings,
            [x, y, x+file_size_m, y+file_size_m],
            out_folder,
            "eurobudem_" + str(grid_resolution) + "m_" + str(x) + "_" + str(y),
            cell_id_fun = lambda x,y: "CRS3035RES"+str(grid_resolution)+"mN"+str(int(y))+"E"+str(int(x)),
            grid_resolution = grid_resolution,
            partition_size = 100000,
            num_processors_to_use = 8
        ) 
