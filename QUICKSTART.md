# Quick Start Guide

## Transmission Line Routing Optimization Tool - Olwiyo-South Sudan 400kV Line

### 1. Installation (5 minutes)

```bash
# Navigate to project directory
cd transmission_routing_tool

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup (1 minute)

```bash
# Start Python interactive shell
python

# Initialize database
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 3. Run Application (1 minute)

```bash
python run.py
```

The application will start at: **http://localhost:5000**

### 4. First Use (5 minutes)

#### Step 1: Register
1. Navigate to http://localhost:5000
2. Click "Register here"
3. Fill in:
   - Username: `admin`
   - Email: `admin@uetcl.go.ug`
   - Organization: `UETCL`
   - Password: `your_password`
4. Click "Register"

#### Step 2: Login
1. Login with your credentials
2. You'll be redirected to the dashboard

#### Step 3: Optimize Route
1. **Review Default Settings**:
   - Start: Olwiyo Substation (3.3833, 32.5667)
   - End: South Sudan Border (3.5833, 32.1167)
   - Voltage: 400 kV
   - Tower Type: Steel Lattice

2. **Adjust AHP Weights** (optional):
   - Topography: 0.25
   - Land Use: 0.30
   - Settlements: 0.20
   - Protected Areas: 0.15
   - Roads: 0.10
   - **Total must equal 1.0**

3. **Click "🚀 Optimize Route"**
   - Wait 10-30 seconds for processing
   - Route will appear on map in orange
   - Tower positions shown as blue circles

4. **Review Results**:
   - Route length (km)
   - Number of towers
   - Estimated construction cost
   - Validation errors/warnings

5. **Export Route**:
   - Click "Export Route" for GeoJSON download
   - Click "View Corridor" to see 60m corridor polygon

### 5. Customization

#### Change Route Points
1. Click "Set Start Point" or "Set End Point"
2. Click on map to set new location
3. Or drag existing markers

#### Adjust Priorities
- **Cost-focused**: Increase Land Use weight (0.40)
- **Environmental**: Increase Protected Areas weight (0.30)
- **Technical**: Increase Topography weight (0.35)

### 6. Understanding Results

#### Route Metrics
- **Route Length**: Total transmission line length in km
- **Estimated Towers**: Based on 350m typical span for 400kV
- **Total Cost**: Accumulated cost from LCP algorithm (lower is better)
- **Construction Cost**: Estimated in USD (includes terrain multiplier)

#### Validation
- **Errors**: Critical issues (e.g., span > 450m, slope > 30°)
- **Warnings**: Cautions (e.g., steep terrain, sharp turns)

#### Corridor
- **Width**: 60m total (10m RoW + 25m Wayleave each side)
- **Area**: Land acquisition requirement in hectares/acres

### 7. Troubleshooting

#### "No valid path found"
- Check that start and end points are not too far apart
- Reduce Protected Areas weight
- Ensure points are in Uganda region

#### Weights don't sum to 1.0
- Adjust sliders until sum shows green
- Use increments of 0.05

#### Map not loading
- Check internet connection (Leaflet uses CDN)
- Clear browser cache
- Try different browser

### 8. Production Deployment

For production use with real GIS data:

1. **Replace demo data** in `routes_api.py` `_create_demo_layers()` with:
   - USGS SRTM 30m DEM files
   - ESA WorldCover 10m land use rasters
   - NEMA/NFA/UWA protected areas shapefiles
   - OpenStreetMap settlements and roads

2. **Use PostgreSQL with PostGIS**:
   ```bash
   # Update .env
   DATABASE_URL=postgresql://user:pass@localhost/transmission_routing
   ```

3. **Configure production settings**:
   ```bash
   export FLASK_CONFIG=production
   export SECRET_KEY=your-secure-random-key
   ```

4. **Deploy with Gunicorn**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

### 9. Next Steps

- Load actual GIS data for Uganda
- Integrate with UETCL databases
- Add user roles and permissions
- Implement project collaboration features
- Add cost estimation refinements
- Export to engineering software (PLS-CADD, etc.)

### 10. Support

For issues or questions:
- Check README.md for detailed documentation
- Review code comments in source files
- Consult Flask and Leaflet.js documentation

---

**Happy Routing! ⚡**

