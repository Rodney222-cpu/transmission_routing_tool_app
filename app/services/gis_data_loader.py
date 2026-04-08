"""
GIS Data Loader

Loads real GIS data (rasters and vectors) for route optimization and map display.

Design goals:
- Works on Windows even when GDAL stack is not installed by making rasterio/geopandas optional.
- Uses real rasters (DEM, landcover) when GeoTIFFs are present and rasterio is available.
- Uses real vectors (roads, settlements, protected areas, etc.) when GeoJSON is present.
- Falls back to demo/synthetic layers when real data isn't available.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any, List

import numpy as np

# Import multi-tile DEM loader
try:
    from app.services.dem_loader import MultiTileDEMLoader
    HAS_DEM_LOADER = True
except ImportError:
    HAS_DEM_LOADER = False

try:
    import rasterio
    from rasterio.warp import reproject, Resampling
    from rasterio.windows import from_bounds as window_from_bounds
    HAS_RASTERIO = True
except Exception:
    HAS_RASTERIO = False


@dataclass
class RasterLayer:
    array: np.ndarray
    crs: str
    bounds_wgs84: Tuple[float, float, float, float]


def _first_existing_file(folder: str, exts: Tuple[str, ...]) -> Optional[str]:
    if not folder or not os.path.isdir(folder):
        return None
    for name in os.listdir(folder):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and any(name.lower().endswith(ext) for ext in exts):
            return p
    return None


def _read_raster_to_bounds(
    path: str,
    bounds_wgs84: Tuple[float, float, float, float],
    out_shape: Tuple[int, int],
    out_crs: str = "EPSG:4326",
) -> Optional[RasterLayer]:
    """
    Read a GeoTIFF raster, crop to WGS84 bounds, and resample into out_shape in out_crs.
    """
    if not HAS_RASTERIO:
        return None

    min_lon, min_lat, max_lon, max_lat = bounds_wgs84
    height, width = out_shape

    with rasterio.open(path) as src:
        src_crs = src.crs
        if src_crs is None:
            # Assume already in WGS84 if CRS missing
            src_crs = rasterio.crs.CRS.from_string("EPSG:4326")

        # If source already in WGS84, we can window-read directly; otherwise read full and reproject.
        if str(src_crs) == out_crs:
            win = window_from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
            data = src.read(1, window=win, boundless=True, fill_value=0)
            # resample to out_shape
            out = np.zeros((height, width), dtype=np.float32)
            reproject(
                source=data,
                destination=out,
                src_transform=src.window_transform(win),
                src_crs=src_crs,
                dst_transform=rasterio.transform.from_bounds(min_lon, min_lat, max_lon, max_lat, width, height),
                dst_crs=out_crs,
                resampling=Resampling.bilinear,
            )
            return RasterLayer(array=out, crs=out_crs, bounds_wgs84=bounds_wgs84)

        # Reproject: read the entire raster (can be heavy, but simplest reliable approach)
        data = src.read(1)
        out = np.zeros((height, width), dtype=np.float32)
        reproject(
            source=data,
            destination=out,
            src_transform=src.transform,
            src_crs=src_crs,
            dst_transform=rasterio.transform.from_bounds(min_lon, min_lat, max_lon, max_lat, width, height),
            dst_crs=out_crs,
            resampling=Resampling.bilinear,
        )
        return RasterLayer(array=out, crs=out_crs, bounds_wgs84=bounds_wgs84)


def _load_geojson(path: str) -> Optional[dict]:
    import json

    if not path or not os.path.isfile(path):
        return None
    if not path.lower().endswith(".geojson") and not path.lower().endswith(".json"):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_layers_for_bounds(
    config: Any,
    bounds_wgs84: Tuple[float, float, float, float],
    out_shape: Tuple[int, int],
) -> Dict[str, Any]:
    """
    Load layers for optimization:
    Returns a dict with keys that CostSurfaceGenerator expects:
      dem, land_use, settlements, protected_areas, roads
    Each is a numpy array (rasterized for vectors where supported), otherwise absent.

    Current implementation:
    - DEM: GeoTIFF in data/dem/*.tif (requires rasterio)
    - Landcover: GeoTIFF in data/landcover/*.tif or data/land_use/*.tif (requires rasterio)
    - Vectors (settlements/roads/protected): if GeoJSON exists in their folders, we rasterize a simple presence grid.
      (This avoids requiring geopandas/fiona on Windows.)
    """
    layers: Dict[str, Any] = {}

    # Try multi-tile DEM loader first (for large areas with multiple tiles)
    dem_folder = getattr(config, "DEM_FOLDER", "")
    if HAS_DEM_LOADER and dem_folder and os.path.isdir(dem_folder):
        try:
            dem_loader = MultiTileDEMLoader(dem_folder)
            dem_array = dem_loader.load_dem_for_bounds(bounds_wgs84, out_shape)
            if dem_array is not None:
                layers["dem"] = dem_array
                print(f"✓ Loaded DEM using multi-tile loader: {dem_array.shape}")
        except Exception as e:
            print(f"Multi-tile DEM loader failed: {e}, falling back to single file")
    
    # Fallback to single file DEM loading
    if "dem" not in layers:
        dem_path = _first_existing_file(dem_folder, (".tif", ".tiff"))
        if dem_path:
            dem = _read_raster_to_bounds(dem_path, bounds_wgs84, out_shape)
            if dem is not None:
                layers["dem"] = dem.array

    land_path = _first_existing_file(getattr(config, "LANDCOVER_FOLDER", ""), (".tif", ".tiff"))
    if land_path and land_path.lower().endswith((".tif", ".tiff")):
        lc = _read_raster_to_bounds(land_path, bounds_wgs84, out_shape)
        if lc is not None:
            layers["land_use"] = lc.array.astype(np.int32)

    # Vector -> simple raster presence grid based on bbox hit test for points.
    # For polygon/line data, this is a lightweight approximation; proper rasterization can be added later.
    for key, folder_attr in (
        ("settlements", "SETTLEMENTS_FOLDER"),
        ("protected_areas", "PROTECTED_AREAS_FOLDER"),
        ("roads", "ROADS_FOLDER"),
    ):
        folder = getattr(config, folder_attr, "")
        gj = _first_existing_file(folder, (".geojson", ".json"))
        if not gj:
            continue
        geojson = _load_geojson(gj)
        if not geojson:
            continue
        presence = rasterize_geojson_presence(geojson, bounds_wgs84, out_shape)
        layers[key] = presence

    return layers


def rasterize_geojson_presence(geojson: dict, bounds_wgs84: Tuple[float, float, float, float], out_shape: Tuple[int, int]) -> np.ndarray:
    """
    Very lightweight rasterization: marks cells as 1 if a GeoJSON Point falls into the cell.
    For non-point geometries, uses their coordinate vertices as samples.
    """
    min_lon, min_lat, max_lon, max_lat = bounds_wgs84
    h, w = out_shape
    grid = np.zeros((h, w), dtype=np.uint8)

    def mark(lon: float, lat: float):
        if lon < min_lon or lon > max_lon or lat < min_lat or lat > max_lat:
            return
        c = int((lon - min_lon) / (max_lon - min_lon) * w)
        r = int((max_lat - lat) / (max_lat - min_lat) * h)
        c = max(0, min(w - 1, c))
        r = max(0, min(h - 1, r))
        grid[r, c] = 1

    feats = geojson.get("features", [])
    for f in feats:
        geom = (f or {}).get("geometry") or {}
        t = geom.get("type")
        coords = geom.get("coordinates")
        if not coords:
            continue
        if t == "Point":
            lon, lat = coords[0], coords[1]
            mark(float(lon), float(lat))
        elif t in ("LineString", "MultiPoint"):
            for pt in coords:
                lon, lat = pt[0], pt[1]
                mark(float(lon), float(lat))
        elif t == "MultiLineString":
            for line in coords:
                for pt in line:
                    lon, lat = pt[0], pt[1]
                    mark(float(lon), float(lat))
        elif t == "Polygon":
            for ring in coords:
                for pt in ring:
                    lon, lat = pt[0], pt[1]
                    mark(float(lon), float(lat))
        elif t == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    for pt in ring:
                        lon, lat = pt[0], pt[1]
                        mark(float(lon), float(lat))

    return grid

