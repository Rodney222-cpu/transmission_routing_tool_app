"""
Convert Shapefiles to GeoJSON for layers that are missing GeoJSON files.
This enables the GIS data loader to use these layers in route optimization.
"""
import os
import geopandas as gpd

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')

# Define conversions needed
conversions = [
    {
        'name': 'protected_areas',
        'shp_folder': os.path.join(DATA_FOLDER, 'protected_areas'),
        'shp_file': 'protected_areas_60.shp',
        'output': os.path.join(DATA_FOLDER, 'protected_areas', 'protected_areas.geojson')
    },
    {
        'name': 'rivers',
        'shp_folder': os.path.join(DATA_FOLDER, 'rivers'),
        'shp_file': 'Ug_Rivers-original.shp',
        'output': os.path.join(DATA_FOLDER, 'rivers', 'rivers.geojson')
    },
    {
        'name': 'wetlands',
        'shp_folder': os.path.join(DATA_FOLDER, 'wetlands'),
        'shp_file': 'Wetlands1994.shp',
        'output': os.path.join(DATA_FOLDER, 'wetlands', 'wetlands.geojson')
    },
    {
        'name': 'lakes',
        'shp_folder': os.path.join(DATA_FOLDER, 'lakes'),
        'shp_file': 'Ug_Lakes.shp',
        'output': os.path.join(DATA_FOLDER, 'lakes', 'lakes.geojson')
    },
]

def convert_shapefile_to_geojson(conversion):
    """Convert a single Shapefile to GeoJSON"""
    shp_path = os.path.join(conversion['shp_folder'], conversion['shp_file'])
    output_path = conversion['output']
    
    # Check if output already exists
    if os.path.exists(output_path):
        print(f"✓ {conversion['name']}: GeoJSON already exists, skipping")
        return True
    
    # Check if source Shapefile exists
    if not os.path.exists(shp_path):
        print(f"❌ {conversion['name']}: Shapefile not found at {shp_path}")
        return False
    
    try:
        print(f"🔄 Converting {conversion['name']}...")
        
        # Read Shapefile
        gdf = gpd.read_file(shp_path)
        print(f"  📊 Loaded {len(gdf)} features from Shapefile")
        print(f"  📐 CRS: {gdf.crs}")
        
        # Convert to WGS84 (EPSG:4326) if needed
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            print(f"  🔄 Converting CRS from {gdf.crs.to_epsg()} to EPSG:4326")
            gdf = gdf.to_crs(epsg=4326)
        
        # Save as GeoJSON
        gdf.to_file(output_path, driver='GeoJSON')
        print(f"✅ {conversion['name']}: Saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ {conversion['name']}: Conversion failed - {e}")
        return False

def main():
    print("=" * 60)
    print("Converting Shapefiles to GeoJSON")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for conversion in conversions:
        result = convert_shapefile_to_geojson(conversion)
        if result:
            if os.path.exists(conversion['output']):
                success_count += 1
            else:
                skip_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ⏭️  Skipped (already exists): {skip_count}")
    print(f"  ❌ Failed: {fail_count}")
    print("=" * 60)
    
    if fail_count > 0:
        print("\n⚠️  Some conversions failed. Check the errors above.")
    else:
        print("\n🎉 All conversions completed successfully!")

if __name__ == '__main__':
    main()
