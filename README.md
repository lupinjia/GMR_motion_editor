# GMR Motion Editor

A PyQt6-based visualization editor for GMR robot motion data, supporting import, editing, and export of GMR format data.

**[English](README.md) | [中文](README_CN.md)**

<!-- Demo GIF - adjust width via the width attribute (e.g., width="600", width="80%") -->
<img src="./docs/gmr_motion_editor_demo.gif" width="800" alt="GMR Motion Editor Demo">

## Features

- **Import/Export**: Load and save `.pkl` format GMR motion data
- **Visualization**: Real-time robot motion rendering using MuJoCo
- **Editing**: Simple start/end time trimming with export functionality
- **Multi-Robot Support**: Supports all 17 robot models in the project

## Installation & Configuration

### 1. Placement (Recommended)

**Recommended**: Place the `motion_editor` folder in the root directory of the GMR project:

```
GMR/                          # GMR project root
├── general_motion_retargeting/
├── assets/
├── motion_editor/            # <-- Place here
│   ├── motion_editor.py
│   ├── src/
│   └── README.md
└── ...
```

**Advantages**:
- Automatic GMR path detection, no manual configuration needed
- Automatically finds robot models and data from the GMR project on startup

### 2. Placement in Other Locations (Optional)

If you want to place `motion_editor` elsewhere (e.g., in a separate working directory), you need to manually configure the GMR path:

**Steps**:

1. **Edit configuration file**: `motion_editor/src/gui/config.py`

2. **Set GMR path**:

```python
# Path to GMR project root directory
GMR_ROOT_PATH = "/path/to/your/GMR"  # <-- Modify to your GMR path
```

**Example**:

```python
# Linux/macOS
GMR_ROOT_PATH = "/home/username/Projects/GMR"

# Windows
GMR_ROOT_PATH = "C:/Users/username/Documents/GMR"
```

### 3. Install Dependencies

Ensure PyQt6 is installed:

```bash
pip install PyQt6
```

Other dependencies (mujoco, numpy, etc.) need to be pre-installed in the GMR project.

### 4. Verify Configuration

Configuration is automatically verified on startup:
- ✅ If configured correctly, displays "Valid GMR installation"
- ❌ If configuration is incorrect, console shows error message and solution

**Verification Requirements**:
- Path must point to GMR project root directory
- Must contain `general_motion_retargeting/` and `assets/` directories

## Usage

### Launch Editor

```bash
# Navigate to motion_editor directory
cd motion_editor

# Launch editor
python motion_editor.py

# Or launch with file path (auto-opens specified file)
python motion_editor.py /path/to/motion_data.pkl
```

### Interface Guide

1. **Robot Selection**: Select corresponding robot type from dropdown menu
2. **Playback Controls**:
   - ▶ Play / ⏸ Pause: Play/pause
   - ⏹ Stop: Stop and reset to starting position
   - ⏮ / ⏭: Previous/next frame
   - ⏮⏮ / ⏭⏭: Jump to trim range start/end
3. **Timeline**:
   - Blue handle: Trim start point
   - Red handle: Trim end point
   - Yellow vertical line: Current frame position
4. **Export**: Click "📤 Export Clip" to export trimmed segment

### Keyboard Shortcuts

- `Space`: Play/pause
- `← / →`: Previous/next frame
- `Home`: Jump to trim range start
- `End`: Jump to trim range end
- `Ctrl+O`: Open file
- `Ctrl+S`: Save file
- `Ctrl+Shift+S`: Save as

## Example Workflow

1. Run `python motion_editor.py`
2. File → Open, select a `.pkl` motion data file
3. Select corresponding robot type from the robot dropdown
4. Click play button to view motion
5. Drag blue and red handles on timeline to set trim range
6. Click "Export Clip" to export trimmed segment

## Project Structure

```
motion_editor/
├── docs/                           # Documentation
│   ├── gmr_visualizer_design.md   # Design document
│   └── implementation_plan.md     # Implementation plan
├── src/                           # Source code
│   └── gui/                       # GUI module
│       ├── __init__.py
│       ├── config.py             # GMR path configuration ⭐
│       ├── gmr_manager.py        # Data management
│       ├── motion_controller.py  # Playback control
│       ├── timeline_widget.py    # Timeline widget
│       └── main_window.py        # Main window
├── tests/                         # Test files
│   ├── test_gmr_manager.py
│   ├── test_timeline_widget.py
│   └── test_motion_controller.py
├── motion_editor.py              # Launch script
└── README.md                     # This file
```

**Important Files**:
- `src/gui/config.py` - **GMR path configuration file**, edit this to set GMR project path

## Supported Robots

Supports all 17 robot models in the GMR project:

- Unitree G1 (29 DOF)
- Unitree G1 with Hands (43 DOF)
- Unitree H1 (19 DOF)
- Unitree H1 2 (27 DOF)
- Booster T1
- Booster T1 29dof
- Booster K1 (22 DOF)
- Stanford ToddlerBot
- Fourier N1
- ENGINEAI PM01
- HighTorque Hi (25 DOF)
- Galaxea R1 Pro (24 DOF)
- Kuavo S45 (28 DOF)
- Berkeley Humanoid Lite (22 DOF)
- PND Adam Lite (25 DOF)
- Tienkung (20 DOF)
- PAL Robotics' Talos (30 DOF)
- Fourier GR3 (31 DOF)

## Development

### Run Tests

```bash
cd motion_editor
python tests/test_gmr_manager.py
python tests/test_timeline_widget.py
python tests/test_motion_controller.py
```

### Tech Stack

- Python 3.10+
- PyQt6 (GUI framework)
- MuJoCo (3D rendering)
- NumPy (Data processing)

## License

This project is based on the GMR project and follows the MIT License.
