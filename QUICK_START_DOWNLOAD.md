# 🚀 QUICK START: Download Uganda GIS Data (5 Minutes)

## ✅ EASIEST METHOD - Follow These Steps:

### **STEP 1: Download Uganda Data (2 minutes)**

I just opened this page in your browser:
**https://download.geofabrik.de/africa/uganda.html**

On that page:
1. Find the file: **`uganda-latest-free.shp.zip`**
2. Click to download (~50-100 MB)
3. Wait for download to complete
4. Save to your Downloads folder

---

### **STEP 2: Extract the ZIP File (1 minute)**

1. Go to your Downloads folder
2. Find `uganda-latest-free.shp.zip`
3. Right-click → "Extract All..."
4. Extract to a folder (e.g., `uganda_gis_data`)

You'll see many files like:
- `gis_osm_roads_free_1.shp`
- `gis_osm_buildings_a_free_1.shp`
- `gis_osm_water_a_free_1.shp`
- `gis_osm_landuse_a_free_1.shp`
- And many more...

---

### **STEP 3: Organize Files (2 minutes)**

#### **Option A: Automatic (Recommended)**
Run this command in your terminal:
```powershell
python download_uganda_data.py
```
This will automatically organize the files for you!

#### **Option B: Manual**
Copy files to these folders:

```
transmission_routing_tool/data/
├── roads/
│   └── Copy: gis_osm_roads_free_1.shp (and .shx, .dbf, .prj)
├── settlements/
│   └── Copy: gis_osm_buildings_a_free_1.shp (and .shx, .dbf, .prj)
├── waterbodies/
│   └── Copy: gis_osm_water_a_free_1.shp (and .shx, .dbf, .prj)
├── land_use/
│   └── Copy: gis_osm_landuse_a_free_1.shp (and .shx, .dbf, .prj)
├── forests/
│   └── Copy: gis_osm_natural_free_1.shp (and .shx, .dbf, .prj)
├── power_infrastructure/
│   └── Copy: gis_osm_power_free_1.shp (and .shx, .dbf, .prj)
├── airports/
│   └── Copy: gis_osm_transport_a_free_1.shp (and .shx, .dbf, .prj)
└── education/
    └── Copy: gis_osm_pois_free_1.shp (and .shx, .dbf, .prj)
```

**IMPORTANT:** When copying .shp files, also copy the related files:
- `.shx` - Shape index
- `.dbf` - Attribute data
- `.prj` - Projection info
- `.cpg` - Character encoding

---

### **STEP 4: Download Elevation Data (Optional - 5 minutes)**

For terrain/topology analysis, you need DEM (Digital Elevation Model):

1. **Go to:** https://earthexplorer.usgs.gov/
2. **Create free account** (if you don't have one)
3. **Search for Uganda:**
   - Click "Search Criteria"
   - Enter: Uganda or coordinates (29.5°E to 35.0°E, -1.5°S to 4.2°N)
4. **Select Dataset:**
   - Click "Data Sets"
   - Expand "Digital Elevation"
   - Check: **SRTM 1 Arc-Second Global**
5. **Download:**
   - Click "Results"
   - Download tiles covering your project area
   - Save to: `data/dem/`

---

## 📊 WHAT YOU'LL HAVE AFTER DOWNLOAD

After completing these steps, you'll have real GIS data for:

✅ **Roads** - All road types in Uganda  
✅ **Settlements** - Buildings and populated areas  
✅ **Water bodies** - Lakes, rivers, wetlands  
✅ **Land use** - Agriculture, residential, parks  
✅ **Forests** - Natural vegetation  
✅ **Power infrastructure** - Existing transmission lines, substations  
✅ **Airports** - Airports and airstrips  
✅ **Education** - Schools, colleges (in POIs)  
✅ **DEM** - Elevation/terrain data (if downloaded)  

---

## 🎯 AFTER DOWNLOADING

### **Test with Real Data:**

1. **Make sure files are in data/ folders**
2. **Restart Flask server** (if running)
3. **Create new project** in the web app
4. **Click "Optimize Route"**
5. **System will use REAL Uganda data!** 🎉

---

## 🔧 TROUBLESHOOTING

### **Problem: Files not found**
- Check that .shp files are in correct folders
- Make sure related files (.shx, .dbf, .prj) are also copied

### **Problem: Download too slow**
- Try downloading at different time
- Use alternative source: DIVA-GIS (smaller files)

### **Problem: Don't want to download**
- App works with demo data too!
- Real data improves accuracy but not required for testing

---

## 📞 ALTERNATIVE SOURCES

If Geofabrik doesn't work, try these:

1. **DIVA-GIS:** https://www.diva-gis.org/gdata
   - Select: Uganda
   - Download: Roads, Water, Elevation
   - Smaller file sizes

2. **HOT Export Tool:** https://export.hotosm.org/
   - Custom area selection
   - Choose specific layers
   - Requires free OSM account

3. **OpenStreetMap Direct:** https://www.openstreetmap.org/
   - Export specific areas
   - Smaller regions only

---

## ✅ SUMMARY

**Minimum Required (5 minutes):**
1. Download `uganda-latest-free.shp.zip` from Geofabrik ✅
2. Extract ZIP file ✅
3. Copy .shp files to data/ folders ✅
4. Done! Ready to use real data! 🎉

**Optional (adds 5 more minutes):**
- Download DEM from USGS EarthExplorer
- Adds terrain analysis capability

---

**Your transmission line routing tool will now use REAL Uganda GIS data for optimization!** 🌍⚡

