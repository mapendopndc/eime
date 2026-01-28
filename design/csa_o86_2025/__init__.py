"""
CSA O86-2025 Timber Design Implementation

Engineering design of timber structures following the Canadian Standards Association
O86-2025 Engineering Design in Wood standard.
"""

__version__ = "0.1.0"

# Simple table access
from .tables import (
    SpecifiedStrengthTable,
    ServiceConditionFactorTable,
    EffectiveLengthFactorTable,
)

# Calculator components
from .calculators.timber_member import (
    TimberMaterial,
    RectangularProfile,
    TimberSection,
    TimberDesignParameters,
)

__all__ = [
    # Tables
    "SpecifiedStrengthTable",
    "ServiceConditionFactorTable", 
    "EffectiveLengthFactorTable",
    # Calculators
    "TimberMaterial",
    "RectangularProfile",
    "TimberSection",
    "TimberDesignParameters",
]

