# EIME Beam Analysis Debug Dashboard

A comprehensive Streamlit-based debug dashboard for visualizing and analyzing timber beam designs using the full EIME workflow.

## Features

- **Complete EIME Workflow:**
  - PyNite FEM structural analysis
  - NBCC 2020 load combinations
  - Preprocessed station analysis with detailed shear properties
  - CSA O86:25 timber design calculations

- **Interactive Visualizations:**
  - Load, shear, and moment diagrams
  - Station-by-station analysis
  - Real-time design calculations

- **Detailed Station Information:**
  - **Analysis Tab:** Factored loads and demands
  - **Preprocessing Tab:** Geometry and material parameters
  - **Design Tab:** Full resistance calculations with LaTeX formulas
  - **Results Tab:** Utilization ratios and pass/fail status

## Installation

Ensure all EIME dependencies are installed:

```bash
pip install streamlit plotly pint PyNite
```

## Usage

Run the Streamlit app from the `experiments/debug_dashboard` directory:

```bash
streamlit run app.py
```

Or from the root of the repository:

```bash
streamlit run experiments/debug_dashboard/app.py
```

## Dashboard Layout

1. **Top Controls:**
   - Load Combination selector
   - Diagram Type selector (Loading/Shear/Moment)

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
