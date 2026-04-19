"""
Test script to verify checkbox layer functionality
Run this to check if all GIS layers can be loaded properly
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from app.services.uganda_gis_loader import UgandaGISLoader

def test_layer_loading():
    """Test loading all GIS layers"""
    
    print("=" * 60)
    print("TESTING CHECKBOX LAYER FUNCTIONALITY")
    print("=" * 60)
    
    # Initialize the loader
    config = Config()
    loader = UgandaGISLoader(config)
    
    # Test bounds (Uganda)
    bounds = (29.5, 0.5, 35.0, 4.5)
    
    # Layers to test
    layers_to_test = [
        'uganda_districts',
        'protected_areas',
        'rivers',
        'wetlands',
        'lakes',
        'roads',
        'elevation',
        'settlements',
        'hospitals',
        'commercial',
        'land_use'
    ]
    
    results = {}
    
    for layer_name in layers_to_test:
        print(f"\n{'='*60}")
        print(f"📍 Testing layer: {layer_name}")
        print(f"{'='*60}")
        
        try:
            geojson = loader.load_layer_geojson(layer_name, bounds)
            
            if geojson is None:
                print(f"❌ FAILED: {layer_name} - No data returned")
                results[layer_name] = {'status': 'FAILED', 'features': 0, 'error': 'No data'}
                continue
            
            feature_count = len(geojson.get('features', []))
            print(f"✅ SUCCESS: {layer_name} loaded with {feature_count} features")
            
            # Check feature types
            feature_types = {}
            for feature in geojson.get('features', [])[:5]:  # Check first 5
                geom_type = feature.get('geometry', {}).get('type', 'Unknown')
                feature_types[geom_type] = feature_types.get(geom_type, 0) + 1
            
            print(f"   Sample geometry types: {feature_types}")
            
            results[layer_name] = {
                'status': 'SUCCESS',
                'features': feature_count,
                'geometry_types': feature_types
            }
            
        except Exception as e:
            print(f"❌ ERROR loading {layer_name}: {e}")
            import traceback
            traceback.print_exc()
            results[layer_name] = {'status': 'ERROR', 'features': 0, 'error': str(e)}
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results.values() if r['status'] == 'SUCCESS')
    failed_count = sum(1 for r in results.values() if r['status'] in ['FAILED', 'ERROR'])
    
    print(f"\n✅ Successful: {success_count}/{len(layers_to_test)}")
    print(f"❌ Failed: {failed_count}/{len(layers_to_test)}")
    
    print(f"\nDetailed Results:")
    for layer_name, result in results.items():
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"  {status_icon} {layer_name}: {result['features']} features - {result['status']}")
    
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")
    
    if success_count == len(layers_to_test):
        print("\n🎉 All layers are working correctly!")
        print("   Your checkbox layers should be fully functional.")
    else:
        print("\n⚠️ Some layers failed to load. Check the following:")
        for layer_name, result in results.items():
            if result['status'] != 'SUCCESS':
                print(f"   - {layer_name}: {result.get('error', 'Unknown error')}")
    
    print(f"\n{'='*60}")
    
    return results


if __name__ == '__main__':
    results = test_layer_loading()
