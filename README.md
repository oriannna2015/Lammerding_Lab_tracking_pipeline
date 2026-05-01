# Lammerding Lab — Cell Tracking Support

**Computational Pipeline for Multi-Channel Cell Tracking Analysis**

**Version**: 2.1
**Last Update Date**: May 1st, 2026
**Author**: Oriana (Sihe) Chen
**Lab**: Cornell University Lammerding Lab

---

## Overview

This pipeline provides an integrated, GUI-driven workflow for processing multi-channel fluorescence microscopy time-lapse data. It spans the full analysis chain: channel splitting, image stabilization, deep-learning-based nuclear segmentation (StarDist), cell tracking (TrackMate), subtrack lineage decomposition, and Red/Green fluorescence intensity extraction for nuclear envelope rupture analysis.

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
7. [Troubleshooting](#troubleshooting)
8. [References](#references)

---

## System Requirements

**Software**

- Python 3.8 or higher (3.9 recommended)
- Fiji/ImageJ with the following plugins:
  - Image Stabilizer (Plugins → Registration → Image Stabilizer)
  - TrackMate (Plugins → Tracking → TrackMate; included with Fiji)
- Windows 10/11, macOS, or Linux

**Python Packages** — installed automatically via `Install_Dependencies.bat` (see [Installation](#installation)):

`numpy`, `pandas`, `scipy`, `scikit-image`, `tensorflow`, `stardist`, `csbdeep`, `tifffile`, `tqdm`, `openpyxl`

**Hardware**

| Component | Minimum              | Recommended                                     |
| --------- | -------------------- | ----------------------------------------------- |
| RAM       | 8 GB                 | 16 GB+                                          |
| Storage   | 2–3× raw data size | —                                              |
| GPU       | —                   | CUDA-compatible (accelerates StarDist ~5–10×) |
| CPU       | —                   | Multi-core (batch processing)                   |

---

## Installation

### Step 1: Set Up a Python Environment

Run **`Install_Dependencies.bat`** and follow the interactive prompts:

1. **Choose environment type**:

   - **conda** — recommended if you have Miniconda or Anaconda installed. Downloads from https://docs.conda.io/en/latest/miniconda.html
   - **venv** — uses Python's built-in virtual environment; requires Python 3.8+ already on your system (https://www.python.org/downloads/)
2. **Enter a name** for your environment (e.g. `celltrack`).
3. The script will automatically create the environment with Python 3.9 and install all required packages from `requirements.txt`.
4. On completion, the terminal will display the activation command for your environment — **note it down**:

   ```
   # conda:
   conda activate celltrack

   # venv:
   C:\path\to\celltrack_env\Scripts\activate
   ```

If any errors occur during setup, refer to the troubleshooting table at the end of this document or check package compatibility in `requirements.txt`.

> **Every time you open a new terminal to run CellTracker Pro, you must activate your environment first** before double-clicking `CellTracker_Pro.bat`

### Step 2: Verify Fiji Plugins

1. Download and install Fiji from https://fiji.sc if not already present.
2. Launch Fiji and confirm the following are accessible:
   - **Image Stabilizer**: Plugins → Registration → Image Stabilizer
   - **TrackMate**: Plugins → Tracking → TrackMate

### Step 3: Prepare StarDist Model

**Option A — Use the pre-trained model** included in the package (`StarDist_Cont_Grey_4_200_128_2_0.0003_Aug4_150epoch/`) or StarDist pacakes downloaded from other source. Note the folder path for use in configuration.

**Option B — Train a custom model** for your specific cell type using [ZeroCostDL4Mic](https://github.com/HenriquesLab/ZeroCostDL4Mic/wiki). Reference training parameters for nuclear segmentation:

Download the trained model folder and note its path.

---

## Input Data Structure

Raw microscopy data must follow this hierarchy:

```
Input_Data_Folder/
├── Rep 1/                       # Biological replicate
│   ├── 0-24h/                   # Timepoint
│   │   ├── Dense/               # Experimental condition
│   │   │   ├── B1_2/            # Location (field of view)
│   │   │   │   ├── B1_2_0001.tif
│   │   │   │   └── ...
│   │   │   └── B1_3/
│   │   ├── 5um/
│   │   └── 10um/
│   └── 24-48h/
├── Rep 3/
└── Rep 4/
```

**Requirements**

- Format: TIFF (`.tif`) multi-channel stacks
- Default channel order: Green, Phase, Red (configurable)
- Consistent location names within each condition folder
- Hierarchy: **Replicate → Timepoint → Condition → Location**

---

## Pipeline Configuration

### Launch the GUI

1. Activate your Python environment (created during Installation):
   ```
   # conda:
   conda activate <env_name>

   # venv:
   <env_folder>\Scripts\activate
   ```
2. Double-click **`CellTracker_Pro.bat`**. The launcher verifies your environment and opens the GUI in your browser automatically.

If the launcher reports missing packages, re-run `Install_Dependencies.bat` with your environment activated, or refer to the [Troubleshooting](#troubleshooting) section.

### Configure Settings

1. Open the **⚙️ Configuration** tab.
2. Fill in the required paths:
   - **Input Data Folder**: Root folder containing your replicates
   - **Working Directory**: Folder where intermediate and output files will be saved
   - **StarDist Model Path**: Path to your model folder
   - **Channel Names**: Adjust if different from the default (Green, Phase, Red)
3. Set QC parameters (defaults are suitable for most datasets):
   - **Max Splits Allowed**: 3 — removes tracks with excessive division events
   - **Min Track Duration**: 20 frames — removes short-lived tracks
4. Click **"Save Config"** then **"Apply Config"** to validate paths and create output directories.

### Scan Data

Switch to the **▶️ Pipeline** tab and click **"🔍 Scan Data Folder"**. Verify that the detected location count matches your dataset before proceeding.

> Logs from all operations are available in the **📋 Log** tab and can be saved for documentation.

---

## Data Processing Workflow

Steps are executed sequentially via the **▶️ Pipeline** tab. Click **"▶️ Run"** for each step in order. Steps 2 and 4 involve a manual Fiji stage followed by a GUI verification step.

---

### Step 1: Channel Splitting

**Purpose**: Separate multi-channel TIFF frames into individual per-channel subfolders.

**In the GUI**: Click **"▶️ Run"** for Step 1.

The pipeline scans all locations and splits each multi-channel TIFF into:

- `LocationName_Green/`
- `LocationName_Phase/`
- `LocationName_Red/`

Already-processed locations are skipped automatically.

**Expected output** (per location):

```
B1_2/
├── B1_2_Green/   ← individual frame TIFFs
├── B1_2_Phase/
└── B1_2_Red/
```

> **Note**: This step is optional if your data is already organized into separate channel folders.

---

### Step 2: Image Stabilization

**Purpose**: Correct stage drift across time-lapse frames using the Lucas-Kanade affine algorithm. All three channels are stabilized with an identical geometric correction, which is required for accurate cross-channel fluorescence extraction.

**Part A — Generate macro (GUI)**

Click **"▶️ Run"** for Step 2. The pipeline generates `image_stabilization_macro.ijm` in your Working Directory, pre-configured with your data paths.

**Part B — Execute in Fiji**

1. Open Fiji.
2. Navigate to **Plugins → Scripts → Script Interpreter**.
3. Set language to **ImageJ Macro**.
4. Open the generated `image_stabilization_macro.ijm` file and click **Run**.
5. Monitor progress in the Fiji console. Already-stabilized locations are skipped automatically.

**Part C — Verify (GUI)**

Return to the GUI and click **"✓ Verify Results"**. The pipeline checks all locations and reports completion status (X/X locations).

**Expected output** (per location):

```
B1_2/
├── B1_2_Red_Stabilized.tif
├── B1_2_Green_Stabilized.tif
└── B1_2_Phase_Stabilized.tif
```

---

### Step 3: Segmentation using StarDist

**Purpose**: Generate integer-labeled nuclear masks from stabilized images using a trained StarDist 2D model. Each nucleus receives a unique label per frame; output masks are 16-bit grayscale TIFF stacks compatible with TrackMate's Label Image Detector.

**In the GUI**: Click **"▶️ Run"** for Step 3.

Verify that the correct StarDist model path is set in the Configuration tab before running. GPU acceleration is used automatically if available.

**Expected output**:

```
Working_Directory/InputMask/
├── Rep-1_0-24h_Dense_B1_2_Red_Seg.tif
├── Rep-1_0-24h_Dense_B1_3_Red_Seg.tif
└── ...
```

> This is typically the most time-intensive step. Monitor progress in the GUI Log tab.

---

### Step 4: Tracking using TrackMate

**Purpose**: Reconstruct cell trajectories across time from segmentation masks.

Step 4 supports two workflows. Both require manual operation in Fiji; the GUI generates the necessary guide and verifies the results.

**In the GUI**: Click **"▶️ Run"** for Step 4 to generate `TrackMate_Operation_Guide.txt` in your Working Directory with location-specific file names and export paths.

---

#### Option A — Manual Tracking (per location)

For each location listed in the generated guide:

1. **Open Fiji** → File → Open → select `*_Red_Seg.tif` from `InputMask/`.
2. **Launch TrackMate**: Plugins → Tracking → TrackMate → click **Next**.
3. **Check dimensions**: If prompted, ensure time is assigned as **T** (not Z) → click **Next**.
4. **Configure Detector**:
   - Select **Label Image Detector**
   - Enable **Simplify Contours**
   - Click **Next** → **Detect** and verify spot overlay.
5. **Configure Tracker** (LAP Tracker):
   - Frame-to-frame linking max distance: 10–20 px
   - Gap closing: max distance 20 px, max frame gap 2
   - Track splitting: enable if observing mitosis (max distance 10 px)
   - Track merging: **Disable**
6. **Filter Tracks**: Add filter "Track duration > 5 frames" to remove spurious tracks.
7. **Export Results**: Actions → **Export tracks to CSV**
   - Save to `[location]/Tracking Result/` using the exact filenames from the generated guide:
     - `Rep-X_Time_Condition_Location_Red_Seg-spots.csv`
     - `Rep-X_Time_Condition_Location_Red_Seg-edges.csv`
     - `Rep-X_Time_Condition_Location_Red_Seg-tracks.csv`
   - Optionally save the TrackMate session (`.xml`) for reproducibility.

---

#### Option B — Batch Tracking (TrackMate Batcher)

1. **Open TrackMate Batcher**: Plugins → Tracking → TrackMate Batcher.
2. Set **Input folder** to `Working_Directory/InputMask/` and **Output folder** to `Working_Directory/OutputTracks/`.
3. Load the template session file (`.xml`) included in the package or saved from a manual run (Option A).
4. Select outputs: ✓ Spots CSV, ✓ Edges CSV, ✓ Tracks CSV. **Uncheck** "The 3 Tables (xlsx)" (known compatibility issue).
5. Click **Run**. After completion, proceed to **Step 4.5** to relocalize results.

---

**Verify (GUI)**: Click **"✓ Verify Results"** to confirm all locations have the required CSV files (X/X locations).

**Expected output** (per location):

```
B1_2/Tracking Result/
├── Rep-1_0-24h_Dense_B1_2_Red_Seg-spots.csv
├── Rep-1_0-24h_Dense_B1_2_Red_Seg-edges.csv
└── Rep-1_0-24h_Dense_B1_2_Red_Seg-tracks.csv
```

| File             | Content                                                  |
| ---------------- | -------------------------------------------------------- |
| `*-spots.csv`  | Per-spot position and intensity at each timepoint        |
| `*-edges.csv`  | Links between spots (connectivity across frames)         |
| `*-tracks.csv` | Summary statistics per track (speed, displacement, etc.) |

---

### Step 4.5: Results Relocalization (Optional)

**Purpose**: Move batch-processed results from the centralized `OutputTracks/` folder into individual location folders.

**When to use**: Only after Option B (Batch Tracking) in Step 4. Skip this step if you used Option A (Manual Tracking).

**In the GUI**: Click **"▶️ Run"** for Step 4.5. The pipeline parses filenames and moves each CSV to the corresponding `Tracking Result/` subfolder. `OutputTracks/` will be empty after successful relocation.

---

### Step 5: Fluorescence Intensity Analysis

**Purpose**: Extract mean Red and Green fluorescence intensities per tracked cell at each frame, and compute the Red/Green ratio ($I_R / (I_G + \varepsilon)$, $\varepsilon = 10^{-6}$) as a proxy for nuclear envelope rupture.

**In the GUI**: Click **"▶️ Run"** for Step 5.

The pipeline loads tracking results, stabilized fluorescence stacks, and segmentation masks, then generates a per-track intensity timeseries CSV.

**Expected output** (per location):

```
B1_2/Tracking Result/
└── Rep-1_0-24h_Dense_B1_2_Red_Seg-subtrack_fluorescence.csv
```

| Column            | Description                           |
| ----------------- | ------------------------------------- |
| `TRACK_ID`      | TrackMate track identifier            |
| `FRAME_N_RED`   | Mean Red intensity at frame N         |
| `FRAME_N_GREEN` | Mean Green intensity at frame N       |
| `FRAME_N_RATIO` | Normalized Red/Green ratio at frame N |

---

### Step 6: Subtrack Lineage Analysis

**Purpose**: Decompose each track at division points into subtracks, apply quality-control filters, and compute per-subtrack motility metrics. This produces division-aware statistics that avoid averaging pre- and post-division measurements.

**In the GUI**: Click **"▶️ Run"** for Step 6.

QC filters (configurable in the Configuration tab):

- **Max Splits Allowed** (default: 3) — removes tracks with excessive division events
- **Min Track Duration** (default: 20 frames) — removes short-lived tracks

**Expected output** (per location):

```
B1_2/Tracking Result/secondary_analysis/
├── Rep-1_0-24h_Dense_B1_2_Red_Seg-subtrack_statistics.csv
├── Rep-1_0-24h_Dense_B1_2_Red_Seg-subtrack_edges.csv
└── Rep-1_0-24h_Dense_B1_2_Red_Seg-subtrack_lineage.csv
```

| File                          | Content                                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------------------------ |
| `*-subtrack_statistics.csv` | Per-subtrack motility metrics: speed, linearity, directional change rate, displacement, duration |
| `*-subtrack_edges.csv`      | Parent–child relationships between subtracks at each division                                   |
| `*-subtrack_lineage.csv`    | Full lineage tree: generation, root ID, path from root                                           |

---

## Output File Reference

After completing all steps, the full output structure is:

```
Working_Directory/
├── pipeline_config.json
├── image_stabilization_macro.ijm       # Auto-generated (Step 2)
├── TrackMate_Operation_Guide.txt        # Auto-generated (Step 4)
├── InputMask/                           # Segmentation masks
│   └── Rep-1_0-24h_Dense_B1_2_Red_Seg.tif
└── OutputTracks/                        # Empty after Step 4.5

Input_Data_Folder/Rep 1/0-24h/Dense/B1_2/
├── B1_2_0001.tif                        # Original (unchanged)
├── B1_2_Green/                          # Step 1
├── B1_2_Phase/
├── B1_2_Red/
├── B1_2_Red_Stabilized.tif             # Step 2
├── B1_2_Green_Stabilized.tif
├── B1_2_Phase_Stabilized.tif
└── Tracking Result/                     # Steps 4–6
    ├── *-spots.csv
    ├── *-edges.csv
    ├── *-tracks.csv
    ├── *-subtrack_fluorescence.csv
    └── secondary_analysis/
        ├── *-subtrack_statistics.csv
        ├── *-subtrack_edges.csv
        └── *-subtrack_lineage.csv
```

**Key files for downstream analysis**:

| File                            | Primary Use                       | Key Metrics                                                 |
| ------------------------------- | --------------------------------- | ----------------------------------------------------------- |
| `*-tracks.csv`                | Overall track statistics          | Mean speed, linearity, directional change, number of splits |
| `*-subtrack_fluorescence.csv` | Nuclear envelope rupture analysis | Red/Green intensity ratio per subtrack over time            |
| `*-subtrack_statistics.csv`   | Division-aware motility           | Per-subtrack speed, linearity, displacement, duration       |
| `*-subtrack_lineage.csv`      | Division tree reconstruction      | Parent-child relationships, generation depth                |

---

## Troubleshooting

| Problem                              | Likely Cause                                          | Solution                                                                                                     |
| ------------------------------------ | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| No objects detected in TrackMate     | Blank or incorrectly labeled mask                     | Open `*_Red_Seg.tif` in Fiji and verify non-zero integer labels; re-run Step 3 if blank                    |
| "Dimension mismatch" in TrackMate    | Time assigned as Z instead of T                       | When prompted in TrackMate, swap Z/T to assign time as**T**                                            |
| Too many track splits                | High mask noise or aggressive linking                 | Increase linking max distance in TrackMate; filter tracks < 5 frames; consider retraining segmentation model |
| TrackMate Batcher fails or crashes   | Incompatible session file or `.xlsx` output enabled | Regenerate `.xml` from a fresh manual run; uncheck "The 3 Tables (xlsx)" output                            |
| StarDist memory error                | Large stack or high object density                    | Reduce input TIFF region; enable GPU if available                                                            |
| Residual jitter after stabilization  | Suboptimal stabilizer settings                        | Confirm pyramid level 3 and template update disabled in the macro                                            |
| Incorrect Red/Green pairing          | Mismatched frame counts between channels              | Verify stabilized TIFFs have matching frame counts; re-run Step 2 if needed                                  |
| Subtrack analysis yields 0 subtracks | Tracks too short or too many splits                   | Lower Min Track Duration or raise Max Splits in Configuration tab                                            |
| "Please load the files first!"       | Locations not scanned                                 | Click**"🔍 Scan Data Folder"** in the Pipeline tab before running any step                                   |
| Verification always shows 0/0        | Location list empty                                   | Confirm Scan Data Folder was run and detected > 0 locations                                                  |

---

## References

- **StarDist**: Schmidt U et al. "Cell Detection with Star-Convex Polygons." *MICCAI 2018*. doi:10.1007/978-3-030-00934-2_30
- **TrackMate**: Tinevez J-Y et al. "TrackMate: An open and extensible platform for single-particle tracking." *Methods* 2017;115:80–90. doi:10.1016/j.ymeth.2016.09.016
- **Fiji/ImageJ**: Schindelin J et al. "Fiji: an open-source platform for biological-image analysis." *Nature Methods* 2012;9(7):676–682. doi:10.1038/nmeth.2019
- **Image Stabilizer Plugin**: Li K. http://www.cs.cmu.edu/~kangli/code/Image_Stabilizer.html
- **ZeroCostDL4Mic**: von Chamier L et al. "Democratising deep learning for microscopy with ZeroCostDL4Mic." *Nat Commun* 2021;12:2276. doi:10.1038/s41467-021-22518-0

---

## Version History

**v2.1** (February 2026) - Fully Reconstructed GUI design.

**v2.0** (February 2026) — Full GUI implementation; auto-generated macros and guides; verification dialogs; unified configuration management.
**v1.1** (May 2025) — Initial release with command-line interface and basic batch processing.

---

**Author**: Oriana (Sihe) Chen · Cornell University Lammerding Lab
