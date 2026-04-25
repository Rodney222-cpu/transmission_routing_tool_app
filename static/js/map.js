/**
 * Map initialization and management for Transmission Line Routing Tool
 * Uses Leaflet.js for Uganda map visualization with Uganda-only data
 * NO basemaps - blank white space with Uganda districts layer only
 */

// Global map instance
let map;
let startMarker = null;
let endMarker = null;
let routeLayer = null;
let corridorLayer = null;
let towerMarkers = [];
let waypointMarkers = {}; // Store waypoint markers by ID
let ugandaDistrictsLayer = null; // Uganda districts base layer

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
 * Initialize the map with BLANK WHITE SPACE (no basemaps)
 * Uganda districts layer will be added as the base reference
 */
function initMap() {
    // Uganda bounds: approximately [0.5, 29.5] to [4.5, 35.0]
    const ugandaBounds = [[0.5, 29.5], [4.5, 35.0]];
    
    // Create map with NO basemap - blank white space
    map = L.map('map', {
        center: [1.3733, 32.2903],
        zoom: 8,
        minZoom: 7,
        maxZoom: 18,
        maxBounds: ugandaBounds,
        maxBoundsViscosity: 1.0  // Hard restrict to Uganda bounds
    });
    
    // NO BASEMAPS - blank white space only
    // Uganda districts will be loaded as the reference layer
    
    // Load Uganda districts as base reference layer
    loadUgandaDistrictsLayer();
    // loadUgandaBasemap();
    
    // Fit map to Uganda bounds
    map.fitBounds(ugandaBounds);
    
    // NO OLD LAYER CONTROL - Using new checkbox-based layer manager
    // All layers are controlled via checkboxes in dashboard.html
    
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
 * Uganda boundary overlay removed per user request
 * Map now shows only QGIS basemaps without boundary overlay
 */
function loadUgandaBasemap() {
    // No boundary overlay - user requested removal
    console.log('✓ Uganda boundary overlay disabled (user request)');
}

/**
 * Load Uganda Districts layer as the base reference map
 * Uses shapefile: data/uganda_districts/uganda_districts_2019_i.shp
 * This loads IMMEDIATELY when map initializes with ALL 136 districts
 */
function loadUgandaDistrictsLayer() {
    console.log('🗺️ Loading Uganda Districts as basemap (ALL 136 districts)...');
    
    ugandaDistrictsLayer = L.layerGroup();
    
    // Use UGANDA BOUNDS, not current map view, to load ALL districts
    const ugandaBounds = { min_lon: 29.5, min_lat: 0.5, max_lon: 35.0, max_lat: 4.5 };
    
    // Directly load the shapefile via API with full Uganda bounds
    loadGISLayerWithBounds('uganda_districts', ugandaDistrictsLayer, {
        color: '#666666',
        fillColor: '#E8E8E8',
        fillOpacity: 0.4,
        weight: 1.5
    }, 'District', ugandaBounds);
    
    // Add to map immediately
    ugandaDistrictsLayer.addTo(map);
    console.log('✅ Uganda Districts layer added to map');
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
        console.log(`🔄 Loading layer: ${layerName}`);
        
        // Show loading message
        const loadMsg = `⏳ Loading ${layerName}... please wait`;
        console.log(loadMsg);
        
        // Get current map bounds
        const bounds = map.getBounds();
        const min_lon = bounds.getWest();
        const min_lat = bounds.getSouth();
        const max_lon = bounds.getEast();
        const max_lat = bounds.getNorth();

        console.log(`📍 Map bounds: ${min_lon}, ${min_lat} to ${max_lon}, ${max_lat}`);

        // Fetch GeoJSON from API - ALL features, no limit
        const url = `/api/gis/layers/${layerName}?min_lon=${min_lon}&min_lat=${min_lat}&max_lon=${max_lon}&max_lat=${max_lat}`;
        console.log(`🌐 Fetching: ${url}`);
        
        const startTime = Date.now();
        const response = await fetch(url);
        const loadTime = ((Date.now() - startTime) / 1000).toFixed(2);

        if (!response.ok) {
            console.error(`❌ Failed to load ${layerName} layer: HTTP ${response.status}`);
            const errorText = await response.text();
            console.error('Error response:', errorText);
            return;
        }

        const geojson = await response.json();
        console.log(`📦 Received GeoJSON for ${layerName} in ${loadTime}s`);

        if (!geojson || !geojson.features || geojson.features.length === 0) {
            console.warn(`⚠️ No ${layerName} data available (0 features)`);
            return;
        }

        const featureCount = geojson.features.length;
        console.log(`✓ Loading ALL ${featureCount} features for ${layerName}`);

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
                const name = feature.properties.name || feature.properties.DName2019 || feature.properties.DName2016 || feature.properties.type || popupPrefix;
                layer.bindPopup(`<b>${popupPrefix}</b><br>${name}`);
                
                // Add click handler for QGIS attribute table
                layer.on('click', function(e) {
                    if (typeof showAttributeTable === 'function') {
                        showAttributeTable(feature, layer);
                    }
                });
            }
        });

        leafletLayer.addLayer(geoJsonLayer);
        console.log(`✅ Successfully added ${layerName} to map (${loadTime}s, ${featureCount} features)`);
        
        // Fit map to layer bounds if it's the districts layer
        if (layerName === 'uganda_districts') {
            map.fitBounds(geoJsonLayer.getBounds());
            console.log('🎯 Map fitted to Uganda districts bounds');
        }

    } catch (error) {
        console.error(`❌ Error loading ${layerName} layer:`, error);
    }
}

/**
 * Load GIS layer from API with custom bounds (for loading full datasets)
 */
async function loadGISLayerWithBounds(layerName, leafletLayer, style, popupPrefix, customBounds) {
    try {
        console.log(`🔄 Loading layer with custom bounds: ${layerName}`);
        
        // Use custom bounds instead of map bounds
        const min_lon = customBounds.min_lon;
        const min_lat = customBounds.min_lat;
        const max_lon = customBounds.max_lon;
        const max_lat = customBounds.max_lat;

        console.log(`📍 Custom bounds: ${min_lon}, ${min_lat} to ${max_lon}, ${max_lat}`);

        // Fetch GeoJSON from API
        const url = `/api/gis/layers/${layerName}?min_lon=${min_lon}&min_lat=${min_lat}&max_lon=${max_lon}&max_lat=${max_lat}`;
        console.log(`🌐 Fetching: ${url}`);
        
        const response = await fetch(url);

        if (!response.ok) {
            console.error(`❌ Failed to load ${layerName} layer: HTTP ${response.status}`);
            const errorText = await response.text();
            console.error('Error response:', errorText);
            return;
        }

        const geojson = await response.json();
        console.log(`📦 Received GeoJSON for ${layerName}:`, geojson);

        if (!geojson || !geojson.features || geojson.features.length === 0) {
            console.warn(`⚠️ No ${layerName} data available (0 features)`);
            return;
        }

        console.log(`✓ Loading ${geojson.features.length} features for ${layerName}`);

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
                const name = feature.properties.name || feature.properties.DName2019 || feature.properties.DName2016 || feature.properties.type || popupPrefix;
                layer.bindPopup(`<b>${popupPrefix}</b><br>${name}`);
                
                // Add click handler for QGIS attribute table
                layer.on('click', function(e) {
                    if (typeof showAttributeTable === 'function') {
                        showAttributeTable(feature, layer);
                    }
                });
            }
        });

        leafletLayer.addLayer(geoJsonLayer);
        console.log(`✅ Successfully added ${layerName} to map`);
        
        // Fit map to layer bounds if it's the districts layer
        if (layerName === 'uganda_districts') {
            map.fitBounds(geoJsonLayer.getBounds());
            console.log('🎯 Map fitted to Uganda districts bounds');
        }

    } catch (error) {
        console.error(`❌ Error loading ${layerName} layer:`, error);
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

    updateStartCoords(lat, lng);
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

    updateEndCoords(lat, lng);
}

/**
 * Set waypoint location — updates the shared `waypoints` array (declared in
 * optimize.js), drops a draggable violet marker on the map, and refreshes
 * the sidebar list so coordinates appear instead of "Not set".
 */
function setWaypointLocation(waypointId, lat, lng) {
    if (typeof waypoints === 'undefined') {
        console.warn('waypoints array not available');
        return;
    }
    const wp = waypoints.find(w => w.id === waypointId);
    if (!wp) {
        console.warn(`Waypoint ${waypointId} not found`);
        return;
    }
    wp.lat = lat;
    wp.lon = lng;

    // Replace any existing marker for this waypoint id
    removeWaypointMarker(waypointId);

    const violetIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    const marker = L.marker([lat, lng], { icon: violetIcon, draggable: true })
        .addTo(map)
        .bindPopup(`<b>${wp.name}</b><br>Lat: ${lat.toFixed(4)}, Lon: ${lng.toFixed(4)}`)
        .openPopup();

    marker.on('dragend', function(e) {
        const pos = e.target.getLatLng();
        const target = waypoints.find(w => w.id === waypointId);
        if (target) {
            target.lat = pos.lat;
            target.lon = pos.lng;
            marker.setPopupContent(`<b>${target.name}</b><br>Lat: ${pos.lat.toFixed(4)}, Lon: ${pos.lng.toFixed(4)}`);
        }
        if (typeof renderWaypoints === 'function') renderWaypoints();
    });

    waypointMarkers[waypointId] = marker;

    if (typeof renderWaypoints === 'function') renderWaypoints();
}

/**
 * Remove a waypoint marker from the map (called by removeWaypoint in optimize.js)
 */
function removeWaypointMarker(waypointId) {
    const existing = waypointMarkers[waypointId];
    if (existing) {
        map.removeLayer(existing);
        delete waypointMarkers[waypointId];
    }
}

/**
 * Update start coordinates display
 */
function updateStartCoords(lat, lon) {
    const el = document.getElementById('startCoords');
    if (el) el.textContent = `Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}`;
    
    // Also update coordinate input fields
    const startLatInput = document.getElementById('startLat');
    const startLonInput = document.getElementById('startLon');
    if (startLatInput) startLatInput.value = lat.toFixed(6);
    if (startLonInput) startLonInput.value = lon.toFixed(6);
    
    currentProject.start = { lat, lon, name: 'Start Point' };
    updatePointLabels();
}

/**
 * Update end coordinates display
 */
function updateEndCoords(lat, lon) {
    const el = document.getElementById('endCoords');
    if (el) el.textContent = `Lat: ${lat.toFixed(4)}, Lon: ${lon.toFixed(4)}`;
    
    // Also update coordinate input fields
    const endLatInput = document.getElementById('endLat');
    const endLonInput = document.getElementById('endLon');
    if (endLatInput) endLatInput.value = lat.toFixed(6);
    if (endLonInput) endLonInput.value = lon.toFixed(6);
    
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
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    
    // Initialize QGIS tools after map is ready
    setTimeout(function() {
        if (typeof initQGISTools === 'function') {
            initQGISTools();
        }
    }, 500);
});
