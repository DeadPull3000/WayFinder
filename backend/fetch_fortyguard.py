import os
import time
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def main():
    api_key = os.getenv("FORTYGUARD_API_KEY")
    if not api_key:
        print("Error: FORTYGUARD_API_KEY not found in environment variables.")
        return

    # Define endpoints
    submit_url = "https://api.fortyguard.com/v1/heatmap"
    output_path = "data/raw/phoenix_heat.json"

    # Define headers
    headers = {
        "api-key": api_key,
        "x-api-key": api_key,  # Backup just in case
        "Content-Type": "application/json"
    }

    # Dummy GeoJSON polygon for Downtown Phoenix, Arizona
    # Bounding box approximately: min_lon=-112.08, min_lat=33.44, max_lon=-112.06, max_lat=33.455
    polygon_aoi = {
        "type": "Polygon",
        "coordinates": [
            [
                [-112.080, 33.440],
                [-112.060, 33.440],
                [-112.060, 33.455],
                [-112.080, 33.455],
                [-112.080, 33.440]
            ]
        ]
    }

    payload = {
        "polygon_aoi": polygon_aoi,
        "date_time": {
            "start_date": "2026-08-20",
            "start_time": "12:00",
            "filter_type": 1
        },
        "granularity": 100
    }

    print("Submitting heatmap request to FortyGuard API...")
    try:
        response = requests.post(submit_url, headers=headers, json=payload)
        response.raise_for_status()
        resp_data = response.json()
        
        # Extract activity_id from various possible JSON structures
        activity_id = resp_data.get("activity_id") or resp_data.get("data", {}).get("activity_id")
        if not activity_id:
            print("Error: Could not extract activity_id from the response:")
            print(json.dumps(resp_data, indent=2))
            return
            
        print(f"Request submitted successfully. Activity ID: {activity_id}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to submit request: {e}")
        if 'response' in locals() and response is not None:
            print(f"Response: {response.text}")
        return

    # Poll status endpoint
    status_url = f"https://api.fortyguard.com/v1/status/{activity_id}"
    print("Starting asynchronous polling loop...")
    
    # Ensure raw data folder exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    while True:
        try:
            status_response = requests.get(status_url, headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            # Extract status from various possible JSON structures
            status = status_data.get("status") or status_data.get("data", {}).get("status")
            print(f"Current status: {status}")
            
            if status and status.lower() in ["succeeded", "completed", "success"]:
                print("Task succeeded! Saving resulting data...")
                
                # Check if GeoJSON is nested inside data
                geojson_data = status_data.get("data", status_data)
                
                with open(output_path, "w") as f:
                    json.dump(geojson_data, f, indent=4)
                print(f"Saved GeoJSON to {output_path}")
                break
                
            elif status and status.lower() in ["failed", "error"]:
                print("Task failed on FortyGuard API side. Stopping polling.")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Error checking status: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    main()
