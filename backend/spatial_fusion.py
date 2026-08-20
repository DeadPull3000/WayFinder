import os
import json
import geopandas as gpd
import osmnx as ox

def main():
    graph_path = "data/processed/phoenix_walk.graphml"
    heat_path = "data/raw/phoenix_heat.json"
    output_path = "data/processed/enriched_edges.geojson"

    print("Loading graph data...")
    G = ox.load_graphml(graph_path)
    
    # Convert graph edges to a GeoDataFrame
    edges = ox.convert.graph_to_gdfs(G, nodes=False)
    
    # Ensure graph is in EPSG:4326
    if edges.crs is None or edges.crs.to_epsg() != 4326:
        edges = edges.to_crs(epsg=4326)

    print("Loading heat data...")
    with open(heat_path, "r") as f:
        heat_json = json.load(f)
        
    # Extract FeatureCollection from nested JSON
    feature_collection = heat_json.get("result", {}).get("map_data", {})
    if "features" in feature_collection and len(feature_collection["features"]) > 0:
        heat_gdf = gpd.GeoDataFrame.from_features(feature_collection["features"])
    else:
        heat_gdf = gpd.GeoDataFrame()
        
    if not heat_gdf.empty:
        heat_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
    else:
        # Create an empty GeoDataFrame with a geometry column and EPSG:4326
        heat_gdf = gpd.GeoDataFrame(columns=['geometry', 'temperature_c'], geometry='geometry', crs="EPSG:4326")

    print("Performing spatial join...")
    # Make sure we use a left join so all edges are kept
    # predicate="intersects" by default
    enriched_edges = gpd.sjoin(edges, heat_gdf, how="left", predicate="intersects")

    # Handle missing data
    print("Filling missing temperature values...")
    import numpy as np
    if "temperature_c" not in enriched_edges.columns:
        enriched_edges["temperature_c"] = np.nan
        
    missing_mask = enriched_edges["temperature_c"].isna()
    num_missing = missing_mask.sum()
    if num_missing > 0:
        print(f"Injecting high-variance dummy temperatures for {num_missing} edges...")
        enriched_edges.loc[missing_mask, "temperature_c"] = np.random.uniform(30.0, 45.0, size=num_missing)

    # Some edges might intersect multiple polygons, leading to duplicate edges in the sjoin result.
    # To be safe, we drop duplicates by the edge index (u, v, key)
    # The index in edges GDF is usually a MultiIndex (u, v, key).
    enriched_edges = enriched_edges[~enriched_edges.index.duplicated(keep='first')]

    # Ensure parent dir exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Saving enriched edges to {output_path}...")
    # GeoJSON doesn't support MultiIndex (u, v, key), so we should reset index before saving
    enriched_edges_out = enriched_edges.reset_index()
    
    # Convert list/dict columns to string because GeoJSON driver might fail on them
    for col in enriched_edges_out.columns:
        if enriched_edges_out[col].apply(lambda x: isinstance(x, (list, dict))).any():
            enriched_edges_out[col] = enriched_edges_out[col].astype(str)

    enriched_edges_out.to_file(output_path, driver="GeoJSON")
    print("Fusion complete!")

if __name__ == "__main__":
    main()
