"""
Configuration Manager Module

Handles user configuration including paths and parameters.
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional


class ConfigManager:
    """Manages pipeline configuration parameters."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration JSON file (optional)
        """
        self.config_file = config_file
        self.config = {}
        
        # Default configuration
        self.defaults = {
            'channel_names': ['Green', 'Phase', 'Red'],
            'stardist_model_path': '',
            'max_splits_allowed': 3,
            'min_track_duration_frames': 20,
            'working_directory': '',
            'input_data_folder': '',
            'input_mask_folder': 'InputMask',
            'output_tracks_folder': 'OutputTracks'
        }
        
        self.config = self.defaults.copy()
        
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
            self.config.update(loaded_config)
            print(f"✓ Configuration loaded from {config_file}")
        except Exception as e:
            print(f"⚠ Failed to load config file: {e}")
            print("Using default configuration.")
    
    def save_config(self, config_file: str):
        """Save configuration to JSON file."""
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✓ Configuration saved to {config_file}")
        except Exception as e:
            print(f"✗ Failed to save config file: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value."""
        self.config[key] = value
    
    def validate_paths(self) -> bool:
        """
        Validate all required paths exist.
        
        Returns:
            True if all paths are valid
        """
        required_paths = ['working_directory', 'input_data_folder']
        
        for path_key in required_paths:
            path = self.config.get(path_key)
            if not path or not os.path.exists(path):
                print(f"✗ Invalid or missing path for '{path_key}': {path}")
                return False
        
        # Check StarDist model
        model_path = self.config.get('stardist_model_path')
        if model_path and not os.path.exists(model_path):
            print(f"⚠ StarDist model path not found: {model_path}")
            print("  Segmentation step will fail if executed.")
        
        return True
    
    def setup_working_directories(self) -> bool:
        """
        Create necessary working directories.
        
        Returns:
            True if successful
        """
        try:
            working_dir = Path(self.config['working_directory'])
            
            # Create InputMask folder
            input_mask_path = working_dir / self.config['input_mask_folder']
            input_mask_path.mkdir(parents=True, exist_ok=True)
            self.config['input_mask_full_path'] = str(input_mask_path)
            
            # Create OutputTracks folder
            output_tracks_path = working_dir / self.config['output_tracks_folder']
            output_tracks_path.mkdir(parents=True, exist_ok=True)
            self.config['output_tracks_full_path'] = str(output_tracks_path)
            
            print(f"✓ Created working directories:")
            print(f"  - {input_mask_path}")
            print(f"  - {output_tracks_path}")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to create working directories: {e}")
            return False
    
    def get_channel_names(self) -> List[str]:
        """Get channel names."""
        return self.config.get('channel_names', self.defaults['channel_names'])
    
    def display_config(self):
        """Display current configuration."""
        print("\n" + "=" * 80)
        print("CURRENT CONFIGURATION")
        print("=" * 80)
        for key, value in self.config.items():
            if isinstance(value, (str, int, float, bool)):
                print(f"  {key}: {value}")
            elif isinstance(value, list):
                print(f"  {key}: {', '.join(map(str, value))}")
        print("=" * 80)
