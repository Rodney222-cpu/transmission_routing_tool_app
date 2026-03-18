# 🗺️ Map Layers - Quick Reference Guide
## For Project Owners & Stakeholders

---

## 📊 **THE 6 MAIN LAYERS**

### **1. Land Use (WorldCover)** 🌍
**What it shows:** What's on the ground (forests, farms, buildings, water)

| Color | Type | Cost | Why? |
|-------|------|------|------|
| 🟢 Green | Grassland | ⭐ BEST | Easy to build, cheap |
| 🟢 Dark Green | Forest | ⚠️ Medium | Need to clear trees |
| 🟡 Yellow | Farmland | ⚠️ Medium | Compensation to farmers |
| ⚫ Gray | Buildings | ❌ AVOID | People live there! |
| 🔵 Blue | Water | ❌ CANNOT CROSS | Lakes, rivers |
| 🟤 Brown | Wetlands | ⚠️ Difficult | Environmental concerns |

**Simple Rule:** Green grassland = good, Buildings/water = bad

---

### **2. Topography (Hills & Valleys)** ⛰️
**What it shows:** How steep the land is

| Slope | Difficulty | Cost | Example |
|-------|------------|------|---------|
| 0-5° | Flat | ⭐ BEST | Like a football field |
| 5-15° | Gentle | ⚠️ OK | Like a small hill |
| 15-25° | Moderate | ⚠️ Difficult | Like a steep road |
| 25-30° | Steep | ❌ Very Hard | Like climbing stairs |
| >30° | Very Steep | ❌ CANNOT BUILD | Like a cliff |

**Simple Rule:** Flat land = easy to build, Mountains = very difficult

---

### **3. Settlements (Cities & Villages)** 🏘️
**What it shows:** Where people live

| Distance | Cost | Why? |
|----------|------|------|
| Inside settlement | ❌ CANNOT BUILD | People's homes! |
| < 100m away | ❌ Very High | Too close to homes |
| 100-500m away | ⚠️ High | Need safety buffer |
| 500-1000m away | ⚠️ Medium | Some concerns |
| > 1000m away | ⭐ BEST | Safe distance |

**Simple Rule:** Stay far away from where people live

---

### **4. Protected Areas (National Parks)** 🌳
**What it shows:** Nature reserves, wildlife areas

| Type | Cost | Why? |
|------|------|------|
| National Park | ❌ VERY HIGH | Need special permits |
| Wildlife Reserve | ❌ VERY HIGH | Environmental laws |
| Forest Reserve | ⚠️ High | Restricted access |
| Outside protected areas | ⭐ BEST | No restrictions |

**Examples in Uganda:**
- Murchison Falls National Park
- Queen Elizabeth National Park
- Budongo Forest Reserve

**Simple Rule:** Avoid national parks - very expensive permits and delays

---

### **5. Roads** 🛣️
**What it shows:** Highways, streets, tracks

| Road Type | Cost | Why? |
|-----------|------|------|
| Near highway | ⭐ BEST | Easy access for trucks |
| Near local road | ⭐ Good | Can bring materials |
| Near track | ⚠️ OK | Some access |
| No road nearby | ❌ Difficult | Hard to reach |

**Simple Rule:** Near roads = GOOD (easier construction access)

---

### **6. Water Bodies** 💧
**What it shows:** Lakes, rivers, wetlands

| Type | Cost | Why? |
|------|------|------|
| Small stream | ⚠️ Medium | Can cross with special towers |
| Large river | ❌ Very High | Expensive river crossing |
| Lake | ❌ CANNOT CROSS | Must go around |
| Wetland | ⚠️ High | Environmental concerns |

**Simple Rule:** Avoid water - expensive to cross

---

## 🎯 **HOW THE SYSTEM USES LAYERS**

### **Step 1: Combine All Layers**
The system looks at ALL 6 layers at the same time for every point on the map.

### **Step 2: Calculate Cost**
Each point gets a "cost score" based on:
- Land use (forest vs grassland)
- Slope (flat vs steep)
- Distance to settlements
- Inside protected area?
- Near roads?
- Water bodies?

### **Step 3: Find Cheapest Path**
The algorithm finds the path with the **lowest total cost** from start to end.

---

## 📊 **AHP WEIGHTS (Importance of Each Layer)**

Think of weights as **how much attention** we pay to each layer:

| Layer | Weight | Priority | What It Means |
|-------|--------|----------|---------------|
| Protected Areas | 28.9% | #1 Highest | MOST important to avoid |
| Settlements | 20.0% | #2 Very High | Very important to avoid |
| Vegetation | 15.6% | #3 High | Important to consider |
| Land Use | 13.3% | #4 Medium | Moderately important |
| Water | 8.9% | #5 Medium | Consider when present |
| Topography | 6.7% | #6 Lower | Less critical (Uganda is mostly flat) |

**Why these weights?**
- Based on UETCL's official standards
- Reflects real-world priorities
- Balances cost, environment, and safety

---

## 💰 **COST EXAMPLES**

### **Example 1: GOOD Route** ✅
- **Land:** Grassland (cost: 1.0)
- **Slope:** Flat, 3° (cost: 1.0)
- **Settlements:** 2km away (cost: 1.0)
- **Protected:** Outside parks (cost: 1.0)
- **Roads:** 500m from highway (cost: 0.8)
- **Water:** No water nearby (cost: 1.0)
- **TOTAL COST:** 0.69 ⭐ **EXCELLENT!**

### **Example 2: BAD Route** ❌
- **Land:** Forest (cost: 3.0)
- **Slope:** Steep, 28° (cost: 5.0)
- **Settlements:** 300m from village (cost: 5.0)
- **Protected:** Outside parks (cost: 1.0)
- **Roads:** 5km from road (cost: 2.0)
- **Water:** Near river (cost: 3.0)
- **TOTAL COST:** 2.02 ❌ **AVOID!**

### **Example 3: VERY BAD Route** ❌❌
- **Land:** Buildings (cost: 10.0)
- **Slope:** Very steep, 35° (cost: 100.0)
- **Settlements:** Inside town (cost: 100.0)
- **Protected:** Inside national park (cost: 10.0)
- **Roads:** No access (cost: 2.0)
- **Water:** Lake crossing (cost: 100.0)
- **TOTAL COST:** 2.81 ❌❌ **IMPOSSIBLE!**

---

## 🎓 **SUMMARY FOR BEGINNERS**

### **What the system does:**
1. Looks at the map
2. Checks all 6 layers for every point
3. Calculates cost for each point
4. Finds the cheapest path from start to end
5. Shows you the best route!

### **What makes a good route:**
- ✅ Flat grassland
- ✅ Far from people
- ✅ Outside protected areas
- ✅ Near roads
- ✅ Avoids water

### **What makes a bad route:**
- ❌ Steep mountains
- ❌ Through cities
- ❌ Inside national parks
- ❌ No road access
- ❌ Crossing lakes

---

## 📖 **FOR MORE DETAILS**

See the full guide: `LAYERS_EXPLAINED_FOR_BEGINNERS.md`

---

**Questions? Just remember:**
- **Green grassland = Good** 🟢
- **Buildings/water = Bad** ⚫🔵
- **Flat = Good** ⛰️
- **Near roads = Good** 🛣️
- **Far from people = Good** 🏘️
- **Outside parks = Good** 🌳

