"""
API Routes for Transmission Line Routing Optimization Tool
Handles route optimization, cost surface generation, and data export
"""
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
import numpy as np
import os
import json
from datetime import datetime

from app import db
from app.models import Project, Route, CostSurface
from app.optimizer.cost_surface import CostSurfaceGenerator
from app.optimizer.dijkstra import LeastCostPathFinder
from app.optimizer.astar import AStarPathFinder
from app.optimizer.engineering_validation import EngineeringValidator
from app.services.corridor_restriction import CorridorRestrictionService
from app.services.gis_data_loader import load_layers_for_bounds

api_bp = Blueprint('api', __name__)


@api_bp.route('/projects', methods=['GET'])
@login_required
def get_projects():
    """Get all projects for current user"""
    projects = Project.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'projects': [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'voltage_level': p.voltage_level,
            'tower_type': p.tower_type,
            'status': p.status,
            'created_at': p.created_at.isoformat(),
            'start': {'lat': p.start_lat, 'lon': p.start_lon, 'name': p.start_name},
            'end': {'lat': p.end_lat, 'lon': p.end_lon, 'name': p.end_name}
        } for p in projects]
    })


@api_bp.route('/projects', methods=['POST'])
@login_required
def create_project():
    """
    Create a new transmission line routing project
    
    Expected JSON:
    {
        "name": "Olwiyo-South Sudan Line",
        "description": "400kV interconnection",
        "voltage_level": 400,
        "tower_type": "lattice",
        "start": {"lat": 3.3833, "lon": 32.5667, "name": "Olwiyo Substation"},
        "end": {"lat": 3.5833, "lon": 32.1167, "name": "South Sudan Border"},
        "ahp_weights": {
            "topography": 0.25,
            "land_use": 0.30,
            "settlements": 0.20,
            "protected_areas": 0.15,
            "roads": 0.10
        }
    }
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'start', 'end']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Create project
    project = Project(
        name=data['name'],
        description=data.get('description', ''),
        voltage_level=data.get('voltage_level', 400),
        tower_type=data.get('tower_type', 'lattice'),
        start_lat=data['start']['lat'],
        start_lon=data['start']['lon'],
        start_name=data['start'].get('name', 'Start Point'),
        end_lat=data['end']['lat'],
        end_lon=data['end']['lon'],
        end_name=data['end'].get('name', 'End Point'),
        user_id=current_user.id,
        status='draft'
    )
    
    # Set AHP weights
    ahp_weights = data.get('ahp_weights', current_app.config['DEFAULT_AHP_WEIGHTS'])
    project.set_ahp_weights(ahp_weights)

    # Set waypoints in metadata
    waypoints = data.get('waypoints', [])
    if waypoints:
        metadata = project.get_metadata() or {}
        metadata['waypoints'] = waypoints
        project.set_metadata(metadata)

    db.session.add(project)
    db.session.commit()
    
    return jsonify({
        'message': 'Project created successfully',
        'project_id': project.id
    }), 201


def _run_pathfinder(cost_surface, bounds, route_points, algorithm):
    """Run dijkstra or astar and return path_result, path_coords, pathfinder for a single algorithm."""
    if algorithm == 'astar':
        pathfinder = AStarPathFinder(cost_surface)
    else:
        pathfinder = LeastCostPathFinder(cost_surface)

    all_paths = []
    total_cost = 0
    for i in range(len(route_points) - 1):
        segment_start_pixel = _geo_to_pixel(
            route_points[i]['lon'], route_points[i]['lat'],
            bounds, cost_surface.shape
        )
        segment_end_pixel = _geo_to_pixel(
            route_points[i + 1]['lon'], route_points[i + 1]['lat'],
            bounds, cost_surface.shape
        )
        segment_result = pathfinder.find_path(segment_start_pixel, segment_end_pixel)
        if segment_result is None:
            return None, None, None
        if i == 0:
            all_paths.extend(segment_result['path'])
        else:
            all_paths.extend(segment_result['path'][1:])
        total_cost += segment_result['total_cost']

    path_result = {'path': all_paths, 'total_cost': total_cost, 'distance': len(all_paths)}
    path_coords = pathfinder.path_to_coordinates(path_result['path'], bounds, 30)
    return path_result, path_coords, pathfinder


@api_bp.route('/projects/<int:project_id>/optimize', methods=['POST'])
@login_required
def optimize_route(project_id):
    """
    Generate optimized route for a project.
    Body: { "algorithm": "dijkstra" | "astar" (optional, default dijkstra),
            "compare": true (optional) to run both and return comparison }
    """
    project = Project.query.get_or_404(project_id)

    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json() or {}
    algorithm = (data.get('algorithm') or 'dijkstra').lower()
    if algorithm not in ('dijkstra', 'astar'):
        algorithm = 'dijkstra'
    compare = data.get('compare', False)

    try:
        project.status = 'processing'
        db.session.commit()

        ahp_weights = project.get_ahp_weights() or current_app.config['DEFAULT_AHP_WEIGHTS']
        margin = 0.1
        bounds = [
            min(project.start_lon, project.end_lon) - margin,
            min(project.start_lat, project.end_lat) - margin,
            max(project.start_lon, project.end_lon) + margin,
            max(project.start_lat, project.end_lat) + margin
        ]

        cost_generator = CostSurfaceGenerator(current_app.config)
        # Prefer real GIS data if present; otherwise fall back to demo layers.
        # We precompute an expected raster shape so real rasters can be resampled consistently.
        layers_data = {}
        data_source = "demo"
        try:
            shape = _shape_from_bounds(bounds, resolution_m=30)
            layers_data = load_layers_for_bounds(current_app.config, tuple(bounds), shape)
            if layers_data:
                data_source = "real"
        except Exception:
            layers_data = {}
            data_source = "demo"
        if not layers_data:
            layers_data = _create_demo_layers(bounds, current_app.config)

        cost_surface, metadata = cost_generator.generate_composite_cost_surface(
            bounds, ahp_weights, layers_data
        )
        metadata = metadata or {}
        metadata["data_source"] = data_source

        cost_surface_path = os.path.join(
            current_app.config['DATA_FOLDER'],
            f'cost_surface_project_{project_id}.tif'
        )
        cost_generator.save_cost_surface(cost_surface, cost_surface_path, bounds)
        cost_surf_record = CostSurface(
            project_id=project.id,
            file_path=cost_surface_path,
            resolution=30,
            layer_weights=json.dumps(ahp_weights)
        )
        cost_surf_record.set_bounds(bounds)
        db.session.add(cost_surf_record)

        proj_metadata = project.get_metadata()
        waypoints_data = proj_metadata.get('waypoints', []) if proj_metadata else []
        route_points = [{'lat': project.start_lat, 'lon': project.start_lon}]
        route_points.extend(waypoints_data)
        route_points.append({'lat': project.end_lat, 'lon': project.end_lon})

        comparison = {}
        path_result = None
        path_coords = None
        pathfinder = None
        chosen_algorithm = algorithm

        if compare:
            for algo in ('dijkstra', 'astar'):
                pr, pc, pf = _run_pathfinder(cost_surface, bounds, route_points, algo)
                if pr is not None:
                    comparison[algo] = {
                        'total_cost': pr['total_cost'],
                        'path_length_pixels': pr['distance'],
                        'path_coords_count': len(pc),
                    }
                else:
                    comparison[algo] = None
            # Use requested algorithm for main result
            path_result, path_coords, pathfinder = _run_pathfinder(cost_surface, bounds, route_points, algorithm)
        else:
            path_result, path_coords, pathfinder = _run_pathfinder(cost_surface, bounds, route_points, algorithm)

        if path_result is None or path_coords is None or pathfinder is None:
            project.status = 'failed'
            db.session.commit()
            return jsonify({'error': 'No valid path found for the selected algorithm'}), 400

        simplified_path = pathfinder.simplify_path(path_result['path'], tolerance=1)
        simplified_coords = pathfinder.path_to_coordinates(simplified_path, bounds, 30)

        validator = EngineeringValidator(current_app.config)
        validation_result = validator.validate_route(path_coords)
        tower_positions = validator.generate_tower_positions(path_coords)
        detailed_costs = validator.calculate_detailed_costs(path_coords, tower_positions)

        route_geojson = {
            'type': 'Feature',
            'properties': {
                'project_id': project.id,
                'total_cost': detailed_costs['total_cost'],
                'cost_per_km': detailed_costs['cost_per_km'],
                'length_m': validation_result['metrics']['total_length_m'],
                'length_km': detailed_costs['total_length_km'],
                'estimated_towers': len(tower_positions),
                'avg_span_length_m': detailed_costs['avg_span_length_m'],
                'algorithm': chosen_algorithm,
            },
            'geometry': {
                'type': 'LineString',
                'coordinates': simplified_coords
            }
        }

        route = Route(
            project_id=project.id,
            total_length=validation_result['metrics']['total_length_m'],
            total_cost=detailed_costs['total_cost'],
            estimated_towers=len(tower_positions),
            is_valid=validation_result['is_valid'],
            algorithm=chosen_algorithm
        )
        route.set_geometry(route_geojson)
        route.set_validation_errors(validation_result['errors'])
        db.session.add(route)
        project.status = 'completed'
        db.session.commit()

        response = {
            'message': 'Route optimized successfully',
            'route_id': route.id,
            'route': route_geojson,
            'tower_positions': tower_positions,
            'validation': validation_result,
            'cost_breakdown': detailed_costs,
            'metadata': proj_metadata,
            'algorithm_used': chosen_algorithm,
        }
        if comparison:
            response['algorithm_comparison'] = comparison
        return jsonify(response)

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"ERROR in optimize_route: {str(e)}")
        print(error_traceback)
        project.status = 'failed'
        db.session.commit()
        return jsonify({'error': str(e), 'traceback': error_traceback}), 500


@api_bp.route('/projects/<int:project_id>/routes', methods=['GET'])
@login_required
def get_project_routes(project_id):
    """Get all routes for a project"""
    project = Project.query.get_or_404(project_id)

    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    routes = Route.query.filter_by(project_id=project_id).all()

    return jsonify({
        'routes': [{
            'id': r.id,
            'geometry': r.get_geometry(),
            'total_length': r.total_length,
            'total_cost': r.total_cost,
            'estimated_towers': r.estimated_towers,
            'is_valid': r.is_valid,
            'validation_errors': r.get_validation_errors(),
            'created_at': r.created_at.isoformat()
        } for r in routes]
    })


@api_bp.route('/projects/<int:project_id>/generate-towers', methods=['POST'])
@login_required
def generate_towers(project_id):
    """
    Generate tower positions for an existing route
    Separate from route optimization for better visualization
    """
    project = Project.query.get_or_404(project_id)

    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Get the most recent route for this project
        route = Route.query.filter_by(project_id=project_id).order_by(Route.created_at.desc()).first()

        if not route:
            return jsonify({'error': 'No route found for this project'}), 404

        # Get route geometry
        route_geojson = route.get_geometry()
        path_coords = route_geojson['geometry']['coordinates']

        # Generate tower positions
        validator = EngineeringValidator(current_app.config)
        tower_positions = validator.generate_tower_positions(path_coords)

        # Calculate detailed costs with towers
        detailed_costs = validator.calculate_detailed_costs(path_coords, tower_positions)

        # Update route with tower information
        route.estimated_towers = len(tower_positions)
        route.total_cost = detailed_costs['total_cost']
        db.session.commit()

        return jsonify({
            'message': 'Towers generated successfully',
            'tower_positions': tower_positions,
            'num_towers': len(tower_positions),
            'cost_breakdown': detailed_costs
        })

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"ERROR in generate_towers: {str(e)}")
        print(error_traceback)
        return jsonify({'error': str(e), 'traceback': error_traceback}), 500


@api_bp.route('/routes/<int:route_id>/export', methods=['GET'])
@login_required
def export_route(route_id):
    """
    Export route as GeoJSON or XYZ (Eastings, Northings, elevation).

    Query params:
        format: 'geojson' (default), 'xyz'
        crs: for xyz, 'EPSG:21096' (UTM 36N Uganda) or leave default
    """
    route = Route.query.get_or_404(route_id)
    project = Project.query.get(route.project_id)

    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    export_format = request.args.get('format', 'geojson')
    geojson = route.get_geometry()
    coords_wgs84 = geojson['geometry']['coordinates']  # list of [lon, lat]

    if export_format == 'geojson':
        return jsonify(geojson)

    if export_format == 'xyz':
        # XYZ = Eastings, Northings, elevation (for simulation)
        try:
            import pyproj
            from pyproj import Transformer
        except ImportError:
            return jsonify({
                'crs': current_app.config.get('MAP_CRS', 'EPSG:4326'),
                'crs_description': 'pyproj not installed. Coordinates in lon, lat, elevation (elevation placeholder 0).',
                'coordinates': [[c[0], c[1], 0.0] for c in coords_wgs84]
            })
        target_crs = request.args.get('crs') or current_app.config.get('PREFERRED_PROJECTED_CRS', 'EPSG:21096')
        transformer = Transformer.from_crs('EPSG:4326', target_crs, always_xy=True)
        xyz = []
        for lon, lat in coords_wgs84:
            easting, northing = transformer.transform(lon, lat)
            xyz.append([easting, northing, 0.0])  # elevation 0 without DEM lookup
        return jsonify({
            'crs': target_crs,
            'crs_description': 'Eastings, Northings, elevation (m). Elevation 0 if not from DEM.',
            'coordinates': xyz
        })

    if export_format == 'shapefile':
        return jsonify({'error': 'Shapefile export not yet implemented'}), 501

    return jsonify({'error': 'Invalid format. Use geojson or xyz'}), 400


@api_bp.route('/layers', methods=['GET'])
@login_required
def get_layers():
    """
    Return GIS layer data for map display (DEM, land use, settlements, protected areas, roads).
    Query params: min_lon, min_lat, max_lon, max_lat (map bounds), layers (optional comma-separated, default all).
    Data sources: demo/synthetic; in production replace with USGS DEM, ESA WorldCover, NEMA/NFA/UWA, OSM.
    """
    try:
        min_lon = float(request.args.get('min_lon', 32.0))
        min_lat = float(request.args.get('min_lat', 3.2))
        max_lon = float(request.args.get('max_lon', 32.6))
        max_lat = float(request.args.get('max_lat', 3.6))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid bounds. Provide min_lon, min_lat, max_lon, max_lat.'}), 400
    bounds = [min_lon, min_lat, max_lon, max_lat]
    requested = request.args.get('layers', 'dem,land_use,settlements,protected_areas,roads')
    requested = [s.strip() for s in requested.split(',') if s.strip()]

    # Prefer real data if present; fall back to demo if not.
    # Use a smaller grid for map display to keep responses light.
    out_shape = (60, 60)
    try:
        layers_data = load_layers_for_bounds(current_app.config, tuple(bounds), out_shape)
    except Exception:
        layers_data = {}
    if not layers_data:
        layers_data = _create_demo_layers(bounds, current_app.config)
    result = {}
    min_lon, min_lat, max_lon, max_lat = bounds
    height, width = layers_data['dem'].shape
    lon_per_pixel = (max_lon - min_lon) / width
    lat_per_pixel = (max_lat - min_lat) / height
    # Limit resolution for response size (max ~80x80 grid)
    step = max(1, min(height // 50, width // 50))

    if 'dem' in requested and 'dem' in layers_data:
        features = []
        dem = layers_data['dem']
        for r in range(0, height, step):
            for c in range(0, width, step):
                lat = max_lat - r * lat_per_pixel
                lon = min_lon + c * lon_per_pixel
                elev = float(dem[r, c])
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                    'properties': {'elevation': elev}
                })
        result['dem'] = {'type': 'FeatureCollection', 'features': features}

    if 'land_use' in requested and 'land_use' in layers_data:
        features = []
        lu = layers_data['land_use']
        classes = {10: 'Tree cover', 30: 'Grassland', 40: 'Cropland', 50: 'Built-up', 80: 'Water', 90: 'Wetlands'}
        for r in range(0, height, step):
            for c in range(0, width, step):
                lat = max_lat - r * lat_per_pixel
                lon = min_lon + c * lon_per_pixel
                cl = int(lu[r, c])
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                    'properties': {'class': cl, 'label': classes.get(cl, 'Other')}
                })
        result['land_use'] = {'type': 'FeatureCollection', 'features': features}

    if 'settlements' in requested and 'settlements' in layers_data:
        features = []
        st = layers_data['settlements']
        for r in range(0, height, step):
            for c in range(0, width, step):
                if st[r, c] > 0:
                    lat = max_lat - r * lat_per_pixel
                    lon = min_lon + c * lon_per_pixel
                    features.append({
                        'type': 'Feature',
                        'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                        'properties': {'type': 'settlement'}
                    })
        result['settlements'] = {'type': 'FeatureCollection', 'features': features}

    if 'protected_areas' in requested and 'protected_areas' in layers_data:
        features = []
        pa = layers_data['protected_areas']
        for r in range(0, height, step):
            for c in range(0, width, step):
                if pa[r, c] > 0:
                    lat = max_lat - r * lat_per_pixel
                    lon = min_lon + c * lon_per_pixel
                    features.append({
                        'type': 'Feature',
                        'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                        'properties': {'type': 'protected'}
                    })
        result['protected_areas'] = {'type': 'FeatureCollection', 'features': features}

    if 'roads' in requested and 'roads' in layers_data:
        features = []
        rd = layers_data['roads']
        for r in range(0, height, step):
            for c in range(0, width, step):
                if rd[r, c] > 0:
                    lat = max_lat - r * lat_per_pixel
                    lon = min_lon + c * lon_per_pixel
                    features.append({
                        'type': 'Feature',
                        'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                        'properties': {'type': 'road'}
                    })
        result['roads'] = {'type': 'FeatureCollection', 'features': features}

    return jsonify({
        'crs': current_app.config.get('MAP_CRS', 'EPSG:4326'),
        'bounds': bounds,
        'layers': result
    })


@api_bp.route('/routes/<int:route_id>/corridor', methods=['GET'])
@login_required
def get_route_corridor(route_id):
    """Get corridor polygon for a route"""
    route = Route.query.get_or_404(route_id)
    project = Project.query.get(route.project_id)

    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Get route coordinates
    geojson = route.get_geometry()
    coords = geojson['geometry']['coordinates']

    # Generate corridor
    corridor_service = CorridorRestrictionService(current_app.config)
    corridor_geojson = corridor_service.generate_corridor_geojson(coords)
    land_acquisition = corridor_service.calculate_land_acquisition_area(coords)

    return jsonify({
        'corridor': corridor_geojson,
        'land_acquisition': land_acquisition
    })


def _create_demo_layers(bounds, config):
    """
    Create demo GIS layers for testing
    In production, replace with actual data loading
    """
    # Calculate dimensions
    min_lon, min_lat, max_lon, max_lat = bounds
    width = int((max_lon - min_lon) * 111320 / 30)
    height = int((max_lat - min_lat) * 111320 / 30)

    # Create synthetic layers
    dem = np.random.rand(height, width) * 100  # Random elevation 0-100m
    land_use = np.random.choice([10, 30, 40, 50, 80, 90], size=(height, width))
    settlements = np.random.choice([0, 1], size=(height, width), p=[0.95, 0.05])
    protected_areas = np.random.choice([0, 1], size=(height, width), p=[0.9, 0.1])
    roads = np.random.choice([0, 1], size=(height, width), p=[0.98, 0.02])

    return {
        'dem': dem,
        'land_use': land_use,
        'settlements': settlements,
        'protected_areas': protected_areas,
        'roads': roads
    }


def _shape_from_bounds(bounds, resolution_m: float = 30) -> tuple:
    """
    Compute a raster shape (height, width) for given WGS84 bounds and meter resolution.
    Uses a simple 111,320 m/degree approximation (consistent with existing demo code).
    """
    min_lon, min_lat, max_lon, max_lat = bounds
    width = int((max_lon - min_lon) * 111320 / resolution_m)
    height = int((max_lat - min_lat) * 111320 / resolution_m)
    width = max(1, width)
    height = max(1, height)
    return (height, width)


def _geo_to_pixel(lon, lat, bounds, shape):
    """Convert geographic coordinates to pixel coordinates"""
    min_lon, min_lat, max_lon, max_lat = bounds
    height, width = shape

    col = int((lon - min_lon) / (max_lon - min_lon) * width)
    row = int((max_lat - lat) / (max_lat - min_lat) * height)

    # Clamp to valid range
    col = max(0, min(width - 1, col))
    row = max(0, min(height - 1, row))

    return (row, col)

