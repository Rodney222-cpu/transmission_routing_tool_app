import geopandas as gpd
import json

print("Loading roads shapefile...")
gdf = gpd.read_file('data/roads/Ug_Roads_UNRA_2012.shp')
print(f"Loaded {len(gdf)} features")

print("Converting to GeoJSON...")
geojson = gdf.to_json()
print(f"GeoJSON size: {len(geojson) / 1024 / 1024:.2f} MB")

print("Parsing JSON...")
data = json.loads(geojson)
print(f"Features: {len(data['features'])}")
print("✓ Success!")
