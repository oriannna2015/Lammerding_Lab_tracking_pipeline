"""
Folder Utilities Module

Utility functions for folder scanning and path management.
"""
import os
from pathlib import Path
from typing import List, Tuple, Dict


def clean_location_name(location_name: str) -> str:
    """
    Remove '_cropped' suffix from location name if present.
    
    Args:
        location_name: Original location folder name (e.g., 'A1_1_cropped')
    
    Returns:
        Cleaned location name (e.g., 'A1_1')
    """
    if location_name.endswith('_cropped'):
        return location_name[:-8]  # Remove last 8 characters ('_cropped')
    return location_name


def scan_data_folder_structure(root_folder: str) -> List[Dict[str, str]]:
    """
    Scan data folder to find all locations.
    
    Expected structure:
    root_folder/
        Rep X/
            timepoint/
                datatype/
                    location/
    
    Args:
        root_folder: Root data folder path
    
    Returns:
        List of location dictionaries with keys: rep, timepoint, datatype, location, path
    """
    locations = []
    root_path = Path(root_folder)
    
    if not root_path.exists():
        print(f"✗ Root folder not found: {root_folder}")
        return locations
    
    # Scan for Reps
    for rep_folder in sorted(root_path.iterdir()):
        if not rep_folder.is_dir() or not rep_folder.name.startswith('Rep'):
            continue
        
        rep = rep_folder.name
        
        # Scan for timepoints
        for timepoint_folder in sorted(rep_folder.iterdir()):
            if not timepoint_folder.is_dir():
                continue
            
            timepoint = timepoint_folder.name
            
            # Scan for datatypes
            for datatype_folder in sorted(timepoint_folder.iterdir()):
                if not datatype_folder.is_dir():
                    continue
                
                datatype = datatype_folder.name
                
                # Scan for locations
                for location_folder in sorted(datatype_folder.iterdir()):
                    if not location_folder.is_dir():
                        continue
                    
                    location = location_folder.name
                    
                    # Check if this is a valid location folder
                    # Valid locations should have subfolders or tif files
                    has_content = any(location_folder.iterdir())
                    
                    if has_content:
                        locations.append({
                            'rep': rep,
                            'timepoint': timepoint,
                            'datatype': datatype,
                            'location': clean_location_name(location),  # Remove '_cropped' suffix if present
                            'path': str(location_folder)
                        })
    
    return locations


def find_tracking_results(root_folder: str) -> List[Path]:
    """
    Find all 'Tracking Result' folders recursively.
    
    Args:
        root_folder: Root folder to search
    
    Returns:
        List of Tracking Result folder paths
    """
    tracking_results = []
    root_path = Path(root_folder)
    
    for item in root_path.rglob('*'):
        if item.is_dir() and item.name == 'Tracking Result':
            tracking_results.append(item)
    
    return tracking_results


def get_location_identifier(rep: str, timepoint: str, datatype: str, location: str) -> str:
    """
    Generate a unique location identifier string.
    
    Args:
        rep: Replicate name (e.g., 'Rep 1')
        timepoint: Timepoint name (e.g., '0-24h')
        datatype: Data type name (e.g., '10um', 'Dense')
        location: Location name (e.g., 'B1_2')
    
    Returns:
        Location identifier string (e.g., 'Rep-1_0-24h_10um_B1_2')
    """
    # Replace spaces with hyphens for cleaner naming
    rep_clean = rep.replace(' ', '-')
    return f"{rep_clean}_{timepoint}_{datatype}_{location}"


def ensure_folder_exists(folder_path: str) -> bool:
    """
    Ensure a folder exists, creating it if necessary.
    
    Args:
        folder_path: Path to folder
    
    Returns:
        True if folder exists or was created successfully
    """
    try:
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"✗ Failed to create folder {folder_path}: {e}")
        return False


def find_files_by_pattern(folder: str, pattern: str) -> List[Path]:
    """
    Find files matching a pattern in a folder.
    
    Args:
        folder: Folder path
        pattern: File pattern (e.g., '*.tif', '*_Red_*.tif')
    
    Returns:
        List of matching file paths
    """
    folder_path = Path(folder)
    
    if not folder_path.exists():
        return []
    
    return sorted(folder_path.glob(pattern))


def get_relative_path(full_path: str, base_path: str) -> str:
    """
    Get relative path from base path.
    
    Args:
        full_path: Full file/folder path
        base_path: Base path to compute relative from
    
    Returns:
        Relative path string
    """
    try:
        return str(Path(full_path).relative_to(Path(base_path)))
    except ValueError:
        return full_path


def validate_location_structure(location_path: str, channel_names: List[str]) -> Tuple[bool, str]:
    """
    Validate that a location has the expected channel folder structure.
    
    Args:
        location_path: Path to location folder
        channel_names: List of expected channel names
    
    Returns:
        Tuple of (is_valid, message)
    """
    location_path_obj = Path(location_path)
    location_name = clean_location_name(location_path_obj.name)  # Remove '_cropped' suffix if present
    
    # Check for channel subfolders
    for channel in channel_names:
        channel_folder = location_path_obj / f"{location_name}_{channel}"
        if not channel_folder.exists():
            return False, f"Missing channel folder: {channel_folder.name}"
    
    return True, "Valid structure"
