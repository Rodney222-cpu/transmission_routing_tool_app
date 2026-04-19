# Uganda Transmission Line Routing Tool - Complete Guide

## 📋 **Table of Contents**

1. [Project Overview](#project-overview)
2. [QGIS Integration](#qgis-integration)
3. [GIS Data Layers](#gis-data-layers)
4. [Basemaps](#basemaps)
5. [AHP Weights & Cost Surface](#ahp-weights--cost-surface)
6. [Route Optimization](#route-optimization)
7. [Start/End Points & Waypoints](#startend-points--waypoints)
8. [QGIS Routing Workflow](#qgis-routing-workflow)
9. [Setup & Installation](#setup--installation)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview

**Application:** Uganda Transmission Line Routing Tool  
**Purpose:** Optimize transmission line routes across Uganda using real GIS data  
**Tech Stack:** Python/Flask, Leaflet.js, Dijkstra/A* algorithms  
**Data Source:** Real Uganda government shapefiles  

### Key Features:
- ✅ 9 QGIS-standard basemaps
- ✅ 10 real Uganda GIS layers
- ✅ Set start/end points and waypoints
- ✅ AHP-weighted cost surface optimization
- ✅ QGIS-style routing workflow
- ✅ Measurement tools
- ✅ Layer management
- ✅ Export options (GeoJSON, XYZ)

---

## QGIS Integration

Your application mimics QGIS functionality while maintaining a simplified UI focused on transmission line routing.

### What's Same as QGIS:
- ✅ Uses same basemap tile servers (OpenStreetMap, Google, ESRI, etc.)
- ✅ Loads same shapefile format (.shp, .shx, .dbf, .prj)
- ✅ Same layer management (checkboxes to toggle)
- ✅ Same spatial analysis methodology (AHP, cost distance)
- ✅ Same attribute table viewing
- ✅ Same measurement tools

### What's Different:
- 🎯 Simplified UI (only transmission line routing features)
- 🇺🇬 Restricted to Uganda only (maxBounds enforced)
- 🚀 Built-in route optimization (no plugins needed)
- 💻 Web-based (no desktop installation)

---

## GIS Data Layers

All layers use **REAL Uganda shapefiles** from your Downloads folder (`C:\Users\PC1\Downloads\shape files\`).

### Layer Status Table:

| Layer | Shapefile | Status | Data Source |
|-------|-----------|--------|-------------|
| 🏔️ Elevation (Contours) | `Ug_Contours_Utedited_2007_Proj.shp` | ✅ Ready | Uganda Govt 2007 |
| 🏫 Schools | `Ug_Schools ORIGINAL.shp` | ✅ Ready | Uganda Education Dept |
| 🛣️ Roads (UNRA 2012) | `Ug_Roads_UNRA_2012.shp` | ✅ Ready | UNRA 2012 |
| 🌊 Rivers | `Ug_Rivers-original.shp` | ✅ Ready | Uganda Water Dept |
| 🌊 Wetlands (1994) | `Wetlands1994.shp` | ✅ Ready | NEMA 1994 |
| 🌊 Lakes | `Ug_Lakes.shp` | ✅ Ready | Uganda Water Dept |
| 🦁 Protected Areas | `protected_areas_60.shp` | ✅ Ready | UWA/NEMA |
| 🏥 Health Facilities | `health_facilities.shp` | ✅ Ready | Uganda Health Ministry |
| 🏢 Commercial Facilities | `commercial_facilities.shp` | ✅ Ready | Uganda Commerce |
| 🏘️ Trading Centres | `Ug_Trading_Centres ORIGINAL.shp` | ✅ Ready | Uganda Commerce |

### File Locations:

All shapefiles are stored in: `d:\transmission_routing_tool\data\`

```
data/
├── elevation/          ← Ug_Contours_Utedited_2007_Proj.*
├── schools/            ← Ug_Schools ORIGINAL.*
├── roads/              ← Ug_Roads_UNRA_2012.*
├── rivers/             ← Ug_Rivers-original.*
├── wetlands/           ← Wetlands1994.*
├── lakes/              ← Ug_Lakes.*
├── protected_areas/    ← protected_areas_60.*
├── health_facilities/  ← health_facilities.*
├── commercial_facilities/ ← commercial_facilities.*
└── trading_centres/    ← Ug_Trading_Centres ORIGINAL.*
```

### Setup Script:

To copy shapefiles from Downloads to project (run once):
```bash
python setup_shapefiles.py
```

---

## Basemaps

All 9 basemaps use **QGIS-standard tile servers** (same as QuickMapServices plugin).

### Basemap List:

| # | Basemap | Provider | Type | Status |
|---|---------|----------|------|--------|
| 1 | 🗺️ OpenStreetMap | OSM Foundation | Street map | ✅ Working |
| 2 | 🛰️ Google Satellite | Google | Satellite | ✅ Working |
| 3 | 🛰️ Google Hybrid | Google | Satellite + labels | ✅ Working |
| 4 | 🌍 ESRI Satellite | ESRI | World imagery | ✅ Working |
| 5 | 🌍 ESRI Topographic | ESRI | Topographic | ✅ Working |
| 6 | 🛩️ Bing Aerial | Microsoft | Aerial photography | ✅ Working |
| 7 | 🎨 CartoDB Positron | CartoDB | Clean design | ✅ Working |
| 8 | ⛰️ Stamen Terrain | Stamen | Terrain | ✅ Working |
| 9 | 🏔️ OpenTopoMap | OpenTopoMap | Topographic contours | ✅ Working |

### Uganda Restriction:

Map is restricted to Uganda bounds only:
- **Bounds:** Lat: 0.5° to 4.5°, Lon: 29.5° to 35.0°
- **maxBoundsViscosity:** 1.0 (cannot pan outside)
- **Result:** Users can only view Uganda territory

---

## AHP Weights & Cost Surface

AHP (Analytic Hierarchy Process) weights determine route optimization priorities.

### Current Weights:

| Layer | Weight | Importance | Shapefile Used |
|-------|--------|------------|----------------|
| Protected Areas | 15% | High | `protected_areas_60.shp` |
| Rivers | 15% | High | `Ug_Rivers-original.shp` |
| Wetlands | 15% | High | `Wetlands1994.shp` |
| Roads | 10% | Medium | `Ug_Roads_UNRA_2012.shp` |
| Elevation | 15% | High | DEM + contours |
| Lakes | 15% | High | `Ug_Lakes.shp` |
| Settlements (Schools) | 15% | High | `Ug_Schools ORIGINAL.shp` |

**Total:** 100% (1.0)

### How It Works:

1. User adjusts weights using sliders
2. App generates composite cost surface
3. Higher weight = higher cost to pass through
4. Route optimization avoids high-cost areas
5. Result: Optimal route based on user priorities

### Cost Surface Generation:

File: `app/optimizer/cost_surface.py`

```python
CostSurfaceGenerator().generate_composite_cost_surface(
    bounds=bounds,
    ahp_weights=weights,
    layers_data=layers
)
```

---

## Route Optimization

### Algorithms Available:

1. **Dijkstra** - Standard least-cost path (default)
2. **A*** - Heuristic-guided (faster for large areas)
3. **Both** - Compare results side-by-side

### Optimization Process:

```
1. User sets start, end, waypoints
   ↓
2. User adjusts AHP weights
   ↓
3. App generates cost surface
   ↓
4. Algorithm finds least-cost path
   ↓
5. Route displayed on map
   ↓
6. Towers placed along route
   ↓
7. Statistics calculated
```

### Long-Distance Routing:

For routes > 100km:
- Add waypoints to break into segments
- Recommended: 50-75km segments
- App will suggest waypoint count based on distance

---

## Start/End Points & Waypoints

### Setting Points:

1. **Set Start Point:**
   - Click "Set Start Point" button
   - Click on map
   - Green marker appears
   - Coordinates displayed in sidebar

2. **Set End Point:**
   - Click "Set End Point" button
   - Click on map
   - Red marker appears
   - Coordinates displayed in sidebar

3. **Add Waypoint (Optional):**
   - Click "+ Add Waypoint" button
   - New waypoint added to list
   - Click on map to place
   - Orange marker appears
   - Can add multiple waypoints

### Marker Features:

- ✅ Draggable (click and drag to move)
- ✅ Coordinates update automatically
- ✅ Popup shows exact location
- ✅ Validation (must be within Uganda)

### Waypoint Usage:

Waypoints are used in route optimization:
```
Route = Start → Waypoint 1 → Waypoint 2 → ... → End
```

Each segment is optimized independently using cost surface.

---

## QGIS Routing Workflow

### Overview:

Implements professional QGIS methodology for transmission line routing (optional enhancement).

### Workflow Steps:

1. **Multi-Criteria Evaluation (MCE)**
   - Combine layers using AHP weights
   - Generate composite cost surface

2. **Cost Distance Analysis** (like QGIS r.cost)
   - Calculate accumulated cost from start
   - Track backlink directions (8-directional)
   - Uses Dijkstra's algorithm

3. **Least-Cost Path Extraction** (like QGIS r.drain)
   - Follow backlink directions from end to start
   - Extract optimal path
   - Goes through all waypoints

4. **Corridor Analysis** (like QGIS Buffer)
   - Generate buffer around route
   - Right-of-Way analysis (60m width)
   - Shows impact area

5. **Environmental Impact Assessment** (like QGIS Zonal Stats)
   - Calculate impact for each layer
   - Mean, max, min, sum statistics
   - Total impact score

6. **Route Statistics**
   - Length, cost, elevation
   - Tower count, span lengths
   - Construction feasibility

### Implementation:

File: `app/optimizer/qgis_routing_workflow.py`

```python
workflow = QGISRoutingWorkflow()

# Step 1: Cost distance
accumulated_cost, backlink = workflow.calculate_cost_distance(
    cost_surface, start_points=[start_grid]
)

# Step 2: Extract path
path = workflow.extract_least_cost_path(end_grid)

# Step 3: Corridor
corridor = workflow.generate_route_corridor(path, width_cells=10)

# Step 4: Impact
impact, total = workflow.calculate_environmental_impact(path, layers)

# Step 5: Statistics
stats = workflow.calculate_route_statistics(path, cost_surface, dem)
```

### Status:

- ✅ Module created
- ⚠️ Currently commented out (optional)
- ✅ App works fine without it (uses Dijkstra/A*)
- 🔧 Can enable by uncommenting import in `routes_api.py`

### Example Usage:

File: `app/optimizer/qgis_workflow_example.py`

Shows complete workflow with sample data.

---

## Setup & Installation

### Prerequisites:

- Python 3.8+
- Virtual environment (`.venv`)
- Windows OS

### Installation Steps:

1. **Clone/Download Project:**
   ```bash
   cd d:\transmission_routing_tool
   ```

2. **Activate Virtual Environment:**
   ```bash
   .venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy Shapefiles (One-Time):**
   ```bash
   python setup_shapefiles.py
   ```
   This copies from `C:\Users\PC1\Downloads\shape files\` to `data/`

5. **Initialize Database:**
   ```bash
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

6. **Run Application:**
   ```bash
   python run.py
   ```

7. **Open Browser:**
   ```
   http://localhost:5000
   ```

### First-Time Setup:

1. Login (create account if needed)
2. Check layer checkboxes to enable
3. Select basemap
4. Set start point
5. Set end point
6. (Optional) Add waypoints
7. Adjust AHP weights
8. Click "Optimize Route"

---

## Troubleshooting

### Common Issues:

**1. Layers not showing on map**
- **Fixed!** Added `/api/gis/layers/<layer_name>` endpoint
- **Fixed!** Updated `uganda_gis_loader.py` to load shapefiles (not just GeoJSON)
- **How it works:** Shapefiles are automatically converted to GeoJSON using geopandas
- **Verify:** Check browser console for "Loaded shapefile" messages

**2. ModuleNotFoundError: No module named 'app.optimizer.qgis_routing_workflow'**
- **Fix:** File is optional, import is commented out
- **Status:** App works fine without it

**3. "Please set both Start Point and End Point"**
- **Fix:** Click "Set Start Point" → Click map
- **Fix:** Click "Set End Point" → Click map
- **Note:** Both are required before optimization

**4. Route too long / area too large**
- **Fix:** Add waypoints to break into segments
- **Recommended:** 50-75km per segment
- **App suggests:** Number of waypoints needed

**5. Elevation shows zero values**
- **Fix:** Check DEM files in `data/dem/`
- **Verify:** GeoTIFF files exist and are valid
- **Fallback:** Uses regional estimate if DEM unavailable

**6. Slow performance on large areas**
- **Fix:** Add more waypoints
- **Fix:** Use A* instead of Dijkstra (faster)
- **Fix:** Reduce area bounds

### File Verification:

Check if shapefiles exist:
```bash
python -c "import os; print(os.path.exists('data/schools/Ug_Schools ORIGINAL.shp'))"
```

Should print: `True`

### Logs:

Check terminal output for:
- ✅ `✓ Loaded DEM using multi-tile loader`
- ✅ `✓ Shapefile setup complete!`
- ✅ `Running on http://127.0.0.1:5000`

---

## Quick Reference

### Start Application:
```bash
cd d:\transmission_routing_tool
.venv\Scripts\activate
python run.py
```

### Access Application:
```
http://localhost:5000
```

### Copy Shapefiles:
```bash
python setup_shapefiles.py
```

### Key Files:
- **Main app:** `run.py`
- **Config:** `config.py`
- **Routes:** `app/routes_api.py`
- **Map:** `static/js/map.js`
- **Optimization:** `static/js/optimize.js`
- **Cost surface:** `app/optimizer/cost_surface.py`
- **Dijkstra:** `app/optimizer/dijkstra.py`
- **A*:** `app/optimizer/astar.py`

### Data Folders:
- **Shapefiles:** `data/` (10 subfolders)
- **DEM:** `data/dem/`
- **Cache:** `data/cache/`

---

## Changelog

### Latest Updates:
- ✅ Integrated 10 real Uganda shapefiles from Downloads
- ✅ Added 9 QGIS-standard basemaps
- ✅ Implemented QGIS routing workflow (optional)
- ✅ Preserved start/end/waypoint features
- ✅ Updated AHP weights to use shapefile data
- ✅ Added measurement tools
- ✅ Added layer management
- ✅ Restricted map to Uganda only

---

## Support

### Documentation Files:
- This file: `COMPLETE_GUIDE.md` (you are here)
- Setup script: `setup_shapefiles.py`

### Data Sources:
- Uganda Government Survey (2007)
- UNRA (2012)
- NEMA, UWA, Education, Health, Commerce Departments

### QGIS Equivalents:
- Basemaps: QuickMapServices plugin
- Shapefiles: Add Vector Layer
- Analysis: Processing Toolbox
- Routing: Least Cost Path plugin

---

**Last Updated:** April 18, 2026  
**Version:** 1.0  
**Status:** Production Ready ✅
