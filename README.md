# ☀️ The Shady Side

> **Navigation where heat is part of the terrain.**

![The Shady Side Dashboard Screenshot](placeholder_for_screenshot.png)

---

## 🚨 The Problem: Shortest Isn't Safest
Traditional navigation apps like Google Maps or Waze calculate routes based entirely on distance and traffic. But in rapidly warming urban environments (like Phoenix, Arizona, where pavement temperatures can exceed 160°F), the "shortest" route can sometimes be the most dangerous. Pedestrians need a way to navigate cities safely during peak heat waves, optimizing for thermal comfort and shade rather than just time.

## 💡 The Solution
**The Shady Side** is a time-dependent, multi-objective graph routing engine powered by **FortyGuard's** hyper-local temperature API. 

We transform extreme urban heat from an invisible threat into a navigable geographic layer. By dynamically weighting street network edges with real-time, high-resolution thermal data, our algorithm mathematically discovers the absolute coolest path to your destination—balancing travel time against critical heat exposure.

---

## ✨ Key Features

- **🧊 Coolest vs. Fastest Routing**: Dynamically calculates three divergent paths (Fastest, Coolest, Balanced) using modified Dijkstra's algorithms that penalize high-temperature street segments.
- **📈 Interactive Heat Profiles**: Features a comparative Chart.js line graph that visualizes the step-by-step thermal exposure profile of your journey.
- **🤖 Agentic AI Insights**: A built-in "Route Explainer" automatically analyzes the trade-offs between routes (e.g., *"Insight: By taking the Coolest route, you spend an extra 2.4 minutes, but reduce your overall thermal exposure by 12.3%."*).
- **⏱️ Diurnal Time Machine**: Need to leave at 3:00 PM vs. 8:00 AM? Our engine applies a time-dependent diurnal multiplier to the routing graph, allowing you to instantly scrub through the day and watch how the optimal path physically shifts as the city heats up and cools down.
- **🌳 Urban Planner Mode**: An interactive sandbox that lets city planners drop simulated 150m "Cool Zones" (like planting trees or installing shade structures) onto the map, instantly recalculating routes to prove the ROI of green infrastructure investments.

---

## 🏗️ How it Works (Technical Architecture)

Our stack is built for spatial accuracy and high-performance graph traversal:

1. **Mapping Engine (OSMnx & NetworkX)**: We pull down the walkable pedestrian network of Downtown Phoenix. Using `NetworkX`, we run multi-objective shortest path calculations where `edge_weight = time_cost * (adjusted_temperature ** 2)`.
2. **Spatial Data Fusion (GeoPandas)**: We utilize `GeoPandas` to perform advanced spatial joins, securely mapping the FortyGuard heatmap polygons directly onto the street network edges.
3. **Data Polling Daemon (Python)**: A resilient, asynchronous background script securely polls the FortyGuard API, retries on network failures, and triggers the spatial fusion pipeline upon downloading new thermal data.
4. **Backend Server (FastAPI)**: Serves our routing and heatmap endpoints with sub-second latency, handling the Pydantic payloads from the frontend.
5. **Interactive Frontend (Leaflet & Vanilla JS)**: A lightweight, responsive dashboard featuring custom map panes, strict UI state machines, Chart.js integrations, and seamless loading overlays.

---

## 🚀 Local Setup Instructions (For Judges)

Want to run The Shady Side engine on your own machine? Follow these steps:

### 1. Prerequisites
Ensure you have **Python 3.9+** and **Git** installed on your machine.

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/The-Shady-Side.git
cd The-Shady-Side
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Note: Key libraries include `fastapi`, `uvicorn`, `osmnx`, `networkx`, `geopandas`, and `python-dotenv`)*

### 4. Configure Your Environment
You will need your own FortyGuard API key. Create a `.env` file in the root directory and add your key:
```env
FORTYGUARD_API_KEY=your_fortyguard_api_key_here
```

### 5. Start the Backend Server
Boot up the FastAPI server using Uvicorn:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```
*(The API will now be listening on `http://localhost:8000`)*

### 6. Launch the Frontend
Simply open `frontend/index.html` in your favorite modern web browser (e.g., Chrome, Edge, Safari). No frontend build step required!

---

*Built with ❤️ for the FortyGuard Hackathon.*
