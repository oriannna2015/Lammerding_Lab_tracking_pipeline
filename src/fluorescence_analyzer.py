"""
Fluorescence Analyzer Module

Extracts fluorescence intensity over tracked cells and subtracks.
Now supports subtrack-based analysis with Red/Green ratio calculation.
"""
import os
import time
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
import tifffile


class FluorescenceAnalyzer:
    """Analyzes fluorescence intensity from tracking results based on subtracks."""
    
    def __init__(self, input_mask_folder: str):
        """
        Initialize fluorescence analyzer.
        
        Args:
            input_mask_folder: Folder containing segmentation masks
        """
        self.input_mask_folder = input_mask_folder
        self.processed_count = 0
        self.failed_locations = []
        self.skipped_locations = []
    
    def analyze_location(self, location_info: Dict[str, str]) -> bool:
        """
        Analyze fluorescence for a single location based on subtracks.
        
        Args:
            location_info: Location dictionary
        
        Returns:
            True if successful
        """
        try:
            location_path = Path(location_info['path'])
            location_name = location_info['location']
            
            # Find Tracking Result folder
            tracking_result_path = location_path / "Tracking Result"
            if not tracking_result_path.exists():
                print(f"  ✗ No Tracking Result folder found")
                self.skipped_locations.append(str(location_path))
                return False
            
            # Check for secondary_analysis folder and subtrack files
            secondary_analysis_path = tracking_result_path / "secondary_analysis"
            if not secondary_analysis_path.exists():
                print(f"  ✗ No secondary_analysis folder found (run subtrack analysis first)")
                self.skipped_locations.append(str(location_path))
                return False
            
            # Find subtrack lineage file
            subtrack_lineage_files = list(secondary_analysis_path.glob("*-subtrack_lineage.csv"))
            if not subtrack_lineage_files:
                print(f"  ✗ No subtrack lineage file found")
                self.skipped_locations.append(str(location_path))
                return False
            
            subtrack_lineage_path = subtrack_lineage_files[0]
            prefix = subtrack_lineage_path.stem.replace('-subtrack_lineage', '')
            output_csv_path = secondary_analysis_path / f"{prefix}-subtrack_fluorescence.csv"
            
            # Check if already processed
            if output_csv_path.exists():
                print(f"  ⏩ Already processed")
                self.skipped_locations.append(str(location_path))
                return True
            
            # Find spots CSV file
            spot_files = list(tracking_result_path.glob("*-spots.csv"))
            spot_files = [f for f in spot_files if 'all' not in f.name.lower()]
            
            if not spot_files:
                print(f"  ✗ No spots CSV file found")
                self.skipped_locations.append(str(location_path))
                return False
            
            spots_csv_path = spot_files[0]
            
            # Find segmentation mask
            from folder_utils import get_location_identifier
            location_id = get_location_identifier(
                location_info['rep'],
                location_info['timepoint'],
                location_info['datatype'],
                location_name
            )
            segmentation_tif_path = Path(self.input_mask_folder) / f"{location_id}_Red_Seg.tif"
            
            if not segmentation_tif_path.exists():
                print(f"  ✗ Segmentation mask not found: {segmentation_tif_path.name}")
                self.failed_locations.append(str(location_path))
                return False
            
            # Find fluorescence images
            red_fluor_path = location_path / f"{location_name}_Red_Stabilized.tif"
            green_fluor_path = location_path / f"{location_name}_Green_Stabilized.tif"
            
            if not (red_fluor_path.exists() and green_fluor_path.exists()):
                print(f"  ✗ Red or Green fluorescence images missing")
                self.failed_locations.append(str(location_path))
                return False
            
            # Load data
            print(f"  Loading subtrack lineage...")
            subtrack_lineage_df = pd.read_csv(subtrack_lineage_path)
            
            print(f"  Loading spots CSV...")
            spots_df = self._load_spots_csv(spots_csv_path)
            
            print(f"  Loading images...")
            seg_stack = tifffile.imread(segmentation_tif_path)
            red_fluor_stack = tifffile.imread(red_fluor_path)
            green_fluor_stack = tifffile.imread(green_fluor_path)
            
            # Validate shapes
            if not (seg_stack.shape == red_fluor_stack.shape == green_fluor_stack.shape):
                print(f"  ✗ Image shape mismatch")
                self.failed_locations.append(str(location_path))
                return False
            
            # Extract intensities per subtrack
            print(f"  Extracting intensities per subtrack...")
            subtrack_green, subtrack_red = self._extract_subtrack_intensities(
                subtrack_lineage_df, spots_df, seg_stack, red_fluor_stack, green_fluor_stack
            )
            
            if not subtrack_green:
                print(f"  ✗ No valid subtracks found")
                self.failed_locations.append(str(location_path))
                return False
            
            # Format output
            print(f"  Formatting output...")
            output_df = self._format_output(subtrack_green, subtrack_red, seg_stack.shape[0])
            
            # Save
            output_df.to_csv(output_csv_path)
            print(f"  ✓ Saved: {output_csv_path.name}")
            
            self.processed_count += 1
            return True
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.failed_locations.append(str(location_info['path']))
            return False
    
    def _load_spots_csv(self, csv_path: Path) -> pd.DataFrame:
        """Load spots CSV file."""
        columns = [
            'LABEL', 'ID', 'TRACK_ID', 'QUALITY',
            'POSITION_X', 'POSITION_Y', 'POSITION_Z', 'POSITION_T',
            'FRAME', 'RADIUS', 'VISIBILITY', 'MANUAL_SPOT_COLOR',
            'MEAN_INTENSITY_CH1', 'MEDIAN_INTENSITY_CH1', 'MIN_INTENSITY_CH1',
            'MAX_INTENSITY_CH1', 'TOTAL_INTENSITY_CH1', 'STD_INTENSITY_CH1',
            'CONTRAST_CH1', 'SNR_CH1',
            'ELLIPSE_X0', 'ELLIPSE_Y0', 'ELLIPSE_MAJOR', 'ELLIPSE_MINOR',
            'ELLIPSE_THETA', 'ELLIPSE_ASPECTRATIO', 'AREA', 'PERIMETER',
            'CIRCULARITY', 'SOLIDITY', 'SHAPE_INDEX'
        ]
        
        spots_df = pd.read_csv(csv_path, skiprows=3, header=None)
        spots_df.columns = columns
        return spots_df
    
    def _extract_subtrack_intensities(
        self,
        subtrack_lineage_df: pd.DataFrame,
        spots_df: pd.DataFrame,
        seg_stack: np.ndarray,
        red_fluor_stack: np.ndarray,
        green_fluor_stack: np.ndarray
    ) -> Tuple[dict, dict]:
        """
        Extract fluorescence intensities for each subtrack at each frame.
        
        Returns:
            (subtrack_green, subtrack_red) dictionaries mapping subtrack_id -> {frame_idx -> intensity}
        """
        subtrack_green = {}
        subtrack_red = {}
        
        # Build mapping: (TRACK_ID, FRAME) -> SUBTRACK_ID
        track_frame_to_subtrack = {}
        for _, row in subtrack_lineage_df.iterrows():
            subtrack_id = row['SUBTRACK_ID']
            track_id = int(row['TRACK_ID'])
            start_frame = int(row['START_FRAME'])
            end_frame = int(row['END_FRAME'])
            
            for frame in range(start_frame, end_frame + 1):
                track_frame_to_subtrack[(track_id, frame)] = subtrack_id
        
        # Extract intensities frame by frame
        for frame_idx in range(seg_stack.shape[0]):
            frame_spots = spots_df[spots_df['FRAME'] == frame_idx]
            seg_frame = seg_stack[frame_idx]
            red_fluor_frame = red_fluor_stack[frame_idx]
            green_fluor_frame = green_fluor_stack[frame_idx]
            
            for _, spot in frame_spots.iterrows():
                try:
                    track_id = int(spot['TRACK_ID'])
                    x = float(spot['POSITION_X'])
                    y = float(spot['POSITION_Y'])
                except (KeyError, ValueError):
                    continue
                
                # Check if this spot belongs to a subtrack
                key = (track_id, frame_idx)
                if key not in track_frame_to_subtrack:
                    continue
                
                subtrack_id = track_frame_to_subtrack[key]
                
                col = int(round(x))
                row = int(round(y))
                
                # Bounds check
                if row < 0 or row >= seg_frame.shape[0] or col < 0 or col >= seg_frame.shape[1]:
                    continue
                
                label_id = seg_frame[row, col]
                if label_id == 0:
                    continue
                
                # Create mask for this cell
                mask = (seg_frame == label_id)
                
                # Extract intensities
                red_cell_pixels = red_fluor_frame[mask]
                green_cell_pixels = green_fluor_frame[mask]
                
                mean_red_intensity = np.mean(red_cell_pixels) if red_cell_pixels.size > 0 else np.nan
                mean_green_intensity = np.mean(green_cell_pixels) if green_cell_pixels.size > 0 else np.nan
                
                if subtrack_id not in subtrack_green:
                    subtrack_green[subtrack_id] = {}
                    subtrack_red[subtrack_id] = {}
                
                subtrack_green[subtrack_id][frame_idx] = mean_green_intensity
                subtrack_red[subtrack_id][frame_idx] = mean_red_intensity
        
        return subtrack_green, subtrack_red
    
    def _format_output(
        self,
        subtrack_green: dict,
        subtrack_red: dict,
        max_frame: int
    ) -> pd.DataFrame:
        """
        Format output following original format: 
        - Rows: Subtracks (Subtrack_X_Green, Subtrack_X_Red, Subtrack_X_Ratio)
        - Columns: Frames (Frame0, Frame1, ...)
        """
        subtrack_ids = sorted(subtrack_green.keys())
        
        # Build data arrays
        green_data = []
        red_data = []
        ratio_data = []
        
        for subtrack_id in subtrack_ids:
            green_row = [subtrack_green[subtrack_id].get(f, np.nan) for f in range(max_frame)]
            red_row = [subtrack_red[subtrack_id].get(f, np.nan) for f in range(max_frame)]
            
            # Calculate ratio row
            ratio_row = []
            for f in range(max_frame):
                red_val = subtrack_red[subtrack_id].get(f, np.nan)
                green_val = subtrack_green[subtrack_id].get(f, np.nan)
                
                if pd.notna(red_val) and pd.notna(green_val) and green_val > 0:
                    ratio = red_val / green_val
                else:
                    ratio = np.nan
                ratio_row.append(ratio)
            
            green_data.append(green_row)
            red_data.append(red_row)
            ratio_data.append(ratio_row)
        
        # Combine: Green block, then Red block, then Ratio block
        final_data = green_data + red_data + ratio_data
        
        # Build row names
        row_names = (
            [f"{sid}_Green" for sid in subtrack_ids] +
            [f"{sid}_Red" for sid in subtrack_ids] +
            [f"{sid}_Ratio" for sid in subtrack_ids]
        )
        
        # Build column names
        col_names = [f"Frame{f}" for f in range(max_frame)]
        
        # Create DataFrame
        output_df = pd.DataFrame(final_data, index=row_names, columns=col_names)
        
        return output_df
    
    def batch_analyze(self, locations: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Batch analyze multiple locations.
        
        Args:
            locations: List of location dictionaries
        
        Returns:
            Dictionary with processing statistics
        """
        print("\n" + "=" * 80)
        print("FLUORESCENCE INTENSITY ANALYSIS")
        print("=" * 80)
        print(f"Processing {len(locations)} locations...")
        
        self.processed_count = 0
        self.failed_locations = []
        self.skipped_locations = []
        
        for idx, loc_info in enumerate(locations, 1):
            location_name = loc_info['location']
            print(f"\n[{idx}/{len(locations)}] {loc_info['rep']} - {loc_info['timepoint']} - {loc_info['datatype']} - {location_name}")
            
            self.analyze_location(loc_info)
            time.sleep(0.1)
        
        # Summary
        print("\n" + "=" * 80)
        print("FLUORESCENCE ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"Successfully processed: {self.processed_count}/{len(locations)}")
        print(f"Skipped: {len(self.skipped_locations)}")
        
        if self.failed_locations:
            print(f"\nFailed locations ({len(self.failed_locations)}):")
            for loc in self.failed_locations:
                print(f"  - {loc}")
        
        return {
            'total': len(locations),
            'success': self.processed_count,
            'failed': len(self.failed_locations),
            'skipped': len(self.skipped_locations)
        }
