import fiona
from shapely.geometry import shape



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

def keepOnlyGeometry(feature):
    for attribute in list(feature.keys()):
        if attribute != 'geometry': feature.pop(attribute)
