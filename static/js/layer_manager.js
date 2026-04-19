/**
 * Layer Management for Transmission Line Routing Tool
 * Handles checkbox events for GIS layers (shapefiles)
 */

// Layer instances
let gisLayers = {
    uganda_districts: null,
    protected_areas: null,
    rivers: null,
    wetlands: null,
    lakes: null,
    roads: null,
    elevation: null,
    settlements: null,
    hospitals: null,
    commercial: null,
    land_use: null
};

/**
 * Initialize layer checkbox event handlers
 */
function initLayerCheckboxes() {
    console.log('✓ Initializing layer checkboxes...');
    
    // Uganda Districts (base map)
    document.getElementById('showUgandaDistricts')?.addEventListener('change', function() {
        toggleLayer('uganda_districts', this.checked);
    });
    
    // Environmental layers
    document.getElementById('showProtectedAreas')?.addEventListener('change', function() {
        toggleLayer('protected_areas', this.checked);
    });
    
    document.getElementById('showRivers')?.addEventListener('change', function() {
        toggleLayer('rivers', this.checked);
    });
    
    document.getElementById('showWetlands')?.addEventListener('change', function() {
        toggleLayer('wetlands', this.checked);
    });
    
    document.getElementById('showLakes')?.addEventListener('change', function() {
        toggleLayer('lakes', this.checked);
    });
    
    // Infrastructure layers
    document.getElementById('showRoads')?.addEventListener('change', function() {
        toggleLayer('roads', this.checked);
    });
    
    document.getElementById('showElevation')?.addEventListener('change', function() {
        toggleLayer('elevation', this.checked);
    });
    
    // Settlements & Facilities
    document.getElementById('showSettlements')?.addEventListener('change', function() {
        toggleLayer('settlements', this.checked);
    });
    
    document.getElementById('showHospitals')?.addEventListener('change', function() {
        toggleLayer('hospitals', this.checked);
    });
    
    document.getElementById('showCommercial')?.addEventListener('change', function() {
        toggleLayer('commercial', this.checked);
    });
    
    // Land cover
    document.getElementById('showLandUse')?.addEventListener('change', function() {
        toggleLayer('land_use', this.checked);
    });
    
    // Clear all layers button
    document.getElementById('clearLayers')?.addEventListener('click', clearAllLayers);
    
    console.log('✓ Layer checkboxes initialized');
}

/**
 * Toggle a GIS layer on/off
 */
function toggleLayer(layerName, visible) {
    console.log(`🔘 Toggle ${layerName}: ${visible ? 'ON' : 'OFF'}`);
    
    if (visible) {
        // Add layer if not already created
        if (!gisLayers[layerName]) {
            console.log(`🆕 Creating new layer: ${layerName}`);
            gisLayers[layerName] = createGISLayer(layerName);
        }
        
        // Add to map if not already added
        if (!map.hasLayer(gisLayers[layerName])) {
            console.log(`➕ Adding ${layerName} to map`);
            gisLayers[layerName].addTo(map);
        } else {
            console.log(`✓ ${layerName} already on map`);
        }
    } else {
        // Remove layer from map
        if (gisLayers[layerName] && map.hasLayer(gisLayers[layerName])) {
            console.log(`➖ Removing ${layerName} from map`);
            map.removeLayer(gisLayers[layerName]);
        }
    }
}

/**
 * Create a GIS layer based on layer name
 * Each layer loads from corresponding shapefile
 */
function createGISLayer(layerName) {
    console.log(`🎨 Creating GIS layer: ${layerName}`);
    
    const layer = L.layerGroup();
    
    // Layer configurations - matches shapefile names
    const layerConfig = {
        'uganda_districts': {
            style: { color: '#666666', fillColor: '#F5F5F5', fillOpacity: 0.3, weight: 1 },
            popupPrefix: 'District'
        },
        'protected_areas': {
            style: { color: '#228B22', fillColor: '#90EE90', fillOpacity: 0.3, weight: 2 },
            popupPrefix: 'Protected Area'
        },
        'rivers': {
            style: { color: '#0000CD', weight: 2, opacity: 0.7 },
            popupPrefix: 'River'
        },
        'wetlands': {
            style: { color: '#4A90E2', fillColor: '#87CEEB', fillOpacity: 0.5, weight: 1 },
            popupPrefix: 'Wetland'
        },
        'lakes': {
            style: { color: '#0000CD', fillColor: '#87CEEB', fillOpacity: 0.6, weight: 2 },
            popupPrefix: 'Lake'
        },
        'roads': {
            style: { color: '#696969', weight: 3, opacity: 0.7 },
            popupPrefix: 'Road'
        },
        'elevation': {
            style: { color: '#8B4513', weight: 1, opacity: 0.5 },
            popupPrefix: 'Contour'
        },
        'settlements': {
            style: { radius: 5, fillColor: '#FF6347', color: '#8B0000', weight: 1, fillOpacity: 0.7 },
            popupPrefix: 'School'
        },
        'hospitals': {
            style: { radius: 6, fillColor: '#FF0000', color: '#8B0000', weight: 1, fillOpacity: 0.8 },
            popupPrefix: 'Hospital'
        },
        'commercial': {
            style: { radius: 5, fillColor: '#FF8C00', color: '#8B4500', weight: 1, fillOpacity: 0.7 },
            popupPrefix: 'Commercial'
        },
        'land_use': {
            style: { color: '#8B4513', fillColor: '#DEB887', fillOpacity: 0.2, weight: 1 },
            popupPrefix: 'Land Use'
        }
    };
    
    const config = layerConfig[layerName];
    if (!config) {
        console.error(`❌ Unknown layer: ${layerName}`);
        return layer;
    }
    
    console.log(`⚙️ Layer config for ${layerName}:`, config.style);
    
    // Load layer from API (which loads from shapefile)
    layer.on('add', function() {
        console.log(`📡 Layer 'add' event triggered for ${layerName}`);
        loadGISLayer(layerName, layer, config.style, config.popupPrefix);
    });
    
    return layer;
}

/**
 * Clear all GIS layers from map
 */
function clearAllLayers() {
    console.log('Clearing all layers...');
    
    // Remove all layers from map
    Object.keys(gisLayers).forEach(layerName => {
        if (gisLayers[layerName] && map.hasLayer(gisLayers[layerName])) {
            map.removeLayer(gisLayers[layerName]);
        }
    });
    
    // Uncheck all checkboxes
    document.querySelectorAll('.map-controls input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    
    // Re-check Uganda Districts (base layer)
    document.getElementById('showUgandaDistricts').checked = true;
    toggleLayer('uganda_districts', true);
    
    console.log('✓ All layers cleared');
}

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Wait for map to be initialized
    setTimeout(() => {
        if (typeof map !== 'undefined') {
            initLayerCheckboxes();
        }
    }, 1000);
});
