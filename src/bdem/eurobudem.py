from math import ceil,isnan,floor
from building_demography import building_demography_grid
import rasterio

import sys
sys.path.append('/home/juju/workspace/pyEx/src/')
from utils.featureutils import loadFeatures,keepOnlyGeometry
from utils.geomutils import average_z_coordinate

#TODO
# test del my_dict['b'] for input data formating in keepOnlyGeometry
# other countries: IT, NL, BE, SK, CZ, PL... see eubc
# FR date of creation
# other years

bbox = [5250000, 2750000, 5250000, 2750000] #PL small
#bbox = [4250000, 1250000, 5250000, 2750000] #IT
#bbox = [4267541, 2749532, 4267541, 3250000] #LU
#bbox = [3000000, 2000000, 4413621, 3462995] #FR

grid_resolution = 100
file_size_m = 500000
out_folder = '/home/juju/gisco/building_demography/out_partition/'
num_processors_to_use = 6

clamp = lambda v:floor(v/file_size_m)*file_size_m
[xmin,ymin,xmax,ymax] = [clamp(v) for v in bbox]




def loadBuildings(bbox):
    buildings = []

    #PL
    bs = loadFeatures('/home/juju/geodata/PL/bdot10k/bu_bubd_bdot10k.gpkg', bbox)
    for bu in bs: formatBuildingPL(bu)
    buildings += bs

    #FR
    bs = loadFeatures('/home/juju/geodata/FR/BD_TOPO/BATI/batiment_3035.gpkg', bbox)
    for bu in bs: formatBuildingFR(bu)
    buildings += bs

    #LU
    bs = loadFeatures('/home/juju/geodata/LU/ACT/BDLTC_SHP/BATI/BATIMENT_3035.gpkg', bbox)
    for bu in bs: formatBuildingLU(bu)
    buildings += bs

    #IT
    bs = loadFeatures('/home/juju/geodata/IT/DBSN/dbsn.gpkg', bbox)
    for bu in bs: formatBuildingIT(bu)
    buildings += bs

    #TODO remove duplicates

    return buildings


#PL
def formatBuildingPL(bu):

    """"
    budynki przemysłowe
    budynki transportu i łączności
    budynki handlowo-usługowe
    zbiorniki, silosy i budynki magazynowe
    budynki biurowe
    budynki szpitali i inne budynki opieki zdrowotnej
    budynki oświaty, nauki i kultury oraz budynki sportowe
    budynki produkcyjne, usługowe i gospodarcze dla rolnictwa
    pozostałe budynki niemieszkalne
    budynki mieszkalne

    industrial buildings
    transport and communications buildings
    commercial and service buildings
    tanks, silos and storage buildings
    office buildings
    hospital buildings and other health care buildings
    education, science and culture buildings and sports buildings
    production, service and farm buildings for agriculture
    other non-residential buildings
    residential buildings


    funkcja Ogol na Budynku: OT_FunOgol na Budynku [0..1]
    funkcja Szczegol owa Budynku: OT_FunSzczegol owa Budynku [0..*]
    przewa za ja ca Funkcja Budynku: OT_FunSzczegol owa Budynku [0..1]
    l i czba Kondygna cji : Integer [0..1]
        
    function Ogol on Building: OT_FunOgol on Building [0..1]
    Building Detail function: OT_Building Detail Fun [0..*]
    predominant building function: OT_FunBuilding Detail [0..1]
    l and number of Storeys: Integer [0..1]    

    *budynekGospodarstwaRolnego
    budynekZabytkowy M
    budynkiBiurowe
    budynkiGarazy
    budynkiHandlowoUslugowe
    *Agricultural Farm building
    Historic building
    Office buildings
    Garage buildings
    Commercial and Service buildings

    *budynkiHoteli
    budynkiKultuReligijnego M
    budynkiKulturyFizycznej
    budynkiLacznosciDworcowITerminali
    budynkiMieszkalneJednorodzinne
    *Hotel buildings
    Religious Cult buildings M
    Physical Culture buildings
    communication buildings, railway stations and terminals
    Single-family residential buildings R

    *budynkiMuzeowIBibliotek
    budynkiODwochMieszkaniach
    budynkiOTrzechIWiecejMieszkaniach
    budynkiPrzemyslowe
    budynkiSzkolIInstytucjiBadawczych
    *buildings of museums and libraries
    buildings About Two Apartments R
    buildings with three more apartments R
    Industrial buildings
    buildings of schools and research institutions

    *budynkiSzpitaliIZakladowOpiekiMedycznej
    budynkiZakwaterowaniaTurystycznegoPozostale
    budynkiZbiorowegoZamieszkania R
    ogolnodostepneObiektyKulturalne
    pozostaleBudynkiNiemieszkalne
    *buildings of hospitals and medical care facilities
    Tourist Accommodation buildings Other
    Collective Housing buildings R
    publicly accessible Cultural Facilities
    other non-residential buildings

    *zbiornikSilosIBudynkiMagazynowe
    *Silos tank and warehouse buildings

    """

    #floor number
    u = bu["LKOND"]
    if u==None: u = 1
    #monument
    m = bu["ZABYTEK"]

    keepOnlyGeometry(bu)

    #LKOND - KODKST
    bu["floor_nb"] = int(u)

    #FUNOGBUD - main function
    #FUNSZCZ - detailled function
    bu["residential"] = 1
    bu["activity"] = 0
    bu["cultural_value"] = 1 if m=="Tak" else 0



#IT
def formatBuildingIT(bu):
    u = bu["edifc_uso"]
    if u!=None: u = u[:2]

    t = bu["edifc_ty"]
    if t!=None: t = t[:2]

    m = bu["edifc_mon"]
    if m!=None: m = m[:2]

    a = bu["edifc_at"]

    keepOnlyGeometry(bu)

    if a != None and a != -9999 and a!=0 and a!=-29997.0 and a!=-29999.0 : print("Elevation provided for IT building:", a)

    #TODO find information on IT building height
    #bu_top = average_z_coordinate(bu["geometry"])
    #if(bu_top != 0): print("Elevation provided for IT building geometry:", bu_top)
    bu["floor_nb"] = 1

    bu["residential"] = 1 if u=="01" else 0.25 if u=="93" else 0
    bu["activity"] = 1 if u in ["02","03","04","06","07","08","09","10","11","12"] else 0.25 if u=="93" else 0
    bu["cultural_value"] = 1 if u=="05" or m=="01" or t in ["03","06","07","10","11","12","13","15","16","17","18","20","22","24","25"] else 0

#LU
DTM_LU = None
def get_DTM_LU():
    if DTM_LU==None: DTM_LU = rasterio.open("/home/juju/geodata/LU/MNT_lux2017_3035.tif")
    return DTM_LU
def formatBuildingLU(bu):
    n = bu["NATURE"]
    if n==None: n=0
    n = int(n)
    keepOnlyGeometry(bu)

    #estimate building height from geometry 'z' and DTM
    bu_top = average_z_coordinate(bu["geometry"])
    centroid = bu["geometry"].centroid
    row, col = get_DTM_LU().index(centroid.x, centroid.y)
    elevation = get_DTM_LU().read(1, window=((row, row+1), (col, col+1)))[0][0]
    h = bu_top - elevation
    if elevation == -32767 or bu_top > 1000 or bu_top<0 or elevation<0: h=3
    if h>38*3: h=3 #if a building has more than 38 floors, then there is a bug. Set height to one floor only.

    bu["floor_nb"] = 1 if h==None or isnan(h) else max(ceil(h/3), 1)

    bu["residential"] = 1 if n==0 else 0
    bu["activity"] = 1 if (n>=10000 and n<42000) or n==80000 or n==11000 else 0
    bu["cultural_value"] = 1 if n in [41004,41005,41302,41303,41305] or (n>=50000 and n<=50011) else 0

#FR
def formatBuildingFR(bu):
    h = bu["hauteur"]
    u1 = bu["usage_1"]
    u2 = bu["usage_2"]
    n = bu["nature"]

    keepOnlyGeometry(bu)

    floor_nb = 1 if h==None or isnan(h) else ceil(h/3)
    bu["floor_nb"] = floor_nb
    residential = 1 if u1=="Résidentiel" else 0.3 if u2=="Résidentiel" else 0.25 if u1=="Indifférencié" else 0
    bu["residential"] = residential
    activity = 1 if u1=="Agricole" or u1=="Commercial et services" or u1=="Industriel" else 0.3 if u2=="Agricole" or u2=="Commercial et services" or u2=="Industriel" else 0.25 if u1=="Indifférencié" else 0
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
            grid_resolution = grid_resolution,
            partition_size = 100000,
            num_processors_to_use = num_processors_to_use,
            skip_empty_cells = True
        ) 
