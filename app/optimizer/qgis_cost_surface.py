"""
QGIS-Style Cost Surface Analysis and Least-Cost Routing
========================================================
Complete pipeline:
  1. Base raster grid  – consistent CRS/resolution/extent (Uganda EPSG:4326)
  2. Rasterization     – all vectors → rasters aligned to base grid
  3. Friction mapping  – layer-specific cost logic (barriers=high, roads=low, slope, etc.)
  4. Normalisation     – every layer scaled to 1–10
  5. Weighted overlay  – cost_surface = Σ(weight_i × layer_i), weights sum to 1.0
  6. Classification    – quantile (preferred) or equal-interval, 5 classes
  7. Rendering         – QGIS green→lime→yellow→orange→red colour ramp + speckle
  8. Least-cost path   – Dijkstra on pixel graph, diagonal movement × 1.414
  9. Debug stats       – per-layer min/max, weight contributions, surface stats
"""

import os
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize
from shapely.geometry import LineString
import geopandas as gpd
from scipy.ndimage import distance_transform_edt
from PIL import Image
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# QGIS colour ramp  (green → lime → yellow → orange → red)
# ---------------------------------------------------------------------------
_QGIS_5_COLORS = [
    (34,  139,  34),   # class 1 – dark green
    (124, 205,  50),   # class 2 – lime green
    (255, 230,   0),   # class 3 – yellow
    (255, 140,   0),   # class 4 – orange
    (220,  20,  20),   # class 5 – red
]

# Land-use cost dictionary (value in shapefile → raw cost 1-100)
_LAND_USE_COST = {
    0:  10,   # unknown / no data
    1: 100,   # urban / built-up
    2:  50,   # farmland / cropland
    3:  20,   # grassland / savanna
    4:  60,   # forest / woodland
    5:  80,   # wetland
    6:  30,   # bare soil / rock
    7:  15,   # open water (small)
    10: 100,  # ESA: tree cover
    20:  30,  # ESA: shrubland
    30:  20,  # ESA: grassland
    40:  50,  # ESA: cropland
    50: 100,  # ESA: built-up
    60:  25,  # ESA: bare / sparse
    80: 100,  # ESA: permanent water
    90:  80,  # ESA: herbaceous wetland
    95:  85,  # ESA: mangroves
}


class QGISStyleCostSurfaceAnalyzer:
    """
    Complete QGIS-style cost surface analysis and least-cost routing.

    Pipeline
    --------
    1. build_base_grid()          – define CRS / resolution / extent
    2. rasterize_layer()          – vector → raster aligned to base grid
    3. friction_*()               – layer-specific cost logic (1-100 raw)
    4. normalize_to_1_10()        – scale every layer to 1-10
    5. weighted_overlay()         – Σ(weight_i × layer_i), weights sum to 1
    6. classify_cost_surface()    – quantile or equal-interval, 5 classes
    7. render_classified_image()  – QGIS colour ramp + speckle
    8. least_cost_path_dijkstra() – Dijkstra, diagonal × 1.414
    """

    def __init__(self, config, output_dir='static'):
        self.config = config
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.uganda_bounds = [29.5, -1.5, 35.0, 4.5]
        self.default_resolution = 0.001
        self.target_crs = 'EPSG:4326'

    # ------------------------------------------------------------------
    # 1. BASE GRID
    # ------------------------------------------------------------------
    def build_base_grid(self, bounds, resolution_m=100):
        """
        Return (shape, transform) for a raster grid aligned to *bounds*
        at *resolution_m* metres.  All layers must use the same grid.
        """
        min_lon, min_lat, max_lon, max_lat = bounds
        # 1 degree ≈ 111 320 m (longitude), 110 540 m (latitude)
        center_lat = 0.5 * (min_lat + max_lat)
        m_per_deg_lon = 111320.0 * max(np.cos(np.radians(center_lat)), 0.01)
        m_per_deg_lat = 110540.0
        width  = max(4, int((max_lon - min_lon) * m_per_deg_lon / resolution_m))
        height = max(4, int((max_lat - min_lat) * m_per_deg_lat / resolution_m))
        transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)
        return (height, width), transform

    # ------------------------------------------------------------------
    # 2. RASTERIZATION  (vector → raster, aligned to base grid)
    # ------------------------------------------------------------------
    def rasterize_layer(self, gdf, bounds, shape, burn_value=1):
        """
        Rasterize a GeoDataFrame onto the base grid.
        Returns a uint8 binary array (1 = feature present, 0 = absent).
        """
        transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3],
                                shape[1], shape[0])
        if gdf.empty:
            return np.zeros(shape, dtype=np.uint8)
        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs('EPSG:4326')
        shapes = ((geom, burn_value) for geom in gdf.geometry if geom is not None)
        out = rasterize(shapes, out_shape=shape, transform=transform,
                        fill=0, all_touched=True, dtype=np.uint8)
        return out

    def load_and_rasterize_vector(self, vector_path, bounds, shape):
        """Load a vector file and rasterize it onto the base grid."""
        try:
            gdf = gpd.read_file(vector_path)
            return self.rasterize_layer(gdf, bounds, shape)
        except Exception as e:
            logger.warning(f"Could not load {vector_path}: {e}")
            return np.zeros(shape, dtype=np.uint8)

    def load_and_resample_raster(self, raster_path, bounds, shape):
        """Load a GeoTIFF and resample it onto the base grid."""
        try:
            with rasterio.open(raster_path) as src:
                dst_transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3],
                                            shape[1], shape[0])
                dest = np.zeros(shape, dtype=np.float32)
                reproject(
                    source=rasterio.band(src, 1),
                    destination=dest,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs='EPSG:4326',
                    resampling=Resampling.bilinear,
                )
                return dest
        except Exception as e:
            logger.warning(f"Could not load raster {raster_path}: {e}")
            return np.zeros(shape, dtype=np.float32)

    # ------------------------------------------------------------------
    # 3. FRICTION / COST MAPPING  (raw cost 1-100)
    # ------------------------------------------------------------------
    def _pixel_sampling(self, bounds, shape):
        """Return (m_per_px_y, m_per_px_x) for distance_transform_edt."""
        h, w = shape
        center_lat = 0.5 * (bounds[1] + bounds[3])
        deg_per_px_x = (bounds[2] - bounds[0]) / max(w, 1)
        deg_per_px_y = (bounds[3] - bounds[1]) / max(h, 1)
        m_per_px_x = deg_per_px_x * 111320.0 * max(np.cos(np.radians(center_lat)), 0.01)
        m_per_px_y = deg_per_px_y * 110540.0
        return (m_per_px_y, m_per_px_x)

    def friction_barrier(self, binary_raster, inside_cost=100, outside_cost=1):
        """
        Barriers (protected areas, wetlands, lakes):
        inside = very high cost, outside = low cost.
        """
        return np.where(binary_raster > 0,
                        float(inside_cost),
                        float(outside_cost)).astype(np.float32)

    def friction_distance_penalty(self, binary_raster, bounds, shape,
                                  max_dist_m=5000, near_cost=100, far_cost=1):
        """
        Distance-based penalty: closer to feature = higher cost.
        Used for rivers (crossing penalty), settlements, commercial areas.
        """
        sampling = self._pixel_sampling(bounds, shape)
        presence = (binary_raster > 0).astype(np.uint8)
        if not presence.any():
            return np.full(shape, far_cost, dtype=np.float32)
        dist_m = distance_transform_edt(1 - presence, sampling=sampling)
        cost = np.clip(near_cost - (dist_m / max_dist_m) * (near_cost - far_cost),
                       far_cost, near_cost)
        return cost.astype(np.float32)

    def friction_distance_benefit(self, binary_raster, bounds, shape,
                                  max_dist_m=2000, near_cost=1, far_cost=10):
        """
        Distance-based benefit: closer to feature = LOWER cost.
        Used for roads and hospitals (easier access = cheaper construction).
        """
        sampling = self._pixel_sampling(bounds, shape)
        presence = (binary_raster > 0).astype(np.uint8)
        if not presence.any():
            return np.full(shape, far_cost, dtype=np.float32)
        dist_m = distance_transform_edt(1 - presence, sampling=sampling)
        cost = np.clip(near_cost + (dist_m / max_dist_m) * (far_cost - near_cost),
                       near_cost, far_cost)
        return cost.astype(np.float32)

    def friction_land_use(self, raster_data, bounds, shape):
        """
        Land-use cost using the _LAND_USE_COST dictionary.
        Handles both binary (presence/absence) and classified rasters.
        """
        cost = np.full(shape, 20.0, dtype=np.float32)   # default: open land
        unique_vals = np.unique(raster_data.astype(np.int32))
        for v in unique_vals:
            if v in _LAND_USE_COST:
                cost[raster_data.astype(np.int32) == v] = _LAND_USE_COST[v]
        return cost

    def friction_elevation_slope(self, elevation_data):
        """
        Derive slope from elevation; steeper = higher cost (1-100).
        """
        dy, dx = np.gradient(elevation_data.astype(np.float32))
        slope_deg = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
        cost = np.clip((slope_deg / 45.0) * 99.0 + 1.0, 1.0, 100.0)
        return cost.astype(np.float32)

    # ------------------------------------------------------------------
    # 4. NORMALISATION  (1-10 scale, balanced contribution)
    # ------------------------------------------------------------------
    @staticmethod
    def normalize_to_1_10(layer):
        """Scale any cost layer to the range [1, 10]."""
        lo = float(np.nanmin(layer))
        hi = float(np.nanmax(layer))
        if hi <= lo:
            return np.full_like(layer, 5.0, dtype=np.float32)
        return (1.0 + 9.0 * (layer - lo) / (hi - lo)).astype(np.float32)

    # ------------------------------------------------------------------
    # 5. WEIGHTED OVERLAY
    # ------------------------------------------------------------------
    @staticmethod
    def normalize_weights(weights_dict):
        """Normalise weights so they sum to 1.0."""
        total = sum(abs(v) for v in weights_dict.values())
        if total == 0:
            n = len(weights_dict)
            return {k: 1.0 / n for k in weights_dict}
        return {k: abs(v) / total for k, v in weights_dict.items()}

    def weighted_overlay(self, normalized_layers, normalized_weights, debug=False):
        """
        cost_surface = Σ(weight_i × layer_i)
        All layers must already be normalised to 1-10.
        Returns float32 array.
        """
        first = next(iter(normalized_layers.values()))
        h, w = first.shape
        surface = np.zeros((h, w), dtype=np.float32)
        for name, layer in normalized_layers.items():
            w_val = normalized_weights.get(name, 0.0)
            surface += w_val * layer
            if debug:
                logger.info(f"  [{name}] weight={w_val:.4f}  "
                            f"min={layer.min():.2f} max={layer.max():.2f} "
                            f"contribution_range=[{(w_val*layer.min()):.3f}, "
                            f"{(w_val*layer.max()):.3f}]")
        if debug:
            logger.info(f"  Surface: min={surface.min():.3f} "
                        f"max={surface.max():.3f} mean={surface.mean():.3f}")
        return surface

    # keep old name for backward compat
    def compute_weighted_overlay(self, cost_rasters, normalized_weights):
        return self.weighted_overlay(cost_rasters, normalized_weights)

    # ------------------------------------------------------------------
    # 6. CLASSIFICATION  (quantile preferred, mirrors QGIS)
    # ------------------------------------------------------------------
    def classify_cost_surface(self, cost_surface, n_classes=5, method='quantile'):
        """
        Classify cost surface into n_classes using quantile or equal-interval.

        Returns dict:
          classified  – uint8 array (1..n_classes)
          breaks      – list of (lo, hi) raw-value tuples
          colors      – list of (R,G,B) tuples
          labels      – list of label strings
          method, n_classes, global_min, global_max
        """
        flat = cost_surface[np.isfinite(cost_surface)].ravel()
        global_min = float(flat.min())
        global_max = float(flat.max())

        if method == 'quantile':
            pcts = np.linspace(0, 100, n_classes + 1)
            edges = np.percentile(flat, pcts).tolist()
        else:
            edges = np.linspace(global_min, global_max, n_classes + 1).tolist()

        # deduplicate
        uniq = [edges[0]]
        for e in edges[1:]:
            if e > uniq[-1] + 1e-9:
                uniq.append(e)
        while len(uniq) < n_classes + 1:
            uniq.append(uniq[-1] + 1e-6)
        edges = uniq[:n_classes + 1]
        actual = len(edges) - 1

        # colour ramp
        if actual == 5:
            colors = list(_QGIS_5_COLORS)
        else:
            colors = []
            for i in range(actual):
                t = i / max(actual - 1, 1)
                if t < 0.25:
                    c = _lerp_color(_QGIS_5_COLORS[0], _QGIS_5_COLORS[1], t / 0.25)
                elif t < 0.5:
                    c = _lerp_color(_QGIS_5_COLORS[1], _QGIS_5_COLORS[2], (t - 0.25) / 0.25)
                elif t < 0.75:
                    c = _lerp_color(_QGIS_5_COLORS[2], _QGIS_5_COLORS[3], (t - 0.5) / 0.25)
                else:
                    c = _lerp_color(_QGIS_5_COLORS[3], _QGIS_5_COLORS[4], (t - 0.75) / 0.25)
                colors.append((int(c[0]), int(c[1]), int(c[2])))

        classified = np.zeros(cost_surface.shape, dtype=np.uint8)
        breaks, labels = [], []
        for i in range(actual):
            lo, hi = edges[i], edges[i + 1]
            mask = (cost_surface >= lo) & (cost_surface < hi) if i < actual - 1 \
                   else (cost_surface >= lo) & np.isfinite(cost_surface)
            classified[mask] = i + 1
            breaks.append((round(lo, 3), round(hi, 3)))
            labels.append(f'{lo:.2f} \u2013 {hi:.2f}')

        return {
            'classified': classified,
            'breaks': breaks,
            'colors': colors,
            'labels': labels,
            'method': method,
            'n_classes': actual,
            'global_min': round(global_min, 3),
            'global_max': round(global_max, 3),
        }

    # ------------------------------------------------------------------
    # 7. RENDERING  (QGIS speckle + colour ramp)
    # ------------------------------------------------------------------
    def render_classified_image(self, classified_array, colors, noise_seed=42):
        """
        Render classified array → RGBA PNG with per-pixel speckle noise.
        Full opacity so all 5 colors are clearly visible on the map.
        """
        h, w = classified_array.shape
        rng = np.random.default_rng(noise_seed)
        noise = rng.integers(-8, 9, size=(h, w), dtype=np.int16)
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        for idx, (r, g, b) in enumerate(colors):
            mask = classified_array == (idx + 1)
            rgba[mask, 0] = np.clip(r + noise[mask], 0, 255).astype(np.uint8)
            rgba[mask, 1] = np.clip(g + noise[mask], 0, 255).astype(np.uint8)
            rgba[mask, 2] = np.clip(b + (noise[mask] // 2), 0, 255).astype(np.uint8)
            rgba[mask, 3] = 255   # fully opaque — Leaflet opacity controls transparency
        return rgba

    # ------------------------------------------------------------------
    # 8. LEAST-COST PATH  (Using skimage.graph.route_through_array)
    # ------------------------------------------------------------------
    def least_cost_path_skimage(self, cost_surface, start_rc, end_rc):
        """
        QGIS-style least-cost path using skimage.graph.route_through_array.
        
        This is the RECOMMENDED method as it exactly replicates QGIS behavior:
        - Uses Dijkstra's algorithm internally
        - Diagonal movement cost = 1.414 (geometric=True)
        - 8-directional movement (fully_connected=True)
        - Minimizes accumulated cost (NOT straight-line distance)
        
        Args:
            cost_surface: 2D float32 array (traversal cost per pixel)
            start_rc: (row, col) start pixel
            end_rc: (row, col) end pixel
            
        Returns:
            dict with:
                - path: list of (row, col) pixels
                - total_cost: accumulated cost along path
        """
        try:
            from skimage.graph import route_through_array
        except ImportError:
            logger.error("skimage not installed. Install with: pip install scikit-image")
            return self.least_cost_path_dijkstra(cost_surface, start_rc, end_rc)
        
        h, w = cost_surface.shape
        
        # Clamp coordinates to valid range
        sr, sc = (max(0, min(h - 1, int(start_rc[0]))),
                  max(0, min(w - 1, int(start_rc[1]))))
        er, ec = (max(0, min(h - 1, int(end_rc[0]))),
                  max(0, min(w - 1, int(end_rc[1]))))
        
        logger.info(f"🔍 Pathfinding: start=({sr},{sc}) end=({er},{ec})")
        logger.info(f"🔍 Cost surface: shape={cost_surface.shape}, "
                   f"min={cost_surface.min():.2f}, max={cost_surface.max():.2f}")
        
        try:
            # CRITICAL PARAMETERS:
            # - geometric=True: diagonal movement cost = sqrt(2) ≈ 1.414
            # - fully_connected=True: 8-directional movement (N,NE,E,SE,S,SW,W,NW)
            indices, total_cost = route_through_array(
                cost_surface,
                start=(sr, sc),
                end=(er, ec),
                geometric=True,        # Diagonal cost = 1.414
                fully_connected=True   # 8-direction movement
            )
            
            # Convert to list of tuples
            path = [(int(r), int(c)) for r, c in indices]
            
            logger.info(f"✓ Least-cost path: {len(path)} pixels, "
                       f"accumulated cost={total_cost:.2f}")
            
            return {
                'path': path,
                'total_cost': float(total_cost),
                'num_pixels': len(path)
            }
            
        except Exception as e:
            logger.error(f"route_through_array failed: {e}")
            # Fallback to manual Dijkstra
            return self.least_cost_path_dijkstra(cost_surface, start_rc, end_rc)
    
    def least_cost_path_dijkstra(self, cost_surface, start_rc, end_rc):
        """
        Manual Dijkstra implementation (fallback if skimage not available).
        
        Args:
            cost_surface: 2D float32 array
            start_rc: (row, col) start pixel
            end_rc:   (row, col) end pixel

        Returns:
            dict with path and total_cost
        """
        from heapq import heappush, heappop

        h, w = cost_surface.shape
        INF = float('inf')

        sr, sc = (max(0, min(h - 1, start_rc[0])),
                  max(0, min(w - 1, start_rc[1])))
        er, ec = (max(0, min(h - 1, end_rc[0])),
                  max(0, min(w - 1, end_rc[1])))

        dist = np.full((h, w), INF, dtype=np.float64)
        dist[sr, sc] = 0.0
        prev = {}
        heap = [(0.0, sr, sc)]

        while heap:
            d, r, c = heappop(heap)
            if d > dist[r, c]:
                continue
            if r == er and c == ec:
                break
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < h and 0 <= nc < w):
                        continue
                    move = 1.4142135623730951 if (dr != 0 and dc != 0) else 1.0
                    nd = d + float(cost_surface[nr, nc]) * move
                    if nd < dist[nr, nc]:
                        dist[nr, nc] = nd
                        prev[(nr, nc)] = (r, c)
                        heappush(heap, (nd, nr, nc))

        # reconstruct
        if dist[er, ec] == INF:
            logger.warning("Dijkstra: no path found")
            return {'path': [], 'total_cost': INF, 'num_pixels': 0}
        
        path = []
        cur = (er, ec)
        while cur in prev:
            path.append(cur)
            cur = prev[cur]
        path.append((sr, sc))
        path.reverse()
        
        logger.info(f"✓ Dijkstra path: {len(path)} pixels, "
                    f"accumulated cost={dist[er,ec]:.2f}")
        
        return {
            'path': path,
            'total_cost': float(dist[er, ec]),
            'num_pixels': len(path)
        }

    # ------------------------------------------------------------------
    # COORDINATE HELPERS (Using rasterio transform)
    # ------------------------------------------------------------------
    @staticmethod
    def latlon_to_pixel_transform(lat, lon, transform):
        """
        Convert lat/lon to pixel coordinates using rasterio transform.
        This is the CORRECT method for coordinate mapping.
        
        Args:
            lat, lon: Geographic coordinates (WGS84)
            transform: rasterio.Affine transform
            
        Returns:
            (row, col) pixel coordinates
        """
        try:
            # rasterio uses (x, y) = (lon, lat) order
            col, row = ~transform * (lon, lat)
            return (int(round(row)), int(round(col)))
        except Exception as e:
            logger.warning(f"Transform failed: {e}, using fallback")
            return None
    
    @staticmethod
    def pixel_to_latlon_transform(row, col, transform):
        """
        Convert pixel coordinates to lat/lon using rasterio transform.
        
        Args:
            row, col: Pixel coordinates
            transform: rasterio.Affine transform
            
        Returns:
            (lat, lon) geographic coordinates
        """
        try:
            # Get center of pixel
            lon, lat = transform * (col + 0.5, row + 0.5)
            return (lat, lon)
        except Exception as e:
            logger.warning(f"Transform failed: {e}")
            return None
    
    @staticmethod
    def latlon_to_pixel(lat, lon, bounds, shape):
        """
        Simple lat/lon to pixel conversion (fallback method).
        Use latlon_to_pixel_transform() when transform is available.
        """
        h, w = shape
        row = int((bounds[3] - lat) / (bounds[3] - bounds[1]) * h)
        col = int((lon - bounds[0]) / (bounds[2] - bounds[0]) * w)
        return (max(0, min(h - 1, row)), max(0, min(w - 1, col)))

    @staticmethod
    def pixel_to_latlon(row, col, bounds, shape):
        """
        Simple pixel to lat/lon conversion (fallback method).
        Use pixel_to_latlon_transform() when transform is available.
        """
        h, w = shape
        lat = bounds[3] - (row / h) * (bounds[3] - bounds[1])
        lon = bounds[0] + (col / w) * (bounds[2] - bounds[0])
        return lat, lon

    @staticmethod
    def path_pixels_to_coords(path_pixels, bounds, shape):
        """Convert list of (row,col) to [[lon,lat], ...] GeoJSON coordinates."""
        coords = []
        h, w = shape
        for r, c in path_pixels:
            lat = bounds[3] - (r / h) * (bounds[3] - bounds[1])
            lon = bounds[0] + (c / w) * (bounds[2] - bounds[0])
            coords.append([lon, lat])
        return coords
    
    @staticmethod
    def path_pixels_to_coords_transform(path_pixels, transform):
        """
        Convert list of (row,col) to [[lon,lat], ...] using rasterio transform.
        This is the CORRECT method for coordinate conversion.
        """
        coords = []
        for r, c in path_pixels:
            lon, lat = transform * (c + 0.5, r + 0.5)
            coords.append([lon, lat])
        return coords

    # ------------------------------------------------------------------
    # EXPORT HELPERS
    # ------------------------------------------------------------------
    def export_cost_surface_geotiff(self, cost_surface, bounds, output_path):
        h, w = cost_surface.shape
        transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], w, h)
        with rasterio.open(output_path, 'w', driver='GTiff',
                           height=h, width=w, count=1,
                           dtype=np.float32, crs='EPSG:4326',
                           transform=transform) as dst:
            dst.write(cost_surface, 1)
        logger.info(f"✓ GeoTIFF saved: {output_path}")

    def export_route_geojson(self, path_pixels, bounds, shape):
        """Return a GeoJSON Feature dict for the route."""
        coords = self.path_pixels_to_coords(path_pixels, bounds, shape)
        return {
            'type': 'Feature',
            'properties': {'name': 'Least-Cost Route'},
            'geometry': {'type': 'LineString', 'coordinates': coords},
        }

    # ------------------------------------------------------------------
    # BACKWARD-COMPAT WRAPPERS  (used by routes_api.py)
    # ------------------------------------------------------------------
    def prepare_raster_from_vector(self, vector_path, bounds, shape,
                                   reclassify_func=None, column=None):
        binary = self.load_and_rasterize_vector(vector_path, bounds, shape)
        if reclassify_func:
            try:
                gdf = gpd.read_file(vector_path)
                transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3],
                                        shape[1], shape[0])
                return reclassify_func(binary, gdf, bounds, transform).astype(np.float32)
            except Exception:
                pass
        return np.where(binary > 0, 100.0, 1.0).astype(np.float32)

    def prepare_raster_from_raster(self, raster_path, bounds, shape,
                                   reclassify_func=None):
        data = self.load_and_resample_raster(raster_path, bounds, shape)
        if reclassify_func:
            try:
                return reclassify_func(data).astype(np.float32)
            except Exception:
                pass
        return data.astype(np.float32)

    def reclassify_protected_areas(self, rasterized, gdf, bounds, transform):
        return self.friction_barrier(rasterized, inside_cost=100, outside_cost=1)

    def reclassify_water_distance(self, rasterized, gdf, bounds, transform):
        return self.friction_distance_penalty(rasterized, bounds, rasterized.shape)

    def reclassify_wetlands(self, rasterized, gdf, bounds, transform):
        return self.friction_barrier(rasterized, inside_cost=90, outside_cost=1)

    def reclassify_land_use(self, rasterized, gdf, bounds, transform):
        return self.friction_land_use(rasterized, bounds, rasterized.shape)

    def reclassify_elevation_slope(self, elevation_data):
        return self.friction_elevation_slope(elevation_data)

    # ------------------------------------------------------------------
    # FULL PIPELINE  (called by routes_qgis_api.py)
    # ------------------------------------------------------------------
    def run_full_pipeline(self, layers_config, start_point, end_point,
                          bounds=None, resolution=None, generate_route=True,
                          algorithm='dijkstra'):
        """
        QGIS-style cost surface analysis and least-cost path routing.
        
        WORKFLOW:
        1. Cost Surface Creation - Generate weighted overlay raster
        2. Coordinate → Pixel Mapping - Convert lat/lon to pixel indices
        3. Raster-based Pathfinding - Use skimage.graph.route_through_array
        4. Path Reconstruction - Convert pixels back to geographic coordinates
        5. GeoJSON Export - Create LineString for display

        Args:
            layers_config: {name: {enabled, weight, path, type}}
            start_point: (lat, lon) tuple
            end_point: (lat, lon) tuple
            bounds: [min_lon, min_lat, max_lon, max_lat]
            resolution: pixel size in degrees (None → use resolution_m=100)
            generate_route: If False, ONLY generate cost surface (no routing)
            algorithm: 'dijkstra' (skimage) or 'astar' (fallback)
            
        Returns:
            dict with cost_surface_tif, cost_surface_png, route_shp, metadata
        """
        t0 = time.time()
        if bounds is None:
            bounds = self.uganda_bounds
        resolution_m = 100 if resolution is None else int(resolution * 111320)
        
        # Step 1: Build base grid and get transform
        shape, transform = self.build_base_grid(bounds, resolution_m=resolution_m)
        
        logger.info("=" * 60)
        logger.info("QGIS-STYLE COST SURFACE ANALYSIS")
        logger.info("=" * 60)
        logger.info(f"📐 Raster shape: {shape[1]} × {shape[0]} pixels")
        logger.info(f"📏 Resolution: {resolution_m}m per pixel")
        logger.info(f"🗺️  Bounds: {bounds}")
        logger.info(f"🔧 Transform: {transform}")

        # Step 2: Load and process layers
        layer_reclass = {
            'protected_areas': self.reclassify_protected_areas,
            'rivers':          self.reclassify_water_distance,
            'wetlands':        self.reclassify_wetlands,
            'lakes':           self.reclassify_water_distance,
            'land_use':        self.reclassify_land_use,
            'elevation':       (lambda d, *a: self.reclassify_elevation_slope(d)),
            'settlements':     self.reclassify_water_distance,
            'roads':           self.reclassify_water_distance,
        }

        raw_rasters, weights_raw = {}, {}
        for name, cfg in layers_config.items():
            if not cfg.get('enabled', False):
                continue
            path = cfg.get('path')
            if not path or not os.path.exists(path):
                logger.warning(f"⚠️  {name}: path not found")
                continue
            fn = layer_reclass.get(name)
            if path.lower().endswith(('.tif', '.tiff')):
                r = self.prepare_raster_from_raster(path, bounds, shape, fn)
            else:
                r = self.prepare_raster_from_vector(path, bounds, shape, fn)
            raw_rasters[name] = r
            weights_raw[name] = float(cfg.get('weight', 1.0))
            logger.info(f"✓ {name}: loaded, weight={weights_raw[name]:.3f}")

        if not raw_rasters:
            raise ValueError("No valid layers loaded")

        # Step 3: Normalize and create weighted overlay (COST SURFACE)
        logger.info("-" * 60)
        logger.info("COST SURFACE GENERATION")
        logger.info("-" * 60)
        
        norm_layers = {n: self.normalize_to_1_10(r) for n, r in raw_rasters.items()}
        norm_weights = self.normalize_weights(weights_raw)
        cost_surface = self.weighted_overlay(norm_layers, norm_weights, debug=True)
        
        logger.info(f"📊 Cost Surface Statistics:")
        logger.info(f"   Min: {cost_surface.min():.3f}")
        logger.info(f"   Max: {cost_surface.max():.3f}")
        logger.info(f"   Mean: {cost_surface.mean():.3f}")
        logger.info(f"   Std: {cost_surface.std():.3f}")

        # Step 4: Export cost surface as GeoTIFF
        tif_path = os.path.join(self.output_dir, 'cost_surface.tif')
        self.export_cost_surface_geotiff(cost_surface, bounds, tif_path)

        # Step 5: Classify and render cost surface
        cls = self.classify_cost_surface(cost_surface, n_classes=5, method='quantile')
        rgba = self.render_classified_image(cls['classified'], cls['colors'])
        png_path = os.path.join(self.output_dir, 'cost_surface.png')
        Image.fromarray(rgba, 'RGBA').save(png_path)
        
        logger.info(f"✓ Cost surface saved: {tif_path}")
        logger.info(f"✓ Visualization saved: {png_path}")

        # Step 6: ROUTING (only if generate_route=True)
        route_shp = None
        route_geojson = None
        path_result = None
        
        if generate_route and start_point and end_point:
            logger.info("-" * 60)
            logger.info("LEAST-COST PATH ROUTING")
            logger.info("-" * 60)
            logger.info(f"📍 Start: {start_point}")
            logger.info(f"📍 End: {end_point}")
            
            # Step 6a: Coordinate → Pixel Mapping (CRITICAL)
            start_rc = self.latlon_to_pixel_transform(start_point[0], start_point[1], transform)
            end_rc = self.latlon_to_pixel_transform(end_point[0], end_point[1], transform)
            
            # Fallback if transform fails
            if start_rc is None:
                start_rc = self.latlon_to_pixel(start_point[0], start_point[1], bounds, shape)
            if end_rc is None:
                end_rc = self.latlon_to_pixel(end_point[0], end_point[1], bounds, shape)
            
            logger.info(f"🔍 Start pixel: {start_rc}")
            logger.info(f"🔍 End pixel: {end_rc}")
            
            # Step 6b: Raster-based Pathfinding (CORE ENGINE)
            if algorithm == 'skimage' or algorithm == 'dijkstra':
                path_result = self.least_cost_path_skimage(cost_surface, start_rc, end_rc)
            else:
                path_result = self.least_cost_path_dijkstra(cost_surface, start_rc, end_rc)
            
            path_px = path_result.get('path', [])
            
            if path_px:
                logger.info(f"✓ Path found: {len(path_px)} pixels")
                logger.info(f"✓ Total cost: {path_result.get('total_cost', 0):.2f}")
                
                # Step 6c: Path Reconstruction (pixel → geographic)
                coords = self.path_pixels_to_coords_transform(path_px, transform)
                
                # Step 6d: Convert to LineString and export
                line = LineString([(c[0], c[1]) for c in coords])
                gdf = gpd.GeoDataFrame({'name': ['route']}, geometry=[line], crs='EPSG:4326')
                route_shp = os.path.join(self.output_dir, 'route.shp')
                gdf.to_file(route_shp)
                
                # Step 6e: Create GeoJSON for display
                route_geojson = {
                    'type': 'Feature',
                    'properties': {
                        'name': 'Least-Cost Route',
                        'total_cost': path_result.get('total_cost', 0),
                        'num_pixels': len(path_px),
                        'algorithm': algorithm
                    },
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': coords
                    }
                }
                
                logger.info(f"✓ Route exported: {route_shp}")
            else:
                logger.warning("❌ No path found")
        else:
            logger.info("ℹ️  Route generation skipped (generate_route=False)")

        elapsed = time.time() - t0
        logger.info("=" * 60)
        logger.info(f"✓ Pipeline completed in {elapsed:.2f}s")
        logger.info("=" * 60)

        return {
            'cost_surface_tif': tif_path,
            'cost_surface_png': png_path,
            'route_shp': route_shp,
            'route_geojson': route_geojson,
            'bounds': bounds,
            'transform': str(transform),
            'metadata': {
                'resolution_m': resolution_m,
                'shape': list(shape),
                'weights': norm_weights,
                'min_cost': float(cost_surface.min()),
                'max_cost': float(cost_surface.max()),
                'mean_cost': float(cost_surface.mean()),
                'path_length_nodes': len(path_result.get('path', [])) if path_result else 0,
                'total_cost': float(path_result.get('total_cost', 0)) if path_result else 0,
                'algorithm': algorithm,
                'processing_time_s': round(elapsed, 2),
            },
        }


# ---------------------------------------------------------------------------
# MODULE-LEVEL HELPERS
# ---------------------------------------------------------------------------
def _lerp_color(c1, c2, t):
    return (c1[0] + (c2[0] - c1[0]) * t,
            c1[1] + (c2[1] - c1[1]) * t,
            c1[2] + (c2[2] - c1[2]) * t)


# kept for any external callers
def run_full_pipeline_standalone(analyzer, layers_config, start_point, end_point,
                                 bounds=None, resolution=None):
    return analyzer.run_full_pipeline(layers_config, start_point, end_point,
                                      bounds=bounds, resolution=resolution)
