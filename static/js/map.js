/**
 * Map initialization and management for Transmission Line Routing Tool
 * Uses Leaflet.js for Uganda map visualization with Uganda-only data
 * NO OpenStreetMap or world map data - only Uganda shapefiles
 */

// Global map instance
let map;
let startMarker = null;
let endMarker = null;
let routeLayer = null;
let corridorLayer = null;
let towerMarkers = [];
let waypointMarkers = {}; // Store waypoint markers by ID
let ugandaBoundaryLayer = null; // Uganda boundary from ug.json

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
 * Initialize the map with Uganda-only basemap from ug.json
 */
function initMap() {
    // Uganda bounds: approximately [0.5, 29.5] to [4.5, 35.0]
    const ugandaBounds = [[0.5, 29.5], [4.5, 35.0]];
    
    // Create map centered on Uganda with restricted view
    map = L.map('map', {
        center: [1.3733, 32.2903],
        zoom: 8,
        minZoom: 7,
        maxZoom: 18,
        maxBounds: ugandaBounds,
        maxBoundsViscosity: 1.0  // Hard restrict to Uganda bounds
    });
    
    // Load Uganda boundary from ug.json as the basemap
    loadUgandaBasemap();
    
    // Fit map to Uganda bounds
    map.fitBounds(ugandaBounds);
    
    // GIS overlay layers from YOUR SHAPEFILES only (NO OpenStreetMap data)
    const overlayLayers = {
        "🏔️ Elevation (Contours)": createDEMLayer(),
        "🏫 Schools": createSchoolsLayer(),
        "🛣️ Roads (UNRA 2012)": createRoadsLayer(),
        "🌊 Rivers": createRiversLayer(),
        "🌊 Wetlands (1994)": createWetlandsLayer(),
        "🌊 Lakes": createLakesLayer(),
        "🦁 Protected Areas": createProtectedAreasLayer(),
        "🏥 Health Facilities": createHealthFacilitiesLayer(),
        "🏢 Commercial Facilities": createCommercialLayer(),
        "🏘️ Trading Centres": createTradingCentresLayer()
    };

    // Layer control - overlays only, Uganda base is always visible
    L.control.layers(null, overlayLayers, {collapsed: true, position: 'topright'}).addTo(map);
    
    // Add scale
    L.control.scale({ imperial: false, metric: true }).addTo(map);
    
    // No preset markers - user sets start, way and end points via sidebar buttons
    updatePointLabels();

    // Add legend (defined in layers.js) after map exists
    if (typeof window !== 'undefined' && typeof window.addLegend === 'function') {
        window.addLegend();
    }

    // Map click handler for point selection
    map.on('click', function(e) {
        if (selectionMode) {
            const lat = e.latlng.lat;
            const lng = e.latlng.lng;
            
            // Check if click is within Uganda bounds
            if (lat < 0.5 || lat > 4.5 || lng < 29.5 || lng > 35.0) {
                alert('Please select a point within Uganda');
                return;
            }
            
            if (selectionMode === 'start') {
                setStartPoint(lat, lng);
            } else if (selectionMode === 'end') {
                setEndPoint(lat, lng);
            } else if (selectionMode === 'waypoint' && currentWaypointId) {
                setWaypointLocation(currentWaypointId, lat, lng);
            }
            
            // Reset selection mode
            selectionMode = null;
            currentWaypointId = null;
            document.body.style.cursor = 'default';
        }
    });
}

/**
 * Load Uganda boundary from ug.json as the basemap
 */
async function loadUgandaBasemap() {
    try {
        // Load ug.json (Uganda boundary)
        const response = await fetch('/data/uganda_boundary.json');
        if (!response.ok) {
            console.warn('Could not load uganda_boundary.json, using fallback');
            addUgandaFallbackBoundary();
            return;
        }
        
        const ugandaGeoJSON = await response.json();
        
        // Add Uganda boundary as filled polygon (the basemap)
        ugandaBoundaryLayer = L.geoJSON(ugandaGeoJSON, {
            style: {
                color: '#228B22',        // Forest green border
                weight: 2,
                opacity: 1.0,
                fillColor: '#90EE90',    // Light green fill
                fillOpacity: 0.3         // Semi-transparent
            }
        }).addTo(map);
        
        // Add country label
        L.marker([1.3733, 32.2903], {
            icon: L.divIcon({
                className: 'uganda-label',
                html: '<div style="font-size: 28px; font-weight: bold; color: #006400; text-shadow: 2px 2px 4px white;">🇺🇬 UGANDA</div>',
                iconSize: [200, 50],
                iconAnchor: [100, 25]
            })
        }).addTo(map);
        
        console.log('✓ Uganda basemap loaded from ug.json');
        
    } catch (error) {
        console.error('Error loading Uganda basemap:', error);
        addUgandaFallbackBoundary();
    }
}

/**
 * Fallback Uganda boundary if ug.json fails to load
 */
function addUgandaFallbackBoundary() {
    // Simplified Uganda border coordinates
    const ugandaBorder = [
        [4.5, 30.0], [4.5, 30.5], [4.2, 31.0], [3.8, 32.0], [3.5, 33.0],
        [2.5, 34.0], [1.5, 34.5], [0.5, 34.0], [0.5, 33.5], [0.8, 32.5],
        [1.0, 31.5], [1.5, 30.5], [2.5, 30.0], [3.5, 29.8], [4.5, 30.0]
    ];
    
    ugandaBoundaryLayer = L.polygon(ugandaBorder, {
        color: '#228B22',
        weight: 2,
        opacity: 1.0,
        fillColor: '#90EE90',
        fillOpacity: 0.3
    }).addTo(map);
    
    L.marker([1.3733, 32.2903], {
        icon: L.divIcon({
            className: 'uganda-label',
            html: '<div style="font-size: 28px; font-weight: bold; color: #006400; text-shadow: 2px 2px 4px white;">🇺🇬 UGANDA</div>',
            iconSize: [200, 50],
            iconAnchor: [100, 25]
        })
    }).addTo(map);
}

/**
 * Create layer for Rivers
 */
function createRiversLayer() {
    const layer = L.layerGroup();
    layer.on('add', function() {
        loadGISLayer('rivers', layer, {
            color: '#0066CC',
            weight: 2,
            opacity: 0.8
        }, 'River');
    });
    return layer;
}

/**
 * Create layer for Wetlands
 */
function createWetlandsLayer() {
    const layer = L.layerGroup();
    layer.on('add', function() {
        loadGISLayer('wetlands', layer, {
            color: '#4A90E2',
            fillColor: '#87CEEB',
            fillOpacity: 0.5,
            weight: 1
        }, 'Wetland');
    });
    return layer;
}

/**
 * Create layer for Lakes
 */
function createLakesLayer() {
    const layer = L.layerGroup();
    layer.on('add', function() {
        loadGISLayer('lakes', layer, {
            color: '#0000CD',
            fillColor: '#87CEEB',
            fillOpacity: 0.6,
            weight: 2
        }, 'Lake');
    });
    return layer;
}

/**
 * Create layer for Hospitals
 */
function createHospitalsLayer() {
    const layer = L.layerGroup();
    layer.on('add', function() {
        loadGISLayer('hospitals', layer, {
            radius: 6,
            fillColor: '#FF0000',
            color: '#8B0000',
            weight: 1,
            fillOpacity: 0.8
        }, 'Hospital');
    });
    return layer;
}

/**
 * Create layer for Commercial Areas
 */
function createCommercialLayer() {
    const layer = L.layerGroup();
    layer.on('add', function() {
        loadGISLayer('commercial', layer, {
            color: '#FF8C00',
            fillColor: '#FFD700',
            fillOpacity: 0.4,
            weight: 2
        }, 'Commercial Area');
    });
    return layer;
}

// ... rest of existing functions (createDEMLayer, createSettlementsLayer, etc.) ...
// These will be added in subsequent edits

/**
 * Create layer for DEM/Elevation
 */
function createDEMLayer() {
    const layer = L.layerGroup();
    layer.on('add', function() {
        loadGISLayer('dem', layer, {
            color: '#8B4513',
            fillOpacity: 0.3,
            weight: 1
        }, 'Elevation');
    });
    return layer;
}

/**
 * Create layer for Settlements (Schools)
 */
function createSettlementsLayer() {
    const layer = L.layerGroup();
    layer.on('add', function() {
        loadGISLayer('settlements', layer, {
            radius: 5,
            fillColor: '#FF6347',
            color: '#8B0000',
            weight: 1,
            fillOpacity: 0.7
        }, 'School');
    });
    return layer;
}

/**
 * Create layer for Roads
 */
function createRoadsLayer() {
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

/**
 * Create layer for Water Bodies (legacy - now split into rivers, wetlands, lakes)
 */
function createWaterBodiesLayer() {
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

/**
 * Create layer for Forests/Vegetation
 */
function createForestsLayer() {
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

/**
 * Create layer for Land Use
 */
function createLandUseLayer() {
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

/**
 * Create layer for Protected Areas
 */
function createProtectedAreasLayer() {
    const layer = L.layerGroup();
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

/**
 * Create layer for Power Infrastructure
 */
function createPowerInfraLayer() {
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
 * Create layer for Schools (from Ug_Schools shapefile)
 */
function createSchoolsLayer() {
    const layer = L.layerGroup();
    layer.on('add', function() {
        loadGISLayer('schools', layer, {
            radius: 5,
            fillColor: '#4169E1',
            color: '#000080',
            weight: 1,
            fillOpacity: 0.8
        }, 'School');
    });
    return layer;
}

/**
 * Create layer for Health Facilities (from health_facilities shapefile)
 */
function createHealthFacilitiesLayer() {
    const layer = L.layerGroup();
    layer.on('add', function() {
        loadGISLayer('health_facilities', layer, {
            radius: 6,
            fillColor: '#FF0000',
            color: '#8B0000',
            weight: 1,
            fillOpacity: 0.8
        }, 'Health Facility');
    });
    return layer;
}

/**
 * Create layer for Trading Centres (from Ug_Trading_Centres shapefile)
 */
function createTradingCentresLayer() {
    const layer = L.layerGroup();
    layer.on('add', function() {
        loadGISLayer('trading_centres', layer, {
            radius: 4,
            fillColor: '#FF8C00',
            color: '#8B4500',
            weight: 1,
            fillOpacity: 0.7
        }, 'Trading Centre');
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
            return;
        }

        // Add GeoJSON to layer with styling
        const geoJsonLayer = L.geoJSON(geojson, {
            style: style,
            pointToLayer: function(feature, latlng) {
                if (style.radius) {
                    return L.circleMarker(latlng, style);
                }
                return L.marker(latlng);
            },
            onEachFeature: function(feature, layer) {
                const name = feature.properties.name || feature.properties.type || popupPrefix;
                layer.bindPopup(`<b>${popupPrefix}</b><br>${name}`);
            }
        });

        leafletLayer.addLayer(geoJsonLayer);

    } catch (error) {
        console.error(`Error loading ${layerName} layer:`, error);
    }
}

/**
 * Set start point
 */
function setStartPoint(lat, lng) {
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

    startMarker = L.marker([lat, lng], { icon: greenIcon, draggable: true })
        .addTo(map)
        .bindPopup('<b>Start Point</b><br>Lat: ' + lat.toFixed(4) + ', Lon: ' + lng.toFixed(4))
        .openPopup();

    startMarker.on('dragend', function(e) {
        const pos = e.target.getLatLng();
        updateStartCoords(pos.lat, pos.lng);
    });

    currentProject.start = { lat, lon: lng, name: 'Start Point' };
    updatePointLabels();
}

/**
 * Set end point
 */
function setEndPoint(lat, lng) {
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

    endMarker = L.marker([lat, lng], { icon: redIcon, draggable: true })
        .addTo(map)
        .bindPopup('<b>End Point</b><br>Lat: ' + lat.toFixed(4) + ', Lon: ' + lng.toFixed(4))
        .openPopup();

    endMarker.on('dragend', function(e) {
        const pos = e.target.getLatLng();
        updateEndCoords(pos.lat, pos.lng);
    });

    currentProject.end = { lat, lon: lng, name: 'End Point' };
    updatePointLabels();
}

/**
 * Set waypoint location
 */
function setWaypointLocation(waypointId, lat, lng) {
    // Implementation depends on your waypoint system
    console.log(`Waypoint ${waypointId} set to:`, lat, lng);
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
        if (elevation !== null) {
            popupContent += `<br>Elevation: ${elevation.toFixed(1)}m`;
        }
        marker.bindPopup(popupContent);

        towerMarkers.push(marker);
    });
}

/**
 * Display corridor on map
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
