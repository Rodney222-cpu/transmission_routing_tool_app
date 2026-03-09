/**
 * GIS Layer management for map visualization
 * Handles DEM, Land Use, Settlements, Protected Areas, and Roads layers
 */

// Layer state
let layers = {
    dem: null,
    landUse: null,
    settlements: null,
    protected: null,
    roads: null
};

/**
 * Initialize layer controls
 */
document.addEventListener('DOMContentLoaded', function() {
    // Layer toggle checkboxes
    document.getElementById('showDEM')?.addEventListener('change', function() {
        toggleLayer('dem', this.checked);
    });
    
    document.getElementById('showLandUse')?.addEventListener('change', function() {
        toggleLayer('landUse', this.checked);
    });
    
    document.getElementById('showSettlements')?.addEventListener('change', function() {
        toggleLayer('settlements', this.checked);
    });
    
    document.getElementById('showProtected')?.addEventListener('change', function() {
        toggleLayer('protected', this.checked);
    });
    
    document.getElementById('showRoads')?.addEventListener('change', function() {
        toggleLayer('roads', this.checked);
    });
});

/**
 * Toggle layer visibility
 */
function toggleLayer(layerName, show) {
    if (show) {
        loadLayer(layerName);
    } else {
        removeLayer(layerName);
    }
}

/**
 * Load and display a GIS layer
 */
function loadLayer(layerName) {
    // Remove existing layer
    removeLayer(layerName);
    
    // In production, this would load actual GIS data
    // For demo, we'll add placeholder layers
    
    switch(layerName) {
        case 'dem':
            // Add DEM/topography visualization
            // This would typically be a WMS layer or raster tiles
            console.log('Loading DEM layer...');
            // Placeholder: Add a semi-transparent overlay
            break;
            
        case 'landUse':
            // Add land use layer (ESA WorldCover)
            console.log('Loading Land Use layer...');
            // In production: Load from WMS or tile service
            break;
            
        case 'settlements':
            // Add settlements layer
            console.log('Loading Settlements layer...');
            // Could use OpenStreetMap data
            loadSettlementsFromOSM();
            break;
            
        case 'protected':
            // Add protected areas (NEMA/NFA/UWA)
            console.log('Loading Protected Areas layer...');
            break;
            
        case 'roads':
            // Add roads layer
            console.log('Loading Roads layer...');
            loadRoadsFromOSM();
            break;
    }
}

/**
 * Remove a layer from the map
 */
function removeLayer(layerName) {
    if (layers[layerName]) {
        map.removeLayer(layers[layerName]);
        layers[layerName] = null;
    }
}

/**
 * Load settlements from OpenStreetMap
 */
function loadSettlementsFromOSM() {
    // Example: Load settlements as markers
    // In production, use Overpass API or pre-processed data
    
    // Sample settlements in the area
    const settlements = [
        { name: 'Gulu', lat: 2.7746, lon: 32.2989 },
        { name: 'Kitgum', lat: 3.2817, lon: 32.8864 },
        { name: 'Atiak', lat: 3.3500, lon: 32.2000 }
    ];
    
    const settlementMarkers = [];
    
    settlements.forEach(settlement => {
        const marker = L.circleMarker([settlement.lat, settlement.lon], {
            radius: 8,
            fillColor: '#ff7800',
            color: '#000',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.6
        }).bindPopup(`<b>${settlement.name}</b><br>Settlement`);
        
        settlementMarkers.push(marker);
    });
    
    layers.settlements = L.layerGroup(settlementMarkers).addTo(map);
}

/**
 * Load roads from OpenStreetMap
 */
function loadRoadsFromOSM() {
    // Example: Load major roads
    // In production, use Overpass API or tile service
    
    // Sample road data (simplified)
    const roads = [
        [[3.3, 32.3], [3.4, 32.4], [3.5, 32.5]],
        [[3.2, 32.2], [3.3, 32.3], [3.4, 32.2]]
    ];
    
    const roadLines = roads.map(coords => {
        return L.polyline(coords, {
            color: '#666',
            weight: 2,
            opacity: 0.7
        });
    });
    
    layers.roads = L.layerGroup(roadLines).addTo(map);
}

/**
 * Add legend for layers
 */
function addLegend() {
    const legend = L.control({ position: 'bottomright' });
    
    legend.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'legend');
        div.innerHTML = `
            <h4>Legend</h4>
            <div><span style="background: #00aa00;"></span> Start Point</div>
            <div><span style="background: #ff0000;"></span> End Point</div>
            <div><span style="background: #FF6B00;"></span> Optimized Route</div>
            <div><span style="background: #0066CC;"></span> Tower Positions</div>
            <div><span style="background: #FFD700;"></span> 60m Corridor</div>
        `;
        return div;
    };
    
    legend.addTo(map);
}

// Add legend when map is ready
if (typeof map !== 'undefined') {
    addLegend();
}

