import json
import numpy as np
from shapely.geometry import Polygon, mapping

# Bounding box roughly for Downtown Phoenix
min_lon = -112.12
max_lon = -112.04
min_lat = 33.42
max_lat = 33.48

num_cells = 30
lon_step = (max_lon - min_lon) / num_cells
lat_step = (max_lat - min_lat) / num_cells

features = []
for i in range(num_cells):
    for j in range(num_cells):
        poly_min_lon = min_lon + i * lon_step
        poly_max_lon = poly_min_lon + lon_step
        poly_min_lat = min_lat + j * lat_step
        poly_max_lat = poly_min_lat + lat_step
        
        poly = Polygon([
            (poly_min_lon, poly_min_lat),
            (poly_max_lon, poly_min_lat),
            (poly_max_lon, poly_max_lat),
            (poly_min_lon, poly_max_lat),
            (poly_min_lon, poly_min_lat)
        ])
        
        # Spatial correlation: make it hot in the center, cool on the edges, with some randomness
        dist_from_center = np.sqrt(((i - num_cells/2)**2) + ((j - num_cells/2)**2))
        base_temp = 43.0 - (dist_from_center * 0.7)
        temp = base_temp + np.random.uniform(-4, 4)
        temp = max(30.0, min(45.0, temp)) # clamp
        
        feature = {
            "type": "Feature",
            "geometry": mapping(poly),
            "properties": {
                "temperature_c": round(temp, 1)
            }
        }
        features.append(feature)

heat_json = {
    "result": {
        "map_data": {
            "type": "FeatureCollection",
            "features": features
        }
    }
}

with open("data/raw/phoenix_heat.json", "w") as f:
    json.dump(heat_json, f)
print("Grid generated!")
