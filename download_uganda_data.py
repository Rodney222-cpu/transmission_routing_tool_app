"""
Automated script to download Uganda GIS data
This script downloads free GIS data from Geofabrik and organizes it
"""
import os
import urllib.request
import zipfile
import shutil
from pathlib import Path

# URLs for Uganda GIS data
GEOFABRIK_UGANDA_SHAPEFILE = "https://download.geofabrik.de/africa/uganda-latest-free.shp.zip"

# Data directory
DATA_DIR = Path("data")

def create_data_folders():
    """Create all necessary data folders"""
    folders = [
        'dem',
        'land_use',
        'settlements',
        'protected_areas',
        'roads',
        'education',
        'power_infrastructure',
        'waterbodies',
        'forests',
        'airports'
    ]
    
    for folder in folders:
        folder_path = DATA_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created folder: {folder_path}")

def download_file(url, destination):
    """Download file with progress"""
    print(f"\n📥 Downloading from: {url}")
    print(f"📁 Saving to: {destination}")
    
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, (downloaded / total_size) * 100)
        print(f"\rProgress: {percent:.1f}% ({downloaded / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB)", end='')
    
    try:
        urllib.request.urlretrieve(url, destination, progress_hook)
        print("\n✅ Download complete!")
        return True
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False

def extract_and_organize(zip_path):
    """Extract ZIP and organize files into appropriate folders"""
    print(f"\n📦 Extracting: {zip_path}")
    
    # Create temp extraction folder
    temp_dir = DATA_DIR / "temp_extract"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        print("✅ Extraction complete!")
        
        # Organize files by type
        organize_files(temp_dir)
        
        # Clean up
        shutil.rmtree(temp_dir)
        os.remove(zip_path)
        print("✅ Cleanup complete!")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")

def organize_files(source_dir):
    """Organize extracted files into appropriate folders"""
    print("\n📂 Organizing files...")
    
    # Mapping of file patterns to destination folders
    file_mappings = {
        'landuse': 'land_use',
        'buildings': 'settlements',
        'roads': 'roads',
        'water_a': 'waterbodies',
        'waterways': 'waterbodies',
        'natural': 'forests',
        'pois': 'education',  # Points of interest include schools
        'power': 'power_infrastructure',
        'transport': 'roads',
        'aeroway': 'airports'
    }
    
    # Move files to appropriate folders
    for file_path in source_dir.rglob('*.shp'):
        file_name = file_path.stem.lower()
        
        # Find matching destination
        destination_folder = None
        for pattern, folder in file_mappings.items():
            if pattern in file_name:
                destination_folder = folder
                break
        
        if destination_folder:
            # Copy all related files (.shp, .shx, .dbf, .prj, etc.)
            base_name = file_path.stem
            for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                src_file = file_path.parent / f"{base_name}{ext}"
                if src_file.exists():
                    dest_file = DATA_DIR / destination_folder / f"{base_name}{ext}"
                    shutil.copy2(src_file, dest_file)
            
            print(f"  ✅ {file_path.name} → {destination_folder}/")

def main():
    """Main download and setup function"""
    print("=" * 70)
    print("🌍 UGANDA GIS DATA DOWNLOADER")
    print("=" * 70)
    print("\nThis script will download free GIS data for Uganda from Geofabrik.")
    print("Download size: ~50-100 MB")
    print("Time required: 5-10 minutes (depending on internet speed)")
    
    # Create folders
    print("\n" + "=" * 70)
    print("STEP 1: Creating data folders")
    print("=" * 70)
    create_data_folders()
    
    # Download Uganda shapefile data
    print("\n" + "=" * 70)
    print("STEP 2: Downloading Uganda OSM data")
    print("=" * 70)
    zip_path = DATA_DIR / "uganda_osm.zip"
    
    if download_file(GEOFABRIK_UGANDA_SHAPEFILE, zip_path):
        # Extract and organize
        print("\n" + "=" * 70)
        print("STEP 3: Extracting and organizing files")
        print("=" * 70)
        extract_and_organize(zip_path)
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! GIS DATA READY TO USE")
        print("=" * 70)
        print("\nData has been organized into folders:")
        print("  - data/land_use/")
        print("  - data/settlements/")
        print("  - data/roads/")
        print("  - data/waterbodies/")
        print("  - data/forests/")
        print("  - data/power_infrastructure/")
        print("  - data/airports/")
        print("\nNext steps:")
        print("1. Download DEM data manually from USGS EarthExplorer")
        print("2. Run the optimization tool - it will use this real data!")
    else:
        print("\n❌ Download failed. Please try manual download:")
        print(f"   URL: {GEOFABRIK_UGANDA_SHAPEFILE}")

if __name__ == "__main__":
    main()

