import os
import geopandas as gpd
import osmnx as ox
import networkx as nx
from shapely.geometry import LineString

import numpy as np

def calculate_routes(start_lon, start_lat, end_lon, end_lat):
    """
    Directly accept coordinates to prevent (lat, lon) mixups.
    """
    # Load the original graph to extract node geometries
    G_orig = ox.load_graphml("data/processed/phoenix_walk.graphml")
    gdf_nodes, _ = ox.convert.graph_to_gdfs(G_orig)
    
    # Load enriched edges
    gdf_edges = gpd.read_file("data/processed/enriched_edges.geojson")
    
    # Ensure index columns are properly typed for NetworkX
    gdf_edges['u'] = gdf_edges['u'].astype('int64')
    gdf_edges['v'] = gdf_edges['v'].astype('int64')
    gdf_edges['key'] = gdf_edges['key'].astype('int64')

    # Convert any list/array columns to string to avoid OSMnx array ambiguity errors
    for col in gdf_edges.columns:
        if gdf_edges[col].apply(lambda x: isinstance(x, (list, np.ndarray, dict))).any():
            gdf_edges[col] = gdf_edges[col].astype(str)
    
    # Ensure numeric columns are floats
    gdf_edges['length'] = gdf_edges['length'].astype(float)
    gdf_edges['temperature_c'] = gdf_edges['temperature_c'].astype(float)
    
    top_temps = sorted(gdf_edges['temperature_c'].dropna().unique(), reverse=True)[:5]
    print(f"Top 5 distinct temperatures in graph: {top_temps}")
    
    # Calculate costs
    # time_cost: length (meters) / 1.4 (average walking speed in m/s)
    gdf_edges['time_cost'] = gdf_edges['length'] / 1.4
    
    # heat_cost: time_cost * (temperature_c ** 2)
    gdf_edges['heat_cost'] = gdf_edges['time_cost'] * (gdf_edges['temperature_c'] ** 2)
    
    # balanced_cost: combination of time and heat
    gdf_edges['balanced_cost'] = (gdf_edges['time_cost'] * 0.5) + (gdf_edges['heat_cost'] * 0.5)
    
    # Set the multi-index required by osmnx
    gdf_edges.set_index(['u', 'v', 'key'], inplace=True)
    
    # Rebuild graph from nodes and enriched edges
    G = ox.convert.graph_from_gdfs(gdf_nodes, gdf_edges)
    
    # Find nearest nodes to start and end coordinates (X=lon, Y=lat)
    orig_node = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
    dest_node = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)
    
    # Find shortest paths
    path_time = nx.shortest_path(G, orig_node, dest_node, weight='time_cost')
    path_heat = nx.shortest_path(G, orig_node, dest_node, weight='heat_cost')
    path_balanced = nx.shortest_path(G, orig_node, dest_node, weight='balanced_cost')
    
    def get_route_info(path):
        geom = []
        total_time = 0
        total_heat_exposure = 0
        temperature_profile = []
        
        for u, v in zip(path[:-1], path[1:]):
            edge_data = G.get_edge_data(u, v)
            # Find the edge key with the minimum length
            k = min(edge_data, key=lambda key: edge_data[key].get('length', 0))
            data = edge_data[k]
            
            # Extract geometry
            if 'geometry' in data:
                geom.append(data['geometry'])
            else:
                node_u = G.nodes[u]
                node_v = G.nodes[v]
                geom.append(LineString([(node_u['x'], node_u['y']), (node_v['x'], node_v['y'])]))
                
            total_time += data['time_cost']
            
            # Get temperature, defaulting to 35.0 if missing or nan
            temp = data.get('temperature_c', 35.0)
            if np.isnan(temp):
                temp = 35.0
                
            temperature_profile.append(round(temp, 1))
            
            # Accumulate heat exposure over time
            total_heat_exposure += temp * data['time_cost']
            
        return geom, total_time, total_heat_exposure, temperature_profile

    geom_time, time_t, time_h, time_prof = get_route_info(path_time)
    geom_heat, heat_t, heat_h, heat_prof = get_route_info(path_heat)
    geom_bal, bal_t, bal_h, bal_prof = get_route_info(path_balanced)
    
    results = {
        "time_route": {
            "geometry": geom_time,
            "total_time_seconds": time_t,
            "total_heat_exposure": time_h,
            "temperature_profile": time_prof
        },
        "heat_route": {
            "geometry": geom_heat,
            "total_time_seconds": heat_t,
            "total_heat_exposure": heat_h,
            "temperature_profile": heat_prof
        },
        "balanced_route": {
            "geometry": geom_bal,
            "total_time_seconds": bal_t,
            "total_heat_exposure": bal_h,
            "temperature_profile": bal_prof
        }
    }
    return results

if __name__ == "__main__":
    # Simple test execution
    # Bounding box center approximately 33.4475, -112.070
    start = (33.445, -112.075)
    end = (33.450, -112.065)
    
    print(f"Calculating routes from {start} to {end}...")
    routes = calculate_routes(start[1], start[0], end[1], end[0])
    
    for route_name, data in routes.items():
        print(f"\n{route_name}:")
        print(f"  Total Time: {data['total_time_seconds']:.2f} seconds")
        print(f"  Total Heat Exposure: {data['total_heat_exposure']:.2f} units")
        print(f"  Segments: {len(data['geometry'])}")
