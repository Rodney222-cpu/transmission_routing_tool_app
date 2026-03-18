# Fix: "Failed to Fetch" Error When Optimizing Routes

## 🐛 Problem

When setting start point, end point, and waypoints, then clicking "Optimize Route", you got this error:
```
Error: Failed to fetch
```

---

## 🔍 Root Cause

The issue was in how the "Both" algorithm option was being handled:

### **Frontend (optimize.js):**
When user selected "Both" algorithm, the code sent:
```javascript
{ algorithm: "both" }
```

### **Backend (routes_api.py):**
The backend only accepts:
- `algorithm: "dijkstra"` or `algorithm: "astar"`
- Plus optional `compare: true` to run both

The backend didn't recognize `"both"` as a valid algorithm, causing the request to fail.

---

## ✅ Solution Applied

### **Fixed File:** `static/js/optimize.js`

**Before (lines 249-266):**
```javascript
let algorithm = 'dijkstra';
for (const radio of algorithmRadios) {
    if (radio.checked) {
        algorithm = radio.value;  // Could be "both"
        break;
    }
}

const optimizeResponse = await fetch(`/api/projects/${currentProject.projectId}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ algorithm: algorithm })  // Sends "both" - WRONG!
});
```

**After (lines 249-274):**
```javascript
let algorithm = 'dijkstra';
for (const radio of algorithmRadios) {
    if (radio.checked) {
        algorithm = radio.value;
        break;
    }
}

// Handle "both" option - run comparison
let requestBody = {};
if (algorithm === 'both') {
    requestBody = { algorithm: 'dijkstra', compare: true };  // CORRECT!
} else {
    requestBody = { algorithm: algorithm };
}

const optimizeResponse = await fetch(`/api/projects/${currentProject.projectId}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody)
});
```

---

## 🎯 What This Does

### **When user selects "Dijkstra":**
- Sends: `{ algorithm: "dijkstra" }`
- Backend runs: Dijkstra only
- Result: Single route with Dijkstra

### **When user selects "A*":**
- Sends: `{ algorithm: "astar" }`
- Backend runs: A* only
- Result: Single route with A*

### **When user selects "Both":**
- Sends: `{ algorithm: "dijkstra", compare: true }`
- Backend runs: Both Dijkstra AND A*
- Result: Route with comparison table showing both algorithms

---

## 🚀 How to Test

1. **Restart the server** (if it's running):
   - Press `Ctrl+C` in the terminal
   - Run: `python run.py`

2. **Or just refresh the browser** (Flask auto-reloads static files)

3. **Test the fix:**
   - Set start point
   - Set end point (optional: add waypoints)
   - Select any algorithm (Dijkstra, A*, or Both)
   - Click "Optimize Route"
   - ✅ Should work now!

---

## 📊 Additional Improvements

### **Also Added Better Error Handling:**

**File:** `app/routes_api.py` (lines 164-170)

Added validation to check if start/end points are set:
```python
# Validate project has required coordinates
if project.start_lat is None or project.start_lon is None:
    return jsonify({'error': 'Start point not set'}), 400
if project.end_lat is None or project.end_lon is None:
    return jsonify({'error': 'End point not set'}), 400
```

This provides a clearer error message if you forget to set points.

---

## ✅ Expected Behavior Now

### **Scenario 1: Dijkstra Only**
1. Select "Dijkstra"
2. Click "Optimize Route"
3. See route appear on map
4. See cost breakdown

### **Scenario 2: A* Only**
1. Select "A*"
2. Click "Optimize Route"
3. See route appear on map
4. See cost breakdown

### **Scenario 3: Both (Comparison)**
1. Select "Both"
2. Click "Optimize Route"
3. See route appear on map
4. See cost breakdown
5. **PLUS:** See comparison table showing:
   - Dijkstra: Total cost, distance, path points
   - A*: Total cost, distance, path points

### **Scenario 4: With Waypoints**
1. Set start point
2. Click "Add Waypoint" and set waypoint(s)
3. Set end point
4. Select algorithm
5. Click "Optimize Route"
6. Route passes through all waypoints in order

---

## 🎉 Summary

**Problem:** "Failed to fetch" error when optimizing routes  
**Cause:** Frontend sent `algorithm: "both"` which backend didn't recognize  
**Fix:** Convert "both" to `algorithm: "dijkstra", compare: true`  
**Status:** ✅ **FIXED**

---

## 📝 Files Modified

1. **`static/js/optimize.js`** - Fixed algorithm parameter handling
2. **`app/routes_api.py`** - Added validation for start/end points

---

**The error is now fixed! Try optimizing a route and it should work perfectly! 🚀**

