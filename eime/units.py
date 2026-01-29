"""
Unit handling utilities for EIME framework.

This module provides utilities for working with Pint quantities, including
validation, conversion, and extraction of values for calculations.
"""

from typing import Any, Union
import numpy as np
import pandas as pd

try:
    from pint import Quantity, DimensionalityError, UnitRegistry
    # Create a shared unit registry for the entire EIME package
    ureg = UnitRegistry()
except ImportError:
    raise ImportError(
        "Pint is required for unit handling. Install with: pip install pint>=0.23"
    )


class UnitError(Exception):
    """Raised when unit validation or conversion fails."""
    pass


def is_quantity(value: Any) -> bool:
    """
    Check if a value is a Pint Quantity.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is a Pint Quantity
    """
    return isinstance(value, Quantity)


def validate_quantity(value: Any, param_name: str, expected_unit: str) -> None:
    """
    Validate that a value is a Pint Quantity with the expected dimensionality.
    
    Args:
        value: Value to validate
        param_name: Name of the parameter (for error messages)
        expected_unit: Expected unit string (e.g., 'mm', 'MPa', 'dimensionless')
        
    Raises:
        UnitError: If value is not a Quantity or has wrong dimensionality
    """
    if not is_quantity(value):
        raise UnitError(
            f"Parameter '{param_name}' must be a Pint Quantity with units. "
            f"Expected unit: {expected_unit}. "
            f"Received: {type(value).__name__}. "
            f"Example: {param_name} = 45 * ureg.{expected_unit}"
        )
    
    # Check dimensionality compatibility
    if expected_unit == 'dimensionless':
        if not value.dimensionless:
            raise UnitError(
                f"Parameter '{param_name}' must be dimensionless. "
                f"Received: {value.units}"
            )
    else:
        try:
            # Try to convert to expected unit to validate dimensionality
            _ = value.to(expected_unit)
        except DimensionalityError as e:
            raise UnitError(
                f"Parameter '{param_name}' has incompatible units. "
                f"Expected: {expected_unit} "
                f"Received: {value.units} "
                f"Error: {str(e)}"
            )


def extract_magnitude(value: Any, target_unit: str = None) -> Union[float, np.ndarray, pd.Series]:
    """
    Extract the numerical magnitude from a Pint Quantity.
    
    Optionally converts to a target unit before extraction.
    
    Args:
        value: Pint Quantity to extract from
        target_unit: Optional unit to convert to before extraction
        
    Returns:
        Numerical value (float, array, or Series)
        
    Raises:
        UnitError: If conversion to target unit fails
    """
    if not is_quantity(value):
        raise UnitError(
            f"Cannot extract magnitude from non-Quantity type: {type(value).__name__}"
        )
    
    if target_unit is not None:
        try:
            value = value.to(target_unit)
        except DimensionalityError as e:
            raise UnitError(
                f"Cannot convert {value.units} to {target_unit}: {str(e)}"
            )
    
    return value.magnitude


def get_unit_string(value: Any) -> str:
    """
    Get the unit string from a Pint Quantity.
    
    Args:
        value: Pint Quantity
        
    Returns:
        Unit string (e.g., 'millimeter', 'megapascal')
    """
    if not is_quantity(value):
        return ""
    
    return str(value.units)


def get_compact_unit_string(value: Any) -> str:
    """
    Get a compact unit string from a Pint Quantity formatted for LaTeX.
    
    Converts exponents from ** notation to LaTeX superscript (^{}).
    Example: 'mm ** 3' becomes 'mm^{3}'
    
    Args:
        value: Pint Quantity
        
    Returns:
        Compact unit string formatted for LaTeX (e.g., 'mm^{3}', 'MPa')
    """
    if not is_quantity(value):
        return ""
    
    # Use :~P for pretty compact format (preserves defined units better)
    unit_str = f"{value.units:~P}"
    
    # Convert ** notation to LaTeX superscript with braces
    # Replace ' ** X' with '^{X}' for LaTeX
    import re
    unit_str = re.sub(r'\s*\*\*\s*(\d+)', r'^{\1}', unit_str)
    
    # Also handle multiplication sign - both * and ·
    unit_str = unit_str.replace(' * ', ' \\cdot ')
    unit_str = unit_str.replace('·', ' \\cdot ')
    
    return unit_str


def make_quantity(magnitude: Union[float, np.ndarray, pd.Series], unit_string: str) -> Quantity:
    """
    Create a Pint Quantity from a magnitude and unit string.
    
    Note: This requires the user to have access to a UnitRegistry.
    For EIME, users should import ureg from pint directly.
    
    Args:
        magnitude: Numerical value
        unit_string: Unit string (e.g., 'mm', 'MPa')
        
    Returns:
        Pint Quantity
    """
    # This is a helper function - in practice, users will use ureg directly
    from pint import UnitRegistry
    ureg = UnitRegistry()
    return magnitude * ureg(unit_string)
