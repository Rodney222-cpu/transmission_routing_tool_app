"""
Cost Surface Generation Module
Implements Analytic Hierarchy Process (AHP) for multi-criteria cost surface generation
Specific to Uganda terrain and land use characteristics
"""
import numpy as np
from scipy.ndimage import distance_transform_edt
import os
import json

# Optional rasterio import for GeoTIFF support
try:
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.warp import reproject, Resampling
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    print("Warning: rasterio not installed. GeoTIFF I/O will be limited.")


class CostSurfaceGenerator:
    """
    Generates composite cost surfaces for transmission line routing
    using AHP methodology and Uganda-specific constraints
    """
    
    def __init__(self, config, resolution=30):
        """
        Initialize cost surface generator

        Args:
            config: Flask app configuration object
            resolution: Resolution in meters (default: 30m SRTM standard)
        """
        self.config = config
        self.resolution = resolution

    def generate_composite_cost_surface(self, bounds, ahp_weights, layers_data, resolution=None, grid_shape=None):
        """
        Generate composite cost surface using AHP weights

        Args:
            bounds: [min_lon, min_lat, max_lon, max_lat]
            ahp_weights: Dictionary of weights for each criterion
            layers_data: Dictionary containing paths or arrays for each layer
            resolution: Optional custom resolution in meters (overrides self.resolution)
            grid_shape: Optional (height, width) to match preloaded layer rasters exactly
                (avoids duplicate dimension math and large float64 temporaries)

        Returns:
            numpy.ndarray: Composite cost surface
            dict: Metadata about the cost surface
        """
        # Use custom resolution if provided, otherwise use instance resolution
        res = resolution if resolution is not None else self.resolution
        self.resolution = res

        min_lon, min_lat, max_lon, max_lat = bounds
        if grid_shape is not None:
            height, width = int(grid_shape[0]), int(grid_shape[1])
        else:
            width = int((max_lon - min_lon) * 111320 / res)
            height = int((max_lat - min_lat) * 111320 / res)
        
        # Initialize composite cost surface
        composite_cost = np.zeros((height, width), dtype=np.float32)
        
        # Process each layer and add weighted contribution
        if 'dem' in layers_data and ahp_weights.get('topography', 0) > 0:
            topo_cost = self._process_topography(layers_data['dem'], bounds, (height, width))
            composite_cost += ahp_weights['topography'] * topo_cost
        
        if 'land_use' in layers_data and ahp_weights.get('land_use', 0) > 0:
            landuse_cost = self._process_land_use(layers_data['land_use'], bounds, (height, width))
            composite_cost += ahp_weights['land_use'] * landuse_cost
        
        if 'settlements' in layers_data and ahp_weights.get('settlements', 0) > 0:
            settlement_cost = self._process_settlements(layers_data['settlements'], bounds, (height, width))
            composite_cost += ahp_weights['settlements'] * settlement_cost
        
        if 'protected_areas' in layers_data and ahp_weights.get('protected_areas', 0) > 0:
            protected_cost = self._process_protected_areas(layers_data['protected_areas'], bounds, (height, width))
            composite_cost += ahp_weights['protected_areas'] * protected_cost
        
        if 'roads' in layers_data and ahp_weights.get('roads', 0) > 0:
            roads_cost = self._process_roads(layers_data['roads'], bounds, (height, width))
            composite_cost += ahp_weights['roads'] * roads_cost

        # Additional layers
        if 'education' in layers_data and ahp_weights.get('public_infrastructure', 0) > 0:
            education_cost = self._process_education(layers_data['education'], bounds, (height, width))
            composite_cost += ahp_weights['public_infrastructure'] * 0.3 * education_cost

        if 'power_infrastructure' in layers_data:
            power_cost = self._process_power_infrastructure(layers_data['power_infrastructure'], bounds, (height, width))
            # Power infrastructure reduces cost (synergy with existing lines)
            composite_cost -= 0.05 * power_cost

        if 'waterbodies' in layers_data and ahp_weights.get('water', 0) > 0:
            water_cost = self._process_waterbodies(layers_data['waterbodies'], bounds, (height, width))
            composite_cost += ahp_weights['water'] * water_cost

        if 'forests' in layers_data and ahp_weights.get('vegetation', 0) > 0:
            forest_cost = self._process_forests(layers_data['forests'], bounds, (height, width))
            composite_cost += ahp_weights['vegetation'] * forest_cost

        if 'airports' in layers_data and ahp_weights.get('public_infrastructure', 0) > 0:
            airport_cost = self._process_airports(layers_data['airports'], bounds, (height, width))
            composite_cost += ahp_weights['public_infrastructure'] * 0.7 * airport_cost

        # Normalize to 0-100 range
        composite_cost = self._normalize_cost_surface(composite_cost)
        
        metadata = {
            'bounds': bounds,
            'resolution': res,
            'shape': composite_cost.shape,
            'weights': ahp_weights,
            'min_cost': float(np.min(composite_cost)),
            'max_cost': float(np.max(composite_cost)),
            'mean_cost': float(np.mean(composite_cost))
        }
        
        return composite_cost, metadata
    
    def _process_topography(self, dem_data, bounds, shape):
        """
        Process DEM to generate slope-based cost surface
        
        Args:
            dem_data: Path to DEM file or numpy array
            bounds: Geographic bounds
            shape: Target shape (height, width)
        
        Returns:
            numpy.ndarray: Topography cost surface
        """
        # Load or use DEM data
        if isinstance(dem_data, str):
            with rasterio.open(dem_data) as src:
                dem = src.read(1)
        else:
            dem = dem_data
        
        # Resize to target shape if needed
        if dem.shape != shape:
            dem = self._resize_array(dem, shape)

        dem = np.asarray(dem, dtype=np.float32)
        # Calculate slope in degrees (keep float32 to avoid large float64 allocations)
        dy, dx = np.gradient(dem)
        slope = np.degrees(np.arctan(np.sqrt(dx.astype(np.float32) ** 2 + dy.astype(np.float32) ** 2))).astype(np.float32)

        # Apply slope-based costs (Uganda-specific)
        cost = np.ones_like(slope, dtype=np.float32)
        slope_costs = self.config.get('SLOPE_COSTS', {
            'flat': 1.0, 'gentle': 1.5, 'moderate': 2.5, 'steep': 5.0, 'very_steep': 100.0
        })
        cost[slope <= 5] = slope_costs['flat']
        cost[(slope > 5) & (slope <= 15)] = slope_costs['gentle']
        cost[(slope > 15) & (slope <= 25)] = slope_costs['moderate']
        cost[(slope > 25) & (slope <= 30)] = slope_costs['steep']
        cost[slope > 30] = slope_costs['very_steep']
        
        return cost
    
    def _process_land_use(self, landuse_data, bounds, shape):
        """
        Process land use data to generate cost surface
        Uganda-specific land use types: agricultural, built-up, wetlands, forest
        
        Args:
            landuse_data: Path to land use file or numpy array
            bounds: Geographic bounds
            shape: Target shape
        
        Returns:
            numpy.ndarray: Land use cost surface
        """
        # Load land use data
        if isinstance(landuse_data, str):
            with rasterio.open(landuse_data) as src:
                landuse = src.read(1)
        else:
            landuse = landuse_data
        
        # Resize if needed
        if landuse.shape != shape:
            landuse = self._resize_array(landuse, shape)
        
        # Map land use classes to costs (ESA WorldCover classes)
        # 10: Tree cover, 20: Shrubland, 30: Grassland, 40: Cropland
        # 50: Built-up, 60: Bare, 70: Snow/Ice, 80: Water, 90: Wetlands, 95: Mangroves
        cost = np.ones_like(landuse, dtype=np.float32)
        land_use_costs = self.config.get('LAND_USE_COSTS', {
            'forest': 3.0, 'grassland': 1.0, 'agricultural': 1.5,
            'built_up': 10.0, 'water': 100.0, 'wetlands': 5.0, 'protected_area': 8.0
        })
        cost[landuse == 10] = land_use_costs['forest']
        cost[landuse == 30] = land_use_costs['grassland']
        cost[landuse == 40] = land_use_costs['agricultural']
        cost[landuse == 50] = land_use_costs['built_up']
        cost[landuse == 80] = land_use_costs['water']
        cost[landuse == 90] = land_use_costs['wetlands']

        return cost

    def _process_settlements(self, settlement_data, bounds, shape):
        """
        Process settlement data to generate proximity-based cost surface

        Args:
            settlement_data: Path to settlement file or binary array
            bounds: Geographic bounds
            shape: Target shape

        Returns:
            numpy.ndarray: Settlement proximity cost surface
        """
        # Load settlement data (binary: 1 = settlement, 0 = no settlement)
        if isinstance(settlement_data, str):
            with rasterio.open(settlement_data) as src:
                settlements = src.read(1)
        else:
            settlements = settlement_data

        # Resize if needed
        if settlements.shape != shape:
            settlements = self._resize_array(settlements, shape)

        # Calculate distance transform (distance to nearest settlement in pixels)
        distance_pixels = distance_transform_edt(settlements == 0).astype(np.float32)
        distance_meters = distance_pixels * float(self.resolution)

        # Apply distance-based costs
        cost = np.ones_like(distance_meters, dtype=np.float32)
        cost[distance_meters < 100] = 10.0
        cost[(distance_meters >= 100) & (distance_meters < 500)] = 5.0
        cost[(distance_meters >= 500) & (distance_meters < 1000)] = 2.0
        cost[distance_meters >= 1000] = 1.0
        cost[settlements > 0] = 100.0  # Very high cost within settlements

        return cost

    def _process_protected_areas(self, protected_data, bounds, shape):
        """
        Process protected areas (NEMA/NFA/UWA data)

        Args:
            protected_data: Path to protected areas file or binary array
            bounds: Geographic bounds
            shape: Target shape

        Returns:
            numpy.ndarray: Protected areas cost surface
        """
        # Load protected areas data
        if isinstance(protected_data, str):
            with rasterio.open(protected_data) as src:
                protected = src.read(1)
        else:
            protected = protected_data

        # Resize if needed
        if protected.shape != shape:
            protected = self._resize_array(protected, shape)

        # High cost for protected areas
        cost = np.ones_like(protected, dtype=np.float32)
        land_use_costs = self.config.get('LAND_USE_COSTS', {'protected_area': 8.0})
        cost[protected > 0] = land_use_costs['protected_area']

        return cost

    def _process_roads(self, roads_data, bounds, shape):
        """
        Process roads data - proximity to roads can reduce costs (easier access)

        Args:
            roads_data: Path to roads file or binary array
            bounds: Geographic bounds
            shape: Target shape

        Returns:
            numpy.ndarray: Roads proximity cost surface
        """
        # Load roads data
        if isinstance(roads_data, str):
            with rasterio.open(roads_data) as src:
                roads = src.read(1)
        else:
            roads = roads_data

        # Resize if needed
        if roads.shape != shape:
            roads = self._resize_array(roads, shape)

        # Calculate distance to roads
        distance_pixels = distance_transform_edt(roads == 0).astype(np.float32)
        distance_meters = distance_pixels * float(self.resolution)

        # Lower cost near roads (easier construction access)
        cost = np.ones_like(distance_meters, dtype=np.float32)
        cost[distance_meters < 500] = 0.8  # Benefit from road proximity
        cost[(distance_meters >= 500) & (distance_meters < 2000)] = 0.9
        cost[distance_meters >= 2000] = 1.0

        return cost

    def _resize_array(self, array, target_shape):
        """
        Resize array to target shape using bilinear interpolation

        Args:
            array: Input array
            target_shape: (height, width)

        Returns:
            numpy.ndarray: Resized array
        """
        from scipy.ndimage import zoom

        zoom_factors = (target_shape[0] / array.shape[0],
                       target_shape[1] / array.shape[1])
        out = zoom(np.asarray(array, dtype=np.float32), zoom_factors, order=1)
        return np.asarray(out, dtype=np.float32)

    def _normalize_cost_surface(self, cost_surface):
        """
        Normalize cost surface to 0-100 range

        Args:
            cost_surface: Input cost surface

        Returns:
            numpy.ndarray: Normalized cost surface
        """
        min_val = np.min(cost_surface)
        max_val = np.max(cost_surface)

        if max_val > min_val:
            normalized = ((cost_surface - min_val) / (max_val - min_val)) * 100.0
        else:
            normalized = np.zeros_like(cost_surface, dtype=np.float32)

        return normalized.astype(np.float32, copy=False)

    def save_cost_surface(self, cost_surface, output_path, bounds, crs='EPSG:4326'):
        """
        Save cost surface as GeoTIFF

        Args:
            cost_surface: Cost surface array
            output_path: Path to save the GeoTIFF
            bounds: [min_lon, min_lat, max_lon, max_lat]
            crs: Coordinate reference system
        """
        if not HAS_RASTERIO:
            # Save as NumPy array instead
            np.save(output_path.replace('.tif', '.npy'), cost_surface)
            print(f"Saved cost surface as NumPy array: {output_path.replace('.tif', '.npy')}")
            return

        height, width = cost_surface.shape
        transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], width, height)

        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=cost_surface.dtype,
            crs=crs,
            transform=transform,
            compress='lzw'
        ) as dst:
            dst.write(cost_surface, 1)

    def _process_education(self, education_data, bounds, shape):
        """
        Process education facilities (schools, colleges, universities)
        Higher costs near educational institutions

        Args:
            education_data: Education facilities data
            bounds: Geographic bounds
            shape: Output shape (height, width)

        Returns:
            numpy.ndarray: Cost surface for education facilities
        """
        height, width = shape
        cost = np.ones((height, width), dtype=np.float32) * 1.0  # Base cost

        # In production, this would process actual education facility locations
        # For now, return base cost
        # TODO: Implement buffer-based costs around education facilities

        return cost

    def _process_power_infrastructure(self, power_data, bounds, shape):
        """
        Process existing power infrastructure (substations, transmission lines)
        Lower costs near existing infrastructure (synergy)

        Args:
            power_data: Power infrastructure data
            bounds: Geographic bounds
            shape: Output shape (height, width)

        Returns:
            numpy.ndarray: Cost surface for power infrastructure (lower = better synergy)
        """
        height, width = shape
        cost = np.zeros((height, width), dtype=np.float32)  # No cost by default

        # In production, this would process actual power infrastructure
        # Proximity to existing lines/substations would reduce costs
        # TODO: Implement proximity-based cost reduction

        return cost

    def _process_waterbodies(self, water_data, bounds, shape):
        """
        Process water bodies (rivers, lakes, wetlands)
        Classify by size and apply appropriate costs

        Args:
            water_data: Water bodies data
            bounds: Geographic bounds
            shape: Output shape (height, width)

        Returns:
            numpy.ndarray: Cost surface for water bodies
        """
        height, width = shape
        cost = np.ones((height, width), dtype=np.float32) * 1.0  # Base cost

        # In production, classify water bodies by size
        # Small streams: moderate cost (crossable)
        # Large rivers/lakes: high cost (avoid)
        # TODO: Implement size-based water crossing costs

        return cost

    def _process_forests(self, forest_data, bounds, shape):
        """
        Process forest/vegetation data
        Higher costs in dense forests

        Args:
            forest_data: Forest/vegetation data
            bounds: Geographic bounds
            shape: Output shape (height, width)

        Returns:
            numpy.ndarray: Cost surface for forests
        """
        height, width = shape
        cost = np.ones((height, width), dtype=np.float32) * 1.0  # Base cost

        # In production, process forest density and type
        # Dense forest: high cost
        # Light vegetation: moderate cost
        # TODO: Implement forest density-based costs

        return cost

    def _process_airports(self, airport_data, bounds, shape):
        """
        Process airports and airstrips
        Very high costs near airports (flight path safety)

        Args:
            airport_data: Airport locations data
            bounds: Geographic bounds
            shape: Output shape (height, width)

        Returns:
            numpy.ndarray: Cost surface for airports
        """
        height, width = shape
        cost = np.ones((height, width), dtype=np.float32) * 1.0  # Base cost

        # In production, apply buffer zones around airports
        # 0-500m: extremely high cost
        # 500-2000m: high cost
        # >2000m: moderate cost
        # TODO: Implement airport buffer-based costs

        return cost

    def load_cost_surface(self, file_path):
        """
        Load cost surface from GeoTIFF

        Args:
            file_path: Path to cost surface file

        Returns:
            tuple: (cost_surface array, metadata dict)
        """
        if not HAS_RASTERIO:
            # Load from NumPy array
            npy_path = file_path.replace('.tif', '.npy')
            cost_surface = np.load(npy_path)
            metadata = {
                'bounds': None,
                'crs': 'EPSG:4326',
                'transform': None,
                'shape': cost_surface.shape
            }
            return cost_surface, metadata

        with rasterio.open(file_path) as src:
            cost_surface = src.read(1)
            metadata = {
                'bounds': src.bounds,
                'crs': str(src.crs),
                'transform': src.transform,
                'shape': cost_surface.shape
            }

        return cost_surface, metadata

