"""
Direct SRTM DEM Downloader for Uganda
Downloads SRTM tiles from alternative sources that don't require authentication
"""

import os
import urllib.request
import time
import zipfile
from pathlib import Path

# SRTM tile list for Uganda (latitude, longitude)
# These are the 1-degree tiles covering Uganda
UGANDA_TILES = [
    # Northern Uganda
    (4, 30), (4, 31), (4, 32), (4, 33), (4, 34), (4, 35),
    (3, 30), (3, 31), (3, 32), (3, 33), (3, 34), (3, 35),
    (2, 30), (2, 31), (2, 32), (2, 33), (2, 34), (2, 35),
    (1, 30), (1, 31), (1, 32), (1, 33), (1, 34), (1, 35),
    (0, 30), (0, 31), (0, 32), (0, 33), (0, 34), (0, 35),
    (-1, 30), (-1, 31), (-1, 32), (-1, 33), (-1, 34), (-1, 35),
]


def get_tile_name(lat, lon):
    """Generate SRTM tile name"""
    lat_str = f"N{abs(lat):02d}" if lat >= 0 else f"S{abs(lat):02d}"
    lon_str = f"E{abs(lon):03d}" if lon >= 0 else f"W{abs(lon):03d}"
    return f"{lat_str}{lon_str}"


def download_with_progress(url, destination, timeout=120):
    """Download file with progress bar"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, (downloaded / total_size) * 100)
                print(f"\r  Progress: {percent:.1f}%", end='')
        
        # Create opener with headers
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', headers['User-Agent'])]
        urllib.request.install_opener(opener)
        
        urllib.request.urlretrieve(url, destination, progress_hook)
        print()  # New line after progress
        return True
        
    except Exception as e:
        print(f"\n  Error: {e}")
        return False


def download_from_srtm_csi(lat, lon, output_dir):
    """
    Download SRTM tile from CGIAR-CSI SRTM mirror
    This is a reliable mirror that doesn't require authentication
    """
    tile_name = get_tile_name(lat, lon)
    
    # CGIAR-CSI uses a different naming convention
    # Files are organized by latitude folders
    lat_folder = f"N{abs(lat):02d}" if lat >= 0 else f"S{abs(lat):02d}"
    
    # Try multiple sources
    sources = [
        # Source 1: CGIAR-CSI GeoTIFF (if available)
        f"https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x4/TIFF/{tile_name}.tif",
        # Source 2: Alternative SRTM mirror
        f"http://dwtkns.com/srtm30m/{tile_name}.SRTMGL1.hgt.zip",
    ]
    
    output_tif = output_dir / f"{tile_name}.tif"
    output_zip = output_dir / f"{tile_name}.zip"
    
    # Check if already exists
    if output_tif.exists():
        file_size = output_tif.stat().st_size / (1024 * 1024)
        print(f"  Already exists ({file_size:.1f} MB), skipping")
        return True, "exists"
    
    # Try each source
    for i, url in enumerate(sources):
        print(f"  Trying source {i+1}...")
        
        # Try downloading as TIF first
        if url.endswith('.tif'):
            if download_with_progress(url, output_tif):
                file_size = output_tif.stat().st_size / (1024 * 1024)
                print(f"  ✓ Downloaded: {output_tif.name} ({file_size:.1f} MB)")
                return True, "downloaded"
        
        # Try downloading as ZIP
        elif url.endswith('.zip'):
            if download_with_progress(url, output_zip):
                print(f"  Extracting...")
                try:
                    with zipfile.ZipFile(output_zip, 'r') as zip_ref:
                        zip_ref.extractall(output_dir)
                    output_zip.unlink()  # Remove zip file
                    
                    # Rename .hgt to .tif if needed
                    hgt_file = output_dir / f"{tile_name}.hgt"
                    if hgt_file.exists():
                        hgt_file.rename(output_tif)
                    
                    if output_tif.exists():
                        file_size = output_tif.stat().st_size / (1024 * 1024)
                        print(f"  ✓ Downloaded: {output_tif.name} ({file_size:.1f} MB)")
                        return True, "downloaded"
                except Exception as e:
                    print(f"  Extraction failed: {e}")
                    if output_zip.exists():
                        output_zip.unlink()
        
        # Clean up failed downloads
        if output_tif.exists():
            output_tif.unlink()
        if output_zip.exists():
            output_zip.unlink()
    
    return False, "failed"


def main():
    """Main download function"""
    print("=" * 70)
    print("UGANDA SRTM DEM DOWNLOADER")
    print("Direct download from public mirrors")
    print("=" * 70)
    print(f"\nTotal tiles to download: {len(UGANDA_TILES)}")
    print("\nNote: This uses public SRTM mirrors. Some tiles may not be available.")
    print("If downloads fail, you may need to use USGS EarthExplorer manually.")
    print()
    
    # Create output directory
    output_dir = Path("data/dem")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Download location: {output_dir.absolute()}")
    print()
    
    # Ask for confirmation
    response = input("Do you want to start downloading? (y/n): ").lower().strip()
    if response != 'y':
        print("Download cancelled.")
        return
    
    print()
    
    # Download tiles
    successful = 0
    failed = 0
    skipped = 0
    
    for i, (lat, lon) in enumerate(UGANDA_TILES, 1):
        tile_name = get_tile_name(lat, lon)
        
        print(f"\n[{i}/{len(UGANDA_TILES)}] {tile_name}")
        
        success, status = download_from_srtm_csi(lat, lon, output_dir)
        
        if status == "exists":
            skipped += 1
        elif success:
            successful += 1
        else:
            failed += 1
            print(f"  ✗ Failed to download from all sources")
        
        # Rate limiting - be nice to servers
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
        print("\n" + "-" * 70)
        print("NOTE: Some downloads failed. This is normal for public mirrors.")
        print("Failed tiles can be downloaded manually from USGS EarthExplorer:")
        print("  https://earthexplorer.usgs.gov/")
        print("\nOr you can run this script again to retry failed downloads.")
        print("-" * 70)


if __name__ == "__main__":
    main()
