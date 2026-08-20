// Initialize Map (Downtown Phoenix)
const map = L.map('map').setView([33.4484, -112.0740], 14);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20
}).addTo(map);

// State variables
let startMarker = null;
let endMarker = null;
let routeLayers = [];

// DOM Elements
const startInput = document.getElementById('start-input');
const endInput = document.getElementById('end-input');
const findBtn = document.getElementById('find-routes-btn');
const clearBtn = document.getElementById('clear-btn');
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

// Map Click Handler
map.on('click', function(e) {
    if (!startMarker) {
        startMarker = L.marker(e.latlng, {icon: startIcon}).addTo(map);
        startInput.value = `${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`;
    } else if (!endMarker) {
        endMarker = L.marker(e.latlng, {icon: endIcon}).addTo(map);
        endInput.value = `${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`;
        findBtn.disabled = false;
    }
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
});

const clearRoutes = () => {
    routeLayers.forEach(layer => map.removeLayer(layer));
    routeLayers = [];
};

// Fetch Routes
findBtn.addEventListener('click', async () => {
    if (!startMarker || !endMarker) return;
    
    findBtn.disabled = true;
    findBtn.textContent = 'Calculating...';
    clearRoutes();
    
    const payload = {
        start_lat: startMarker.getLatLng().lat,
        start_lon: startMarker.getLatLng().lng,
        end_lat: endMarker.getLatLng().lat,
        end_lon: endMarker.getLatLng().lng
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
        // Render order matters (widest bottom, thinnest top)
        renderRoute(data.fastest, '#e74c3c', 8);
        renderRoute(data.balanced, '#f39c12', 5);
        renderRoute(data.coolest, '#3498db', 2);
        
        // Update Metrics
        updateMetrics('fastest', data.fastest.features[0].properties);
        updateMetrics('balanced', data.balanced.features[0].properties);
        updateMetrics('coolest', data.coolest.features[0].properties);
        
        metricsContainer.style.display = 'block';
        
    } catch (error) {
        console.error(error);
        alert('Error calculating routes. Make sure the backend server is running and the points are within Downtown Phoenix.');
    } finally {
        findBtn.disabled = false;
        findBtn.textContent = 'Find Routes';
    }
});

const renderRoute = (geojsonData, color, weight) => {
    const layer = L.geoJSON(geojsonData, {
        style: {
            color: color,
            weight: weight,
            opacity: 0.9
        }
    }).addTo(map);
    routeLayers.push(layer);
};

const updateMetrics = (idPrefix, props) => {
    // Format seconds to minutes:seconds
    const mins = Math.floor(props.total_time_seconds / 60);
    const secs = Math.floor(props.total_time_seconds % 60);
    
    document.getElementById(`${idPrefix}-time`).textContent = `${mins}m ${secs}s`;
    
    // Format heat
    document.getElementById(`${idPrefix}-heat`).textContent = props.total_heat_exposure.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1});
};
