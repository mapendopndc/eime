"""
CSA O86-2025 Timber Design Calculators

High-level calculators for timber design using CSA O86-2025.
"""

from .timber_member import (
    RectangularProfile,
    TimberMaterial,
    TimberSection,
    TimberDesignParameters,
    TimberLoads,
    TimberBeamDesign
)
# Alias for backward compatibility
TimberMemberDesign = TimberBeamDesign

__all__ = [
    "RectangularProfile",
    "TimberMaterial",
    "TimberSection",
    "TimberDesignParameters",
    "TimberLoads",
    "TimberBeamDesign",
    "TimberMemberDesign",  # Backward compatibility alias
]
