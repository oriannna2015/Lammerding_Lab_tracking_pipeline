# Integrated Cell Tracking Pipeline

**Version**: 2.0
**Date**: February 12, 2026
**Author**: Oriana Chen

---

## Overview

This integrated pipeline automates cell tracking data processing from raw multi-channel images through complete lineage analysis. It combines automated steps with guided manual interventions for tasks requiring specialized Fiji/ImageJ plugins.

**What makes this pipeline special?**

- **🖥️ Graphical User Interface (GUI)**: Easy-to-use visual interface with real-time progress monitoring
- **Auto-Generated Scripts**: Pipeline automatically generates customized ImageJ macros and guides based on your specific data structure, paths, and configuration. No manual path editing required!

### Key Features

- **🖥️ Graphical Interface**: Modern GUI with tabs for configuration, pipeline control, and log monitoring
- **Unified Workflow**: Single entry point handles both single locations and batch processing
- **Interactive Setup**: Guided configuration of paths and parameters (both GUI and CLI modes)
- **Auto-Generated Scripts**: Pipeline generates ready-to-use ImageJ macros and guides
  - `stabilization_batch_macro.ijm` - Customized for your data structure
  - `TrackMate_操作指南.txt` - Detailed instructions with location-specific examples
- **Automated Steps**: Channel splitting, segmentation, fluorescence analysis, and subtrack analysis
- **Smart Verification**: Automatic checks after each manual step with visual feedback
- **Flexible Processing**: Works with standard experimental folder structures
- **Restartable**: All steps can resume from interruptions

---

## Pipeline Steps

### 1. Channel Splitting (Automated)

Splits multi-channel TIFF sequences into separate channel folders (Green, Phase, Red).

**Input**: Raw multi-channel image sequences
**Output**: Organized channel folders for each location

### 2. Image Stabilization (Manual - Fiji)

Pipeline automatically generates a customized ImageJ macro script for your data. Simply run it in Fiji.

**Input**: Split channel folders**Output**:

- `stabilization_batch_macro.ijm` (auto-generated script)
- `*_Red_Stabilized.tif`, `*_Green_Stabilized.tif`, `*_Phase_Stabilized.tif` (per location)

### 3. Cell Segmentation (Automated)

Applies trained StarDist model to segment cells in Red channel images.

**Input**: Red stabilized images
**Output**: Segmentation masks in `InputMask/` folder

### 4. TrackMate Tracking (Manual - Fiji)

Pipeline generates a detailed operation guide with naming examples for all your locations.

**Input**: Segmentation masks from `InputMask/`**Output**:

- `TrackMate_操作指南.txt` (detailed step-by-step guide in Chinese)
- CSV files (spots, edges, tracks) in `Tracking Result/` subfolder per location

### 5. Fluorescence Intensity Analysis (Automated)

Extracts Red/Green fluorescence intensities for each tracked cell over time.

**Input**: Tracking results, segmentation masks, fluorescence images
**Output**: Intensity timeseries CSV files

### 6. Subtrack Lineage Analysis (Automated)

Analyzes cell division events and generates subtrack statistics.

**Input**: TrackMate tracking results
**Output**: Subtrack statistics, edges, and lineage CSV files in `secondary_analysis/` subfolder

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Fiji/ImageJ with Image Stabilizer and TrackMate plugins

### Setup

1. **Clone or download this repository**

```bash
cd "C:\Tracking Data\Updated_Pipeline_Resource_Package"
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Verify Fiji installation**
   - Ensure Image Stabilizer plugin is installed
   - Ensure TrackMate plugin is installed

---

## Usage

- GUI Mode (推荐 Recommended) 🖥️

**启动图形界面 / Launch GUI:**

```bash
cd "C:\Tracking Data\Updated_Pipeline_Resource_Package"
python run_gui.py
```

**使用步骤 / Usage Steps:**

1. **⚙️ 配置标签页 (Configuration Tab)**:

   - 设置原始数据文件夹 / Set input data folder
   - 设置工作目录 / Set working directory
   - 设置 StarDist 模型路径 / Set StarDist model path
   - 配置通道名称 / Configure channel names (default: Green, Phase, Red)
   - 调整 QC 参数 / Adjust QC parameters
   - 保存配置 / Save configuration
2. **▶️ 处理流程标签页 (Pipeline Tab)**:

   - 点击"扫描数据文件夹"查看 locations / Click "Scan Data Folder"
   - 依次执行各步骤 / Execute each step sequentially
   - 手动步骤会生成脚本和指南 / Manual steps generate scripts/guides
   - 完成后验证结果 / Verify results after completion
3. **📋 日志标签页 (Log Tab)**:

   - 实时查看处理日志 / View processing logs in real-time
   - 保存日志以便后续查看 / Save logs for later review

### Alternative - Command Line Mode

Run the integrated pipeline in interactive mod
Run the integrated pipeline:

```bash
cd "C:\Tracking Data\Updated_Pipeline_Resource_Package"
python src/integrated_pipeline.py
```

The pipeline will:

1. Guide you through interactive setup (first time only)
2. Scan your data and show what it found
3. Process Step 1 (Channel Splitting)
4. **Generate `stabilization_batch_macro.ijm`** - Just run it in Fiji!
5. Verify stabilization results
6. Process Step 3 (Segmentation)
7. **Generate `TrackMate_操作指南.txt`** - Follow the guide for each location
8. Verify TrackMate results
9. Process Steps 5-6 (Fluorescence & Subtrack analysis)

**First time?** The setup wizard will ask for:

- Input data folder (your raw images)
- Working directory (where to save results)
- StarDist model path (for segmentation)
- Channel names (default: Green, Phase, Red)

### Input Data Structure

Your input data should be organized as:

```
Input_Data_Folder/
├── Rep 1/
│   ├── 0-24h/
│   │   ├── 10um/
│   │   │   ├── B1_2/
│   │   │   │   ├── B1_2_0001.tif
│   │   │   │   ├── B1_2_0002.tif
│   │   │   │   └── ...
│   │   │   └── B1_3/
│   │   ├── Dense/
│   │   └── 5um/
│   ├── 24-48h/
│   └── ...
├── Rep 3/
└── Rep 4/
```

### Output Structure

Processed data will be organized in your working directory:

```
Working_Directory/
├── InputMask/                          # Segmentation masks
│   ├── Rep-1_0-24h_10um_B1_2_Red_Seg.tif
│   └── ...
├── OutputTracks/                       # (Reserved for future use)
├── Rep 1/
│   ├── 0-24h/
│   │   ├── 10um/
│   │   │   ├── B1_2/
│   │   │   │   ├── B1_2_Green/       # Split channels
│   │   │   │   ├── B1_2_Phase/
│   │   │   │   ├── B1_2_Red/
│   │   │   │   ├── B1_2_Red_Stabilized.tif     # Stabilized images
│   │   │   │   ├── B1_2_Green_Stabilized.tif
│   │   │   │   ├── B1_2_Phase_Stabilized.tif
│   │   │   │   └── Tracking Result/
│   │   │   │       ├── Rep-1_0-24h_10um_B1_2_Red_Seg-spots.csv
│   │   │   │       ├── Rep-1_0-24h_10um_B1_2_Red_Seg-edges.csv
│   │   │   │       ├── Rep-1_0-24h_10um_B1_2_Red_Seg-tracks.csv
│   │   │   │       ├── Rep-1_0-24h_10um_B1_2_Red_Seg-intensity_timeseries.csv
│   │   │   │       └── secondary_analysis/
│   │   │   │           ├── Rep-1_0-24h_10um_B1_2_Red_Seg-subtrack_statistics.csv
│   │   │   │           ├── Rep-1_0-24h_10um_B1_2_Red_Seg-subtrack_edges.csv
│   │   │   │           └── Rep-1_0-24h_10um_B1_2_Red_Seg-subtrack_lineage.csv
│   │   │   └── ...
└── pipeline_config.json                # Saved configuration
```

---

## Configuration

### Interactive Setup

The pipeline includes an interactive setup that collects:

1. **Input Data Folder**: Location of raw experimental data
2. **Working Directory**: Where processed data will be stored
3. **Channel Names**: Defaults to `['Green', 'Phase', 'Red']`
4. **StarDist Model Path**: Path to trained segmentation model
5. **QC Parameters**:
   - Max splits per track (default: 3)
   - Min track duration in frames (default: 20)

Configuration is saved as `pipeline_config.json` in the working directory for reuse.

### Manual Configuration

You can also create a `pipeline_config.json` file manually:

```json
{
  "channel_names": ["Green", "Phase", "Red"],
  "stardist_model_path": "C:\\Path\\To\\StarDist_Model",
  "max_splits_allowed": 3,
  "min_track_duration_frames": 20,
  "working_directory": "C:\\Tracking Data\\Working",
  "input_data_folder": "C:\\Tracking Data\\Test_Data_Folder",
  "input_mask_folder": "InputMask",
  "output_tracks_folder": "OutputTracks"
}
```

---

## Manual Steps Guide

### Image Stabilization

The pipeline automatically generates a ready-to-use ImageJ macro script:

**Workflow**:

1. **Run Step 2** in the pipeline
2. **Pipeline generates** `stabilization_batch_macro.ijm` in your working directory
3. **Open Fiji/ImageJ**
4. **Run the macro**: Plugins → Macros → Run... → Select `stabilization_batch_macro.ijm`
5. **Wait for completion** - macro will show progress for each location
6. **Verify results** - pipeline will check all stabilized files exist
7. **Continue to Step 3**

**Features of the generated macro**:

- Automatically processes all locations in your data
- Skips already-processed locations (restartable)
- Shows progress messages for each location
- Handles missing data gracefully
- Adapted to your specific channel names and folder structure

**No manual editing required** - the script is customized for your exact configuration!

### TrackMate Tracking

The pipeline generates a comprehensive guide with examples for all your locations:

**Workflow**:

1. **Run Step 4** in the pipeline
2. **Pipeline generates** `TrackMate_操作指南.txt` with:
   - Detailed step-by-step instructions (in Chinese)
   - Correct file naming for each of your locations
   - Parameter recommendations
   - Quality checklist
3. **Follow the guide** to process each location in Fiji
4. **Export CSV files** to `[location]/Tracking Result/` folder
5. **Verify results** - pipeline checks all required files exist
6. **Continue to Step 5**

**Key Points**:

- Use "Label image detector" in TrackMate
- Export all three CSV files: spots, edges, tracks
- Follow exact naming format provided in the guide
- Can process in batches - completed locations are detected automatically

**The generated guide includes**:

- Complete location list with mask file names
- Expected output file names for each location
- Parameter suggestions based on your data
- Troubleshooting tips

---

## Module Reference

### `pipeline_gui.py` ⭐ NEW

**Graphical User Interface for the pipeline.**

**Key Features**:

- Configuration management with visual forms
- Real-time pipeline execution with progress tracking
- Automatic script generation for manual steps
- Verification dialogs with visual feedback
- Log viewing and saving capabilities

**Main Class**:

- `PipelineGUI`: Main GUI application with notebook tabs for Configuration, Pipeline, and Logs

**Usage**:

```bash
python run_gui.py
```

### `integrated_pipeline.py`

**Main pipeline orchestrator (also supports CLI mode).**

**Key Methods**:

- `setup()`: Interactive configuration wizard
- `run_full_pipeline()`: Execute all steps end-to-end
- `_generate_stabilization_macro()`: Auto-generate ImageJ macro
- `_generate_trackmate_guide()`: Auto-generate TrackMate guide
- `_verify_stabilization()`: Check stabilized files
- `_verify_trackmate()`: Check tracking results

### `config_manager.py`

Handles pipeline configuration including path validation and working directory setup.

**Key Methods**:

- `load_config(config_file)`: Load from JSON
- `save_config(config_file)`: Save to JSON
- `validate_paths()`: Verify all required paths exist
- `setup_working_directories()`: Create InputMask and OutputTracks folders

### `folder_utils.py`

Utilities for folder scanning and path management.

**Key Functions**:

- `scan_data_folder_structure(root)`: Find all locations in data folder
- `find_tracking_results(root)`: Locate all Tracking Result folders
- `get_location_identifier(rep, timepoint, datatype, location)`: Generate unique location ID

### `channel_splitter.py`

Splits multi-channel images into separate channel folders.

**Key Methods**:

- `split_location(source, target, location_name)`: Process single location
- `batch_split(locations, output_root)`: Process multiple locations

### `segmentation.py`

Performs cell segmentation using StarDist model.

**Key Methods**:

- `load_model()`: Initialize StarDist model
- `segment_image(input, output)`: Segment single image stack
- `batch_segment(locations, output_folder)`: Process multiple locations

### `fluorescence_analyzer.py`

Extracts fluorescence intensity from tracked cells.

**Key Methods**:

- `analyze_location(location_info)`: Process single location
- `batch_analyze(locations)`: Process multiple locations

### `subtrack_lineage_analysis.py`

Analyzes cell division and generates subtrack lineages.

**Key Functions**:

- `SubtrackAnalyzer.run()`: Analyze single Tracking Result folder
- `batch_analyze_all_locations(parent_folder, max_splits, min_duration)`: Process all locations

### `integrated_pipeline.py`

Main pipeline orchestrator with interactive workflow.

**Key Methods**:

- `setup()`: Interactive configuration
- `scan_locations()`: Discover all locations in data folder
- `run_full_pipeline()`: Execute complete workflow

---

## Troubleshooting

### Common Issues

**Issue**: "No .tif files found"
**Solution**: Verify input folder structure matches expected format

**Issue**: "StarDist model not found"
**Solution**: Check model path in configuration, ensure folder name is exact

**Issue**: "Segmentation mask not found"
**Solution**: Ensure segmentation step completed successfully, check `InputMask/` folder

**Issue**: "No Tracking Result folder"
**Solution**: Complete TrackMate step and ensure CSV files are exported to correct location

### Data Validation

Before running the pipeline:

1. Verify input folder structure matches expected format
2. Ensure all TIFF files are readable
3. Check that StarDist model path is correct
4. Confirm Fiji plugins are installed

---

## Quality Control

### Track Filtering Parameters

The subtrack analysis applies quality control filters:

- **Max Splits**: Removes tracks with excessive division events (default: 3)
- **Min Duration**: Filters out short-lived tracks (default: 20 frames)

These parameters can be adjusted during setup or in the configuration file.

### Output Validation

Check these key outputs:

1. **Channel splitting**: Verify channel folders contain correct number of files
2. **Segmentation**: Inspect masks in `InputMask/` for quality
3. **Fluorescence analysis**: Check intensity timeseries CSV for reasonable values
4. **Subtrack analysis**: Review subtrack statistics for biological plausibility

---

## Performance Notes

- **Segmentation**: Most time-intensive step (~30-60 seconds per frame per location)
- **Batch Processing**: Can process multiple locations sequentially
- **Memory Usage**: Segmentation may require 8-16 GB RAM for large image stacks
- **Disk Space**: Processed data typically requires 2-3x original data size

---

## License

This pipeline is provided for research use. Please cite appropriately when publishing results generated using this software.

---

## References

- **StarDist**: Schmidt U, Weigert M, Broaddus C, Myers G. "Cell Detection with Star-Convex Polygons." MICCAI 2018.
- **TrackMate**: Tinevez JY, et al. "TrackMate: An open and extensible platform for single-particle tracking." Methods 2017.
- **ImageJ**: Schneider CA, Rasband WS, Eliceiri KW. "NIH Image to ImageJ: 25 years of image analysis." Nature Methods 2012.
