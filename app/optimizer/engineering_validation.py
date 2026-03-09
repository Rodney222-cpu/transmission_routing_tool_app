"""
Engineering Validation Module for 400kV Lattice Tower Transmission Lines
Validates routes against technical constraints specific to Uganda case study
"""
import numpy as np
from typing import List, Tuple, Dict


class EngineeringValidator:
    """
    Validates transmission line routes against engineering constraints
    Specific to 400kV steel lattice towers (Olwiyo-South Sudan line)
    """
    
    def __init__(self, config):
        """
        Initialize validator with configuration

        Args:
            config: Flask app configuration object
        """
        self.config = config
        self.min_span = config.get('MIN_TOWER_SPAN', 200)  # 200m
        self.max_span = config.get('MAX_TOWER_SPAN', 450)  # 450m
        self.typical_span = config.get('TYPICAL_TOWER_SPAN', 350)  # 350m
        self.max_slope = config.get('MAX_SLOPE_ANGLE', 30)  # 30 degrees
        self.min_clearance = config.get('MIN_GROUND_CLEARANCE', 7.6)  # 7.6m
        self.corridor_width = config.get('TOTAL_CORRIDOR_WIDTH', 60)  # 60m
    
    def validate_route(self, path_coords: List[Tuple[float, float]], 
                      dem_data: np.ndarray = None,
                      resolution: float = 30) -> Dict:
        """
        Validate a route against all engineering constraints
        
        Args:
            path_coords: List of (lon, lat) coordinates
            dem_data: Digital Elevation Model array (optional)
            resolution: Spatial resolution in meters
        
        Returns:
            dict containing:
                - is_valid: Boolean indicating if route passes all checks
                - errors: List of validation errors
                - warnings: List of warnings
                - metrics: Dictionary of route metrics
        """
        errors = []
        warnings = []
        metrics = {}
        
        # Calculate total route length
        total_length = self._calculate_route_length(path_coords)
        metrics['total_length_m'] = total_length
        metrics['total_length_km'] = total_length / 1000
        
        # Estimate number of towers based on typical span
        estimated_towers = int(total_length / self.typical_span) + 1
        metrics['estimated_towers'] = estimated_towers
        
        # Validate tower spans
        span_validation = self._validate_tower_spans(path_coords)
        if not span_validation['valid']:
            errors.extend(span_validation['errors'])
        metrics['tower_spans'] = span_validation['spans']
        
        # Validate terrain slope if DEM is provided
        if dem_data is not None:
            slope_validation = self._validate_slope(path_coords, dem_data, resolution)
            if not slope_validation['valid']:
                errors.extend(slope_validation['errors'])
            if slope_validation['warnings']:
                warnings.extend(slope_validation['warnings'])
            metrics['max_slope_deg'] = slope_validation['max_slope']
            metrics['avg_slope_deg'] = slope_validation['avg_slope']
        
        # Validate corridor width constraints
        corridor_validation = self._validate_corridor_width(path_coords)
        if corridor_validation['warnings']:
            warnings.extend(corridor_validation['warnings'])
        
        # Calculate estimated cost
        metrics['estimated_cost_usd'] = self._estimate_construction_cost(
            total_length, estimated_towers, metrics.get('max_slope_deg', 0)
        )
        
        is_valid = len(errors) == 0
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'metrics': metrics
        }
    
    def _calculate_route_length(self, coords: List[Tuple[float, float]]) -> float:
        """
        Calculate total route length in meters using Haversine formula
        
        Args:
            coords: List of (lon, lat) coordinates
        
        Returns:
            Total length in meters
        """
        total_length = 0.0
        
        for i in range(len(coords) - 1):
            lon1, lat1 = coords[i]
            lon2, lat2 = coords[i + 1]
            
            # Haversine formula
            R = 6371000  # Earth radius in meters
            
            lat1_rad = np.radians(lat1)
            lat2_rad = np.radians(lat2)
            delta_lat = np.radians(lat2 - lat1)
            delta_lon = np.radians(lon2 - lon1)
            
            a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            
            distance = R * c
            total_length += distance
        
        return total_length
    
    def _validate_tower_spans(self, coords: List[Tuple[float, float]]) -> Dict:
        """
        Validate that tower spans are within acceptable limits
        
        Args:
            coords: List of (lon, lat) coordinates
        
        Returns:
            dict with validation results
        """
        errors = []
        spans = []
        
        for i in range(len(coords) - 1):
            lon1, lat1 = coords[i]
            lon2, lat2 = coords[i + 1]
            
            # Calculate span distance
            span = self._haversine_distance(lat1, lon1, lat2, lon2)
            spans.append(span)
            
            if span < self.min_span:
                errors.append(
                    f"Span {i+1} ({span:.1f}m) is below minimum ({self.min_span}m)"
                )
            elif span > self.max_span:
                errors.append(
                    f"Span {i+1} ({span:.1f}m) exceeds maximum ({self.max_span}m)"
                )
        
        avg_span = np.mean(spans) if spans else 0
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'spans': spans,
            'avg_span': avg_span,
            'min_span': min(spans) if spans else 0,
            'max_span': max(spans) if spans else 0
        }
    
    def _haversine_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371000  # Earth radius in meters
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c

    def _validate_slope(self, coords: List[Tuple[float, float]],
                       dem_data: np.ndarray, resolution: float) -> Dict:
        """
        Validate terrain slope along the route

        Args:
            coords: List of (lon, lat) coordinates
            dem_data: Digital Elevation Model array
            resolution: Spatial resolution in meters

        Returns:
            dict with validation results
        """
        errors = []
        warnings = []
        slopes = []

        # Sample elevations along the route
        # This is simplified - in production, you'd interpolate from DEM
        for i in range(len(coords) - 1):
            # Calculate slope between consecutive points
            # Placeholder: In real implementation, extract elevation from DEM
            # For now, we'll use a simplified approach

            # Estimate slope (this would use actual DEM data)
            estimated_slope = 0  # Placeholder
            slopes.append(estimated_slope)

            if estimated_slope > self.max_slope:
                errors.append(
                    f"Segment {i+1} slope ({estimated_slope:.1f}°) exceeds maximum ({self.max_slope}°)"
                )
            elif estimated_slope > 25:
                warnings.append(
                    f"Segment {i+1} has steep slope ({estimated_slope:.1f}°) - may require special tower design"
                )

        max_slope = max(slopes) if slopes else 0
        avg_slope = np.mean(slopes) if slopes else 0

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'max_slope': max_slope,
            'avg_slope': avg_slope
        }

    def _validate_corridor_width(self, coords: List[Tuple[float, float]]) -> Dict:
        """
        Validate 60m corridor width (10m RoW + 25m Wayleave each side)

        Args:
            coords: List of (lon, lat) coordinates

        Returns:
            dict with validation results
        """
        warnings = []

        # Check for sharp turns that might violate corridor width
        for i in range(1, len(coords) - 1):
            # Calculate angle between consecutive segments
            angle = self._calculate_turn_angle(coords[i-1], coords[i], coords[i+1])

            if angle < 30:  # Sharp turn
                warnings.append(
                    f"Sharp turn at point {i+1} ({angle:.1f}°) - verify {self.corridor_width}m corridor clearance"
                )

        return {
            'warnings': warnings
        }

    def _calculate_turn_angle(self, p1: Tuple[float, float],
                             p2: Tuple[float, float],
                             p3: Tuple[float, float]) -> float:
        """
        Calculate the turn angle at point p2

        Args:
            p1, p2, p3: Consecutive points as (lon, lat)

        Returns:
            Angle in degrees
        """
        # Convert to vectors
        v1 = np.array([p2[0] - p1[0], p2[1] - p1[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])

        # Calculate angle
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.degrees(np.arccos(cos_angle))

        return angle

    def _estimate_construction_cost(self, length_m: float,
                                   num_towers: int,
                                   max_slope: float) -> float:
        """
        Estimate construction cost for 400kV line

        Args:
            length_m: Route length in meters
            num_towers: Number of towers
            max_slope: Maximum slope in degrees

        Returns:
            Estimated cost in USD
        """
        # Cost estimates for 400kV transmission line (Uganda context)
        # These are approximate values - adjust based on actual project data

        # Base costs
        cost_per_km = 500000  # USD per km for conductors and hardware
        cost_per_tower = 150000  # USD per lattice tower (400kV)

        # Terrain multiplier
        terrain_multiplier = 1.0
        if max_slope > 25:
            terrain_multiplier = 1.5  # Difficult terrain
        elif max_slope > 15:
            terrain_multiplier = 1.2  # Moderate terrain

        # Calculate total cost
        conductor_cost = (length_m / 1000) * cost_per_km
        tower_cost = num_towers * cost_per_tower

        total_cost = (conductor_cost + tower_cost) * terrain_multiplier

        # Add 20% for contingency and project management
        total_cost *= 1.2

        return total_cost

    def generate_tower_positions(self, coords: List[Tuple[float, float]],
                                target_span: float = None) -> List[Tuple[float, float]]:
        """
        Generate optimal tower positions along the route

        Args:
            coords: List of (lon, lat) coordinates defining the route
            target_span: Target span distance in meters (default: typical_span)

        Returns:
            List of (lon, lat) coordinates for tower positions
        """
        if target_span is None:
            target_span = self.typical_span

        tower_positions = [coords[0]]  # Start with first point

        accumulated_distance = 0
        last_tower_idx = 0

        for i in range(1, len(coords)):
            # Calculate distance from last tower
            segment_dist = self._haversine_distance(
                coords[i-1][1], coords[i-1][0],
                coords[i][1], coords[i][0]
            )
            accumulated_distance += segment_dist

            # Place tower if we've exceeded target span
            if accumulated_distance >= target_span:
                tower_positions.append(coords[i])
                accumulated_distance = 0
                last_tower_idx = i

        # Always include the end point
        if coords[-1] not in tower_positions:
            tower_positions.append(coords[-1])

        return tower_positions

    def calculate_detailed_costs(self, path_coords: List[Tuple[float, float]],
                                 tower_positions: List[Tuple[float, float]],
                                 dem_data: np.ndarray = None) -> Dict:
        """
        Calculate detailed cost breakdown for the transmission line

        Args:
            path_coords: List of (lon, lat) coordinates for the route
            tower_positions: List of (lon, lat) coordinates for tower locations
            dem_data: Digital Elevation Model array (optional, for terrain classification)

        Returns:
            dict containing detailed cost breakdown
        """
        # Get cost constants from config
        costs = self.config.get('COST_ESTIMATION', {})

        # Calculate total route length
        total_length_km = 0
        for i in range(1, len(path_coords)):
            segment_dist = self._haversine_distance(
                path_coords[i-1][1], path_coords[i-1][0],
                path_coords[i][1], path_coords[i][0]
            )
            total_length_km += segment_dist / 1000  # Convert to km

        # Calculate number of towers
        num_towers = len(tower_positions)

        # Classify terrain (simplified - can be enhanced with actual DEM data)
        # For now, use average costs
        tower_cost_per_unit = costs.get('tower_cost_average', 55000)
        foundation_cost_per_unit = costs.get('foundation_moderate', 25000)

        # Calculate individual cost components
        tower_costs = num_towers * tower_cost_per_unit
        foundation_costs = num_towers * foundation_cost_per_unit
        conductor_costs = total_length_km * costs.get('conductor_cost_per_km', 85000)
        installation_costs = total_length_km * costs.get('installation_per_km', 120000)
        row_costs = total_length_km * costs.get('row_acquisition_per_km', 50000)

        # Subtotal (construction costs)
        construction_subtotal = (tower_costs + foundation_costs + conductor_costs +
                                installation_costs + row_costs)

        # Engineering and design
        engineering_costs = construction_subtotal * costs.get('engineering_percentage', 0.08)

        # Contingency
        contingency_costs = construction_subtotal * costs.get('contingency_percentage', 0.15)

        # Total cost
        total_cost = construction_subtotal + engineering_costs + contingency_costs

        # Cost per kilometer
        cost_per_km = total_cost / total_length_km if total_length_km > 0 else 0

        # Calculate average span length
        total_span_length = 0
        span_count = 0
        for i in range(1, len(tower_positions)):
            span_dist = self._haversine_distance(
                tower_positions[i-1][1], tower_positions[i-1][0],
                tower_positions[i][1], tower_positions[i][0]
            )
            total_span_length += span_dist
            span_count += 1

        avg_span_length = total_span_length / span_count if span_count > 0 else 0

        return {
            'total_cost': total_cost,
            'cost_per_km': cost_per_km,
            'total_length_km': total_length_km,
            'num_towers': num_towers,
            'avg_span_length_m': avg_span_length,
            'breakdown': {
                'towers': {
                    'cost': tower_costs,
                    'quantity': num_towers,
                    'unit_cost': tower_cost_per_unit,
                    'description': 'Steel lattice towers (400kV)'
                },
                'foundations': {
                    'cost': foundation_costs,
                    'quantity': num_towers,
                    'unit_cost': foundation_cost_per_unit,
                    'description': 'Tower foundations'
                },
                'conductors': {
                    'cost': conductor_costs,
                    'length_km': total_length_km,
                    'cost_per_km': costs.get('conductor_cost_per_km', 85000),
                    'description': 'ACSR conductors and hardware'
                },
                'installation': {
                    'cost': installation_costs,
                    'length_km': total_length_km,
                    'cost_per_km': costs.get('installation_per_km', 120000),
                    'description': 'Labor, equipment, and installation'
                },
                'row_acquisition': {
                    'cost': row_costs,
                    'length_km': total_length_km,
                    'cost_per_km': costs.get('row_acquisition_per_km', 50000),
                    'description': 'Right-of-Way and land acquisition'
                },
                'engineering': {
                    'cost': engineering_costs,
                    'percentage': costs.get('engineering_percentage', 0.08) * 100,
                    'description': 'Engineering and design services'
                },
                'contingency': {
                    'cost': contingency_costs,
                    'percentage': costs.get('contingency_percentage', 0.15) * 100,
                    'description': 'Project contingency'
                }
            }
        }
