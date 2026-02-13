"""
Launch script for the Pipeline GUI Application.

启动细胞追踪数据处理平台图形界面。
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pipeline_gui import main

if __name__ == "__main__":
    main()
