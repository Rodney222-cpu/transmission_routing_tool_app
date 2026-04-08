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
    // Default basemap is added by static/js/layers.js (Standard OSM) so style matches sidebar toggles
    
    // Add satellite imagery option
    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles © Esri',
        maxZoom: 18
    });
    
    // GIS overlay layers (NOT added by default - user must select)
    const overlayLayers = {
        "DEM / Topography": createDEMLayer(),
        "Protected Areas": createProtectedAreasLayer(),
        "Settlements": createSettlementsLayer(),
        "Land Use": createLandUseLayer(),
        "Roads": createRoadsLayer(),
        "Water Bodies": createWaterBodiesLayer(),
        "Forests": createForestsLayer(),
        "Power Infrastructure": createPowerInfraLayer()
    };

    // Layer control with base maps and overlays
    const baseMaps = {
        "Street Map": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'),
        "Satellite": satellite
    };

    L.control.layers(baseMaps, overlayLayers, {collapsed: false}).addTo(map);
    
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
        // pos can be [lon, lat] or [lon, lat, elevation]
        const lon = pos[0];
        const lat = pos[1];
        const elevation = pos.length > 2 ? pos[2] : null;

        const marker = L.circleMarker([lat, lon], {
            radius: 5,
            fillColor: '#0066CC',
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);

        let popupContent = `<b>Tower ${index + 1}</b><br>Lat: ${lat.toFixed(4)}<br>Lon: ${lon.toFixed(4)}`;
        if (elevation !== null && elevation !== undefined && !Number.isNaN(elevation)) {
            popupContent += `<br>Elevation: ${Number(elevation).toFixed(1)} m`;
        }

        marker.bindPopup(popupContent);
        towerMarkers.push(marker);
    });
}

/**
 * Create GIS layer overlays (not added by default - user selectable)
 * These load real data from Uganda GIS sources via API
 */
function createDEMLayer() {
    // DEM visualization - shows elevation info
    const demLayer = L.layerGroup();
    const infoText = L.marker([3.4833, 32.3417], {
        icon: L.divIcon({
            className: 'layer-info',
            html: '<div style="background: rgba(255,255,255,0.9); padding: 5px; border-radius: 3px; font-size: 11px;">DEM/Topography (SRTM 30m)</div>',
            iconSize: [200, 30]
        })
    });
    demLayer.addLayer(infoText);

    // Note: DEM is raster data, typically shown as hillshade or contours
    // For now, showing info marker. Full DEM visualization requires tile server.

    return demLayer;
}

function createProtectedAreasLayer() {
    // Load real protected areas from Uganda GIS data
    const layer = L.layerGroup();

    // Load data when layer is added to map
    layer.on('add', function() {
        loadGISLayer('protected_areas', layer, {
            color: '#228B22',
            fillColor: '#90EE90',
            fillOpacity: 0.3,
            weight: 2
        }, 'Protected Area');
    });

    return layer;
}

function createSettlementsLayer() {
    // Load real settlements from Uganda GIS data
    const layer = L.layerGroup();

    layer.on('add', function() {
        loadGISLayer('settlements', layer, {
            radius: 5,
            fillColor: '#FF6347',
            color: '#8B0000',
            weight: 1,
            fillOpacity: 0.7
        }, 'Settlement');
    });

    return layer;
}

function createLandUseLayer() {
    // Load real land use data from Uganda GIS
    const layer = L.layerGroup();

    layer.on('add', function() {
        loadGISLayer('land_use', layer, {
            color: '#8B4513',
            fillColor: '#DEB887',
            fillOpacity: 0.2,
            weight: 1
        }, 'Land Use');
    });

    return layer;
}

function createRoadsLayer() {
    // Load real roads from Uganda GIS (OpenStreetMap)
    const layer = L.layerGroup();

    layer.on('add', function() {
        loadGISLayer('roads', layer, {
            color: '#696969',
            weight: 3,
            opacity: 0.7
        }, 'Road');
    });

    return layer;
}

function createWaterBodiesLayer() {
    // Load real water bodies from Uganda GIS
    const layer = L.layerGroup();

    layer.on('add', function() {
        loadGISLayer('water', layer, {
            color: '#0000CD',
            fillColor: '#87CEEB',
            fillOpacity: 0.5,
            weight: 2
        }, 'Water Body');
    });

    return layer;
}

function createForestsLayer() {
    // Load real forest data from Uganda GIS
    const layer = L.layerGroup();

    layer.on('add', function() {
        loadGISLayer('forests', layer, {
            color: '#006400',
            fillColor: '#228B22',
            fillOpacity: 0.4,
            weight: 2
        }, 'Forest');
    });

    return layer;
}

function createPowerInfraLayer() {
    // Load real power infrastructure from Uganda GIS
    const layer = L.layerGroup();

    layer.on('add', function() {
        loadGISLayer('power', layer, {
            color: '#FF0000',
            weight: 2,
            dashArray: '5, 5',
            opacity: 0.7
        }, 'Power Infrastructure');
    });

    return layer;
}

/**
 * Load GIS layer from API and add to map
 */
async function loadGISLayer(layerName, leafletLayer, style, popupPrefix) {
    try {
        // Get current map bounds
        const bounds = map.getBounds();
        const min_lon = bounds.getWest();
        const min_lat = bounds.getSouth();
        const max_lon = bounds.getEast();
        const max_lat = bounds.getNorth();

        // Fetch GeoJSON from API
        const response = await fetch(
            `/api/gis/layers/${layerName}?min_lon=${min_lon}&min_lat=${min_lat}&max_lon=${max_lon}&max_lat=${max_lat}`
        );

        if (!response.ok) {
            console.warn(`Failed to load ${layerName} layer`);
            return;
        }

        const geojson = await response.json();

        if (!geojson || !geojson.features || geojson.features.length === 0) {
            console.log(`No ${layerName} data available for this area`);
            // Add info marker
            const center = map.getCenter();
            const infoMarker = L.marker([center.lat, center.lng], {
                icon: L.divIcon({
                    className: 'layer-info',
                    html: `<div style="background: rgba(255,255,255,0.9); padding: 5px; border-radius: 3px; font-size: 11px;">No ${layerName} data available. Add data to data/${layerName}/ folder.</div>`,
                    iconSize: [250, 40]
                })
            });
            leafletLayer.addLayer(infoMarker);
            return;
        }

        // Add GeoJSON to layer
        const geoJsonLayer = L.geoJSON(geojson, {
            style: function(feature) {
                return style;
            },
            pointToLayer: function(feature, latlng) {
                if (style.radius) {
                    // Circle marker for points
                    return L.circleMarker(latlng, style);
                } else {
                    // Regular marker
                    return L.marker(latlng);
                }
            },
            onEachFeature: function(feature, layer) {
                // Add popup with properties
                const props = feature.properties || {};
                let popupContent = `<b>${popupPrefix}</b><br>`;

                // Add relevant properties
                if (props.name) popupContent += `Name: ${props.name}<br>`;
                if (props.place) popupContent += `Type: ${props.place}<br>`;
                if (props.highway) popupContent += `Road Type: ${props.highway}<br>`;
                if (props.landuse) popupContent += `Land Use: ${props.landuse}<br>`;
                if (props.natural) popupContent += `Natural: ${props.natural}<br>`;
                if (props.power) popupContent += `Power: ${props.power}<br>`;
                if (props.amenity) popupContent += `Amenity: ${props.amenity}<br>`;

                layer.bindPopup(popupContent);
            }
        });

        leafletLayer.addLayer(geoJsonLayer);
        console.log(`Loaded ${geojson.features.length} features for ${layerName}`);

    } catch (error) {
        console.error(`Error loading ${layerName} layer:`, error);
    }
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

