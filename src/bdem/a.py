import geopandas as gpd
from math import ceil,isnan
from building_demography import building_demography_grid

#minx = 3800000; maxx = 4200000; miny = 2700000; maxy = 3000000
minx = 3900000; maxx = 3950000; miny = 2800000; maxy = 2850000

buildings_loader = lambda bbox: gpd.read_file('/home/juju/geodata/FR/BDTOPO_3-3_TOUSTHEMES_GPKG_LAMB93_R44_2023-12-15/BDT_3-3_GPKG_3035_R44-ED2023-12-15.gpkg', layer='batiment', bbox=bbox)
nb_floors_fun = lambda f: 1 if f.hauteur==None or isnan(f.hauteur) else ceil(f.hauteur/3.7)
residential_fun = lambda f: 1 if f.usage_1=="Résidentiel" else 0.3 if f.usage_2=="Résidentiel" else 0.1 if f.usage_1=="Indifférencié" else 0
cultural_value_fun = lambda f: 1 if f.usage_1=="Religieux" or f.nature=="Tour, donjon" or f.nature=="Monument" or f.nature=="Moulin à vent" or f.nature=="Arc de triomphe" or f.nature=="Fort, blockhaus, casemate" or f.nature=="Eglise" or f.nature=="Château" or f.nature=="Chapelle" or f.nature=="Arène ou théâtre antique" else 0

building_demography_grid(
    buildings_loader,
    [minx, miny, maxx, maxy],
    '/home/juju/gisco/building_demography/',
    "bu_dem_fr_bdtopo_grid",
    resolution=1000,
    partition_size = 50000,
    nb_floors_fun=nb_floors_fun,
    residential_fun=residential_fun,
    cultural_value_fun=cultural_value_fun,
    num_processors_to_use = 8
)
