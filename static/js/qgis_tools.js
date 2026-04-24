/**
 * QGIS-inspired Tools for Transmission Line Routing Tool
 * Adds professional GIS functionality while maintaining existing UI
 */

/**
 * Initialize QGIS-style toolbar and tools
 */
function initQGISTools() {
    // Add mouse move event for coordinate display
    map.on('mousemove', updateCoordinateDisplay);
    map.on('zoomend', updateScaleDisplay);

    // Initialize toolbar buttons
    setupToolbarButtons();

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
    // Close button for the feature attribute panel (triggered by feature
    // clicks via showAttributeTable).
    document.getElementById('closeAttributePanel')?.addEventListener('click', () => {
        document.querySelector('.attribute-panel').style.display = 'none';
    });
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

// Initialize QGIS tools once the Leaflet map instance exists. initMap()
// in map.js assigns the `map` global asynchronously, so we poll until
// it's ready rather than relying on a fixed setTimeout.
document.addEventListener('DOMContentLoaded', function() {
    let tries = 0;
    const wait = setInterval(function() {
        tries += 1;
        if (typeof map !== 'undefined' && map && typeof map.on === 'function') {
            clearInterval(wait);
            initQGISTools();
        } else if (tries > 60) { // ~6 seconds
            clearInterval(wait);
            console.warn('QGIS tools: map instance never became ready.');
        }
    }, 100);
});
