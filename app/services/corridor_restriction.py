"""
Corridor Restriction Service
Manages 60m corridor width validation (10m RoW + 25m Wayleave each side)
"""
import numpy as np
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import unary_union
from typing import List, Tuple, Dict


class CorridorRestrictionService:
    """
    Service for managing transmission line corridor restrictions
    Specific to Uganda UETCL requirements: 60m total width
    """
    
    def __init__(self, config):
        """
        Initialize corridor service

        Args:
            config: Flask app configuration
        """
        self.config = config
        self.row_width = config.get('RIGHT_OF_WAY', 10)  # 10m
        self.wayleave_width = config.get('WAYLEAVE_EACH_SIDE', 25)  # 25m each side
        self.total_width = config.get('TOTAL_CORRIDOR_WIDTH', 60)  # 60m
        self.half_width = self.total_width / 2  # 30m from centerline
    
    def create_corridor_polygon(self, route_coords: List[Tuple[float, float]]) -> Polygon:
        """
        Create a corridor polygon around the route
        
        Args:
            route_coords: List of (lon, lat) coordinates
        
        Returns:
            Shapely Polygon representing the corridor
        """
        if len(route_coords) < 2:
            return None
        
        # Create LineString from route
        line = LineString(route_coords)
        
        # Buffer the line by half the corridor width
        # Note: This creates a buffer in degrees, which is approximate
        # For production, convert to projected CRS (e.g., UTM)
        buffer_degrees = self._meters_to_degrees(self.half_width, route_coords[0][1])
        corridor = line.buffer(buffer_degrees)
        
        return corridor
    
    def check_corridor_conflicts(self, corridor: Polygon, 
                                 restricted_areas: List[Polygon]) -> Dict:
        """
        Check for conflicts between corridor and restricted areas
        
        Args:
            corridor: Corridor polygon
            restricted_areas: List of restricted area polygons
        
        Returns:
            dict containing conflict information
        """
        conflicts = []
        total_conflict_area = 0
        
        for i, restricted in enumerate(restricted_areas):
            if corridor.intersects(restricted):
                intersection = corridor.intersection(restricted)
                conflict_area = intersection.area
                
                conflicts.append({
                    'area_id': i,
                    'conflict_area': conflict_area,
                    'geometry': intersection
                })
                
                total_conflict_area += conflict_area
        
        corridor_area = corridor.area
        conflict_percentage = (total_conflict_area / corridor_area * 100) if corridor_area > 0 else 0
        
        return {
            'has_conflicts': len(conflicts) > 0,
            'num_conflicts': len(conflicts),
            'conflicts': conflicts,
            'total_conflict_area': total_conflict_area,
            'corridor_area': corridor_area,
            'conflict_percentage': conflict_percentage
        }
    
    def calculate_land_acquisition_area(self, route_coords: List[Tuple[float, float]]) -> Dict:
        """
        Calculate land acquisition requirements for the corridor
        
        Args:
            route_coords: List of (lon, lat) coordinates
        
        Returns:
            dict with land acquisition metrics
        """
        corridor = self.create_corridor_polygon(route_coords)
        
        if corridor is None:
            return {'error': 'Invalid route'}
        
        # Calculate areas
        total_area_deg2 = corridor.area
        
        # Convert to hectares (approximate)
        # 1 degree ≈ 111km at equator, area varies with latitude
        avg_lat = np.mean([coord[1] for coord in route_coords])
        total_area_m2 = self._degrees_to_meters_area(total_area_deg2, avg_lat)
        total_area_hectares = total_area_m2 / 10000
        
        # Calculate route length
        line = LineString(route_coords)
        length_deg = line.length
        length_m = self._degrees_to_meters_length(length_deg, avg_lat)
        
        return {
            'corridor_area_m2': total_area_m2,
            'corridor_area_hectares': total_area_hectares,
            'corridor_area_acres': total_area_hectares * 2.471,  # Convert to acres
            'route_length_m': length_m,
            'route_length_km': length_m / 1000,
            'corridor_width_m': self.total_width,
            'row_width_m': self.row_width,
            'wayleave_width_m': self.wayleave_width * 2
        }
    
    def _meters_to_degrees(self, meters: float, latitude: float) -> float:
        """
        Convert meters to degrees at given latitude
        
        Args:
            meters: Distance in meters
            latitude: Latitude in degrees
        
        Returns:
            Distance in degrees
        """
        # Approximate conversion
        meters_per_degree_lat = 111320
        meters_per_degree_lon = 111320 * np.cos(np.radians(latitude))
        
        # Use average for buffer
        avg_meters_per_degree = (meters_per_degree_lat + meters_per_degree_lon) / 2
        
        return meters / avg_meters_per_degree
    
    def _degrees_to_meters_area(self, area_deg2: float, latitude: float) -> float:
        """Convert area from square degrees to square meters"""
        meters_per_degree_lat = 111320
        meters_per_degree_lon = 111320 * np.cos(np.radians(latitude))
        
        return area_deg2 * meters_per_degree_lat * meters_per_degree_lon
    
    def _degrees_to_meters_length(self, length_deg: float, latitude: float) -> float:
        """Convert length from degrees to meters"""
        meters_per_degree = 111320 * np.cos(np.radians(latitude))
        return length_deg * meters_per_degree
    
    def generate_corridor_geojson(self, route_coords: List[Tuple[float, float]]) -> Dict:
        """
        Generate GeoJSON representation of the corridor
        
        Args:
            route_coords: List of (lon, lat) coordinates
        
        Returns:
            GeoJSON dict
        """
        corridor = self.create_corridor_polygon(route_coords)
        
        if corridor is None:
            return None
        
        # Convert to GeoJSON
        geojson = {
            'type': 'Feature',
            'properties': {
                'corridor_width_m': self.total_width,
                'row_width_m': self.row_width,
                'wayleave_width_m': self.wayleave_width * 2
            },
            'geometry': {
                'type': 'Polygon',
                'coordinates': [list(corridor.exterior.coords)]
            }
        }
        
        return geojson

