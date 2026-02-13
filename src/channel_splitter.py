"""
Channel Splitter Module

Splits multi-channel TIFF stacks into separate channel folders within the source location.
"""
import os
import shutil
import math
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm


class ChannelSplitter:
    """Handles splitting of multi-channel images into separate channels in place."""
    
    def __init__(self, channel_names: List[str]):
        """
        Initialize channel splitter.
        
        Args:
            channel_names: List of channel names (e.g., ['Green', 'Phase', 'Red'])
        """
        self.channel_names = channel_names
        self.num_channels = len(channel_names)
        self.processed_count = 0
        self.failed_locations = []
    
    def split_location(self, location_folder: str, location_name: str) -> bool:
        """
        Split channels for a single location IN PLACE.
        Creates channel subfolders within the location folder.
        
        Args:
            location_folder: Location folder containing TIFF files
            location_name: Name of the location
        
        Returns:
            True if successful
        """
        try:
            location_path = Path(location_folder)
            
            if not location_path.exists():
                print(f"  ✗ Location folder not found: {location_folder}")
                return False
            
            # Find all TIFF files in the root of location folder
            tif_files = sorted([
                f for f in location_path.iterdir()
                if f.suffix.lower() == '.tif' and f.is_file()
            ])
            
            if not tif_files:
                print(f"  ⚠ No .tif files found in: {location_folder}")
                return False
            
            total_files = len(tif_files)
            
            # Calculate split points
            split_points = [
                math.floor(i * total_files / self.num_channels)
                for i in range(self.num_channels + 1)
            ]
            
            # Split files into channels
            for i in range(self.num_channels):
                start_idx = split_points[i]
                end_idx = split_points[i + 1]
                file_segment = tif_files[start_idx:end_idx]
                
                # Create channel folder within location folder
                channel_name = self.channel_names[i]
                channel_folder = location_path / f"{location_name}_{channel_name}"
                channel_folder.mkdir(parents=True, exist_ok=True)
                
                # Move files to channel folder
                for file in file_segment:
                    target_file = channel_folder / file.name
                    if not target_file.exists():
                        shutil.move(str(file), str(target_file))
            
            print(f"  ✓ Split {total_files} files into {self.num_channels} channels")
            self.processed_count += 1
            return True
            
        except Exception as e:
            print(f"  ✗ Error splitting channels: {e}")
            self.failed_locations.append((location_folder, str(e)))
            return False
    
    def batch_split(self, locations: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Batch process multiple locations in place.
        
        Args:
            locations: List of location dictionaries with 'path' and 'location' keys
        
        Returns:
            Dictionary with processing statistics
        """
        print("\n" + "=" * 80)
        print("CHANNEL SPLITTING (IN-PLACE)")
        print("=" * 80)
        print(f"Processing {len(locations)} locations...")
        
        self.processed_count = 0
        self.failed_locations = []
        
        for idx, loc_info in enumerate(tqdm(locations, desc="Splitting channels"), 1):
            location_name = loc_info['location']
            location_path = loc_info['path']
            
            print(f"\n[{idx}/{len(locations)}] {loc_info['rep']} - {loc_info['timepoint']} - {loc_info['datatype']} - {location_name}")
            
            self.split_location(location_path, location_name)
        
        # Summary
        print("\n" + "=" * 80)
        print("CHANNEL SPLITTING COMPLETE")
        print("=" * 80)
        print(f"Successfully processed: {self.processed_count}/{len(locations)}")
        
        if self.failed_locations:
            print(f"\nFailed locations ({len(self.failed_locations)}):")
            for loc, error in self.failed_locations:
                print(f"  - {loc}: {error}")
        
        return {
            'total': len(locations),
            'success': self.processed_count,
            'failed': len(self.failed_locations)
        }
