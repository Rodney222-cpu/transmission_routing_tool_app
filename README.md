# Transmission Line Routing Tool - UETCL Project

> **A web application to help plan 400kV transmission lines in Uganda**
> 
> Developed for: Uganda Electricity Transmission Company Limited (UETCL)
> Case Study: Olwiyo (Uganda) to South Sudan Border 400kV Interconnection

---

## What Does This Tool Do?

This tool helps engineers **find the best route** for high-voltage power lines. Instead of manually drawing lines on a map, the computer uses smart algorithms to:

1. **Avoid obstacles** - Steers clear of towns, protected areas, steep hills, and water
2. **Save money** - Finds shorter paths with fewer towers needed
3. **Follow rules** - Makes sure the route meets engineering standards (tower spacing, slope limits)
4. **Show results visually** - Displays the route on a map with charts and statistics

---

## Quick Start (Get Running in 5 Minutes)

### Step 1: Install Python Requirements

Open your terminal/command prompt and run:

```bash
# Go to the project folder
cd transmission_routing_tool

# Create a virtual environment (keeps things organized)
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### Step 2: Set Up the Database

```bash
python
```

Then in the Python prompt:
```python
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
exit()
```

### Step 3: Run the Application

```bash
python run.py
```

### Step 4: Open in Browser

Go to: **http://localhost:5000**

---

## How to Use the Tool

### 1. Create an Account
- Click **"Register"** on the login page
- Fill in your details (Organization can be "UETCL")
- Log in with your new account

### 2. Plan Your Route

#### Set Start and End Points
1. Click **"Set Start Point"** button
2. Click on the map where the line should begin
3. Click **"Set End Point"** button
4. Click on the map where the line should end

#### Add Waypoints (Optional but Recommended for Long Routes)
- Click **"+ Add Waypoint"** to add intermediate points
- The route will pass through these points
- **Tip:** For long routes (over 100km), add waypoints every 50-75km to help the optimizer

### 3. Choose Your Settings

#### Voltage Level
- **400 kV** - For main transmission lines (default)
- **220 kV** - For sub-transmission
- **132 kV** - For distribution

#### AHP Weights (What to Avoid)
These sliders tell the computer what to prioritize avoiding:

| Weight | What It Means | Default |
|--------|---------------|---------|
| Settlements | Avoid towns and villages | 20% |
| Protected Areas | Avoid parks and reserves | 28.9% |
| Vegetation | Avoid forests | 15.6% |
| Land Use | Avoid farmland | 13.3% |
| Water | Avoid rivers and wetlands | 8.9% |
| Topography | Avoid steep hills | 6.7% |
| Cultural Heritage | Avoid sacred sites | 4.4% |
| Public Infrastructure | Avoid schools, hospitals | 2.2% |

**Important:** All weights must add up to 100% (1.0)

### 4. Choose Map Layers

On the right side of the map, you can turn on different map views:

**Free Layers (No API Key Needed):**
- **Standard** - Basic OpenStreetMap view
- **CyclOSM** - Shows cycling routes (good for paths through terrain)
- **Humanitarian** - Shows buildings and roads clearly
- **Tracestrack Topo** - Shows hills and terrain contours
- **Shortbread** - Clean, simple map style

**Layers Requiring API Keys:**
- **Cycle Map** - Thunderforest (needs free API key)
- **Transport Map** - Thunderforest (needs free API key)
- **MapTiler OMT** - MapTiler (needs free API key)

**Tip:** You can select multiple layers at once to compare features!

### 5. Optimize the Route

1. Choose your algorithm:
   - **Dijkstra** - Classic route finder (reliable)
   - **A*** - Faster with similar results
   - **Both** - Compare both algorithms

2. Click **"🚀 Optimize Route"**

3. Wait for processing (usually 10-30 seconds)

### 6. Review Results

After optimization, you'll see:

#### Route Quality Score
A visual chart showing how well your route avoids:
- 🏘️ Settlements
- ⛰️ Difficult terrain
- 💧 Water bodies
- 📏 Optimal tower spacing

**Color Guide:**
- 🟢 Green (80-100%) = Excellent
- 🟡 Yellow (60-79%) = Good
- 🟠 Orange (40-59%) = Needs improvement
- 🔴 Red (0-39%) = Problem area

#### Statistics
- **Route Length** - Total kilometers
- **Estimated Towers** - How many towers needed
- **Average Span** - Distance between towers
- **Total Cost** - Estimated construction cost
- **Elevation Profile** - Hills and valleys along the route

#### Export Options
- **Export GeoJSON** - For use in other mapping software
- **Export XYZ** - For engineering simulation (Eastings, Northings, Elevation)

---

## Understanding the Map Symbols

| Symbol | Meaning |
|--------|---------|
| 🟢 Green marker | Start point |
| 🔴 Red marker | End point |
| 🟠 Orange markers | Waypoints (optional) |
| 🟠 Orange line | Optimized route |
| 🔵 Blue circles | Tower positions |
| 🟡 Yellow area | 60m corridor (Right of Way) |

---

## Adding Real GIS Data (Optional but Recommended)

The tool works with demo data, but you can add real Uganda data for better results:

### Folder Structure
```
data/
├── dem/              # Elevation data (SRTM GeoTIFF files)
├── landcover/        # Land use data (GeoTIFF)
├── settlements/      # Towns and villages (GeoJSON)
├── protected_areas/  # National parks (GeoJSON)
├── roads/            # Road networks (GeoJSON)
├── waterbodies/      # Rivers and lakes (GeoJSON)
└── forests/          # Forest areas (GeoJSON)
```

### Where to Get Data
- **DEM (Elevation):** USGS EarthExplorer (SRTM 30m)
- **Land Cover:** ESA WorldCover
- **Settlements/Roads:** OpenStreetMap (Geofabrik)
- **Protected Areas:** NEMA, NFA, UWA

---

## API Keys (Optional)

### Thunderforest API Key (for Cycle Map & Transport Map)
1. Go to: https://www.thunderforest.com/
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add to `.env` file: `THUNDERFOREST_API_KEY=your_key_here`

### MapTiler API Key (for MapTiler OMT)
1. Go to: https://www.maptiler.com/
2. Sign up for a free account
3. Get your API key
4. Add to `.env` file: `MAPTILER_API_KEY=your_key_here`

**Note:** Free tiers are more than enough for school projects!

---

## Troubleshooting

### "Route area too large" Error
**Problem:** Your route is too long for the computer to process at once.

**Solution:** Add waypoints to break the route into smaller segments (50-75km each).

### Elevation Shows 0 or Looks Wrong
**Problem:** No DEM data available.

**Solution:** The tool now uses realistic elevation estimates for Uganda (600-3500m) when no DEM is available. Add real DEM data to `data/dem/` for more accuracy.

### Map Layers Not Loading
**Problem:** Internet connection or API key issue.

**Solution:** 
- Check your internet connection
- Try the free layers (Standard, CyclOSM, Humanitarian) that don't need API keys
- If using Cycle Map or Transport Map, make sure you added the Thunderforest API key and restarted the server

### "No valid path found" Error
**Problem:** The algorithm can't find a route between your points.

**Solution:**
- Make sure start and end points are not too close together
- Add waypoints to guide the route around obstacles
- Check that your AHP weights sum to 1.0

---

## Project Files Explained (For Your Presentation)

### **Main Application Files**

| File | What It Does | Simple Explanation |
|------|--------------|-------------------|
| `run.py` | Starts the web server | Like turning on the engine of a car |
| `config.py` | Settings and configuration | The "settings menu" for the app |
| `requirements.txt` | List of Python packages needed | Shopping list for what to install |

### **The "Brain" - Algorithm Files (`app/optimizer/`)**

| File | What It Does | Real-World Analogy |
|------|--------------|-------------------|
| `cost_surface.py` | Creates a "cost map" showing what areas are expensive/difficult to build through | Like a weather map, but showing "danger zones" for construction |
| `dijkstra.py` | Finds the cheapest path from A to B | Like Google Maps finding the fastest route |
| `astar.py` | Faster version of Dijkstra | Like Google Maps with traffic prediction - smarter and faster |
| `engineering_validation.py` | Checks if the route follows rules (tower spacing, slope limits) | Like a building inspector checking if construction meets code |

### **The "Helper" Files (`app/services/`)**

| File | What It Does | Simple Explanation |
|------|--------------|-------------------|
| `dem_loader.py` | Loads elevation data from multiple map tiles | Gets height information for the terrain |
| `elevation_sampling.py` | Reads elevation at specific points | Like asking "how high is this exact spot?" |
| `gis_data_loader.py` | Loads map data (roads, towns, rivers) | Opens the map files |
| `uganda_gis_loader.py` | Special loader for Uganda data | Handles Uganda-specific map formats |

### **The "Database" Files**

| File | What It Does | Simple Explanation |
|------|--------------|-------------------|
| `app/models.py` | Defines database tables | Creates the "filing cabinet" structure |
| `instance/transmission_routing.db` | The actual database file | Where all user accounts and routes are stored |

### **The "Web Pages" (`templates/`)**

| File | What It Shows | User Sees |
|------|---------------|-----------|
| `login.html` | Login page | Username/password boxes |
| `register.html` | Registration page | Form to create new account |
| `dashboard.html` | Main map interface | The big map with all the tools |

### **The "Styling" (`static/`)**

| File/Folder | What It Does | Simple Explanation |
|-------------|--------------|-------------------|
| `css/style.css` | Colors, fonts, layout | Makes everything look pretty |
| `js/map.js` | Map controls and interactions | Handles clicking on the map |
| `js/optimize.js` | Route optimization logic | Does the math when you click "Optimize" |
| `js/layers.js` | Map layer switching | Handles changing map styles |
| `images/` | Pictures and icons | Logo, background images |

### **The "Data" (`data/`)**

| Folder | Contains | Source |
|--------|----------|--------|
| `dem/` | Elevation data (SRTM) | USGS - NASA satellite data |
| `roads/` | Road networks | OpenStreetMap |
| `settlements/` | Towns and villages | OpenStreetMap |
| `waterbodies/` | Rivers and lakes | OpenStreetMap |
| `forests/` | Forest areas | OpenStreetMap |
| `land_use/` | Farmland, urban areas | OpenStreetMap |

### **How Files Work Together (Flow Diagram)**

```
User clicks on map
    ↓
map.js → captures click coordinates
    ↓
optimize.js → sends to server
    ↓
routes_api.py → receives request
    ↓
cost_surface.py → creates "avoidance map"
    ↓
dijkstra.py OR astar.py → finds best path
    ↓
engineering_validation.py → checks if valid
    ↓
elevation_sampling.py → gets heights along route
    ↓
routes_api.py → sends results back
    ↓
optimize.js → displays route and charts
```

### **Key Terms for Your Presentation**

| Term | Simple Definition |
|------|-------------------|
| **DEM** | Digital Elevation Model - a map showing ground height |
| **GIS** | Geographic Information System - digital mapping |
| **AHP** | Analytic Hierarchy Process - method to combine multiple factors |
| **Cost Surface** | A map where each pixel has a "cost" value (higher = avoid) |
| **Waypoint** | A point the route must pass through |
| **Corridor** | The area around the power line (60m wide) |
| **Span** | Distance between two transmission towers |

---

## Key Technical Details

### Algorithms Used
- **Dijkstra's Algorithm** - Finds the cheapest path on a grid
- **A* (A-Star)** - Faster version using heuristics
- **AHP (Analytic Hierarchy Process)** - Combines multiple factors into one "cost"

### Engineering Constraints
- **Tower Spacing:** 250-450 meters (depending on terrain)
- **Corridor Width:** 60 meters (10m RoW + 25m wayleave each side)
- **Max Slope:** 30 degrees
- **Voltage:** 400 kV (configurable)

### Coordinate Systems
- **Map Display:** WGS 84 (EPSG:4326) - Latitude/Longitude
- **Export for Simulation:** UTM Zone 36N (EPSG:21096) - Eastings/Northings

---

## Tips for Best Results

1. **For Short Routes (< 50km):** Use default settings
2. **For Medium Routes (50-150km):** Add 1-2 waypoints
3. **For Long Routes (> 150km):** Add waypoints every 50-75km
4. **To Avoid Towns:** Increase "Settlements" weight
5. **To Avoid Hills:** Increase "Topography" weight
6. **To Follow Roads:** Decrease "Roads" cost in config.py

---

## Support

For questions or issues:
1. Check the error message in the browser console (F12)
2. Check the terminal where you ran `python run.py`
3. Make sure all weights sum to 1.0
4. Try adding waypoints for long routes

---

## Credits

- **Developed for:** Uganda Electricity Transmission Company Limited (UETCL)
- **Case Study:** Olwiyo-South Sudan 400kV Interconnection
- **Data Sources:** USGS (elevation), ESA (land cover), OpenStreetMap (roads/settlements)
- **Algorithms:** Dijkstra, A*, AHP Multi-Criteria Analysis

---

**Good luck with your transmission line planning! ⚡**
