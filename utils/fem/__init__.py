"""
2D Finite Element Method solver for structural analysis.

Note: PyNite integration is available in the preprocessor package.
General extraction: from preprocessor.pynite_extraction import extract_shear_diagram
CSA O86 shear: from design.csa_o86_2025.shear_segments import prepare_shear_segment_arrays
"""

# This module previously contained pynite_shear.py
# It has been relocated and split:
# - General PyNite extraction: preprocessor/pynite_extraction.py
# - CSA O86 shear segments: design/csa_o86_2025/shear_segments.py
# - Orchestration: preprocessor/pynite_csa_mapper.py

__all__ = []
