"""
API endpoint for QGIS-style cost surface analysis and least-cost routing.

POST /api/generate-cost-surface

Request:
{
    "layers": {
        "protected_areas": {"enabled": true, "weight": 0.2, "type": "vector"},
        "rivers": {"enabled": true, "weight": 0.2, "type": "vector"},
        "wetlands": {"enabled": true, "weight": 0.15, "type": "vector"},
        "land_use": {"enabled": true, "weight": 0.15, "type": "vector"},
        "elevation": {"enabled": true, "weight": 0.3, "type": "raster"}
    },
    "start_point": {"lat": 0.3476, "lon": 32.5825},
    "end_point": {"lat": 1.3733, "lon": 32.2903},
    "bounds": [29.5, -1.5, 35.0, 4.5],
    "resolution": 0.001
}

Response:
{
    "success": true,
    "cost_surface_tif": "/static/cost_surface.tif",
    "cost_surface_png": "/static/cost_surface.png",
    "route_shp": "/static/route.shp",
    "bounds": [...],
    "metadata": {...}
}
"""

import os
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
import base64

qgis_api_bp = Blueprint('qgis_api', __name__)

# Top-level blueprint exposing the spec-compliant POST /generate-cost-surface
cost_surface_bp = Blueprint('cost_surface', __name__)


# Folders associated with each supported layer name
_LAYER_FOLDER_CONFIG_KEYS = {
    'protected_areas': 'PROTECTED_AREAS_FOLDER',
    'rivers': 'RIVERS_FOLDER',
    'wetlands': 'WETLANDS_FOLDER',
    'lakes': 'LAKES_FOLDER',
    'land_use': 'LAND_USE_FOLDER',
    'elevation': 'ELEVATION_FOLDER',
    'settlements': 'SCHOOLS_FOLDER',
    'roads': 'ROADS_FOLDER',
}


def _resolve_layer_path(folder_path):
    """
    Scan a layer's data folder and return (path, type) for the first usable file.
    Prefers raster (.tif/.tiff), then shapefile (.shp), then GeoJSON.
    Returns (None, None) if nothing usable is found.
    """
    if not folder_path or not os.path.isdir(folder_path):
        return None, None

    raster_hit = None
    shp_hit = None
    geojson_hit = None
    for name in os.listdir(folder_path):
        lower = name.lower()
        full = os.path.join(folder_path, name)
        if lower.endswith(('.tif', '.tiff')) and raster_hit is None:
            raster_hit = full
        elif lower.endswith('.shp') and shp_hit is None:
            shp_hit = full
        elif lower.endswith(('.geojson', '.json')) and geojson_hit is None:
            geojson_hit = full

    if raster_hit:
        return raster_hit, 'raster'
    if shp_hit:
        return shp_hit, 'vector'
    if geojson_hit:
        return geojson_hit, 'vector'
    return None, None


def _run_cost_surface_pipeline(data):
    """
    Shared handler for cost-surface generation. Returns a (json_dict, status_code)
    tuple so the Flask route wrappers stay thin.
    """
    from app.optimizer.qgis_cost_surface import QGISStyleCostSurfaceAnalyzer
    import time

    if not data:
        return {'success': False, 'error': 'No JSON data provided'}, 400

    layers_input = data.get('layers', {})
    weights_input = data.get('weights')
    start_point_data = data.get('start_point', {})
    end_point_data = data.get('end_point', {})

    # Support both shapes:
    #   1) layers as a dict: {name: {enabled, weight, ...}}
    #   2) layers as a list + parallel weights dict/list (per spec UI)
    layers_config = {}
    if isinstance(layers_input, dict):
        layers_config = {k: dict(v) for k, v in layers_input.items()}
    elif isinstance(layers_input, list):
        if isinstance(weights_input, dict):
            for name in layers_input:
                layers_config[name] = {
                    'enabled': True,
                    'weight': float(weights_input.get(name, 1.0)),
                }
        elif isinstance(weights_input, list) and len(weights_input) == len(layers_input):
            for name, w in zip(layers_input, weights_input):
                layers_config[name] = {'enabled': True, 'weight': float(w)}
        else:
            for name in layers_input:
                layers_config[name] = {'enabled': True, 'weight': 1.0}
    else:
        return {'success': False, 'error': 'layers must be a dict or list'}, 400

    if not layers_config:
        return {'success': False, 'error': 'No layers specified'}, 400

    start_lat = start_point_data.get('lat')
    start_lon = start_point_data.get('lon')
    end_lat = end_point_data.get('lat')
    end_lon = end_point_data.get('lon')
    if None in (start_lat, start_lon, end_lat, end_lon):
        return {'success': False, 'error': 'Start and end points required'}, 400

    start_point = (float(start_lat), float(start_lon))
    end_point = (float(end_lat), float(end_lon))

    bounds = data.get('bounds')
    resolution = data.get('resolution')

    enabled_count = sum(1 for cfg in layers_config.values() if cfg.get('enabled', False))
    if enabled_count == 0:
        return {'success': False, 'error': 'At least one layer must be enabled'}, 400

    print("🎯 QGIS-style cost surface analysis started")
    print(f"   Enabled layers: {enabled_count}")
    print(f"   Start: {start_point}, End: {end_point}")

    start_time = time.time()
    analyzer = QGISStyleCostSurfaceAnalyzer(
        config=current_app.config,
        output_dir='static',
    )

    # Resolve a real on-disk file for every enabled layer by scanning its folder
    for layer_name, cfg in layers_config.items():
        if not cfg.get('enabled', False):
            continue
        if cfg.get('path'):
            continue  # caller pre-supplied a path
        folder_key = _LAYER_FOLDER_CONFIG_KEYS.get(layer_name)
        folder_path = current_app.config.get(folder_key) if folder_key else None
        resolved, layer_type = _resolve_layer_path(folder_path)
        if resolved:
            cfg['path'] = resolved
            cfg['type'] = layer_type
            print(f"   ✓ {layer_name}: {resolved}")
        else:
            print(f"   ⚠ {layer_name}: No usable file in {folder_path}")

    result = analyzer.run_full_pipeline(
        layers_config=layers_config,
        start_point=start_point,
        end_point=end_point,
        bounds=bounds,
        resolution=resolution,
    )

    elapsed = time.time() - start_time
    print(f"✓ Pipeline completed in {elapsed:.2f}s")

    png_path = result.get('cost_surface_png')
    png_base64 = None
    if png_path and os.path.exists(png_path):
        with open(png_path, 'rb') as f:
            png_base64 = base64.b64encode(f.read()).decode('utf-8')

    response = {
        'success': True,
        'cost_surface_tif': '/' + result['cost_surface_tif'],
        'cost_surface_png': '/' + result['cost_surface_png'],
        'cost_surface_png_base64': png_base64,
        'route_shp': '/' + result['route_shp'] if result.get('route_shp') else None,
        'bounds': result['bounds'],
        'metadata': result['metadata'],
    }
    return response, 200


@cost_surface_bp.route('/generate-cost-surface', methods=['POST'])
def generate_cost_surface():
    """Spec-compliant endpoint: POST /generate-cost-surface."""
    try:
        payload, status = _run_cost_surface_pipeline(request.get_json(silent=True))
        return jsonify(payload), status
    except Exception as e:
        print(f"❌ Error in cost surface pipeline: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@qgis_api_bp.route('/generate-cost-surface', methods=['POST'])
@login_required
def generate_qgis_cost_surface():
    """
    Authenticated alias reachable at POST /api/qgis/generate-cost-surface.
    Kept for backward compatibility with the existing dashboard UI.
    """
    try:
        payload, status = _run_cost_surface_pipeline(request.get_json(silent=True))
        return jsonify(payload), status
    except Exception as e:
        print(f"❌ Error in QGIS cost surface pipeline: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@qgis_api_bp.route('/layer-info/<layer_name>', methods=['GET'])
@login_required
def get_layer_info(layer_name):
    """
    Get information about a specific layer (path, type, etc.).
    """
    try:
        from app.services.uganda_gis_loader import UgandaGISLoader
        
        loader = UgandaGISLoader(current_app.config)
        
        layer_map = {
            'protected_areas': current_app.config.get('PROTECTED_AREAS_FOLDER'),
            'rivers': current_app.config.get('RIVERS_FOLDER'),
            'wetlands': current_app.config.get('WETLANDS_FOLDER'),
            'lakes': current_app.config.get('LAKES_FOLDER'),
            'land_use': current_app.config.get('LAND_USE_FOLDER'),
            'elevation': current_app.config.get('ELEVATION_FOLDER'),
            'settlements': current_app.config.get('SCHOOLS_FOLDER'),
            'roads': current_app.config.get('ROADS_FOLDER')
        }
        
        folder_path = layer_map.get(layer_name)
        
        if not folder_path or not os.path.exists(folder_path):
            return jsonify({
                'success': False,
                'error': f'Layer {layer_name} not found'
            }), 404
        
        # Find files
        files = []
        for filename in os.listdir(folder_path):
            if filename.endswith(('.shp', '.geojson', '.tif', '.tiff')):
                files.append({
                    'name': filename,
                    'path': os.path.join(folder_path, filename),
                    'type': 'raster' if filename.endswith(('.tif', '.tiff')) else 'vector'
                })
        
        return jsonify({
            'success': True,
            'layer': layer_name,
            'folder': folder_path,
            'files': files
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting layer info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
