"""
Preprocessor package for EIME framework.

This package provides preprocessing tools for converting PyNite FEM analysis
into vectorized design parameters. It sits between the analysis (PyNite) and
the core design library, preparing design stations with vectorized parameters.

Main Components
---------------
Beam : Geometric beam definition with supports and bracing
BeamMesh : Mesh generation for design stations
GeometryMapper : Maps geometric parameters to mesh stations
AnalysisMapper : Maps analysis results to mesh stations
LoadDurationMapper : Maps load duration parameters to mesh stations
ParameterAssembler : Assembles all mapped parameters for design
BeamDesignResults : Results wrapper with beam-aware methods

PyNite Integration Modules
---------------------------
analysis : Extract shear diagrams and segment data from PyNite models
    - extract_shear_diagram()
    - identify_shear_segments()
    - prepare_shear_segment_arrays()
    - compute_sum_g()
    
shear_viz : Visualize shear diagrams and segments
    - plot_shear_diagram_with_segments()
    - plot_cv_calculation_details()

Typical Workflow
----------------
1. Run PyNite analysis
2. Use analysis module to extract shear data
3. Define beam geometry (spans, supports, bracing)
4. Generate mesh at design stations
5. Extract/map parameters at each station
6. Assemble parameters for vectorized design
7. Pass to core design library for calculations
8. Post-process and visualize results
"""

from .geometry import Beam
from .mesh import BeamMesh
from .parameters import (
    GeometryMapper,
    AnalysisMapper,
    LoadDurationMapper,
    ParameterAssembler,
)
from .results import BeamDesignResults

# PyNite integration:
# - General PyNite extraction: from preprocessor.pynite_extraction import extract_shear_diagram
# - CSA O86 shear segments: from design.csa_o86_2025.shear_segments import prepare_shear_segment_arrays
# - Orchestration: from preprocessor.pynite_csa_mapper import map_pynite_to_stations

__all__ = [
    "Beam",
    "BeamMesh",
    "GeometryMapper",
    "AnalysisMapper",
    "LoadDurationMapper",
    "ParameterAssembler",
    "BeamDesignResults",
    # PyNite modules available as submodules
    "shear_viz",
]
