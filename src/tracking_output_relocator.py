"""
Tracking Output Relocator

This module handles relocation of TrackMate tracking results from a centralized
output folder back to their original location folders in the data structure.

Usage scenarios:
- After batch processing in TrackMate, all results are in one OutputTracks folder
- Need to reorganize files back to: Data Root / Rep X / Time / Type / Location / Tracking Result /

Date: 2026-02-13
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


class TrackingOutputRelocator:
    """
    Relocates tracking output files from a centralized folder back to their
    original location folders in the data structure.
    """
    
    def __init__(self, output_folder: str, root_data_folder: str):
        """
        Initialize the relocator.
        
        Args:
            output_folder: Path to the centralized output folder (e.g., OutputTracks)
            root_data_folder: Path to the root data folder containing the original structure
        """
        self.output_folder = Path(output_folder)
        self.root_data_folder = Path(root_data_folder)
        self.stats = {
            'total_files': 0,
            'moved': 0,
            'skipped': 0,
            'errors': 0,
            'locations_updated': 0
        }
    
    def parse_filename(self, filename: str) -> Optional[Tuple[str, str, str, str, str]]:
        """
        Parse a tracking output filename to extract location information.
        
        Expected format: Rep-X_TimeRange_Type_LocationID_Red_Seg-xxx.csv
        Example: Rep-3_0-24h_Dense_B1_12_Red_Seg-spots.csv
        
        Args:
            filename: The filename to parse
            
        Returns:
            Tuple of (rep, time, type, location, original_filename) or None if parsing fails
        """
        # Check if file has expected pattern
        if "_Red_Seg" not in filename:
            return None
        
        # Extract prefix (everything before _Red_Seg)
        prefix = filename.split("_Red_Seg")[0]
        parts = prefix.split("_")
        
        if len(parts) < 4:
            return None
        
        # Parse components
        rep = parts[0].replace("Rep-", "Rep ")  # "Rep-3" -> "Rep 3"
        time = parts[1]  # "0-24h"
        type_ = parts[2]  # "Dense" or "10um"
        location = "_".join(parts[3:])  # Reconstruct full location ID (e.g., "B1_12")
        
        return (rep, time, type_, location, filename)
    
    def group_files_by_location(self) -> Dict[str, List[str]]:
        """
        Group all files in the output folder by their location prefix.
        
        Returns:
            Dictionary mapping location prefixes to list of filenames
        """
        prefix_map = defaultdict(list)
        
        if not self.output_folder.exists():
            print(f"✗ Output folder does not exist: {self.output_folder}")
            return {}
        
        for file in self.output_folder.iterdir():
            if not file.is_file():
                continue
            
            # Only process known tracking file types
            if not file.suffix.lower() in ['.tif', '.csv', '.avi', '.xml']:
                continue
            
            self.stats['total_files'] += 1
            
            # Parse filename
            parsed = self.parse_filename(file.name)
            if parsed is None:
                print(f"  ⚠️  Skipped: {file.name} (unrecognized format)")
                self.stats['skipped'] += 1
                continue
            
            rep, time, type_, location, _ = parsed
            prefix = f"{rep}_{time}_{type_}_{location}"
            prefix_map[prefix].append(file.name)
        
        return prefix_map
    
    def relocate_location_files(self, prefix: str, filelist: List[str]) -> bool:
        """
        Relocate all files for a single location.
        
        Args:
            prefix: Location prefix (Rep_Time_Type_Location)
            filelist: List of filenames to move
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse the first file to get location info
            parsed = self.parse_filename(filelist[0])
            if parsed is None:
                return False
            
            rep, time, type_, location, _ = parsed
            
            # Construct target folder path
            location_path = self.root_data_folder / rep / time / type_ / location
            
            if not location_path.exists():
                print(f"  ✗ Target folder not found: {location_path}")
                self.stats['errors'] += 1
                return False
            
            # Create Tracking Result subfolder
            result_path = location_path / "Tracking Result"
            result_path.mkdir(exist_ok=True)
            
            # Move all files
            moved_count = 0
            for filename in filelist:
                src = self.output_folder / filename
                dst = result_path / filename
                
                try:
                    shutil.move(str(src), str(dst))
                    moved_count += 1
                    self.stats['moved'] += 1
                except Exception as e:
                    print(f"    ✗ Failed to move {filename}: {e}")
                    self.stats['errors'] += 1
            
            if moved_count > 0:
                print(f"  ✓ Moved {moved_count} file(s) → {rep} / {time} / {type_} / {location}")
                self.stats['locations_updated'] += 1
                return True
            
            return False
            
        except Exception as e:
            print(f"  ✗ Error processing {prefix}: {e}")
            self.stats['errors'] += 1
            return False
    
    def relocate_all(self) -> Dict[str, int]:
        """
        Relocate all tracking output files.
        
        Returns:
            Dictionary with relocation statistics
        """
        print("=" * 80)
        print("TRACKING OUTPUT RELOCATION")
        print("=" * 80)
        print(f"Output folder: {self.output_folder}")
        print(f"Data root: {self.root_data_folder}")
        print()
        
        # Group files by location
        print("Analyzing files...")
        prefix_map = self.group_files_by_location()
        
        if not prefix_map:
            print("✗ No files to relocate")
            return self.stats
        
        print(f"Found {len(prefix_map)} location(s) with tracking results")
        print()
        
        # Process each location
        print("Relocating files...")
        for prefix, filelist in prefix_map.items():
            self.relocate_location_files(prefix, filelist)
        
        # Print summary
        print()
        print("=" * 80)
        print("RELOCATION COMPLETE")
        print("=" * 80)
        print(f"Total files processed: {self.stats['total_files']}")
        print(f"Files moved: {self.stats['moved']}")
        print(f"Files skipped: {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Locations updated: {self.stats['locations_updated']}")
        print("=" * 80)
        
        return self.stats


def relocate_tracking_outputs(output_folder: str, root_data_folder: str) -> Dict[str, int]:
    """
    Convenience function to relocate tracking outputs.
    
    Args:
        output_folder: Path to centralized output folder
        root_data_folder: Path to root data folder
        
    Returns:
        Statistics dictionary
    """
    relocator = TrackingOutputRelocator(output_folder, root_data_folder)
    return relocator.relocate_all()


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Relocate TrackMate tracking outputs back to original data folders"
    )
    parser.add_argument("--output", "-o", required=True,
                       help="Path to centralized output folder (e.g., OutputTracks)")
    parser.add_argument("--root", "-r", required=True,
                       help="Path to root data folder")
    
    args = parser.parse_args()
    
    relocate_tracking_outputs(args.output, args.root)
