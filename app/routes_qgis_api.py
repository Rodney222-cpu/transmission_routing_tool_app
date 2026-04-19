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


@qgis_api_bp.route('/generate-cost-surface', methods=['POST'])
@login_required
def generate_qgis_cost_surface():
    """
    QGIS-style cost surface analysis and least-cost routing.
    
    Expects:
    - layers: Dict of layer configs with enabled status and weights
    - start_point: {"lat": float, "lon": float}
    - end_point: {"lat": float, "lon": float}
    - bounds: Optional [min_lon, min_lat, max_lon, max_lat]
    - resolution: Optional pixel size in degrees
    """
    try:
        from app.optimizer.qgis_cost_surface import QGISStyleCostSurfaceAnalyzer
        from app.services.uganda_gis_loader import UgandaGISLoader
        import time
        
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        layers_config = data.get('layers', {})
        start_point_data = data.get('start_point', {})
        end_point_data = data.get('end_point', {})
        
        # Validate inputs
        if not layers_config:
            return jsonify({'success': False, 'error': 'No layers specified'}), 400
        
        start_lat = start_point_data.get('lat')
        start_lon = start_point_data.get('lon')
        end_lat = end_point_data.get('lat')
        end_lon = end_point_data.get('lon')
        
        if not all([start_lat, start_lon, end_lat, end_lon]):
            return jsonify({'success': False, 'error': 'Start and end points required'}), 400
        
        start_point = (start_lat, start_lon)
        end_point = (end_lat, end_lon)
        
        bounds = data.get('bounds')
        resolution = data.get('resolution')
        
        # Count enabled layers
        enabled_count = sum(1 for config in layers_config.values() if config.get('enabled', False))
        if enabled_count == 0:
            return jsonify({'success': False, 'error': 'At least one layer must be enabled'}), 400
        
        print(f"🎯 QGIS-style cost surface analysis started")
        print(f"   Enabled layers: {enabled_count}")
        print(f"   Start: {start_point}, End: {end_point}")
        
        # Initialize analyzer
        start_time = time.time()
        analyzer = QGISStyleCostSurfaceAnalyzer(
            config=current_app.config,
            output_dir='static'
        )
        
        # Resolve layer paths using Uganda GIS loader
        loader = UgandaGISLoader(current_app.config)
        
        layer_path_map = {
            'protected_areas': 'protected_areas',
            'rivers': 'rivers',
            'wetlands': 'wetlands',
            'lakes': 'lakes',
            'land_use': 'land_use',
            'elevation': 'elevation',
            'settlements': 'settlements',
            'roads': 'roads'
        }
        
        # Add paths to layer config
        for layer_name, config in layers_config.items():
            if config.get('enabled', False):
                layer_key = layer_path_map.get(layer_name)
                if layer_key:
                    # Try to get file path
                    folder_map = {
                        'protected_areas': current_app.config.get('PROTECTED_AREAS_FOLDER'),
                        'rivers': current_app.config.get('RIVERS_FOLDER'),
                        'wetlands': current_app.config.get('WETLANDS_FOLDER'),
                        'lakes': current_app.config.get('LAKES_FOLDER'),
                        'land_use': current_app.config.get('LAND_USE_FOLDER'),
                        'elevation': current_app.config.get('ELEVATION_FOLDER'),
                        'settlements': current_app.config.get('SCHOOLS_FOLDER'),
                        'roads': current_app.config.get('ROADS_FOLDER')
                    }
                    
                    folder_path = folder_map.get(layer_key)
                    if folder_path and os.path.exists(folder_path):
                        # Find shapefile or GeoJSON
                        for ext in ['.shp', '.geojson', '.tif', '.tiff']:
                            possible_path = os.path.join(folder_path, f'{layer_key}{ext}')
                            if os.path.exists(possible_path):
                                config['path'] = possible_path
                                config['type'] = 'raster' if ext in ['.tif', '.tiff'] else 'vector'
                                print(f"   ✓ {layer_name}: {possible_path}")
                                break
                    else:
                        print(f"   ⚠ {layer_name}: Folder not found")
        
        # Run pipeline
        result = analyzer.run_full_pipeline(
            layers_config=layers_config,
            start_point=start_point,
            end_point=end_point,
            bounds=bounds,
            resolution=resolution
        )
        
        elapsed = time.time() - start_time
        print(f"✓ Pipeline completed in {elapsed:.2f}s")
        
        # Read PNG and convert to base64 for frontend display
        png_path = result['cost_surface_png']
        if os.path.exists(png_path):
            with open(png_path, 'rb') as f:
                png_base64 = base64.b64encode(f.read()).decode('utf-8')
        else:
            png_base64 = None
        
        # Build response
        response = {
            'success': True,
            'cost_surface_tif': '/' + result['cost_surface_tif'],
            'cost_surface_png': '/' + result['cost_surface_png'],
            'cost_surface_png_base64': png_base64,
            'route_shp': '/' + result['route_shp'] if result['route_shp'] else None,
            'bounds': result['bounds'],
            'metadata': result['metadata']
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"❌ Error in QGIS cost surface pipeline: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
