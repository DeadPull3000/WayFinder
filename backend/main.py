import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from shapely.geometry import mapping, MultiLineString

# Add current directory to path so we can import routing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from routing import calculate_routes

app = FastAPI(title="Thermal Wayfinder API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float

def format_geojson(route_data, route_name):
    # route_data['geometry'] is a list of shapely LineStrings
    multi_line = MultiLineString(route_data["geometry"])
    
    feature = {
        "type": "Feature",
        "geometry": mapping(multi_line),
        "properties": {
            "name": route_name,
            "total_time_seconds": round(route_data["total_time_seconds"], 2),
            "total_heat_exposure": round(route_data["total_heat_exposure"], 2)
        }
    }
    
    return {
        "type": "FeatureCollection",
        "features": [feature]
    }

@app.post("/api/route")
def get_route(req: RouteRequest):
    # Calculate routes passing explicit longitude and latitude
    routes = calculate_routes(req.start_lon, req.start_lat, req.end_lon, req.end_lat)
    
    # Format and return as GeoJSON
    return {
        "fastest": format_geojson(routes["time_route"], "Fastest Route"),
        "coolest": format_geojson(routes["heat_route"], "Coolest Route"),
        "balanced": format_geojson(routes["balanced_route"], "Balanced Route")
    }

@app.get("/api/heatmap")
def get_heatmap():
    heat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw", "phoenix_heat.json")
    if os.path.exists(heat_path):
        import json
        with open(heat_path, "r") as f:
            heat_data = json.load(f)
            # Extracted FeatureCollection inside result.map_data
            feature_collection = heat_data.get("result", {}).get("map_data", {})
            return feature_collection
    return {"type": "FeatureCollection", "features": []}

# To run: uvicorn main:app --reload --port 8000
