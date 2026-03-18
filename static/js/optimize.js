/**
 * Route optimization logic and API interactions
 */

// AHP weights state (from Table 4-12, Page 90 of Report)
let ahpWeights = {
    settlements: 0.20,           // PEOPLE (20.0%)
    protected_areas: 0.289,      // HABITAT (17.8%) + FAUNA (11.1%)
    vegetation: 0.156,           // VEGETATION (15.6%)
    land_use: 0.133,             // LAND (13.3%)
    water: 0.089,                // WATER (8.9%)
    topography: 0.067,           // LANDSCAPE (6.7%)
    cultural_heritage: 0.044,    // PHYSICAL CULTURAL HERITAGE (4.4%)
    public_infrastructure: 0.022 // PUBLIC INFRASTRUCTURES (2.2%)
};

// Waypoints array
let waypoints = [];

/**
 * Initialize optimization controls
 */
document.addEventListener('DOMContentLoaded', function() {
    // Set start/end point buttons
    document.getElementById('setStartBtn').addEventListener('click', function() {
        selectionMode = 'start';
        this.classList.add('active');
        document.getElementById('setEndBtn').classList.remove('active');
    });
    
    document.getElementById('setEndBtn').addEventListener('click', function() {
        selectionMode = 'end';
        this.classList.add('active');
        document.getElementById('setStartBtn').classList.remove('active');
    });
    
    // AHP weight sliders
    setupWeightSliders();
    
    // Optimize button
    document.getElementById('optimizeBtn').addEventListener('click', optimizeRoute);

    // Generate towers button
    document.getElementById('generateTowersBtn')?.addEventListener('click', generateTowers);

    // Export buttons
    document.getElementById('exportBtn')?.addEventListener('click', () => exportRoute('geojson'));
    document.getElementById('exportXyzBtn')?.addEventListener('click', () => exportRoute('xyz'));

    // View corridor button
    document.getElementById('viewCorridorBtn')?.addEventListener('click', viewCorridor);

    // Add waypoint button
    document.getElementById('addWaypointBtn')?.addEventListener('click', addWaypoint);
});

/**
 * Setup AHP weight sliders with auto-normalization
 */
function setupWeightSliders() {
    const sliders = {
        settlements: document.getElementById('settlementsWeight'),
        protected_areas: document.getElementById('protectedWeight'),
        vegetation: document.getElementById('vegetationWeight'),
        land_use: document.getElementById('landUseWeight'),
        water: document.getElementById('waterWeight'),
        topography: document.getElementById('topoWeight'),
        cultural_heritage: document.getElementById('culturalWeight'),
        public_infrastructure: document.getElementById('publicInfraWeight')
    };

    const values = {
        settlements: document.getElementById('settlementsValue'),
        protected_areas: document.getElementById('protectedValue'),
        vegetation: document.getElementById('vegetationValue'),
        land_use: document.getElementById('landUseValue'),
        water: document.getElementById('waterValue'),
        topography: document.getElementById('topoValue'),
        cultural_heritage: document.getElementById('culturalValue'),
        public_infrastructure: document.getElementById('publicInfraValue')
    };

    // Update weights when sliders change
    Object.keys(sliders).forEach(key => {
        if (sliders[key]) {  // Check if element exists
            sliders[key].addEventListener('input', function() {
                ahpWeights[key] = parseFloat(this.value);
                values[key].textContent = parseFloat(this.value).toFixed(3);
                updateWeightSum();
            });
        }
    });
}

/**
 * Update and display weight sum
 */
function updateWeightSum() {
    const sum = Object.values(ahpWeights).reduce((a, b) => a + b, 0);
    document.getElementById('weightSum').textContent = sum.toFixed(2);
    
    // Warn if sum is not 1.0
    const sumElement = document.getElementById('weightSum');
    if (Math.abs(sum - 1.0) > 0.01) {
        sumElement.style.color = '#ff0000';
    } else {
        sumElement.style.color = '#00aa00';
    }
}

/**
 * Add a waypoint
 */
function addWaypoint() {
    const waypointId = Date.now();
    const waypoint = {
        id: waypointId,
        lat: null,
        lon: null,
        name: `Waypoint ${waypoints.length + 1}`
    };

    waypoints.push(waypoint);
    renderWaypoints();

    // Enable waypoint selection mode
    selectionMode = 'waypoint';
    currentWaypointId = waypointId;
    alert('Click on the map to set waypoint location');
}

/**
 * Remove a waypoint
 */
function removeWaypoint(waypointId) {
    waypoints = waypoints.filter(w => w.id !== waypointId);
    renderWaypoints();

    // Remove marker from map
    removeWaypointMarker(waypointId);
}

/**
 * Render waypoints list
 */
function renderWaypoints() {
    const container = document.getElementById('waypointsList');

    if (waypoints.length === 0) {
        container.innerHTML = '<p class="help-text" style="font-size: 11px; margin: 5px 0;">No waypoints added</p>';
        return;
    }

    let html = '<div class="waypoints-container">';
    waypoints.forEach((wp, index) => {
        const coords = wp.lat && wp.lon ? `${wp.lat.toFixed(4)}, ${wp.lon.toFixed(4)}` : 'Not set';
        html += `
            <div class="waypoint-item" style="margin-bottom: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <input type="text" value="${wp.name}"
                               onchange="updateWaypointName(${wp.id}, this.value)"
                               style="width: 100%; padding: 2px 5px; font-size: 11px; border: 1px solid #ddd; border-radius: 3px;">
                        <div style="font-size: 10px; color: #666; margin-top: 2px;">${coords}</div>
                    </div>
                    <button onclick="removeWaypoint(${wp.id})"
                            style="margin-left: 8px; padding: 2px 8px; font-size: 11px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer;">
                        ✕
                    </button>
                </div>
            </div>
        `;
    });
    html += '</div>';

    container.innerHTML = html;
}

/**
 * Update waypoint name
 */
function updateWaypointName(waypointId, newName) {
    const waypoint = waypoints.find(w => w.id === waypointId);
    if (waypoint) {
        waypoint.name = newName;
    }
}

/**
 * Optimize route using API
 */
async function optimizeRoute() {
    // Require user to set start and end points (no presets)
    if (!currentProject.start || !currentProject.end) {
        alert('Please set both Start Point and End Point on the map before optimizing.');
        return;
    }
    // Validate weights
    const sum = Object.values(ahpWeights).reduce((a, b) => a + b, 0);
    if (Math.abs(sum - 1.0) > 0.01) {
        alert('AHP weights must sum to 1.0. Current sum: ' + sum.toFixed(2));
        return;
    }
    
    // Show loading indicator
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('optimizeBtn').disabled = true;
    
    try {
        // Validate waypoints
        const validWaypoints = waypoints.filter(wp => wp.lat && wp.lon);

        // Step 1: Create project
        const projectData = {
            name: document.getElementById('projectName').value,
            description: 'Automated route optimization',
            voltage_level: parseInt(document.getElementById('voltageLevel').value),
            tower_type: document.getElementById('towerType').value,
            start: currentProject.start,
            end: currentProject.end,
            waypoints: validWaypoints.map(wp => ({
                lat: wp.lat,
                lon: wp.lon,
                name: wp.name
            })),
            ahp_weights: ahpWeights
        };

        console.log('Creating project with data:', projectData);

        const createResponse = await fetch('/api/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });

        if (!createResponse.ok) {
            const errorData = await createResponse.json();
            console.error('Project creation failed:', errorData);
            throw new Error('Failed to create project: ' + (errorData.error || 'Unknown error'));
        }

        const createResult = await createResponse.json();
        currentProject.projectId = createResult.project_id;
        console.log('Project created with ID:', currentProject.projectId);

        // Step 2: Optimize route (with optional algorithm and compare)
        const algorithm = document.getElementById('algorithmSelect')?.value || 'dijkstra';
        const compare = document.getElementById('compareAlgorithms')?.checked || false;
        console.log('Starting optimization for project:', currentProject.projectId, 'algorithm:', algorithm, 'compare:', compare);
        const optimizeResponse = await fetch(`/api/projects/${currentProject.projectId}/optimize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ algorithm: algorithm, compare: compare })
        });

        if (!optimizeResponse.ok) {
            const errorData = await optimizeResponse.json();
            console.error('Optimization failed:', errorData);
            throw new Error('Route optimization failed: ' + (errorData.error || 'Unknown error'));
        }
        
        const result = await optimizeResponse.json();

        // Display route on map (without towers initially)
        displayRoute(result.route, []);

        // Display results (include algorithm used and comparison if present)
        displayResults(result);

        if (result.algorithm_comparison) {
            const comp = result.algorithm_comparison;
            let msg = 'Algorithm comparison:\n';
            if (comp.dijkstra) msg += `Dijkstra: cost=${comp.dijkstra.total_cost.toFixed(0)}, points=${comp.dijkstra.path_coords_count}\n`;
            else msg += 'Dijkstra: no path\n';
            if (comp.astar) msg += `A*: cost=${comp.astar.total_cost.toFixed(0)}, points=${comp.astar.path_coords_count}`;
            else msg += 'A*: no path';
            console.log(msg);
        }

        // Show the "Generate Towers" button
        document.getElementById('generateTowersBtn').style.display = 'block';

    } catch (error) {
        console.error('Optimization error:', error);
        alert('Error: ' + error.message);
    } finally {
        // Hide loading indicator
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('optimizeBtn').disabled = false;
    }
}

/**
 * Generate towers for existing route
 */
async function generateTowers() {
    if (!currentProject.projectId) {
        alert('Please optimize a route first');
        return;
    }

    try {
        document.getElementById('loadingIndicator').style.display = 'block';
        document.getElementById('generateTowersBtn').disabled = true;

        const response = await fetch(`/api/projects/${currentProject.projectId}/generate-towers`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (response.ok) {
            // Display towers on map
            displayTowers(result.tower_positions);

            // Update cost breakdown
            displayCostBreakdown(result.cost_breakdown);

            alert(`Generated ${result.num_towers} towers successfully!`);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error generating towers:', error);
        alert('Failed to generate towers: ' + error.message);
    } finally {
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('generateTowersBtn').disabled = false;
    }
}

/**
 * Display optimization results
 */
function displayResults(result) {
    const metrics = result.validation.metrics;
    const errors = result.validation.errors;
    const warnings = result.validation.warnings;
    const costBreakdown = result.cost_breakdown;

    let html = '<div class="metrics">';
    if (result.algorithm_used) {
        html += `<p><strong>Algorithm:</strong> ${result.algorithm_used}</p>`;
    }
    html += `<p><strong>Route Length:</strong> ${(metrics.total_length_km).toFixed(2)} km</p>`;
    html += `<p><strong>Estimated Towers:</strong> ${result.route.properties.estimated_towers}</p>`;
    html += `<p><strong>Avg Span Length:</strong> ${result.route.properties.avg_span_length_m.toFixed(1)} m</p>`;
    html += `<p><strong>Total Cost:</strong> $${(costBreakdown.total_cost / 1000000).toFixed(2)}M</p>`;
    html += `<p><strong>Cost per km:</strong> $${(costBreakdown.cost_per_km / 1000).toFixed(0)}K</p>`;
    html += '</div>';

    // Show errors
    if (errors && errors.length > 0) {
        html += '<div class="errors"><h4>⚠️ Errors:</h4><ul>';
        errors.forEach(err => {
            html += `<li>${err}</li>`;
        });
        html += '</ul></div>';
    }

    // Show warnings
    if (warnings && warnings.length > 0) {
        html += '<div class="warnings"><h4>⚡ Warnings:</h4><ul>';
        warnings.forEach(warn => {
            html += `<li>${warn}</li>`;
        });
        html += '</ul></div>';
    }

    document.getElementById('routeMetrics').innerHTML = html;

    // Display detailed cost breakdown
    displayCostBreakdown(costBreakdown);

    document.getElementById('resultsSection').style.display = 'block';
}

/**
 * Display detailed cost breakdown
 */
function displayCostBreakdown(costBreakdown) {
    if (!costBreakdown || !costBreakdown.breakdown) {
        return;
    }

    const breakdown = costBreakdown.breakdown;
    let html = '<div class="cost-items">';

    // Towers
    html += `<div class="cost-item">
        <span class="cost-label">Towers (${breakdown.towers.quantity})</span>
        <span class="cost-value">$${(breakdown.towers.cost / 1000).toFixed(0)}K</span>
    </div>`;

    // Foundations
    html += `<div class="cost-item">
        <span class="cost-label">Foundations (${breakdown.foundations.quantity})</span>
        <span class="cost-value">$${(breakdown.foundations.cost / 1000).toFixed(0)}K</span>
    </div>`;

    // Conductors
    html += `<div class="cost-item">
        <span class="cost-label">Conductors (${breakdown.conductors.length_km.toFixed(1)} km)</span>
        <span class="cost-value">$${(breakdown.conductors.cost / 1000).toFixed(0)}K</span>
    </div>`;

    // Installation
    html += `<div class="cost-item">
        <span class="cost-label">Installation & Labor</span>
        <span class="cost-value">$${(breakdown.installation.cost / 1000).toFixed(0)}K</span>
    </div>`;

    // ROW
    html += `<div class="cost-item">
        <span class="cost-label">Right-of-Way</span>
        <span class="cost-value">$${(breakdown.row_acquisition.cost / 1000).toFixed(0)}K</span>
    </div>`;

    // Engineering
    html += `<div class="cost-item">
        <span class="cost-label">Engineering (${breakdown.engineering.percentage}%)</span>
        <span class="cost-value">$${(breakdown.engineering.cost / 1000).toFixed(0)}K</span>
    </div>`;

    // Contingency
    html += `<div class="cost-item">
        <span class="cost-label">Contingency (${breakdown.contingency.percentage}%)</span>
        <span class="cost-value">$${(breakdown.contingency.cost / 1000).toFixed(0)}K</span>
    </div>`;

    // Total
    html += `<div class="cost-item cost-total">
        <span class="cost-label"><strong>TOTAL</strong></span>
        <span class="cost-value"><strong>$${(costBreakdown.total_cost / 1000000).toFixed(2)}M</strong></span>
    </div>`;

    html += '</div>';

    document.getElementById('costBreakdown').innerHTML = html;
}

/**
 * Export route as GeoJSON or XYZ (Eastings, Northings, elevation for simulation)
 */
async function exportRoute(format) {
    if (!currentProject.projectId) {
        alert('No route to export');
        return;
    }
    const fmt = format || 'geojson';
    try {
        const routesResponse = await fetch(`/api/projects/${currentProject.projectId}/routes`);
        const routesData = await routesResponse.json();
        if (!routesData.routes || routesData.routes.length === 0) {
            alert('No route to export');
            return;
        }
        const routeId = routesData.routes[0].id;
        const exportUrl = `/api/routes/${routeId}/export?format=${fmt}`;
        const res = await fetch(exportUrl);
        const data = await res.json();
        if (!res.ok) {
            alert(data.error || 'Export failed');
            return;
        }
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fmt === 'xyz' ? 'route_xyz_epsg21096.json' : 'transmission_line_route.geojson';
        a.click();
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Export error:', error);
        alert('Failed to export route');
    }
}

/**
 * View corridor polygon
 */
async function viewCorridor() {
    if (!currentProject.projectId) {
        alert('No route available');
        return;
    }
    
    try {
        // Get routes for project
        const routesResponse = await fetch(`/api/projects/${currentProject.projectId}/routes`);
        const routesData = await routesResponse.json();
        
        if (routesData.routes && routesData.routes.length > 0) {
            const routeId = routesData.routes[0].id;
            
            // Get corridor
            const corridorResponse = await fetch(`/api/routes/${routeId}/corridor`);
            const corridorData = await corridorResponse.json();
            
            // Display corridor on map
            displayCorridor(corridorData.corridor);
            
            // Show land acquisition info
            const la = corridorData.land_acquisition;
            alert(`Corridor Information:\n\n` +
                  `Area: ${la.corridor_area_hectares.toFixed(2)} hectares (${la.corridor_area_acres.toFixed(2)} acres)\n` +
                  `Length: ${la.route_length_km.toFixed(2)} km\n` +
                  `Width: ${la.corridor_width_m}m (RoW: ${la.row_width_m}m + Wayleave: ${la.wayleave_width_m}m)`);
        }
    } catch (error) {
        console.error('Corridor error:', error);
        alert('Failed to load corridor');
    }
}

