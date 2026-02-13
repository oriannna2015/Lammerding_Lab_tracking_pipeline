"""
Segmentation Module

Performs cell segmentation using StarDist model.
"""
import os
import gc
import time
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
import tifffile
from tqdm import tqdm


class Segmentator:
    """Handles cell segmentation using StarDist."""
    
    def __init__(self, model_path: str):
        """
        Initialize segmentator with StarDist model.
        
        Args:
            model_path: Path to StarDist model folder
        """
        self.model_path = model_path
        self.model = None
        self.processed_count = 0
        self.failed_files = []
        self.skipped_files = []
    
    def load_model(self) -> bool:
        """
        Load StarDist model.
        
        Returns:
            True if model loaded successfully
        """
        try:
            from stardist.models import StarDist2D
            from csbdeep.utils import normalize
            
            self.normalize = normalize
            
            model_name = os.path.basename(self.model_path)
            model_basedir = os.path.dirname(self.model_path)
            
            print("Loading StarDist model...")
            self.model = StarDist2D(None, name=model_name, basedir=model_basedir)
            print("✓ StarDist model loaded successfully")
            return True
            
        except Exception as e:
            print(f"✗ Failed to load StarDist model: {e}")
            return False
    
    def segment_image(self, input_path: str, output_path: str) -> bool:
        """
        Segment a single image stack.
        
        Args:
            input_path: Path to input TIFF stack
            output_path: Path to output segmentation mask
        
        Returns:
            True if successful
        """
        try:
            # Check if output already exists
            if os.path.exists(output_path):
                print(f"  ⏩ Skipped (already exists): {os.path.basename(output_path)}")
                self.skipped_files.append(input_path)
                return True
            
            # Load image stack
            print(f"  Loading: {os.path.basename(input_path)}")
            stack = tifffile.imread(input_path)
            
            # Segment each frame
            segmented_stack = []
            for i in tqdm(range(stack.shape[0]), desc="  Segmenting frames", leave=False):
                norm_img = self.normalize(stack[i], 1, 99.8)
                labels, _ = self.model.predict_instances(norm_img)
                segmented_stack.append(labels.astype(np.uint16))
            
            segmented_stack = np.stack(segmented_stack, axis=0)
            
            # Save output
            print(f"  Saving: {os.path.basename(output_path)}")
            with tifffile.TiffWriter(output_path, imagej=True) as tif:
                tif.write(segmented_stack, metadata={"axes": "TYX"})
                tif._fh.flush()
                os.fsync(tif._fh.fileno())
            
            print(f"  ✓ Segmentation complete")
            
            # Cleanup
            del segmented_stack
            del stack
            gc.collect()
            time.sleep(0.2)
            
            self.processed_count += 1
            return True
            
        except Exception as e:
            print(f"  ✗ Segmentation failed: {e}")
            self.failed_files.append((input_path, str(e)))
            return False
    
    def batch_segment(
        self,
        locations: List[Dict[str, str]],
        input_mask_folder: str
    ) -> Dict[str, int]:
        """
        Batch segment multiple locations.
        
        Args:
            locations: List of location dictionaries
            input_mask_folder: Output folder for segmentation masks
        
        Returns:
            Dictionary with processing statistics
        """
        print("\n" + "=" * 80)
        print("SEGMENTATION")
        print("=" * 80)
        
        if not self.load_model():
            return {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
        
        print(f"\nProcessing {len(locations)} locations...")
        
        self.processed_count = 0
        self.failed_files = []
        self.skipped_files = []
        
        Path(input_mask_folder).mkdir(parents=True, exist_ok=True)
        
        for idx, loc_info in enumerate(locations, 1):
            location_name = loc_info['location']
            location_path = Path(loc_info['path'])
            
            # Find Red_Stabilized.tif file
            red_stabilized_file = location_path / f"{location_name}_Red_Stabilized.tif"
            
            if not red_stabilized_file.exists():
                print(f"\n[{idx}/{len(locations)}] {location_name}")
                print(f"  ⚠ Red_Stabilized.tif not found, skipping")
                self.skipped_files.append(str(red_stabilized_file))
                continue
            
            # Generate output path
            from folder_utils import get_location_identifier
            location_id = get_location_identifier(
                loc_info['rep'],
                loc_info['timepoint'],
                loc_info['datatype'],
                location_name
            )
            output_file = Path(input_mask_folder) / f"{location_id}_Red_Seg.tif"
            
            print(f"\n[{idx}/{len(locations)}] {location_name}")
            self.segment_image(str(red_stabilized_file), str(output_file))
        
        # Summary
        print("\n" + "=" * 80)
        print("SEGMENTATION COMPLETE")
        print("=" * 80)
        print(f"Successfully processed: {self.processed_count}/{len(locations)}")
        print(f"Skipped (already exist): {len(self.skipped_files)}")
        
        if self.failed_files:
            print(f"\nFailed files ({len(self.failed_files)}):")
            for file, error in self.failed_files:
                print(f"  - {file}: {error}")
        
        return {
            'total': len(locations),
            'success': self.processed_count,
            'failed': len(self.failed_files),
            'skipped': len(self.skipped_files)
        }
