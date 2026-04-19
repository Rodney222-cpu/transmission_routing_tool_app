"""
QGIS-Style Cost Surface Analysis and Least-Cost Routing

This module implements a complete cost surface generation pipeline that mirrors QGIS functionality:
1. Raster preparation (alignment, reprojection, resampling)
2. Layer-specific reclassification (cost values 1-100)
3. Weighted overlay computation
4. Least-cost path finding (A* algorithm)
5. Export to GeoTIFF, PNG, and Shapefile
"""

import os
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize
from rasterio.mask import raster_geometry_mask
from shapely.geometry import Point, LineString, box
import geopandas as gpd
from scipy.ndimage import distance_transform_edt
from PIL import Image
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QGISStyleCostSurfaceAnalyzer:
    """
    Performs cost surface analysis and least-cost routing similar to QGIS.
    
    Pipeline:
    1. Raster preparation - align all rasters to same grid
    2. Reclassification - convert to cost values (1-100)
    3. Weighted overlay - combine layers with weights
    4. Least-cost path - A* routing on cost surface
    5. Export - GeoTIFF, PNG, Shapefile
    """
    
    def __init__(self, config, output_dir='static'):
        """
        Initialize analyzer.
        
        Args:
            config: Flask app config
            output_dir: Directory for output files
        """
        self.config = config
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Uganda bounding box
        self.uganda_bounds = [29.5, -1.5, 35.0, 4.5]  # [min_lon, min_lat, max_lon, max_lat]
        
        # Default resolution (degrees)
        self.default_resolution = 0.001  # ~100m at equator
        
        # CRS
        self.target_crs = 'EPSG:4326'  # WGS84
    
    def prepare_raster_from_vector(self, vector_path, bounds, shape, 
                                    reclassify_func=None, column=None):
        """
        Step 1: Convert vector to raster and reclassify.
        
        Args:
            vector_path: Path to vector file (GeoJSON or Shapefile)
            bounds: Bounding box [min_lon, min_lat, max_lon, max_lat]
            shape: Raster shape (height, width)
            reclassify_func: Function to reclassify values to cost (1-100)
            column: Column name to use for values
            
        Returns:
            numpy array of cost values (1-100)
        """
        try:
            # Load vector
            gdf = gpd.read_file(vector_path)
            
            if gdf.empty:
                logger.warning(f"Empty vector file: {vector_path}")
                return np.ones(shape, dtype=np.float32)
            
            # Reproject to target CRS
            if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs('EPSG:4326')
            
            # Create transform
            transform = from_bounds(
                bounds[0], bounds[1], bounds[2], bounds[3],
                shape[1], shape[0]
            )
            
            # Rasterize
            if column and column in gdf.columns:
                shapes = ((geom, value) for geom, value in zip(gdf.geometry, gdf[column]))
            else:
                shapes = ((geom, 1) for geom in gdf.geometry)
            
            rasterized = rasterize(
                shapes,
                out_shape=shape,
                transform=transform,
                fill=0,
                all_touched=True
            )
            
            # Reclassify to cost values
            if reclassify_func:
                cost_raster = reclassify_func(rasterized, gdf, bounds, transform)
            else:
                # Default: binary (0 or 1)
                cost_raster = np.where(rasterized > 0, 100, 1)
            
            logger.info(f"✓ Vector rasterized: {os.path.basename(vector_path)}, shape: {shape}")
            return cost_raster.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error preparing vector raster: {e}")
            return np.ones(shape, dtype=np.float32)
    
    def prepare_raster_from_raster(self, raster_path, bounds, shape, 
                                    reclassify_func=None):
        """
        Step 1: Load and align existing raster.
        
        Args:
            raster_path: Path to raster file (GeoTIFF)
            bounds: Target bounding box
            shape: Target shape (height, width)
            reclassify_func: Function to reclassify to cost values
            
        Returns:
            numpy array of cost values
        """
        try:
            with rasterio.open(raster_path) as src:
                # Reproject if needed
                if src.crs.to_epsg() != 4326:
                    # Create destination array
                    dest = np.zeros(shape, dtype=src.dtypes[0])
                    
                    transform = from_bounds(
                        bounds[0], bounds[1], bounds[2], bounds[3],
                        shape[1], shape[0]
                    )
                    
                    reproject(
                        source=rasterio.band(src, 1),
                        destination=dest,
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs='EPSG:4326',
                        resampling=Resampling.bilinear
                    )
                    data = dest
                else:
                    # Read and resample
                    window = src.window(*bounds)
                    data = src.read(
                        1,
                        window=window,
                        out_shape=shape,
                        resampling=Resampling.bilinear
                    )
                
                # Reclassify
                if reclassify_func:
                    cost_raster = reclassify_func(data)
                else:
                    cost_raster = data.astype(np.float32)
                
                logger.info(f"✓ Raster loaded: {os.path.basename(raster_path)}, shape: {shape}")
                return cost_raster
                
        except Exception as e:
            logger.error(f"Error loading raster: {e}")
            return np.ones(shape, dtype=np.float32)
    
    def reclassify_protected_areas(self, rasterized, gdf, bounds, transform):
        """
        Step 2: Reclassify protected areas.
        Inside = 100 (high cost), Outside = 1 (low cost)
        """
        cost_raster = np.where(rasterized > 0, 100, 1)
        return cost_raster
    
    def reclassify_water_distance(self, rasterized, gdf, bounds, transform):
        """
        Step 2: Reclassify rivers/lakes based on distance.
        Nearer = higher cost (100 at water, decreasing with distance)
        """
        # Create binary mask (1 = water, 0 = not water)
        water_mask = (rasterized > 0).astype(np.float32)
        
        # Compute distance transform (in pixels)
        distance_pixels = distance_transform_edt(1 - water_mask)
        
        # Convert to real distance (assuming ~100m per pixel)
        distance_meters = distance_pixels * 100
        
        # Reclassify: closer = higher cost
        # 0m = 100, 5000m = 1, linear interpolation
        max_distance = 5000  # meters
        cost_raster = np.clip(100 - (distance_meters / max_distance) * 99, 1, 100)
        
        return cost_raster
    
    def reclassify_wetlands(self, rasterized, gdf, bounds, transform):
        """
        Step 2: Reclassify wetlands.
        Inside = 80-100 (high cost), Outside = 1
        """
        cost_raster = np.where(rasterized > 0, 90, 1)
        return cost_raster
    
    def reclassify_land_use(self, rasterized, gdf, bounds, transform):
        """
        Step 2: Reclassify land use by class.
        Urban = 100, Farmland = 50, Grassland = 20, Forest = 60
        """
        # Initialize with low cost
        cost_raster = np.ones(rasterized.shape, dtype=np.float32) * 20
        
        # If we have classification data, use it
        if rasterized.max() > 0:
            # Example classification (customize based on your data)
            cost_raster = np.where(rasterized == 1, 100, cost_raster)  # Urban
            cost_raster = np.where(rasterized == 2, 50, cost_raster)   # Farmland
            cost_raster = np.where(rasterized == 3, 20, cost_raster)   # Grassland
            cost_raster = np.where(rasterized == 4, 60, cost_raster)   # Forest
            cost_raster = np.where(rasterized == 5, 80, cost_raster)   # Wetland
        
        return cost_raster
    
    def reclassify_elevation_slope(self, elevation_data):
        """
        Step 2: Derive slope from elevation, steeper = higher cost.
        
        Args:
            elevation_data: numpy array of elevation values (meters)
            
        Returns:
            Cost raster (1-100)
        """
        # Compute slope using gradient
        dy, dx = np.gradient(elevation_data)
        
        # Slope in degrees
        slope_degrees = np.arctan(np.sqrt(dx**2 + dy**2)) * 180 / np.pi
        
        # Reclassify slope to cost
        # 0° = 1, 45° = 100, linear interpolation
        max_slope = 45  # degrees
        cost_raster = np.clip((slope_degrees / max_slope) * 99 + 1, 1, 100)
        
        return cost_raster
    
    def normalize_weights(self, weights_dict):
        """
        Step 3: Normalize weights so they sum to 1.0.
        Uses only selected layers.
        
        Args:
            weights_dict: Dict of {layer_name: weight}
            
        Returns:
            Normalized weights dict
        """
        total = sum(weights_dict.values())
        if total == 0:
            # Equal weights
            n = len(weights_dict)
            return {k: 1.0/n for k in weights_dict.keys()}
        
        return {k: v / total for k, v in weights_dict.items()}
    
    def compute_weighted_overlay(self, cost_rasters, normalized_weights):
        """
        Step 4: Compute weighted overlay.
        
        cost_surface = Σ(weight_i × raster_i)
        
        Args:
            cost_rasters: Dict of {layer_name: cost_raster}
            normalized_weights: Dict of {layer_name: normalized_weight}
            
        Returns:
            Combined cost surface numpy array
        """
        logger.info("Computing weighted overlay...")
        
        # Initialize with zeros
        height, width = list(cost_rasters.values())[0].shape
        cost_surface = np.zeros((height, width), dtype=np.float32)
        
        # Weighted sum
        for layer_name, cost_raster in cost_rasters.items():
            weight = normalized_weights.get(layer_name, 0)
            cost_surface += weight * cost_raster
            logger.info(f"  Added {layer_name} (weight: {weight:.3f})")
        
        logger.info(f"✓ Weighted overlay computed. Min: {cost_surface.min():.2f}, Max: {cost_surface.max():.2f}")
        
        return cost_surface
    
    def find_least_cost_path_astar(self, cost_surface, start_point, end_point, bounds):
        """
        Step 5: Least-cost path using A* algorithm.
        
        Args:
            cost_surface: 2D numpy array of cost values
            start_point: (lat, lon)
            end_point: (lat, lon)
            bounds: [min_lon, min_lat, max_lon, max_lat]
            
        Returns:
            List of (row, col) coordinates forming the path
        """
        from heapq import heappop, heappush
        
        height, width = cost_surface.shape
        
        # Convert lat/lon to pixel coordinates
        def latlon_to_pixel(lat, lon):
            row = int((bounds[3] - lat) / (bounds[3] - bounds[1]) * height)
            col = int((lon - bounds[0]) / (bounds[2] - bounds[0]) * width)
            return (row, col)
        
        start = latlon_to_pixel(start_point[0], start_point[1])
        end = latlon_to_pixel(end_point[0], end_point[1])
        
        # Clamp to bounds
        start = (max(0, min(height-1, start[0])), max(0, min(width-1, start[1])))
        end = (max(0, min(height-1, end[0])), max(0, min(width-1, end[1])))
        
        logger.info(f"A* search: {start} → {end}")
        
        # A* algorithm
        def heuristic(a, b):
            """Euclidean distance"""
            return ((a[0] - b[0])**2 + (a[1] - b[1])**2) ** 0.5
        
        def get_neighbors(pos):
            """8-connected neighbors"""
            row, col = pos
            neighbors = []
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < height and 0 <= nc < width:
                        neighbors.append((nr, nc))
            return neighbors
        
        # Priority queue: (f_score, counter, position)
        counter = 0
        open_set = [(heuristic(start, end), counter, start)]
        came_from = {}
        g_score = {start: 0}
        closed_set = set()
        
        logger.info("Running A* algorithm...")
        
        while open_set:
            _, _, current = heappop(open_set)
            
            if current == end:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                logger.info(f"✓ Path found: {len(path)} nodes")
                return path
            
            closed_set.add(current)
            
            for neighbor in get_neighbors(current):
                if neighbor in closed_set:
                    continue
                
                # Movement cost (diagonal = sqrt(2))
                dr = abs(neighbor[0] - current[0])
                dc = abs(neighbor[1] - current[1])
                move_cost = 1.414 if (dr == 1 and dc == 1) else 1.0
                
                tentative_g = g_score[current] + cost_surface[neighbor[0], neighbor[1]] * move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, end)
                    counter += 1
                    heappush(open_set, (f_score, counter, neighbor))
        
        logger.warning("No path found!")
        return []
    
    def export_cost_surface_geotiff(self, cost_surface, bounds, output_path):
        """
        Step 4: Save cost surface as GeoTIFF.
        """
        height, width = cost_surface.shape
        
        transform = from_bounds(
            bounds[0], bounds[1], bounds[2], bounds[3],
            width, height
        )
        
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=np.float32,
            crs='EPSG:4326',
            transform=transform,
        ) as dst:
            dst.write(cost_surface, 1)
        
        logger.info(f"✓ Cost surface saved: {output_path}")
    
    def export_cost_surface_png(self, cost_surface, bounds, output_path):
        """
        Step 7: Export cost surface as PNG with color ramp.
        Green = low, Yellow = medium, Red = high
        """
        # Normalize to 0-255
        min_val = np.nanmin(cost_surface)
        max_val = np.nanmax(cost_surface)
        
        if max_val > min_val:
            normalized = ((cost_surface - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        else:
            normalized = np.zeros_like(cost_surface, dtype=np.uint8)
        
        # Apply color ramp
        height, width = cost_surface.shape
        rgba_image = np.zeros((height, width, 4), dtype=np.uint8)
        
        for i in range(height):
            for j in range(width):
                val = normalized[i, j]
                
                if val < 85:
                    # Green (low cost)
                    r = int(val / 85 * 34)
                    g = int(val / 85 * 139 + (85 - val) / 85 * 255)
                    b = int(val / 85 * 34)
                elif val < 170:
                    # Yellow (medium cost)
                    t = (val - 85) / 85
                    r = int(34 + t * 221)
                    g = int(139 + t * 116)
                    b = int(34 - t * 34)
                else:
                    # Red (high cost)
                    t = (val - 170) / 85
                    r = 255
                    g = int(255 - t * 255)
                    b = 0
                
                rgba_image[i, j] = [r, g, b, 200]
        
        # Save PNG
        img = Image.fromarray(rgba_image, 'RGBA')
        img.save(output_path)
        
        logger.info(f"✓ Cost surface PNG saved: {output_path}")
    
    def export_route_shapefile(self, path_pixels, bounds, output_path, shape=None):
        """
        Step 6: Convert path to LineString and save as Shapefile.
        """
        if shape is None:
            # Default shape - will be overridden by actual path dimensions
            height = 100
            width = 100
        else:
            height, width = shape
        
        def pixel_to_latlon(row, col):
            lat = bounds[3] - (row / height) * (bounds[3] - bounds[1])
            lon = bounds[0] + (col / width) * (bounds[2] - bounds[0])
            return (lon, lat)  # Shapely uses (x, y) = (lon, lat)
        
        # Convert pixels to coordinates
        coords = [pixel_to_latlon(row, col) for row, col in path_pixels]
        
        # Create LineString
        line = LineString(coords)
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame({'name': ['Least Cost Route']}, geometry=[line], crs='EPSG:4326')
        
        # Save to Shapefile
        gdf.to_file(output_path)
        
        logger.info(f"✓ Route saved: {output_path}")
    
    def run_full_pipeline(self, layers_config, start_point, end_point, bounds=None, resolution=None):
        """
        Run complete QGIS-style cost surface and routing pipeline.
        
        Args:
            layers_config: Dict with layer configs
                {
                    "protected_areas": {"enabled": True, "weight": 0.2, "path": "..."},
                    "rivers": {"enabled": True, "weight": 0.2, "path": "..."},
                    ...
                }
            start_point: (lat, lon)
            end_point: (lat, lon)
            bounds: [min_lon, min_lat, max_lon, max_lat]
            resolution: Pixel size in degrees
            
        Returns:
            Dict with output file paths and metadata
        """
        start_time = time.time()
        
        # Use Uganda bounds if not provided
        if bounds is None:
            bounds = self.uganda_bounds
        
        # Calculate shape from resolution
        if resolution is None:
            resolution = self.default_resolution
        
        width = int((bounds[2] - bounds[0]) / resolution)
        height = int((bounds[3] - bounds[1]) / resolution)
        shape = (height, width)
        
        logger.info(f"Starting QGIS-style pipeline...")
        logger.info(f"  Bounds: {bounds}")
        logger.info(f"  Shape: {shape}")
        logger.info(f"  Start: {start_point}, End: {end_point}")
        
        # Step 1 & 2: Prepare and reclassify rasters
        cost_rasters = {}
        
        layer_reclass_funcs = {
            'protected_areas': self.reclassify_protected_areas,
            'rivers': self.reclassify_water_distance,
            'wetlands': self.reclassify_wetlands,
            'lakes': self.reclassify_water_distance,
            'land_use': self.reclassify_land_use,
            'elevation': lambda data, *args: self.reclassify_elevation_slope(data),
        }
        
        for layer_name, config in layers_config.items():
            if not config.get('enabled', False):
                continue
            
            path = config.get('path')
            if not path or not os.path.exists(path):
                logger.warning(f"Layer {layer_name}: File not found: {path}")
                continue
            
            reclass_func = layer_reclass_funcs.get(layer_name)
            
            # Determine if vector or raster
            if path.endswith(('.tif', '.tiff')):
                # Raster
                cost_raster = self.prepare_raster_from_raster(
                    path, bounds, shape, reclass_func
                )
            else:
                # Vector
                cost_raster = self.prepare_raster_from_vector(
                    path, bounds, shape, reclass_func
                )
            
            cost_rasters[layer_name] = cost_raster
        
        if not cost_rasters:
            raise ValueError("No valid layers enabled")
        
        # Step 3: Normalize weights
        selected_weights = {
            name: config['weight']
            for name, config in layers_config.items()
            if config.get('enabled', False) and name in cost_rasters
        }
        
        normalized_weights = self.normalize_weights(selected_weights)
        logger.info(f"Normalized weights: {normalized_weights}")
        
        # Step 4: Weighted overlay
        cost_surface = self.compute_weighted_overlay(cost_rasters, normalized_weights)
        
        # Save cost surface GeoTIFF
        cost_surface_path = os.path.join(self.output_dir, 'cost_surface.tif')
        self.export_cost_surface_geotiff(cost_surface, bounds, cost_surface_path)
        
        # Save cost surface PNG
        cost_surface_png_path = os.path.join(self.output_dir, 'cost_surface.png')
        self.export_cost_surface_png(cost_surface, bounds, cost_surface_png_path)
        
        # Step 5: Least-cost path
        path_pixels = self.find_least_cost_path_astar(
            cost_surface, start_point, end_point, bounds
        )
        
        # Step 6: Export route
        route_path = os.path.join(self.output_dir, 'route.shp')
        if path_pixels:
            self.export_route_shapefile(path_pixels, bounds, route_path, shape=shape)
        
        elapsed = time.time() - start_time
        
        return {
            'cost_surface_tif': cost_surface_path,
            'cost_surface_png': cost_surface_png_path,
            'route_shp': route_path if path_pixels else None,
            'bounds': bounds,
            'metadata': {
                'resolution': resolution,
                'shape': shape,
                'weights': normalized_weights,
                'min_cost': float(cost_surface.min()),
                'max_cost': float(cost_surface.max()),
                'mean_cost': float(cost_surface.mean()),
                'path_length_nodes': len(path_pixels),
                'processing_time_s': round(elapsed, 2)
            }
        }
