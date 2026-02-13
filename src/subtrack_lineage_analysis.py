"""
Subtrack Lineage Analysis Pipeline (v2.0)

This script analyzes TrackMate tracking data to extract subtrack lineages and compute
motion statistics for each subtrack. It applies quality control filters and uses a
recursive depth-first search algorithm to build subtrack trees.

Key Features:
- QC filtering by max splits and minimum duration
- Recursive DFS algorithm with split spot in pre-split subtrack
- Generates 3 CSV outputs: statistics, edges, and lineage
- Supports batch processing of multiple locations

Date: 2026-02-11
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import sys

# ============================================================================
# GLOBAL QC PARAMETERS
# ============================================================================
MAX_SPLITS_ALLOWED = 3
MIN_TRACK_DURATION_FRAMES = 20


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
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


class SubtrackAnalyzer:
    """
    Analyzes TrackMate tracking data to generate subtrack lineages.
    
    This class implements a recursive DFS algorithm to split tracks into subtracks
    based on division events, compute motion statistics for each subtrack, and
    maintain parent-child relationships.
    """
    
    def __init__(self, tracking_result_folder: Path, max_splits: int = None, min_duration: int = None):
        """
        Initialize the SubtrackAnalyzer.
        
        Args:
            tracking_result_folder: Path to the 'Tracking Result' folder
            max_splits: Maximum allowed splits per track (default: use global setting)
            min_duration: Minimum track duration in frames (default: use global setting)
        """
        self.tracking_result_folder = Path(tracking_result_folder)
        self.max_splits = max_splits if max_splits is not None else MAX_SPLITS_ALLOWED
        self.min_duration = min_duration if min_duration is not None else MIN_TRACK_DURATION_FRAMES
        
        self.spots_df = None
        self.edges_df = None
        self.tracks_df = None
        self.filtered_tracks = None
        
        self.subtrack_stats = []
        self.subtrack_edges = []
        self.subtrack_lineage = []
        self.subtrack_counter = 0
        self.track_subtrack_counters = {}  # Track subtrack index per original track
    
    def load_data(self) -> bool:
        """
        Load TrackMate CSV files (spots, edges, tracks).
        
        Returns:
            True if all files loaded successfully, False otherwise
        """
        try:
            # Find CSV files - try both naming patterns
            csv_files = list(self.tracking_result_folder.glob("*-all-spots.csv"))
            if not csv_files:
                csv_files = list(self.tracking_result_folder.glob("*-spots.csv"))
            if not csv_files:
                print(f"  ✗ No spots CSV file found in {self.tracking_result_folder}")
                return False
            
            # Determine base name based on which pattern was found
            if '-all-spots' in csv_files[0].stem:
                base_name = csv_files[0].stem.replace('-all-spots', '')
                spots_file = self.tracking_result_folder / f"{base_name}-all-spots.csv"
            else:
                base_name = csv_files[0].stem.replace('-spots', '')
                spots_file = self.tracking_result_folder / f"{base_name}-spots.csv"
            
            edges_file = self.tracking_result_folder / f"{base_name}-edges.csv"
            tracks_file = self.tracking_result_folder / f"{base_name}-tracks.csv"
            
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    self.spots_df = pd.read_csv(spots_file, encoding=encoding)
                    self.edges_df = pd.read_csv(edges_file, encoding=encoding)
                    self.tracks_df = pd.read_csv(tracks_file, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode CSV files with any supported encoding")
            
            # Ensure numeric columns are the correct type
            numeric_cols_spots = ['POSITION_X', 'POSITION_Y', 'POSITION_Z', 'FRAME', 'ID', 'TRACK_ID', 
                                  'QUALITY', 'MEAN_INTENSITY_CH1']
            for col in numeric_cols_spots:
                if col in self.spots_df.columns:
                    self.spots_df[col] = pd.to_numeric(self.spots_df[col], errors='coerce')
            
            numeric_cols_edges = ['SPOT_SOURCE_ID', 'SPOT_TARGET_ID', 'EDGE_TIME']
            for col in numeric_cols_edges:
                if col in self.edges_df.columns:
                    self.edges_df[col] = pd.to_numeric(self.edges_df[col], errors='coerce')
            
            numeric_cols_tracks = ['TRACK_ID', 'NUMBER_SPOTS', 'NUMBER_GAPS', 'NUMBER_SPLITS', 
                                   'NUMBER_MERGES', 'TRACK_DURATION', 'TRACK_START', 'TRACK_STOP']
            for col in numeric_cols_tracks:
                if col in self.tracks_df.columns:
                    self.tracks_df[col] = pd.to_numeric(self.tracks_df[col], errors='coerce')
            
            print(f"  ✓ Loaded {len(self.tracks_df)} tracks")
            print(f"  ✓ Loaded {len(self.spots_df)} spots")
            print(f"  ✓ Loaded {len(self.edges_df)} edges")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Error loading data: {e}")
            return False
    
    def apply_qc_filter(self):
        """
        Apply quality control filters to tracks.
        
        Filters:
        1. Remove tracks with > max_splits splits
        2. Remove tracks with < min_duration frames
        """
        print(f"\nApplying QC filters:")
        print(f"  - Max splits: {self.max_splits}")
        print(f"  - Min duration: {self.min_duration} frames")
        
        original_count = len(self.tracks_df)
        
        # Ensure numeric columns are the correct type
        self.tracks_df['NUMBER_SPLITS'] = pd.to_numeric(self.tracks_df['NUMBER_SPLITS'], errors='coerce')
        self.tracks_df['TRACK_DURATION'] = pd.to_numeric(self.tracks_df['TRACK_DURATION'], errors='coerce')
        
        # Filter by splits
        tracks_by_splits = self.tracks_df[self.tracks_df['NUMBER_SPLITS'] <= self.max_splits]
        removed_splits = original_count - len(tracks_by_splits)
        if removed_splits > 0:
            print(f"  ✗ Removed {removed_splits} tracks (splits > {self.max_splits})")
        
        # Filter by duration
        self.filtered_tracks = tracks_by_splits[
            tracks_by_splits['TRACK_DURATION'] >= self.min_duration
        ]
        removed_duration = len(tracks_by_splits) - len(self.filtered_tracks)
        if removed_duration > 0:
            print(f"  ✗ Removed {removed_duration} tracks (duration < {self.min_duration})")
        
        print(f"  ✓ Retained {len(self.filtered_tracks)} tracks for analysis")
    
    def build_subtrack_tree(self):
        """
        Build subtrack lineages using recursive depth-first search.
        
        Algorithm:
        - For each filtered track, find the root spot
        - Recursively traverse the lineage tree
        - Split spots are included in the pre-split subtrack
        - Each branch after a split becomes a new subtrack
        """
        print(f"\nBuilding subtrack lineages...")
        
        for _, track in self.filtered_tracks.iterrows():
            track_id = track['TRACK_ID']
            
            # Initialize subtrack counter for this track
            self.track_subtrack_counters[track_id] = 0
            
            # Get all spots in this track
            track_spots = self.spots_df[self.spots_df['TRACK_ID'] == track_id].copy()
            track_edges = self.edges_df[
                self.edges_df['SPOT_SOURCE_ID'].isin(track_spots['ID']) |
                self.edges_df['SPOT_TARGET_ID'].isin(track_spots['ID'])
            ].copy()
            
            # Find root spot (no incoming edge)
            root_candidates = track_spots[
                ~track_spots['ID'].isin(track_edges['SPOT_TARGET_ID'])
            ]
            
            if len(root_candidates) == 0:
                continue
            
            root_spot_id = root_candidates.iloc[0]['ID']
            
            # Start recursive DFS
            self._dfs_build_subtrack(
                current_spot_id=root_spot_id,
                track_id=track_id,
                track_spots=track_spots,
                track_edges=track_edges,
                parent_subtrack_id=None,
                generation=0
            )
        
        print(f"  ✓ Generated {self.subtrack_counter} subtracks from {len(self.filtered_tracks)} tracks")
    
    def _dfs_build_subtrack(
        self,
        current_spot_id: int,
        track_id: int,
        track_spots: pd.DataFrame,
        track_edges: pd.DataFrame,
        parent_subtrack_id: Optional[int],
        generation: int
    ):
        """
        Recursive DFS to build subtracks.
        
        Args:
            current_spot_id: Starting spot for this subtrack
            track_id: Original track ID
            track_spots: All spots in the track
            track_edges: All edges in the track
            parent_subtrack_id: Parent subtrack ID (None for root)
            generation: Generation number (0 for root)
        """
        # Assign new subtrack ID and index
        self.track_subtrack_counters[track_id] += 1
        subtrack_index = self.track_subtrack_counters[track_id]
        subtrack_id = f"Track_{track_id}_Sub_{subtrack_index}"
        self.subtrack_counter += 1
        
        # Collect spots for this subtrack
        subtrack_spot_ids = []
        current_id = current_spot_id
        
        while current_id is not None:
            subtrack_spot_ids.append(current_id)
            
            # Find outgoing edges from current spot
            outgoing_edges = track_edges[track_edges['SPOT_SOURCE_ID'] == current_id]
            
            if len(outgoing_edges) == 0:
                # Terminal spot - end of subtrack
                break
            elif len(outgoing_edges) == 1:
                # No split - continue to next spot
                current_id = outgoing_edges.iloc[0]['SPOT_TARGET_ID']
            else:
                # Split detected - include split spot in this subtrack, then branch
                # Process each daughter branch as new subtrack
                for _, edge in outgoing_edges.iterrows():
                    daughter_spot_id = edge['SPOT_TARGET_ID']
                    self._dfs_build_subtrack(
                        current_spot_id=daughter_spot_id,
                        track_id=track_id,
                        track_spots=track_spots,
                        track_edges=track_edges,
                        parent_subtrack_id=subtrack_id,
                        generation=generation + 1
                    )
                break
        
        # Get frame statistics first
        subtrack_spots = track_spots[track_spots['ID'].isin(subtrack_spot_ids)].sort_values('FRAME')
        start_frame = int(subtrack_spots['FRAME'].min())
        end_frame = int(subtrack_spots['FRAME'].max())
        duration = end_frame - start_frame
        
        # Store subtrack lineage info
        self.subtrack_lineage.append({
            'SUBTRACK_ID': subtrack_id,
            'TRACK_ID': track_id,
            'SUBTRACK_INDEX': subtrack_index,
            'START_FRAME': start_frame,
            'END_FRAME': end_frame,
            'DURATION': duration,
            'NUMBER_SPOTS': len(subtrack_spot_ids)
        })
        
        # Compute statistics for this subtrack
        self._compute_subtrack_statistics(
            subtrack_id=subtrack_id,
            subtrack_index=subtrack_index,
            subtrack_spot_ids=subtrack_spot_ids,
            track_id=track_id,
            track_spots=track_spots,
            parent_subtrack_id=parent_subtrack_id,
            generation=generation
        )
        
        # Assign edges to this subtrack
        self._assign_edges_to_subtrack(
            subtrack_id=subtrack_id,
            subtrack_spot_ids=subtrack_spot_ids,
            track_edges=track_edges
        )
    
    def _compute_subtrack_statistics(
        self,
        subtrack_id: str,
        subtrack_index: int,
        subtrack_spot_ids: List[int],
        track_id: int,
        track_spots: pd.DataFrame,
        parent_subtrack_id: Optional[str],
        generation: int
    ):
        """Compute motion statistics for a subtrack."""
        # Get spots for this subtrack
        spots = track_spots[track_spots['ID'].isin(subtrack_spot_ids)].sort_values('FRAME')
        
        # Calculate mean quality and intensity
        mean_quality = spots['QUALITY'].mean() if 'QUALITY' in spots.columns else 0
        mean_intensity = spots['MEAN_INTENSITY_CH1'].mean() if 'MEAN_INTENSITY_CH1' in spots.columns else 0
        
        # Calculate number of edges (n_spots - 1)
        number_edges = len(spots) - 1 if len(spots) > 1 else 0
        
        if len(spots) < 2:
            # Need at least 2 spots for statistics
            self.subtrack_stats.append({
                'SUBTRACK_ID': subtrack_id,
                'TRACK_ID': track_id,
                'SUBTRACK_INDEX': subtrack_index,
                'START_FRAME': int(spots['FRAME'].min()) if len(spots) > 0 else 0,
                'END_FRAME': int(spots['FRAME'].max()) if len(spots) > 0 else 0,
                'NUMBER_SPOTS': len(spots),
                'NUMBER_EDGES': number_edges,
                'SUBTRACK_DURATION': 0,
                'SUBTRACK_START': int(spots['FRAME'].min()) if len(spots) > 0 else 0,
                'SUBTRACK_STOP': int(spots['FRAME'].max()) if len(spots) > 0 else 0,
                'SUBTRACK_DISPLACEMENT': 0,
                'SUBTRACK_X_LOCATION': spots['POSITION_X'].mean() if len(spots) > 0 else 0,
                'SUBTRACK_Y_LOCATION': spots['POSITION_Y'].mean() if len(spots) > 0 else 0,
                'START_X': spots.iloc[0]['POSITION_X'] if len(spots) > 0 else 0,
                'START_Y': spots.iloc[0]['POSITION_Y'] if len(spots) > 0 else 0,
                'END_X': spots.iloc[-1]['POSITION_X'] if len(spots) > 0 else 0,
                'END_Y': spots.iloc[-1]['POSITION_Y'] if len(spots) > 0 else 0,
                'SUBTRACK_MEAN_SPEED': 0,
                'SUBTRACK_MAX_SPEED': 0,
                'SUBTRACK_MIN_SPEED': 0,
                'SUBTRACK_MEDIAN_SPEED': 0,
                'SUBTRACK_STD_SPEED': 0,
                'TOTAL_DISTANCE_TRAVELED': 0,
                'MAX_DISTANCE_TRAVELED': 0,
                'CONFINEMENT_RATIO': 0,
                'MEAN_STRAIGHT_LINE_SPEED': 0,
                'LINEARITY_OF_FORWARD_PROGRESSION': 0,
                'MEAN_DIRECTIONAL_CHANGE_RATE': 0,
                'OUTREACH_RATIO': 0,
                'TORTUOSITY': 0,
                'SUBTRACK_MEAN_QUALITY': mean_quality,
                'SUBTRACK_MEAN_INTENSITY_CH1': mean_intensity
            })
            return
        
        # Basic measurements
        n_spots = len(spots)
        duration = spots['FRAME'].max() - spots['FRAME'].min()
        
        # Position arrays
        x = spots['POSITION_X'].values
        y = spots['POSITION_Y'].values
        
        # Calculate displacements
        dx = np.diff(x)
        dy = np.diff(y)
        step_distances = np.sqrt(dx**2 + dy**2)
        
        # Total distance traveled
        total_distance = np.sum(step_distances)
        
        # Net displacement (start to end)
        net_displacement = np.sqrt((x[-1] - x[0])**2 + (y[-1] - y[0])**2)
        
        # Max distance from origin
        distances_from_start = np.sqrt((x - x[0])**2 + (y - y[0])**2)
        max_distance = np.max(distances_from_start)
        
        # Speed calculations
        speeds = step_distances
        mean_speed = np.mean(speeds) if len(speeds) > 0 else 0
        max_speed = np.max(speeds) if len(speeds) > 0 else 0
        min_speed = np.min(speeds) if len(speeds) > 0 else 0
        median_speed = np.median(speeds) if len(speeds) > 0 else 0
        std_speed = np.std(speeds) if len(speeds) > 0 else 0
        
        # Straight line speed (net displacement / duration)
        mean_straight_line_speed = net_displacement / duration if duration > 0 else 0
        
        # Linearity (net displacement / total distance)
        linearity_forward = net_displacement / total_distance if total_distance > 0 else 0
        
        # Confinement ratio
        confinement_ratio = net_displacement / total_distance if total_distance > 0 else 0
        
        # Outreach ratio (max distance / total distance)
        outreach_ratio = max_distance / total_distance if total_distance > 0 else 0
        
        # Tortuosity (total distance / net displacement)
        tortuosity = total_distance / net_displacement if net_displacement > 0 else 0
        
        # Directional change rate
        if len(dx) > 1:
            angles = np.arctan2(dy, dx)
            angle_changes = np.abs(np.diff(angles))
            angle_changes = np.where(angle_changes > np.pi, 2*np.pi - angle_changes, angle_changes)
            mean_angle_change = np.mean(angle_changes)
            directional_change_rate = mean_angle_change
        else:
            mean_angle_change = 0
            directional_change_rate = 0
        
        # Calculate mean quality and intensity
        mean_quality = spots['QUALITY'].mean() if 'QUALITY' in spots.columns else 0
        mean_intensity = spots['MEAN_INTENSITY_CH1'].mean() if 'MEAN_INTENSITY_CH1' in spots.columns else 0
        
        # Calculate number of edges
        number_edges = len(spots) - 1
        
        # Store statistics with corrected column names
        self.subtrack_stats.append({
            'SUBTRACK_ID': subtrack_id,
            'TRACK_ID': track_id,
            'SUBTRACK_INDEX': subtrack_index,
            'START_FRAME': int(spots['FRAME'].min()),
            'END_FRAME': int(spots['FRAME'].max()),
            'NUMBER_SPOTS': n_spots,
            'NUMBER_EDGES': number_edges,
            'SUBTRACK_DURATION': int(duration),
            'SUBTRACK_START': int(spots['FRAME'].min()),
            'SUBTRACK_STOP': int(spots['FRAME'].max()),
            'SUBTRACK_DISPLACEMENT': net_displacement,
            'SUBTRACK_X_LOCATION': np.mean(x),
            'SUBTRACK_Y_LOCATION': np.mean(y),
            'START_X': x[0],
            'START_Y': y[0],
            'END_X': x[-1],
            'END_Y': y[-1],
            'SUBTRACK_MEAN_SPEED': mean_speed,
            'SUBTRACK_MAX_SPEED': max_speed,
            'SUBTRACK_MIN_SPEED': min_speed,
            'SUBTRACK_MEDIAN_SPEED': median_speed,
            'SUBTRACK_STD_SPEED': std_speed,
            'TOTAL_DISTANCE_TRAVELED': total_distance,
            'MAX_DISTANCE_TRAVELED': max_distance,
            'CONFINEMENT_RATIO': confinement_ratio,
            'MEAN_STRAIGHT_LINE_SPEED': mean_straight_line_speed,
            'LINEARITY_OF_FORWARD_PROGRESSION': linearity_forward,
            'MEAN_DIRECTIONAL_CHANGE_RATE': directional_change_rate,
            'OUTREACH_RATIO': outreach_ratio,
            'TORTUOSITY': tortuosity,
            'SUBTRACK_MEAN_QUALITY': mean_quality,
            'SUBTRACK_MEAN_INTENSITY_CH1': mean_intensity
        })
    
    def _assign_edges_to_subtrack(
        self,
        subtrack_id: str,
        subtrack_spot_ids: List[int],
        track_edges: pd.DataFrame
    ):
        """Assign edges to a subtrack."""
        subtrack_edge_mask = (
            track_edges['SPOT_SOURCE_ID'].isin(subtrack_spot_ids) &
            track_edges['SPOT_TARGET_ID'].isin(subtrack_spot_ids)
        )
        
        edges_in_subtrack = track_edges[subtrack_edge_mask].copy()
        edges_in_subtrack['SUBTRACK_ID'] = subtrack_id
        
        self.subtrack_edges.append(edges_in_subtrack)
    
    def generate_subtrack_edges(self):
        """Consolidate all subtrack edges into a single DataFrame."""
        print(f"\nGenerating subtrack-grouped edges...")
        
        if self.subtrack_edges:
            self.subtrack_edges_df = pd.concat(self.subtrack_edges, ignore_index=True)
            print(f"  ✓ Assigned {len(self.subtrack_edges_df)} edges to subtracks")
        else:
            self.subtrack_edges_df = pd.DataFrame()
            print(f"  ✗ No edges to assign")
    
    def save_results(self, output_folder: Path, base_name: str):
        """Save analysis results to CSV files."""
        output_folder.mkdir(parents=True, exist_ok=True)
        
        print(f"\nSaving results to {output_folder}...")
        
        # Save subtrack statistics
        stats_df = pd.DataFrame(self.subtrack_stats)
        stats_file = output_folder / f"{base_name}-subtrack_statistics.csv"
        stats_df.to_csv(stats_file, index=False)
        print(f"  ✓ {stats_file.name} ({len(stats_df)} subtracks)")
        
        # Save subtrack edges
        edges_file = output_folder / f"{base_name}-subtrack_edges.csv"
        self.subtrack_edges_df.to_csv(edges_file, index=False)
        print(f"  ✓ {edges_file.name} ({len(self.subtrack_edges_df)} edges)")
        
        # Save subtrack lineage
        lineage_df = pd.DataFrame(self.subtrack_lineage)
        lineage_file = output_folder / f"{base_name}-subtrack_lineage.csv"
        lineage_df.to_csv(lineage_file, index=False)
        print(f"  ✓ {lineage_file.name} ({len(lineage_df)} lineage records)")
    
    def run(self):
        """Execute the complete analysis pipeline."""
        print("=" * 80)
        print("SUBTRACK LINEAGE ANALYSIS PIPELINE")
        print("=" * 80)
        
        # Load data
        print("Loading TrackMate data files...")
        if not self.load_data():
            return False
        
        # Apply QC filters
        self.apply_qc_filter()
        
        if len(self.filtered_tracks) == 0:
            print("\n✗ No tracks remaining after QC filtering!")
            return False
        
        # Build subtrack tree
        self.build_subtrack_tree()
        
        # Generate edges
        self.generate_subtrack_edges()
        
        # Save results
        csv_files = list(self.tracking_result_folder.glob("*-all-spots.csv"))
        if not csv_files:
            csv_files = list(self.tracking_result_folder.glob("*-spots.csv"))
        
        if '-all-spots' in csv_files[0].stem:
            base_name = csv_files[0].stem.replace('-all-spots', '')
        else:
            base_name = csv_files[0].stem.replace('-spots', '')
        
        output_folder = self.tracking_result_folder / "secondary_analysis"
        self.save_results(output_folder, base_name)
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE!")
        print("=" * 80)
        
        return True


def batch_analyze_all_locations(
    parent_folder: Path,
    max_splits: int = None,
    min_duration: int = None
) -> Dict[str, bool]:
    """
    Batch process all locations under a parent folder.
    
    Args:
        parent_folder: Parent folder to search for locations
        max_splits: Maximum allowed splits per track
        min_duration: Minimum track duration in frames
    
    Returns:
        Dictionary mapping location names to success status
    """
    parent_path = Path(parent_folder)
    
    # Find all 'Tracking Result' folders
    print("Searching for Tracking Result folders...")
    tracking_result_folders = []
    
    for item in parent_path.rglob('*'):
        if item.is_dir() and item.name == 'Tracking Result':
            tracking_result_folders.append(item)
    
    print(f"Found {len(tracking_result_folders)} locations to process\n")
    
    if len(tracking_result_folders) == 0:
        print("No 'Tracking Result' folders found!")
        return {}
    
    # Process each location
    results = {}
    successful = 0
    failed = 0
    
    for idx, tracking_result_folder in enumerate(tracking_result_folders, 1):
        location_name = clean_location_name(tracking_result_folder.parent.name)  # Remove '_cropped' suffix if present
        
        print(f"[{idx}/{len(tracking_result_folders)}] Processing: {location_name}")
        print("-" * 80)
        
        try:
            analyzer = SubtrackAnalyzer(
                tracking_result_folder,
                max_splits=max_splits,
                min_duration=min_duration
            )
            success = analyzer.run()
            
            if success:
                print(f"✓ {location_name} completed successfully\n")
                results[location_name] = True
                successful += 1
            else:
                print(f"✗ {location_name} failed\n")
                results[location_name] = False
                failed += 1
                
        except Exception as e:
            print(f"✗ Error processing {location_name}: {e}\n")
            results[location_name] = False
            failed += 1
    
    # Print summary
    print("=" * 80)
    print("BATCH ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"Total locations: {len(tracking_result_folders)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print("=" * 80)
    
    return results


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================
def main():
    """Command line interface for subtrack analysis."""
    parser = argparse.ArgumentParser(
        description='Subtrack Lineage Analysis Pipeline - Analyze TrackMate tracking data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Batch process all locations in a parent folder
  python subtrack_lineage_analysis.py --batch "C:\\Tracking Data\\Test_Data_E7_8"
  
  # Process a single Tracking Result folder
  python subtrack_lineage_analysis.py --folder "C:\\Tracking Data\\Test_Data_E7_8\\Tracking Result"
  
  # Customize QC parameters
  python subtrack_lineage_analysis.py --batch "C:\\Data" --max-splits 5 --min-duration 15
        """
    )
    
    # Input options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--batch', '-b', type=str, metavar='PARENT_FOLDER',
                       help='Batch process all "Tracking Result" folders under this parent folder')
    group.add_argument('--folder', '-f', type=str, metavar='TRACKING_RESULT_FOLDER',
                       help='Process a single "Tracking Result" folder')
    
    # QC parameters
    parser.add_argument('--max-splits', '-s', type=int, default=MAX_SPLITS_ALLOWED,
                        help=f'Maximum number of splits allowed per track (default: {MAX_SPLITS_ALLOWED})')
    parser.add_argument('--min-duration', '-d', type=int, default=MIN_TRACK_DURATION_FRAMES,
                        help=f'Minimum track duration in frames (default: {MIN_TRACK_DURATION_FRAMES})')
    
    args = parser.parse_args()
    
    # Batch processing mode
    if args.batch:
        parent_folder = Path(args.batch)
        if not parent_folder.exists():
            print(f"✗ Error: Parent folder not found: {parent_folder}")
            sys.exit(1)
        
        results = batch_analyze_all_locations(
            parent_folder,
            max_splits=args.max_splits,
            min_duration=args.min_duration
        )
        
        # Exit with error code if any location failed
        failed_count = sum(1 for success in results.values() if not success)
        sys.exit(0 if failed_count == 0 else 1)
    
    # Single folder mode
    elif args.folder:
        tracking_folder = Path(args.folder)
        if not tracking_folder.exists():
            print(f"✗ Error: Tracking Result folder not found: {tracking_folder}")
            sys.exit(1)
        
        analyzer = SubtrackAnalyzer(
            tracking_folder,
            max_splits=args.max_splits,
            min_duration=args.min_duration
        )
        
        success = analyzer.run()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
