import os
import osmnx as ox

def main():
    output_path = "data/processed/phoenix_walk.graphml"
    
    print("Downloading pedestrian street network around (33.45, -112.08) within 3000m...")
    # Use graph_from_point for a larger, consistent bounding area
    graph = ox.graph_from_point((33.45, -112.08), dist=3000, network_type="walk")
    
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Saving graph to {output_path}...")
    ox.save_graphml(graph, filepath=output_path)
    print("Map data fetch complete!")

if __name__ == "__main__":
    main()
