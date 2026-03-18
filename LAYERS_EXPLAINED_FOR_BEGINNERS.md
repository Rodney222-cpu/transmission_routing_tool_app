# 🗺️ Understanding the Map Layers - Beginner's Guide

This guide explains all the map layers in simple terms so anyone can understand what they mean and why they matter for transmission line routing.

---

## 📚 **Table of Contents**

1. [What Are Layers?](#what-are-layers)
2. [Land Use (ESA WorldCover Classes)](#land-use-esa-worldcover-classes)
3. [Topography (DEM - Digital Elevation Model)](#topography-dem)
4. [Settlements](#settlements)
5. [Protected Areas](#protected-areas)
6. [Roads](#roads)
7. [Water Bodies](#water-bodies)
8. [How Layers Affect Route Cost](#how-layers-affect-route-cost)
9. [AHP Weights Explained](#ahp-weights-explained)

---

## 🎯 **What Are Layers?**

Think of layers like **transparent sheets stacked on top of each other**:

```
┌─────────────────────┐
│   Settlements       │ ← Cities, towns, villages
├─────────────────────┤
│   Roads             │ ← Highways, streets
├─────────────────────┤
│   Protected Areas   │ ← National parks, reserves
├─────────────────────┤
│   Water Bodies      │ ← Lakes, rivers
├─────────────────────┤
│   Land Use          │ ← Forests, farms, buildings
├─────────────────────┤
│   Topography (DEM)  │ ← Hills, valleys, elevation
└─────────────────────┘
        ↓
    Combined Map
```

Each layer shows **different information** about the same area. The system combines all layers to find the **best route** for the transmission line.

---

## 🌍 **Land Use (ESA WorldCover Classes)**

### **What Is It?**
Land use shows **what covers the ground** - forests, farms, buildings, water, etc.

### **Data Source:**
**ESA WorldCover** - Satellite images from the European Space Agency that classify every 10m × 10m square of land.

### **The Classes (Categories):**

| Class Code | Name | What It Means | Color on Map | Cost Factor |
|------------|------|---------------|--------------|-------------|
| **10** | **Tree Cover** | Forests, dense trees | 🟢 Dark Green | **3.0** (Moderate) |
| **20** | **Shrubland** | Bushes, small plants | 🟤 Brown | **2.0** (Low-Moderate) |
| **30** | **Grassland** | Open grass, savanna | 🟡 Yellow-Green | **1.0** (Low - Best!) |
| **40** | **Cropland** | Farms, agriculture | 🟠 Tan/Beige | **1.5** (Low-Moderate) |
| **50** | **Built-up** | Cities, buildings, roads | ⚫ Dark Gray | **10.0** (Very High!) |
| **60** | **Bare/Sparse** | Rocks, sand, bare ground | 🟫 Light Brown | **1.2** (Low) |
| **70** | **Snow/Ice** | Permanent snow/ice | ⚪ White | **1.0** (N/A in Uganda) |
| **80** | **Water Bodies** | Lakes, large rivers | 🔵 Blue | **100.0** (Avoid!) |
| **90** | **Wetlands** | Swamps, marshes | 🟦 Teal | **5.0** (High) |
| **95** | **Mangroves** | Coastal mangrove forests | 🟩 Blue-Green | **5.0** (High) |

### **Why It Matters:**

✅ **Grassland (30)** = **BEST** - Easy to build, low cost  
✅ **Cropland (40)** = **GOOD** - Farmland, moderate compensation  
⚠️ **Forest (10)** = **MODERATE** - Need to clear trees, environmental impact  
⚠️ **Wetlands (90)** = **DIFFICULT** - Soft ground, environmental concerns  
❌ **Built-up (50)** = **VERY EXPENSIVE** - Must avoid buildings, high compensation  
❌ **Water (80)** = **AVOID** - Cannot build towers in lakes!  

### **In Simple Terms:**
- **Green areas (forests)** = Need to cut trees (expensive + environmental impact)
- **Yellow areas (grassland)** = Easy to build (cheap!)
- **Gray areas (buildings)** = Must avoid or pay a lot for land
- **Blue areas (water)** = Cannot build there!

---

## ⛰️ **Topography (DEM - Digital Elevation Model)**

### **What Is It?**
Shows the **height of the land** - hills, valleys, mountains, flat areas.

### **Data Source:**
**USGS SRTM 30m** - Satellite radar measurements of Earth's elevation, accurate to 30 meters.

### **What You See:**

| Elevation | Color | Terrain Type | Cost Impact |
|-----------|-------|--------------|-------------|
| **Low (< 1000m)** | 🟢 Green | Flat plains, valleys | **Low cost** |
| **Medium (1000-1500m)** | 🟡 Yellow | Rolling hills | **Moderate cost** |
| **High (1500-2000m)** | 🟠 Orange | Steep hills | **High cost** |
| **Very High (> 2000m)** | 🔴 Red | Mountains | **Very high cost** |

### **Why It Matters:**

✅ **Flat terrain** = Easy construction, standard tower heights  
⚠️ **Gentle slopes (< 15°)** = Acceptable, slightly higher cost  
⚠️ **Steep slopes (15-30°)** = Difficult, need special foundations  
❌ **Very steep (> 30°)** = **NOT ALLOWED** - Too dangerous!  

### **Slope Calculation:**
The system calculates **slope** (steepness) from elevation:
- **Slope = Rise / Run × 100%**
- **Example:** If land rises 30m over 100m distance = 30% slope = 16.7° angle

### **Engineering Limits:**
- ✅ **0-15° slope** = Good (normal construction)
- ⚠️ **15-30° slope** = Acceptable (difficult terrain, higher cost)
- ❌ **> 30° slope** = **ERROR** - Too steep, route rejected!

### **In Simple Terms:**
- **Flat land** = Easy to build, cheap
- **Hills** = Harder to build, more expensive
- **Steep mountains** = Cannot build transmission lines safely!

---

## 🏘️ **Settlements**

### **What Is It?**
Shows where **people live** - cities, towns, villages.

### **Data Source:**
**OpenStreetMap (OSM)** - Community-mapped data of all settlements in Uganda.

### **Categories:**

| Type | What It Means | Color on Map |
|------|---------------|--------------|
| **City** | Large urban area (e.g., Kampala) | 🔴 Large red circle |
| **Town** | Medium urban area | 🟠 Medium orange circle |
| **Village** | Small settlement | 🟡 Small yellow circle |

### **Why It Matters:**

❌ **Cannot build through settlements!**
- People live there
- Buildings in the way
- Very expensive land compensation
- Safety concerns (electromagnetic fields near homes)

### **Distance-Based Costs:**

| Distance from Settlement | Cost Factor | Why |
|--------------------------|-------------|-----|
| **< 100m** | **100.0** | Too close - avoid! |
| **100-500m** | **5.0** | Close - high cost |
| **500-1000m** | **2.0** | Moderate distance |
| **> 1000m** | **1.0** | Safe distance - good! |

### **In Simple Terms:**
- **Stay away from villages and cities!**
- The closer to people, the more expensive
- Best routes go through **empty areas**

---

## 🌳 **Protected Areas**

### **What Is It?**
Land that is **legally protected** for conservation - national parks, wildlife reserves, forest reserves.

### **Data Source:**
- **NEMA** (National Environment Management Authority)
- **NFA** (National Forestry Authority)
- **UWA** (Uganda Wildlife Authority)
- **OpenStreetMap** (backup)

### **Examples in Uganda:**
- **Murchison Falls National Park**
- **Queen Elizabeth National Park**
- **Bwindi Impenetrable Forest**
- **Budongo Forest Reserve**

### **Why It Matters:**

⚠️ **Very difficult to get permission!**
- Environmental impact assessments required
- May need special approval from government
- High environmental compensation costs
- Possible route rejection

### **Cost Factor: 8.0** (Very High)

### **In Simple Terms:**
- **Protected areas = National parks, wildlife reserves**
- **Very hard to build there** - lots of paperwork and approvals
- **Best to avoid** if possible
- If you must cross, expect delays and high costs

---

## 🛣️ **Roads**

### **What Is It?**
Shows all **roads and highways** in the area.

### **Data Source:**
**OpenStreetMap (OSM)** - All road types from highways to small tracks.

### **Road Types:**

| Type | What It Means | Color on Map |
|------|---------------|--------------|
| **Motorway** | Major highway (e.g., Kampala-Gulu) | 🔴 Thick red line |
| **Primary** | Main road | 🟠 Orange line |
| **Secondary** | Regional road | 🟡 Yellow line |
| **Tertiary** | Local road | ⚪ White line |
| **Track** | Dirt road | ⚫ Gray line |

### **Why Roads Are GOOD:**

✅ **Roads help construction!**
- Easy access for trucks and equipment
- Can transport materials
- Workers can reach the site
- **Lower cost near roads!**

### **Distance-Based Benefits:**

| Distance from Road | Cost Factor | Why |
|-------------------|-------------|-----|
| **< 500m** | **0.8** | Great access - cheaper! |
| **500-2000m** | **0.9** | Good access |
| **> 2000m** | **1.0** | No benefit (too far) |

### **In Simple Terms:**
- **Roads are your friend!**
- Building near roads = **cheaper** (easy to bring materials)
- Building far from roads = **more expensive** (hard to access)
- Routes often follow roads when possible

---

## 💧 **Water Bodies**

### **What Is It?**
Shows **lakes, rivers, streams, and wetlands**.

### **Data Source:**
**OpenStreetMap (OSM)** - All water features in Uganda.

### **Types:**

| Type | What It Means | Color on Map | Can Cross? |
|------|---------------|--------------|------------|
| **Lake** | Large water body (e.g., Lake Victoria) | 🔵 Large blue area | ❌ NO - Must go around |
| **River (Large)** | Major river (e.g., Nile) | 🔵 Thick blue line | ⚠️ Expensive crossing |
| **River (Small)** | Stream, creek | 🔵 Thin blue line | ✅ Yes - with bridge/crossing |
| **Wetland** | Swamp, marsh | 🟦 Teal area | ⚠️ Difficult, avoid if possible |

### **Why It Matters:**

❌ **Large water bodies = AVOID!**
- Cannot build towers in water
- Very expensive to cross (special towers, long spans)
- Environmental concerns

✅ **Small rivers = Can cross**
- Need special river-crossing towers
- Longer span (400-450m)
- Higher cost but doable

### **Cost Factors:**

| Water Type | Cost Factor | Why |
|------------|-------------|-----|
| **Large lake** | **100.0** | Cannot cross - route around! |
| **Small river** | **15.0** | Can cross but expensive |
| **Wetland** | **5.0** | Soft ground, environmental issues |

### **In Simple Terms:**
- **Big lakes** = Go around them!
- **Small rivers** = Can cross but costs more
- **Wetlands** = Soft muddy ground, hard to build
- Best routes **avoid water** when possible

---

## 💰 **How Layers Affect Route Cost**

### **The Cost Surface:**

The system combines **all layers** into one "cost surface" - a map showing how expensive each area is to build through.

### **How It Works:**

```
Step 1: Each layer gets a COST
├─ Grassland = 1.0 (cheap)
├─ Forest = 3.0 (moderate)
├─ Buildings = 10.0 (expensive)
└─ Water = 100.0 (avoid!)

Step 2: Each layer gets a WEIGHT (importance)
├─ Protected Areas = 28.9% (most important!)
├─ Settlements = 20.0%
├─ Vegetation = 15.6%
├─ Land Use = 13.3%
├─ Water = 8.9%
├─ Topography = 6.7%
└─ Infrastructure = 2.2%

Step 3: Combine them
Final Cost = (Layer1 × Weight1) + (Layer2 × Weight2) + ...
```

### **Example Calculation:**

**Location A: Open grassland, flat, far from people**
```
Land Use (grassland):    1.0 × 13.3% = 0.133
Topography (flat):       1.0 × 6.7%  = 0.067
Settlements (far):       1.0 × 20.0% = 0.200
Protected (none):        1.0 × 28.9% = 0.289
─────────────────────────────────────────────
Total Cost = 0.689 (LOW - GOOD ROUTE!)
```

**Location B: Forest, steep hill, near village**
```
Land Use (forest):       3.0 × 13.3% = 0.399
Topography (steep):      5.0 × 6.7%  = 0.335
Settlements (near):      5.0 × 20.0% = 1.000
Protected (none):        1.0 × 28.9% = 0.289
─────────────────────────────────────────────
Total Cost = 2.023 (HIGH - AVOID!)
```

**Location C: Inside national park**
```
Protected Area:          8.0 × 28.9% = 2.312
(Other layers):          ...         = 0.500
─────────────────────────────────────────────
Total Cost = 2.812 (VERY HIGH - AVOID!)
```

### **In Simple Terms:**
- **Low cost areas** = Easy to build, cheap
- **High cost areas** = Difficult to build, expensive
- The algorithm finds the **path with lowest total cost**

---

## 📊 **AHP Weights Explained**

### **What Is AHP?**

**AHP = Analytic Hierarchy Process**

It's a scientific method to decide **how important** each factor is when choosing a route.

### **The Weights (Based on UETCL Standards):**

| Layer | Weight | What It Means | Why This Weight? |
|-------|--------|---------------|------------------|
| **Protected Areas** | **28.9%** | Most important! | Environmental law, wildlife protection |
| **Settlements** | **20.0%** | Very important | People's safety, land compensation |
| **Vegetation** | **15.6%** | Important | Forests, environmental impact |
| **Land Use** | **13.3%** | Moderate | Farms, buildings, land type |
| **Water** | **8.9%** | Moderate | Rivers, wetlands, crossings |
| **Topography** | **6.7%** | Less important | Hills affect cost but not as critical |
| **Cultural Heritage** | **4.4%** | Minor | Sacred sites, historical places |
| **Infrastructure** | **2.2%** | Minor | Schools, hospitals, public buildings |
| **TOTAL** | **100%** | | |

### **Why These Weights?**

These weights come from the **UETCL Olwiyo-South Sudan 400kV Report** (Page 90, Table 4-12).

They reflect **Uganda's priorities**:
1. **Protect the environment** (Protected areas = 28.9%)
2. **Protect people** (Settlements = 20%)
3. **Minimize environmental damage** (Vegetation = 15.6%)
4. **Consider land use** (Agriculture, etc. = 13.3%)

### **What Happens If You Change Weights?**

You can adjust weights in the UI! Here's what happens:

**Increase "Protected Areas" weight:**
- Route will **avoid parks more strongly**
- May take a longer path to go around reserves
- Lower environmental impact

**Increase "Settlements" weight:**
- Route will **stay far from villages**
- May go through forests instead of near towns
- Lower social impact

**Increase "Topography" weight:**
- Route will **prefer flat land**
- May avoid hills even if it means going through forests
- Easier construction

### **In Simple Terms:**
- **Weights = How much you care about each factor**
- **Higher weight = More important to avoid**
- **Default weights = UETCL's recommended values**
- You can change them based on your project priorities!

---

## 🎯 **Quick Reference Chart**

### **What to Avoid (High Cost):**

| Feature | Cost | Why Avoid? |
|---------|------|------------|
| 🏙️ **Cities/Buildings** | 10.0 | People, compensation, safety |
| 💧 **Large Lakes** | 100.0 | Cannot build in water! |
| 🌳 **Protected Areas** | 8.0 | Environmental laws, permits |
| 🏞️ **Wetlands** | 5.0 | Soft ground, environmental concerns |
| 🌲 **Dense Forests** | 3.0 | Tree clearing, environmental impact |
| ⛰️ **Steep Slopes (>30°)** | Rejected | Too dangerous! |

### **What to Prefer (Low Cost):**

| Feature | Cost | Why Prefer? |
|---------|------|------------|
| 🌾 **Grassland** | 1.0 | Easy to build, low impact |
| 🌾 **Cropland** | 1.5 | Farmland, moderate compensation |
| 🛣️ **Near Roads** | 0.8 | Easy access for construction |
| 🏔️ **Flat Terrain** | 1.0 | Standard construction |
| 🏜️ **Open Areas** | 1.0 | No obstacles |

---

## 📚 **Summary for Beginners**

### **Think of It Like This:**

Building a transmission line is like **planning a road trip**:

1. **Land Use** = What's on the ground (forests, farms, buildings)
2. **Topography** = How hilly the terrain is
3. **Settlements** = Where people live (must avoid!)
4. **Protected Areas** = National parks (need permission)
5. **Roads** = Existing roads (help you get there!)
6. **Water** = Lakes and rivers (hard to cross)

### **The Goal:**

Find a path that:
- ✅ Avoids cities and villages
- ✅ Avoids national parks
- ✅ Stays on flat or gentle terrain
- ✅ Crosses small obstacles (rivers, forests) when necessary
- ✅ Follows roads when possible
- ✅ **Costs the least money to build!**

### **The Algorithm:**

The computer looks at **millions of possible paths** and picks the one with the **lowest total cost**, considering all the layers and their weights.

---

## 🎓 **Learning More**

### **Data Sources:**

- **ESA WorldCover:** https://worldcover.org
- **USGS SRTM:** https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-srtm
- **OpenStreetMap:** https://www.openstreetmap.org
- **UETCL Report:** Olwiyo-South Sudan 400kV Interconnection Feasibility Study

### **Key Terms:**

- **Raster:** Grid of pixels, each with a value (like a photo)
- **Vector:** Points, lines, polygons (like a drawing)
- **Cost Surface:** Map showing cost to build in each area
- **Pathfinding:** Algorithm to find the best route
- **AHP:** Method to decide importance of factors

---

## ✅ **You Now Understand:**

✅ What each layer shows
✅ Why each layer matters
✅ How costs are calculated
✅ Why the algorithm picks certain routes
✅ How to interpret the results

**You're ready to use the tool like a pro!** 🎉

---

## 🚀 **Next Steps**

1. **Try the tool** - Create a project and optimize a route
2. **Enable layers** - Turn on different layers to see the data
3. **Adjust weights** - Experiment with AHP weights to see how routes change
4. **Generate towers** - Click "Generate Towers" to see the final design
5. **Export results** - Download the route for further analysis

**Happy routing!** 🗺️⚡

