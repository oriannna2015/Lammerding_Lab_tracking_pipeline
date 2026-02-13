# Lammerding Lab - Cell Tracking Support

**Computational Pipeline for Multi-Channel Cell Tracking Analysis**

**Version**: 2.0
**Date**: February 13, 2026
**Author**: Oriana Chen
**Contact**: Lammerding Lab

---

## Overview

This computational pipeline provides an integrated workflow for processing multi-channel fluorescence microscopy time-lapse data, from raw image sequences through complete cell lineage and motility analysis. The pipeline combines automated Python scripts with guided Fiji/ImageJ processing steps to handle irregular cell morphologies, track nuclear envelope rupture events via fluorescence intensity ratios, and extract quantitative motility metrics from cell division lineages.

### Purpose

To automate the analysis of cancer cell migration and nuclear envelope integrity by:

- Stabilizing multi-channel time-lapse microscopy images
- Segmenting irregularly-shaped cancer cell nuclei using deep learning (StarDist)
- Tracking cells across time using TrackMate
- Extracting Red/Green fluorescence intensity ratios to monitor nuclear envelope rupture
- Analyzing cell division events and generating subtrack lineages with quality control
- Computing motility metrics (speed, linearity, directional change) for each cell lineage

### Key Features

- **🖥️ Graphical User Interface**: Modern GUI for configuration, execution monitoring, and logging
- **Auto-Generated Scripts**: Pipeline automatically generates customized ImageJ macros and TrackMate guides based on your data structure—no manual path editing required
- **Batch Processing**: Handles multiple experimental replicates, timepoints, and conditions simultaneously
- **Quality Control**: Built-in filtering for division events and track duration
- **Restartable Workflow**: Resume from any step; already-processed data is automatically detected
- **Smart Verification**: Automatic validation after manual steps with visual feedback
- **Modular Design**: Can run individual steps or complete end-to-end pipeline

---

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Input Data Structure](#input-data-structure)
4. [Pipeline Configuration](#pipeline-configuration)
5. [Protocol: Data Processing Workflow](#protocol-data-processing-workflow)
   - [Step 1: Channel Splitting](#step-1-channel-splitting)
   - [Step 2: Image Stabilization](#step-2-image-stabilization)
   - [Step 3: Segmentation using StarDist](#step-3-segmentation-using-stardist)
   - [Step 4: Tracking using TrackMate](#step-4-tracking-using-trackmate)
   - [Step 4.5: Results Relocalization](#step-45-results-relocalization-optional)
   - [Step 5: Fluorescence Intensity Analysis](#step-5-fluorescence-intensity-analysis)
   - [Step 6: Subtrack Lineage Analysis](#step-6-subtrack-lineage-analysis)
6. [Output File Reference](#output-file-reference)
7. [Troubleshooting &amp; Optimization](#troubleshooting--optimization)
8. [Timing &amp; Performance](#timing--performance)
9. [Quality Control Guidelines](#quality-control-guidelines)
10. [References](#references)

---

## System Requirements

### Software Dependencies

- **Python**: 3.8 or higher
- **Fiji/ImageJ**: Latest version with required plugins
  - Image Stabilizer plugin
  - TrackMate plugin (included in Fiji)
- **Operating System**: Windows 10/11, macOS, or Linux

### Python Packages

All required packages are listed in `requirements.txt`:

- numpy
- pandas
- scipy
- scikit-image
- tensorflow (for StarDist)
- stardist
- csbdeep
- tifffile
- tqdm

### Hardware Recommendations

- **RAM**: Minimum 8 GB, recommended 16 GB or more
- **Storage**: 2-3x the size of your raw data (for intermediate and final outputs)
- **GPU**: Optional but recommended for segmentation (CUDA-compatible GPU accelerates StarDist by ~5-10x)
- **Processor**: Multi-core CPU recommended for batch processing

### Conda Environment (Recommended)

Creating a dedicated conda environment ensures package compatibility:

```bash
conda create -n celltrack python=3.9
conda activate celltrack
```

---

## Installation

### Step 1: Clone or Download Repository

```bash
cd "C:\Tracking Data"
# If using git:
git clone <repository_url> Updated_Pipeline_Resource_Package
cd Updated_Pipeline_Resource_Package
```

### Step 2: Install Python Dependencies

**Option A: Automatic Installation (Windows)**

Double-click `Install_Dependencies.bat` (Install_Dependencies.bat)

**Option B: Manual Installation**

```bash
# Activate your conda environment (if using conda)
conda activate celltrack

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Verify Fiji Installation

1. Download Fiji from https://fiji.sc if not already installed
2. Launch Fiji
3. Verify plugins:

   - **Image Stabilizer**: Plugins → Registration → Image Stabilizer
   - **TrackMate**: Plugins → Tracking → TrackMate

   `<<<<Macro Installation Instruction Update I Progress>`>>>

### Step 4: Prepare StarDist Model

**Option A: Use Pre-trained Model**

If you have a pre-trained model, note its directory path (e.g., `StarDist_Cont_Grey_4_200_128_2_0.0003_Aug4_150epoch/`)

**Option B: Train Your Own Model**

Training a custom segmentation model is recommended for optimal performance on your specific cell type. Use **ZeroCostDL4Mic**:

1. Access: https://github.com/HenriquesLab/ZeroCostDL4Mic/wiki
2. Follow StarDist training notebook
3. **Reference Training Parameters** (for nuclear segmentation):
   - **Training Data**: 50 pairs of Mask/Fluorescence images
     - Annotation masks created using StarDist Fiji macro + manual correction
     - Validation split: 10%
     - Augmentation: 4X
   - **Model Parameters**:
     - Patch size: 128
     - Batch size: 4
     - Epochs: 150
     - Learning rate: 0.0003
     - Steps/epoch: 200
4. Download trained model folder to your local directory

---

## Input Data Structure

Your raw microscopy data must follow this hierarchical structure:

```
Input_Data_Folder/
├── Rep 1/                          # Biological replicate 1
│   ├── 0-24h/                      # Timepoint
│   │   ├── Dense/                  # Experimental condition
│   │   │   ├── B1_2/               # Location (field of view)
│   │   │   │   ├── B1_2_0001.tif   # Multi-channel time-lapse stack
│   │   │   │   ├── B1_2_0002.tif
│   │   │   │   └── ...
│   │   │   ├── B1_3/
│   │   │   └── ...
│   │   ├── 5um/
│   │   └── 10um/
│   ├── 24-48h/
│   ├── 48-72h/
│   └── 72-96h/
├── Rep 3/
└── Rep 4/
```

### Requirements

- **File format**: TIFF (.tif) multi-channel stacks
- **Channels**: 3 channels (default: Green, Phase, Red)
  - Modify channel names in configuration if different
- **Naming**: Consistent location names within each condition folder
- **Structure**: Must maintain Replicate → Timepoint → Condition → Location hierarchy

---

## Pipeline Configuration

### Method 1: Graphical Interface (Recommended) 🖥️

**Launch GUI:**

```bash
# Option A: Use batch file (Windows)
Double-click "GUI_init.bat"

# Option B: Run Python directly
python main.py
```

**Configuration Steps:**

1. **⚙️ Configuration Tab**:

   - **Input Data Folder**: Browse to your `Input_Data_Folder/` root
   - **Working Directory**: Choose where processed data will be saved
   - **StarDist Model Path**: Browse to your trained model folder
   - **Channel Names**: Verify or modify (default: Green, Phase, Red)
   - **QC Parameters**:
     - Max Splits Allowed: 3 (filters tracks with excessive divisions)
     - Min Track Duration: 20 frames (filters short-lived tracks)
   - Click **"Save Config"** to save configuration as JSON
   - Click **"Apply Config"** to validate paths and create directories
2. **▶️ Pipeline Tab**:

   - Click **"🔍 Scan Data Folder"** to detect all locations
   - Verify detected location count
   - Execute steps sequentially using **"▶️ Run"** buttons
   - Monitor progress in real-time
3. **📋 Log Tab**:

   - View processing logs
   - Save logs for documentation

### Method 2: Manual Configuration File

Create `pipeline_config.json` in working directory:

```json
{
  "input_data_folder": "C:\\Tracking Data\\Test_Data_Folder",
  "working_directory": "C:\\Tracking Data\\Working",
  "stardist_model_path": "C:\\Models\\StarDist_Cont_Grey_4_200_128_2_0.0003_Aug4_150epoch",
  "channel_names": ["Green", "Phase", "Red"],
  "max_splits_allowed": 3,
  "min_track_duration_frames": 20,
  "input_mask_folder": "InputMask",
  "output_tracks_folder": "OutputTracks"
}
```

---

## Protocol: Data Processing Workflow

### Step 1: Channel Splitting

**Purpose**: Separate multi-channel TIFF stacks into individual channel folders for downstream processing.

**Method**: Automated (Python)

**Procedure**:

1. Launch GUI or run:

   ```bash
   python src/channel_splitter.py
   ```
2. Pipeline will:

   - Scan all locations in input data folder
   - For each location, extract frames from multi-channel TIFFs
   - Save each channel to separate folder:
     - `LocationName_Green/`
     - `LocationName_Phase/`
     - `LocationName_Red/`
3. Progress displayed in GUI log or console

**Expected Output**:

```
Input_Data_Folder/Rep1/0-24h/Dense/B1_2/
├── B1_2_Green/
│   ├── B1_2_Green_0001.tif
│   ├── B1_2_Green_0002.tif
│   └── ...
├── B1_2_Phase/
│   └── ...
└── B1_2_Red/
    └── ...
```

**Timing**: ~2-5 seconds per location (depends on stack size)

**Note**: Already-processed locations are automatically skipped on re-run.

---

### Step 2: Image Stabilization

**Purpose**: Correct for stage drift and sample movement during time-lapse acquisition to enable accurate tracking.

**Method**: Semi-Automated (Pipeline generates ImageJ macro → Manual execution in Fiji)

**Algorithm**: Lucas-Kanade algorithm with affine transformation, pyramid level 3, no template update

**Procedure**:

#### Part A: Generate Stabilization Macro

1. **In Pipeline GUI**: Click **"▶️ Run"** for Step 2

   - Pipeline scans your data structure
   - Auto-generates `image_stabilization_macro.ijm` in working directory
   - Macro is customized with your specific:
     - Root path
     - Replicate names
     - Timepoint names
     - Condition types
2. **Macro Logic**:

   - Opens three independent channels as image sequences
   - Merges as combined RGB
   - Applies Image Stabilizer plugin
   - Splits channels and saves with suffixes:
     - `*_Red_Stabilized.tif`
     - `*_Green_Stabilized.tif`
     - `*_Phase_Stabilized.tif`

#### Part B: Execute in Fiji

3. **Open Fiji**
4. **Run Generated Macro**:

   - Plugins → Scripts → Script Interpreter
   - Paste the content from  `image_stabilization_macro.ijm` into the script box, remember to switch language to ImageJ Macro
   - Click Open
5. **Monitor Progress**:

   - Fiji console shows progress for each location
   - Messages: "▶ Processing: [location]", "✅ Done: [location]"
   - Already-stabilized locations are skipped automatically
6. **Verify in Pipeline**:

   - Return to GUI
   - Click **"✓ Verify Results"** button in dialog
   - Pipeline checks all locations for stabilized files
   - Shows verification status: X/X locations complete

**Expected Output**:

```
Input_Data_Folder/Rep1/0-24h/Dense/B1_2/
├── B1_2_Red_Stabilized.tif    # Grayscale, stabilized
├── B1_2_Green_Stabilized.tif  # Grayscale, stabilized
├── B1_2_Phase_Stabilized.tif  # Grayscale, stabilized
├── B1_2_Green/ (from Step 1)
└── ...
```

**Timing**: ~30-60 seconds per location (depends on stack size and frame count)

**Critical Notes**:

- Output files are in **grayscale** format, ready for segmentation
- Macro is restartable—already-processed locations are automatically skipped
- No manual path editing required

---

### Step 3: Segmentation using StarDist

**Purpose**: Segment irregularly-shaped cancer cell nuclei using a trained StarDist 2D deep learning model.

**Method**: Automated (Python with TensorFlow/StarDist)

**Preparation**:

Ensure conda environment is activated:

```bash
conda activate celltrack
```

**Procedure**:

1. **Verify Model Path**: Ensure StarDist model path is correctly set in configuration
2. **Run Segmentation**:

   - **GUI**: Click **"▶️ Run"** for Step 3
   - **CLI**:
     ```bash
     python src/segmentation.py
     ```
3. **Pipeline will**:

   - Load StarDist model
   - For each location:
     - Load `*_Red_Stabilized.tif` (nuclei channel)
     - Apply model frame-by-frame
     - Generate labeled mask (each nucleus = unique integer label)
     - Save as `Rep-X_Time_Condition_Location_Red_Seg.tif`
   - Save all masks to `Working_Directory/InputMask/` folder
4. **GPU Acceleration**: If available, segmentation automatically uses GPU

**Expected Output**:

```
Working_Directory/
└── InputMask/
    ├── Rep-1_0-24h_Dense_B1_2_Red_Seg.tif
    ├── Rep-1_0-24h_Dense_B1_3_Red_Seg.tif
    ├── Rep-1_0-24h_5um_B2_1_Red_Seg.tif
    └── ...
```

**Timing**: ~30-60 seconds per frame per location (highly dependent on GPU availability)

**Segmentation Output Format**:

- TIFF stack, same dimensions as input
- Integer-labeled (0 = background, 1 = first nucleus, 2 = second nucleus, etc.)
- Grayscale 16-bit
- Ready for TrackMate Label Image Detector

**Note**: This is typically the most time-intensive step. Monitor progress in GUI log.

---

### Step 4: Tracking using TrackMate

**Purpose**: Reconstruct time-resolved cell trajectories based on segmented nuclei masks.

**Method**: Semi-Automated (Pipeline generates guide → Manual execution in Fiji TrackMate)

**Procedure**:

#### Option 1 - Manual Processing via GUI

2. **For each location**:

   a. **Open Mask in Fiji**:

   - File → Open → Select `*_Red_Seg.tif` from `InputMask/`

   b. **Launch TrackMate**:

   - Plugins → Tracking → TrackMate
   - Click "Next"

   c. **Check Dimensions**:

   - Accept auto-detected dimensionality
   - If prompted, swap Z/T so time is assigned as T (not Z)
   - Click "Next"

   d. **Configure Detector**:

   - Select: **"Label image detector"**
   - **Simplify contours**: Enabled
   - Click "Next" → Click "Detect"
   - Verify spots overlay on nuclei

   e. **Initial Filtering** (Optional):

   - Can skip or add filters (e.g., Quality > 0)
   - Click "Next"

   f. **Configure Tracker**:

   - Select: **"LAP Tracker"**
   - **Frame-to-frame linking**:
     - Max distance: 10-20 pixels (adjust based on cell speed)
   - **Track segment gap closing**:
     - Max distance: 20 pixels
     - Max frame gap: 2
   - **Track segment splitting** (enable if observing mitosis):
     - Max distance: 10 pixels
   - **Track segment merging**: DISABLE (not biologically relevant)
   - Click "Next"

   g. **Filter Tracks** (Recommended):

   - Add filter: "Track duration" > 5 frames
   - Removes short-lived spurious tracks
   - Click "Next"

   h. **Display Options**:

   - Skip display configuration
   - Click "Next"

   i. **Export Results**:

   - Actions: **"Export tracks to CSV"**
   - **IMPORTANT**: Export to location folder:
     - Create subfolder: `[location]/Tracking Result/`
     - Save with exact naming format:
       - `Rep-X_Time_Condition_Location_Red_Seg-spots.csv`
       - `Rep-X_Time_Condition_Location_Red_Seg-edges.csv`
       - `Rep-X_Time_Condition_Location_Red_Seg-tracks.csv`
   - See generated guide for exact names

   j. **Optional**: Save TrackMate session (.xml) for future reference
3. **Repeat** for all locations listed in generated guide

#### Option 2 - Batch Processing via TrackMate Batcher

4. **Configure Batch Processing**:

   a. **Open TrackMate Batcher**:

   - Plugins → Tracking → TrackMate Batcher

   b. **Specify Input/Output**:

   - **Input folder**: `Working_Directory/InputMask/`
   - **Output folder**: `Working_Directory/OutputTracks/`
   - **Session file**: Browse for `.xml` template
     - Use example session file from resources package
     - Or save one from manual processing (Option 1)

   c. **Select Outputs**:

   - ✓ Spots CSV
   - ✓ Edges CSV
   - ✓ Tracks CSV
   - ✗ **Uncheck** "The 3 Tables (xlsx)"
     - Known compatibility issue with latest Fiji

   d. **Run Batch**:

   - Click "Run"
   - Monitor progress in console
   - Errors for individual files will be logged but batch continues
5. **Proceed to Step 4.5** to relocalize results to location folders

#### Part D: Verify Tracking Results

6. **In Pipeline GUI**:
   - Click **"✓ Verify Results"** in verification dialog
   - Pipeline checks each location for required CSV files
   - Shows status: X/X locations complete

**Expected Output**:

```
Input_Data_Folder/Rep1/0-24h/Dense/B1_2/
└── Tracking Result/
    ├── Rep-1_0-24h_Dense_B1_2_Red_Seg-spots.csv
    ├── Rep-1_0-24h_Dense_B1_2_Red_Seg-edges.csv
    ├── Rep-1_0-24h_Dense_B1_2_Red_Seg-tracks.csv
    └── (optional) Rep-1_0-24h_Dense_B1_2_Red_Seg.xml
```

**TrackMate Output File Descriptions**:

| File               | Content                                                           | Usage                              |
| ------------------ | ----------------------------------------------------------------- | ---------------------------------- |
| `*-spots.csv`    | Spot-level data (position, intensity, quality for each timepoint) | Intensity analysis                 |
| `*-edges.csv`    | Connectivity between spots (links between timepoints)             | Reconstructing tracks              |
| `*-tracks.csv`   | Summary statistics for each track (speed, displacement, etc.)     | Motility metrics, lineage analysis |
| `*all-spots.csv` | All spots including unlinked detections (optional)                | Debugging                          |
| `*.xml`          | TrackMate session file with full metadata (optional)              | Reproducibility                    |

**Timing**:

- Manual: ~5-10 minutes per location (first-time setup)
- Batch: ~1-2 minutes per location (after initial template creation)

**Critical Notes**:

- **File naming must be exact** for downstream pipeline steps
- Refer to auto-generated guide for location-specific names
- Can process in batches—pipeline detects completed locations automatically

---

### Step 4.5: Results Relocalization

**Purpose**: If using TrackMate Batcher, relocalize output files from centralized `OutputTracks/` folder back to individual location folders.

**Method**: Automated (Python)

**When to Use**:

- After TrackMate Batch Processing (Option 2 in Step 4)
- When results are in `Working_Directory/OutputTracks/`
- Skip if manual processing already saved to location folders

**Procedure**:

1. **In Pipeline GUI**: Click **"▶️ Run"** for Step 4.5
2. **Pipeline will**:

   - Scan `OutputTracks/` for CSV files
   - Parse filenames to determine location
   - Create `Tracking Result/` subfolder in each location
   - Move CSV files to corresponding location folders
3. **Verify**: `OutputTracks/` folder should be empty after successful relocation

**Expected Result**:

Files move from:

```
Working_Directory/OutputTracks/
├── Rep-1_0-24h_Dense_B1_2_Red_Seg-spots.csv
└── ...
```

To:

```
Input_Data_Folder/Rep1/0-24h/Dense/B1_2/Tracking Result/
├── Rep-1_0-24h_Dense_B1_2_Red_Seg-spots.csv
├── Rep-1_0-24h_Dense_B1_2_Red_Seg-edges.csv
└── Rep-1_0-24h_Dense_B1_2_Red_Seg-tracks.csv
```

**Timing**: <1 second per location

---

### Step 5: Subtrack Lineage Analysis

**Purpose**: Analyze cell division events, generate subtrack lineages with quality control, and compute motility metrics for each subtrack.

**Method**: Automated (Python)

**Algorithm**: Recursive depth-first search (DFS) to build subtrack trees from TrackMate edges, with QC filtering

**Quality Control Filters**:

- **Max Splits Allowed**: Removes tracks with excessive division events (default: 3)
  - Filters out potential tracking errors or over-segmentation
- **Min Track Duration**: Filters out short-lived tracks (default: 20 frames)
  - Ensures sufficient data for meaningful motility analysis

**Procedure**:

1. **In Pipeline GUI**: Click **"▶️ Run"** for Step 6
2. **Pipeline will**:

   - For each location:
     - Load tracking results
     - Identify split events from edges CSV
     - Build subtrack tree using DFS algorithm
     - Apply QC filters
     - Calculate per-subtrack statistics:
       - Mean speed
       - Linearity of forward progression
       - Mean directional change rate
       - Duration
       - Displacement
     - Generate three output files
3. **Outputs saved** to `Tracking Result/secondary_analysis/` subfolder

**Expected Output**:

```
Input_Data_Folder/Rep1/0-24h/Dense/B1_2/Tracking Result/
├── (primary tracking files)
└── secondary_analysis/
    ├── Rep-1_0-24h_Dense_B1_2_Red_Seg-subtrack_statistics.csv
    ├── Rep-1_0-24h_Dense_B1_2_Red_Seg-subtrack_edges.csv
    └── Rep-1_0-24h_Dense_B1_2_Red_Seg-subtrack_lineage.csv
```

**Output File Descriptions**:

1. **`*-subtrack_statistics.csv`**:

   - One row per subtrack
   - Columns: SUBTRACK_ID, PARENT_TRACK_ID, MEAN_SPEED, LINEARITY, DIRECTIONAL_CHANGE_RATE, DURATION, DISPLACEMENT, etc.
2. **`*-subtrack_edges.csv`**:

   - Parent-child relationships between subtracks
   - Columns: PARENT_SUBTRACK_ID, CHILD_SUBTRACK_ID, SPLIT_FRAME
3. **`*-subtrack_lineage.csv`**:

   - Complete lineage tree structure
   - Columns: SUBTRACK_ID, GENERATION, LINEAGE_ROOT_ID, PATH_FROM_ROOT

**Timing**: ~5-15 seconds per location (depends on track complexity)

**Note**: Pipeline automatically handles locations without division events (generates empty secondary_analysis folder or single-subtrack entries).

---

### Step 6: Fluorescence Intensity Analysis

**Purpose**: Extract Red/Green fluorescence intensities for each tracked cell over time to monitor nuclear envelope integrity.

**Method**: Automated (Python)

**Background**: Nuclear envelope rupture events are characterized by changes in Red/Green fluorescence intensity ratios when using appropriate fluorescent reporters.

**Procedure**:

1. **In Pipeline GUI**: Click **"▶️ Run"** for Step 5
2. **Pipeline will**:

   - For each location:
     - Load tracking results (`*-spots.csv`, `*-edges.csv`, `*-tracks.csv`)
     - Load fluorescence images:
       - `*_Red_Stabilized.tif`
       - `*_Green_Stabilized.tif`
     - Load segmentation mask (`*_Red_Seg.tif`)
     - For each tracked cell (Track ID):
       - Extract mean Red intensity at each timepoint
       - Extract mean Green intensity at each timepoint
       - Calculate Red/Green ratio
       - Normalize by median
     - Generate intensity timeseries CSV
3. **Output Saved** to `Tracking Result/` folder for each location

**Expected Output**:

```
Input_Data_Folder/Rep1/0-24h/Dense/B1_2/Tracking Result/
├── Rep-1_0-24h_Dense_B1_2_Red_Seg-spots.csv
├── Rep-1_0-24h_Dense_B1_2_Red_Seg-edges.csv
├── Rep-1_0-24h_Dense_B1_2_Red_Seg-tracks.csv
└── Rep-1_0-24h_Dense_B1_2_Red_Seg-intensity_timeseries.csv  ← NEW
```

**Output Format** (`*-intensity_timeseries.csv`):

| Column        | Description                             |
| ------------- | --------------------------------------- |
| TRACK_ID      | Unique track identifier from TrackMate  |
| FRAME_0_RED   | Red channel mean intensity at frame 0   |
| FRAME_0_GREEN | Green channel mean intensity at frame 0 |
| FRAME_0_RATIO | Red/Green ratio (normalized) at frame 0 |
| FRAME_1_RED   | Red channel mean intensity at frame 1   |
| ...           | (continues for all frames)              |

**Timing**: ~10-30 seconds per location (depends on track count and stack size)

---

---

## Output File Reference

### Complete Output Structure

After running all pipeline steps, your data structure will be:

```
Working_Directory/
├── pipeline_config.json                    # Saved configuration
├── image_stabilization_macro.ijm           # Auto-generated (Step 2)
├── TrackMate_Operation_Guide.txt           # Auto-generated (Step 4)
│
├── InputMask/                              # Flattened segmentation masks
│   ├── Rep-1_0-24h_Dense_B1_2_Red_Seg.tif
│   └── ...
│
└── OutputTracks/                            # (Empty after Step 4.5)

Input_Data_Folder/
└── Rep 1/
    └── 0-24h/
        └── Dense/
            └── B1_2/
                ├── B1_2_0001.tif (original)
                ├── B1_2_0002.tif (original)
                │
                ├── B1_2_Green/              # Step 1: Split channels
                │   ├── B1_2_Green_0001.tif
                │   └── ...
                ├── B1_2_Phase/
                │   └── ...
                ├── B1_2_Red/
                │   └── ...
                │
                ├── B1_2_Red_Stabilized.tif   # Step 2: Stabilized
                ├── B1_2_Green_Stabilized.tif
                ├── B1_2_Phase_Stabilized.tif
                │
                └── Tracking Result/          # Steps 4-6
                    ├── Rep-1_0-24h_Dense_B1_2_Red_Seg-spots.csv
                    ├── Rep-1_0-24h_Dense_B1_2_Red_Seg-edges.csv
                    ├── Rep-1_0-24h_Dense_B1_2_Red_Seg-tracks.csv
                    ├── Rep-1_0-24h_Dense_B1_2_Red_Seg-intensity_timeseries.csv
                    └── secondary_analysis/
                        ├── Rep-1_0-24h_Dense_B1_2_Red_Seg-subtrack_statistics.csv
                        ├── Rep-1_0-24h_Dense_B1_2_Red_Seg-subtrack_edges.csv
                        └── Rep-1_0-24h_Dense_B1_2_Red_Seg-subtrack_lineage.csv
```

### Key Output Files for Downstream Analysis

| File                           | Primary Use                       | Key Metrics                                                                                     |
| ------------------------------ | --------------------------------- | ----------------------------------------------------------------------------------------------- |
| `*-tracks.csv`               | Overall track statistics          | TRACK_MEAN_SPEED, LINEARITY_OF_FORWARD_PROGRESSION, MEAN_DIRECTIONAL_CHANGE_RATE, NUMBER_SPLITS |
| `*-intensity_timeseries.csv` | Nuclear envelope rupture analysis | Red/Green intensity ratios over time per track                                                  |
| `*-subtrack_statistics.csv`  | Division-aware motility analysis  | Per-subtrack motility metrics with lineage information                                          |
| `*-subtrack_lineage.csv`     | Division tree reconstruction      | Parent-child relationships, generation depth                                                    |

---

## Troubleshooting & Optimization

### Common Issues and Solutions

| Issue                                                        | Possible Cause                                                                          | Solution                                                                                                                                                                                                                  |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **No objects detected in TrackMate**                   | Segmentation mask may be blank or improperly labeled                                    | Open `*_Red_Seg.tif` in Fiji and ensure objects have integer labels. Use label viewer or LUTs to verify. Re-run segmentation if necessary.                                                                              |
| **Tracking fails with "Dimension mismatch" error**     | TrackMate misinterpreted Z/T stack                                                      | When prompted, ensure time is assigned as**T**, not Z. Swap dimensions if necessary. Check Image → Properties in Fiji. Pipeline handles this automatically but issue can occur with manually added masks.          |
| **High rate of over-tracking / too many track splits** | - High noise in mask `<br>`- Short-lived ROIs `<br>`- Aggressive linking parameters | - Increase**Linking max distance** in TrackMate `<br>`- Disable splitting if mitosis isn't of interest `<br>`- Filter out short tracks (<5 frames)`<br>`- Refine segmentation model with better training data |
| **TrackMate fails to launch or crashes on batch**      | GUI bug or batcher session file incompatible                                            | Try running one instance manually to regenerate a fresh `.xml` session file. Avoid enabling `.xlsx` output if not needed (known compatibility issue).                                                                 |
| **StarDist memory error**                              | Large TIFF stack or too many objects in one frame                                       | - Reduce `patch_size` or `batch_size` in model configuration `<br>`- Crop input TIFF to smaller regions `<br>`- Use grayscale instead of RGB (pipeline default design)`<br>`- Enable GPU if available           |
| **Incorrect Red/Green intensity pairing**              | Mismatched TIFF sequences or inconsistent frame counts                                  | Verify all `*_Red_Stabilized.tif` and `*_Green_Stabilized.tif` have the same number of frames and order. Re-run stabilization if needed.                                                                              |
| **Stabilization not effective (residual jitter)**      | Image Stabilizer pyramid level too low, or bad reference frame                          | Set pyramid level to**3**. Use **no template update**. Try testing stabilization on single-location macro first. Consider manual verification of reference frame quality.                                     |
| **Final summary tables missing some locations**        | Tracking or segmentation was skipped for certain folders                                | Review raw folders for missing `*_Seg.tif` or `*-tracks.csv`. Re-run missing steps manually if needed. Check GUI log for errors.                                                                                      |
| **Red/Green ratio spikes or flatlines unexpectedly**   | - Mask shifts due to drift `<br>`- ROI does not cover nucleus fully                   | Visually inspect a few track masks overlaid on image stack. Consider refining segmentation model or using median filters for intensity extraction.                                                                        |
| **Batch script not producing all result files**        | Script encountered exception mid-run                                                    | Run batch scripts with console open. Add try-except logging in loop for error tracing. Test batcher with one instance first to debug.                                                                                     |
| **"Please load the files first!" message**             | Locations not scanned in GUI                                                            | Click**"🔍 Scan Data Folder"** button in Pipeline Tab before running any steps.                                                                                                                                           |
| **Verification always shows 0/0 passed**               | Locations list is empty                                                                 | Ensure you've clicked "Scan Data Folder" and verified location count is >0 before running manual steps.                                                                                                                   |

## References

### Software & Methods

- **StarDist**: Schmidt U, Weigert M, Broaddus C, Myers G. "Cell Detection with Star-Convex Polygons." In: *Medical Image Computing and Computer Assisted Intervention – MICCAI 2018*. Lecture Notes in Computer Science, vol 11071. Springer, 2018. doi:10.1007/978-3-030-00934-2_30
- **TrackMate**: Tinevez J-Y, Perry N, Schindelin J, et al. "TrackMate: An open and extensible platform for single-particle tracking." *Methods* 2017;115:80-90. doi:10.1016/j.ymeth.2016.09.016
- **ImageJ/Fiji**: Schindelin J, Arganda-Carreras I, Frise E, et al. "Fiji: an open-source platform for biological-image analysis." *Nature Methods* 2012;9(7):676-682. doi:10.1038/nmeth.2019
- **Image Stabilizer Plugin**: Li K. "The image stabilizer plugin for ImageJ." http://www.cs.cmu.edu/~kangli/code/Image_Stabilizer.html

### Resource Training

- **ZeroCostDL4Mic**: von Chamier L, Laine RF, Jukkala J, et al. "Democratising deep learning for microscopy with ZeroCostDL4Mic." *Nature Communications* 2021;12:2276. doi:10.1038/s41467-021-22518-0
  - Training notebook and handbook: https://github.com/HenriquesLab/ZeroCostDL4Mic/wiki

---

## Version History & Notes

**Version 2.0** (February 2026)

- Complete GUI implementation with real-time monitoring
- Auto-generated ImageJ macros and TrackMate guides
- Integrated verification dialogs
- Enhanced error handling and logging
- Unified configuration management

**Version 1.1** (May 2025)

- Initial protocol documentation
- Command-line interface
- Basic batch processing

---

## Support & Contact

For issues, questions, or contributions:

**Author**: Oriana Chen
**Lab**: Cornell Univeristy Lammerding Lab

---

**End of Protocol**
