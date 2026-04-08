"""
Guide to download DEM (Elevation) data from USGS EarthExplorer for Uganda
This script provides step-by-step instructions and automated download links
"""

import webbrowser
import os

def print_step(step_number, title, description):
    """Print a formatted step"""
    print(f"\n{'='*70}")
    print(f"STEP {step_number}: {title}")
    print('='*70)
    print(description)

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║         USGS DEM DOWNLOAD GUIDE FOR UGANDA                           ║
║         SRTM 30m Elevation Data                                      ║
╚══════════════════════════════════════════════════════════════════════╝

This guide will help you download elevation data for the transmission line
routing tool. The DEM (Digital Elevation Model) is ESSENTIAL for accurate
terrain analysis.

Data Source: USGS EarthExplorer (NASA SRTM Mission)
Resolution: 30 meters
Coverage: All of Uganda
File Format: GeoTIFF (.tif)
""")
    
    # Step 1
    print_step(1, "Create a USGS Account (FREE)", """
You need a free account to download data from USGS.

1. Go to: https://ers.cr.usgs.gov/register/
2. Fill in your details:
   - Username: Choose a username
   - Password: Create a secure password
   - Email: Your email address
   - First Name, Last Name: Your name
   - Organization: "Makerere University" or "UETCL"
   - Country: "Uganda"
3. Click "Sign Up"
4. Check your email and verify your account

⚠️  IMPORTANT: Save your username and password - you'll need it for downloads!
""")
    
    # Step 2
    print_step(2, "Open USGS EarthExplorer", """
1. Go to: https://earthexplorer.usgs.gov/
2. Click "Login" in the top right
3. Enter your username and password
4. You should see the EarthExplorer search interface
""")
    
    # Step 3
    print_step(3, "Search for Uganda Area", """
In the EarthExplorer interface:

1. Under "Search Criteria" tab:
   
   Option A - Search by Coordinates (RECOMMENDED):
   - Click "Use Map" or enter coordinates manually
   - Enter these coordinates for Uganda:
     * North: 4.5 (latitude)
     * South: -1.5 (latitude)
     * East: 35.0 (longitude)
     * West: 29.5 (longitude)
   
   Option B - Search by Feature:
   - Click "Feature"
   - Select "Country" from dropdown
   - Type "Uganda"
   - Click "Show"

2. Click "Data Sets >>" button
""")
    
    # Step 4
    print_step(4, "Select SRTM Data", """
1. In the "Data Sets" tab:
   - Expand "Digital Elevation"
   - Expand "SRTM"
   - Check "SRTM 1 Arc-Second Global" (this is 30m resolution)
   
   ⚠️  Do NOT select "SRTM Void Filled" - it's lower resolution

2. Click "Results >>" button
""")
    
    # Step 5
    print_step(5, "Download the Data Files", """
You should see a list of SRTM tiles covering Uganda.

For the Olwiyo to South Sudan route, you need these tiles:

📍 TILES TO DOWNLOAD:
┌─────────────────┬────────────────────────────────────────┐
│ Tile Name       │ Coverage Area                          │
├─────────────────┼────────────────────────────────────────┤
│ N03E032         │ Olwiyo area (Northern Uganda)          │
│ N03E031         │ West of Olwiyo                         │
│ N04E032         │ North of Olwiyo (near South Sudan)     │
│ N02E032         │ South of Olwiyo                        │
└─────────────────┴────────────────────────────────────────┘

TO DOWNLOAD EACH TILE:
1. Find the tile in the results list
2. Click the "Download" button (down arrow icon)
3. Select "GeoTIFF" format (NOT JPEG or other formats)
4. Save to your computer
5. Repeat for all 4 tiles

📁 SAVE LOCATION: Create a folder and save all tiles there
   Example: C:/Users/YourName/Downloads/Uganda_DEM/
""")
    
    # Step 6
    print_step(6, "Move Files to Project", """
After downloading all 4 tiles:

1. Find your downloaded files (they will be .tif files)
   Example names:
   - srtm_32_12.tif
   - srtm_31_12.tif
   - srtm_32_13.tif
   - srtm_32_11.tif

2. Copy or move these files to the project folder:
   
   DESTINATION: transmission_routing_tool/data/dem/
   
   Path should look like:
   📁 transmission_routing_tool/
   └── 📁 data/
       └── 📁 dem/
           ├── srtm_32_12.tif
           ├── srtm_31_12.tif
           ├── srtm_32_13.tif
           └── srtm_32_11.tif

3. That's it! The tool will automatically use this data.
""")
    
    # Step 7
    print_step(7, "Verify the Installation", """
To verify the DEM data is working:

1. Restart your Flask server (if it's running):
   - Press Ctrl+C in the terminal
   - Run: python run.py

2. Open the application in browser

3. Create a route and optimize it

4. Check the results - you should see:
   - Real elevation values (not zeros)
   - Elevation profile chart showing terrain
   - Tower positions with actual elevations

✅ If you see realistic elevations (600-1500m for Northern Uganda),
   the DEM data is working correctly!
""")
    
    # Quick Links
    print("\n" + "="*70)
    print("QUICK LINKS")
    print("="*70)
    
    links = {
        "USGS Register": "https://ers.cr.usgs.gov/register/",
        "EarthExplorer": "https://earthexplorer.usgs.gov/",
        "SRTM Info": "https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-shuttle-radar-topography-mission-srtm-1-arc"
    }
    
    for name, url in links.items():
        print(f"\n{name}:")
        print(f"  {url}")
    
    # Offer to open links
    print("\n" + "="*70)
    print("OPEN LINKS IN BROWSER?")
    print("="*70)
    print("\nWould you like to open the USGS pages in your browser?")
    print("Type 'y' and press Enter to open them:")
    
    try:
        response = input("\nOpen links? (y/n): ").lower().strip()
        if response == 'y':
            print("\nOpening USGS registration page...")
            webbrowser.open(links["USGS Register"])
            print("Opening EarthExplorer...")
            webbrowser.open(links["EarthExplorer"])
            print("\n✅ Browser tabs opened!")
    except:
        pass
    
    # Summary
    print("""

╔══════════════════════════════════════════════════════════════════════╗
║                         SUMMARY                                      ║
╚══════════════════════════════════════════════════════════════════════╝

✅ WHAT YOU'RE DOWNLOADING:
   - SRTM 30m elevation data for Uganda
   - 4 tiles covering the Olwiyo-South Sudan route
   - Total size: ~100-200 MB

✅ WHY THIS DATA IS IMPORTANT:
   - Shows hills, valleys, and terrain slope
   - Helps calculate tower positions
   - Required for 400kV line engineering standards
   - Makes your presentation to UETCL credible

✅ TIME NEEDED:
   - Registration: 5 minutes
   - Download: 10-20 minutes (depending on internet)
   - Setup: 5 minutes
   - Total: ~30 minutes

✅ ALTERNATIVE IF USGS IS SLOW:
   - Use the tool without DEM (it uses realistic estimates)
   - Download DEM later when you have better internet
   - The tool works fine with estimated elevations for demonstrations

Good luck! 🌍⚡
""")

if __name__ == "__main__":
    main()
