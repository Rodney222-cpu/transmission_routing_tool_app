"""
Uganda GIS Data Loader for Map Visualization

Loads real GIS data from Uganda sources and converts to GeoJSON for Leaflet display.
Falls back to OpenStreetMap Overpass API if local files not available.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: 'requests' module not installed. Real-time GIS data loading from OSM will not work.")
    print("Install with: python -m pip install requests")


class UgandaGISLoader:
    """Load Uganda GIS data for map visualization"""
    
    def __init__(self, config):
        self.config = config
        self.cache_dir = os.path.join(config.DATA_FOLDER, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def load_layer_geojson(self, layer_name: str, bounds: Tuple[float, float, float, float]) -> Optional[Dict]:
        """
        Load GIS layer as GeoJSON for map display
        
        Args:
            layer_name: One of 'settlements', 'roads', 'protected_areas', 'water', 'forests', 'power', 'education', 'airports'
            bounds: (min_lon, min_lat, max_lon, max_lat) in WGS84
        
        Returns:
            GeoJSON dict or None
        """
        # Try to load from local files first
        local_geojson = self._load_local_geojson(layer_name)
        if local_geojson:
            return self._filter_by_bounds(local_geojson, bounds)
        
        # Fall back to OpenStreetMap Overpass API
        return self._fetch_from_overpass(layer_name, bounds)
    
    def _load_local_geojson(self, layer_name: str) -> Optional[Dict]:
        """Load GeoJSON from local data folder"""
        folder_map = {
            'settlements': self.config.SETTLEMENTS_FOLDER,
            'roads': self.config.ROADS_FOLDER,
            'protected_areas': self.config.PROTECTED_AREAS_FOLDER,
            'water': self.config.WATERBODIES_FOLDER,
            'forests': self.config.FORESTS_FOLDER,
            'power': self.config.POWER_INFRASTRUCTURE_FOLDER,
            'education': self.config.EDUCATION_FOLDER,
            'airports': self.config.AIRPORTS_FOLDER,
        }
        
        folder = folder_map.get(layer_name)
        if not folder or not os.path.isdir(folder):
            return None
        
        # Look for GeoJSON files
        for filename in os.listdir(folder):
            if filename.lower().endswith(('.geojson', '.json')):
                filepath = os.path.join(folder, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Error loading {filepath}: {e}")
                    continue
        
        return None
    
    def _filter_by_bounds(self, geojson: Dict, bounds: Tuple[float, float, float, float]) -> Dict:
        """Filter GeoJSON features by bounding box"""
        min_lon, min_lat, max_lon, max_lat = bounds
        
        filtered_features = []
        for feature in geojson.get('features', []):
            geom = feature.get('geometry', {})
            coords = geom.get('coordinates')
            if not coords:
                continue
            
            # Simple bbox check (can be improved)
            if self._intersects_bounds(coords, bounds):
                filtered_features.append(feature)
        
        return {
            'type': 'FeatureCollection',
            'features': filtered_features
        }
    
    def _intersects_bounds(self, coords, bounds) -> bool:
        """Check if coordinates intersect with bounds"""
        min_lon, min_lat, max_lon, max_lat = bounds
        
        def check_point(lon, lat):
            return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat
        
        # Recursively check coordinates
        if isinstance(coords, (list, tuple)):
            if len(coords) == 2 and isinstance(coords[0], (int, float)):
                # It's a point [lon, lat]
                return check_point(coords[0], coords[1])
            else:
                # It's nested
                return any(self._intersects_bounds(c, bounds) for c in coords)
        
        return False
    
    def _fetch_from_overpass(self, layer_name: str, bounds: Tuple[float, float, float, float]) -> Optional[Dict]:
        """
        Fetch data from OpenStreetMap Overpass API

        Note: This is a fallback for when local data is not available.
        For production, download data locally using QUICK_START_DOWNLOAD.md guide.
        """
        if not HAS_REQUESTS:
            print(f"Cannot fetch {layer_name} from OSM: 'requests' module not installed")
            return None

        min_lon, min_lat, max_lon, max_lat = bounds
        bbox_str = f"{min_lat},{min_lon},{max_lat},{max_lon}"
        
        # Overpass query templates for different layers
        queries = {
            'settlements': f'[out:json];(node["place"~"city|town|village"]({bbox_str}););out geom;',
            'roads': f'[out:json];way["highway"]({bbox_str});out geom;',
            'protected_areas': f'[out:json];(way["boundary"="protected_area"]({bbox_str});relation["boundary"="protected_area"]({bbox_str}););out geom;',
            'water': f'[out:json];(way["natural"="water"]({bbox_str});way["waterway"]({bbox_str}););out geom;',
            'forests': f'[out:json];way["landuse"="forest"]({bbox_str});out geom;',
            'power': f'[out:json];(way["power"="line"]({bbox_str});node["power"="tower"]({bbox_str}););out geom;',
            'education': f'[out:json];node["amenity"~"school|college|university"]({bbox_str});out geom;',
            'airports': f'[out:json];(node["aeroway"="aerodrome"]({bbox_str});way["aeroway"="aerodrome"]({bbox_str}););out geom;',
        }
        
        query = queries.get(layer_name)
        if not query:
            return None
        
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f'{layer_name}_{min_lat}_{min_lon}_{max_lat}_{max_lon}.geojson')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Fetch from Overpass API (with rate limiting)
        try:
            time.sleep(1)  # Rate limiting
            response = requests.get(
                'https://overpass-api.de/api/interpreter',
                params={'data': query},
                timeout=30
            )
            
            if response.status_code == 200:
                osm_data = response.json()
                geojson = self._convert_osm_to_geojson(osm_data, layer_name)
                
                # Cache the result
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(geojson, f)
                except:
                    pass
                
                return geojson
        except Exception as e:
            print(f"Error fetching from Overpass API: {e}")

        return None

    def _convert_osm_to_geojson(self, osm_data: Dict, layer_name: str) -> Dict:
        """Convert OSM JSON to GeoJSON"""
        features = []

        elements = osm_data.get('elements', [])
        for elem in elements:
            elem_type = elem.get('type')

            if elem_type == 'node':
                # Point geometry
                lat = elem.get('lat')
                lon = elem.get('lon')
                if lat is None or lon is None:
                    continue

                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [lon, lat]
                    },
                    'properties': elem.get('tags', {})
                }
                features.append(feature)

            elif elem_type == 'way':
                # LineString or Polygon geometry
                geom_coords = elem.get('geometry', [])
                if not geom_coords:
                    continue

                coords = [[pt['lon'], pt['lat']] for pt in geom_coords]

                # Determine if it's a polygon (closed way)
                is_polygon = (len(coords) > 2 and
                             coords[0][0] == coords[-1][0] and
                             coords[0][1] == coords[-1][1])

                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon' if is_polygon else 'LineString',
                        'coordinates': [coords] if is_polygon else coords
                    },
                    'properties': elem.get('tags', {})
                }
                features.append(feature)

        return {
            'type': 'FeatureCollection',
            'features': features
        }

