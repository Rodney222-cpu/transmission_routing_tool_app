/**
 * QGIS-inspired Tools for Transmission Line Routing Tool
 * Adds professional GIS functionality while maintaining existing UI
 */

// Global variables for QGIS tools
let measureControl = null;
let profileControl = null;
let bufferControl = null;
let activeTool = null;
let measurementLayers = L.layerGroup().addTo(map);
let bufferLayers = L.layerGroup().addTo(map);

/**
 * Initialize QGIS-style toolbar and tools
 */
function initQGISTools() {
    // Add mouse move event for coordinate display
    map.on('mousemove', updateCoordinateDisplay);
    map.on('zoomend', updateScaleDisplay);
    
    // Initialize toolbar buttons
    setupToolbarButtons();
    
    // Initialize layer panel
    setupLayerPanel();
    
    console.log('✓ QGIS tools initialized');
}

/**
 * Update coordinate display as mouse moves
 */
function updateCoordinateDisplay(e) {
    const coordDisplay = document.getElementById('mouseCoords');
    if (coordDisplay) {
        coordDisplay.textContent = `Lat: ${e.latlng.lat.toFixed(6)}, Lon: ${e.latlng.lng.toFixed(6)}`;
    }
}

/**
 * Update scale display when zoom changes
 */
function updateScaleDisplay() {
    const scaleDisplay = document.getElementById('mapScale');
    if (scaleDisplay) {
        const zoom = map.getZoom();
        // Approximate scale calculation
        const scale = Math.round(591657550.5 / Math.pow(2, zoom));
        scaleDisplay.textContent = `1:${scale.toLocaleString()}`;
    }
}

/**
 * Setup toolbar button event listeners
 */
function setupToolbarButtons() {
    // Navigation tools
    document.getElementById('panTool')?.addEventListener('click', activatePanTool);
    document.getElementById('zoomInTool')?.addEventListener('click', () => map.zoomIn());
    document.getElementById('zoomOutTool')?.addEventListener('click', () => map.zoomOut());
    document.getElementById('zoomToLayerBtn')?.addEventListener('click', zoomToAllLayers);
    
    // Measurement tools
    document.getElementById('measureDistance')?.addEventListener('click', activateMeasureDistance);
    document.getElementById('measureArea')?.addEventListener('click', activateMeasureArea);
    
    // Analysis tools
    document.getElementById('profileTool')?.addEventListener('click', activateProfileTool);
    document.getElementById('bufferTool')?.addEventListener('click', activateBufferTool);
    
    // Export tools
    document.getElementById('printMap')?.addEventListener('click', printMap);
    document.getElementById('exportMapImage')?.addEventListener('click', exportMapAsImage);
    
    // Layer panel toggle
    document.getElementById('toggleLayerPanel')?.addEventListener('click', toggleLayerPanel);
    
    // Layer panel toggle
    document.getElementById('showUgandaBoundary')?.addEventListener('change', toggleUgandaBoundary);
    
    // Close buttons for panels
    document.getElementById('closeLayerPanel')?.addEventListener('click', () => {
        document.querySelector('.layer-panel').style.display = 'none';
    });
    
    document.getElementById('closeAttributePanel')?.addEventListener('click', () => {
        document.querySelector('.attribute-panel').style.display = 'none';
    });
}

/**
 * Activate pan tool
 */
function activatePanTool() {
    setActiveTool('pan');
    document.body.style.cursor = 'grab';
    highlightActiveButton('panTool');
}

/**
 * Activate distance measurement
 */
function activateMeasureDistance() {
    setActiveTool('measureDistance');
    document.body.style.cursor = 'crosshair';
    highlightActiveButton('measureDistance');
    startMeasurement('distance');
}

/**
 * Activate area measurement
 */
function activateMeasureArea() {
    setActiveTool('measureArea');
    document.body.style.cursor = 'crosshair';
    highlightActiveButton('measureArea');
    startMeasurement('area');
}

/**
 * Activate profile tool
 */
function activateProfileTool() {
    setActiveTool('profile');
    document.body.style.cursor = 'crosshair';
    highlightActiveButton('profileTool');
    alert('Click two points on the map to create an elevation profile line');
    startProfileMeasurement();
}

/**
 * Activate buffer tool
 */
function activateBufferTool() {
    setActiveTool('buffer');
    document.body.style.cursor = 'crosshair';
    highlightActiveButton('bufferTool');
    alert('Click on a feature to create a buffer around it');
    startBufferAnalysis();
}

/**
 * Set active tool and reset others
 */
function setActiveTool(tool) {
    activeTool = tool;
    // Reset cursor for all tools
    document.body.style.cursor = 'default';
}

/**
 * Highlight the active button
 */
function highlightActiveButton(buttonId) {
    // Remove highlight from all buttons
    document.querySelectorAll('.qgis-btn').forEach(btn => {
        btn.style.background = '#f0f0f0';
        btn.style.borderColor = '#ccc';
    });
    
    // Highlight active button
    const activeBtn = document.getElementById(buttonId);
    if (activeBtn) {
        activeBtn.style.background = '#4CAF50';
        activeBtn.style.borderColor = '#4CAF50';
        activeBtn.style.color = 'white';
    }
}

/**
 * Start measurement tool (distance or area)
 */
function startMeasurement(type) {
    let points = [];
    let tempLine = null;
    let markers = [];
    
    map.on('click', measureClick);
    
    function measureClick(e) {
        points.push(e.latlng);
        
        // Add marker
        const marker = L.circleMarker(e.latlng, {
            radius: 4,
            color: '#FF0000',
            fillColor: '#FF0000',
            fillOpacity: 1
        }).addTo(measurementLayers);
        markers.push(marker);
        
        if (points.length === 2) {
            if (type === 'distance') {
                // Draw line and show distance
                tempLine = L.polyline(points, {
                    color: '#FF0000',
                    weight: 3,
                    dashArray: '5, 10'
                }).addTo(measurementLayers);
                
                const distance = map.distance(points[0], points[1]);
                const distText = distance > 1000 ? 
                    `${(distance/1000).toFixed(2)} km` : 
                    `${distance.toFixed(2)} m`;
                
                L.popup()
                    .setLatLng(e.latlng)
                    .setContent(`Distance: ${distText}`)
                    .openOn(map);
                
                // Stop measurement after showing result
                map.off('click', measureClick);
                setActiveTool(null);
                document.body.style.cursor = 'default';
            }
        } else if (points.length >= 3 && type === 'area') {
            // Continue adding points for area
            if (tempLine) {
                measurementLayers.removeLayer(tempLine);
            }
            tempLine = L.polygon(points, {
                color: '#FF0000',
                weight: 2,
                fillOpacity: 0.2
            }).addTo(measurementLayers);
        }
    }
    
    // Double click to finish area measurement
    if (type === 'area') {
        map.on('dblclick', finishAreaMeasurement);
    }
    
    function finishAreaMeasurement(e) {
        L.DomEvent.stopPropagation(e);
        
        if (points.length >= 3) {
            // Calculate area (simplified)
            const area = calculateArea(points);
            const areaText = area > 1000000 ? 
                `${(area/1000000).toFixed(2)} km²` : 
                `${area.toFixed(2)} m²`;
            
            L.popup()
                .setLatLng(e.latlng)
                .setContent(`Area: ${areaText}`)
                .openOn(map);
        }
        
        map.off('click', measureClick);
        map.off('dblclick', finishAreaMeasurement);
        setActiveTool(null);
        document.body.style.cursor = 'default';
    }
}

/**
 * Calculate area from points (simplified algorithm)
 */
function calculateArea(points) {
    if (points.length < 3) return 0;
    
    let area = 0;
    const n = points.length;
    
    for (let i = 0; i < n; i++) {
        const j = (i + 1) % n;
        area += points[i].lng * points[j].lat;
        area -= points[j].lng * points[i].lat;
    }
    
    area = Math.abs(area) / 2;
    
    // Convert to square meters (approximate)
    const centerLat = points.reduce((sum, p) => sum + p.lat, 0) / n;
    const metersPerDegree = 111320 * Math.cos(centerLat * Math.PI / 180);
    area *= metersPerDegree * metersPerDegree;
    
    return area;
}

/**
 * Start profile measurement
 */
function startProfileMeasurement() {
    let points = [];
    let tempLine = null;
    
    map.on('click', profileClick);
    
    function profileClick(e) {
        points.push(e.latlng);
        
        // Add marker
        L.circleMarker(e.latlng, {
            radius: 4,
            color: '#0000FF',
            fillColor: '#0000FF',
            fillOpacity: 1
        }).addTo(measurementLayers);
        
        if (points.length === 2) {
            // Draw profile line
            tempLine = L.polyline(points, {
                color: '#0000FF',
                weight: 3
            }).addTo(measurementLayers);
            
            // Show profile information
            const distance = map.distance(points[0], points[1]);
            alert(`Profile line created: ${(distance/1000).toFixed(2)} km\n\nIn a full implementation, this would show an elevation profile chart.`);
            
            map.off('click', profileClick);
            setActiveTool(null);
            document.body.style.cursor = 'default';
        }
    }
}

/**
 * Start buffer analysis
 */
function startBufferAnalysis() {
    map.on('click', bufferClick);
    
    function bufferClick(e) {
        const radius = prompt('Enter buffer radius in meters:', '1000');
        if (!radius) return;
        
        const bufferRadius = parseFloat(radius);
        if (isNaN(bufferRadius) || bufferRadius <= 0) {
            alert('Please enter a valid number');
            return;
        }
        
        // Create buffer circle
        const circle = L.circle(e.latlng, {
            radius: bufferRadius,
            color: '#0000FF',
            fillColor: '#0000FF',
            fillOpacity: 0.2
        }).addTo(bufferLayers);
        
        circle.bindPopup(`Buffer: ${bufferRadius}m radius`);
        
        map.off('click', bufferClick);
        setActiveTool(null);
        document.body.style.cursor = 'default';
    }
}

/**
 * Zoom to all active layers
 */
function zoomToAllLayers() {
    const allLayers = [];
    
    // Get all layers from the map
    map.eachLayer(function(layer) {
        if (layer instanceof L.GeoJSON || layer instanceof L.Polygon || layer instanceof L.CircleMarker) {
            allLayers.push(layer);
        }
    });
    
    if (allLayers.length > 0) {
        const group = L.featureGroup(allLayers);
        map.fitBounds(group.getBounds().pad(0.1));
    } else {
        alert('No active layers to zoom to');
    }
}

/**
 * Print map functionality
 */
function printMap() {
    window.print();
}

/**
 * Export map as image
 */
function exportMapAsImage() {
    alert('Map export functionality would require a library like html2canvas.\n\nIn a full implementation, this would capture the map as an image.');
}

/**
 * Toggle layer panel visibility
 */
function toggleLayerPanel() {
    const panel = document.querySelector('.layer-panel');
    if (panel) {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * Toggle Uganda boundary visibility
 */
function toggleUgandaBoundary() {
    const checkbox = document.getElementById('showUgandaBoundary');
    if (ugandaBoundaryLayer) {
        if (checkbox.checked) {
            map.addLayer(ugandaBoundaryLayer);
        } else {
            map.removeLayer(ugandaBoundaryLayer);
        }
    }
}

/**
 * Setup layer panel
 */
function setupLayerPanel() {
    // Populate the layer tree with all available layers
    populateLayerTree();
}

/**
 * Populate layer tree with available GIS layers
 */
function populateLayerTree() {
    const layerTree = document.getElementById('layerTree');
    if (!layerTree) return;
    
    // Define all available layers (matching the overlayLayers in map.js)
    const layers = [
        { id: 'elevation', name: '🏔️ Elevation (Contours)', icon: '🏔️' },
        { id: 'schools', name: '🏫 Schools', icon: '🏫' },
        { id: 'roads', name: '🛣️ Roads (UNRA 2012)', icon: '🛣️' },
        { id: 'rivers', name: '🌊 Rivers', icon: '🌊' },
        { id: 'wetlands', name: '🌊 Wetlands (1994)', icon: '🌊' },
        { id: 'lakes', name: '🌊 Lakes', icon: '🌊' },
        { id: 'protected_areas', name: '🦁 Protected Areas', icon: '🦁' },
        { id: 'health_facilities', name: '🏥 Health Facilities', icon: '🏥' },
        { id: 'commercial', name: '🏢 Commercial Facilities', icon: '🏢' },
        { id: 'trading_centres', name: '🏘️ Trading Centres', icon: '🏘️' }
    ];
    
    let html = '';
    layers.forEach(layer => {
        html += `
            <div class="layer-tree-item">
                <input type="checkbox" id="layer_${layer.id}" data-layer="${layer.id}">
                <label for="layer_${layer.id}">${layer.name}</label>
            </div>
        `;
    });
    
    layerTree.innerHTML = html;
    
    // Add event listeners to layer checkboxes
    document.querySelectorAll('.layer-tree-item input').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const layerId = this.dataset.layer;
            // Use the main toggleLayer function from layer_manager.js
            if (typeof toggleLayer === 'function') {
                toggleLayer(layerId, this.checked);
            } else {
                console.warn('toggleLayer function not found - layer_manager.js may not be loaded');
            }
        });
    });
}

/**
 * Toggle layer visibility (deprecated - use layer_manager.js instead)
 * This function is kept for backward compatibility but does nothing
 * as the actual layer toggling is handled by layer_manager.js
 */
function toggleLayerQGIS(layerId, visible) {
    // This function is deprecated - layer_manager.js handles all layer toggling
    console.log(`[DEPRECATED] Layer ${layerId} ${visible ? 'enabled' : 'disabled'} - use toggleLayer() from layer_manager.js`);
}

/**
 * Show attribute table for a feature
 */
function showAttributeTable(feature, layer) {
    const panel = document.querySelector('.attribute-panel');
    const content = document.getElementById('attributeTableContent');
    
    if (feature && feature.properties) {
        let html = '<table class="attribute-table">';
        html += '<thead><tr><th>Property</th><th>Value</th></tr></thead>';
        html += '<tbody>';
        
        for (const [key, value] of Object.entries(feature.properties)) {
            // Format the key name for better readability
            const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            html += `<tr><td>${formattedKey}</td><td>${value !== null && value !== undefined ? value : 'N/A'}</td></tr>`;
        }
        
        html += '</tbody></table>';
        content.innerHTML = html;
    } else {
        content.innerHTML = '<p style="padding: 10px; color: #666;">No feature selected. Click on a map feature to view its attributes.</p>';
    }
    
    panel.style.display = 'block';
}

/**
 * Add click handler to all GIS layers to show attribute table
 */
function enableFeatureSelection() {
    // This function would be called after layers are loaded
    // It adds click event listeners to all GIS features
    
    map.eachLayer(function(layer) {
        if (layer instanceof L.GeoJSON) {
            layer.on('click', function(e) {
                showAttributeTable(e.sourceFeature, layer);
            });
        }
    });
}

// Initialize QGIS tools when map is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait for map to be initialized
    setTimeout(initQGIS, 1000);
});

function initQGIS() {
    if (typeof map !== 'undefined') {
        initQGISTools();
    }
}
