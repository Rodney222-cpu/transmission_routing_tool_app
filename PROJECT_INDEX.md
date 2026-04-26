# Transmission Line Routing Tool — Complete Project Index

> **Project:** UETCL 400kV Transmission Line Routing Optimization  
> **Case Study:** Olwiyo (Uganda) → South Sudan Border Interconnection  
> **Generated:** Auto-indexed codebase reference

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Directory Structure](#2-directory-structure)
3. [File Index by Category](#3-file-index-by-category)
   - [3.1 Application Core](#31-application-core)
   - [3.2 Optimizer Engine](#32-optimizer-engine)
   - [3.3 Services Layer](#33-services-layer)
   - [3.4 Web Frontend](#34-web-frontend)
   - [3.5 Data & Assets](#35-data--assets)
   - [3.6 Scripts & Utilities](#36-scripts--utilities)
   - [3.7 Documentation](#37-documentation)
4. [Module Dependency Map](#4-module-dependency-map)
5. [API Endpoint Reference](#5-api-endpoint-reference)
6. [Database Schema](#6-database-schema)
7. [GIS Data Layer Inventory](#7-gis-data-layer-inventory)
8. [Configuration Reference](#8-configuration-reference)
9. [Quick Navigation](#9-quick-navigation)

---

## 1. Project Overview

A Flask-based web application that optimizes transmission line routing using:
- **AHP** (Analytic Hierarchy Process) for multi-criteria weighting
- **Dijkstra** & **A\*** algorithms for least-cost pathfinding
- **QGIS-style** cost surface generation with 5-band color ramps
- **Uganda-specific** GIS data integration (shapefiles, GeoTIFFs)
- **Engineering validation** for 400kV lattice tower constraints

### Key Technologies
| Layer | Stack |
|-------|-------|
| Backend | Python 3, Flask, SQLAlchemy, Flask-Login |
| Algorithms | NumPy, SciPy, custom Dijkstra/A* implementations |
| GIS | rasterio (optional), Shapely, pyproj, GeoJSON/Shapefile I/O |
| Frontend | Leaflet.js, vanilla JavaScript, Chart.js, HTML/CSS |
| Database | SQLite (default), configurable to PostgreSQL |

---

## 2. Directory Structure

```
transmission_routing_tool/
├── app/                          # Flask application package
│   ├── __init__.py               # App factory, extensions init
│   ├── auth.py                   # Authentication blueprint (login/register/logout)
│   ├── models.py                 # SQLAlchemy database models
│   ├── views.py                  # Main view routes (dashboard, index)
│   ├── routes_api.py             # Core REST API (projects, routes, optimization)
│   ├── routes_qgis_api.py        # QGIS-style cost surface API endpoints
│   ├── optimizer/                # Routing algorithms
│   │   ├── __init__.py
│   │   ├── astar.py              # A* pathfinder with weighted heuristic
│   │   ├── cost_surface.py       # AHP-based composite cost surface generator
│   │   ├── dijkstra.py           # Dijkstra LCP with LOS smoothing
│   │   ├── engineering_validation.py  # 400kV tower/span/slope validation
│   │   ├── qgis_cost_surface.py  # QGIS-style raster analysis pipeline
│   │   ├── qgis_routing_workflow.py   # QGIS integration workflow
│   │   └── qgis_workflow_example.py   # Example usage script
│   └── services/                 # Data loading & helper services
│       ├── __init__.py
│       ├── corridor_restriction.py    # 60m corridor polygon generation
│       ├── dem_loader.py         # Multi-tile DEM loader
│       ├── elevation_sampling.py # Elevation extraction & chart downsampling
│       ├── gis_data_loader.py    # Real GIS raster/vector loader
│       └── uganda_gis_loader.py  # Uganda shapefile → GeoJSON converter
├── data/                         # GIS data folders (shapefiles, rasters)
│   ├── airports/
│   ├── cache/
│   ├── commercial_facilities/
│   ├── dem/                      # SRTM elevation GeoTIFFs
│   ├── education/
│   ├── elevation/                # Contour lines
│   ├── forests/
│   ├── health_facilities/
│   ├── lakes/
│   ├── land_use/
│   ├── landcover/                # ESA WorldCover GeoTIFFs
│   ├── power_infrastructure/
│   ├── protected_areas/          # NEMA/NFA/UWA data
│   ├── rivers/
│   ├── roads/                    # UNRA road network
│   ├── schools/
│   ├── settlements/
│   ├── trading_centres/
│   ├── uganda_districts/         # 136 district boundaries
│   ├── waterbodies/
│   └── wetlands/
├── instance/                     # SQLite database, uploaded files
├── scripts/                      # Helper scripts
├── static/                       # Web assets
│   ├── css/
│   │   └── style.css             # Dashboard styling
│   ├── images/                   # UETCL logo, backgrounds
│   ├── js/
│   │   ├── layer_manager.js      # Checkbox-based layer controls
│   │   ├── map.js                # Leaflet map init, GIS layer loading
│   │   ├── optimize.js           # Route optimization UI logic
│   │   └── qgis_tools.js         # QGIS-style toolbar, attribute table
│   └── vendor/                   # chart.umd.min.js (local vendored)
├── templates/                    # Jinja2 HTML templates
│   ├── dashboard.html            # Main map interface
│   ├── login.html                # Authentication page
│   └── register.html             # User registration
├── test_output/                  # Generated test rasters/shapefiles
├── uploads/                      # User-uploaded files
├── add_metadata_column.py        # DB migration utility
├── config.py                     # Flask configuration classes
├── convert_shapefiles_to_geojson.py  # Batch conversion script
├── create_placeholder_images.py  # Generate placeholder assets
├── create_simple_images.py       # Simple image generator
├── download_dem_usgs.py          # USGS DEM downloader
├── download_srtm_direct.py       # SRTM direct download
├── download_srtm_elevation.py    # SRTM elevation fetcher
├── download_srtm_uganda.py       # Uganda SRTM downloader
├── download_uganda_data.py       # Batch Uganda data downloader
├── open_download_pages.py        # Open browser download pages
├── run.py                        # Application entry point
├── setup_shapefiles.py           # Shapefile setup utility
├── test_checkbox_layers.py       # Layer checkbox test
├── test_cost_surface_complete.py # Full cost surface test
├── test_layers.py                # GIS layer loading test
├── test_qgis_cost_surface.py     # QGIS cost surface test
├── test_roads.py                 # Road layer test
├── verify_roads.py               # Road data verification
├── verify_shapefile_mapping.py   # Shapefile mapping verification
├── COLLABORATOR_GUIDE.md         # Team collaboration guide
├── COMPLETE_GUIDE.md             # Full developer guide
├── COST_SURFACE_IMPLEMENTATION.md # Cost surface technical spec
├── QGIS_COST_SURFACE_GUIDE.md    # QGIS integration guide
├── README.md                     # User-facing documentation
├── requirements.txt              # Python dependencies
└── .gitignore / .gitattributes   # Git configuration
```

---

## 3. File Index by Category

### 3.1 Application Core

| File | Lines | Purpose | Key Classes/Functions |
|------|-------|---------|----------------------|
| `run.py` | ~40 | Entry point, dev server | `create_app()`, directory setup |
| `config.py` | ~300 | Configuration classes | `Config`, `DevelopmentConfig`, `ProductionConfig` |
| `app/__init__.py` | ~50 | Flask app factory | `create_app()`, blueprint registration |
| `app/models.py` | ~180 | Database ORM | `User`, `Project`, `Route`, `CostSurface` |
| `app/auth.py` | ~140 | Authentication routes | `register()`, `login()`, `logout()` |
| `app/views.py` | ~30 | Page routes | `index()`, `dashboard()` |

### 3.2 Optimizer Engine

| File | Lines | Purpose | Key Classes/Functions |
|------|-------|---------|----------------------|
| `app/optimizer/cost_surface.py` | ~420 | AHP cost surface generation | `CostSurfaceGenerator.generate_composite_cost_surface()` |
| `app/optimizer/dijkstra.py` | ~380 | Dijkstra LCP pathfinder | `LeastCostPathFinder.find_path()`, `smooth_path_los()` |
| `app/optimizer/astar.py` | ~320 | Weighted A* pathfinder | `AStarPathFinder.find_path()` (heuristic_weight=2.0) |
| `app/optimizer/engineering_validation.py` | ~480 | Engineering rules validator | `EngineeringValidator.validate_route()`, `generate_tower_positions()` |
| `app/optimizer/qgis_cost_surface.py` | — | QGIS raster analysis | `QGISStyleCostSurfaceAnalyzer.run_full_pipeline()` |
| `app/optimizer/qgis_routing_workflow.py` | — | QGIS integration | Workflow orchestration |

### 3.3 Services Layer

| File | Lines | Purpose | Key Classes/Functions |
|------|-------|---------|----------------------|
| `app/services/gis_data_loader.py` | ~250 | Load real GIS rasters/vectors | `load_layers_for_bounds()`, `rasterize_geojson_presence()` |
| `app/services/uganda_gis_loader.py` | ~320 | Shapefile → GeoJSON for Leaflet | `UgandaGISLoader.load_layer_geojson()`, `_load_shapefile_as_geojson()` |
| `app/services/dem_loader.py` | — | Multi-tile DEM loading | `MultiTileDEMLoader.load_dem_for_bounds()` |
| `app/services/elevation_sampling.py` | — | Elevation extraction | `sample_elevations_m()`, `downsample_for_chart()` |
| `app/services/corridor_restriction.py` | — | Corridor polygon generation | `CorridorRestrictionService.generate_corridor_geojson()` |

### 3.4 Web Frontend

| File | Lines | Purpose | Key Functions |
|------|-------|---------|---------------|
| `templates/dashboard.html` | ~400 | Main map UI | Leaflet map, sidebar controls, layer checkboxes |
| `templates/login.html` | — | Login page | Form submission |
| `templates/register.html` | — | Registration page | Account creation |
| `static/js/map.js` | ~650 | Map initialization & layer loading | `initMap()`, `loadGISLayer()`, `setStartPoint()`, `displayRoute()` |
| `static/js/optimize.js` | ~900 | Optimization UI & API calls | `optimizeRoute()`, `generateCostSurface()`, `displayResults()` |
| `static/js/qgis_tools.js` | — | QGIS toolbar, attribute table | `initQGISTools()`, `showAttributeTable()` |
| `static/js/layer_manager.js` | — | Checkbox layer controls | Layer toggle management |
| `static/css/style.css` | — | All UI styling | Dashboard layout, responsive design |

### 3.5 Data & Assets

| Directory | Contents | Format | Source |
|-----------|----------|--------|--------|
| `data/dem/` | Elevation rasters | GeoTIFF (.tif) | USGS SRTM 30m |
| `data/landcover/` | Land cover rasters | GeoTIFF (.tif) | ESA WorldCover 10m |
| `data/land_use/` | Land use vectors | Shapefile (.shp) | OpenStreetMap / local |
| `data/settlements/` | Settlement points | GeoJSON / Shapefile | OpenStreetMap |
| `data/roads/` | Road network | Shapefile (.shp) | UNRA 2012 / OSM |
| `data/rivers/` | River lines | Shapefile (.shp) | Local GIS |
| `data/wetlands/` | Wetland polygons | Shapefile (.shp) | 1994 wetland survey |
| `data/lakes/` | Lake polygons | Shapefile (.shp) | Local GIS |
| `data/protected_areas/` | Park/reserve boundaries | Shapefile (.shp) | NEMA/NFA/UWA |
| `data/forests/` | Forest polygons | Shapefile (.shp) | NFA |
| `data/schools/` | School locations | Shapefile (.shp) | Uganda Ministry of Education |
| `data/health_facilities/` | Hospital/clinic points | Shapefile (.shp) | Ministry of Health |
| `data/uganda_districts/` | 136 district boundaries | Shapefile (.shp) | UBOS 2019 |
| `data/airports/` | Airport locations | Shapefile (.shp) | UCAA |
| `data/elevation/` | Contour lines | Shapefile (.shp) | Generated from DEM |
| `data/commercial_facilities/` | Commercial areas | Shapefile (.shp) | Local GIS |
| `data/trading_centres/` | Trading center points | Shapefile (.shp) | Local GIS |
| `data/power_infrastructure/` | Substations, existing lines | Shapefile (.shp) | UETCL |

### 3.6 Scripts & Utilities

| Script | Purpose |
|--------|---------|
| `download_dem_usgs.py` | Download SRTM DEM tiles from USGS EarthExplorer |
| `download_srtm_uganda.py` | Batch download Uganda SRTM tiles |
| `download_uganda_data.py` | Fetch all Uganda GIS datasets |
| `convert_shapefiles_to_geojson.py` | Convert .shp → .geojson for web display |
| `setup_shapefiles.py` | Validate and organize shapefile folders |
| `verify_roads.py` | Check road layer integrity |
| `verify_shapefile_mapping.py` | Verify shapefile-to-layer mappings |
| `add_metadata_column.py` | Add metadata columns to existing database |
| `create_placeholder_images.py` | Generate placeholder UI images |
| `test_*.py` (6 files) | Unit/integration tests for layers, cost surface, routing |

### 3.7 Documentation

| File | Audience | Contents |
|------|----------|----------|
| `README.md` | End users | Installation, usage guide, troubleshooting |
| `COMPLETE_GUIDE.md` | Developers | Full architecture, file explanations, data flow |
| `COLLABORATOR_GUIDE.md` | Team members | Git workflow, coding standards, contribution guide |
| `COST_SURFACE_IMPLEMENTATION.md` | GIS developers | Cost surface math, AHP weights, reclassification |
| `QGIS_COST_SURFACE_GUIDE.md` | QGIS users | QGIS integration steps, layer styling |
| `PROJECT_INDEX.md` | Everyone | This file — complete codebase index |

---

## 4. Module Dependency Map

```
run.py
  └── app/__init__.py
        ├── app/models.py  ←→  instance/transmission_routing.db (SQLite)
        ├── app/auth.py    ←→  app/models.py
        ├── app/views.py   ←→  templates/*.html
        ├── app/routes_api.py
        │     ├── app/optimizer/cost_surface.py
        │     ├── app/optimizer/dijkstra.py
        │     ├── app/optimizer/astar.py
        │     ├── app/optimizer/engineering_validation.py
        │     ├── app/services/gis_data_loader.py
        │     ├── app/services/uganda_gis_loader.py
        │     ├── app/services/elevation_sampling.py
        │     └── app/services/corridor_restriction.py
        ├── app/routes_qgis_api.py
        │     └── app/optimizer/qgis_cost_surface.py
        └── config.py

Frontend:
dashboard.html
  ├── static/js/map.js
  ├── static/js/optimize.js
  ├── static/js/qgis_tools.js
  ├── static/js/layer_manager.js
  └── static/css/style.css

Data Flow (Optimization):
User clicks "Optimize" → optimize.js POST /api/projects → routes_api.py
  → gis_data_loader.py (load real layers OR create demo layers)
  → cost_surface.py (generate composite cost surface with AHP weights)
  → dijkstra.py OR astar.py (find least-cost path)
  → engineering_validation.py (validate spans, slopes, generate towers)
  → elevation_sampling.py (sample elevations along route)
  → routes_api.py returns GeoJSON + metrics + cost breakdown
  → optimize.js displays route on map + charts
```

---

## 5. API Endpoint Reference

### 5.1 Project Management (`/api`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/projects` | Yes | List user's projects |
| POST | `/api/projects` | Yes | Create new project |
| POST | `/api/projects/<id>/optimize` | Yes | Run route optimization |
| GET | `/api/projects/<id>/routes` | Yes | Get all routes for project |
| POST | `/api/projects/<id>/generate-towers` | Yes | Generate tower positions |
| GET | `/api/projects/<id>/cost-surface-image` | Yes | Get cost surface PNG |

### 5.2 Route Operations (`/api`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/routes/<id>/export?format=geojson` | Yes | Export as GeoJSON |
| GET | `/api/routes/<id>/export?format=xyz` | Yes | Export as XYZ (UTM 36N) |
| GET | `/api/routes/<id>/corridor` | Yes | Get 60m corridor polygon |

### 5.3 GIS Data (`/api`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/gis/layers/<name>` | Yes | Load layer as GeoJSON (bounds query) |
| GET | `/api/layers` | Yes | Get rasterized layer grids for display |
| POST | `/api/cost-surface/generate` | Yes | Generate QGIS-style cost surface PNG |

### 5.4 QGIS Integration (`/api/qgis`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/generate-cost-surface` | No | Spec-compliant cost surface pipeline |
| POST | `/api/qgis/generate-cost-surface` | Yes | Authenticated alias |
| GET | `/api/qgis/layer-info/<name>` | Yes | Get layer metadata |

### 5.5 Authentication (`/auth`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET/POST | `/auth/register` | No | Create account |
| GET/POST | `/auth/login` | No | Log in |
| GET/POST | `/auth/logout` | Yes | Log out |
| GET | `/auth/user` | Yes | Get current user info |

---

## 6. Database Schema

### 6.1 Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    users    │       │   projects  │       │    routes   │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │──┐    │ id (PK)     │──┐    │ id (PK)     │
│ username    │  │    │ name        │  │    │ project_id  │
│ email       │  └───>│ user_id (FK)│  └───>│ geometry    │
│ password_hash│      │ start_lat   │       │ total_length│
│ organization │      │ start_lon   │       │ total_cost  │
│ role        │       │ end_lat     │       │ is_valid    │
│ created_at  │       │ end_lon     │       │ algorithm   │
└─────────────┘       │ ahp_weights │       │ created_at  │
                      │ status      │       └─────────────┘
                      │ created_at  │
                      └─────────────┘
                            │
                            │ 1:N
                            ▼
                      ┌─────────────┐
                      │ cost_surfaces│
                      ├─────────────┤
                      │ id (PK)     │
                      │ project_id  │
                      │ file_path   │
                      │ resolution  │
                      │ bounds      │
                      │ layer_weights│
                      └─────────────┘
```

### 6.2 Table Details

**`users`**
- Primary key: `id` (Integer, auto-increment)
- Indexed: `username`, `email`
- Passwords stored with Werkzeug `generate_password_hash()`
- Roles: `user`, `admin`, `engineer`

**`projects`**
- Stores start/end coordinates, AHP weights (JSON), waypoints (JSON metadata)
- Status: `draft`, `processing`, `completed`, `failed`
- One-to-many with `routes` and `cost_surfaces`

**`routes`**
- Geometry stored as GeoJSON string
- Validation errors stored as JSON array
- Supports algorithm tracking (`dijkstra` / `astar`)

**`cost_surfaces`**
- File path to generated GeoTIFF or NumPy array
- Bounding box stored as JSON
- Resolution in meters per pixel

---

## 7. GIS Data Layer Inventory

### 7.1 Supported Layers (Checkbox-Controlled)

| Layer Name | Checkbox ID | Data Folder | Geometry Type | Default Weight |
|------------|-------------|-------------|---------------|----------------|
| Uganda Districts | `showUgandaDistricts` | `uganda_districts/` | Polygon | — |
| Protected Areas | `showProtectedAreas` | `protected_areas/` | Polygon | 0.15 |
| Rivers | `showRivers` | `rivers/` | LineString | 0.15 |
| Wetlands | `showWetlands` | `wetlands/` | Polygon | 0.10 |
| Lakes | `showLakes` | `lakes/` | Polygon | 0.10 |
| Roads | `showRoads` | `roads/` | LineString | 0.10 |
| Elevation (Contours) | `showElevation` | `elevation/` | LineString | 0.15 |
| Settlements (Schools) | `showSettlements` | `schools/` | Point | 0.15 |
| Hospitals | `showHospitals` | `health_facilities/` | Point | — |
| Commercial Areas | `showCommercial` | `commercial_facilities/` | Polygon | — |
| Land Use | `showLandUse` | `land_use/` | Polygon | 0.10 |

### 7.2 Cost Surface Reclassification Rules

| Layer | Reclassification Function | Logic |
|-------|--------------------------|-------|
| `protected_areas` | `reclassify_protected_areas` | Inside = high cost (avoid) |
| `rivers`, `lakes` | `reclassify_water_distance` | Proximity-based, crossing penalty |
| `wetlands` | `reclassify_wetlands` | Inside = high cost |
| `land_use` | `reclassify_land_use` | Per-class cost (built-up > forest > grassland) |
| `elevation` | `reclassify_elevation_slope` | Slope-derived cost from DEM |
| `settlements` | `reclassify_water_distance` | Proximity-based (nearer = higher cost) |
| `roads` | `reclassify_water_distance` | Proximity-based (nearer = lower cost, synergy) |

### 7.3 Color Ramp (QGIS-Style 5-Band)

| Cost Range | Color | RGB | Meaning |
|------------|-------|-----|---------|
| 156–220 | Dark Green | (34, 139, 34) | Very low cost |
| 220–284 | Lime Green | (124, 205, 50) | Low cost |
| 284–348 | Yellow | (255, 230, 0) | Moderate cost |
| 348–412 | Orange | (255, 140, 0) | High cost |
| 412–476 | Red | (220, 20, 20) | Very high cost |

---

## 8. Configuration Reference

### 8.1 Engineering Constraints (400kV Lattice Towers)

| Parameter | Value | Source |
|-----------|-------|--------|
| Voltage Level | 400 kV | UETCL specification |
| Tower Type | Steel lattice | Standard for 400kV |
| Min Span (flat) | 300 m | Configurable |
| Max Span (flat) | 450 m | Configurable |
| Typical Span | 375 m | Midpoint of range |
| Min Span (difficult) | 250 m | Steep terrain |
| Max Span (difficult) | 300 m | Steep terrain |
| Corridor Width | 60 m | 10m RoW + 25m wayleave × 2 |
| Max Slope | 30° | Engineering limit |
| Min Ground Clearance | 7.6 m | 400kV safety standard |

### 8.2 Default AHP Weights (Backend)

| Criterion | Weight | Rationale |
|-----------|--------|-----------|
| Settlements | 0.200 | People/proximity priority |
| Protected Areas | 0.289 | Habitat + fauna combined |
| Vegetation | 0.156 | Forest preservation |
| Land Use | 0.133 | Agricultural impact |
| Water | 0.089 | Wetland/riverine habitat |
| Topography | 0.067 | Landscape alteration |
| Cultural Heritage | 0.044 | Sacred sites |
| Public Infrastructure | 0.022 | Schools, hospitals |

### 8.3 Cost Estimation Constants (USD)

| Item | Flat Terrain | Difficult Terrain |
|------|-------------|-------------------|
| Tower cost | $45,000 | $65,000 |
| Foundation | $15,000 | $40,000 |
| Conductor/km | $85,000 | $85,000 |
| Installation/km | $120,000 | $120,000 |
| RoW acquisition/km | $50,000 | $50,000 |
| Engineering | 8% of construction | 8% |
| Contingency | 15% of construction | 15% |

### 8.4 Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `FLASK_CONFIG` | Config class name | `development` |
| `SECRET_KEY` | Flask session security | `dev-secret-key-change-in-production` |
| `DATABASE_URL` | SQLAlchemy URI | `sqlite:///transmission_routing.db` |
| `MAPTILER_API_KEY` | MapTiler basemap access | (empty) |
| `THUNDERFOREST_API_KEY` | Thunderforest basemap access | (empty) |

---

## 9. Quick Navigation

### Find Code By Task

| Task | File(s) |
|------|---------|
| **Add a new map layer** | `static/js/map.js` (create function), `templates/dashboard.html` (checkbox), `app/routes_api.py` (`get_gis_layer`), `config.py` (folder constant) |
| **Change AHP weight defaults** | `config.py` (`DEFAULT_AHP_WEIGHTS`), `static/js/optimize.js` (`ahpWeights`) |
| **Modify tower spacing rules** | `config.py` (`MIN_TOWER_SPAN`, `MAX_TOWER_SPAN`), `app/optimizer/engineering_validation.py` |
| **Adjust cost surface colors** | `app/routes_api.py` (`generate_cost_surface` → `band_defs`), `app/routes_api.py` (`get_cost_surface_image`) |
| **Add new export format** | `app/routes_api.py` (`export_route`) |
| **Change algorithm behavior** | `app/optimizer/dijkstra.py` (LOS smoothing params), `app/optimizer/astar.py` (`DEFAULT_HEURISTIC_WEIGHT`) |
| **Update UI styling** | `static/css/style.css`, `templates/dashboard.html` |
| **Add database field** | `app/models.py` (add column), run `db.create_all()` |
| **Modify cost surface generation** | `app/optimizer/cost_surface.py` (layer processors), `app/optimizer/qgis_cost_surface.py` (reclassification) |
| **Add authentication provider** | `app/auth.py` (modify login/register), `app/models.py` (add fields) |

### Common Debugging Entry Points

| Symptom | Investigation File |
|---------|-------------------|
| Route not found | `app/optimizer/dijkstra.py` / `astar.py` — check `cost_surface` values |
| Layer not loading | `app/services/uganda_gis_loader.py` — check `_load_local_geojson()` |
| Weights don't sum | `static/js/optimize.js` — `updateWeightSum()` |
| Memory error | `app/routes_api.py` — `optimize_route()` resolution adjustment logic |
| Towers too close/far | `app/optimizer/engineering_validation.py` — `generate_tower_positions()` |
| Cost surface all same color | `app/optimizer/cost_surface.py` — check `_normalize_cost_surface()` |
| DEM shows 0 elevation | `app/services/elevation_sampling.py` — fallback to Uganda defaults |

---

*End of Project Index*

