"""
Launch script for Lammerding Lab Cell Tracking Support.

Author: Oriana Chen
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pipeline_gui import main

if __name__ == "__main__":
    main()
