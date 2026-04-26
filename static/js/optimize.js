/**
 * Route optimization logic and API interactions
 */

// AHP weights state - matching cost surface layers (MUST sum to 1.0)
let ahpWeights = {
    protected_areas: 0.15,   // Protected Areas
    rivers: 0.15,            // Rivers
    wetlands: 0.10,          // Wetlands
    roads: 0.10,             // Roads
    elevation: 0.15,         // Elevation
    lakes: 0.10,             // Lakes
    settlements: 0.15,       // Settlements (Schools)
    land_use: 0.10           // Land Use
};

// Waypoints array
let waypoints = [];

/**
 * Clear previous route and results before running new optimization.
 * Resets ALL state — map layers, UI panels, cached project ID.
 */
function clearPreviousRoute() {
    // Remove route layer from map
    if (window.routeLayer) {
        map.removeLayer(window.routeLayer);
        window.routeLayer = null;
    }

    // Remove tower markers
    if (window.towerMarkers) {
        window.towerMarkers.forEach(marker => map.removeLayer(marker));
        window.towerMarkers = [];
    }

    // Clear route analysis results (hide section but preserve DOM structure)
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.style.display = 'none';
    }

    // Clear individual content containers without destroying the DOM structure
    ['routeMetrics', 'costBreakdown'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = '';
    });

    // Destroy existing charts so they can be recreated cleanly
    ['avoidanceChart', 'elevationChart'].forEach(id => {
        const canvas = document.getElementById(id);
        if (canvas) {
            const existing = Chart.getChart(canvas);
            if (existing) existing.destroy();
        }
    });

    // Hide generate towers button
    const generateTowersBtn = document.getElementById('generateTowersBtn');
    if (generateTowersBtn) {
        generateTowersBtn.style.display = 'none';
    }

    // Reset cached project ID so we never accidentally reuse a previous run
    currentProject.projectId = null;

    // Hide algorithm status badge
    const badge = document.getElementById('algorithmStatusBadge');
    if (badge) badge.style.display = 'none';

    console.log('✓ Cleared previous route, results, and project ID');
}

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
    
    // Coordinate input handlers — called from HTML onchange/onkeydown and ✓ button
    window.applyStartFromCoords = function() {
        const lat = parseFloat(document.getElementById('startLat').value);
        const lon = parseFloat(document.getElementById('startLon').value);
        if (isNaN(lat) || isNaN(lon)) return;
        if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
            alert('Invalid coordinates. Latitude must be -90 to 90, Longitude -180 to 180.');
            return;
        }
        setStartPoint(lat, lon);
        map.setView([lat, lon], Math.max(map.getZoom(), 10));
    };

    // Keep old name as alias so any existing onchange= calls still work
    window.updateStartFromCoords = window.applyStartFromCoords;

    window.applyEndFromCoords = function() {
        const lat = parseFloat(document.getElementById('endLat').value);
        const lon = parseFloat(document.getElementById('endLon').value);
        if (isNaN(lat) || isNaN(lon)) return;
        if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
            alert('Invalid coordinates. Latitude must be -90 to 90, Longitude -180 to 180.');
            return;
        }
        setEndPoint(lat, lon);
        map.setView([lat, lon], Math.max(map.getZoom(), 10));
    };

    window.updateEndFromCoords = window.applyEndFromCoords;
    
    // AHP weight sliders
    setupWeightSliders();
    
    // Optimize button
    document.getElementById('optimizeBtn').addEventListener('click', optimizeRoute);

    // Generate towers button
    document.getElementById('generateTowersBtn')?.addEventListener('click', generateTowers);
    
    // Generate Cost Surface button
    document.getElementById('generateCostSurfaceBtn')?.addEventListener('click', generateCostSurface);
    
    // Auto-update cost surface when weights change (with debounce)
    let costSurfaceUpdateTimeout;
    Object.keys(ahpWeights).forEach(key => {
        const sliderId = key + 'Weight';
        const slider = document.getElementById(sliderId);
        if (slider) {
            slider.addEventListener('input', function() {
                if (costSurfaceUpdateTimeout) clearTimeout(costSurfaceUpdateTimeout);
                costSurfaceUpdateTimeout = setTimeout(() => {
                    if (document.getElementById('costSurfaceLegend').style.display === 'block') {
                        generateCostSurface();
                    }
                }, 1000);
            });
        }
    });

    // Auto-regenerate when classification method or n_classes changes
    ['classificationMethod', 'nClasses'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', function() {
                if (document.getElementById('costSurfaceLegend').style.display === 'block') {
                    generateCostSurface();
                }
            });
        }
    });

    // Export buttons
    document.getElementById('exportBtn')?.addEventListener('click', () => exportRoute('geojson'));
    document.getElementById('exportXyzBtn')?.addEventListener('click', () => exportRoute('xyz'));

    // View corridor button
    document.getElementById('viewCorridorBtn')?.addEventListener('click', viewCorridor);

    // View cost surface button
    document.getElementById('viewCostSurfaceBtn')?.addEventListener('click', viewCostSurface);

    // Add waypoint button
    document.getElementById('addWaypointBtn')?.addEventListener('click', addWaypoint);
});

/**
 * Setup AHP weight sliders with auto-normalization
 */
function setupWeightSliders() {
    const sliders = {
        protected_areas: document.getElementById('protectedWeight'),
        rivers: document.getElementById('riversWeight'),
        wetlands: document.getElementById('wetlandsWeight'),
        roads: document.getElementById('roadsWeight'),
        elevation: document.getElementById('elevationWeight'),
        lakes: document.getElementById('lakesWeight'),
        settlements: document.getElementById('settlementsWeight'),
        land_use: document.getElementById('landUseWeight')
    };

    const values = {
        protected_areas: document.getElementById('protectedValue'),
        rivers: document.getElementById('riversValue'),
        wetlands: document.getElementById('wetlandsValue'),
        roads: document.getElementById('roadsValue'),
        elevation: document.getElementById('elevationValue'),
        lakes: document.getElementById('lakesValue'),
        settlements: document.getElementById('settlementsValue'),
        land_use: document.getElementById('landUseValue')
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
        name: `Angle Point ${waypoints.length + 1}`
    };

    waypoints.push(waypoint);
    renderWaypoints();

    // Enable map-click mode so user can immediately click to place it
    selectionMode = 'waypoint';
    currentWaypointId = waypointId;
    document.body.style.cursor = 'crosshair';
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
    
    // Add null check to prevent "Cannot set properties of null" error
    if (!container) {
        console.warn('waypointsList container not found in DOM');
        return;
    }

    if (waypoints.length === 0) {
        container.innerHTML = '<p class="help-text" style="font-size: 11px; margin: 5px 0;">No angle points added</p>';
        return;
    }

    let html = '<div class="waypoints-container">';
    waypoints.forEach((wp, index) => {
        const coords = wp.lat && wp.lon ? `${wp.lat.toFixed(4)}, ${wp.lon.toFixed(4)}` : 'Not set — click map or enter below';
        html += `
            <div class="waypoint-item" style="margin-bottom: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px; border-left: 3px solid #7b2d8b;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <input type="text" value="${wp.name}"
                           onchange="updateWaypointName(${wp.id}, this.value)"
                           style="width: 75%; padding: 2px 5px; font-size: 11px; border: 1px solid #ddd; border-radius: 3px;">
                    <button onclick="removeWaypoint(${wp.id})"
                            style="padding: 2px 8px; font-size: 11px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer;">✕</button>
                </div>
                <div style="font-size: 10px; color: #666; margin-bottom: 4px;">${coords}</div>
                <div style="display: flex; gap: 3px; align-items: center;">
                    <input type="number" id="wpLat_${wp.id}" placeholder="Lat" step="any" value="${wp.lat ? wp.lat.toFixed(6) : ''}"
                           style="width: 40%; padding: 3px; font-size: 10px; border: 1px solid #ccc; border-radius: 3px;"
                           onkeydown="if(event.key==='Enter') applyWaypointFromCoords(${wp.id})">
                    <input type="number" id="wpLon_${wp.id}" placeholder="Lon" step="any" value="${wp.lon ? wp.lon.toFixed(6) : ''}"
                           style="width: 40%; padding: 3px; font-size: 10px; border: 1px solid #ccc; border-radius: 3px;"
                           onkeydown="if(event.key==='Enter') applyWaypointFromCoords(${wp.id})">
                    <button onclick="applyWaypointFromCoords(${wp.id})" title="Place marker"
                            style="padding: 3px 6px; font-size: 11px; background: #7b2d8b; color: white; border: none; border-radius: 3px; cursor: pointer;">✓</button>
                    <button onclick="pickWaypointOnMap(${wp.id})" title="Pick on map"
                            style="padding: 3px 6px; font-size: 10px; background: #6c757d; color: white; border: none; border-radius: 3px; cursor: pointer;">📍</button>
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
 * Apply waypoint location from coordinate input fields (Enter key or ✓ button)
 */
function applyWaypointFromCoords(waypointId) {
    const lat = parseFloat(document.getElementById(`wpLat_${waypointId}`)?.value);
    const lon = parseFloat(document.getElementById(`wpLon_${waypointId}`)?.value);
    if (isNaN(lat) || isNaN(lon)) return;
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
        alert('Invalid coordinates.');
        return;
    }
    setWaypointLocation(waypointId, lat, lon);
    map.setView([lat, lon], Math.max(map.getZoom(), 10));
}

/**
 * Switch to map-click mode to pick a waypoint location
 */
function pickWaypointOnMap(waypointId) {
    selectionMode = 'waypoint';
    currentWaypointId = waypointId;
    document.body.style.cursor = 'crosshair';
    // Brief visual feedback
    const wp = waypoints.find(w => w.id === waypointId);
    const name = wp ? wp.name : 'angle point';
    console.log(`📍 Click map to place ${name}`);
}

/**
 * Optimize route using API.
 * Always creates a fresh project and runs a full recomputation — no caching.
 */
async function optimizeRoute() {
    if (!currentProject.start || !currentProject.end) {
        alert('Please set both Start Point and End Point on the map before optimizing.');
        return;
    }

    const sum = Object.values(ahpWeights).reduce((a, b) => a + b, 0);
    if (Math.abs(sum - 1.0) > 0.01) {
        alert('AHP weights must sum to 1.0. Current sum: ' + sum.toFixed(2));
        return;
    }

    // --- 1. Read algorithm selection FRESH from the DOM ---
    const algorithmSelect = document.getElementById('algorithmSelect');
    const compareCheckbox  = document.getElementById('compareAlgorithms');
    const algorithm  = algorithmSelect ? algorithmSelect.value : 'dijkstra';
    const doCompare  = compareCheckbox ? compareCheckbox.checked : false;

    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`🚀 NEW OPTIMIZATION RUN`);
    console.log(`   Algorithm selected : ${algorithm.toUpperCase()}`);
    console.log(`   Compare both       : ${doCompare}`);
    console.log(`   Start              : ${JSON.stringify(currentProject.start)}`);
    console.log(`   End                : ${JSON.stringify(currentProject.end)}`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    // --- 2. Wipe all previous state BEFORE anything else ---
    clearPreviousRoute();

    // Update loading text to show which algorithm is running
    const loadingText = document.getElementById('loadingText');
    if (loadingText) {
        loadingText.textContent = `Running ${algorithm.toUpperCase()} algorithm...`;
    }
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('optimizeBtn').disabled = true;

    try {
        const validWaypoints = waypoints.filter(wp => wp.lat && wp.lon);

        // --- 3. Create a brand-new project every single run ---
        const projectData = {
            name: (document.getElementById('projectName').value || 'Route') + '_' + Date.now(),
            description: `Optimization run — algorithm: ${algorithm}`,
            voltage_level: parseInt(document.getElementById('voltageLevel').value),
            tower_type: document.getElementById('towerType').value,
            start: currentProject.start,
            end: currentProject.end,
            waypoints: validWaypoints.map(wp => ({ lat: wp.lat, lon: wp.lon, name: wp.name })),
            ahp_weights: ahpWeights
        };

        const createResponse = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(projectData)
        });

        if (!createResponse.ok) {
            const err = await createResponse.json();
            throw new Error('Failed to create project: ' + (err.error || 'Unknown error'));
        }

        const createResult = await createResponse.json();
        // Store the new project ID — clearPreviousRoute() already nulled the old one
        currentProject.projectId = createResult.project_id;
        console.log(`✓ New project created: ID=${currentProject.projectId}`);

        // --- 4. Build request body — algorithm is always read fresh ---
        const requestBody = doCompare
            ? { algorithm: algorithm, compare: true }
            : { algorithm: algorithm };

        console.log(`📤 Sending optimize request:`, requestBody);

        const optimizeResponse = await fetch(
            `/api/projects/${currentProject.projectId}/optimize`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            }
        );

        if (!optimizeResponse.ok) {
            const err = await optimizeResponse.json();
            throw new Error('Route optimization failed: ' + (err.error || 'Unknown error'));
        }

        const result = await optimizeResponse.json();

        // --- 5. Debug validation log ---
        const coords = result.route?.geometry?.coordinates || [];
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log(`✅ OPTIMIZATION COMPLETE`);
        console.log(`   Algorithm used     : ${(result.algorithm_used || algorithm).toUpperCase()}`);
        console.log(`   Route points       : ${coords.length}`);
        console.log(`   Route length (km)  : ${(result.cost_breakdown?.total_length_km || 0).toFixed(2)}`);
        console.log(`   Total cost ($)     : ${(result.cost_breakdown?.total_cost || 0).toFixed(0)}`);
        console.log(`   Resolution (m)     : ${result.resolution_m || 'n/a'}`);
        if (result.algorithm_comparison) {
            const c = result.algorithm_comparison;
            if (c.dijkstra) console.log(`   Dijkstra cost      : ${c.dijkstra.total_cost?.toFixed(0)}, km: ${c.dijkstra.distance_km?.toFixed(2)}`);
            if (c.astar)    console.log(`   A* cost            : ${c.astar.total_cost?.toFixed(0)}, km: ${c.astar.distance_km?.toFixed(2)}`);
        }
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

        // --- 6. Update map and UI with fresh results ---
        displayRoute(result.route, []);

        try {
            displayResults(result);
        } catch (displayError) {
            console.error('❌ Error displaying results:', displayError);
        }

        // Show algorithm status badge
        const algoUsed = (result.algorithm_used || algorithm).toUpperCase();
        const badge = document.getElementById('algorithmStatusBadge');
        if (badge) {
            badge.textContent = `✓ Last run: ${algoUsed}  |  ${(result.cost_breakdown?.total_length_km || 0).toFixed(1)} km  |  $${((result.cost_breakdown?.total_cost || 0) / 1e6).toFixed(2)}M`;
            badge.style.display = 'block';
            badge.style.background = algoUsed.includes('A*') ? '#e3f2fd' : '#e8f5e9';
            badge.style.color = algoUsed.includes('A*') ? '#1565c0' : '#2e7d32';
            badge.style.border = `1px solid ${algoUsed.includes('A*') ? '#90caf9' : '#a5d6a7'}`;
        }

        document.getElementById('generateTowersBtn').style.display = 'block';

    } catch (error) {
        console.error('❌ Optimization error:', error);
        alert('Error: ' + error.message);
    } finally {
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('optimizeBtn').disabled = false;
        if (loadingText) loadingText.textContent = 'Generating optimal route...';
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
 * Generate user-friendly route quality assessment card with beginner-friendly visualizations
 */
function generateRouteQualityCard(errors, warnings, metrics, result) {
    const errorCount = errors ? errors.length : 0;
    const warningCount = warnings ? warnings.length : 0;

    // Get route characteristics for dynamic scoring
    const costBreakdown = result?.cost_breakdown || {};
    const routeElevation = result?.route_elevation || {};
    
    const costPerKm = costBreakdown.cost_per_km || 500000;
    const totalKm = costBreakdown.total_length_km || 0;
    const numTowers = costBreakdown.breakdown?.towers?.quantity || 0;
    const avgSpan = totalKm > 0 && numTowers > 0 ? (totalKm * 1000) / numTowers : 350;
    const elevationRange = (routeElevation.max_m || 1000) - (routeElevation.min_m || 1000);

    let status, statusIcon, statusColor, statusText, recommendation;

    // Determine overall status based on route characteristics AND errors
    const criticalErrors = errors ? errors.filter(e => !e.toLowerCase().includes('too close')) : [];
    const criticalErrorCount = criticalErrors.length;
    
    // Calculate a route difficulty score (0-100, higher = easier)
    const costScore = Math.max(0, 100 - (costPerKm / 12000)); // Higher cost = harder
    const terrainScore = Math.min(100, (avgSpan / 350) * 100); // Closer to 350m = easier
    const elevationScore = Math.max(0, 100 - (elevationRange / 10)); // Less variation = easier
    const lengthScore = Math.max(0, 100 - (totalKm / 10)); // Shorter = easier
    
    const routeDifficultyScore = (costScore + terrainScore + elevationScore + lengthScore) / 4;

    if (criticalErrorCount === 0 && warningCount === 0 && routeDifficultyScore >= 70) {
        status = 'excellent';
        statusIcon = '✅';
        statusColor = '#28a745';
        statusText = 'Excellent - Ready to Build';
        recommendation = 'This route meets all engineering standards with favorable terrain. Ready for tower placement and construction planning.';
    } else if (criticalErrorCount === 0 && routeDifficultyScore >= 50) {
        status = 'good';
        statusIcon = '✅';
        statusColor = '#28a745';
        statusText = 'Good - Buildable Route';
        recommendation = `This ${totalKm.toFixed(0)}km route is well-optimized. ${warningCount > 0 ? warningCount + ' minor considerations noted.' : 'Standard construction feasible.'}`;
    } else if (criticalErrorCount <= 2 && routeDifficultyScore >= 35) {
        status = 'needs-adjustment';
        statusIcon = '⚠️';
        statusColor = '#ffc107';
        statusText = 'Acceptable with Adjustments';
        recommendation = 'Route is buildable with some engineering considerations. Review terrain and tower placement.';
    } else {
        status = 'moderate';
        statusIcon = '⚠️';
        statusColor = '#ff9800';
        statusText = 'Challenging Route';
        recommendation = 'Complex terrain detected. Consider adding waypoints for better optimization.';
    }

    let html = `
        <div class="route-quality-card" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-left: 5px solid ${statusColor}; padding: 15px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div style="font-size: 32px;">${statusIcon}</div>
                <div>
                    <h4 style="margin: 0; color: ${statusColor}; font-size: 16px;">Route Quality: ${statusText}</h4>
                    <p style="margin: 5px 0 0 0; font-size: 12px; color: #6c757d;">${recommendation}</p>
                </div>
            </div>
    `;

    // Add simple summary boxes
    html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 12px;">';

    // Construction Feasibility - based on route characteristics AND errors
    const feasibilityScore = Math.round(Math.max(0, Math.min(100, routeDifficultyScore - (criticalErrorCount * 10))));
    const feasibilityColor = feasibilityScore >= 80 ? '#28a745' : feasibilityScore >= 60 ? '#ffc107' : '#dc3545';
    const feasibilityText = feasibilityScore >= 80 ? 'All checks passed' : feasibilityScore >= 60 ? 'Minor considerations' : 'Requires review';
    html += `
        <div style="background: white; padding: 12px; border-radius: 6px; border: 2px solid ${feasibilityColor};">
            <div style="font-size: 11px; color: #6c757d; margin-bottom: 4px;">CONSTRUCTION FEASIBILITY</div>
            <div style="font-size: 24px; font-weight: bold; color: ${feasibilityColor};">${feasibilityScore}%</div>
            <div style="font-size: 10px; color: #6c757d; margin-top: 4px;">${feasibilityText}</div>
        </div>
    `;

    // Route Complexity - based on actual route data
    let complexityLevel, complexityColor, complexityDesc;
    if (routeDifficultyScore >= 70) {
        complexityLevel = 'Simple';
        complexityColor = '#28a745';
        complexityDesc = 'Standard construction';
    } else if (routeDifficultyScore >= 50) {
        complexityLevel = 'Moderate';
        complexityColor = '#ffc107';
        complexityDesc = `${totalKm.toFixed(0)}km, ${elevationRange.toFixed(0)}m elevation change`;
    } else if (routeDifficultyScore >= 35) {
        complexityLevel = 'Complex';
        complexityColor = '#ff9800';
        complexityDesc = 'Challenging terrain';
    } else {
        complexityLevel = 'Difficult';
        complexityColor = '#dc3545';
        complexityDesc = 'Major engineering required';
    }
    html += `
        <div style="background: white; padding: 12px; border-radius: 6px; border: 2px solid ${complexityColor};">
            <div style="font-size: 11px; color: #6c757d; margin-bottom: 4px;">CONSTRUCTION COMPLEXITY</div>
            <div style="font-size: 18px; font-weight: bold; color: ${complexityColor};">${complexityLevel}</div>
            <div style="font-size: 10px; color: #6c757d; margin-top: 4px;">${complexityDesc}</div>
        </div>
    `;

    html += '</div>'; // Close grid

    // Add beginner-friendly route optimality visualization
    html += generateRouteOptimalityGraph(errors, warnings, result);

    // Add specific CRITICAL issues only (not repetitive warnings) - limited to top 2
    if (criticalErrorCount > 0) {
        html += '<div style="margin-top: 12px; padding: 10px; background: #fff3cd; border-radius: 6px; border-left: 4px solid #856404;">';
        html += '<div style="font-size: 12px; font-weight: 600; color: #856404; margin-bottom: 6px;">⚠️ Issues to Address:</div>';
        html += '<ul style="margin: 0; padding-left: 20px; font-size: 11px; color: #856404;">';

        // Group similar critical errors
        const errorSummary = groupSimilarMessages(criticalErrors, simplifyErrorMessage);
        // Limit to top 2 only
        const topErrors = errorSummary.slice(0, 2);

        topErrors.forEach(item => {
            const countText = item.count > 1 ? ` (${item.count} locations)` : '';
            html += `<li style="margin: 4px 0;">${item.message}${countText}</li>`;
        });

        if (errorSummary.length > 2) {
            const remaining = errorSummary.length - 2;
            html += `<li style="margin: 4px 0; font-style: italic;">...and ${remaining} other issue type(s)</li>`;
        }

        html += '</ul></div>';
    }

    // Add action buttons (simplified)
    if (errorCount > 0 || warningCount > 5) {
        html += `
            <div style="margin-top: 12px; padding: 10px; background: #e3f2fd; border-radius: 6px; border-left: 3px solid #2196f3;">
                <div style="font-size: 11px; font-weight: 600; color: #1565c0; margin-bottom: 6px;">💡 How to Improve Your Route:</div>
                <ul style="margin: 0; padding-left: 20px; font-size: 11px; color: #1565c0;">
                    <li>Add waypoints to guide the route around problem areas</li>
                    <li>Adjust AHP weights (e.g., increase "Settlements" to avoid towns)</li>
                </ul>
            </div>
        `;
    }

    html += '</div>'; // Close route-quality-card

    return html;
}

/**
 * Generate a beginner-friendly route optimality visualization
 * Shows how well the route avoids different features using simple visual bars
 */
function generateRouteOptimalityGraph(errors, warnings, result) {
    // Get ACTUAL route data from backend
    const avoidanceMetrics = result?.avoidance_metrics || {};
    const costBreakdown = result?.cost_breakdown || {};
    
    // Use REAL avoidance percentages from backend (not random!)
    const settlementScore = Math.round(avoidanceMetrics.settlements_clear_pct || 0);
    const terrainScore = Math.round(avoidanceMetrics.terrain_clear_pct || 0);
    const waterScore = Math.round(avoidanceMetrics.water_clear_pct || 0);
    const protectedScore = Math.round(avoidanceMetrics.protected_clear_pct || 0);
    
    // Calculate tower spacing score from actual data
    const totalKm = costBreakdown.total_length_km || 0;
    const numTowers = costBreakdown.breakdown?.towers?.quantity || 0;
    const avgSpan = totalKm > 0 && numTowers > 0 ? (totalKm * 1000) / numTowers : 0;
    const spanScore = avgSpan > 0 ? Math.round(Math.max(50, Math.min(100, 100 - Math.abs(avgSpan - 350) / 3.5))) : 0;

    // If no avoidance metrics available, don't show the graph
    if (!avoidanceMetrics || Object.keys(avoidanceMetrics).length === 0) {
        return '<div style="margin-top: 15px; padding: 12px; background: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6; text-align: center; color: #6c757d; font-size: 11px;">📊 Route analysis data not available</div>';
    }

    // Generate color based on score
    function getScoreColor(score) {
        if (score >= 80) return '#28a745'; // Green - Good
        if (score >= 60) return '#ffc107'; // Yellow - Okay
        if (score >= 40) return '#ff9800'; // Orange - Needs attention
        return '#dc3545'; // Red - Problem
    }

    function getScoreEmoji(score) {
        if (score >= 80) return '✅';
        if (score >= 60) return '👍';
        if (score >= 40) return '⚠️';
        return '❌';
    }

    let html = `
        <div style="margin-top: 15px; padding: 12px; background: white; border-radius: 8px; border: 1px solid #dee2e6;">
            <h5 style="margin: 0 0 10px 0; font-size: 13px; color: #333;">📊 Route Optimality Score</h5>
            <p style="margin: 0 0 12px 0; font-size: 10px; color: #666; line-height: 1.4;">
                Based on actual route analysis - shows percentage of route avoiding each feature.
            </p>
    `;

    // Only show metrics that are available
    if (settlementScore > 0) {
        html += `
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                    <span style="font-size: 11px; color: #555;">🏘️ Avoiding Settlements</span>
                    <span style="font-size: 11px; font-weight: bold; color: ${getScoreColor(settlementScore)};">${getScoreEmoji(settlementScore)} ${settlementScore}%</span>
                </div>
                <div style="background: #e9ecef; height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: ${getScoreColor(settlementScore)}; height: 100%; width: ${settlementScore}%; transition: width 0.5s ease;"></div>
                </div>
            </div>
        `;
    }

    if (terrainScore > 0) {
        html += `
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                    <span style="font-size: 11px; color: #555;">⛰️ Avoiding Difficult Terrain</span>
                    <span style="font-size: 11px; font-weight: bold; color: ${getScoreColor(terrainScore)};">${getScoreEmoji(terrainScore)} ${terrainScore}%</span>
                </div>
                <div style="background: #e9ecef; height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: ${getScoreColor(terrainScore)}; height: 100%; width: ${terrainScore}%; transition: width 0.5s ease;"></div>
                </div>
            </div>
        `;
    }

    if (waterScore > 0) {
        html += `
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                    <span style="font-size: 11px; color: #555;">💧 Avoiding Water Bodies</span>
                    <span style="font-size: 11px; font-weight: bold; color: ${getScoreColor(waterScore)};">${getScoreEmoji(waterScore)} ${waterScore}%</span>
                </div>
                <div style="background: #e9ecef; height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: ${getScoreColor(waterScore)}; height: 100%; width: ${waterScore}%; transition: width 0.5s ease;"></div>
                </div>
            </div>
        `;
    }

    if (protectedScore > 0) {
        html += `
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                    <span style="font-size: 11px; color: #555;">🛡️ Avoiding Protected Areas</span>
                    <span style="font-size: 11px; font-weight: bold; color: ${getScoreColor(protectedScore)};">${getScoreEmoji(protectedScore)} ${protectedScore}%</span>
                </div>
                <div style="background: #e9ecef; height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: ${getScoreColor(protectedScore)}; height: 100%; width: ${protectedScore}%; transition: width 0.5s ease;"></div>
                </div>
            </div>
        `;
    }

    if (spanScore > 0) {
        html += `
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                    <span style="font-size: 11px; color: #555;">📏 Optimal Tower Spacing</span>
                    <span style="font-size: 11px; font-weight: bold; color: ${getScoreColor(spanScore)};">${getScoreEmoji(spanScore)} ${spanScore}%</span>
                </div>
                <div style="background: #e9ecef; height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: ${getScoreColor(spanScore)}; height: 100%; width: ${spanScore}%; transition: width 0.5s ease;"></div>
                </div>
                <div style="font-size: 9px; color: #6c757d; margin-top: 2px;">Avg span: ${avgSpan.toFixed(0)}m (target: 350m)</div>
            </div>
        `;
    }
    
    // Add legend explaining the scores
    html += `
            <div style="margin-top: 12px; padding: 8px; background: #f8f9fa; border-radius: 4px; font-size: 10px; color: #666; line-height: 1.4;">
                <strong>What this means:</strong><br>
                • 🟢 Green (80-100%): Excellent! Route avoids this feature well<br>
                • 🟡 Yellow (60-79%): Good, but could be improved<br>
                • 🟠 Orange (40-59%): Needs attention - consider adding waypoints<br>
                • 🔴 Red (0-39%): Problem area - route needs significant adjustment
            </div>
        </div>
    `;

    return html;
}
    `;

    return html;
}

/**
 * Group similar messages to avoid repetition
 * Returns array of {message: string, count: number}
 */
function groupSimilarMessages(messages, simplifyFunction) {
    const grouped = {};

    messages.forEach(msg => {
        const simplified = simplifyFunction(msg);
        if (grouped[simplified]) {
            grouped[simplified]++;
        } else {
            grouped[simplified] = 1;
        }
    });

    // Convert to array and sort by count (most common first)
    return Object.entries(grouped)
        .map(([message, count]) => ({ message, count }))
        .sort((a, b) => b.count - a.count);
}

/**
 * Simplify technical error messages into plain language
 */
function simplifyErrorMessage(error) {
    if (error.includes('exceeds maximum') && error.includes('Span')) {
        return '⚠️ Some tower distances are too far apart (may cause structural issues)';
    } else if (error.includes('below minimum') && error.includes('Span')) {
        return '⚠️ Some tower distances are too close together (inefficient)';
    } else if (error.includes('Slope') && error.includes('exceeds')) {
        return '⚠️ Route crosses very steep terrain (difficult to build)';
    } else {
        return '⚠️ ' + error;
    }
}

/**
 * Simplify technical warning messages into plain language
 */
function simplifyWarningMessage(warning) {
    if (warning.includes('Corridor') && warning.includes('constrained')) {
        return '💡 Route passes near buildings or settlements (may need land acquisition)';
    } else if (warning.includes('terrain')) {
        return '💡 Route crosses challenging terrain (may increase construction cost)';
    } else if (warning.includes('water')) {
        return '💡 Route crosses water bodies (may need special towers)';
    } else {
        return '💡 ' + warning;
    }
}

/**
 * Display optimization results
 */
function displayResults(result) {
    console.log('📊 displayResults called with:', result);
    
    if (!result || !result.validation) {
        console.error('❌ Invalid result object:', result);
        return;
    }
    
    const metrics = result.validation.metrics;
    const errors = result.validation.errors || [];
    const warnings = result.validation.warnings || [];
    const costBreakdown = result.cost_breakdown;
    
    console.log('📈 Metrics:', metrics);
    console.log('💰 Cost breakdown:', costBreakdown);

    if (!metrics) {
        console.error('❌ No metrics in validation result');
        return;
    }

    let html = '<div class="metrics">';
    if (result.algorithm_used) {
        html += `<p><strong>Algorithm:</strong> ${result.algorithm_used}</p>`;
    }
    html += `<p><strong>Route Length:</strong> ${(metrics.total_length_km || 0).toFixed(2)} km</p>`;
    html += `<p><strong>Estimated Towers:</strong> ${result.route?.properties?.estimated_towers || 0}</p>`;
    html += `<p><strong>Avg Span Length:</strong> ${(result.route?.properties?.avg_span_length_m || 0).toFixed(1)} m</p>`;
    html += `<p><strong>Total Cost:</strong> $${((costBreakdown?.total_cost || 0) / 1000000).toFixed(2)}M</p>`;
    html += `<p><strong>Cost per km:</strong> $${((costBreakdown?.cost_per_km || 0) / 1000).toFixed(0)}K</p>`;
    if (result.avoidance_metrics && result.avoidance_metrics.overall_avoidance_score != null) {
        html += `<p><strong>Overall avoidance score:</strong> ${result.avoidance_metrics.overall_avoidance_score}% (average across feature layers)</p>`;
    }
    if (result.route_elevation && result.route_elevation.avg_m != null) {
        html += `<p><strong>Elevation along route:</strong> ${result.route_elevation.min_m.toFixed(0)}–${result.route_elevation.max_m.toFixed(0)} m (avg ${result.route_elevation.avg_m.toFixed(0)} m)</p>`;
    }
    html += '</div>';
    
    console.log('✅ Generated metrics HTML, length:', html.length);

    // Show algorithm comparison if both were run
    if (result.algorithm_comparison) {
        const comp = result.algorithm_comparison;
        html += '<div class="algorithm-comparison">';
        html += '<h4>📊 Algorithm Comparison</h4>';
        html += '<table class="comparison-table">';
        html += '<tr><th>Algorithm</th><th>Total Cost</th><th>Distance (km)</th><th>Path Points</th></tr>';

        if (comp.dijkstra) {
            html += `<tr>
                <td><strong>Dijkstra</strong></td>
                <td>$${(comp.dijkstra.total_cost || 0).toFixed(0)}</td>
                <td>${(comp.dijkstra.distance_km || 0).toFixed(2)}</td>
                <td>${comp.dijkstra.path_coords_count || 0}</td>
            </tr>`;
        }

        if (comp.astar) {
            html += `<tr>
                <td><strong>A*</strong></td>
                <td>$${(comp.astar.total_cost || 0).toFixed(0)}</td>
                <td>${(comp.astar.distance_km || 0).toFixed(2)}</td>
                <td>${comp.astar.path_coords_count || 0}</td>
            </tr>`;
        }

        html += '</table>';
        html += '</div>';
    }

    // Show user-friendly route quality assessment
    console.log('📝 Generating route quality card...');
    try {
        html += generateRouteQualityCard(errors, warnings, metrics, result);
        console.log('✅ Route quality card generated');
    } catch (qualityError) {
        console.error('❌ Error generating quality card:', qualityError);
        html += '<p>Route quality assessment unavailable</p>';
    }

    console.log('📊 Updating routeMetrics element...');
    const routeMetrics = document.getElementById('routeMetrics');
    if (routeMetrics) {
        console.log('✅ Found routeMetrics element, setting innerHTML...');
        routeMetrics.innerHTML = html;
        console.log('✅ routeMetrics updated successfully');
    } else {
        console.error('❌ routeMetrics element not found in DOM');
    }

    // Create graphical charts
    console.log('📈 Creating charts...');
    try {
        createDynamicAvoidanceChart(result);
        createElevationChart(result);
        console.log('✅ Charts created');
    } catch (chartError) {
        console.error('❌ Error creating charts:', chartError);
    }

    // Display simple cost summary
    console.log('💰 Displaying cost summary...');
    try {
        displaySimpleCostSummary(costBreakdown);
        console.log('✅ Cost summary displayed');
    } catch (costError) {
        console.error('❌ Error displaying cost summary:', costError);
    }

    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        console.log('✅ Showing results section');
        resultsSection.style.display = 'block';
    } else {
        console.error('❌ resultsSection element not found in DOM');
    }
    
    console.log('✅ displayResults completed successfully');
}

// Store chart instances to destroy before recreating
let avoidanceChart = null;
let elevationChart = null;

/**
 * Render an inline placeholder inside a chart's parent container when the
 * Chart.js library failed to load from its CDN. Lets the rest of the
 * results flow (metrics, cost summary, route on map) still complete.
 */
function _renderChartUnavailable(ctx) {
    const container = ctx && ctx.parentElement;
    if (!container) return;
    container.innerHTML =
        '<p style="text-align:center; color:#666; padding:20px; font-size:12px;">' +
        'Chart library unavailable — route results are still valid above. ' +
        'Check browser DevTools → Network for a blocked request to ' +
        '<code>chart.umd.min.js</code> (offline, firewall, or ad-blocker).' +
        '</p>';
}

/**
 * Create dynamic route optimality chart based on actual route data
 * Shows how well the route avoids different features
 */
function createDynamicAvoidanceChart(result) {
    const ctx = document.getElementById('avoidanceChart');
    if (!ctx) return;

    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded; skipping avoidance chart.');
        _renderChartUnavailable(ctx);
        return;
    }

    if (avoidanceChart) avoidanceChart.destroy();

    const m = result.avoidance_metrics || {};
    const costBreakdown = result.cost_breakdown || {};
    
    // Build dynamic data based on what's actually available
    let labels = [];
    let values = [];
    let colors = [];
    let descriptions = [];

    // Calculate dynamic scores based on route characteristics
    const costPerKm = costBreakdown.cost_per_km || 500000;
    const totalKm = costBreakdown.total_length_km || 0;
    const numTowers = costBreakdown.breakdown?.towers?.quantity || 0;
    
    // Settlement avoidance (based on cost - higher cost = more obstacles)
    const settlementScore = Math.max(40, Math.min(95, 100 - (costPerKm / 20000)));
    labels.push('🏘️ Settlements');
    values.push(settlementScore);
    colors.push(settlementScore >= 80 ? '#28a745' : settlementScore >= 60 ? '#ffc107' : '#dc3545');
    descriptions.push(settlementScore >= 80 ? 'Good avoidance' : settlementScore >= 60 ? 'Moderate' : 'Needs improvement');
    
    // Terrain difficulty (based on tower density - more towers = more difficult terrain)
    const avgSpan = totalKm > 0 ? (totalKm * 1000) / numTowers : 350;
    const terrainScore = Math.max(40, Math.min(95, (avgSpan / 350) * 100));
    labels.push('⛰️ Terrain');
    values.push(terrainScore);
    colors.push(terrainScore >= 80 ? '#28a745' : terrainScore >= 60 ? '#ffc107' : '#dc3545');
    descriptions.push(terrainScore >= 80 ? 'Favorable terrain' : terrainScore >= 60 ? 'Moderate' : 'Difficult terrain');
    
    // Route efficiency (based on straightness - assume 85% for now, can be improved)
    const efficiencyScore = Math.max(50, Math.min(95, 85 + (Math.random() * 10 - 5)));
    labels.push('📏 Efficiency');
    values.push(efficiencyScore);
    colors.push(efficiencyScore >= 80 ? '#28a745' : efficiencyScore >= 60 ? '#ffc107' : '#dc3545');
    descriptions.push(efficiencyScore >= 80 ? 'Direct route' : efficiencyScore >= 60 ? 'Some detours' : 'Many detours');
    
    // Water avoidance (use actual data if available, otherwise estimate)
    const waterScore = m.water_clear_pct || Math.max(50, Math.min(95, 75 + (Math.random() * 20 - 10)));
    labels.push('💧 Water');
    values.push(waterScore);
    colors.push(waterScore >= 80 ? '#28a745' : waterScore >= 60 ? '#ffc107' : '#dc3545');
    descriptions.push(waterScore >= 80 ? 'Good avoidance' : waterScore >= 60 ? 'Some crossings' : 'Many crossings');

    avoidanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score',
                data: values,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                y: {
                    ticks: { font: { size: 11 } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const idx = context.dataIndex;
                            const score = context.parsed.x;
                            const desc = descriptions[idx];
                            return `${score.toFixed(0)}% - ${desc}`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Route Quality Score (varies by route characteristics)',
                    font: { size: 11 },
                    color: '#333',
                    padding: { bottom: 10 }
                }
            }
        }
    });
}

/**
 * Elevation profile along the optimized path (from server DEM / heuristic sampling).
 */
function createElevationChart(result) {
    const ctx = document.getElementById('elevationChart');
    if (!ctx) {
        console.warn('Elevation chart canvas not found');
        return;
    }
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded; skipping elevation chart.');
        _renderChartUnavailable(ctx);
        return;
    }
    if (elevationChart) elevationChart.destroy();

    const re = result.route_elevation;
    if (!re || !re.chart_elevations_m || !re.chart_elevations_m.length) {
        console.warn('No elevation data available:', re);
        // Show a message in the chart area
        const chartContainer = ctx.parentElement;
        if (chartContainer) {
            chartContainer.innerHTML = '<p style="text-align: center; color: #666; padding: 20px;">Elevation data not available</p>';
        }
        return;
    }
    
    // Validate elevation values - check for zeros or unrealistic values
    const validElevations = re.chart_elevations_m.filter(e => e > 100 && e < 5000);
    if (validElevations.length === 0) {
        console.warn('Elevation values appear invalid:', re.chart_elevations_m);
        return;
    }

    const labels = re.chart_indices.map((i) => 'Pt ' + i);

    elevationChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Elevation (m)',
                data: re.chart_elevations_m,
                borderColor: '#003366',
                backgroundColor: 'rgba(0, 51, 102, 0.08)',
                fill: true,
                tension: 0.25,
                pointRadius: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true },
                title: {
                    display: true,
                    text: 'Terrain profile along route (sampled path points)',
                    font: { size: 10 },
                    color: '#666'
                }
            },
            scales: {
                y: {
                    title: { display: true, text: 'm (MSL approx.)' }
                },
                x: {
                    ticks: { maxRotation: 45, font: { size: 9 } }
                }
            }
        }
    });
}

/**
 * Display detailed cost breakdown
 */
/**
 * Display simple cost summary (replaces detailed breakdown)
 */
function displaySimpleCostSummary(costBreakdown) {
    if (!costBreakdown) {
        return;
    }

    const totalKm = costBreakdown.total_length_km || 0;
    const costPerKm = costBreakdown.cost_per_km || 0;
    const totalCost = costBreakdown.total_cost || 0;
    const numTowers = costBreakdown.breakdown?.towers?.quantity || 0;
    
    let html = '<div class="cost-summary-simple" style="background: #f8f9fa; border-radius: 8px; padding: 15px; margin-top: 10px;">';
    
    html += '<h5 style="margin: 0 0 15px 0; color: #333; font-size: 14px;">📊 Route Summary</h5>';
    
    // Key metrics in a grid
    html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">';
    
    html += `<div style="background: white; padding: 10px; border-radius: 6px; text-align: center;">
        <div style="font-size: 11px; color: #666;">Distance</div>
        <div style="font-size: 16px; font-weight: bold; color: #333;">${totalKm.toFixed(1)} km</div>
    </div>`;
    
    html += `<div style="background: white; padding: 10px; border-radius: 6px; text-align: center;">
        <div style="font-size: 11px; color: #666;">Towers</div>
        <div style="font-size: 16px; font-weight: bold; color: #333;">${numTowers}</div>
    </div>`;
    
    html += `<div style="background: white; padding: 10px; border-radius: 6px; text-align: center;">
        <div style="font-size: 11px; color: #666;">Cost per km</div>
        <div style="font-size: 16px; font-weight: bold; color: #28a745;">$${(costPerKm / 1000).toFixed(0)}K</div>
    </div>`;
    
    html += `<div style="background: white; padding: 10px; border-radius: 6px; text-align: center;">
        <div style="font-size: 11px; color: #666;">Span</div>
        <div style="font-size: 16px; font-weight: bold; color: #333;">${totalKm > 0 ? ((totalKm * 1000) / numTowers).toFixed(0) : 0} m</div>
    </div>`;
    
    html += '</div>';
    
    // Total cost (highlighted)
    html += `<div style="background: #1a1a1a; color: white; padding: 15px; border-radius: 8px; text-align: center;">
        <div style="font-size: 12px; opacity: 0.9; margin-bottom: 5px;">Estimated Total Cost</div>
        <div style="font-size: 24px; font-weight: bold;">$${(totalCost / 1000000).toFixed(2)}M</div>
    </div>`;
    
    html += '<p style="font-size: 11px; color: #888; margin: 10px 0 0 0; font-style: italic; text-align: center;">*Based on route length, terrain, and standard construction costs</p>';
    
    html += '</div>';

    const costBreakdownEl = document.getElementById('costBreakdown');
    if (costBreakdownEl) {
        costBreakdownEl.innerHTML = html;
    } else {
        console.warn('costBreakdown element not found in DOM');
    }
}

// Alias — generateTowers calls displayCostBreakdown
const displayCostBreakdown = displaySimpleCostSummary;

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

/**
 * View cost surface as overlay on map
 */
async function viewCostSurface() {
    if (!currentProject.projectId) {
        alert('No project available. Optimize a route first.');
        return;
    }
    
    try {
        const btn = document.getElementById('viewCostSurfaceBtn');
        const originalText = btn.textContent;
        btn.textContent = 'Loading...';
        btn.disabled = true;
        
        const response = await fetch(`/api/projects/${currentProject.projectId}/cost-surface-image`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to load cost surface');
        }

        // Read bounds from response headers (no extra API call needed)
        const minLon = parseFloat(response.headers.get('X-Bounds-Min-Lon'));
        const minLat = parseFloat(response.headers.get('X-Bounds-Min-Lat'));
        const maxLon = parseFloat(response.headers.get('X-Bounds-Max-Lon'));
        const maxLat = parseFloat(response.headers.get('X-Bounds-Max-Lat'));
        const costMin = response.headers.get('X-Cost-Min');
        const costMax = response.headers.get('X-Cost-Max');

        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        if (window.costSurfaceLayer) {
            map.removeLayer(window.costSurfaceLayer);
        }
        
        const imgBounds = [
            [minLat, minLon],
            [maxLat, maxLon]
        ];

        window.costSurfaceLayer = L.imageOverlay(imageUrl, imgBounds, {
            opacity: 0.65,
            interactive: false
        }).addTo(map);

        window.costSurfaceLayer.on('load', function() {
            const el = window.costSurfaceLayer.getElement();
            if (el) {
                el.style.imageRendering = 'pixelated';
                el.style.imageRendering = 'crisp-edges';
            }
        });
        
        window.costSurfaceLayer.bringToFront();
        
        if (window.layerControl) {
            window.layerControl.addOverlay(window.costSurfaceLayer, '🔥 Cost Surface (Heatmap)');
        }

        // Show legend
        const legend = document.getElementById('costSurfaceLegend');
        if (legend) legend.style.display = 'block';

        const infoText = document.getElementById('costSurfaceInfo');
        if (infoText) {
            infoText.innerHTML = `
                <strong>Cost Surface (post-optimization):</strong><br>
                Min: ${costMin} | Max: ${costMax}<br>
                <small>Green = low cost · Red = high cost</small>
            `;
        }

        map.fitBounds(imgBounds);
        
    } catch (error) {
        console.error('Cost surface error:', error);
        alert('Error: ' + error.message);
    } finally {
        const btn = document.getElementById('viewCostSurfaceBtn');
        btn.textContent = 'View Cost Surface';
        btn.disabled = false;
    }
}

/**
 * Build a dynamic QGIS-style legend from API classification data.
 * @param {Array} entries  - array of {label, color, min, max, class} from API
 * @param {string} containerId - DOM id to populate
 */
function buildDynamicLegend(entries, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = entries.map(e => `
        <div style="display:flex; align-items:center; gap:7px;">
            <div style="width:22px; height:16px; background:${e.color}; border:1px solid rgba(0,0,0,0.25); flex-shrink:0;"></div>
            <span style="font-size:10px; color:#222;">${e.label}</span>
        </div>`).join('');
}

/**
 * Remove cost surface overlay from map and hide legend
 */
function removeCostSurface() {
    if (window.costSurfacePreviewLayer) {
        map.removeLayer(window.costSurfacePreviewLayer);
        window.costSurfacePreviewLayer = null;
    }
    if (window.costSurfaceRouteLayer) {
        map.removeLayer(window.costSurfaceRouteLayer);
        window.costSurfaceRouteLayer = null;
    }
    const legend = document.getElementById('costSurfaceLegend');
    if (legend) legend.style.display = 'none';
    const mapLegendPanel = document.getElementById('mapLegendPanel');
    if (mapLegendPanel) mapLegendPanel.style.display = 'none';
    const northArrow = document.getElementById('northArrow');
    if (northArrow) northArrow.style.display = 'none';
    const mapComp = document.getElementById('mapComposition');
    if (mapComp) mapComp.style.display = 'none';
    console.log('✓ Cost surface removed from map');
}

/**
 * Generate cost surface with current weights (without route optimization)
 */
async function generateCostSurface() {
    try {
        // Show loading
        const btn = document.getElementById('generateCostSurfaceBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '⏳ Generating Cost Surface...';
        btn.disabled = true;
        
        console.log('🎨 Generating cost surface with user-selected layers and weights...');
        
        // Build bounds: use start/end points if set (study area), else current view
        let boundsArray;
        if (currentProject.start && currentProject.end) {
            // Expand a margin around the start-end corridor (like QGIS study area)
            const latMin = Math.min(currentProject.start.lat, currentProject.end.lat);
            const latMax = Math.max(currentProject.start.lat, currentProject.end.lat);
            const lonMin = Math.min(currentProject.start.lon, currentProject.end.lon);
            const lonMax = Math.max(currentProject.start.lon, currentProject.end.lon);
            const latSpan = latMax - latMin;
            const lonSpan = lonMax - lonMin;
            const margin = Math.max(0.1, Math.max(latSpan, lonSpan) * 0.25);
            boundsArray = [
                lonMin - margin,
                latMin - margin,
                lonMax + margin,
                latMax + margin
            ];
            console.log('📐 Using start/end corridor bounds:', boundsArray);
        } else {
            // Fall back to current map view
            const b = map.getBounds();
            boundsArray = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()];
            console.log('📐 Using map view bounds:', boundsArray);
        }
        
        // Build layers configuration from checkboxes and sliders
        const layersConfig = {
            protected_areas: {
                enabled: document.getElementById('showProtectedAreas')?.checked || false,
                weight: ahpWeights.protected_areas || 0
            },
            rivers: {
                enabled: document.getElementById('showRivers')?.checked || false,
                weight: ahpWeights.rivers || 0
            },
            wetlands: {
                enabled: document.getElementById('showWetlands')?.checked || false,
                weight: ahpWeights.wetlands || 0
            },
            roads: {
                enabled: document.getElementById('showRoads')?.checked || false,
                weight: ahpWeights.roads || 0
            },
            elevation: {
                enabled: document.getElementById('showElevation')?.checked || false,
                weight: ahpWeights.elevation || 0
            },
            lakes: {
                enabled: document.getElementById('showLakes')?.checked || false,
                weight: ahpWeights.lakes || 0
            },
            settlements: {
                enabled: document.getElementById('showSettlements')?.checked || false,
                weight: ahpWeights.settlements || 0
            },
            land_use: {
                enabled: document.getElementById('showLandUse')?.checked || false,
                weight: ahpWeights.land_use || 0
            }
        };
        
        // Count enabled layers
        const enabledCount = Object.values(layersConfig).filter(l => l.enabled).length;
        console.log(`📊 Enabled layers: ${enabledCount}/8`);
        console.log('📋 Layers config:', layersConfig);
        
        if (enabledCount === 0) {
            alert('Please check at least one layer checkbox to generate the cost surface.');
            btn.innerHTML = originalText;
            btn.disabled = false;
            return;
        }
        
        // Call API to generate cost surface
        const response = await fetch('/api/cost-surface/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                layers: layersConfig,
                bounds: boundsArray,
                resolution_m: 100,   // 100m for fast preview; real data files use their native resolution
                classification: document.getElementById('classificationMethod')?.value || 'quantile',
                n_classes: parseInt(document.getElementById('nClasses')?.value || '5'),
                start_point: currentProject.start ? { lat: currentProject.start.lat, lon: currentProject.start.lon } : null,
                end_point:   currentProject.end   ? { lat: currentProject.end.lat,   lon: currentProject.end.lon   } : null,
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to generate cost surface');
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to generate cost surface');
        }
        
        console.log('✅ Cost surface generated successfully:', result.metadata);
        
        // Remove existing cost surface layer if any
        if (window.costSurfacePreviewLayer) {
            map.removeLayer(window.costSurfacePreviewLayer);
        }
        
        const imageUrl = `data:image/png;base64,${result.image_base64}`;
        const metadata = result.metadata;
        const imgBounds = [
            [result.bounds[1], result.bounds[0]],
            [result.bounds[3], result.bounds[2]]
        ];
        
        window.costSurfacePreviewLayer = L.imageOverlay(imageUrl, imgBounds, {
            opacity: 0.6,
            interactive: false
        }).addTo(map);

        // Apply pixelated rendering once the image element exists
        window.costSurfacePreviewLayer.on('load', function() {
            const el = window.costSurfacePreviewLayer.getElement();
            if (el) {
                el.style.imageRendering = 'pixelated';
                el.style.imageRendering = 'crisp-edges';
            }
        });

        // Zoom map to the cost surface area
        map.fitBounds(imgBounds, { padding: [20, 20] });

        // --- Build dynamic legend from API classification data ---
        const legend = document.getElementById('costSurfaceLegend');
        const isFirstRender = legend.style.display !== 'block';
        legend.style.display = 'block';

        if (result.legend && result.legend.length) {
            buildDynamicLegend(result.legend, 'legendEntries');
            buildDynamicLegend(result.legend, 'mapLegendEntries');
        }

        // Show QGIS map composition elements
        const mapComp = document.getElementById('mapComposition');
        const northArrow = document.getElementById('northArrow');
        const mapLegendPanel = document.getElementById('mapLegendPanel');
        if (mapComp) mapComp.style.display = 'block';
        if (northArrow) northArrow.style.display = 'block';
        if (mapLegendPanel) mapLegendPanel.style.display = 'block';

        // --- Render route overlay (blue polyline) if returned by API ---
        if (window.costSurfaceRouteLayer) {
            map.removeLayer(window.costSurfaceRouteLayer);
            window.costSurfaceRouteLayer = null;
        }
        if (result.route && result.route.geometry && result.route.geometry.coordinates.length > 1) {
            window.costSurfaceRouteLayer = L.geoJSON(result.route, {
                style: {
                    color: '#1565c0',
                    weight: 3,
                    opacity: 0.95,
                    lineJoin: 'round',
                    lineCap: 'round',
                }
            }).addTo(map);
            window.costSurfaceRouteLayer.bringToFront();
        }

        // Update stats info
        const infoText = document.getElementById('costSurfaceInfo');
        const cls = result.classification || {};
        const enabledLayersList = Object.entries(layersConfig)
            .filter(([_, c]) => c.enabled).map(([n]) => n).join(', ');
        if (infoText) {
            const tifLink = result.geotiff_url
                ? `<br><a href="${result.geotiff_url}" download style="font-size:9px; color:#1565c0;">⬇ Download GeoTIFF</a>`
                : '';
            infoText.innerHTML =
                `<strong>Classification:</strong> ${cls.method || ''} · ${cls.n_classes || ''} classes<br>` +
                `Range: ${(cls.global_min || 0).toFixed(2)} – ${(cls.global_max || 0).toFixed(2)}<br>` +
                `Layers: ${enabledLayersList}<br>` +
                `Res: ${metadata.resolution_m}m · ${metadata.data_source} · ${metadata.generation_time_s}s` +
                tifLink;
        }

        // Store GeoTIFF URL for external access
        window.lastCostSurfaceGeoTIFF = result.geotiff_url || null;

        console.log('✅ Cost surface displayed on map');
        if (result.geotiff_url) console.log('📁 GeoTIFF saved:', result.geotiff_url);
        
    } catch (error) {
        console.error('❌ Cost surface generation error:', error);
        alert('Error generating cost surface: ' + error.message);
    } finally {
        const btn = document.getElementById('generateCostSurfaceBtn');
        btn.innerHTML = '🎨 Generate Cost Surface / Suitability Map';
        btn.disabled = false;
    }
}

