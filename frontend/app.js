// Initialize Map (Downtown Phoenix)
const map = L.map('map', { zoomControl: false }).setView([33.4484, -112.0740], 14);
L.control.zoom({ position: 'topright' }).addTo(map);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20
}).addTo(map);

// State variables
let routeLayerGroup = L.layerGroup().addTo(map);
let interventionLayerGroup = L.layerGroup().addTo(map);
let heatChartInstance = null;
let coolingInterventions = [];

function renderHeatChart(fastestProfile, coolestProfile) {
    const ctx = document.getElementById('heatChart').getContext('2d');
    
    // Destroy the old chart if it exists so we don't get overlapping hover glitches
    if (heatChartInstance) {
        heatChartInstance.destroy();
    }

    // Create a generic X-axis label array based on the longest route
    const maxLength = Math.max(fastestProfile.length, coolestProfile.length);
    const labels = Array.from({length: maxLength}, (_, i) => `Step ${i + 1}`);

    heatChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Fastest Route (°C)',
                    data: fastestProfile,
                    borderColor: '#e74c3c', // Red
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0 // Hide dots for a smooth line
                },
                {
                    label: 'Coolest Route (°C)',
                    data: coolestProfile,
                    borderColor: '#3498db', // Blue
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            color: '#111',
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, color: '#111' } }
            },
            scales: {
                y: {
                    title: { display: true, text: 'Temperature (°C)', color: '#111' },
                    ticks: { color: '#111' },
                    grid: { color: 'rgba(0, 0, 0, 0.1)' },
                    suggestedMin: 30, // Adjust based on Phoenix temps
                    suggestedMax: 45
                },
                x: {
                    display: false // Hide x-axis text to keep it clean
                }
            }
        }
    });
}

// DOM Elements
const startInput = document.getElementById('start-input');
const endInput = document.getElementById('end-input');
const findBtn = document.getElementById('find-routes-btn');
const clearBtn = document.getElementById('clear-map-btn');
const metricsContainer = document.getElementById('metrics-container');

// Custom Icons
const createIcon = (color) => {
    return L.divIcon({
        className: 'custom-icon',
        html: `<div style="background-color: ${color}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.4);"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7]
    });
};

const startIcon = createIcon('#27ae60');
const endIcon = createIcon('#c0392b');

function safelyUpdateInput(keyword, latlng) {
    try {
        // Case-insensitive search for the input boxes, covering IDs or placeholders
        let input = document.getElementById(`${keyword}-input`) || 
                    document.getElementById(keyword) || 
                    document.querySelector(`input[placeholder*="${keyword}" i]`);
        
        if (input) {
            input.value = latlng ? `${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}` : '';
        } else {
            console.warn(`The Shady Side Warning: Could not find HTML input for '${keyword}'. Check your HTML IDs.`);
        }
    } catch (err) {
        console.error("Error updating input:", err);
    }
}

let startMarker = null;
let endMarker = null;

function handlePinDrop(latlng) {
    console.log("Map clicked at:", latlng); // Debugging

    const plannerMode = document.getElementById('planner-mode');
    if (plannerMode && plannerMode.checked) {
        coolingInterventions.push({ lat: latlng.lat, lng: latlng.lng });
        L.circle(latlng, { radius: 150, color: '#3498db', fillColor: '#3498db', fillOpacity: 0.4, weight: 2 }).addTo(interventionLayerGroup);
        
        if (startMarker && endMarker) {
            findBtn.click();
        }
        return;
    }

    try {
        map.closeTooltip();
    } catch (e) {}

    // Ensure markers are drawn in the 'markerPane' so they stay ABOVE the heatmap polygons
    let markerOptions = { radius: 8, fillOpacity: 1, pane: 'markerPane', weight: 2, color: 'white' };

    try {
        if (!startMarker) {
            markerOptions.fillColor = 'green';
            startMarker = L.circleMarker(latlng, markerOptions).addTo(map);
            safelyUpdateInput('start', latlng);
        } else if (!endMarker) {
            markerOptions.fillColor = 'red';
            endMarker = L.circleMarker(latlng, markerOptions).addTo(map);
            safelyUpdateInput('end', latlng);
            findBtn.disabled = false; // Add this back so the user can search
        } else {
            // Reset state
            map.removeLayer(startMarker);
            map.removeLayer(endMarker);
            
            // If routes exist on the map, clear them too (ensure your route layer variable matches this)
            if (typeof routeLayerGroup !== 'undefined' && routeLayerGroup) {
                routeLayerGroup.clearLayers();
            }
            metricsContainer.style.display = 'none'; // Add this back
            
            const insightBox = document.getElementById('route-insight-box');
            if (insightBox) {
                insightBox.style.display = 'none';
                insightBox.textContent = '';
            }
            
            if (heatChartInstance) {
                heatChartInstance.destroy();
                heatChartInstance = null;
            }
            
            markerOptions.fillColor = 'green';
            startMarker = L.circleMarker(latlng, markerOptions).addTo(map);
            endMarker = null;
            
            safelyUpdateInput('start', latlng);
            safelyUpdateInput('end', null); // Clear the end input
            findBtn.disabled = true; // Add this back
        }
    } catch (err) {
        console.error("Critical error in handlePinDrop:", err);
    }
}

// Map Click Handler
map.on('click', function(e) {
    handlePinDrop(e.latlng);
});

// Clear Map
clearBtn.addEventListener('click', () => {
    if (startMarker) map.removeLayer(startMarker);
    if (endMarker) map.removeLayer(endMarker);
    startMarker = null;
    endMarker = null;
    startInput.value = '';
    endInput.value = '';
    findBtn.disabled = true;
    metricsContainer.style.display = 'none';
    clearRoutes();
    
    const insightBox = document.getElementById('route-insight-box');
    if (insightBox) {
        insightBox.style.display = 'none';
        insightBox.textContent = '';
    }
    
    if (heatChartInstance) {
        heatChartInstance.destroy();
        heatChartInstance = null;
    }
    
    interventionLayerGroup.clearLayers();
    coolingInterventions = [];
});

const clearRoutes = () => {
    routeLayerGroup.clearLayers();
};

// Fetch Routes
findBtn.addEventListener('click', async () => {
    if (!startMarker || !endMarker) return;
    
    findBtn.disabled = true;
    findBtn.textContent = 'Calculating...';
    document.getElementById('loading-overlay').style.display = 'flex';
    clearRoutes();
    
    const departureTime = document.getElementById('departure-time').value;
    
    const payload = {
        start_lat: startMarker.getLatLng().lat,
        start_lon: startMarker.getLatLng().lng,
        end_lat: endMarker.getLatLng().lat,
        end_lon: endMarker.getLatLng().lng,
        time: departureTime,
        interventions: coolingInterventions
    };
    
    try {
        const response = await fetch('http://localhost:8000/api/route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error('Failed to fetch routes');
        
        const data = await response.json();
        
        // Render Routes
        // Render order matters: Coolest last so it stays on top.
        renderRoute(data.fastest, '#e74c3c', 8, 0.6);
        renderRoute(data.balanced, '#f39c12', 5, 0.8);
        renderRoute(data.coolest, '#3498db', 3, 1.0);
        
        // Update Metrics
        updateMetrics('fastest', data.fastest.features[0].properties);
        updateMetrics('balanced', data.balanced.features[0].properties);
        updateMetrics('coolest', data.coolest.features[0].properties);
        
        const fastestProfile = data.fastest.features[0].properties.temperature_profile;
        const coolestProfile = data.coolest.features[0].properties.temperature_profile;
        if (fastestProfile && coolestProfile) {
            renderHeatChart(fastestProfile, coolestProfile);
        }
        
        metricsContainer.style.display = 'block';
        
        const insightBox = document.getElementById('route-insight-box');
        if (data.insight_text) {
            insightBox.textContent = data.insight_text;
            insightBox.style.display = 'block';
        }
        
    } catch (error) {
        console.error(error);
        alert('Error calculating routes. Make sure the backend server is running and the points are within Downtown Phoenix.');
    } finally {
        document.getElementById('loading-overlay').style.display = 'none';
        findBtn.disabled = false;
        findBtn.textContent = 'Find Routes';
    }
});

const renderRoute = (geojsonData, color, weight, opacity) => {
    const layer = L.geoJSON(geojsonData, {
        style: {
            color: color,
            weight: weight,
            opacity: opacity
        }
    });
    routeLayerGroup.addLayer(layer);
};

const updateMetrics = (idPrefix, props) => {
    // Format seconds to minutes:seconds
    const mins = Math.floor(props.total_time_seconds / 60);
    const secs = Math.floor(props.total_time_seconds % 60);
    
    document.getElementById(`${idPrefix}-time`).textContent = `${mins}m ${secs}s`;
    
    // Format heat
    document.getElementById(`${idPrefix}-heat`).textContent = Math.round(props.total_heat_exposure).toLocaleString();
};

// Fetch and Render Heatmap
const loadHeatmap = async () => {
    try {
        const response = await fetch('http://localhost:8000/api/heatmap');
        if (!response.ok) throw new Error('Failed to fetch heatmap');
        
        const data = await response.json();
        
        const getColor = (temp) => {
            if (temp > 40) return '#8B0000'; // Dark Red
            if (temp >= 35) return '#FFA500'; // Orange
            return '#FFFFE0'; // Light Yellow
        };
        
        // Add heatmap layer behind routes
        const heatmapLayer = L.geoJSON(data, {
            style: (feature) => {
                return {
                    fillColor: getColor(feature.properties.temperature_c),
                    color: getColor(feature.properties.temperature_c),
                    weight: 0,
                    fillOpacity: 0.35
                };
            },
            onEachFeature: function(feature, layer) {
                // Ensure tooltips are strictly hover-only
                if (feature.properties && feature.properties.temperature_c) {
                    layer.bindTooltip(`Temperature: ${feature.properties.temperature_c.toFixed(1)}°C`, {
                        sticky: true,
                        permanent: false, // Prevents them from getting stuck
                        direction: "auto",
                        className: "heat-tooltip"
                    });
                }

                // Forward the click safely
                layer.on('click', function(e) {
                    L.DomEvent.stopPropagation(e); // Stop the event from causing Leaflet visual glitches
                    handlePinDrop(e.latlng);
                });
            }
        });
        
        // Insert heatmap layer behind route layers but above base map
        heatmapLayer.addTo(map);
        heatmapLayer.bringToBack();
        
    } catch (error) {
        console.error('Error loading heatmap:', error);
    }
};

// Load heatmap on startup
loadHeatmap();
