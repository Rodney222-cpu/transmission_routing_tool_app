"""
Verify and map shapefiles from Downloads folder to correct layers
This script ensures the correct shapefiles are in the right data folders
"""
import os
import shutil
from pathlib import Path

# Source: Downloads folder
DOWNLOADS_SHAPEFILES = Path.home() / "Downloads" / "Shape files"

# Destination: Project data folder
DATA_FOLDER = Path("d:/transmission_routing_tool/data")

# Mapping of layer name to correct shapefile
LAYER_MAPPING = {
    'protected_areas': {
        'shapefile': 'protected_areas_60.shp',
        'destination': DATA_FOLDER / 'protected_areas',
        'description': 'Protected Areas (National Parks, Reserves)'
    },
    'rivers': {
        'shapefile': 'Ug_Rivers-original.shp',
        'destination': DATA_FOLDER / 'rivers',
        'description': 'Rivers and Streams'
    },
    'wetlands': {
        'shapefile': 'Wetlands1994.shp',
        'destination': DATA_FOLDER / 'wetlands',
        'description': 'Wetlands (1994 data)'
    },
    'roads': {
        'shapefile': 'Ug_Roads_UNRA_2012.shp',
        'destination': DATA_FOLDER / 'roads',
        'description': 'Roads (UNRA 2012)'
    },
    'elevation': {
        'shapefile': 'Ug_Contours_Utedited_2007_Proj.shp',
        'destination': DATA_FOLDER / 'elevation',
        'description': 'Elevation Contours'
    },
    'lakes': {
        'shapefile': 'Ug_Lakes.shp',
        'destination': DATA_FOLDER / 'lakes',
        'description': 'Lakes and Large Water Bodies'
    },
    'settlements': {
        'shapefile': 'Ug_Schools ORIGINAL.shp',
        'destination': DATA_FOLDER / 'schools',
        'description': 'Settlements (using Schools data)'
    },
    'land_use': {
        'shapefile': 'gis_osm_landuse_a_free_1.shp',
        'destination': DATA_FOLDER / 'land_use',
        'description': 'Land Use/Land Cover'
    },
    'uganda_districts': {
        'shapefile': 'uganda_districts_2019_i.shp',
        'destination': DATA_FOLDER / 'uganda_districts',
        'description': 'Uganda District Boundaries'
    },
    'hospitals': {
        'shapefile': 'health_facilities.shp',
        'destination': DATA_FOLDER / 'health_facilities',
        'description': 'Health Facilities/Hospitals'
    },
    'commercial': {
        'shapefile': 'commercial_facilities.shp',
        'destination': DATA_FOLDER / 'commercial_facilities',
        'description': 'Commercial Facilities'
    },
}

def verify_shapefiles():
    """Verify that all shapefiles exist in the correct locations"""
    
    print("=" * 80)
    print("VERIFYING SHAPEFILE MAPPING")
    print("=" * 80)
    
    all_ok = True
    
    for layer_name, config in LAYER_MAPPING.items():
        shapefile_name = config['shapefile']
        destination = config['destination']
        description = config['description']
        
        # Check if destination folder exists
        if not destination.exists():
            print(f"\n⚠️  Folder not found: {destination}")
            print(f"   Creating folder...")
            destination.mkdir(parents=True, exist_ok=True)
        
        # Check if shapefile exists in destination
        shapefile_path = destination / shapefile_name
        
        if shapefile_path.exists():
            print(f"\n✅ {layer_name}: {description}")
            print(f"   📁 {shapefile_path}")
            
            # Check for companion files (.dbf, .shx, .prj)
            base_name = shapefile_path.stem
            companion_extensions = ['.dbf', '.shx', '.prj']
            missing_companions = []
            
            for ext in companion_extensions:
                companion_path = destination / f"{base_name}{ext}"
                if not companion_path.exists():
                    missing_companions.append(ext)
            
            if missing_companions:
                print(f"   ⚠️  Missing companion files: {', '.join(missing_companions)}")
            else:
                print(f"   ✓ All companion files present")
        else:
            print(f"\n❌ {layer_name}: {description}")
            print(f"   ❌ Shapefile NOT FOUND: {shapefile_path}")
            all_ok = False
            
            # Check if it exists in Downloads
            downloads_path = DOWNLOADS_SHAPEFILES / shapefile_name
            if downloads_path.exists():
                print(f"   📥 Found in Downloads: {downloads_path}")
                print(f"   💡 Would you like to copy it? (Manual action required)")
            else:
                print(f"   ❌ Not found in Downloads either")
    
    print("\n" + "=" * 80)
    if all_ok:
        print("✅ ALL SHAPEFILES VERIFIED SUCCESSFULLY!")
    else:
        print("⚠️  SOME SHAPEFILES ARE MISSING - Manual intervention required")
    print("=" * 80)
    
    return all_ok

def print_layer_summary():
    """Print a summary of layer to shapefile mapping"""
    
    print("\n" + "=" * 80)
    print("LAYER TO SHAPEFILE MAPPING SUMMARY")
    print("=" * 80)
    print("\nThese are the layers used in sliders and checkboxes:\n")
    
    print(f"{'Layer Name':<25} {'Shapefile':<50} {'Status'}")
    print("-" * 80)
    
    for layer_name, config in LAYER_MAPPING.items():
        shapefile_name = config['shapefile']
        destination = config['destination']
        shapefile_path = destination / shapefile_name
        
        status = "✅" if shapefile_path.exists() else "❌"
        print(f"{layer_name:<25} {shapefile_name:<50} {status}")
    
    print("\n" + "=" * 80)
    print("COST SURFACE LAYERS (8 layers with sliders):")
    print("=" * 80)
    
    cost_surface_layers = [
        'protected_areas', 'rivers', 'wetlands', 'roads',
        'elevation', 'lakes', 'settlements', 'land_use'
    ]
    
    for layer_name in cost_surface_layers:
        config = LAYER_MAPPING[layer_name]
        print(f"  • {layer_name}: {config['description']}")
        print(f"    → {config['shapefile']}")
    
    print("\n" + "=" * 80)
    print("CHECKBOX LAYERS (11 layers):")
    print("=" * 80)
    
    checkbox_layers = [
        'uganda_districts', 'protected_areas', 'rivers', 'wetlands',
        'lakes', 'roads', 'elevation', 'settlements',
        'hospitals', 'commercial', 'land_use'
    ]
    
    for layer_name in checkbox_layers:
        if layer_name in LAYER_MAPPING:
            config = LAYER_MAPPING[layer_name]
            print(f"  • {layer_name}: {config['description']}")
            print(f"    → {config['shapefile']}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    verify_shapefiles()
    print_layer_summary()
