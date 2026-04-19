from app.services.uganda_gis_loader import UgandaGISLoader
from config import Config

loader = UgandaGISLoader(Config())

# Test protected areas
geojson = loader.load_layer_geojson('protected_areas', (29.5, 0.5, 35.0, 4.5))
if geojson:
    print(f'✓ Protected areas: {len(geojson["features"])} features')
else:
    print('✗ Protected areas: NO DATA')

# Test rivers
geojson = loader.load_layer_geojson('rivers', (29.5, 0.5, 35.0, 4.5))
if geojson:
    print(f'✓ Rivers: {len(geojson["features"])} features')
else:
    print('✗ Rivers: NO DATA')

# Test wetlands
geojson = loader.load_layer_geojson('wetlands', (29.5, 0.5, 35.0, 4.5))
if geojson:
    print(f'✓ Wetlands: {len(geojson["features"])} features')
else:
    print('✗ Wetlands: NO DATA')

# Test lakes
geojson = loader.load_layer_geojson('lakes', (29.5, 0.5, 35.0, 4.5))
if geojson:
    print(f'✓ Lakes: {len(geojson["features"])} features')
else:
    print('✗ Lakes: NO DATA')

# Test uganda districts
geojson = loader.load_layer_geojson('uganda_districts', (29.5, 0.5, 35.0, 4.5))
if geojson:
    print(f'✓ Uganda Districts: {len(geojson["features"])} features')
else:
    print('✗ Uganda Districts: NO DATA')
