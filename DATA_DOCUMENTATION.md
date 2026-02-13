# TrackMate Data Analysis - Complete Documentation

**Dataset**: Test_Data_E7_8 (Rep 3, 0-24h, Dense condition)
**Date**: 2026-02-11
**TrackMate Version**: Fiji Plugin

---

## Part 1: Tracking Result Folder Structure

### File Inventory

```
Tracking Result/
├── Rep-3_0-24h_Dense_E7_8_Red_Seg-spots.csv          # All detected spots
├── Rep-3_0-24h_Dense_E7_8_Red_Seg-edges.csv          # Edges connecting spots 
├── Rep-3_0-24h_Dense_E7_8_Red_Seg-tracks.csv         # Track-level statistics
├── Rep-3_0-24h_Dense_E7_8_Red_Seg-all-spots.csv      # Complete spots export
├── Rep-3_0-24h_Dense_E7_8_Red_Seg-intensity_timeseries.csv  # Intensity time series
├── Rep-3_0-24h_Dense_E7_8_Red_Seg.xml                # TrackMate session configuration
├── Rep-3_0-24h_Dense_E7_8_Red_Seg_Tracks.xml         # Track data in XML format
├── Rep-3_0-24h_Dense_E7_8_Red_Seg-movie.avi          # Visualization movie
└── secondary_analysis/                                # Secondary analysis outputs
    ├── *-subtrack_statistics.csv                     # Subtrack statistics 
    ├── *-subtrack_edges.csv                          # Subtrack-grouped edges 
    ├── *-subtrack_lineage.csv                        # Subtrack lineage table 
```

---

### 1.1 Spots CSV

**File**: `*-spots.csv`
**Content**: All cell positions (spots) detected by TrackMate

**Column Descriptions**:

| Column                    | Type    | Description                                              |
| ------------------------- | ------- | -------------------------------------------------------- |
| `LABEL`                 | String  | Spot label (e.g., "ID920419")                            |
| `ID`                    | Integer | Spot unique identifier                                   |
| `TRACK_ID`              | Integer | Parent track ID (empty if unassigned)                    |
| `QUALITY`               | Float   | Detection quality score (higher = more reliable)         |
| `POSITION_X/Y/Z`        | Float   | Spatial coordinates (pixel units)                        |
| `POSITION_T`            | Float   | Time coordinate (seconds)                                |
| `FRAME`                 | Integer | Frame number                                             |
| `RADIUS`                | Float   | Estimated spot radius (pixels)                           |
| `VISIBILITY`            | Integer | Visibility flag (1 = visible)                            |
| `MEAN_INTENSITY_CH1`    | Float   | Channel 1 mean intensity                                 |
| `MEDIAN_INTENSITY_CH1`  | Float   | Channel 1 median intensity                               |
| `MIN/MAX_INTENSITY_CH1` | Float   | Channel 1 min/max intensity                              |
| `TOTAL_INTENSITY_CH1`   | Float   | Channel 1 total intensity (integrated)                   |
| `STD_INTENSITY_CH1`     | Float   | Channel 1 intensity standard deviation                   |
| `CONTRAST_CH1`          | Float   | Contrast = (Max-Min) / (Max+Min)                         |
| `SNR_CH1`               | Float   | Signal-to-noise ratio = Mean / Std                       |
| `ELLIPSE_X0/Y0`         | Float   | Fitted ellipse center coordinates                        |
| `ELLIPSE_MAJOR/MINOR`   | Float   | Ellipse major/minor axis                                 |
| `ELLIPSE_THETA`         | Float   | Ellipse rotation angle (radians)                         |
| `ELLIPSE_ASPECTRATIO`   | Float   | Major/minor axis ratio                                   |
| `AREA`                  | Float   | Spot area (pixels²)                                     |
| `PERIMETER`             | Float   | Perimeter (pixels)                                       |
| `CIRCULARITY`           | Float   | Circularity = 4π×Area/Perimeter² (1 = perfect circle) |
| `SOLIDITY`              | Float   | Solidity = Area/ConvexArea                               |
| `SHAPE_INDEX`           | Float   | Shape index                                              |

**Use Cases**:

- View cell positions and morphology at individual timepoints
- Intensity analysis (e.g., fluorescence intensity changes)
- Morphological analysis (circularity, area, etc.)

---

### 1.2 Edges CSV

**File**: `*-edges.csv`
**Content**: Edges connecting spots between adjacent timepoints, representing inter-frame cell motion

**Column Descriptions**:

| Column                      | Type    | Description                                           |
| --------------------------- | ------- | ----------------------------------------------------- |
| `LABEL`                   | String  | Edge label                                            |
| `TRACK_ID`                | Integer | Parent track ID                                       |
| `SPOT_SOURCE_ID`          | Integer | Source spot ID (Frame N)                              |
| `SPOT_TARGET_ID`          | Integer | Target spot ID (Frame N+1)                            |
| `LINK_COST`               | Float   | Link cost (calculated by TrackMate linking algorithm) |
| `DIRECTIONAL_CHANGE_RATE` | Float   | Directional change rate (radians/time unit)           |
| `SPEED`                   | Float   | Instantaneous speed (pixels/frame)                    |
| `DISPLACEMENT`            | Float   | Displacement distance (pixels)                        |
| `EDGE_TIME`               | Float   | Edge time (seconds)                                   |
| `EDGE_X/Y/Z_LOCATION`     | Float   | Edge midpoint coordinates                             |
| `MANUAL_EDGE_COLOR`       | Integer | Manual color annotation                               |

**Key Kinematic Metrics**:

- **SPEED**: Instantaneous speed = Displacement / Δt
- **DISPLACEMENT**: Euclidean distance between two spots
- **DIRECTIONAL_CHANGE_RATE**: Angular change relative to previous edge

**Use Cases**:

- Inter-frame motion analysis
- Speed trajectory visualization
- Motion direction change detection

---

### 1.3 Tracks CSV 

**File**: `*-tracks.csv`
**Content**: Track-level statistics (each track = complete trajectory of one cell)

**Track Split Logic**

- After a split event, child tracks inherit the same track ID with the
  parent track

**Average / Median / … Speed Calculation**

- **Calculation of track statistics is based on average of edges, and grouping**
  logic is all edges under <`<THE SAME TRACK ID>`>. So yes, data like
  average speed is the mean speed of parent cell before division + all childs
  after division.

**Detailed Column Descriptions**:

#### Basic Information

| Column             | Type    | Description                                            |
| ------------------ | ------- | ------------------------------------------------------ |
| `LABEL`          | String  | Track label (e.g., "Track_16")                         |
| `TRACK_INDEX`    | Integer | Track index number (0-based)                           |
| `TRACK_ID`       | Integer | Track unique identifier                                |
| `NUMBER_SPOTS`   | Integer | Number of spots in track                               |
| `NUMBER_GAPS`    | Integer | Number of gaps in track                                |
| `NUMBER_SPLITS`  | Integer | **Number of split events** (cell division count) |
| `NUMBER_MERGES`  | Integer | Number of merge events                                 |
| `NUMBER_COMPLEX` | Integer | Number of complex events (split+merge)                 |
| `LONGEST_GAP`    | Integer | Longest gap duration (frames)                          |

**Key Concepts**:

- **NUMBER_SPLITS**: When a cell divides into two, it produces 1 split event
- **Gap**: Track interruption (cell temporarily undetected)

---

#### Temporal Dimension

| Column             | Unit   | Description                       |
| ------------------ | ------ | --------------------------------- |
| `TRACK_DURATION` | Frames | Track duration (number of frames) |
| `TRACK_START`    | Frame  | Start frame number                |
| `TRACK_STOP`     | Frame  | Stop frame number                 |

**Formula**: `TRACK_DURATION = TRACK_STOP - TRACK_START + 1`

---

#### Spatial Dimension

| Column                      | Unit   | Description                                                           |
| --------------------------- | ------ | --------------------------------------------------------------------- |
| `TRACK_DISPLACEMENT`      | Pixels | **Net displacement** = straight-line distance from start to end |
| `TOTAL_DISTANCE_TRAVELED` | Pixels | **Total path length** = sum of all edge displacements           |
| `MAX_DISTANCE_TRAVELED`   | Pixels | Maximum distance from starting point                                  |
| `TRACK_X_LOCATION`        | Pixels | Track centroid X coordinate (mean of all spots)                       |
| `TRACK_Y_LOCATION`        | Pixels | Track centroid Y coordinate                                           |
| `TRACK_Z_LOCATION`        | Pixels | Track centroid Z coordinate                                           |

**Key Distinction**:

- **DISPLACEMENT**: "Straight-line distance" (displacement) = distance between trajectory endpoints
- **TOTAL_DISTANCE_TRAVELED**: "Actual path length" = cumulative distance traveled

---

#### Speed Statistics

| Column                 | Unit         | Description                                       |
| ---------------------- | ------------ | ------------------------------------------------- |
| `TRACK_MEAN_SPEED`   | Pixels/frame | **Mean speed** = average of all edge speeds |
| `TRACK_MAX_SPEED`    | Pixels/frame | Maximum instantaneous speed                       |
| `TRACK_MIN_SPEED`    | Pixels/frame | Minimum instantaneous speed                       |
| `TRACK_MEDIAN_SPEED` | Pixels/frame | Median speed                                      |
| `TRACK_STD_SPEED`    | Pixels/frame | Speed standard deviation (speed variability)      |

**Calculation Notes**:

- Based on SPEED column statistics from edges
- Reflects variations in cell motion speed

---

#### Motion Behavior Metrics

| Column                               | Range         | Description                                              |
| ------------------------------------ | ------------- | -------------------------------------------------------- |
| `CONFINEMENT_RATIO`                | 0-1           | **Confinement** = Displacement / Total_Distance    |
| `LINEARITY_OF_FORWARD_PROGRESSION` | 0-1           | **Directionality** = Displacement / Total_Distance |
| `MEAN_STRAIGHT_LINE_SPEED`         | Pixels/frame  | **Net velocity** = Displacement / Duration         |
| `MEAN_DIRECTIONAL_CHANGE_RATE`     | Radians/frame | **Directional change rate** (mean turning angle)   |

**Metric Interpretation**:

**1. CONFINEMENT_RATIO (Confinement)**

- **Formula**: `CR = Net displacement / Total path length`
- **Meaning**: Whether cell wanders within a confined area
- **Interpretation**:
  - **CR ≈ 1**: Linear motion (goal-directed)
  - **CR ≈ 0**: Random walk or confined to area
  - **Medium (0.3-0.7)**: Directed but with fluctuations

**2. LINEARITY_OF_FORWARD_PROGRESSION (Directionality)**

- **TrackMate Implementation**: Same as CONFINEMENT_RATIO
- **Meaning**: Straightness of motion trajectory

**3. MEAN_STRAIGHT_LINE_SPEED (Net Velocity)**

- **Formula**: `MSS = Net displacement / Total time`
- **Meaning**: "Effective velocity", represents **directional migration rate**
- **Differs from MEAN_SPEED**:
  - MEAN_SPEED: Average instantaneous speed (always positive)
  - MSS: Net velocity considering direction (can be very low)

**4. MEAN_DIRECTIONAL_CHANGE_RATE (Turning Rate)**

- **Unit**: Radians/frame
- **Meaning**: Average turning angle
- **Interpretation**:
  - **Low value**: Stable motion direction
  - **High value**: Frequent direction changes

---

#### Quality Metrics

| Column                 | Description                              |
| ---------------------- | ---------------------------------------- |
| `TRACK_MEAN_QUALITY` | Mean quality score of all spots in track |

---

### 1.4 Other Files

**XML Files**:

- `*-Seg.xml`: TrackMate session file (contains all parameter settings)
- `*-Seg_Tracks.xml`: Track data in XML format

**Video File**:

- `*-movie.avi`: Trajectory visualization video generated by TrackMate

**Intensity Time Series**:

- `*-intensity_timeseries.csv`: Intensity vs time data for each track

---

## Part 2: Secondary Analysis (Subtrack Analysis)

Execution Instruction:

` python "<pipeline_folder_path>/subtrack_lineage_analysis.py" --batch "<parent_folder_path>"`

### 2.1 Analysis Motivation

**Problem**: TrackMate's tracks.csv treats entire cell lineage as one track, cannot distinguish motion differences before/after division.

**Solution**: **Subtrack Analysis** = Split tracks at division points, so each subtrack represents a continuous trajectory segment without divisions.

**Core Logic**:

```
Original Track A (2 splits):
  Frame 0-40: Mother cell
  Frame 40: 1st division (1→2)
  Frame 40-70: Daughter cell B
  Frame 70: 2nd division (1→2)
  Frame 70-100: Granddaughter cells C and D

Subtrack Division (v2.0 algorithm):
  Subtrack_1: Frame 0-40   (Mother cell, includes split spot)
  Subtrack_2: Frame 41-70  (Daughter cell B, includes 2nd split spot)
  Subtrack_3: Frame 71-100 (Granddaughter cell C)
  Subtrack_4: Frame 71-100 (Granddaughter cell D)
  Subtrack_5: Frame 41-100 (Other daughter branch)
```

**Key Principle** (v2.0):

- **Split spot is included in the pre-split subtrack**
- Post-split branches start from next frame
- Uses recursive DFS algorithm to handle nested splits

---

### 2.2 QC Filtering Rules

**Global Parameters** (modifiable at script beginning):

```python
MAX_SPLITS_ALLOWED = 3              # Maximum split events
MIN_TRACK_DURATION_FRAMES = 20      # Minimum frames
```

**Filtering Criteria**:

- Exclude tracks with `NUMBER_SPLITS > 3` (possible tracking error)
- Exclude tracks with `TRACK_DURATION < 20` (too short, unreliable statistics)

Adjust those parameters to filter out tracks that are not informative or not reliable. Those tracks will not have subtrack statistics.

---

### 2.3 Secondary Analysis Output Files

#### File 1: `*-subtrack_statistics.csv` ⭐

**Content**: Complete kinematic statistics for each subtrack (similar to tracks.csv but for subtracks)

**Column Descriptions** (32 columns):

##### Identification Information

| Column             | Description                                        |
| ------------------ | -------------------------------------------------- |
| `SUBTRACK_ID`    | Subtrack unique identifier (e.g., "Track_7_Sub_3") |
| `TRACK_ID`       | Parent original track ID                           |
| `SUBTRACK_INDEX` | Index within original track (1, 2, 3...)           |
| `START_FRAME`    | Subtrack start frame                               |
| `END_FRAME`      | Subtrack end frame                                 |
| `NUMBER_SPOTS`   | Number of spots in subtrack                        |
| `NUMBER_EDGES`   | Number of edges in subtrack                        |

##### Temporal and Spatial Statistics

| Column                    | Description                   |
| ------------------------- | ----------------------------- |
| `SUBTRACK_DURATION`     | Duration (frames)             |
| `SUBTRACK_START`        | Start time (frame number)     |
| `SUBTRACK_STOP`         | Stop time (frame number)      |
| `SUBTRACK_DISPLACEMENT` | Net displacement (start→end) |
| `SUBTRACK_X/Y_LOCATION` | Subtrack centroid coordinates |
| `START_X/Y`             | Start point coordinates       |
| `END_X/Y`               | End point coordinates         |

##### Speed Statistics

| Column                    | Description                             |
| ------------------------- | --------------------------------------- |
| `SUBTRACK_MEAN_SPEED`   | Mean speed (average of all edge speeds) |
| `SUBTRACK_MAX_SPEED`    | Maximum instantaneous speed             |
| `SUBTRACK_MIN_SPEED`    | Minimum instantaneous speed             |
| `SUBTRACK_MEDIAN_SPEED` | Median speed                            |
| `SUBTRACK_STD_SPEED`    | Speed standard deviation                |

##### Motion Behavior Metrics

| Column                               | Description                                 |
| ------------------------------------ | ------------------------------------------- |
| `TOTAL_DISTANCE_TRAVELED`          | Total path length (cumulative displacement) |
| `MAX_DISTANCE_TRAVELED`            | Maximum distance from starting point        |
| `CONFINEMENT_RATIO`                | Confinement = Displacement / Total_Distance |
| `MEAN_STRAIGHT_LINE_SPEED`         | Net velocity = Displacement / Duration      |
| `LINEARITY_OF_FORWARD_PROGRESSION` | Directionality (same as CONFINEMENT_RATIO)  |
| `MEAN_DIRECTIONAL_CHANGE_RATE`     | Mean turning rate (radians)                 |
| `OUTREACH_RATIO`                   | Max distance / Total distance               |
| `TORTUOSITY`                       | Total distance / Net displacement           |

##### Quality and Intensity

| Column                          | Description                             |
| ------------------------------- | --------------------------------------- |
| `SUBTRACK_MEAN_QUALITY`       | Mean quality score                      |
| `SUBTRACK_MEAN_INTENSITY_CH1` | Mean fluorescence intensity (channel 1) |

**Use Cases**:

- Compare motion changes before/after division
- Analyze motion patterns of different subtracks
- Identify effects of division on speed and directionality

---

#### File 2: `*-subtrack_edges.csv`

**Content**: All edges regrouped by subtrack

**New Columns**:

- `SUBTRACK_ID`: Subtrack to which edge belongs
- `TRACK_ID`: Original track of edge
- `SUBTRACK_INDEX`: Subtrack index

**Use Cases**:

- Analyze inter-frame motion details for specific subtracks
- Plot speed trajectories at subtrack level
- Detect instantaneous speed changes before/after division

---

#### File 3: `*-subtrack_lineage.csv` ⭐

**Content**: Subtrack attribution information (simplified lineage table)

**Column Descriptions** (7 columns):

| Column             | Description                |
| ------------------ | -------------------------- |
| `SUBTRACK_ID`    | Subtrack identifier        |
| `TRACK_ID`       | Parent original track      |
| `SUBTRACK_INDEX` | Index (1 = first subtrack) |
| `START_FRAME`    | Start frame                |
| `END_FRAME`      | End frame                  |
| `DURATION`       | Duration                   |
| `NUMBER_SPOTS`   | Number of spots            |

**Use Cases**:

- **Quickly view track's split structure**
- Identify split timepoints
- Count split frequency

**Example Data** (Track 7 with 2 splits):

```csv
SUBTRACK_ID,     TRACK_ID, INDEX, START, END, DURATION, SPOTS
Track_7_Sub_1,   7,        1,     0,     10,  11,       11
Track_7_Sub_2,   7,        2,     11,    93,  83,       83
Track_7_Sub_3,   7,        3,     11,    14,  4,        4
Track_7_Sub_4,   7,        4,     15,    86,  72,       72
Track_7_Sub_5,   7,        5,     15,    16,  2,        2
```

**Interpretation**:

1. Sub_1 ends at Frame 10 → **1st split point**
2. Sub_2 and Sub_3 both start at Frame 11 → Two branches from 1st split
3. Sub_3 ends at Frame 14 → **2nd split point**
4. Sub_4 and Sub_5 start at Frame 15 → Two branches from 2nd split
5. Sub_2 continues to Frame 93 → Another branch without further splits
