# EIME Beam Analysis Debug Dashboard

A comprehensive Streamlit dashboard for visualizing and debugging beam analysis and design using the full EIME workflow with PyNite FEM analysis.

## Architecture

The dashboard has been refactored into modular components for maintainability and flexibility:

### Files

- **`app.py`** - Main Streamlit application with UI and workflow orchestration
- **`model_builder.py`** - Configurable beam model creation with flexible geometry, materials, and loading
- **`visualization.py`** - Visualization utilities for creating diagrams and plots from PyNite FEM models

## Features

- **Configuration-Driven Design:**
  - Interactive sidebar controls for geometry, sections, and loads
  - Automatic model adaptation to configuration changes
  - Support for multiple spans and custom load patterns

- **Complete EIME Workflow:**
  - PyNite FEM structural analysis
  - NBCC 2020 load combinations
  - Preprocessed station analysis with detailed shear properties
  - CSA O86:25 timber design calculations

- **Interactive Visualizations:**
  - Load, shear, and moment diagrams with resistance overlays
  - Shear segment annotations
  - Station-by-station analysis
  - Real-time design calculations

- **Detailed Station Information:**
  - **Analysis Tab:** Factored loads and demands
  - **Preprocessing Tab:** Geometry, load duration factors, and material parameters
  - **Design Tab:** Full resistance calculations with LaTeX formulas
  - **Results Tab:** Utilization ratios and pass/fail status

## Installation

Ensure all EIME dependencies are installed:

```bash
pip install streamlit plotly pint PyNite
```

## Usage

### Running the Dashboard

Run the Streamlit app from the `experiments/debug_dashboard` directory:

```bash
streamlit run app.py
```

Or from the root of the repository:

```bash
streamlit run experiments/debug_dashboard/app.py
```

### Configuration Interface

Use the **sidebar controls** to modify the model:

1. **📐 Geometry:**
   - Support locations (comma-separated, e.g., `0, 4, 8`)
   - Bracing locations (comma-separated, e.g., `0, 2, 4, 6, 8`)
   - Mesh spacing (0.05 to 1.0 m)

2. **📏 Section Properties:**
   - Width and depth (mm)
   - Material grade (20f-E, 24f-E, 16c-E)
   - Species (Douglas Fir-Larch, Spruce-Pine-Fir)

3. **📦 Applied Loads:**
   - Dead, live, and snow loads (kN/m)
   - Load application ranges (first span, second span, or entire beam)
   - Point loads with position and magnitude

4. Click **🔄 Rebuild Model** to apply changes

### Programmatic Configuration

You can also create custom configurations in code:

```python
from model_builder import ModelBuilder, ModelConfig, BeamConfig, SectionConfig, LoadConfig

# Three-span continuous beam
config = ModelConfig(
    beam=BeamConfig(
        support_locations=[0, 3, 6, 9],
        bracing_locations=[0, 1.5, 3, 4.5, 6, 7.5, 9],
        mesh_spacing=0.2
    ),
    section=SectionConfig(
        width_mm=175.0,
        depth_mm=500.0,
        grade="24f-E",
        species="Douglas Fir-Larch"
    ),
    loads=LoadConfig(
        dead_load=8.0,
        live_load=5.0,
        snow_load=6.0,
        load_ranges={
            'D': [(0, 9)],
            'S': [(0, 3)],
            'L': [(6, 9)]
        }
    )
)

builder = ModelBuilder(config, ureg)
beam_data = builder.build()
```

## Dashboard Layout

1. **Sidebar Configuration:**
   - Geometry settings
   - Section properties
   - Applied loads
   - Rebuild button

2. **Top Controls:**
   - Load Combination selector
   - Diagram Type selector (Loading/Shear/Moment)

3. **Main Diagram:**
   - Interactive Plotly visualization
   - Support and bracing markers
   - Resistance overlay (for shear/moment diagrams)
   - Shear segment annotations

4. **Station Selector:**
   - Slider to select analysis station
   - Real-time station coordinate display

5. **Tabbed Detail View:**
   - Analysis: Loads and demands
   - Preprocessing: Station parameters and load duration factors
   - Design: Full calculation procedures with LaTeX
   - Results: Resistance values and utilization ratios

## Extension Points

### Adding New Visualization Types

Edit `visualization.py`:

```python
def create_custom_diagram(x_data, y_data, ...):
    # Custom visualization logic
    pass
```

### Supporting New Load Patterns

Edit `model_builder.py`:

```python
class LoadConfig:
    # Add new load types
    wind_load: float = 0.0
```

### Adding Analysis Features

The modular architecture makes it easy to:
- Add new tabs with custom analyses
- Integrate additional design checks
- Export results to various formats
- Compare multiple design scenarios

## Performance

- Model creation is cached with `@st.cache_resource`
- Resistance calculations are batched for all stations at once
- Visualization data is computed efficiently with numpy arrays
- Configuration changes require explicit rebuild to prevent excessive recomputation

## Future Enhancements

- [ ] Export results to PDF/Excel
- [ ] Save/load configurations from JSON files
- [ ] Compare multiple design scenarios side-by-side
- [ ] Optimization mode (find minimum section size)
- [ ] Support for other code standards (IBC, Eurocode)
- [ ] Deflection analysis and serviceability checks
- [ ] Interactive diagram clicking to select stations

2. **Diagram Display:**
   - Interactive plot showing selected diagram
   - Support and bracing locations marked

3. **Station Selector:**
   - Slider to select station along beam
   - Shows position (x-coordinate)

4. **Information Tabs:**
   - **Analysis:** Factored loads, W_f, Sum_G
   - **Preprocessing:** Span lengths, unbraced lengths, load duration factors
   - **Design:** Resistance calculations with LaTeX formulas
   - **Results:** Utilization ratios and pass/fail status

## Example Beam

The default configuration is a simply supported beam with:
- **Span:** 8.0 m
- **Section:** 175 × 456 mm glulam
- **Material:** 20f-E Douglas Fir-Larch
- **Bracing:** Every 2.0 m
- **Loads:** 
  - Dead: 6.0 kN/m
  - Live: 4.0 kN/m
  - Snow: 5.0 kN/m

## Customization

To modify the beam configuration, edit the `create_beam_model()` function in `app.py`. You can change:
- Span lengths and support locations
- Bracing locations
- Section dimensions
- Material grade
- Load magnitudes
- Load combinations

## Technical Details

The dashboard demonstrates:
- Vectorized parameter mapping using preprocessor package
- Advanced shear segment analysis per CSA O86 7.5.7.6
- Integration of PyNite FEM with timber design code checks
- Real-time calculation of W_f and Sum_G factors
- Load duration factor determination based on load combinations
