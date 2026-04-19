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
# from app.optimizer.qgis_routing_workflow import QGISRoutingWorkflow  # QGIS workflow - optional enhancement
from app.services.corridor_restriction import CorridorRestrictionService
from app.services.gis_data_loader import load_layers_for_bounds
from app.services.uganda_gis_loader import UgandaGISLoader
from app.services.elevation_sampling import sample_elevations_m, downsample_for_chart

api_bp = Blueprint('api', __name__)


def convert_numpy_types(obj):
    """
    Recursively convert numpy types to native Python types for JSON serialization.
    Handles: numpy.float32, numpy.float64, numpy.int32, numpy.int64, numpy.ndarray, etc.
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj


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


def _run_pathfinder(cost_surface, bounds, route_points, algorithm, resolution_m=30):
    """Run dijkstra or astar and return path_result, path_coords, pathfinder for a single algorithm."""
    try:
        # Check cost surface size
        height, width = cost_surface.shape
        total_pixels = height * width
        print(f"🔍 Pathfinding on {width} × {height} = {total_pixels:,} pixels")

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
        path_coords = pathfinder.path_to_coordinates(path_result['path'], bounds, resolution_m)
        return path_result, path_coords, pathfinder
    except MemoryError as e:
        print(f"❌ Memory error in pathfinding: {str(e)}")
        raise MemoryError("Route area too large for pathfinding. Please add waypoints to break the route into smaller segments.")


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
        # Validate project has required coordinates
        if project.start_lat is None or project.start_lon is None:
            return jsonify({'error': 'Start point not set'}), 400
        if project.end_lat is None or project.end_lon is None:
            return jsonify({'error': 'End point not set'}), 400

        project.status = 'processing'
        db.session.commit()

        ahp_weights = project.get_ahp_weights() or current_app.config['DEFAULT_AHP_WEIGHTS']
        
        # Get waypoints if any
        proj_metadata = project.get_metadata()
        waypoints_data = proj_metadata.get('waypoints', []) if proj_metadata else []
        
        # Calculate geographic span including waypoints
        all_lons = [project.start_lon, project.end_lon] + [wp['lon'] for wp in waypoints_data if 'lon' in wp]
        all_lats = [project.start_lat, project.end_lat] + [wp['lat'] for wp in waypoints_data if 'lat' in wp]
        
        lon_span = max(all_lons) - min(all_lons)
        lat_span = max(all_lats) - min(all_lats)
        span_deg = max(lon_span, lat_span)
        
        # Calculate approximate distance in km for logging and validation
        approx_distance_km = span_deg * 111  # Rough conversion (1 degree ≈ 111 km)
        print(f"📏 Route span: {lon_span:.3f}° lon × {lat_span:.3f}° lat (~{approx_distance_km:.1f} km)")
        print(f"📍 Waypoints: {len(waypoints_data)} intermediate points")
        
        # Wider margin for long routes (multi-district): scale with geographic span
        # For very long routes (>100km), use larger margins to ensure corridor coverage
        if approx_distance_km > 100:
            margin = max(0.15, min(2.0, 0.2 + 0.15 * span_deg))
            print(f"🗺️ Long route detected - using extended margin: {margin:.3f}°")
        else:
            margin = max(0.06, min(1.2, 0.12 + 0.25 * span_deg))
        
        bounds = [
            min(all_lons) - margin,
            min(all_lats) - margin,
            max(all_lons) + margin,
            max(all_lats) + margin
        ]

        cost_generator = CostSurfaceGenerator(current_app.config)
        # Prefer real GIS data if present; otherwise fall back to demo layers.
        # We precompute an expected raster shape so real rasters can be resampled consistently.
        layers_data = {}
        data_source = "demo"

        # Auto-adjust resolution based on area size to prevent memory errors
        resolution_m = 30  # Start with 30m resolution
        # Cap grid size to reduce RAM (float32 pathfinder + scipy temps still need headroom)
        # Increased limit for better long-distance route quality with real DEM
        max_pixels = 2_500_000 if approx_distance_km > 100 else 1_500_000
        # For very long routes, allow up to 2km resolution to handle district-to-district routing
        max_resolution = 2000 if approx_distance_km > 200 else (1500 if approx_distance_km > 100 else 1000)

        try:
            # Calculate initial shape
            shape = _shape_from_bounds(bounds, resolution_m=resolution_m)
            height, width = shape
            total_pixels = height * width

            # If too large, automatically increase resolution (lower detail)
            iteration = 0
            while total_pixels > max_pixels and resolution_m < max_resolution:
                # Calculate exact scaling factor needed
                scale_factor = (total_pixels / max_pixels) ** 0.5
                resolution_m *= max(1.3, scale_factor)  # At least 1.3x, or more if needed
                shape = _shape_from_bounds(bounds, resolution_m=resolution_m)
                height, width = shape
                total_pixels = height * width
                iteration += 1
                print(f"⚠️ Area too large, adjusting resolution to {resolution_m:.0f}m (iteration {iteration})")

                # Safety check to prevent infinite loop
                if iteration > 15:
                    print(f"❌ Could not reduce to acceptable size after 15 iterations")
                    break

            estimated_memory_mb = (total_pixels * 8) / (1024 * 1024)  # 8 bytes per float64

            print(f"📊 Raster dimensions: {width} × {height} = {total_pixels:,} pixels")
            print(f"📏 Resolution: {resolution_m:.0f}m per pixel")
            print(f"💾 Estimated memory: {estimated_memory_mb:.1f} MB")

            # Check if still too large
            if total_pixels > max_pixels:
                # Calculate approximate route distance
                min_lon, min_lat, max_lon, max_lat = bounds
                approx_distance_km = ((max_lon - min_lon) ** 2 + (max_lat - min_lat) ** 2) ** 0.5 * 111

                print(f"❌ Area still too large even at {resolution_m:.0f}m resolution")
                print(f"📏 Approximate route distance: {approx_distance_km:.0f} km")

                # Suggest number of waypoints needed based on distance
                if approx_distance_km > 300:
                    segment_size = 75  # For very long routes, use smaller segments
                elif approx_distance_km > 150:
                    segment_size = 60
                else:
                    segment_size = 50
                    
                num_segments = int(approx_distance_km / segment_size) + 1
                num_waypoints = max(1, num_segments - 1)

                # Provide helpful guidance based on route length
                if approx_distance_km > 200:
                    guidance = f"This is a very long route (~{approx_distance_km:.0f} km) crossing multiple districts. "
                    guidance += f"Add {num_waypoints} waypoints to break it into {num_segments} segments of ~{segment_size}km each. "
                    guidance += "Place waypoints at major towns or landmarks along the desired path."
                else:
                    guidance = f"Route area is large (~{approx_distance_km:.0f} km). "
                    guidance += f"Add {num_waypoints} waypoint(s) to break the route into {num_segments} segments of ~{segment_size}km each."

                return jsonify({
                    'error': guidance,
                    'route_distance_km': round(approx_distance_km, 1),
                    'recommended_waypoints': num_waypoints,
                    'recommended_segment_size_km': segment_size
                }), 400

            try:
                layers_data = load_layers_for_bounds(current_app.config, tuple(bounds), shape)
                if layers_data:
                    data_source = "real"
            except Exception as layer_error:
                print(f"⚠️ Could not load real GIS layers: {str(layer_error)}")
                print(f"⚠️ Falling back to demo data")
                layers_data = None
        except MemoryError as e:
            print(f"❌ Memory error: {str(e)}")
            return jsonify({
                'error': 'Route area too large. Please add waypoints to break the route into smaller segments (recommended: segments < 50km each).'
            }), 400
        except Exception as e:
            print(f"⚠️ Error loading layers: {str(e)}")
            layers_data = {}
            data_source = "demo"
        if not layers_data:
            layers_data = _create_demo_layers(bounds, current_app.config, shape)

        cost_surface, metadata = cost_generator.generate_composite_cost_surface(
            bounds, ahp_weights, layers_data, resolution=resolution_m, grid_shape=shape
        )
        cost_surface = np.asarray(cost_surface, dtype=np.float32)
        metadata = metadata or {}
        metadata["data_source"] = data_source
        metadata["resolution_m"] = resolution_m

        cost_surface_path = os.path.join(
            current_app.config['DATA_FOLDER'],
            f'cost_surface_project_{project_id}.tif'
        )
        cost_generator.save_cost_surface(cost_surface, cost_surface_path, bounds)
        cost_surf_record = CostSurface(
            project_id=project.id,
            file_path=cost_surface_path,
            resolution=int(resolution_m),
            layer_weights=json.dumps(ahp_weights)
        )
        cost_surf_record.set_bounds(bounds)
        db.session.add(cost_surf_record)

        # Build route points from start -> waypoints -> end
        route_points = [{'lat': project.start_lat, 'lon': project.start_lon}]
        route_points.extend(waypoints_data)
        route_points.append({'lat': project.end_lat, 'lon': project.end_lon})
        
        print(f"🛤️ Route has {len(route_points)} points total ({len(waypoints_data)} waypoints)")

        comparison = {}
        path_result = None
        path_coords = None
        pathfinder = None
        chosen_algorithm = algorithm

        if compare:
            # Create validator for distance calculations
            temp_validator = EngineeringValidator(current_app.config)

            for algo in ('dijkstra', 'astar'):
                pr, pc, pf = _run_pathfinder(cost_surface, bounds, route_points, algo, resolution_m)
                if pr is not None:
                    # Calculate actual distance in kilometers
                    distance_m = temp_validator._calculate_route_length(pc)
                    distance_km = distance_m / 1000.0

                    comparison[algo] = {
                        'total_cost': pr['total_cost'],
                        'path_length_pixels': pr['distance'],
                        'distance_km': distance_km,
                        'path_coords_count': len(pc),
                    }
                else:
                    comparison[algo] = None
            # Use requested algorithm for main result
            path_result, path_coords, pathfinder = _run_pathfinder(cost_surface, bounds, route_points, algorithm, resolution_m)
        else:
            path_result, path_coords, pathfinder = _run_pathfinder(cost_surface, bounds, route_points, algorithm, resolution_m)

        if path_result is None or path_coords is None or pathfinder is None:
            project.status = 'failed'
            db.session.commit()
            return jsonify({'error': 'No valid path found for the selected algorithm'}), 400

        simplified_path = pathfinder.simplify_path(path_result['path'], tolerance=1)
        simplified_coords = pathfinder.path_to_coordinates(simplified_path, bounds, resolution_m)

        validator = EngineeringValidator(current_app.config)
        validation_result = validator.validate_route(path_coords)
        tower_positions = validator.generate_tower_positions(path_coords)
        detailed_costs = validator.calculate_detailed_costs(path_coords, tower_positions)

        # Elevation (m) for towers + route profile chart — avoids all-zero display when DEM is synthetic
        try:
            tower_elevations = sample_elevations_m(current_app.config, tower_positions)
            tower_positions = [
                [tower_positions[i][0], tower_positions[i][1], tower_elevations[i]]
                for i in range(len(tower_positions))
            ]
        except Exception as ex:
            print(f"⚠️ Tower elevation sampling: {ex}")
        path_elevations = sample_elevations_m(current_app.config, path_coords)
        chart_idx, chart_elev = downsample_for_chart(path_elevations)
        route_elevation = {
            'min_m': float(min(path_elevations)) if path_elevations else None,
            'max_m': float(max(path_elevations)) if path_elevations else None,
            'avg_m': float(sum(path_elevations) / len(path_elevations)) if path_elevations else None,
            'chart_indices': chart_idx,
            'chart_elevations_m': chart_elev,
        }

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

        # Add resolution info message if adjusted
        message = 'Route optimized successfully'
        if resolution_m > 30:
            message += f' (resolution adjusted to {resolution_m:.0f}m for large area)'

        avoidance_metrics = _compute_avoidance_metrics(layers_data, path_result['path'], shape)

        response = {
            'message': message,
            'route_id': route.id,
            'route': route_geojson,
            'tower_positions': tower_positions,
            'validation': validation_result,
            'cost_breakdown': detailed_costs,
            'metadata': proj_metadata,
            'algorithm_used': chosen_algorithm,
            'resolution_m': resolution_m,
            'cost_surface_metadata': metadata,
            'avoidance_metrics': avoidance_metrics,
            'route_elevation': route_elevation,
        }
        if comparison:
            response['algorithm_comparison'] = comparison

        # Convert all numpy types to native Python types for JSON serialization
        response = convert_numpy_types(response)

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
        try:
            te = sample_elevations_m(current_app.config, tower_positions)
            tower_positions = [
                [tower_positions[i][0], tower_positions[i][1], te[i]]
                for i in range(len(tower_positions))
            ]
        except Exception as ex:
            print(f"⚠️ Tower elevation (generate_towers): {ex}")

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


@api_bp.route('/gis/layers/<layer_name>', methods=['GET'])
@login_required
def get_gis_layer(layer_name):
    """
    Load individual GIS layer as GeoJSON for map display.
    Supports shapefiles and GeoJSON files.
    Query params: min_lon, min_lat, max_lon, max_lat (map bounds)
    Loads ALL features without truncation
    """
    try:
        from app.services.uganda_gis_loader import UgandaGISLoader
        from flask import Response
        import json
        
        # Get map bounds
        min_lon = float(request.args.get('min_lon', 29.5))
        min_lat = float(request.args.get('min_lat', 0.5))
        max_lon = float(request.args.get('max_lon', 35.0))
        max_lat = float(request.args.get('max_lat', 4.5))
        bounds = (min_lon, min_lat, max_lon, max_lat)
        
        # Load layer using UgandaGISLoader - ALL features
        from config import Config
        loader = UgandaGISLoader(Config())
        
        start_time = __import__('time').time()
        geojson = loader.load_layer_geojson(layer_name, bounds)
        load_time = __import__('time').time() - start_time
        
        if geojson is None:
            return jsonify({
                'type': 'FeatureCollection',
                'features': [],
                'message': f'No data available for layer: {layer_name}'
            })
        
        feature_count = len(geojson.get('features', []))
        print(f"✅ Loaded {layer_name}: {feature_count} features in {load_time:.2f}s")
        
        # For large datasets, use compact JSON to reduce size
        if feature_count > 1000:
            # Compact JSON without spaces
            json_str = json.dumps(geojson, separators=(',', ':'))
            print(f"📦 Response size: {len(json_str) / 1024 / 1024:.2f} MB")
            return Response(json_str, mimetype='application/json')
        else:
            return jsonify(geojson)
        
    except Exception as e:
        print(f"Error loading layer {layer_name}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'type': 'FeatureCollection',
            'features': [],
            'error': str(e)
        }), 500


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

        elevations = sample_elevations_m(current_app.config, coords_wgs84)

        target_crs = request.args.get('crs') or current_app.config.get('PREFERRED_PROJECTED_CRS', 'EPSG:21096')
        transformer = Transformer.from_crs('EPSG:4326', target_crs, always_xy=True)
        xyz = []
        for (lon, lat), elev in zip(coords_wgs84, elevations):
            easting, northing = transformer.transform(lon, lat)
            xyz.append([easting, northing, elev])

        return jsonify({
            'crs': target_crs,
            'crs_description': f'Eastings, Northings, elevation (m). Elevation from DEM data (or default 1000m for Uganda).',
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
        layers_data = _create_demo_layers(bounds, current_app.config, out_shape)
    result = {}
    min_lon, min_lat, max_lon, max_lat = bounds
    height, width = layers_data.get('dem', layers_data.get('elevation', np.zeros((60, 60)))).shape
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


@api_bp.route('/projects/<int:project_id>/cost-surface-image', methods=['GET'])
@login_required
def get_cost_surface_image(project_id):
    """
    Get cost surface as a PNG image for visualization.
    Returns a color-coded heatmap showing high-cost (red) and low-cost (green) areas.
    """
    import io
    from PIL import Image
    
    project = Project.query.get_or_404(project_id)
    
    if project.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Find the cost surface for this project
    cost_surface_record = CostSurface.query.filter_by(project_id=project_id).first()
    if not cost_surface_record:
        return jsonify({'error': 'Cost surface not found. Optimize a route first.'}), 404
    
    # Load the cost surface
    cost_surface_path = cost_surface_record.file_path
    if not os.path.exists(cost_surface_path):
        # Try loading from .npy if GeoTIFF doesn't exist
        npy_path = cost_surface_path.replace('.tif', '.npy')
        if os.path.exists(npy_path):
            cost_surface = np.load(npy_path)
        else:
            return jsonify({'error': 'Cost surface file not found'}), 404
    else:
        try:
            import rasterio
            with rasterio.open(cost_surface_path) as src:
                cost_surface = src.read(1)
        except Exception as e:
            return jsonify({'error': f'Failed to load cost surface: {str(e)}'}), 500
    
    # Normalize cost surface to 0-255 for image
    min_val = np.nanmin(cost_surface)
    max_val = np.nanmax(cost_surface)
    if max_val > min_val:
        normalized = ((cost_surface - min_val) / (max_val - min_val) * 255).astype(np.uint8)
    else:
        normalized = np.zeros_like(cost_surface, dtype=np.uint8)
    
    # Create color heatmap matching the reference image
    # Color scale: Green (low) -> Light Green -> Yellow -> Orange -> Red (high)
    # Based on cost values: 156-220 (green), 220-284 (light green), 284-348 (yellow), 348-412 (orange), 412-476 (red)
    height, width = normalized.shape
    rgba_image = np.zeros((height, width, 4), dtype=np.uint8)
    
    # Calculate actual cost range for legend
    cost_range = max_val - min_val
    
    for i in range(height):
        for j in range(width):
            val = normalized[i, j]
            # Normalize to 0-1
            t = val / 255.0
            
            # Color gradient matching the image:
            # Dark Green (low cost) -> Green -> Light Green -> Yellow -> Orange -> Red (high cost)
            if t < 0.2:
                # Dark Green to Green (156-220 equivalent)
                r = 0
                g = int(150 + 105 * (t / 0.2))  # 150-255
                b = 0
            elif t < 0.4:
                # Green to Light Green (220-284 equivalent)
                r = int(144 * ((t - 0.2) / 0.2))  # 0-144
                g = 255
                b = 0
            elif t < 0.6:
                # Light Green to Yellow (284-348 equivalent)
                r = int(144 + 111 * ((t - 0.4) / 0.2))  # 144-255
                g = 255
                b = 0
            elif t < 0.8:
                # Yellow to Orange (348-412 equivalent)
                r = 255
                g = int(255 - 100 * ((t - 0.6) / 0.2))  # 255-155
                b = 0
            else:
                # Orange to Red (412-476 equivalent)
                r = 255
                g = int(155 - 155 * ((t - 0.8) / 0.2))  # 155-0
                b = 0
            
            rgba_image[i, j] = [r, g, b, 200]  # Slightly more opaque for better visibility
    
    # Create PIL Image with transparency
    img = Image.fromarray(rgba_image, 'RGBA')
    
    # Save to bytes
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    # Return with cost scale metadata
    response = send_file(
        img_io,
        mimetype='image/png',
        as_attachment=False,
        download_name=f'cost_surface_project_{project_id}.png'
    )
    
    # Add cost scale headers for frontend legend
    response.headers['X-Cost-Min'] = str(round(min_val, 2))
    response.headers['X-Cost-Max'] = str(round(max_val, 2))
    
    return response


def _create_demo_layers(bounds, config, shape=None):
    """
    Create demo GIS layers for testing
    In production, replace with actual data loading

    Args:
        bounds: [min_lon, min_lat, max_lon, max_lat]
        config: Flask config
        shape: Optional (height, width) tuple. If None, calculates from bounds at 30m resolution
    """
    if shape is None:
        # Calculate dimensions at 30m resolution (legacy behavior)
        min_lon, min_lat, max_lon, max_lat = bounds
        width = int((max_lon - min_lon) * 111320 / 30)
        height = int((max_lat - min_lat) * 111320 / 30)
    else:
        height, width = shape

    # Create synthetic layers with memory-efficient dtypes
    # Synthetic DEM in plausible meters (800–1600 m) when no real SRTM GeoTIFF is present
    dem = (800.0 + np.random.rand(height, width).astype(np.float32) * 800.0)
    land_use = np.random.choice([10, 30, 40, 50, 80, 90], size=(height, width)).astype(np.int16)
    settlements = np.random.choice([0, 1], size=(height, width), p=[0.95, 0.05]).astype(np.int8)
    protected_areas = np.random.choice([0, 1], size=(height, width), p=[0.9, 0.1]).astype(np.int8)
    roads = np.random.choice([0, 1], size=(height, width), p=[0.98, 0.02]).astype(np.int8)

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
    Automatically adjusts resolution for large areas to prevent memory issues.
    """
    min_lon, min_lat, max_lon, max_lat = bounds

    # Calculate initial dimensions
    width = int((max_lon - min_lon) * 111320 / resolution_m)
    height = int((max_lat - min_lat) * 111320 / resolution_m)

    # Limit maximum dimensions to prevent memory issues
    # Increased limits for better long-distance route quality with real DEM data
    MAX_DIMENSION = 1500  # Maximum pixels in any dimension (memory-safe)
    MAX_TOTAL_PIXELS = 2_500_000  # Must match optimize_route cap

    # If dimensions are too large, adjust resolution
    if width > MAX_DIMENSION or height > MAX_DIMENSION or (width * height) > MAX_TOTAL_PIXELS:
        # Calculate required resolution to fit within limits
        scale_factor_width = width / MAX_DIMENSION if width > MAX_DIMENSION else 1
        scale_factor_height = height / MAX_DIMENSION if height > MAX_DIMENSION else 1
        scale_factor_total = ((width * height) / MAX_TOTAL_PIXELS) ** 0.5 if (width * height) > MAX_TOTAL_PIXELS else 1

        scale_factor = max(scale_factor_width, scale_factor_height, scale_factor_total)

        # Adjust resolution
        adjusted_resolution = resolution_m * scale_factor
        width = int((max_lon - min_lon) * 111320 / adjusted_resolution)
        height = int((max_lat - min_lat) * 111320 / adjusted_resolution)

        print(f"⚠️ Large area detected! Adjusted resolution from {resolution_m}m to {adjusted_resolution:.1f}m")
        print(f"   Original size would be: {int((max_lon - min_lon) * 111320 / resolution_m)} × {int((max_lat - min_lat) * 111320 / resolution_m)}")
        print(f"   Adjusted size: {width} × {height}")

    width = max(1, width)
    height = max(1, height)
    return (height, width)


def _compute_avoidance_metrics(layers_data, path_pixels, shape):
    """
    Beginner-friendly scores: percent of route pixels that stay OFF costly cells
    (settlements, protected, water, built-up) in the same raster used for optimization.
    """
    if not path_pixels or not layers_data:
        return {
            'explanation': 'After optimization, we check each pixel along the path against the input maps.'
        }
    h, w = int(shape[0]), int(shape[1])

    def _clip(r, c):
        if 0 <= r < h and 0 <= c < w:
            return r, c
        return None

    out = {}

    if 'settlements' in layers_data:
        arr = np.asarray(layers_data['settlements'])
        bad = tot = 0
        for r, c in path_pixels:
            cc = _clip(r, c)
            if not cc:
                continue
            tot += 1
            if arr[cc[0], cc[1]] > 0:
                bad += 1
        if tot:
            out['settlements_clear_pct'] = round(100.0 * (1.0 - bad / tot), 1)

    if 'protected_areas' in layers_data:
        arr = np.asarray(layers_data['protected_areas'])
        bad = tot = 0
        for r, c in path_pixels:
            cc = _clip(r, c)
            if not cc:
                continue
            tot += 1
            if arr[cc[0], cc[1]] > 0:
                bad += 1
        if tot:
            out['protected_areas_clear_pct'] = round(100.0 * (1.0 - bad / tot), 1)

    if 'land_use' in layers_data:
        arr = np.asarray(layers_data['land_use'])
        water = built = tot = 0
        for r, c in path_pixels:
            cc = _clip(r, c)
            if not cc:
                continue
            tot += 1
            v = int(arr[cc[0], cc[1]])
            if v == 80:
                water += 1
            if v == 50:
                built += 1
        if tot:
            out['water_clear_pct'] = round(100.0 * (1.0 - water / tot), 1)
            out['built_up_clear_pct'] = round(100.0 * (1.0 - built / tot), 1)

    out['explanation'] = (
        'Higher bars mean more of the line avoids that type of costly area in the analysis grid '
        '(not crossing settlement/protected pixels, water, or dense urban land-use cells).'
    )
    pct_vals = [v for k, v in out.items() if k.endswith('_pct') and isinstance(v, (int, float))]
    if pct_vals:
        out['overall_avoidance_score'] = round(sum(pct_vals) / len(pct_vals), 1)
    return out


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

