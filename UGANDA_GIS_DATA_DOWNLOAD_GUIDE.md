# Uganda GIS Data Download Guide

This guide will help you download real GIS data for Uganda to use in the Transmission Line Routing Tool.

---

## 🌍 DATA SOURCES FOR UGANDA

### **1. OpenStreetMap (OSM) - FREE & RECOMMENDED**
- **Website:** https://www.openstreetmap.org/
- **Coverage:** Excellent coverage for Uganda
- **Data Types:** Roads, buildings, land use, water bodies, power infrastructure, education facilities

### **2. HOT Export Tool - EASIEST METHOD**
- **Website:** https://export.hotosm.org/
- **What it does:** Custom data exports for specific regions
- **Format:** Shapefile, GeoJSON, KML

### **3. DIVA-GIS - FREE COUNTRY DATA**
- **Website:** https://www.diva-gis.org/gdata
- **Data:** Administrative boundaries, roads, water bodies, elevation

### **4. SRTM Digital Elevation Model (DEM)**
- **Website:** https://earthexplorer.usgs.gov/
- **Data:** 30m resolution elevation data for terrain analysis

---

## 📥 METHOD 1: HOT Export Tool (EASIEST - RECOMMENDED)

### **Step-by-Step Instructions:**

#### **Step 1: Go to HOT Export Tool**
1. Open browser: https://export.hotosm.org/
2. Click "Start Exporting"
3. Login with OpenStreetMap account (or create free account)

#### **Step 2: Define Area of Interest**
1. Click "New Export"
2. Name: "Uganda Transmission Line Data"
3. Description: "GIS data for Olwiyo-South Sudan 400kV line"
4. Search for "Uganda" or zoom to your project area
5. Draw a box around your area of interest (Olwiyo to South Sudan border)

#### **Step 3: Select Data Layers**
Select these features:
- ✅ **Buildings** (for settlements)
- ✅ **Roads** (all types)
- ✅ **Waterways** (rivers, streams)
- ✅ **Water bodies** (lakes, reservoirs)
- ✅ **Land use** (residential, agricultural, forest)
- ✅ **Amenities** (schools, hospitals)
- ✅ **Power** (towers, substations, lines)
- ✅ **Natural** (forests, wetlands, grasslands)
- ✅ **Aeroway** (airports, airstrips)

#### **Step 4: Choose Export Format**
- Format: **Shapefile (.shp)** - Best for GIS analysis
- Alternative: **GeoJSON** - Also works well

#### **Step 5: Download**
1. Click "Create Export"
2. Wait for processing (5-15 minutes)
3. Download the ZIP file
4. Extract to your computer

---

## 📥 METHOD 2: Geofabrik (FAST DOWNLOADS)

### **Step-by-Step Instructions:**

#### **Step 1: Download Uganda OSM Data**
1. Go to: https://download.geofabrik.de/africa/uganda.html
2. Download: **uganda-latest.osm.pbf** (compressed OSM data)
3. Or download: **uganda-latest-free.shp.zip** (Shapefile format)

#### **Step 2: Extract Specific Layers**
The shapefile ZIP contains:
- `gis_osm_buildings_a_free_1.shp` - Buildings
- `gis_osm_roads_free_1.shp` - Roads
- `gis_osm_waterways_free_1.shp` - Rivers/streams
- `gis_osm_water_a_free_1.shp` - Water bodies
- `gis_osm_landuse_a_free_1.shp` - Land use
- `gis_osm_pois_free_1.shp` - Points of interest (schools, etc.)
- `gis_osm_natural_free_1.shp` - Natural features

---

## 📥 METHOD 3: SRTM Elevation Data (DEM)

### **Step-by-Step Instructions:**

#### **Step 1: Go to USGS EarthExplorer**
1. Website: https://earthexplorer.usgs.gov/
2. Create free account (required)

#### **Step 2: Define Area**
1. Click "Search Criteria"
2. Enter coordinates for Uganda or use map
3. Uganda bounds: 
   - North: 4.2°
   - South: -1.5°
   - East: 35.0°
   - West: 29.5°

#### **Step 3: Select Dataset**
1. Click "Data Sets"
2. Expand "Digital Elevation"
3. Select: **SRTM 1 Arc-Second Global** (30m resolution)

#### **Step 4: Download**
1. Click "Results"
2. Download tiles covering your project area
3. Format: GeoTIFF

---

## 📥 METHOD 4: DIVA-GIS Country Data

### **Step-by-Step Instructions:**

#### **Step 1: Download Uganda Data**
1. Go to: https://www.diva-gis.org/gdata
2. Select Country: **Uganda**
3. Select Subject: Download each of these:
   - **Administrative areas** (boundaries)
   - **Roads**
   - **Water bodies** (lakes, rivers)
   - **Elevation** (DEM)

#### **Step 2: Download**
- Format: Shapefile (ready to use)
- Extract ZIP files to your data folders

---

## 📁 ORGANIZING DOWNLOADED DATA

After downloading, organize files into these folders:

```
transmission_routing_tool/
└── data/
    ├── dem/
    │   └── uganda_srtm_30m.tif
    ├── land_use/
    │   └── gis_osm_landuse_a_free_1.shp
    ├── settlements/
    │   └── gis_osm_buildings_a_free_1.shp
    ├── protected_areas/
    │   └── uganda_protected_areas.shp
    ├── roads/
    │   └── gis_osm_roads_free_1.shp
    ├── education/
    │   └── schools_uganda.shp
    ├── power_infrastructure/
    │   └── gis_osm_power_free_1.shp
    ├── waterbodies/
    │   └── gis_osm_water_a_free_1.shp
    ├── forests/
    │   └── gis_osm_natural_free_1.shp
    └── airports/
        └── gis_osm_aeroway_free_1.shp
```

---

## 🔧 NEXT STEPS AFTER DOWNLOADING

1. **Extract all ZIP files**
2. **Organize into data folders** (see structure above)
3. **Update config.py** with actual file paths
4. **Run the optimization** - system will use real data!

---

## ⚡ QUICK START (5 MINUTES)

**Fastest way to get started:**

1. Go to: https://download.geofabrik.de/africa/uganda.html
2. Download: **uganda-latest-free.shp.zip** (~ 50 MB)
3. Extract ZIP file
4. Copy shapefiles to appropriate data folders
5. Done! ✅

---

## 📞 NEED HELP?

If you encounter issues:
- Check file formats (should be .shp, .tif, or .geojson)
- Verify coordinate system (should be WGS84 / EPSG:4326)
- Make sure all shapefile components are present (.shp, .shx, .dbf, .prj)


