"""
Multi-Tile DEM Loader for Uganda
Efficiently loads and merges SRTM DEM tiles for large-area route optimization
"""

import os
import numpy as np
from typing import Tuple, Optional, List, Dict
from pathlib import Path

try:
    import rasterio
    from rasterio.merge import merge
    from rasterio.warp import reproject, Resampling
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    print("Warning: rasterio not installed. DEM loading will be limited.")


class MultiTileDEMLoader:
    """
    Loads DEM data from multiple SRTM tiles for large-area coverage.
    Optimized for transmission line routing across long distances.
    """
    
    def __init__(self, dem_folder: str):
        """
        Initialize DEM loader
        
        Args:
            dem_folder: Path to folder containing DEM tiles (.tif files)
        """
        self.dem_folder = Path(dem_folder)
        self.tile_index = {}  # Maps tile coordinates to file paths
        self._build_tile_index()
    
    def _build_tile_index(self):
        """Build index of available DEM tiles"""
        if not self.dem_folder.exists():
            print(f"DEM folder not found: {self.dem_folder}")
            return
        
        for file_path in self.dem_folder.glob("*.tif"):
            # Parse filename like "n03_e032_1arc_v3.tif"
            filename = file_path.stem.lower()
            
            # Extract lat/lon from filename
            try:
                parts = filename.split('_')
                lat_part = parts[0]  # "n03" or "s01"
                lon_part = parts[1]  # "e032" or "w030"
                
                lat = int(lat_part[1:])
                if lat_part[0] == 's':
                    lat = -lat
                
                lon = int(lon_part[1:])
                if lon_part[0] == 'w':
                    lon = -lon
                
                # Store tile info (key is (lat, lon) of tile corner)
                self.tile_index[(lat, lon)] = str(file_path)
            except (IndexError, ValueError) as e:
                print(f"Could not parse tile filename: {filename}")
                continue
        
        print(f"Indexed {len(self.tile_index)} DEM tiles")
    
    def get_tiles_for_bounds(self, bounds: Tuple[float, float, float, float]) -> List[str]:
        """
        Get list of tile files needed to cover given bounds
        
        Args:
            bounds: (min_lon, min_lat, max_lon, max_lat) in WGS84
        
        Returns:
            List of tile file paths
        """
        min_lon, min_lat, max_lon, max_lat = bounds
        
        # Calculate which tiles are needed
        tiles_needed = []
        
        # Iterate through integer degrees covering the bounds
        for lat in range(int(np.floor(min_lat)), int(np.ceil(max_lat)) + 1):
            for lon in range(int(np.floor(min_lon)), int(np.ceil(max_lon)) + 1):
                if (lat, lon) in self.tile_index:
                    tiles_needed.append(self.tile_index[(lat, lon)])
        
        return tiles_needed
    
    def load_dem_for_bounds(
        self, 
        bounds: Tuple[float, float, float, float],
        target_shape: Optional[Tuple[int, int]] = None,
        resolution_m: float = 30.0
    ) -> Optional[np.ndarray]:
        """
        Load DEM data for given bounds, merging multiple tiles if necessary
        
        Args:
            bounds: (min_lon, min_lat, max_lon, max_lat) in WGS84
            target_shape: Optional (height, width) to resample to
            resolution_m: Target resolution in meters
        
        Returns:
            DEM array or None if no data available
        """
        if not HAS_RASTERIO:
            print("rasterio not available, cannot load DEM")
            return None
        
        # Get required tiles
        tile_files = self.get_tiles_for_bounds(bounds)
        
        if not tile_files:
            print(f"No DEM tiles found for bounds: {bounds}")
            return None
        
        print(f"Loading {len(tile_files)} DEM tiles for bounds {bounds}")
        
        try:
            # Open all tile files
            src_files = [rasterio.open(f) for f in tile_files]
            
            # Merge tiles
            merged_array, merged_transform = merge(src_files, bounds=bounds)
            
            # Close source files
            for src in src_files:
                src.close()
            
            # Extract first band (elevation)
            dem = merged_array[0].astype(np.float32)
            
            # Handle nodata values (SRTM uses -32767 or -32768 for nodata)
            nodata_vals = [-32767, -32768, -9999]
            for val in nodata_vals:
                dem[dem == val] = np.nan
            
            # Fill NaN values with interpolation
            if np.any(np.isnan(dem)):
                dem = self._fill_nodata(dem)
            
            # Resample to target shape if specified
            if target_shape is not None and dem.shape != target_shape:
                dem = self._resample_dem(dem, target_shape, bounds)
            
            print(f"Loaded DEM shape: {dem.shape}, range: {np.min(dem):.0f}m to {np.max(dem):.0f}m")
            return dem
            
        except Exception as e:
            print(f"Error loading DEM: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _fill_nodata(self, dem: np.ndarray) -> np.ndarray:
        """Fill nodata values using nearest neighbor interpolation"""
        from scipy.ndimage import distance_transform_edt
        
        # Create mask of valid data
        mask = ~np.isnan(dem)
        
        if not np.any(mask):
            # All nodata - return zeros
            return np.zeros_like(dem)
        
        # Distance transform to find nearest valid pixel
        dist, indices = distance_transform_edt(~mask, return_indices=True)
        
        # Fill with nearest valid value
        filled = dem.copy()
        filled[~mask] = dem[indices[0][~mask], indices[1][~mask]]
        
        return filled
    
    def _resample_dem(
        self, 
        dem: np.ndarray, 
        target_shape: Tuple[int, int],
        bounds: Tuple[float, float, float, float]
    ) -> np.ndarray:
        """Resample DEM to target shape using bilinear interpolation"""
        from scipy.ndimage import zoom
        
        # Calculate zoom factors
        zoom_y = target_shape[0] / dem.shape[0]
        zoom_x = target_shape[1] / dem.shape[1]
        
        # Resample
        resampled = zoom(dem, (zoom_y, zoom_x), order=1)
        
        return resampled.astype(np.float32)
    
    def get_elevation_at_point(self, lon: float, lat: float) -> Optional[float]:
        """
        Get elevation at a specific point (for tower positions)
        
        Args:
            lon: Longitude
            lat: Latitude
        
        Returns:
            Elevation in meters or None
        """
        if not HAS_RASTERIO:
            return None
        
        # Find which tile contains this point
        tile_lat = int(np.floor(lat))
        tile_lon = int(np.floor(lon))
        
        if (tile_lat, tile_lon) not in self.tile_index:
            return None
        
        tile_file = self.tile_index[(tile_lat, tile_lon)]
        
        try:
            with rasterio.open(tile_file) as src:
                # Sample at point
                for val in src.sample([(lon, lat)]):
                    elevation = float(val[0])
                    if elevation == src.nodata:
                        return None
                    return elevation
        except Exception as e:
            print(f"Error sampling elevation: {e}")
            return None
        
        return None


def load_dem_for_route(
    config,
    bounds: Tuple[float, float, float, float],
    target_shape: Optional[Tuple[int, int]] = None,
    resolution_m: float = 30.0
) -> Optional[np.ndarray]:
    """
    Convenience function to load DEM for route optimization
    
    Args:
        config: Flask app config
        bounds: (min_lon, min_lat, max_lon, max_lat)
        target_shape: Optional (height, width) to resample to
        resolution_m: Target resolution
    
    Returns:
        DEM array or None
    """
    dem_folder = getattr(config, 'DEM_FOLDER', 'data/dem')
    loader = MultiTileDEMLoader(dem_folder)
    return loader.load_dem_for_bounds(bounds, target_shape, resolution_m)
