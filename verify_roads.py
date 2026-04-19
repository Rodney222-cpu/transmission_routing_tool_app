import geopandas as gpd
import json

print("=" * 60)
print("TESTING ROADS DATA INTEGRITY")
print("=" * 60)

# Load original shapefile
print("\n1. Loading original shapefile...")
gdf_original = gpd.read_file('data/roads/Ug_Roads_UNRA_2012.shp')
print(f"   ✓ Original features: {len(gdf_original)}")
print(f"   ✓ Original columns: {gdf_original.columns.tolist()}")

# Convert to WGS84
print("\n2. Converting to WGS84...")
gdf_wgs84 = gdf_original.to_crs(epsg=4326)
print(f"   ✓ CRS: {gdf_wgs84.crs}")

# Simplify geometry
print("\n3. Simplifying geometry...")
gdf_simplified = gdf_wgs84.copy()
gdf_simplified['geometry'] = gdf_simplified['geometry'].simplify(0.0001)
print(f"   ✓ Features after simplification: {len(gdf_simplified)}")

# Convert to GeoJSON
print("\n4. Converting to GeoJSON...")
geojson_str = gdf_simplified.to_json(show_bbox=False)
geojson = json.loads(geojson_str)
print(f"   ✓ GeoJSON features: {len(geojson['features'])}")
print(f"   ✓ GeoJSON size: {len(geojson_str) / 1024 / 1024:.2f} MB")

# Verify ALL roads are present
print("\n5. VERIFICATION:")
print(f"   Original shapefile: {len(gdf_original)} roads")
print(f"   Final GeoJSON: {len(geojson['features'])} roads")

if len(gdf_original) == len(geojson['features']):
    print("\n   ✅ SUCCESS! ALL roads are preserved!")
    print("   ✅ No roads were removed!")
    print("   ✅ Only geometry was simplified for faster loading!")
else:
    print("\n   ❌ ERROR: Roads were lost!")

# Show sample road
print("\n6. Sample road data:")
if len(geojson['features']) > 0:
    sample = geojson['features'][0]
    print(f"   Type: {sample['type']}")
    print(f"   Properties: {list(sample['properties'].keys())}")
    print(f"   Geometry type: {sample['geometry']['type']}")

print("\n" + "=" * 60)
