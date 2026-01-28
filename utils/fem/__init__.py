"""
2D Finite Element Method solver for structural analysis.
"""

from .pynite_shear import (
    extract_shear_diagram,
    identify_shear_segments,
    prepare_shear_segment_arrays,
    compute_sum_g
)

__all__ = [
    'extract_shear_diagram',
    'identify_shear_segments',
    'prepare_shear_segment_arrays',
    'compute_sum_g'
]
