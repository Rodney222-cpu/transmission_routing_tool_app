/**
 * GIS Layer management for map visualization
 * Loads DEM, Land Use, Settlements, Protected Areas, Roads from API and displays on map.
 * Data sources: USGS (DEM), ESA WorldCover (land use), NEMA/NFA/UWA (protected), OSM (settlements, roads).
 */

// Layer state (keys match API: dem, land_use, settlements, protected_areas, roads)
let layers = {
    dem: null,
    landUse: null,
    settlements: null,
    protected: null,
    roads: null
};

// Map layer name (checkbox id) to API layer name
const layerApiName = {
    dem: 'dem',
    landUse: 'land_use',
    settlements: 'settlements',
    protected: 'protected_areas',
    roads: 'roads'
};

/**
 * Initialize layer controls
 */
document.addEventListener('DOMContentLoaded', function() {
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
 * Get current map bounds for API request
 */
function getMapBounds() {
    if (typeof map === 'undefined' || !map.getBounds) {
        return { min_lon: 32.0, min_lat: 3.2, max_lon: 32.6, max_lat: 3.6 };
    }
    const b = map.getBounds();
    return {
        min_lon: b.getWest(),
        min_lat: b.getSouth(),
        max_lon: b.getEast(),
        max_lat: b.getNorth()
    };
}

/**
 * Load and display a GIS layer from API (DEM, land use, settlements, protected areas, roads)
 */
function loadLayer(layerName) {
    removeLayer(layerName);
    const apiName = layerApiName[layerName] || layerName;
    const bounds = getMapBounds();
    const params = new URLSearchParams({
        min_lon: bounds.min_lon,
        min_lat: bounds.min_lat,
        max_lon: bounds.max_lon,
        max_lat: bounds.max_lat,
        layers: apiName
    });

    fetch('/api/layers?' + params.toString(), { credentials: 'same-origin' })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (!data.layers || !data.layers[apiName]) return;
            const fc = data.layers[apiName];
            if (!fc.features || fc.features.length === 0) return;

            function _clamp(v, min, max) {
                return Math.max(min, Math.min(max, v));
            }

            // Simple blue -> yellow -> red ramp.
            // In this demo, elevation is synthetic and typically in ~0..100.
            function _elevationColor(elevation) {
                const e = _clamp(Number(elevation) || 0, 0, 100);
                if (e <= 50) {
                    // blue (#2b83ba) -> yellow (#ffffbf)
                    const t = e / 50;
                    return _lerpColor('#2b83ba', '#ffffbf', t);
                }
                // yellow (#ffffbf) -> red (#d7191c)
                const t = (e - 50) / 50;
                return _lerpColor('#ffffbf', '#d7191c', t);
            }

            function _hexToRgb(hex) {
                const h = hex.replace('#', '');
                return {
                    r: parseInt(h.slice(0, 2), 16),
                    g: parseInt(h.slice(2, 4), 16),
                    b: parseInt(h.slice(4, 6), 16)
                };
            }

            function _lerp(a, b, t) {
                return Math.round(a + (b - a) * t);
            }

            function _lerpColor(hexA, hexB, t) {
                const a = _hexToRgb(hexA);
                const b = _hexToRgb(hexB);
                const tt = _clamp(t, 0, 1);
                const r = _lerp(a.r, b.r, tt);
                const g = _lerp(a.g, b.g, tt);
                const bb = _lerp(a.b, b.b, tt);
                return `rgb(${r}, ${g}, ${bb})`;
            }

            const styleByLayer = {
                dem: function(f) {
                    const e = f.properties.elevation ?? 0;
                    const r = Math.min(12, 4 + (Number(e) || 0) / 15);
                    return {
                        radius: r,
                        fillColor: _elevationColor(e),
                        color: '#222',
                        weight: 1,
                        fillOpacity: 0.75
                    };
                },
                land_use: function(f) {
                    const cl = f.properties.class || 0;
                    const colors = { 10: '#228B22', 30: '#9ACD32', 40: '#DEB887', 50: '#696969', 80: '#4169E1', 90: '#20B2AA' };
                    return { radius: 6, fillColor: colors[cl] || '#ccc', color: '#333', weight: 1, fillOpacity: 0.6 };
                },
                settlements: function() {
                    return { radius: 8, fillColor: '#ff7800', color: '#000', weight: 1, fillOpacity: 0.6 };
                },
                protected_areas: function() {
                    return { radius: 8, fillColor: '#CD5C5C', color: '#8B0000', weight: 1, fillOpacity: 0.5 };
                },
                roads: function() {
                    return { radius: 4, fillColor: '#666', color: '#333', weight: 1, fillOpacity: 0.8 };
                }
            };
            const styleFn = styleByLayer[apiName];
            const layerGroup = L.geoJSON(fc, {
                pointToLayer: function(feat, latlng) {
                    const opts = styleFn ? styleFn(feat) : { radius: 6, fillColor: '#888', fillOpacity: 0.5 };
                    return L.circleMarker(latlng, opts);
                },
                onEachFeature: function(feat, layer) {
                    const p = feat.properties || {};
                    let pop = '';
                    if (p.elevation != null) pop = 'Elevation: ' + p.elevation + ' m';
                    else if (p.label) pop = p.label;
                    else if (p.type) pop = p.type;
                    if (pop) layer.bindPopup(pop);
                }
            });
            layerGroup.addTo(map);
            layers[layerName] = layerGroup;
        })
        .catch(function(err) {
            console.error('Failed to load layer ' + layerName, err);
        });
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
 * Add legend for layers (called from map.js when map is ready if desired)
 */
function addLegend() {
    if (typeof map === 'undefined') return;
    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function() {
        const div = L.DomUtil.create('div', 'legend');
        div.innerHTML =
            '<h4>Legend</h4>' +
            '<div class="legend-row"><span class="legend-line" style="background:#00aa00;"></span> Start</div>' +
            '<div class="legend-row"><span class="legend-line" style="background:#ff0000;"></span> End</div>' +
            '<div class="legend-row"><span class="legend-line" style="background:#FF6B00;"></span> Route</div>' +
            '<div class="legend-row"><span class="legend-line" style="background:#0066CC;"></span> Towers</div>' +
            '<div class="legend-row"><span class="legend-line" style="background:#FFD700;"></span> Corridor</div>' +
            '<hr class="legend-sep"/>' +
            '<div class="legend-subtitle">DEM/Topography (Elevation)</div>' +
            '<div class="legend-row"><span class="legend-swatch" style="background:#2b83ba;"></span> Low</div>' +
            '<div class="legend-row"><span class="legend-swatch" style="background:#ffffbf;"></span> Mid</div>' +
            '<div class="legend-row"><span class="legend-swatch" style="background:#d7191c;"></span> High</div>' +
            '<hr class="legend-sep"/>' +
            '<div class="legend-subtitle">Land Use (WorldCover classes)</div>' +
            '<div class="legend-row"><span class="legend-swatch" style="background:#228B22;"></span> Tree cover (10)</div>' +
            '<div class="legend-row"><span class="legend-swatch" style="background:#9ACD32;"></span> Grassland (30)</div>' +
            '<div class="legend-row"><span class="legend-swatch" style="background:#DEB887;"></span> Cropland (40)</div>' +
            '<div class="legend-row"><span class="legend-swatch" style="background:#696969;"></span> Built-up (50)</div>' +
            '<div class="legend-row"><span class="legend-swatch" style="background:#4169E1;"></span> Water (80)</div>' +
            '<div class="legend-row"><span class="legend-swatch" style="background:#20B2AA;"></span> Wetlands (90)</div>' +
            '<hr class="legend-sep"/>' +
            '<div class="legend-subtitle">Other layers</div>' +
            '<div class="legend-row"><span class="legend-dot" style="background:#ff7800;"></span> Settlements</div>' +
            '<div class="legend-row"><span class="legend-dot" style="background:#CD5C5C; border-color:#8B0000;"></span> Protected areas</div>' +
            '<div class="legend-row"><span class="legend-dot" style="background:#666; border-color:#333;"></span> Roads</div>' +
            '<div class="legend-note">Tip: click a circle to see its value.</div>';
        return div;
    };
    legend.addTo(map);
}

