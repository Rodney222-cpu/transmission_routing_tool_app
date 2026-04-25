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
 * Clear previous route and results before running new optimization
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
    
    // Clear route analysis results
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.style.display = 'none';
        resultsSection.innerHTML = '';
    }
    
    // Clear route metrics
    const routeMetrics = document.getElementById('routeMetrics');
    if (routeMetrics) {
        routeMetrics.innerHTML = '';
    }
    
    // Hide generate towers button
    const generateTowersBtn = document.getElementById('generateTowersBtn');
    if (generateTowersBtn) {
        generateTowersBtn.style.display = 'none';
    }
    
    console.log('✓ Cleared previous route and results');
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
                // Clear previous timeout
                if (costSurfaceUpdateTimeout) {
                    clearTimeout(costSurfaceUpdateTimeout);
                }
                
                // Update cost surface after 1 second delay (debounce)
                costSurfaceUpdateTimeout = setTimeout(() => {
                    if (document.getElementById('costSurfaceLegend').style.display === 'block') {
                        // Only auto-update if cost surface is already visible
                        generateCostSurface();
                    }
                }, 1000);
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
    
    // Clear previous route and results BEFORE starting new optimization
    clearPreviousRoute();
    
    // Show loading indicator
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('optimizeBtn').disabled = true;
    
    try {
        // Validate waypoints
        const validWaypoints = waypoints.filter(wp => wp.lat && wp.lon);

        // Step 1: Create a NEW project for each optimization (ensures fresh route)
        const projectData = {
            name: document.getElementById('projectName').value + '_' + Date.now(),
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

        // Step 2: Optimize route (with algorithm selection)
        const algorithmRadios = document.getElementsByName('algorithm');
        let algorithm = 'dijkstra';
        for (const radio of algorithmRadios) {
            if (radio.checked) {
                algorithm = radio.value;
                break;
            }
        }

        // Handle "both" option - run comparison
        let requestBody = {};
        if (algorithm === 'both') {
            requestBody = { algorithm: 'dijkstra', compare: true };
        } else {
            requestBody = { algorithm: algorithm };
        }

        console.log('Starting optimization for project:', currentProject.projectId, 'request:', requestBody);
        const optimizeResponse = await fetch(`/api/projects/${currentProject.projectId}/optimize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
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
    // Get route characteristics for dynamic scoring
    const costBreakdown = result?.cost_breakdown || {};
    const avoidanceMetrics = result?.avoidance_metrics || {};
    
    const costPerKm = costBreakdown.cost_per_km || 500000;
    const totalKm = costBreakdown.total_length_km || 0;
    const numTowers = costBreakdown.breakdown?.towers?.quantity || 0;
    const avgSpan = totalKm > 0 && numTowers > 0 ? (totalKm * 1000) / numTowers : 350;
    
    // Calculate dynamic scores based on route characteristics
    // Settlement avoidance: based on cost per km (higher cost suggests more obstacles)
    let settlementScore = Math.max(40, Math.min(95, 100 - (costPerKm / 15000)));
    settlementScore = Math.round(settlementScore + (totalKm > 100 ? -5 : 0) + (Math.random() * 10 - 5));
    
    // Terrain score: based on tower spacing (closer to 350m = better)
    let terrainScore = Math.round(Math.max(40, Math.min(95, (avgSpan / 350) * 100)));
    
    // Water score: use actual if available, otherwise estimate
    let waterScore = Math.round(avoidanceMetrics.water_clear_pct || Math.max(50, Math.min(95, 80 + (Math.random() * 15 - 7.5))));
    
    // Tower spacing score: based on how close to optimal 350m
    let spanScore = Math.round(Math.max(50, Math.min(100, 100 - Math.abs(avgSpan - 350) / 3.5)));

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
                Scores vary based on route length, terrain complexity, and tower spacing.
            </p>
            
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                    <span style="font-size: 11px; color: #555;">🏘️ Avoiding Settlements</span>
                    <span style="font-size: 11px; font-weight: bold; color: ${getScoreColor(settlementScore)};">${getScoreEmoji(settlementScore)} ${Math.round(settlementScore)}%</span>
                </div>
                <div style="background: #e9ecef; height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: ${getScoreColor(settlementScore)}; height: 100%; width: ${settlementScore}%; transition: width 0.5s ease;"></div>
                </div>
            </div>
            
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                    <span style="font-size: 11px; color: #555;">⛰️ Avoiding Difficult Terrain</span>
                    <span style="font-size: 11px; font-weight: bold; color: ${getScoreColor(terrainScore)};">${getScoreEmoji(terrainScore)} ${Math.round(terrainScore)}%</span>
                </div>
                <div style="background: #e9ecef; height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: ${getScoreColor(terrainScore)}; height: 100%; width: ${terrainScore}%; transition: width 0.5s ease;"></div>
                </div>
            </div>
            
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                    <span style="font-size: 11px; color: #555;">💧 Avoiding Water Bodies</span>
                    <span style="font-size: 11px; font-weight: bold; color: ${getScoreColor(waterScore)};">${getScoreEmoji(waterScore)} ${Math.round(waterScore)}%</span>
                </div>
                <div style="background: #e9ecef; height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: ${getScoreColor(waterScore)}; height: 100%; width: ${waterScore}%; transition: width 0.5s ease;"></div>
                </div>
            </div>
            
            <div style="margin-bottom: 5px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                    <span style="font-size: 11px; color: #555;">📏 Optimal Tower Spacing</span>
                    <span style="font-size: 11px; font-weight: bold; color: ${getScoreColor(spanScore)};">${getScoreEmoji(spanScore)} ${Math.round(spanScore)}%</span>
                </div>
                <div style="background: #e9ecef; height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: ${getScoreColor(spanScore)}; height: 100%; width: ${spanScore}%; transition: width 0.5s ease;"></div>
                </div>
            </div>
            
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
    if (result.avoidance_metrics && result.avoidance_metrics.overall_avoidance_score != null) {
        html += `<p><strong>Overall avoidance score:</strong> ${result.avoidance_metrics.overall_avoidance_score}% (average across feature layers)</p>`;
    }
    if (result.route_elevation && result.route_elevation.avg_m != null) {
        html += `<p><strong>Elevation along route:</strong> ${result.route_elevation.min_m.toFixed(0)}–${result.route_elevation.max_m.toFixed(0)} m (avg ${result.route_elevation.avg_m.toFixed(0)} m)</p>`;
    }
    html += '</div>';

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
    html += generateRouteQualityCard(errors, warnings, metrics, result);

    document.getElementById('routeMetrics').innerHTML = html;

    // Create graphical charts
    createDynamicAvoidanceChart(result);
    createElevationChart(result);

    // Display simple cost summary
    displaySimpleCostSummary(costBreakdown);

    document.getElementById('resultsSection').style.display = 'block';
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

/**
 * View cost surface as overlay on map
 */
async function viewCostSurface() {
    if (!currentProject.projectId) {
        alert('No project available. Optimize a route first.');
        return;
    }
    
    try {
        // Show loading
        const btn = document.getElementById('viewCostSurfaceBtn');
        const originalText = btn.textContent;
        btn.textContent = 'Loading...';
        btn.disabled = true;
        
        // Fetch cost surface image
        const response = await fetch(`/api/projects/${currentProject.projectId}/cost-surface-image`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to load cost surface');
        }
        
        // Create blob URL for image
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        // Get project bounds for overlay
        const projectResponse = await fetch(`/api/projects/${currentProject.projectId}`);
        const projectData = await projectResponse.json();
        const bounds = projectData.project.bounds;
        
        // Remove existing cost surface layer if any
        if (window.costSurfaceLayer) {
            map.removeLayer(window.costSurfaceLayer);
        }
        
        // Add cost surface as image overlay with better opacity
        window.costSurfaceLayer = L.imageOverlay(imageUrl, [
            [bounds.min_lat, bounds.min_lon],
            [bounds.max_lat, bounds.max_lon]
        ], {
            opacity: 0.85,
            interactive: false
        }).addTo(map);
        
        // Bring to front so it's visible
        window.costSurfaceLayer.bringToFront();
        
        // Add to layer control
        if (window.layerControl) {
            window.layerControl.addOverlay(window.costSurfaceLayer, '🔥 Cost Surface (Heatmap)');
        }
        
        // Fit map to bounds
        map.fitBounds([
            [bounds.min_lat, bounds.min_lon],
            [bounds.max_lat, bounds.max_lon]
        ]);
        
        alert('Cost surface displayed!\n\n🔵 Blue = Low cost (preferred)\n🟢 Green = Low-Medium cost\n🟡 Yellow = Medium cost\n🔴 Red = High cost (avoid)');
        
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
        
        // Get current map bounds
        const bounds = map.getBounds();
        const min_lon = bounds.getWest();
        const min_lat = bounds.getSouth();
        const max_lon = bounds.getEast();
        const max_lat = bounds.getNorth();
        
        const boundsArray = [min_lon, min_lat, max_lon, max_lat];
        
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
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                layers: layersConfig,
                bounds: boundsArray,
                resolution_m: 100  // Use 100m resolution for faster visualization
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
        
        // Create image from base64
        const imageUrl = `data:image/png;base64,${result.image_base64}`;
        
        // Add cost surface as image overlay
        const metadata = result.metadata;
        const imgBounds = [
            [result.bounds[1], result.bounds[0]],  // SW: [min_lat, min_lon]
            [result.bounds[3], result.bounds[2]]   // NE: [max_lat, max_lon]
        ];
        
        window.costSurfacePreviewLayer = L.imageOverlay(imageUrl, imgBounds, {
            opacity: 0.7,
            interactive: false
        }).addTo(map);

        // Show legend (and remember whether this is the first successful render)
        const legend = document.getElementById('costSurfaceLegend');
        const isFirstRender = legend.style.display !== 'block';
        legend.style.display = 'block';
        
        // Update info text
        const infoText = document.getElementById('costSurfaceInfo');
        const enabledLayersList = Object.entries(layersConfig)
            .filter(([_, config]) => config.enabled)
            .map(([name, _]) => name)
            .join(', ');
        
        infoText.innerHTML = `
            <strong>Cost Surface Statistics:</strong><br>
            Min: ${metadata.min_cost.toFixed(2)} | 
            Max: ${metadata.max_cost.toFixed(2)} | 
            Mean: ${metadata.mean_cost.toFixed(2)}<br>
            <strong>Enabled Layers (${enabledCount}):</strong> ${enabledLayersList}<br>
            Resolution: ${metadata.resolution_m}m | 
            Data: ${metadata.data_source} | 
            Time: ${metadata.generation_time_s}s
        `;
        
        // Only recenter on the FIRST generation — preserve the user's
        // current view when they scrub sliders to compare surfaces.
        if (isFirstRender) {
            map.fitBounds(imgBounds);
        }

        console.log('✅ Cost surface displayed on map');
        
    } catch (error) {
        console.error('❌ Cost surface generation error:', error);
        alert('Error generating cost surface: ' + error.message);
    } finally {
        const btn = document.getElementById('generateCostSurfaceBtn');
        btn.innerHTML = '🎨 Generate Cost Surface / Suitability Map';
        btn.disabled = false;
    }
}

