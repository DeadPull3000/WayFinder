import os
import time
import json
import sys
import requests
from dotenv import load_dotenv

def main():
    print("Loading environment variables...")
    load_dotenv()
    
    api_key = os.getenv("FORTYGUARD_API_KEY")
    if not api_key:
        print("Error: FORTYGUARD_API_KEY not found in .env file.")
        sys.exit(1)

    print("Defining payload...")
    polygon_aoi = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-112.10, 33.43],
                            [-112.06, 33.43],
                            [-112.06, 33.47],
                            [-112.10, 33.47],
                            [-112.10, 33.43]
                        ]
                    ]
                }
            }
        ]
    }

    payload = {
        "polygon_aoi": polygon_aoi,
        "date_time": {
            "start_date": "2024-07-15",
            "start_time": "14:00",
            "filter_type": 1
        },
        "granularity": 80
    }

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }

    print("Submitting task to FortyGuard API...")
    try:
        response = requests.post(
            "https://api.fortyguard.com/v1/heatmap",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        activity_id = data.get("data", {}).get("activity_id")
        
        if not activity_id:
            print("Error: No activity_id returned in the response.")
            print(data)
            return sys.exit(1)
            
        print(f"Task submitted successfully! Activity ID: {activity_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error submitting task: {e}")
        if e.response is not None:
            print(e.response.text)
        return sys.exit(1)

    # Polling loop
    attempt = 1
    while True:
        print(f"Polling (attempt {attempt})...")
        try:
            status_response = requests.get(
                f"https://api.fortyguard.com/v1/status/{activity_id}",
                headers=headers
            )
            status_response.raise_for_status()
            status_data = status_response.json()
            
            # The API documentation and normal behavior usually has a 'status' field.
            status = status_data.get("status")
            
            if status == "succeeded":
                print("Task succeeded! Downloading and saving data...")
                result_data = status_data.get("data", {}).get("result")
                
                if result_data:
                    # Save to data/raw/phoenix_heat.json
                    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw", "phoenix_heat.json")
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    with open(output_path, "w") as f:
                        json.dump({"result": result_data}, f, indent=2)
                        
                    print(f"Data saved successfully to {output_path}!")
                else:
                    print("Error: 'result' data missing in the succeeded response.")
                    print(status_data)
                    sys.exit(1)
                break
            elif status == "failed":
                print("Task failed according to the FortyGuard API.")
                print(status_data)
                sys.exit(1)
            else:
                # Still processing
                time.sleep(30)
                attempt += 1
                
        except requests.exceptions.RequestException as e:
            print(f"Error polling status: {e}")
            if e.response is not None:
                print(e.response.text)
            print("Retrying in 30 seconds due to network error...")
            time.sleep(30)
            attempt += 1

if __name__ == "__main__":
    main()
