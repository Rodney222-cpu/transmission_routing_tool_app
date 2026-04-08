"""
Automatic SRTM DEM Downloader for Uganda
Downloads all SRTM 1 Arc-Second tiles covering Uganda from USGS
"""

import os
import urllib.request
import time
from pathlib import Path

# Uganda SRTM tile coverage
# Format: (latitude, longitude) where latitude is N/S and longitude is E
UGANDA_TILES = [
    # Northern Uganda (N04)
    (4, 30), (4, 31), (4, 32), (4, 33), (4, 34), (4, 35),
    # N03 row
    (3, 30), (3, 31), (3, 32), (3, 33), (3, 34), (3, 35),
    # N02 row
    (2, 30), (2, 31), (2, 32), (2, 33), (2, 34), (2, 35),
    # N01 row
    (1, 30), (1, 31), (1, 32), (1, 33), (1, 34), (1, 35),
    # Equator (N00)
    (0, 30), (0, 31), (0, 32), (0, 33), (0, 34), (0, 35),
    # Southern Uganda (S01)
    (-1, 30), (-1, 31), (-1, 32), (-1, 33), (-1, 34), (-1, 35),
]

# Alternative source: NASA Earthdata SRTM tiles
# Using direct HTTP download from USGS SRTM server
SRTM_BASE_URL = "https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/"

# Alternative: Use OpenTopography or other sources if USGS blocks
OPENTOPO_URL_TEMPLATE = "https://portal.opentopography.org/API/globaldem?demtype=SRTMGL1&west={west}&south={south}&east={east}&north={north}&outputFormat=GTiff"


def get_tile_filename(lat, lon):
    """Generate SRTM tile filename"""
    lat_str = f"N{abs(lat):02d}" if lat >= 0 else f"S{abs(lat):02d}"
    lon_str = f"E{abs(lon):03d}" if lon >= 0 else f"W{abs(lon):03d}"
    return f"{lat_str}{lon_str}.SRTMGL1.hgt.zip"


def get_tile_name(lat, lon):
    """Get tile name without extension"""
    lat_str = f"N{abs(lat):02d}" if lat >= 0 else f"S{abs(lat):02d}"
    lon_str = f"E{abs(lon):03d}" if lon >= 0 else f"W{abs(lon):03d}"
    return f"{lat_str}{lon_str}"


def download_file(url, destination, max_retries=3):
    """Download file with retry logic"""
    for attempt in range(max_retries):
        try:
            print(f"  Downloading: {url}")
            
            # Create request with headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            
            # Download with progress
            def progress_hook(block_num, block_size, total_size):
                if total_size > 0:
                    downloaded = block_num * block_size
                    percent = min(100, (downloaded / total_size) * 100)
                    print(f"\r  Progress: {percent:.1f}%", end='')
            
            urllib.request.urlretrieve(req, destination, progress_hook)
            print()  # New line after progress
            return True
            
        except Exception as e:
            print(f"\n  Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"  Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"  Failed after {max_retries} attempts")
                return False
    return False


def download_from_opentopo(lat, lon, output_dir):
    """Download tile from OpenTopography as alternative source"""
    tile_name = get_tile_name(lat, lon)
    output_file = output_dir / f"{tile_name}.tif"
    
    if output_file.exists():
        print(f"  {tile_name}: Already exists, skipping")
        return True
    
    # Calculate bounds for this tile
    west = lon
    east = lon + 1
    south = lat - 1 if lat < 0 else lat
    north = lat + 1 if lat >= 0 else lat
    
    # For negative latitudes, adjust
    if lat < 0:
        south = lat - 1
        north = lat
    else:
        south = lat
        north = lat + 1
    
    url = OPENTOPO_URL_TEMPLATE.format(
        west=west, south=south, east=east, north=north
    )
    
    print(f"\nDownloading {tile_name} from OpenTopography...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=120) as response:
            with open(output_file, 'wb') as f:
                f.write(response.read())
        
        file_size = output_file.stat().st_size / (1024 * 1024)
        print(f"  ✓ Saved: {output_file.name} ({file_size:.1f} MB)")
        return True
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        if output_file.exists():
            output_file.unlink()
        return False


def main():
    """Main download function"""
    print("=" * 70)
    print("UGANDA SRTM DEM DOWNLOADER")
    print("=" * 70)
    print("\nThis script downloads SRTM 30m elevation data for all of Uganda")
    print("Source: OpenTopography (alternative to USGS EarthExplorer)")
    print(f"Total tiles to download: {len(UGANDA_TILES)}")
    print()
    
    # Create output directory
    output_dir = Path("data/dem")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Download location: {output_dir.absolute()}")
    print()
    
    # Download tiles
    successful = 0
    failed = 0
    skipped = 0
    
    for i, (lat, lon) in enumerate(UGANDA_TILES, 1):
        tile_name = get_tile_name(lat, lon)
        output_file = output_dir / f"{tile_name}.tif"
        
        print(f"\n[{i}/{len(UGANDA_TILES)}] {tile_name}")
        
        # Check if already exists
        if output_file.exists():
            file_size = output_file.stat().st_size / (1024 * 1024)
            print(f"  Already exists ({file_size:.1f} MB), skipping")
            skipped += 1
            continue
        
        # Download with rate limiting
        if download_from_opentopo(lat, lon, output_dir):
            successful += 1
        else:
            failed += 1
        
        # Rate limiting - be nice to the server
        if i < len(UGANDA_TILES):
            time.sleep(2)
    
    # Summary
    print("\n" + "=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"\nSuccessful: {successful}")
    print(f"Skipped (already exist): {skipped}")
    print(f"Failed: {failed}")
    print(f"\nFiles saved to: {output_dir.absolute()}")
    
    if failed > 0:
        print("\nNote: Some downloads failed. You can run this script again")
        print("to retry failed downloads (already downloaded files will be skipped)")


if __name__ == "__main__":
    main()
