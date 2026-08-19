import os
import osmnx as ox
from shapely.geometry import Polygon

def main():
    output_path = "data/processed/phoenix_walk.graphml"
    
    # Custom polygon defining Downtown Phoenix, Arizona to match FortyGuard AOI
    # Bounding box approximately: min_lon=-112.08, min_lat=33.44, max_lon=-112.06, max_lat=33.455
    poly = Polygon([
        [-112.080, 33.440],
        [-112.060, 33.440],
        [-112.060, 33.455],
        [-112.080, 33.455],
        [-112.080, 33.440]
    ])
    
    print("Downloading pedestrian street network for Downtown Phoenix bounding box polygon...")
    graph = ox.graph_from_polygon(poly, network_type="walk")
    
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Saving graph to {output_path}...")
    ox.save_graphml(graph, filepath=output_path)
    print("Map data fetch complete!")

if __name__ == "__main__":
    main()
