"""
Convert Uganda OSM Shapefiles to GeoJSON for use in the Transmission Routing Tool
This ensures all layers use real OpenStreetMap data for Uganda
"""

import os
import json
from pathlib import Path

try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False
    print("Warning: geopandas not installed. Trying alternative method...")

try:
    from shapely.geometry import mapping
    from shapely.wkb import loads as wkb_loads
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False


def convert_shapefile_to_geojson(shapefile_path, output_path):
    """Convert a shapefile to GeoJSON format"""
    if not HAS_GEOPANDAS:
        print(f"Cannot convert {shapefile_path}: geopandas not available")
        return False
    
    try:
        # Read shapefile
        gdf = gpd.read_file(shapefile_path)
        
        # Convert to WGS84 if needed
        if gdf.crs is not None and gdf.crs.to_string() != 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')
        
        # Save as GeoJSON
        gdf.to_file(output_path, driver='GeoJSON')
        print(f"✓ Converted: {os.path.basename(shapefile_path)} -> {os.path.basename(output_path)}")
        print(f"  Features: {len(gdf)}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to convert {shapefile_path}: {e}")
        return False


def convert_all_uganda_data():
    """Convert all Uganda OSM shapefiles to GeoJSON"""
    
    data_dir = Path("data")
    
    # Mapping of folders and their primary shapefiles
    conversions = [
        # Settlements - buildings
        {
            'folder': data_dir / 'settlements',
            'shapefile': 'gis_osm_buildings_a_free_1.shp',
            'output': 'uganda_settlements.geojson',
            'layer_name': 'settlements'
        },
        # Roads
        {
            'folder': data_dir / 'roads',
            'shapefile': 'gis_osm_roads_free_1.shp',
            'output': 'uganda_roads.geojson',
            'layer_name': 'roads'
        },
        # Water bodies
        {
            'folder': data_dir / 'waterbodies',
            'shapefile': 'gis_osm_water_a_free_1.shp',
            'output': 'uganda_water.geojson',
            'layer_name': 'water'
        },
        # Waterways (rivers)
        {
            'folder': data_dir / 'waterbodies',
            'shapefile': 'gis_osm_waterways_free_1.shp',
            'output': 'uganda_waterways.geojson',
            'layer_name': 'waterways'
        },
        # Forests/Natural areas
        {
            'folder': data_dir / 'forests',
            'shapefile': 'gis_osm_natural_a_free_1.shp',
            'output': 'uganda_forests.geojson',
            'layer_name': 'forests'
        },
        # Natural points
        {
            'folder': data_dir / 'forests',
            'shapefile': 'gis_osm_natural_free_1.shp',
            'output': 'uganda_natural.geojson',
            'layer_name': 'natural'
        },
        # Education facilities
        {
            'folder': data_dir / 'education',
            'shapefile': 'gis_osm_pois_a_free_1.shp',
            'output': 'uganda_education.geojson',
            'layer_name': 'education'
        },
        # Points of interest
        {
            'folder': data_dir / 'education',
            'shapefile': 'gis_osm_pois_free_1.shp',
            'output': 'uganda_pois.geojson',
            'layer_name': 'pois'
        },
        # Land use
        {
            'folder': data_dir / 'land_use',
            'shapefile': 'gis_osm_landuse_a_free_1.shp',
            'output': 'uganda_landuse.geojson',
            'layer_name': 'landuse'
        },
    ]
    
    print("=" * 70)
    print("UGANDA OSM DATA CONVERSION")
    print("Converting Shapefiles to GeoJSON for routing tool")
    print("=" * 70)
    print()
    
    success_count = 0
    failed_count = 0
    
    for conv in conversions:
        folder = conv['folder']
        shapefile = folder / conv['shapefile']
        output = folder / conv['output']
        
        print(f"\n[{conv['layer_name']}]")
        
        # Check if shapefile exists
        if not shapefile.exists():
            print(f"  Shapefile not found: {shapefile}")
            failed_count += 1
            continue
        
        # Check if already converted
        if output.exists():
            print(f"  GeoJSON already exists: {output}")
            success_count += 1
            continue
        
        # Convert
        if convert_shapefile_to_geojson(str(shapefile), str(output)):
            success_count += 1
        else:
            failed_count += 1
    
    print("\n" + "=" * 70)
    print("CONVERSION SUMMARY")
    print("=" * 70)
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")
    print()
    
    if failed_count > 0 and not HAS_GEOPANDAS:
        print("NOTE: Some conversions failed because geopandas is not installed.")
        print("Install it with: pip install geopandas")
    
    return success_count, failed_count


def verify_geojson_files():
    """Verify all GeoJSON files are valid and count features"""
    
    print("\n" + "=" * 70)
    print("VERIFYING GEOJSON FILES")
    print("=" * 70)
    print()
    
    data_dir = Path("data")
    
    geojson_files = [
        ('settlements', data_dir / 'settlements' / 'uganda_settlements.geojson'),
        ('roads', data_dir / 'roads' / 'uganda_roads.geojson'),
        ('water', data_dir / 'waterbodies' / 'uganda_water.geojson'),
        ('waterways', data_dir / 'waterbodies' / 'uganda_waterways.geojson'),
        ('forests', data_dir / 'forests' / 'uganda_forests.geojson'),
        ('landuse', data_dir / 'land_use' / 'uganda_landuse.geojson'),
    ]
    
    total_features = 0
    
    for layer_name, filepath in geojson_files:
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    features = data.get('features', [])
                    count = len(features)
                    total_features += count
                    print(f"✓ {layer_name:15s}: {count:8,} features - {filepath}")
            except Exception as e:
                print(f"✗ {layer_name:15s}: Error reading file - {e}")
        else:
            print(f"✗ {layer_name:15s}: File not found - {filepath}")
    
    print(f"\nTotal features across all layers: {total_features:,}")
    return total_features


if __name__ == "__main__":
    # First try to install geopandas if not available
    if not HAS_GEOPANDAS:
        print("Installing required package: geopandas...")
        import subprocess
        import sys
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "geopandas", "-q"])
            # Try importing again
            try:
                import geopandas as gpd
                HAS_GEOPANDAS = True
                print("✓ geopandas installed successfully")
            except ImportError:
                print("✗ Failed to install geopandas")
        except Exception as e:
            print(f"✗ Could not install geopandas: {e}")
    
    # Run conversion
    success, failed = convert_all_uganda_data()
    
    # Verify results
    verify_geojson_files()
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("1. Restart your Flask application to use the converted GeoJSON files")
    print("2. The app will now use real Uganda OSM data for all layers")
    print("3. Check the browser console to confirm 'real' data source")
