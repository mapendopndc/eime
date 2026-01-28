"""
CSA O86-2025 Timber Design Formulas

This module contains all engineering formulas for timber design per CSA O86-2025.
"""

from .glulam_bending import (
    long_duration_factor,
    modified_bending_strength,
    bending_size_factor,
    slenderness_ratio,
    slenderness_ratio_limit,
    lateral_stability_factor_a,
    lateral_stability_factor_b,
    lateral_stability_factor,
    moment_resistance_a,
    moment_resistance_b1,
    moment_resistance_b2,
    moment_resistance_b,
    moment_resistance,
)

from .glulam_shear import (
    g_factor,
    shear_load_coefficient,
    modified_shear_strength,
    total_shear_resistance,
    shear_resistance,
)

from .glulam_compression import (
    modified_compression_strength,
    compression_size_factor,
    compression_slenderness_ratio,
    compression_slenderness_ratio_strong_axis,
    compression_slenderness_ratio_weak_axis,
    compression_slenderness_ratio_max,
    slenderness_factor,
    compression_resistance,
)

from .section_properties import (
    moment_of_inertia,
    section_modulus,
    stiffness_modulus_of_elasticity,
)

from .applied_loads import (
    applied_moment,
    applied_shear,
    applied_compression,
)

__all__ = [
    # Bending
    "long_duration_factor",
    "modified_bending_strength",
    "bending_size_factor",
    "slenderness_ratio",
    "slenderness_ratio_limit",
    "lateral_stability_factor_a",
    "lateral_stability_factor_b",
    "lateral_stability_factor",
    "moment_resistance_a",
    "moment_resistance_b1",
    "moment_resistance_b2",
    "moment_resistance_b",
    "moment_resistance",
    # Shear
    "g_factor",
    "shear_load_coefficient",
    "modified_shear_strength",
    "total_shear_resistance",
    "shear_resistance",
    # Compression
    "modified_compression_strength",
    "compression_size_factor",
    "compression_slenderness_ratio",
    "compression_slenderness_ratio_strong_axis",
    "compression_slenderness_ratio_weak_axis",
    "compression_slenderness_ratio_max",
    "slenderness_factor",
    "compression_resistance",
    # Section Properties
    "moment_of_inertia",
    "section_modulus",
    "stiffness_modulus_of_elasticity",
    # Applied Loads
    "applied_moment",
    "applied_shear",
    "applied_compression",
]
