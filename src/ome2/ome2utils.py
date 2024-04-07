

def ome2_filter_road_links(gdf):
    #gdf = gdf[gdf['road_surface_category'] != 'unpaved']
    #gdf = gdf[gdf['road_surface_category'] != 'paved#unpaved']
    #gdf = gdf[gdf['road_surface_category'] != 'unpaved#paved']
    gdf = gdf[gdf['form_of_way'] != 'tractor_road']
    gdf = gdf[gdf['form_of_way'] != 'tractor_road#single_carriage_way']
    gdf = gdf[gdf['form_of_way'] != 'single_carriage_way#tractor_road']
    gdf = gdf[gdf['access_restriction'] != 'physically_impossible']
    gdf = gdf[gdf['access_restriction'] != 'private']
    gdf = gdf[gdf['access_restriction'] != 'void_restricted#private']
    gdf = gdf[gdf['access_restriction'] != 'void_restricted']
    #gdf = gdf[gdf['access_restriction'] != 'void_restricted#public_access']
    gdf = gdf[gdf['condition_of_facility'] != 'disused']
    gdf = gdf[gdf['condition_of_facility'] != 'under_construction']
    return gdf


def road_link_speed_kmh(f):
    rsc = f["road_surface_category"]
    fow = f["form_of_way"]
    frc = f["functional_road_class"]
    speed_kmh = 30
    if(rsc != 'paved'): speed_kmh = 20
    elif(fow == 'motorway'): speed_kmh = 120
    elif(fow == 'dual_carriage_way'): speed_kmh = 100
    elif(fow == 'slip_road'): speed_kmh = 80
    #elif(fow == 'single_carriage_way'): speed_kmh = 80
    elif(frc == 'main_road'): speed_kmh = 80
    elif(frc == 'first_class'): speed_kmh = 80
    elif(frc == 'second_class'): speed_kmh = 70
    elif(frc == 'third_class'): speed_kmh = 50
    elif(frc == 'fourth_class'): speed_kmh = 40
    elif(frc == 'fifth_class'): speed_kmh = 30
    elif(frc == 'void_unk'): speed_kmh = 30
    else: print(rsc,fow,frc)
    return speed_kmh



def ome2_duration(f):
    return 1
