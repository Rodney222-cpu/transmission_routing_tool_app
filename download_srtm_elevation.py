"""
Automatic SRTM DEM Downloader for Uganda using the 'elevation' library
Downloads all SRTM 1 Arc-Second tiles covering Uganda
"""

import os
import elevation
import time
from pathlib import Path

# Uganda SRTM tile coverage - all tiles that cover Uganda
# Format: (south, west, north, east) for each tile
UGANDA_TILES_BOUNDS = [
    # Row N04 (latitude 4N)
    (4, 30, 5, 31), (4, 31, 5, 32), (4, 32, 5, 33), (4, 33, 5, 34), (4, 34, 5, 35), (4, 35, 5, 36),
    # Row N03
    (3, 30, 4, 31), (3, 31, 4, 32), (3, 32, 4, 33), (3, 33, 4, 34), (3, 34, 4, 35), (3, 35, 4, 36),
    # Row N02
    (2, 30, 3, 31), (2, 31, 3, 32), (2, 32, 3, 33), (2, 33, 3, 34), (2, 34, 3, 35), (2, 35, 3, 36),
    # Row N01
    (1, 30, 2, 31), (1, 31, 2, 32), (1, 32, 2, 33), (1, 33, 2, 34), (1, 34, 2, 35), (1, 35, 2, 36),
    # Row N00 (Equator)
    (0, 30, 1, 31), (0, 31, 1, 32), (0, 32, 1, 33), (0, 33, 1, 34), (0, 34, 1, 35), (0, 35, 1, 36),
    # Row S01 (South of equator)
    (-1, 30, 0, 31), (-1, 31, 0, 32), (-1, 32, 0, 33), (-1, 33, 0, 34), (-1, 34, 0, 35), (-1, 35, 0, 36),
]


def get_tile_name(south, west, north, east):
    """Generate tile name from bounds"""
    lat_str = f"N{int(north):02d}" if north >= 0 else f"S{abs(int(north)):02d}"
    lon_str = f"E{int(east):03d}" if east >= 0 else f"W{abs(int(east)):03d}"
    return f"{lat_str}{lon_str}"


def main():
    """Main download function"""
    print("=" * 70)
    print("UGANDA SRTM DEM DOWNLOADER")
    print("Using 'elevation' library (SRTM 1 Arc-Second)")
    print("=" * 70)
    print(f"\nTotal tiles to download: {len(UGANDA_TILES_BOUNDS)}")
    print("\nThis will download approximately 500-800 MB of data")
    print("Estimated time: 30-60 minutes depending on internet speed")
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
    
    for i, (south, west, north, east) in enumerate(UGANDA_TILES_BOUNDS, 1):
        tile_name = get_tile_name(south, west, north, east)
        output_file = output_dir / f"{tile_name}.tif"
        
        print(f"\n[{i}/{len(UGANDA_TILES_BOUNDS)}] {tile_name}")
        
        # Check if already exists
        if output_file.exists():
            file_size = output_file.stat().st_size / (1024 * 1024)
            print(f"  Already exists ({file_size:.1f} MB), skipping")
            skipped += 1
            continue
        
        try:
            # Download using elevation library
            print(f"  Downloading SRTM tile...")
            elevation.clip(
                bounds=(west, south, east, north),
                output=output_file,
                product='SRTM1'  # SRTM 1 Arc-Second (30m)
            )
            elevation.clean()  # Clean up temporary files
            
            if output_file.exists():
                file_size = output_file.stat().st_size / (1024 * 1024)
                print(f"  ✓ Saved: {output_file.name} ({file_size:.1f} MB)")
                successful += 1
            else:
                print(f"  ✗ Failed: File not created")
                failed += 1
                
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed += 1
            if output_file.exists():
                output_file.unlink()
        
        # Rate limiting
        if i < len(UGANDA_TILES_BOUNDS):
            time.sleep(1)
    
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
