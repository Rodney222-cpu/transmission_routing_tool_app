/**
 * OpenStreetMap-style basemap tiles (same families as openstreetmap.org / common providers).
 * Multiple basemaps can be stacked with reduced opacity so you can compare styles.
 * Optional API keys: set window.MAP_KEYS = { maptiler: 'YOUR_KEY', thunderforest: 'YOUR_KEY' } before load.
 */

const tileLayers = {
    standard: null,
    cyclOSM: null,
    cycleMap: null,
    transportMap: null,
    humanitarian: null,
    tracestrack: null,
    shortbread: null,
    mapTiler: null
};

const activeLayers = new Set();

function mapKeys() {
    return window.MAP_KEYS || {};
}

const tileLayerConfigs = {
    standard: {
        name: 'Standard',
        url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
        subdomains: 'abc'
    },
    cyclOSM: {
        name: 'CyclOSM',
        url: 'https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://www.cyclosm.org">CyclOSM</a> | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 20,
        subdomains: 'abc'
    },
    cycleMap: {
        name: 'Cycle Map',
        url: 'https://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey={apikey}',
        attribution: '&copy; <a href="https://www.thunderforest.com">Thunderforest</a> | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 22,
        subdomains: 'abc',
        needsKey: 'thunderforest'
    },
    transportMap: {
        name: 'Transport Map',
        url: 'https://{s}.tile.thunderforest.com/transport/{z}/{x}/{y}.png?apikey={apikey}',
        attribution: '&copy; <a href="https://www.thunderforest.com">Thunderforest</a> | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 22,
        subdomains: 'abc',
        needsKey: 'thunderforest'
    },
    humanitarian: {
        name: 'Humanitarian',
        url: 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://www.hotosm.org">HOT</a> | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 20,
        subdomains: 'abc'
    },
    tracestrack: {
        name: 'OpenTopoMap',
        url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://opentopomap.org">OpenTopoMap</a> | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 17,
        subdomains: 'abc'
    },
    shortbread: {
        name: 'CartoDB Positron',
        url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | &copy; <a href="https://carto.com/attributions">CARTO</a>',
        maxZoom: 20,
        subdomains: 'abcd'
    },
    mapTiler: {
        name: 'MapTiler OMT',
        url: null,
        buildUrl: function () {
            const k = mapKeys().maptiler || '';
            if (!k) {
                return null;
            }
            return 'https://api.maptiler.com/maps/openstreetmap/{z}/{x}/{y}.png?key=' + encodeURIComponent(k);
        },
        attribution: '&copy; <a href="https://www.maptiler.com">MapTiler</a> | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 22,
        subdomains: ''
    }
};

const checkboxToLayerKey = {
    showStandard: 'standard',
    showCyclOSM: 'cyclOSM',
    showCycleMap: 'cycleMap',
    showTransport: 'transportMap',
    showHumanitarian: 'humanitarian',
    showTopo: 'tracestrack',
    showShortbread: 'shortbread',
    showMapTiler: 'mapTiler'
};

document.addEventListener('DOMContentLoaded', function () {
    Object.keys(checkboxToLayerKey).forEach(function (checkboxId) {
        const el = document.getElementById(checkboxId);
        if (!el) return;
        el.addEventListener('change', function () {
            const key = checkboxToLayerKey[checkboxId];
            if (this.checked) {
                loadOsmTileLayer(key);
            } else {
                removeOsmTileLayer(key);
            }
            updateActiveLayersDisplay();
        });
    });

    document.getElementById('clearLayers')?.addEventListener('click', function () {
        Object.values(checkboxToLayerKey).forEach(removeOsmTileLayer);
        Object.keys(checkboxToLayerKey).forEach(function (id) {
            const cb = document.getElementById(id);
            if (cb) cb.checked = false;
        });
        activeLayers.clear();
        updateActiveLayersDisplay();
    });

    // One default basemap so the map is not empty (layers.js loads after map.js initMap)
    if (typeof map !== 'undefined') {
        loadOsmTileLayer('standard');
        const std = document.getElementById('showStandard');
        if (std) std.checked = true;
        updateActiveLayersDisplay();
    }
});

/**
 * Update the display of active layers in the UI
 */
function updateActiveLayersDisplay() {
    const infoDiv = document.getElementById('activeLayersInfo');
    const listSpan = document.getElementById('activeLayersList');
    
    if (!infoDiv || !listSpan) return;
    
    const activeNames = getActiveLayerNames();
    
    if (activeNames.length === 0) {
        infoDiv.style.display = 'none';
    } else {
        infoDiv.style.display = 'block';
        listSpan.textContent = activeNames.join(', ');
    }
}

function loadOsmTileLayer(layerKey) {
    const config = tileLayerConfigs[layerKey];
    if (!config) {
        console.warn('Unknown basemap', layerKey);
        return;
    }

    let url = config.url;
    
    // Handle layers that need API keys
    if (config.needsKey) {
        const key = mapKeys()[config.needsKey] || '';
        if (!key) {
            alert(config.name + ' needs a free API key from Thunderforest. Add to your .env: THUNDERFOREST_API_KEY=your_key');
            const id = Object.keys(checkboxToLayerKey).find(function (k) {
                return checkboxToLayerKey[k] === layerKey;
            });
            if (id) {
                const cb = document.getElementById(id);
                if (cb) cb.checked = false;
            }
            return;
        }
        url = url.replace('{apikey}', encodeURIComponent(key));
    }
    
    if (typeof config.buildUrl === 'function') {
        url = config.buildUrl();
        if (!url) {
            alert('MapTiler OMT needs a free API key. Add to your .env: MAPTILER_API_KEY=your_key');
            const id = Object.keys(checkboxToLayerKey).find(function (k) {
                return checkboxToLayerKey[k] === layerKey;
            });
            if (id) {
                const cb = document.getElementById(id);
                if (cb) cb.checked = false;
            }
            return;
        }
    }

    removeOsmTileLayer(layerKey);

    const subdomains = config.subdomains || 'abc';
    
    // Calculate opacity: when multiple layers are active, make them semi-transparent
    // so users can see all selected layers at once
    const opacity = activeLayers.size > 0 ? 0.6 : 1.0;
    
    const opts = {
        attribution: config.attribution,
        maxZoom: config.maxZoom,
        opacity: opacity
    };
    if (subdomains) {
        opts.subdomains = subdomains;
    }

    tileLayers[layerKey] = L.tileLayer(url, opts);
    tileLayers[layerKey].addTo(map);
    activeLayers.add(layerKey);
    updateOsmTileOpacity();
    
    console.log('Added layer:', layerKey, 'Active layers:', Array.from(activeLayers));
}

function removeOsmTileLayer(layerKey) {
    if (tileLayers[layerKey]) {
        map.removeLayer(tileLayers[layerKey]);
        tileLayers[layerKey] = null;
    }
    activeLayers.delete(layerKey);
    updateOsmTileOpacity();
}

function updateOsmTileOpacity() {
    const n = activeLayers.size;
    // When multiple layers are selected, make them all semi-transparent
    // so users can see features from all layers at once
    const op = n > 1 ? 0.65 : 1.0;
    activeLayers.forEach(function (key) {
        if (tileLayers[key]) {
            tileLayers[key].setOpacity(op);
        }
    });
}

/**
 * Get list of currently active layer names (for display or debugging)
 */
function getActiveLayerNames() {
    return Array.from(activeLayers).map(function(key) {
        return tileLayerConfigs[key] ? tileLayerConfigs[key].name : key;
    });
}

/**
 * Legend for route / towers (bottom-right)
 */
function addLegend() {
    if (typeof map === 'undefined') return;
    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function () {
        const div = L.DomUtil.create('div', 'legend');
        div.innerHTML =
            '<h4>Legend</h4>' +
            '<div class="legend-row"><span class="legend-line" style="background:#00aa00;"></span> Start</div>' +
            '<div class="legend-row"><span class="legend-line" style="background:#ff0000;"></span> End</div>' +
            '<div class="legend-row"><span class="legend-line" style="background:#FF6B00;"></span> Route</div>' +
            '<div class="legend-row"><span class="legend-line" style="background:#0066CC;"></span> Towers</div>' +
            '<div class="legend-row"><span class="legend-line" style="background:#FFD700;"></span> Corridor</div>';
        return div;
    };
    legend.addTo(map);
}
