# Preprocessor Architecture

This package implements preprocessing for the EIME framework, converting PyNite FEM analysis
into vectorized design parameters for continuous beams with varying parameters.

## Architecture Overview

The preprocessor package sits **between PyNite analysis and the core design library**,
preparing mesh-based inputs for vectorized design calculations.

```
PyNite Analysis (FEM Model)
    ↓
PyNite Shear Extraction (pynite_shear.py)
    ↓
Beam Geometry Definition (Beam)
    ↓
Mesh Generation (BeamMesh) → x_stations array
    ↓
    ├→ GeometryMapper → [span_lengths, lu_values, ...]
    ├→ AnalysisMapper → [M_f, V_f, W_f, Sum_G, ...]
    └→ LoadDurationMapper → [P_L_M, P_S_M, ...]
    ↓
ParameterAssembler → Unified parameter arrays
    ↓
Core Design Library (EIME) → Vectorized design
    ↓
BeamDesignResults → Spatial result queries
    ↓
Visualization → Utilization diagrams
```

```python
from preprocessor import Beam

# Three-span continuous beam
beam = Beam(
    support_locations=[0, 6, 12, 18],  # 3 spans
    bracing_locations=[0, 2, 4, 6, 8, 10, 12, 14, 16, 18]  # Bracing every 2m
)

# Query geometry
lu = beam.get_unbraced_length(5.5)  # Unbraced length at x=5.5m
span_length = beam.get_span_length_at(7.0)  # Span length at x=7.0m
```

### 2. BeamMesh (mesh.py)
Generates discretization points for design calculations.

```python
from preprocessor import BeamMesh

# Create mesh with automatic refinement at discontinuities
mesh = BeamMesh(
    beam,
    spacing=0.1,  # 100mm spacing
    refine_at_discontinuities=True  # Add stations at supports/bracing
)

print(mesh.num_stations)  # Number of design stations
print(mesh.x_stations)    # Array of x-coordinates
```

### 3. Parameter Mappers (parameters.py)

#### GeometryMapper
Maps geometric parameters to each station:
```python
from preprocessor import GeometryMapper

geom_mapper = GeometryMapper(beam, mesh)
geom_params = geom_mapper.map()
# Returns: span_lengths, lu_strong, lu_weak, support_proximity
```

#### AnalysisMapper
Maps structural analysis results to each station:
```python
from preprocessor import AnalysisMapper

# Demands can be arrays, functions, or from PyNite
demands = {
    'M_f': moment_array,
    'V_f': shear_array,
    'P_f': axial_array,
    'load_cases': {'D': {...}, 'L': {...}, 'S': {...}},
    'W_f': total_factored_load,
    'Sum_G': sum_g_array
}

analysis_mapper = AnalysisMapper(mesh, demands, ureg)
analysis_params = analysis_mapper.map()
```

#### LoadDurationMapper
Determines load duration ratios at each station:
```python
from preprocessor import LoadDurationMapper

duration_mapper = LoadDurationMapper(mesh, analysis_params)
duration_params = duration_mapper.map()
# Returns: P_L_M, P_S_M, P_L_V, P_S_V, P_L_P, P_S_P
```

### 4. ParameterAssembler (parameters.py)
Combines all mapped parameters:
```python
from preprocessor import ParameterAssembler

assembler = ParameterAssembler(
    beam, mesh,
    geom_params, analysis_params, duration_params,
    ureg=ureg
)

params = assembler.assemble()
# Ready for TimberBeamDesign
```

### 5. PyNite Integration (analysis.py)
Helper functions to extract demands from PyNite FEM:
```python
from preprocessor.analysis import map_pynite_to_stations

# Extract all demands from PyNite model with sophisticated shear analysis
demands = map_pynite_to_stations(
    model,
    member_name='M1',
    x_stations=mesh.x_stations,
    load_combo='ULS',
    load_cases=['D', 'L', 'S'],
    beam_length=8.0,
    ureg=ureg
)
```

#### Shear Segment Parameters (W_f and Sum_G)

The shear load coefficient (C_V) per CSA O86 7.5.7.6 requires **W_f** and **Sum_G** parameters:

**W_f (Total Factored Load)**
- Represents total factored load on beam
- For each station: uses total load on span or shear segment
- Calculated from PyNite: sum of support reactions or shear at supports
- Units: kN (or N if ureg specified)

**Sum_G (Sum of Shear Deformation Factors)**
- Represents cumulative shear flexibility per CSA O86 7.5.7.6
- Calculated from shear segments using sophisticated analysis
- Each segment has: l_a (distance to left support), l_b (distance to right support)
- G factor per segment: `G = (l_a^5 + l_b^5) / (l_a + l_b)`
- Sum_G = sum of all G factors for segments affecting shear

**How it works:**

1. **Shear Diagram Extraction**: PyNite analysis → shear force diagram
2. **Segment Identification**: Detect load discontinuities → divide into segments
3. **G Factor Calculation**: For each segment, calculate g-factor using V_A, V_B, V_C
4. **Sum_G Computation**: Sum all G factors across segments
5. **Station Mapping**: Each station gets properties of its containing segment

```python
# The sophisticated calculation happens automatically in map_pynite_to_stations:
from preprocessor.pynite_shear import prepare_shear_segment_arrays, compute_sum_g
from design.csa_o86_2025.formulas.glulam_shear import g_factor

# Prepare segment data
segment_data = prepare_shear_segment_arrays(
    model, 'M1', 'ULS', beam_length, ureg=ureg
)

# Calculate Sum_G
Sum_G = compute_sum_g(segment_data, g_factor)

# Results include:
# - segment_data['W_f']: Total factored load
# - segment_data['l_a']: List of segment lengths
# - segment_data['V_A'], V_B, V_C: Shear at segment start, end, center
# - Sum_G: Total of all G factors
```

**For simplified analysis** (without PyNite FEM):
```python
# Provide approximate values
demands = {
    'M_f': moment_array,
    'V_f': shear_array,
    'W_f': total_load_estimate,  # Simple: w * L
    'Sum_G': 1.0,  # Placeholder (conservative)
    'l_a': segment_lengths,
    'l_b': segment_lengths,
}
```

The architecture handles both:
- **Accurate**: PyNite FEM with sophisticated shear segment analysis
- **Simplified**: Manual input with conservative estimates

### 6. BeamDesignResults (results.py)
Spatial result queries and analysis:
```python
from preprocessor import BeamDesignResults

# Wrap TimberBeamDesign results
beam_results = BeamDesignResults(design.utilization, mesh)

# Find governing sections
governing = beam_results.find_governing_stations()
print(governing['bending'])  # (index, x_position, utilization)

# Query at specific location
util = beam_results.get_utilization_at(x=7.5, check_type='shear')

# Find critical sections
critical = beam_results.get_critical_sections(utilization_threshold=0.9)
```

### 7. Visualization (utils/visualization/beam_viz.py)
Plot utilization diagrams:
```python
from utils.visualization.beam_viz import plot_beam_utilization

plot_beam_utilization(
    x_stations=mesh.x_stations,
    utilizations={
        'bending': bending_util_array,
        'shear': shear_util_array,
        'compression': compression_util_array
    },
    support_locations=beam.support_locations,
    bracing_locations=beam.bracing_locations
)
```

## Key Design Principles

1. **Mesh-Centric**: Everything keys off `x_stations` array - single source of truth
2. **Separation of Concerns**: Each mapper handles one aspect (geometry, analysis, or loading)
3. **Implicit Segmentation**: Each mesh point is an independent design problem with its own parameters
4. **Full Vectorization**: All stations computed in parallel via numpy arrays
5. **Composability**: Easy to add new parameter types or design codes

## Integration with Existing EIME

The preprocessor package **does not replace** existing EIME design calculators. Instead:

- Preprocessor package **prepares inputs** (parameter arrays aligned with mesh)
- Existing `TimberBeamDesign` **performs calculations** (already vectorized)
- Preprocessor package **post-processes results** (spatial queries, visualization)

This maintains clean separation between preprocessing workflow and design code implementation.

## Example Workflow

See `examples/simple_continuous_beam.py` for complete example.

```python
from preprocessor import Beam, BeamMesh, GeometryMapper, AnalysisMapper, LoadDurationMapper, ParameterAssembler, BeamDesignResults
from design.csa_o86_2025.calculators.timber_member import TimberBeamDesign
from utils.visualization.beam_viz import plot_beam_utilization

# 1. Define beam
beam = Beam(support_locations=[0, 8], bracing_locations=[0, 4, 8])

# 2. Create mesh
mesh = BeamMesh(beam, spacing=0.2)

# 3. Map parameters
geom = GeometryMapper(beam, mesh).map()
analysis = AnalysisMapper(mesh, demands, ureg).map()
duration = LoadDurationMapper(mesh, analysis).map()

# 4. Assemble
params = ParameterAssembler(beam, mesh, geom, analysis, duration, ureg).assemble()

# 5. Design (use existing calculators)
design = TimberBeamDesign(section, loading, parameters, loading_params)
design.BendingResistance(axis='strong', sign='pos')

# 6. Analyze results
results = BeamDesignResults(design.utilization, mesh)
print(results.summary())

# 7. Visualize
plot_beam_utilization(mesh.x_stations, utilizations, beam.support_locations)
```

## Benefits

✅ Handles varying span lengths, bracing, loads, and load combinations  
✅ Maintains EIME philosophy: each station is independent design problem  
✅ Full vectorization: 10 stations or 1000 stations - same performance  
✅ Clear separation: workflow logic separate from CSA O86 calculations  
✅ Extensible: easy to add new parameters or design codes
