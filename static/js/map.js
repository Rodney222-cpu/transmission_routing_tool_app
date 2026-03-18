/**
 * Map initialization and management for Transmission Line Routing Tool
 * Uses Leaflet.js for Uganda map visualization
 */

// Global map instance
let map;
let startMarker = null;
let endMarker = null;
let routeLayer = null;
let corridorLayer = null;
let towerMarkers = [];
let waypointMarkers = {}; // Store waypoint markers by ID

// No preset points - user must set start, way and end points
// Current project state (start/end set by user via map)
let currentProject = {
    start: null,
    end: null,
    route: null,
    projectId: null
};

// Point selection mode
let selectionMode = null; // 'start', 'end', or 'waypoint'
let currentWaypointId = null; // ID of waypoint being placed

/**
 * Initialize the map
 */
function initMap() {
    // Create map centered on Uganda (between Olwiyo and border)
    map = L.map('map').setView([3.4833, 32.3417], 10);
    
    // Add OpenStreetMap base layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
    
    // Add satellite imagery option
    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles © Esri',
        maxZoom: 18
    });
    
    // Layer control
    const baseMaps = {
        "Street Map": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'),
        "Satellite": satellite
    };
    
    L.control.layers(baseMaps).addTo(map);
    
    // Add scale
    L.control.scale({ imperial: false, metric: true }).addTo(map);
    
    // No preset markers - user sets start, way and end points via sidebar buttons
    updatePointLabels();

    // Add legend (defined in layers.js) after map exists
    if (typeof window !== 'undefined' && typeof window.addLegend === 'function') {
        window.addLegend();
    } else if (typeof addLegend === 'function') {
        addLegend();
    }
    
    // Add click handler for point selection
    map.on('click', onMapClick);
    
    console.log('Map initialized');
}

/**
 * Add start point marker
 */
function addStartMarker(lat, lon) {
    if (startMarker) {
        map.removeLayer(startMarker);
    }
    
    const greenIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
    
    startMarker = L.marker([lat, lon], { icon: greenIcon, draggable: true })
        .addTo(map)
        .bindPopup('<b>Start Point</b><br>Lat: ' + lat.toFixed(4) + ', Lon: ' + lon.toFixed(4))
        .openPopup();
    
    startMarker.on('dragend', function(e) {
        const pos = e.target.getLatLng();
        updateStartCoords(pos.lat, pos.lng);
    });
    
    currentProject.start = { lat, lon, name: 'Start Point' };
    updatePointLabels();
}

/**
 * Add end point marker
 */
function addEndMarker(lat, lon) {
    if (endMarker) {
        map.removeLayer(endMarker);
    }
    
    const redIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
    
    endMarker = L.marker([lat, lon], { icon: redIcon, draggable: true })
        .addTo(map)
        .bindPopup('<b>End Point</b><br>Lat: ' + lat.toFixed(4) + ', Lon: ' + lon.toFixed(4))
        .openPopup();
    
    endMarker.on('dragend', function(e) {
        const pos = e.target.getLatLng();
        updateEndCoords(pos.lat, pos.lng);
    });
    
    currentProject.end = { lat, lon, name: 'End Point' };
    updatePointLabels();
}

/**
 * Handle map clicks for point selection
 */
function onMapClick(e) {
    if (selectionMode === 'start') {
        addStartMarker(e.latlng.lat, e.latlng.lng);
        updateStartCoords(e.latlng.lat, e.latlng.lng);
        selectionMode = null;
        document.getElementById('setStartBtn').classList.remove('active');
    } else if (selectionMode === 'end') {
        addEndMarker(e.latlng.lat, e.latlng.lng);
        updateEndCoords(e.latlng.lat, e.latlng.lng);
        selectionMode = null;
        document.getElementById('setEndBtn').classList.remove('active');
    } else if (selectionMode === 'waypoint' && currentWaypointId) {
        addWaypointMarker(currentWaypointId, e.latlng.lat, e.latlng.lng);
        updateWaypointCoords(currentWaypointId, e.latlng.lat, e.latlng.lng);
        selectionMode = null;
        currentWaypointId = null;
    }
}

/**
 * Add waypoint marker
 */
function addWaypointMarker(waypointId, lat, lon) {
    // Remove existing marker if any
    if (waypointMarkers[waypointId]) {
        map.removeLayer(waypointMarkers[waypointId]);
    }

    const orangeIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    const waypoint = waypoints.find(w => w.id === waypointId);
    const waypointName = waypoint ? waypoint.name : 'Waypoint';

    waypointMarkers[waypointId] = L.marker([lat, lon], { icon: orangeIcon, draggable: true })
        .addTo(map)
        .bindPopup(`<b>${waypointName}</b><br>Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}`)
        .openPopup();

    // Update on drag
    waypointMarkers[waypointId].on('dragend', function(e) {
        const pos = e.target.getLatLng();
        updateWaypointCoords(waypointId, pos.lat, pos.lng);
    });
}

/**
 * Update waypoint coordinates
 */
function updateWaypointCoords(waypointId, lat, lon) {
    const waypoint = waypoints.find(w => w.id === waypointId);
    if (waypoint) {
        waypoint.lat = lat;
        waypoint.lon = lon;
        renderWaypoints();
    }
}

/**
 * Remove waypoint marker
 */
function removeWaypointMarker(waypointId) {
    if (waypointMarkers[waypointId]) {
        map.removeLayer(waypointMarkers[waypointId]);
        delete waypointMarkers[waypointId];
    }
}

/**
 * Update start coordinates display
 */
function updateStartCoords(lat, lon) {
    const el = document.getElementById('startCoords');
    if (el) el.textContent = `Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}`;
    currentProject.start = { lat, lon, name: 'Start Point' };
    updatePointLabels();
}

/**
 * Update end coordinates display
 */
function updateEndCoords(lat, lon) {
    const el = document.getElementById('endCoords');
    if (el) el.textContent = `Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}`;
    currentProject.end = { lat, lon, name: 'End Point' };
    updatePointLabels();
}

/**
 * Update sidebar labels for start/end when not set
 */
function updatePointLabels() {
    const startEl = document.getElementById('startCoords');
    const endEl = document.getElementById('endCoords');
    if (startEl && !currentProject.start) startEl.textContent = 'Not set — click "Set Start Point" then click map';
    if (endEl && !currentProject.end) endEl.textContent = 'Not set — click "Set End Point" then click map';
}

/**
 * Display optimized route on map
 */
function displayRoute(routeGeoJSON, towerPositions) {
    // Remove existing route
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }
    
    // Add route line
    routeLayer = L.geoJSON(routeGeoJSON, {
        style: {
            color: '#FF6B00',
            weight: 4,
            opacity: 0.8
        }
    }).addTo(map);
    
    // Fit map to route
    map.fitBounds(routeLayer.getBounds(), { padding: [50, 50] });
    
    // Add tower markers if provided
    if (towerPositions && towerPositions.length > 0) {
        displayTowers(towerPositions);
    }
    
    currentProject.route = routeGeoJSON;
}

/**
 * Display tower positions
 */
function displayTowers(towerPositions) {
    // Clear existing towers
    towerMarkers.forEach(marker => map.removeLayer(marker));
    towerMarkers = [];
    
    // Add tower markers
    towerPositions.forEach((pos, index) => {
        const marker = L.circleMarker([pos[1], pos[0]], {
            radius: 5,
            fillColor: '#0066CC',
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);
        
        marker.bindPopup(`<b>Tower ${index + 1}</b><br>Lat: ${pos[1].toFixed(4)}<br>Lon: ${pos[0].toFixed(4)}`);
        towerMarkers.push(marker);
    });
}

/**
 * Display corridor polygon
 */
function displayCorridor(corridorGeoJSON) {
    // Remove existing corridor
    if (corridorLayer) {
        map.removeLayer(corridorLayer);
    }
    
    // Add corridor polygon
    corridorLayer = L.geoJSON(corridorGeoJSON, {
        style: {
            color: '#FFD700',
            weight: 2,
            opacity: 0.6,
            fillOpacity: 0.2
        }
    }).addTo(map);
}

// Initialize map when page loads
document.addEventListener('DOMContentLoaded', initMap);

