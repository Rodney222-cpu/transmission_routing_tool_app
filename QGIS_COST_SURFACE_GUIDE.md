# QGIS-Style Cost Surface Analysis & Least-Cost Routing

## 🎯 Overview

Complete Flask backend that performs cost surface analysis and least-cost routing **similar to QGIS**, following a strict 7-step pipeline.

## 📋 Implementation Files

- **Core Processor**: `app/optimizer/qgis_cost_surface.py`
- **API Endpoint**: `app/routes_qgis_api.py`
- **Test Suite**: `test_qgis_cost_surface.py`
- **Blueprint Registration**: `app/__init__.py`

## 🔧 Processing Pipeline (STRICT - 7 Steps)

### Step 1: Raster Preparation
- **Vector → Raster**: Rasterize GeoJSON/Shapefile using `rasterio.features.rasterize()`
- **Raster → Raster**: Load GeoTIFF directly
- **Reproject**: All rasters converted to EPSG:4326 (WGS84)
- **Align**: Identical resolution, extent, and grid origin
- **Output**: Aligned numpy arrays

### Step 2: Layer-Specific Reclassification (1-100 Scale)
Each layer has its own reclassification logic:

| Layer | Logic | Cost Range |
|-------|-------|------------|
| **Protected Areas** | Inside = 100, Outside = 1 | Binary |
| **Rivers/Lakes** | Distance-based: 0m = 100, 5000m = 1 | Continuous |
| **Wetlands** | Inside = 90, Outside = 1 | Binary |
| **Land Use** | Urban=100, Forest=60, Farmland=50, Grassland=20 | Categorical |
| **Elevation** | Derive slope → 0°=1, 45°=100 | Continuous |

### Step 3: Weight Normalization
- Uses **only selected layers**
- Normalizes weights so **sum = 1.0**
- If all weights are 0 → Uses equal weights

### Step 4: Weighted Overlay (Core Computation)
```python
cost_surface = Σ(weight_i × raster_i)
```
- Combines all cost rasters with normalized weights
- Saves as **GeoTIFF**: `/static/cost_surface.tif`

### Step 5: Least-Cost Path (A* Algorithm)
- Treats raster as **grid graph**
- Each pixel = node, Cost = pixel value
- **8-connected** neighbors (diagonal movement allowed)
- Finds optimal path from start to end following **lowest accumulated cost**

### Step 6: Export Route
- Converts path pixels to **LineString geometry**
- Saves as **Shapefile**: `/static/route.shp`
- **Vector format** (NOT raster)

### Step 7: Visualization
- Normalizes cost surface to **0-255**
- Applies **color ramp**:
  - 🟢 **Green** = Low cost
  - 🟡 **Yellow** = Medium cost
  - 🔴 **Red** = High cost
- Exports as **PNG**: `/static/cost_surface.png`

## 🌐 API Endpoint

### POST `/api/qgis/generate-cost-surface`

#### Request Body

```json
{
    "layers": {
        "protected_areas": {
            "enabled": true,
            "weight": 0.2,
            "type": "vector"
        },
        "rivers": {
            "enabled": true,
            "weight": 0.2,
            "type": "vector"
        },
        "wetlands": {
            "enabled": true,
            "weight": 0.15,
            "type": "vector"
        },
        "land_use": {
            "enabled": true,
            "weight": 0.15,
            "type": "vector"
        },
        "elevation": {
            "enabled": true,
            "weight": 0.3,
            "type": "raster"
        }
    },
    "start_point": {
        "lat": 0.3476,
        "lon": 32.5825
    },
    "end_point": {
        "lat": 1.3733,
        "lon": 32.2903
    },
    "bounds": [29.5, -1.5, 35.0, 4.5],
    "resolution": 0.001
}
```

#### Response

```json
{
    "success": true,
    "cost_surface_tif": "/static/cost_surface.tif",
    "cost_surface_png": "/static/cost_surface.png",
    "route_shp": "/static/route.shp",
    "bounds": [29.5, -1.5, 35.0, 4.5],
    "metadata": {
        "resolution": 0.001,
        "shape": [6000, 5500],
        "weights": {
            "protected_areas": 0.2,
            "rivers": 0.2,
            "wetlands": 0.15,
            "land_use": 0.15,
            "elevation": 0.3
        },
        "min_cost": 5.23,
        "max_cost": 87.45,
        "mean_cost": 42.18,
        "path_length_nodes": 342,
        "processing_time_s": 12.5
    }
}
```

## 🧪 Testing

### Run Test Suite

```bash
python test_qgis_cost_surface.py
```

### Tests Include:

1. ✅ **Reclassification Logic** - Each layer's unique cost mapping
2. ✅ **Weight Normalization** - Sum to 1.0
3. ✅ **Weighted Overlay** - Correct weighted sum
4. ✅ **A* Pathfinding** - Optimal route on cost surface
5. ✅ **Full Pipeline** - End-to-end with synthetic data
6. ✅ **Layer Path Resolution** - Uganda GIS data loading

### Test Results

```
✅ ALL TESTS PASSED! (6/6)
```

## 📦 Output Files

| File | Format | Purpose |
|------|--------|---------|
| `cost_surface.tif` | **GeoTIFF** | Raster cost surface (QGIS compatible) |
| `cost_surface.png` | **PNG** | Colored visualization for web display |
| `route.shp` | **Shapefile** | Vector least-cost path (QGIS compatible) |

## ⚙️ Constraints (IMPORTANT)

✅ **Cost surface MUST remain raster (GeoTIFF)**  
✅ **DO NOT convert cost surface to shapefile**  
✅ **Route MUST be vector (shapefile)**  
✅ **All rasters perfectly aligned before overlay**  
✅ **Output visually resembles QGIS-style cost surface**  
✅ **Routing follows lowest accumulated cost, NOT straight-line**  

## 🚀 Usage Example

### Python (Backend)

```python
from app.optimizer.qgis_cost_surface import QGISStyleCostSurfaceAnalyzer

# Initialize
analyzer = QGISStyleCostSurfaceAnalyzer(config, output_dir='static')

# Configure layers
layers_config = {
    'protected_areas': {
        'enabled': True,
        'weight': 0.2,
        'path': 'data/protected_areas/protected_areas_60.shp'
    },
    'rivers': {
        'enabled': True,
        'weight': 0.2,
        'path': 'data/rivers/Ug_Rivers-original.shp'
    },
    'elevation': {
        'enabled': True,
        'weight': 0.3,
        'path': 'data/elevation/dem_uganda.tif'
    }
}

# Run pipeline
result = analyzer.run_full_pipeline(
    layers_config=layers_config,
    start_point=(0.3476, 32.5825),  # (lat, lon)
    end_point=(1.3733, 32.2903),
    bounds=[29.5, -1.5, 35.0, 4.5],
    resolution=0.001  # ~100m
)

# Access outputs
print(f"Cost surface: {result['cost_surface_tif']}")
print(f"Route: {result['route_shp']}")
print(f"Processing time: {result['metadata']['processing_time_s']}s")
```

### JavaScript (Frontend)

```javascript
async function generateCostSurface() {
    const response = await fetch('/api/qgis/generate-cost-surface', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            layers: {
                protected_areas: { enabled: true, weight: 0.2 },
                rivers: { enabled: true, weight: 0.2 },
                elevation: { enabled: true, weight: 0.3 }
            },
            start_point: { lat: 0.3476, lon: 32.5825 },
            end_point: { lat: 1.3733, lon: 32.2903 },
            bounds: [29.5, -1.5, 35.0, 4.5]
        })
    });
    
    const result = await response.json();
    
    if (result.success) {
        // Display PNG on map
        const imageUrl = `data:image/png;base64,${result.cost_surface_png_base64}`;
        // Add to Leaflet map...
        
        console.log(`Route saved: ${result.route_shp}`);
    }
}
```

## 📊 Layer Reclassification Details

### Protected Areas
```python
if pixel inside protected area:
    cost = 100  # High cost (avoid)
else:
    cost = 1    # Low cost (prefer)
```

### Rivers/Lakes (Distance-Based)
```python
distance = distance_to_nearest_water_pixel()
if distance == 0:
    cost = 100
elif distance >= 5000:
    cost = 1
else:
    cost = 100 - (distance / 5000) * 99  # Linear decrease
```

### Wetlands
```python
if pixel inside wetland:
    cost = 90  # High cost
else:
    cost = 1   # Low cost
```

### Land Use (Categorical)
```python
land_use_class = pixel_value
if land_use_class == 'urban':
    cost = 100
elif land_use_class == 'forest':
    cost = 60
elif land_use_class == 'farmland':
    cost = 50
elif land_use_class == 'grassland':
    cost = 20
else:
    cost = 30  # Default
```

### Elevation (Slope-Derived)
```python
slope = calculate_slope_from_elevation()  # degrees
if slope == 0:
    cost = 1
elif slope >= 45:
    cost = 100
else:
    cost = (slope / 45) * 99 + 1  # Linear increase
```

## 🔍 Key Features

### ✅ QGIS Compatibility
- Outputs standard GeoTIFF and Shapefile formats
- Can be opened directly in QGIS
- Proper CRS (EPSG:4326) and georeferencing

### ✅ Strict Alignment
- All rasters reprojected to same CRS
- Identical resolution and extent
- Perfect pixel alignment for overlay

### ✅ Layer-Specific Logic
- Each layer has unique reclassification
- No generic "one-size-fits-all" rules
- Respects domain knowledge (e.g., slope for elevation)

### ✅ Efficient A* Routing
- Heuristic-guided search
- 8-connected grid (diagonal movement)
- Finds true least-cost path (not straight-line)

### ✅ Professional Visualization
- Green-Yellow-Red color ramp
- Matches QGIS default styling
- Ready for web display

## 📁 Project Structure

```
transmission_routing_tool/
├── app/
│   ├── optimizer/
│   │   └── qgis_cost_surface.py          # Core QGIS-style processor
│   ├── routes_qgis_api.py                # API endpoints
│   └── __init__.py                       # Blueprint registration
├── static/
│   ├── cost_surface.tif                  # Output: Cost surface raster
│   ├── cost_surface.png                  # Output: Visualization
│   └── route.shp                         # Output: Route vector
├── test_qgis_cost_surface.py             # Comprehensive test suite
└── QGIS_COST_SURFACE_GUIDE.md            # This file
```

## 🎓 Comparison with QGIS

| Feature | QGIS | This Implementation |
|---------|------|---------------------|
| Raster preparation | Manual tools | Automated pipeline |
| Reclassification | GUI wizard | Programmatic rules |
| Weighted overlay | Raster calculator | `Σ(weight × raster)` |
| Least-cost path | r.cost.surface + r.drain | A* algorithm |
| Output formats | Multiple | GeoTIFF + PNG + Shapefile |
| CRS handling | Manual | Automatic reprojection |
| Integration | Desktop | Web API (Flask) |

## 🐛 Troubleshooting

### Issue: "No valid layers enabled"
**Solution**: Ensure at least one layer has `"enabled": true` and valid path

### Issue: Division by zero in shapefile export
**Solution**: Pass `shape` parameter to `export_route_shapefile()`

### Issue: Rasters not aligning
**Solution**: Check that all input files have valid CRS and extent

### Issue: A* path not found
**Solution**: Ensure start and end points are within bounds and not in infinite-cost areas

## 📞 API Helper Endpoint

### GET `/api/qgis/layer-info/<layer_name>`

Returns information about a specific layer (path, type, available files).

```json
{
    "success": true,
    "layer": "protected_areas",
    "folder": "data/protected_areas",
    "files": [
        {
            "name": "protected_areas_60.shp",
            "path": "data/protected_areas/protected_areas_60.shp",
            "type": "vector"
        }
    ]
}
```

## 🎉 Summary

This implementation provides a **complete, production-ready** QGIS-style cost surface analysis and least-cost routing backend that:

✅ Follows the strict 7-step pipeline  
✅ Supports both vector and raster inputs  
✅ Uses layer-specific reclassification logic  
✅ Produces standard GIS output formats  
✅ Integrates seamlessly with Flask  
✅ Passes comprehensive test suite (6/6 tests)  
✅ Ready for production deployment  
