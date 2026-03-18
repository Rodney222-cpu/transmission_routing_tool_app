# Transmission Line Routing Optimization Tool

A Python Flask web application for automated transmission line routing optimization, developed for the Uganda Electricity Transmission Company Limited (UETCL). This tool is based on the **Olwiyo (Uganda) – South Sudan 400kV Interconnection** case study.

## 🎯 Project Overview

This tool automates the manual and error-prone process of transmission line routing by using geospatial and topographical data to identify optimal paths that balance technical, economic, and environmental factors.

### Key Features

- **Automated Route Optimization**: Uses Dijkstra's algorithm for Least-Cost Path (LCP) analysis
- **Multi-Criteria Analysis**: Implements Analytic Hierarchy Process (AHP) for cost surface generation
- **Engineering Validation**: Validates routes against 400kV lattice tower constraints
- **Interactive Map Interface**: Leaflet.js-based visualization with layer controls
- **Corridor Management**: 60m corridor width validation (10m RoW + 25m Wayleave each side)
- **GIS Data Integration**: Supports DEM, land use, settlements, protected areas, and roads

## 📋 Case Study Specifications

- **Voltage Level**: 400 kV
- **Tower Type**: Steel lattice towers
- **Corridor Width**: 60 meters (10m Right of Way + 25m Wayleave on each side)
- **Route**: Olwiyo Substation (Uganda) to South Sudan Border (Elegu)
- **Data Sources**: USGS (DEM), ESA WorldCover (Land Use), NEMA/NFA/UWA (Protected Areas)

## 🏗️ Architecture

### Backend Components

1. **Cost Surface Generator** (`app/optimizer/cost_surface.py`)
   - Implements AHP weighting methodology
   - Processes multiple GIS layers (topography, land use, settlements, protected areas, roads)
   - Generates composite cost surfaces

2. **Dijkstra's Algorithm** (`app/optimizer/dijkstra.py`)
   - Finds Least-Cost Path on cost surface
   - Supports 8-directional movement
   - Path simplification using Douglas-Peucker algorithm

3. **Engineering Validator** (`app/optimizer/engineering_validation.py`)
   - Validates tower spans (200-450m for 400kV)
   - Checks slope constraints (max 30°)
   - Estimates construction costs

4. **Corridor Service** (`app/services/corridor_restriction.py`)
   - Manages 60m corridor width
   - Calculates land acquisition requirements
   - Generates corridor polygons

### Frontend Components

- **Interactive Map** (Leaflet.js): Uganda-focused map with route visualization
- **AHP Weight Controls**: Adjustable sliders for multi-criteria optimization
- **Real-time Results**: Route metrics, validation errors, and cost estimates

## 🚀 Installation

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup

1. **Clone the repository**
```bash
cd transmission_routing_tool
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## 🌍 Using Real Uganda GIS Data (Recommended)

This project can run with **demo/synthetic layers**, but you’ll get much better results with **real GIS data**.

### Data folder layout

Place your datasets here:

```
transmission_routing_tool/
└── data/
    ├── dem/                # DEM GeoTIFF (SRTM)
    │   └── *.tif
    ├── landcover/          # Landcover GeoTIFF (ESA WorldCover)
    │   └── *.tif
    ├── settlements/        # Settlements/buildings (GeoJSON recommended)
    │   └── *.geojson
    ├── protected_areas/    # Protected areas (GeoJSON recommended)
    │   └── *.geojson
    └── roads/              # Roads (GeoJSON recommended)
        └── *.geojson
```

### Notes (Windows)
- **Rasters (DEM/landcover)**: require `rasterio` to read GeoTIFFs. If `rasterio` isn’t installed, the app falls back to demo data automatically.
- **Vectors (roads/settlements/protected areas)**: this build reads **GeoJSON** without extra GIS libraries. (Shapefiles can be converted to GeoJSON in QGIS.)

### Quick start steps
- Download OSM layers (roads/buildings/landuse) from Geofabrik or HOT Export Tool, and export to **GeoJSON** for the folders above.
- Download DEM tiles (SRTM 30m) from USGS EarthExplorer as **GeoTIFF** and place in `data/dem/`.
- Restart the Flask server and optimize a route. The API response includes `metadata.data_source` = `real` or `demo`.

4. **Configure environment variables**
```bash
# Create .env file
cp .env.example .env
# Edit .env with your settings
```

5. **Initialize database**
```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

6. **Run the application**
```bash
python run.py
```

7. **Access the application**
Open your browser and navigate to: `http://localhost:5000`

## 📊 Usage

### 1. Register/Login
- Create an account or login with existing credentials
- Organization field can be set to "UETCL"

### 2. Set Route Points
- No points are preset. Click **"Set Start Point"**, then click the map; then **"Set End Point"**, then click the map.
- Optionally add **waypoints** with **"+ Add Waypoint"** and click the map to place each one.
- Markers are draggable. You must set both start and end before optimizing.

### 3. Adjust AHP Weights
- Modify weights for different cost factors:
  - **Topography** (0.25): Slope and elevation
  - **Land Use** (0.30): Agricultural, built-up, wetlands
  - **Settlements** (0.20): Proximity to populated areas
  - **Protected Areas** (0.15): NEMA/NFA/UWA zones
  - **Roads** (0.10): Existing infrastructure
- Weights must sum to 1.0

### 4. (Optional) Turn on map layers
- In the map controls (top right), tick **DEM/Topography**, **Land Use**, **Settlements**, **Protected Areas**, or **Roads** to display them. All start unticked.

### 5. Optimize Route
- Choose **Dijkstra (LCP)** or **A* (Pathfinder)** in the Optimizer section. Optionally check **"Compare both algorithms"** to run both.
- Click **"🚀 Optimize Route"**. Processing creates the project, builds the cost surface, and runs the selected pathfinder.
- View the optimized route on the map and (after optimization) use **"🗼 Generate Towers"** for tower positions.

### 6. Review Results
- Route length, estimated towers, algorithm used, and cost breakdown
- Engineering validation errors/warnings
- **Export GeoJSON** or **Export XYZ (E/N/Elev)** for simulation
- View 60m corridor polygon

## 🗂️ Project Structure

```
transmission_routing_tool/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # Database models
│   ├── routes_api.py            # REST API endpoints
│   ├── auth.py                  # Authentication routes
│   ├── views.py                 # Main view routes
│   ├── optimizer/
│   │   ├── cost_surface.py      # Cost surface generation
│   │   ├── dijkstra.py          # LCP (Dijkstra) algorithm
│   │   ├── astar.py             # A* pathfinder (for comparison)
│   │   └── engineering_validation.py  # Route validation
│   └── services/
│       └── corridor_restriction.py    # Corridor management
├── templates/
│   ├── login.html
│   ├── register.html
│   └── dashboard.html
├── static/
│   ├── js/
│   │   ├── map.js               # Leaflet map initialization
│   │   ├── optimize.js          # Optimization logic
│   │   └── layers.js            # GIS layer management
│   ├── css/
│   │   └── style.css
│   └── images/                  # UETCL logo & login background (see IMAGES_README.txt)
├── config.py                    # Configuration settings
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
└── README.md
```

## 🔧 API Endpoints

- `POST /api/projects` - Create new project (start, end, waypoints in body)
- `POST /api/projects/<id>/optimize` - Optimize route (body: `algorithm`: `dijkstra`|`astar`, optional `compare`: true)
- `GET /api/projects/<id>/routes` - Get project routes
- `GET /api/routes/<id>/export` - Export route; `?format=geojson` or `?format=xyz` (Eastings, Northings, elevation)
- `GET /api/routes/<id>/corridor` - Get corridor polygon
- `GET /api/layers` - Get layer GeoJSON for map display; query: `min_lon`, `min_lat`, `max_lon`, `max_lat`, `layers`

## 📝 Configuration

Key configuration parameters in `config.py`:

- **CRS**: `MAP_CRS = EPSG:4326` (WGS 84); `PREFERRED_PROJECTED_CRS = EPSG:21096` (UTM 36N for Uganda/XYZ export)
- **Corridor Specifications**: RoW (10m), Wayleave (25m each side)
- **Tower Constraints**: Min span (200m), Max span (450m), Typical span (350m)
- **AHP Default Weights**: Customizable for different priorities
- **Cost Factors**: Uganda-specific land use and slope costs

## 🧪 Testing

To test the application with demo data:

1. The system generates synthetic GIS layers for testing
2. In production, replace with actual data from:
   - USGS SRTM 30m DEM
   - ESA WorldCover 10m land cover
   - NEMA/NFA/UWA protected areas
   - OpenStreetMap settlements and roads

## 📄 License

This project is developed for UETCL transmission line planning purposes.

## 👥 Contributors

Developed for the Uganda Electricity Transmission Company Limited (UETCL) - Olwiyo-South Sudan 400kV Interconnection Project.

## 🙏 Acknowledgments

- USGS for DEM data
- ESA for WorldCover land use data
- NEMA/NFA/UWA for Uganda environmental data
- OpenStreetMap contributors

---

## 🔄 Upgrades (Software Tool Modifications)

The following upgrades are implemented for user control, algorithm comparison, branding, coordinate clarity, and layer visibility:

### 1. User-defined route points (no presets)
- **Start, way and end points** are not preset in the backend or frontend.
- Users must set **Start Point** and **End Point** on the map (click the sidebar buttons, then click the map). **Waypoints** are optional and added the same way.
- Project name is user-entered (no default). Optimize is disabled until both start and end are set.

### 2. Pathfinder: A* vs Dijkstra
- **A* (Pathfinder)** is available alongside the existing **Dijkstra** LCP optimizer, both on the same cost surface.
- In the dashboard **Optimizer** section you can choose **Dijkstra (LCP)** or **A* (Pathfinder)**.
- Optional **“Compare both algorithms”** runs Dijkstra and A* and returns cost/length for both so you can verify results against your weights and buffers.

### 3. Login: UETCL background and logo
- Login page uses a **custom background image** (`static/images/uetcl_background.jpg`) with a UETCL-style gradient overlay.
- **Company logo** is shown from `static/images/uetcl_logo.png`. If the file is missing, a “UETCL” text fallback is displayed.
- Add your own `uetcl_background.jpg` and `uetcl_logo.png` in `static/images/` (see `static/images/IMAGES_README.txt`).

### 4. Coordinate reference system (CRS) and XYZ for simulation
- **CRS is stated** in the app: **WGS 84 (EPSG:4326)** for the map and GeoJSON.
- **XYZ format** (Eastings, Northings, elevation) is supported for simulation: export uses **UTM 36N (EPSG:21096)** for Uganda when `pyproj` is installed.
- Dashboard shows: *“Coordinate reference system: WGS 84 (EPSG:4326). Export available in Eastings, Northings, elevation (UTM 36N / EPSG:21096) for simulation.”*
- **Export:** “Export GeoJSON” (lon/lat) and **“Export XYZ (E/N/Elev)”** (Eastings, Northings, elevation) in the Results section.

### 5. Layers displayed on the map
- **DEM, Land Use, Settlements, Protected Areas, and Roads** are loaded from the API and drawn on the map when the user turns them on.
- Layer data is requested for the current map bounds; data sources align with optimization (USGS DEM, ESA WorldCover, NEMA/NFA/UWA, OSM). Demo/synthetic data is used when real files are not present.

### 6. Layers start unticked
- All layer checkboxes (DEM/Topography, Land Use, Settlements, Protected Areas, Roads) **start unchecked**.
- Users choose which layers to display; none are preset as on.
