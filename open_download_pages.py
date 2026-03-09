"""
Open GIS data download pages in browser
This script opens all the recommended data sources in your browser
"""
import webbrowser
import time

def open_data_sources():
    """Open all GIS data download pages"""
    
    print("=" * 70)
    print("🌍 OPENING UGANDA GIS DATA DOWNLOAD PAGES")
    print("=" * 70)
    
    sources = [
        {
            'name': 'Geofabrik Uganda (EASIEST - RECOMMENDED)',
            'url': 'https://download.geofabrik.de/africa/uganda.html',
            'description': 'Download: uganda-latest-free.shp.zip (~50 MB)',
            'data': 'Roads, buildings, water, land use, power, airports'
        },
        {
            'name': 'HOT Export Tool (CUSTOM EXPORTS)',
            'url': 'https://export.hotosm.org/',
            'description': 'Create custom export for your specific area',
            'data': 'All OSM data - customizable'
        },
        {
            'name': 'USGS EarthExplorer (DEM/ELEVATION)',
            'url': 'https://earthexplorer.usgs.gov/',
            'description': 'Download SRTM 30m elevation data',
            'data': 'Digital Elevation Model (terrain/topology)'
        },
        {
            'name': 'DIVA-GIS Uganda Data',
            'url': 'https://www.diva-gis.org/gdata',
            'description': 'Select Country: Uganda, download various datasets',
            'data': 'Administrative, roads, water, elevation'
        }
    ]
    
    print("\nI will open these pages in your browser:\n")
    
    for i, source in enumerate(sources, 1):
        print(f"{i}. {source['name']}")
        print(f"   URL: {source['url']}")
        print(f"   What to download: {source['description']}")
        print(f"   Data types: {source['data']}")
        print()
    
    input("Press ENTER to open all pages in your browser...")
    
    print("\n📂 Opening pages...")
    for source in sources:
        print(f"  Opening: {source['name']}")
        webbrowser.open(source['url'])
        time.sleep(2)  # Wait 2 seconds between opening tabs
    
    print("\n✅ All pages opened!")
    print("\n" + "=" * 70)
    print("DOWNLOAD INSTRUCTIONS")
    print("=" * 70)
    print("""
1. GEOFABRIK (EASIEST - START HERE):
   - Click "uganda-latest-free.shp.zip" to download
   - Extract the ZIP file
   - You'll get multiple .shp files for different layers
   
2. HOT EXPORT TOOL (OPTIONAL - FOR CUSTOM AREA):
   - Login with OpenStreetMap account (free)
   - Click "Start Exporting"
   - Draw box around your project area
   - Select features: buildings, roads, water, amenities, power
   - Download as Shapefile
   
3. USGS EARTHEXPLORER (FOR ELEVATION DATA):
   - Create free account
   - Search for "Uganda" or enter coordinates
   - Select "SRTM 1 Arc-Second Global"
   - Download tiles covering your area
   
4. DIVA-GIS (ALTERNATIVE SOURCE):
   - Select "Uganda" from country dropdown
   - Download: Roads, Water, Elevation
   - Format: Shapefile

After downloading, run: python download_uganda_data.py
Or manually organize files into data/ folders.
    """)

if __name__ == "__main__":
    open_data_sources()

