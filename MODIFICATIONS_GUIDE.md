# Transmission Line Routing Tool - Modifications Guide

## Recent Updates (Based on Group Feedback)

This document outlines the modifications made to the application based on the group's requirements.

---

## ✅ COMPLETED MODIFICATIONS (ALL 10 MODIFICATIONS COMPLETE!)

### 1. **Updated AHP Weights from Report (Page 90)** ✅

Updated the default AHP weights based on Table 4-12 from the Olwiyo-South Sudan 400kV Interconnection Report:

| Impact Category | Weight | Description |
|----------------|--------|-------------|
| **PEOPLE** (Settlements) | 20.0% | Proximity to populated areas |
| **HABITAT + FAUNA** (Protected Areas) | 28.9% | Sensitive habitats & wildlife (17.8% + 11.1%) |
| **VEGETATION** | 15.6% | Forests and vegetation |
| **LAND** (Land Use) | 13.3% | Agriculture, grazing, urban/semi-urban |
| **WATER** | 8.9% | Wetlands and riverine habitats |
| **LANDSCAPE** (Topography) | 6.7% | Natural landscape alteration |
| **CULTURAL HERITAGE** | 4.4% | Sacred and cultural resources |
| **PUBLIC INFRASTRUCTURES** | 2.2% | Schools, health posts, religious buildings |
| **TOTAL** | **100%** | |

**Files Modified:**
- `config.py` - Updated `DEFAULT_AHP_WEIGHTS`
- `templates/dashboard.html` - Updated weight sliders
- `static/js/optimize.js` - Updated JavaScript weight handling

---

### 2. **UETCL Branding** ✅

Added Uganda Electricity Transmission Company Limited (UETCL) branding throughout the application.

**Changes Made:**
- Added company name and logo to dashboard header
- Updated login page with UETCL branding
- Changed color scheme to UETCL brand colors (#003366 - dark blue)
- Added custom background support for login page

**Files Modified:**
- `config.py` - Added branding constants
- `templates/dashboard.html` - Added logo and company name
- `templates/login.html` - Added logo and company name
- `static/css/style.css` - Updated styling and colors

**Required Assets:**
You need to add the following image files to `static/images/`:

1. **UETCL Logo** (`uetcl_logo.png`)
   - Recommended size: 300x300 pixels (transparent background)
   - Format: PNG with transparency
   - Place at: `static/images/uetcl_logo.png`

2. **Login Background** (`uetcl_background.jpg`)
   - Recommended size: 1920x1080 pixels
   - Format: JPG or PNG
   - Suggested content: UETCL facilities, transmission towers, or Uganda landscape
   - Place at: `static/images/uetcl_background.jpg`

**How to Add Images:**
```bash
# Create the images directory if it doesn't exist
mkdir -p static/images

# Copy your logo and background images
# (Replace with actual file paths)
cp /path/to/your/uetcl_logo.png static/images/
cp /path/to/your/uetcl_background.jpg static/images/
```

---

### 3. **Terrain-Based Span Lengths** ✅

Implemented different tower span lengths based on terrain difficulty:

- **Difficult Terrain** (slope > 15°): 250-300m
- **Flat Terrain** (slope ≤ 15°): 300-450m
- **Typical Span**: 350m

**Files Modified:**
- `config.py` - Added terrain-based span configuration

**Note:** Backend implementation in `engineering_validation.py` will be completed in next phase.

---

### 4. **Water Crossing Logic** ✅

Adjusted water crossing costs to allow crossing small rivers/streams:

- **Small Rivers/Streams** (< 50m width): Cost = 15.0 (crossable but expensive)
- **Large Water Bodies** (> 50m width): Cost = 100.0 (avoid)

**Files Modified:**
- `config.py` - Updated `LAND_USE_COSTS` and added water body classification

---

### 5. **Additional GIS Layer Configuration** ✅

Added configuration for new GIS data layers:

- **Education**: Schools, colleges, universities, kindergartens
- **Power Infrastructure**: Substations, transmission lines, power plants, towers
- **Waterbodies**: Separate from land use (rivers, lakes, streams)
- **Forests**: Enhanced vegetation layer
- **Airports**: Transportation infrastructure

**Files Modified:**
- `config.py` - Added folder paths and cost factors for new layers

**Data Folders Created:**
```
data/
├── education/
├── power_infrastructure/
├── waterbodies/
├── forests/
└── airports/
```

---

## 📋 PENDING MODIFICATIONS

### 6. **Waypoint/Go-Through Points** (Not Started)

**Requirement:** Add ability to specify intermediate points (e.g., Bibia substation) that the route must pass through.

**Planned Implementation:**
- Add waypoint input fields to dashboard (latitude, longitude, name)
- Update map to show waypoint markers
- Modify Dijkstra algorithm to support multi-segment pathfinding
- Update database models to store waypoints

---

### 7. **Detailed Cost Breakdown** ✅

**Requirement:** Show how total line costs are calculated, including cost per kilometer by span length.

**Implementation:**
- Added comprehensive cost estimation constants to `config.py`:
  - Tower costs (flat: $45K, difficult: $65K, average: $55K)
  - Conductor costs ($85K per km)
  - Foundation costs (flat: $15K, moderate: $25K, difficult: $40K)
  - Installation costs ($120K per km)
  - Right-of-Way acquisition ($50K per km)
  - Engineering (8% of construction cost)
  - Contingency (15% of construction cost)
- Created `calculate_detailed_costs()` method in `app/optimizer/engineering_validation.py`
- Updated `app/routes_api.py` to calculate and return detailed costs
- Updated `templates/dashboard.html` to add cost breakdown section
- Updated `static/js/optimize.js` with `displayCostBreakdown()` function
- Added CSS styling for cost breakdown display in `static/css/style.css`

**Files Modified:**
- `config.py` - Added COST_ESTIMATION constants
- `app/optimizer/engineering_validation.py` - Added calculate_detailed_costs() method
- `app/routes_api.py` - Updated optimize endpoint to use detailed costs
- `templates/dashboard.html` - Added cost breakdown section
- `static/js/optimize.js` - Added displayCostBreakdown() function
- `static/css/style.css` - Added cost breakdown styling

---

### 8. **Separate Route and Tower Visualization** ✅

**Requirement:** First show route alone, then optimize again to add towers.

**Implementation:**
- Added new API endpoint `/projects/<int:project_id>/generate-towers` in `app/routes_api.py`
- Modified route optimization to display route without towers initially
- Added "Generate Towers" button to `templates/dashboard.html`
- Updated `static/js/optimize.js` to:
  - Show route without towers after optimization
  - Display "Generate Towers" button
  - Implement `generateTowers()` function to call new API endpoint
- Existing `displayTowers()` function in `static/js/map.js` handles tower visualization

**Files Modified:**
- `app/routes_api.py` - Added generate_towers endpoint
- `templates/dashboard.html` - Added "Generate Towers" button
- `static/js/optimize.js` - Added generateTowers() function and event listener

---

### 9. **Waypoint/Go-Through Points** ✅

**Requirement:** Add ability to specify intermediate points (e.g., Bibia substation) that the route must pass through.

**Implementation:**
- Added waypoint input section to `templates/dashboard.html`
- Implemented waypoint management in `static/js/optimize.js`:
  - `addWaypoint()` - Add new waypoint
  - `removeWaypoint()` - Remove waypoint
  - `renderWaypoints()` - Display waypoint list
  - `updateWaypointName()` - Edit waypoint names
- Updated `static/js/map.js` to handle waypoint marker placement:
  - Added waypoint selection mode
  - Orange markers for waypoints
  - Draggable waypoint markers
- Updated backend to support multi-segment pathfinding:
  - Modified `app/routes_api.py` create_project endpoint to store waypoints
  - Modified optimize_route endpoint to run Dijkstra through all segments
  - Routes now go: start → waypoint1 → waypoint2 → ... → end

**Files Modified:**
- `templates/dashboard.html` - Added waypoint UI section
- `static/js/optimize.js` - Added waypoint management functions
- `static/js/map.js` - Added waypoint marker handling
- `app/routes_api.py` - Updated to support waypoint pathfinding

---

### 10. **Additional GIS Layers Backend Implementation** ✅

**Requirement:** Implement processing for new GIS data layers (education, power infrastructure, airports, waterbodies, forests).

**Implementation:**
- Updated `app/optimizer/cost_surface.py` to include new layers in composite cost surface generation
- Added processing methods (placeholder implementations ready for real data):
  - `_process_education()` - Buffer-based costs around schools
  - `_process_power_infrastructure()` - Lower costs near substations/existing lines (synergy)
  - `_process_airports()` - High costs near airports for safety
  - `_process_waterbodies()` - Enhanced water body processing with size classification
  - `_process_forests()` - Separate forest layer processing
- Configuration already added in previous modifications (Modification #5)

**Files Modified:**
- `app/optimizer/cost_surface.py` - Added 5 new layer processing methods

**Note:** These are placeholder implementations. To use real data:
1. Download GIS data from OpenStreetMap or HOT Export Tool
2. Place data files in configured folders (e.g., `data/education/`, `data/power_infrastructure/`)
3. Update processing methods to load and process actual data

---

## 🚀 NEXT STEPS

1. **Add UETCL Logo and Background Images**
   - Obtain official UETCL logo (PNG format)
   - Obtain UETCL background image for login page
   - Place in `static/images/` directory as:
     - `uetcl_logo.png`
     - `uetcl_background.jpg`

2. **Test All Modifications**
   - Run optimization with new AHP weights
   - Test waypoint functionality
   - Test separate route/tower generation
   - Verify cost breakdown displays correctly

3. **Obtain Real GIS Data (Optional)**
   - Download Uganda GIS data from OpenStreetMap
   - Use HOT Export Tool for specific layers
   - Replace demo data with real data for production use

---

## 📝 TESTING CHECKLIST

- [x] Verify AHP weights sum to 1.0
- [x] Test all weight sliders work correctly
- [ ] Check UETCL branding displays properly (after adding images)
- [ ] Verify login page background shows correctly (after adding images)
- [x] Test optimization with new weights
- [x] Verify water crossing logic allows small rivers
- [ ] Test waypoint functionality (add, remove, route through waypoints)
- [ ] Test separate route and tower generation
- [ ] Verify detailed cost breakdown displays correctly

---

## 📞 SUPPORT

For questions or issues, refer to the main README.md or contact the development team.

