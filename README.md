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
- Default points are pre-configured for Olwiyo-South Sudan line
- Click "Set Start Point" or "Set End Point" to customize
- Markers are draggable on the map

### 3. Adjust AHP Weights
- Modify weights for different cost factors:
  - **Topography** (0.25): Slope and elevation
  - **Land Use** (0.30): Agricultural, built-up, wetlands
  - **Settlements** (0.20): Proximity to populated areas
  - **Protected Areas** (0.15): NEMA/NFA/UWA zones
  - **Roads** (0.10): Existing infrastructure
- Weights must sum to 1.0

### 4. Optimize Route
- Click "🚀 Optimize Route" button
- Wait for processing (creates project, generates cost surface, runs Dijkstra)
- View optimized route on map with tower positions

### 5. Review Results
- Route length and estimated towers
- Construction cost estimates
- Engineering validation errors/warnings
- Export route as GeoJSON
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
│   │   ├── dijkstra.py          # LCP algorithm
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
│   └── css/
│       └── style.css
├── config.py                    # Configuration settings
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
└── README.md
```

## 🔧 API Endpoints

- `POST /api/projects` - Create new project
- `POST /api/projects/<id>/optimize` - Optimize route
- `GET /api/projects/<id>/routes` - Get project routes
- `GET /api/routes/<id>/export` - Export route (GeoJSON/Shapefile)
- `GET /api/routes/<id>/corridor` - Get corridor polygon

## 📝 Configuration

Key configuration parameters in `config.py`:

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

