"""
Setup script to copy shapefiles from Downloads folder to project data folder
This ensures the app uses your real Uganda GIS data
"""
import os
import shutil
from pathlib import Path

# Source: Your Downloads folder
SOURCE_FOLDER = Path(r"C:\Users\PC1\Downloads\shape files")

# Destination: Project data folder
DEST_FOLDER = Path(r"d:\transmission_routing_tool\data")

# Map of layer names to shapefile patterns
SHAPEFILE_MAPPING = {
    # Elevation/Contours
    'elevation': 'Ug_Contours_Utedited_2007_Proj',
    
    # Schools (Education)
    'schools': 'Ug_Schools ORIGINAL',
    
    # Roads
    'roads': 'Ug_Roads_UNRA_2012',
    
    # Rivers
    'rivers': 'Ug_Rivers-original',
    
    # Wetlands
    'wetlands': 'Wetlands1994',
    
    # Lakes
    'lakes': 'Ug_Lakes',
    
    # Protected Areas
    'protected_areas': 'protected_areas_60',
    
    # Health Facilities
    'health': 'health_facilities',
    
    # Commercial Facilities
    'commercial': 'commercial_facilities',
    
    # Trading Centres
    'trading_centres': 'Ug_Trading_Centres ORIGINAL',
    
    # Education Facilities (alternative)
    'education': 'education_facilities',
}

def copy_shapefiles():
    """Copy shapefiles from Downloads to project data folder"""
    
    print("=" * 60)
    print("Setting up Uganda GIS Data from Downloads Folder")
    print("=" * 60)
    
    # Check source folder exists
    if not SOURCE_FOLDER.exists():
        print(f"❌ Source folder not found: {SOURCE_FOLDER}")
        return False
    
    # Create destination subfolders
    subfolders = [
        'elevation',
        'schools', 
        'roads',
        'rivers',
        'wetlands',
        'lakes',
        'protected_areas',
        'health_facilities',
        'commercial_facilities',
        'trading_centres',
        'education'
    ]
    
    for folder in subfolders:
        dest_path = DEST_FOLDER / folder
        dest_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created folder: {dest_path}")
    
    # Copy shapefiles
    shapefile_extensions = ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.cpg', '.qpj']
    
    for layer_name, pattern in SHAPEFILE_MAPPING.items():
        print(f"\n📁 Processing: {layer_name}")
        
        # Find all files matching the pattern
        source_files = list(SOURCE_FOLDER.glob(f"{pattern}.*"))
        
        if not source_files:
            print(f"  ⚠️  No files found matching: {pattern}")
            continue
        
        # Determine destination folder
        if layer_name == 'health':
            dest_subfolder = 'health_facilities'
        elif layer_name == 'commercial':
            dest_subfolder = 'commercial_facilities'
        elif layer_name == 'trading_centres':
            dest_subfolder = 'trading_centres'
        else:
            dest_subfolder = layer_name
        
        dest_path = DEST_FOLDER / dest_subfolder
        
        # Copy files
        copied_count = 0
        for source_file in source_files:
            ext = source_file.suffix.lower()
            if ext in shapefile_extensions:
                dest_file = dest_path / source_file.name
                shutil.copy2(source_file, dest_file)
                print(f"  ✓ Copied: {source_file.name}")
                copied_count += 1
        
        print(f"  ✅ Copied {copied_count} files for {layer_name}")
    
    print("\n" + "=" * 60)
    print("✅ Shapefile setup complete!")
    print("=" * 60)
    print(f"\nSource: {SOURCE_FOLDER}")
    print(f"Destination: {DEST_FOLDER}")
    print("\nNext steps:")
    print("1. Restart your Flask application")
    print("2. Check the layer checkboxes in the map")
    print("3. Layers will now use your real Uganda data!")
    
    return True

if __name__ == '__main__':
    copy_shapefiles()
