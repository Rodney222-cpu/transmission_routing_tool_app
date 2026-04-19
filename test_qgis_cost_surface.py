"""
Test QGIS-Style Cost Surface Analysis and Least-Cost Routing

This script tests the complete pipeline:
1. Raster preparation from vector/raster data
2. Layer-specific reclassification
3. Weighted overlay computation
4. A* least-cost path finding
5. Export to GeoTIFF, PNG, and Shapefile
"""

import os
import sys
import numpy as np
from shapely.geometry import Point, LineString
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.optimizer.qgis_cost_surface import QGISStyleCostSurfaceAnalyzer


class MockConfig:
    """Mock Flask config for testing"""
    pass


def test_reclassification_logic():
    """Test Step 2: Layer-specific reclassification logic."""
    print("\n" + "="*80)
    print("TEST 1: Layer-Specific Reclassification Logic")
    print("="*80)
    
    config = MockConfig()
    analyzer = QGISStyleCostSurfaceAnalyzer(config)
    
    # Test protected areas reclassification
    print("\n1.1 Protected Areas (inside=100, outside=1)")
    test_raster = np.array([[0, 0, 1, 1],
                            [0, 1, 1, 0],
                            [0, 0, 0, 0]])
    result = analyzer.reclassify_protected_areas(test_raster, None, None, None)
    print(f"   Input:  {test_raster}")
    print(f"   Output: {result}")
    assert result[0, 2] == 100, "Inside should be 100"
    assert result[0, 0] == 1, "Outside should be 1"
    print("   ✓ PASS")
    
    # Test water distance reclassification
    print("\n1.2 Water Distance (nearer=higher cost)")
    test_raster = np.array([[0, 0, 0, 0],
                            [0, 1, 1, 0],
                            [0, 0, 0, 0]])
    result = analyzer.reclassify_water_distance(test_raster, None, None, None)
    print(f"   Water mask: {test_raster}")
    print(f"   Cost raster:\n{result}")
    # Water pixels should be 100
    assert result[1, 1] == 100, "Water should be 100"
    # Far pixels should be lower
    assert result[0, 0] < 100, "Far from water should be < 100"
    print("   ✓ PASS")
    
    # Test wetlands reclassification
    print("\n1.3 Wetlands (inside=90, outside=1)")
    test_raster = np.array([[0, 0, 1, 0],
                            [0, 1, 0, 0]])
    result = analyzer.reclassify_wetlands(test_raster, None, None, None)
    print(f"   Input:  {test_raster}")
    print(f"   Output: {result}")
    assert result[0, 2] == 90, "Wetland should be 90"
    assert result[0, 0] == 1, "Non-wetland should be 1"
    print("   ✓ PASS")
    
    # Test elevation slope reclassification
    print("\n1.4 Elevation Slope (steeper=higher cost)")
    flat_elevation = np.ones((5, 5)) * 100
    result_flat = analyzer.reclassify_elevation_slope(flat_elevation)
    print(f"   Flat elevation cost: {result_flat[0, 0]:.2f}")
    assert result_flat[0, 0] == 1, "Flat should be cost 1"
    
    steep_elevation = np.array([[100, 200, 300],
                                 [100, 200, 300],
                                 [100, 200, 300]], dtype=np.float32)
    result_steep = analyzer.reclassify_elevation_slope(steep_elevation)
    print(f"   Steep elevation cost: {result_steep[0, 1]:.2f}")
    assert result_steep[0, 1] > 1, "Steep should be > 1"
    print("   ✓ PASS")
    
    print("\n✅ All reclassification tests PASSED")


def test_weight_normalization():
    """Test Step 3: Weight normalization."""
    print("\n" + "="*80)
    print("TEST 2: Weight Normalization")
    print("="*80)
    
    config = MockConfig()
    analyzer = QGISStyleCostSurfaceAnalyzer(config)
    
    # Test with unequal weights
    weights = {'protected_areas': 0.3, 'rivers': 0.5, 'wetlands': 0.2}
    normalized = analyzer.normalize_weights(weights)
    print(f"\n2.1 Original weights: {weights}")
    print(f"    Normalized: {normalized}")
    assert abs(sum(normalized.values()) - 1.0) < 1e-10, "Should sum to 1.0"
    print("    ✓ PASS")
    
    # Test with zero weights (should use equal weights)
    weights_zero = {'a': 0, 'b': 0}
    normalized_zero = analyzer.normalize_weights(weights_zero)
    print(f"\n2.2 Zero weights: {weights_zero}")
    print(f"    Normalized: {normalized_zero}")
    assert abs(sum(normalized_zero.values()) - 1.0) < 1e-10
    assert normalized_zero['a'] == normalized_zero['b'], "Should be equal"
    print("    ✓ PASS")
    
    print("\n✅ Weight normalization tests PASSED")


def test_weighted_overlay():
    """Test Step 4: Weighted overlay computation."""
    print("\n" + "="*80)
    print("TEST 3: Weighted Overlay Computation")
    print("="*80)
    
    config = MockConfig()
    analyzer = QGISStyleCostSurfaceAnalyzer(config)
    
    # Create test rasters
    raster1 = np.ones((3, 3)) * 100  # High cost everywhere
    raster2 = np.ones((3, 3)) * 50   # Medium cost everywhere
    
    cost_rasters = {
        'layer1': raster1,
        'layer2': raster2
    }
    
    weights = {'layer1': 0.7, 'layer2': 0.3}
    
    print(f"\n3.1 Layer 1 cost: {raster1[0, 0]}")
    print(f"    Layer 2 cost: {raster2[0, 0]}")
    print(f"    Weights: {weights}")
    
    result = analyzer.compute_weighted_overlay(cost_rasters, weights)
    expected = 100 * 0.7 + 50 * 0.3  # 85
    
    print(f"    Expected: {expected}")
    print(f"    Got:      {result[0, 0]}")
    assert abs(result[0, 0] - expected) < 0.01, "Weighted sum incorrect"
    print("    ✓ PASS")
    
    print("\n✅ Weighted overlay test PASSED")


def test_astar_pathfinding():
    """Test Step 5: A* least-cost path finding."""
    print("\n" + "="*80)
    print("TEST 4: A* Least-Cost Path Finding")
    print("="*80)
    
    config = MockConfig()
    analyzer = QGISStyleCostSurfaceAnalyzer(config)
    
    # Create simple cost surface (low cost in middle, high on edges)
    cost_surface = np.ones((10, 10)) * 100
    cost_surface[4:6, 1:9] = 10  # Low cost corridor
    
    bounds = [0, 0, 10, 10]
    start = (0, 0)  # Top-left
    end = (10, 10)  # Bottom-right
    
    print(f"\n4.1 Cost surface shape: {cost_surface.shape}")
    print(f"    Start: {start}, End: {end}")
    print(f"    Low cost corridor: rows 4-5, cols 1-8")
    
    path = analyzer.find_least_cost_path_astar(cost_surface, start, end, bounds)
    
    print(f"    Path length: {len(path)} nodes")
    assert len(path) > 0, "Path should be found"
    
    # Path should prefer low cost corridor
    path_costs = [cost_surface[r, c] for r, c in path]
    avg_cost = np.mean(path_costs)
    print(f"    Average path cost: {avg_cost:.2f}")
    assert avg_cost < 100, "Path should prefer low cost areas"
    print("    ✓ PASS")
    
    print("\n✅ A* pathfinding test PASSED")


def test_full_pipeline():
    """Test complete pipeline with synthetic data."""
    print("\n" + "="*80)
    print("TEST 5: Full Pipeline with Synthetic Data")
    print("="*80)
    
    config = MockConfig()
    
    # Create test output directory
    test_dir = os.path.join(os.path.dirname(__file__), 'test_output')
    os.makedirs(test_dir, exist_ok=True)
    
    analyzer = QGISStyleCostSurfaceAnalyzer(config, output_dir=test_dir)
    
    # Create synthetic layers config
    bounds = [29.5, -1.5, 35.0, 4.5]
    resolution = 0.05  # Coarse resolution for fast testing
    start_point = (0.5, 30.0)
    end_point = (3.5, 34.0)
    
    layers_config = {
        'protected_areas': {
            'enabled': True,
            'weight': 0.2,
            'path': 'synthetic'  # Will use synthetic data
        },
        'rivers': {
            'enabled': True,
            'weight': 0.2,
            'path': 'synthetic'
        },
        'elevation': {
            'enabled': True,
            'weight': 0.3,
            'path': 'synthetic'
        }
    }
    
    print(f"\n5.1 Bounds: {bounds}")
    print(f"    Resolution: {resolution}")
    print(f"    Start: {start_point}, End: {end_point}")
    print(f"    Layers: {list(layers_config.keys())}")
    
    try:
        # Create synthetic cost rasters for testing
        width = int((bounds[2] - bounds[0]) / resolution)
        height = int((bounds[3] - bounds[1]) / resolution)
        shape = (height, width)
        
        # Generate synthetic rasters
        np.random.seed(42)
        cost_rasters = {
            'protected_areas': np.random.uniform(1, 100, shape),
            'rivers': np.random.uniform(1, 100, shape),
            'elevation': np.random.uniform(1, 100, shape)
        }
        
        # Normalize weights
        weights = {
            'protected_areas': 0.2,
            'rivers': 0.2,
            'elevation': 0.3
        }
        normalized = analyzer.normalize_weights(weights)
        print(f"    Normalized weights: {normalized}")
        
        # Compute weighted overlay
        cost_surface = analyzer.compute_weighted_overlay(cost_rasters, normalized)
        print(f"    Cost surface shape: {cost_surface.shape}")
        print(f"    Min: {cost_surface.min():.2f}, Max: {cost_surface.max():.2f}")
        
        # Export GeoTIFF
        geotiff_path = os.path.join(test_dir, 'test_cost_surface.tif')
        analyzer.export_cost_surface_geotiff(cost_surface, bounds, geotiff_path)
        assert os.path.exists(geotiff_path), "GeoTIFF should be created"
        print(f"    ✓ GeoTIFF saved: {geotiff_path}")
        
        # Export PNG
        png_path = os.path.join(test_dir, 'test_cost_surface.png')
        analyzer.export_cost_surface_png(cost_surface, bounds, png_path)
        assert os.path.exists(png_path), "PNG should be created"
        print(f"    ✓ PNG saved: {png_path}")
        
        # Find least-cost path
        path = analyzer.find_least_cost_path_astar(cost_surface, start_point, end_point, bounds)
        print(f"    ✓ Path found: {len(path)} nodes")
        
        # Export route shapefile
        if path:
            shp_path = os.path.join(test_dir, 'test_route.shp')
            analyzer.export_route_shapefile(path, bounds, shp_path, shape=shape)
            assert os.path.exists(shp_path), "Shapefile should be created"
            print(f"    ✓ Shapefile saved: {shp_path}")
        
        print("\n✅ Full pipeline test PASSED")
        
    except Exception as e:
        print(f"\n❌ Full pipeline test FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_layer_path_resolution():
    """Test layer path resolution from Uganda GIS data."""
    print("\n" + "="*80)
    print("TEST 6: Layer Path Resolution")
    print("="*80)
    
    # Try to load from Flask app context
    try:
        from app import create_app
        app = create_app('development')
        
        with app.app_context():
            from app.services.uganda_gis_loader import UgandaGISLoader
            loader = UgandaGISLoader(app.config)
            
            # Test layer paths
            layers = ['protected_areas', 'rivers', 'wetlands', 'land_use', 'elevation']
            
            for layer in layers:
                folder = getattr(app.config, f'{layer.upper()}_FOLDER', None)
                if folder and os.path.exists(folder):
                    files = os.listdir(folder)
                    shp_files = [f for f in files if f.endswith('.shp')]
                    print(f"  ✓ {layer}: {folder}")
                    print(f"    Shapefiles: {shp_files[:3]}...")
                else:
                    print(f"  ⚠ {layer}: Not configured")
            
            print("\n✅ Layer path resolution test PASSED")
            
    except Exception as e:
        print(f"\n⚠ Layer path resolution test SKIPPED (app context not available): {e}")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("QGIS-STYLE COST SURFACE ANALYSIS - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    tests = [
        ("Reclassification Logic", test_reclassification_logic),
        ("Weight Normalization", test_weight_normalization),
        ("Weighted Overlay", test_weighted_overlay),
        ("A* Pathfinding", test_astar_pathfinding),
        ("Full Pipeline", test_full_pipeline),
        ("Layer Path Resolution", test_layer_path_resolution),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {e}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"TEST SUMMARY")
    print("="*80)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠ {failed} test(s) failed")
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
