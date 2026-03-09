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
from app.optimizer.engineering_validation import EngineeringValidator
from app.services.corridor_restriction import CorridorRestrictionService

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


@api_bp.route('/projects/<int:project_id>/optimize', methods=['POST'])
@login_required
def optimize_route(project_id):
    """
    Generate optimized route for a project using Dijkstra's algorithm
    
    This is the main endpoint for route optimization
    """
    project = Project.query.get_or_404(project_id)
    
    # Check ownership
    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Update project status
        project.status = 'processing'
        db.session.commit()
        
        # Get AHP weights
        ahp_weights = project.get_ahp_weights() or current_app.config['DEFAULT_AHP_WEIGHTS']
        
        # Define bounds (expand around start and end points)
        margin = 0.1  # degrees
        bounds = [
            min(project.start_lon, project.end_lon) - margin,
            min(project.start_lat, project.end_lat) - margin,
            max(project.start_lon, project.end_lon) + margin,
            max(project.start_lat, project.end_lat) + margin
        ]
        
        # Generate cost surface
        cost_generator = CostSurfaceGenerator(current_app.config)

        # For demo purposes, create synthetic data
        # In production, load actual GIS layers
        layers_data = _create_demo_layers(bounds, current_app.config)
        
        cost_surface, metadata = cost_generator.generate_composite_cost_surface(
            bounds, ahp_weights, layers_data
        )
        
        # Save cost surface
        cost_surface_path = os.path.join(
            current_app.config['DATA_FOLDER'],
            f'cost_surface_project_{project_id}.tif'
        )
        cost_generator.save_cost_surface(cost_surface, cost_surface_path, bounds)
        
        # Store cost surface record
        cost_surf_record = CostSurface(
            project_id=project.id,
            file_path=cost_surface_path,
            resolution=30,
            layer_weights=json.dumps(ahp_weights)
        )
        cost_surf_record.set_bounds(bounds)
        db.session.add(cost_surf_record)
        
        # Run Dijkstra's algorithm
        pathfinder = LeastCostPathFinder(cost_surface)

        # Get waypoints from project metadata
        metadata = project.get_metadata()
        waypoints_data = metadata.get('waypoints', []) if metadata else []

        # Build list of points to route through: start -> waypoint1 -> waypoint2 -> ... -> end
        route_points = [{'lat': project.start_lat, 'lon': project.start_lon}]
        route_points.extend(waypoints_data)
        route_points.append({'lat': project.end_lat, 'lon': project.end_lon})

        # Find path through all segments
        all_paths = []
        total_cost = 0

        for i in range(len(route_points) - 1):
            # Convert geographic coordinates to pixel coordinates
            segment_start_pixel = _geo_to_pixel(
                route_points[i]['lon'], route_points[i]['lat'],
                bounds, cost_surface.shape
            )
            segment_end_pixel = _geo_to_pixel(
                route_points[i+1]['lon'], route_points[i+1]['lat'],
                bounds, cost_surface.shape
            )

            # Find path for this segment
            segment_result = pathfinder.find_path(segment_start_pixel, segment_end_pixel)

            if segment_result is None:
                project.status = 'failed'
                db.session.commit()
                return jsonify({'error': f'No valid path found for segment {i+1}'}), 400

            # Add segment path (skip first point if not the first segment to avoid duplicates)
            if i == 0:
                all_paths.extend(segment_result['path'])
            else:
                all_paths.extend(segment_result['path'][1:])

            total_cost += segment_result['total_cost']

        # Create combined path result
        path_result = {
            'path': all_paths,
            'total_cost': total_cost,
            'distance': len(all_paths)
        }

        # Convert pixel path to geographic coordinates
        path_coords = pathfinder.path_to_coordinates(
            path_result['path'], bounds, 30
        )

        # Simplify path to reduce points (use lower tolerance to keep more points)
        simplified_path = pathfinder.simplify_path(path_result['path'], tolerance=1)
        simplified_coords = pathfinder.path_to_coordinates(simplified_path, bounds, 30)

        # Engineering validation - use full path for accurate tower placement
        validator = EngineeringValidator(current_app.config)
        validation_result = validator.validate_route(path_coords)

        # Generate tower positions - use full path for proper spacing
        tower_positions = validator.generate_tower_positions(path_coords)

        # Calculate detailed costs
        detailed_costs = validator.calculate_detailed_costs(path_coords, tower_positions)

        # Create GeoJSON
        route_geojson = {
            'type': 'Feature',
            'properties': {
                'project_id': project.id,
                'total_cost': detailed_costs['total_cost'],
                'cost_per_km': detailed_costs['cost_per_km'],
                'length_m': validation_result['metrics']['total_length_m'],
                'length_km': detailed_costs['total_length_km'],
                'estimated_towers': len(tower_positions),
                'avg_span_length_m': detailed_costs['avg_span_length_m']
            },
            'geometry': {
                'type': 'LineString',
                'coordinates': simplified_coords
            }
        }

        # Save route
        route = Route(
            project_id=project.id,
            total_length=validation_result['metrics']['total_length_m'],
            total_cost=detailed_costs['total_cost'],
            estimated_towers=len(tower_positions),
            is_valid=validation_result['is_valid'],
            algorithm='dijkstra'
        )
        route.set_geometry(route_geojson)
        route.set_validation_errors(validation_result['errors'])

        db.session.add(route)

        # Update project status
        project.status = 'completed'
        db.session.commit()

        return jsonify({
            'message': 'Route optimized successfully',
            'route_id': route.id,
            'route': route_geojson,
            'tower_positions': tower_positions,
            'validation': validation_result,
            'cost_breakdown': detailed_costs,
            'metadata': metadata
        })

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
    Export route as Shapefile or GeoJSON

    Query params:
        format: 'geojson' or 'shapefile' (default: geojson)
    """
    route = Route.query.get_or_404(route_id)
    project = Project.query.get(route.project_id)

    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    export_format = request.args.get('format', 'geojson')

    if export_format == 'geojson':
        # Return GeoJSON directly
        geojson = route.get_geometry()
        return jsonify(geojson)

    elif export_format == 'shapefile':
        # TODO: Implement shapefile export using geopandas
        return jsonify({'error': 'Shapefile export not yet implemented'}), 501

    else:
        return jsonify({'error': 'Invalid format. Use geojson or shapefile'}), 400


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

