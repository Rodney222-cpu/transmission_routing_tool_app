"""
Example: Using QGIS-Style Routing Workflow in Your Application

This shows how the QGIS methodology is integrated into your transmission line routing tool.
"""

from app.optimizer.cost_surface import CostSurfaceGenerator
from app.optimizer.qgis_routing_workflow import QGISRoutingWorkflow
import numpy as np


def example_qgis_routing_workflow():
    """
    Complete QGIS-style transmission line routing workflow
    """
    
    # ==========================================
    # STEP 1: Define Project Parameters
    # ==========================================
    print("=" * 60)
    print("QGIS-STYLE TRANSMISSION LINE ROUTING WORKFLOW")
    print("=" * 60)
    
    # Uganda bounds (example: Kampala to Jinja)
    bounds = [32.0, 0.0, 33.5, 1.0]  # [min_lon, min_lat, max_lon, max_lat]
    
    # Start and end points (lat/lon)
    start_point = {'lat': 0.3136, 'lon': 32.5811}  # Kampala
    end_point = {'lat': 0.4244, 'lon': 33.2042}    # Jinja
    
    # AHP Weights (Multi-Criteria Evaluation)
    ahp_weights = {
        'topography': 0.25,        # Avoid steep slopes
        'land_use': 0.30,          # Avoid forests, urban areas
        'settlements': 0.20,       # Avoid towns/villages
        'protected_areas': 0.15,   # Avoid parks/reserves
        'water': 0.10              # Avoid rivers/wetlands
    }
    
    print(f"\n📍 Start: {start_point['lat']}, {start_point['lon']} (Kampala)")
    print(f"📍 End: {end_point['lat']}, {end_point['lon']} (Jinja)")
    print(f"⚖️  AHP Weights: {ahp_weights}")
    
    # ==========================================
    # STEP 2: Generate Cost Surface (QGIS MCE)
    # ==========================================
    print("\n" + "=" * 60)
    print("STEP 1: MULTI-CRITERIA EVALUATION (MCE)")
    print("QGIS Tool: Raster Calculator / r.mapcalc")
    print("=" * 60)
    
    # In real application, this loads your GIS data
    # layers_data = {
    #     'dem': dem_array,
    #     'land_use': landuse_array,
    #     'settlements': settlements_array,
    #     'protected_areas': protected_array,
    #     'roads': roads_array
    # }
    
    # For example, we'll create a sample cost surface
    print("\n📊 Generating composite cost surface...")
    print("   Combining: Topography + Land Use + Settlements + Protected Areas + Water")
    
    # Simulated cost surface (in real app, this comes from CostSurfaceGenerator)
    cost_surface = np.random.uniform(1, 10, size=(100, 150))
    
    print(f"   ✓ Cost surface shape: {cost_surface.shape}")
    print(f"   ✓ Cost range: {cost_surface.min():.2f} - {cost_surface.max():.2f}")
    
    # ==========================================
    # STEP 3: Cost Distance Analysis (QGIS r.cost)
    # ==========================================
    print("\n" + "=" * 60)
    print("STEP 2: COST DISTANCE ANALYSIS")
    print("QGIS Tool: r.cost / Cost Distance Analysis")
    print("=" * 60)
    
    # Initialize QGIS workflow
    workflow = QGISRoutingWorkflow()
    
    # Convert lat/lon to grid coordinates
    # (In real app, this uses proper coordinate transformation)
    start_row, start_col = 50, 75   # Example grid coordinates
    end_row, end_col = 20, 120
    
    print(f"\n🔍 Calculating accumulated cost from start point...")
    print(f"   Start: ({start_row}, {start_col})")
    print(f"   This calculates the cheapest path to EVERY cell...")
    
    # Calculate cost distance (like QGIS r.cost)
    accumulated_cost, backlink_direction = workflow.calculate_cost_distance(
        cost_surface,
        start_points=[(start_row, start_col)]
    )
    
    print(f"   ✓ Accumulated cost surface generated")
    print(f"   ✓ Back-link direction surface generated")
    print(f"   ✓ Cost at end point: {accumulated_cost[end_row, end_col]:.2f}")
    
    # ==========================================
    # STEP 4: Extract Least-Cost Path (QGIS r.drain)
    # ==========================================
    print("\n" + "=" * 60)
    print("STEP 3: LEAST-COST PATH EXTRACTION")
    print("QGIS Tool: r.drain / Least Cost Path plugin")
    print("=" * 60)
    
    print(f"\n🛤️  Extracting optimal path from end to start...")
    print(f"   Following back-link directions...")
    
    # Extract least-cost path (like QGIS r.drain)
    path = workflow.extract_least_cost_path((end_row, end_col))
    
    print(f"   ✓ Path extracted with {len(path)} points")
    print(f"   ✓ Path length: {len(path)} cells")
    
    # ==========================================
    # STEP 5: Generate Corridor (QGIS Buffer)
    # ==========================================
    print("\n" + "=" * 60)
    print("STEP 4: CORRIDOR ANALYSIS")
    print("QGIS Tool: Buffer / Corridor mapping")
    print("=" * 60)
    
    print(f"\n📏 Generating 60m corridor around route...")
    print(f"   (30m each side - Right-of-Way)")
    
    # Generate corridor
    corridor_mask = workflow.generate_route_corridor(path, width_cells=5)
    
    corridor_area = np.sum(corridor_mask)
    print(f"   ✓ Corridor generated")
    print(f"   ✓ Corridor area: {corridor_area} cells")
    
    # ==========================================
    # STEP 6: Environmental Impact (QGIS Zonal Stats)
    # ==========================================
    print("\n" + "=" * 60)
    print("STEP 5: ENVIRONMENTAL IMPACT ASSESSMENT")
    print("QGIS Tool: Zonal Statistics / Raster analysis")
    print("=" * 60)
    
    # Simulated environmental layers
    environmental_layers = {
        'forests': np.random.uniform(1, 10, size=(100, 150)),
        'wetlands': np.random.uniform(1, 10, size=(100, 150)),
        'protected_areas': np.random.uniform(1, 10, size=(100, 150)),
        'settlements': np.random.uniform(1, 10, size=(100, 150))
    }
    
    print(f"\n🌍 Calculating environmental impact...")
    
    # Calculate impact
    impact_scores, total_impact = workflow.calculate_environmental_impact(
        path,
        environmental_layers
    )
    
    print(f"   ✓ Impact scores calculated:")
    for layer_name, scores in impact_scores.items():
        print(f"     - {layer_name}: Mean={scores['mean']:.2f}, Max={scores['max']:.2f}")
    print(f"   ✓ Total Impact Score: {total_impact:.2f}")
    
    # ==========================================
    # STEP 7: Route Statistics
    # ==========================================
    print("\n" + "=" * 60)
    print("STEP 6: ROUTE STATISTICS")
    print("QGIS Tool: Path analysis / Statistics")
    print("=" * 60)
    
    print(f"\n📊 Calculating comprehensive route statistics...")
    
    # Calculate statistics
    stats = workflow.calculate_route_statistics(path, cost_surface)
    
    print(f"   ✓ Route Statistics:")
    print(f"     - Total Length: {stats['total_length_cells']} cells")
    print(f"     - Mean Cost: {stats['mean_cost']:.2f}")
    print(f"     - Max Cost: {stats['max_cost']:.2f}")
    print(f"     - Min Cost: {stats['min_cost']:.2f}")
    print(f"     - Total Cost: {stats['total_cost']:.2f}")
    
    # ==========================================
    # STEP 8: Route Smoothing
    # ==========================================
    print("\n" + "=" * 60)
    print("STEP 7: ROUTE SMOOTHING")
    print("QGIS Tool: Line smoothing / Generalization")
    print("=" * 60)
    
    print(f"\n✨ Smoothing route to reduce zigzag...")
    
    # Smooth route
    smoothed_path = workflow.smooth_route(path, iterations=3)
    
    print(f"   ✓ Route smoothed (3 iterations)")
    print(f"   ✓ Original points: {len(path)}")
    print(f"   ✓ Smoothed points: {len(smoothed_path)}")
    
    # ==========================================
    # FINAL RESULTS
    # ==========================================
    print("\n" + "=" * 60)
    print("✅ QGIS-STYLE ROUTING COMPLETE!")
    print("=" * 60)
    
    print(f"\n📋 SUMMARY:")
    print(f"   ✓ Cost Surface: Generated (AHP-weighted)")
    print(f"   ✓ Cost Distance: Calculated (accumulated)")
    print(f"   ✓ Optimal Path: Extracted ({len(path)} points)")
    print(f"   ✓ Corridor: Generated (60m width)")
    print(f"   ✓ Environmental Impact: Assessed ({total_impact:.2f})")
    print(f"   ✓ Statistics: Calculated")
    print(f"   ✓ Route: Smoothed")
    
    print(f"\n🎯 This is the EXACT methodology QGIS uses!")
    print(f"   - Multi-Criteria Evaluation ✓")
    print(f"   - Cost Distance Analysis ✓")
    print(f"   - Back-Link Direction ✓")
    print(f"   - Least-Cost Path Extraction ✓")
    print(f"   - Corridor Analysis ✓")
    print(f"   - Environmental Impact ✓")
    
    print("\n" + "=" * 60)
    
    return {
        'cost_surface': cost_surface,
        'accumulated_cost': accumulated_cost,
        'backlink_direction': backlink_direction,
        'path': path,
        'smoothed_path': smoothed_path,
        'corridor': corridor_mask,
        'impact_scores': impact_scores,
        'total_impact': total_impact,
        'statistics': stats
    }


if __name__ == '__main__':
    # Run the example
    results = example_qgis_routing_workflow()
    
    print("\n💡 To integrate this into your API:")
    print("   1. Use CostSurfaceGenerator to create cost surface")
    print("   2. Use QGISRoutingWorkflow for pathfinding")
    print("   3. Return results to frontend")
    print("   4. Display on map with Leaflet")
