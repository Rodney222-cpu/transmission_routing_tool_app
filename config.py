"""
Configuration settings for Transmission Line Routing Optimization Tool
Olwiyo (Uganda) - South Sudan 400kV Interconnection Case Study
"""
import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration"""

    # Company Branding
    COMPANY_NAME = 'Uganda Electricity Transmission Company Limited'
    COMPANY_SHORT_NAME = 'UETCL'
    COMPANY_LOGO = 'uetcl_logo.png'  # Place in static/images/

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'transmission_routing.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    ALLOWED_EXTENSIONS = {'tif', 'tiff', 'shp', 'geojson', 'json'}
    
    # Map basemap API keys (optional — set in .env, never commit real keys)
    MAPTILER_API_KEY = os.environ.get('MAPTILER_API_KEY', '')
    THUNDERFOREST_API_KEY = os.environ.get('THUNDERFOREST_API_KEY', '')

    # GIS Data paths - Real Uganda Shapefiles
    DATA_FOLDER = os.path.join(basedir, 'data')
    DEM_FOLDER = os.path.join(DATA_FOLDER, 'dem')
    LANDCOVER_FOLDER = os.path.join(DATA_FOLDER, 'landcover')
    SETTLEMENTS_FOLDER = os.path.join(DATA_FOLDER, 'settlements')
    PROTECTED_AREAS_FOLDER = os.path.join(DATA_FOLDER, 'protected_areas')
    ROADS_FOLDER = os.path.join(DATA_FOLDER, 'roads')
    EDUCATION_FOLDER = os.path.join(DATA_FOLDER, 'education')
    POWER_INFRASTRUCTURE_FOLDER = os.path.join(DATA_FOLDER, 'power_infrastructure')
    WATERBODIES_FOLDER = os.path.join(DATA_FOLDER, 'waterbodies')
    FORESTS_FOLDER = os.path.join(DATA_FOLDER, 'forests')
    AIRPORTS_FOLDER = os.path.join(DATA_FOLDER, 'airports')
    
    # NEW: Additional Uganda shapefile layers (from Downloads folder)
    ELEVATION_FOLDER = os.path.join(DATA_FOLDER, 'elevation')  # Contours
    SCHOOLS_FOLDER = os.path.join(DATA_FOLDER, 'schools')  # Schools
    RIVERS_FOLDER = os.path.join(DATA_FOLDER, 'rivers')  # Rivers
    WETLANDS_FOLDER = os.path.join(DATA_FOLDER, 'wetlands')  # Wetlands
    LAKES_FOLDER = os.path.join(DATA_FOLDER, 'lakes')  # Lakes
    HEALTH_FACILITIES_FOLDER = os.path.join(DATA_FOLDER, 'health_facilities')  # Health
    COMMERCIAL_FACILITIES_FOLDER = os.path.join(DATA_FOLDER, 'commercial_facilities')  # Commercial
    TRADING_CENTRES_FOLDER = os.path.join(DATA_FOLDER, 'trading_centres')  # Trading Centres
    UGANDA_DISTRICTS_FOLDER = os.path.join(DATA_FOLDER, 'uganda_districts')  # Districts
    LAND_USE_FOLDER = os.path.join(DATA_FOLDER, 'land_use')  # Land Use
    
    # Case Study: Olwiyo - South Sudan Line Specifications
    VOLTAGE_LEVEL = 400  # kV
    TOWER_TYPE = 'lattice'  # Steel lattice towers
    
    # Corridor specifications (in meters)
    RIGHT_OF_WAY = 10  # meters
    WAYLEAVE_EACH_SIDE = 25  # meters
    TOTAL_CORRIDOR_WIDTH = RIGHT_OF_WAY + (2 * WAYLEAVE_EACH_SIDE)  # 60 meters
    
    # Engineering constraints for 400kV lattice towers
    # Terrain-based span lengths
    MIN_TOWER_SPAN_DIFFICULT = 250  # meters (difficult terrain)
    MAX_TOWER_SPAN_DIFFICULT = 300  # meters (difficult terrain)
    MIN_TOWER_SPAN_FLAT = 300  # meters (flat terrain)
    MAX_TOWER_SPAN_FLAT = 450  # meters (flat terrain)
    TYPICAL_TOWER_SPAN = 350  # meters

    # Legacy values for backward compatibility
    MIN_TOWER_SPAN = 250  # meters
    MAX_TOWER_SPAN = 450  # meters

    # Terrain classification thresholds
    DIFFICULT_TERRAIN_SLOPE = 15  # degrees - slopes above this are "difficult"

    MAX_SLOPE_ANGLE = 30  # degrees
    MIN_GROUND_CLEARANCE = 7.6  # meters (for 400kV)
    
    # AHP Default Weights (can be adjusted by user)
    # These weights follow the Analytic Hierarchy Process methodology
    # Based on Table 4-12 from the Olwiyo-South Sudan 400kV Interconnection Report (Page 90)
    DEFAULT_AHP_WEIGHTS = {
        'settlements': 0.20,        # PEOPLE (20.0%) - Proximity to populated areas
        'protected_areas': 0.289,   # HABITAT (17.8%) + FAUNA (11.1%) - Sensitive habitats & wildlife
        'vegetation': 0.156,        # VEGETATION (15.6%) - Forests and vegetation
        'land_use': 0.133,          # LAND (13.3%) - Agriculture, grazing, urban/semi-urban
        'water': 0.089,             # WATER (8.9%) - Wetlands and riverine habitats
        'topography': 0.067,        # LANDSCAPE (6.7%) - Natural landscape alteration
        'cultural_heritage': 0.044, # PHYSICAL CULTURAL HERITAGE (4.4%) - Sacred/cultural sites
        'public_infrastructure': 0.022  # PUBLIC INFRASTRUCTURES (2.2%) - Schools, health posts, etc.
    }
    # Total = 1.000 (100%)
    
    # Cost factors for different land use types (Uganda-specific)
    LAND_USE_COSTS = {
        'agricultural': 1.5,
        'built_up': 10.0,
        'wetlands': 5.0,
        'forest': 3.0,
        'grassland': 1.0,
        'water_large': 100.0,  # Large water bodies (lakes) - avoid
        'water_small': 15.0,   # Small rivers/streams - crossable but expensive
        'water': 15.0,         # Default water cost - allow crossing
        'protected_area': 8.0
    }

    # Water body classification (in meters)
    SMALL_WATER_BODY_WIDTH = 50  # Rivers/streams under 50m can be crossed
    LARGE_WATER_BODY_WIDTH = 50  # Water bodies over 50m should be avoided
    
    # Slope cost multipliers
    SLOPE_COSTS = {
        'flat': 1.0,        # 0-5 degrees
        'gentle': 1.5,      # 5-15 degrees
        'moderate': 2.5,    # 15-25 degrees
        'steep': 5.0,       # 25-30 degrees
        'very_steep': 100.0 # >30 degrees (avoid)
    }
    
    # Settlement proximity costs (distance in meters)
    SETTLEMENT_BUFFER_COSTS = {
        0: 100.0,      # Within settlement
        100: 10.0,     # 0-100m
        500: 5.0,      # 100-500m
        1000: 2.0,     # 500-1000m
        2000: 1.0      # >1000m
    }

    # Education facility proximity costs (distance in meters)
    EDUCATION_BUFFER_COSTS = {
        0: 100.0,      # Within facility
        50: 20.0,      # 0-50m (safety zone)
        200: 10.0,     # 50-200m
        500: 3.0,      # 200-500m
        1000: 1.0      # >500m
    }

    # Power infrastructure proximity costs
    POWER_INFRASTRUCTURE_COSTS = {
        'substation': 0.5,      # Near substations is good (connection point)
        'transmission_line': 2.0,  # Near existing lines (corridor sharing)
        'power_plant': 0.8,     # Near power plants (potential connection)
        'tower': 1.5            # Near existing towers
    }

    # Airport/Transportation proximity costs (distance in meters)
    AIRPORT_BUFFER_COSTS = {
        0: 100.0,      # Within airport
        500: 50.0,     # 0-500m (flight path safety)
        1000: 20.0,    # 500-1000m
        2000: 5.0,     # 1-2km
        5000: 1.0      # >2km
    }
    
    # Cost Estimation Constants (400kV Transmission Line - Uganda)
    # All costs in USD
    COST_ESTIMATION = {
        # Tower costs by terrain type
        'tower_cost_flat': 45000,        # USD per tower (flat terrain)
        'tower_cost_difficult': 65000,   # USD per tower (difficult terrain)
        'tower_cost_average': 55000,     # USD per tower (average)

        # Conductor costs (per km)
        'conductor_cost_per_km': 85000,  # USD per km (ACSR conductor for 400kV)

        # Foundation costs by terrain type (per tower)
        'foundation_flat': 15000,        # USD (flat terrain - simple foundation)
        'foundation_moderate': 25000,    # USD (moderate terrain)
        'foundation_difficult': 40000,   # USD (difficult terrain - rock/steep)

        # Installation and labor (per km)
        'installation_per_km': 120000,   # USD per km (includes labor, equipment)

        # Right-of-Way acquisition (per km)
        'row_acquisition_per_km': 50000, # USD per km (average for Uganda)

        # Engineering and design (percentage of total)
        'engineering_percentage': 0.08,  # 8% of construction cost

        # Contingency (percentage of total)
        'contingency_percentage': 0.15,  # 15% contingency

        # Total cost multiplier for terrain
        'terrain_multiplier_flat': 1.0,
        'terrain_multiplier_moderate': 1.2,
        'terrain_multiplier_difficult': 1.5
    }

    # Data source information
    DATA_SOURCES = {
        'dem': 'USGS SRTM 30m',
        'landcover': 'ESA WorldCover 10m',
        'protected_areas': 'NEMA/NFA/UWA Uganda',
        'settlements': 'OpenStreetMap Uganda',
        'roads': 'OpenStreetMap Uganda'
    }
    
    # Olwiyo Substation coordinates (example - adjust to actual)
    OLWIYO_SUBSTATION = {
        'lat': 3.3833,
        'lon': 32.5667,
        'name': 'Olwiyo Substation'
    }
    
    # South Sudan border point (Elegu)
    SOUTH_SUDAN_BORDER = {
        'lat': 3.5833,
        'lon': 32.1167,
        'name': 'South Sudan Border (Elegu)'
    }
    
    # Map settings
    DEFAULT_MAP_CENTER = [3.4833, 32.3417]  # Between Olwiyo and border
    DEFAULT_MAP_ZOOM = 10

    # Coordinate reference systems (for uniformity and simulation)
    # Display and GeoJSON use WGS 84 (lat/lon)
    MAP_CRS = 'EPSG:4326'  # WGS 84 - used for all map and API coordinates
    # For simulation: Eastings, Northings, elevation (Uganda UTM zone 36N)
    PREFERRED_PROJECTED_CRS = 'EPSG:21096'  # UTM zone 36N for Uganda
    CRS_DESCRIPTION = 'WGS 84 (EPSG:4326). Export in Eastings, Northings, elevation (UTM 36N, EPSG:21096) for simulation.'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

