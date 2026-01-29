"""
Output formatting and LaTeX generation utilities.

This module provides tools for generating LaTeX representations of formulas,
parameters, and engineering calculations for documentation and display.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

# Import unit handling utilities
try:
    from .units import is_quantity, get_compact_unit_string, extract_magnitude
except ImportError:
    # Fallback if units module not available
    def is_quantity(value):
        return False
    def get_compact_unit_string(value):
        return ""
    def extract_magnitude(value, target_unit=None):
        return value


class Param:
    """
    Parameter definition for engineering formulas.
    
    A parameter represents an input to a formula with its LaTeX symbol,
    description, expected unit, and optional source reference.
    
    All parameters MUST specify a unit for dimensional validation.
    Use 'dimensionless' for unitless parameters.
    """
    
    def __init__(
        self,
        latex: str,
        unit: str,
        val: Optional[Any] = None,
        desc: str = "",
        src: str = ""
    ) -> None:
        """
        Initialize a parameter.
        
        Args:
            latex: LaTeX symbol for this parameter (e.g., "f_c", "E")
            unit: Expected unit string (e.g., 'mm', 'MPa', 'dimensionless')
            val: Value of the parameter (optional, must be a Pint Quantity)
            desc: Human-readable description
            src: Source reference (e.g., code clause, table reference)
        """
        self.latex = latex
        self.unit = unit
        self.val = val
        self.desc = desc
        self.src = src
    
    def __repr__(self) -> str:
        return f"Param({self.latex}, unit={self.unit}, val={self.val}, desc='{self.desc}')"


class LaTeXFormatter:
    """Utilities for formatting engineering calculations as LaTeX."""
    
    @staticmethod
    def _format_number_sigfigs(num_val: float, sig_figs: int) -> str:
        """
        Format a number with significant figures, removing trailing zeros.
        
        Uses scientific notation when digits exceed sig_figs.
        
        Args:
            num_val: The numeric value to format
            sig_figs: Number of significant figures
            
        Returns:
            Formatted string with proper significant figures
        """
        import re
        import math
        
        # Handle special cases
        if num_val == 0:
            return "0"
        if not np.isfinite(num_val):
            return str(num_val)
        
        # Calculate the number of digits before the decimal point
        abs_val = abs(num_val)
        if abs_val >= 1:
            num_digits = int(math.floor(math.log10(abs_val))) + 1
        else:
            num_digits = 0
        
        # Use scientific notation if the number of digits exceeds sig_figs
        # or if the number is very small (< 0.001)
        if num_digits > sig_figs or (abs_val < 0.001 and abs_val != 0):
            # Format in scientific notation
            formatted = f"{num_val:.{sig_figs - 1}e}"
            # Parse the exponential notation
            match = re.match(r'([+-]?\d+\.?\d*)[eE]([+-]?\d+)', formatted)
            if match:
                mantissa, exponent = match.groups()
                # Remove leading + from exponent and convert to int to remove leading zeros
                exponent = str(int(exponent))
                # Remove trailing zeros and decimal point from mantissa
                mantissa = mantissa.rstrip('0').rstrip('.')
                return f"{mantissa} \\times 10^{{{exponent}}}"
        else:
            # Use standard formatting with g specifier (removes trailing zeros)
            formatted = f"{num_val:.{sig_figs}g}"
            
            # Check if Python's g formatter switched to exponential when we don't want it
            if 'e' in formatted or 'E' in formatted:
                # Fall back to fixed precision
                if num_digits > 0:
                    decimal_places = max(0, sig_figs - num_digits)
                    formatted = f"{num_val:.{decimal_places}f}".rstrip('0').rstrip('.')
                else:
                    formatted = f"{num_val:.{sig_figs}g}"
            
            return formatted
    
    @staticmethod
    def format_value(value: Any, index: int = 0, precision: int = 3) -> str:
        """
        Format a value for LaTeX display with significant figures.
        
        Handles Pint Quantities by extracting magnitude and unit.
        Removes trailing zeros and uses scientific notation for large numbers.
        
        Args:
            value: Value to format (scalar, array, Series, Quantity, or formula)
            index: Index to extract if value is array-like
            precision: Number of significant figures (default 3)
            
        Returns:
            Formatted LaTeX string with units if applicable
        """
        # Handle Pint Quantities
        if is_quantity(value):
            # Convert to appropriate display units based on dimensionality
            # This ensures we show kN·m instead of N·mm, kN instead of N, etc.
            try:
                # Check dimensionality and convert to appropriate units
                dims = value.dimensionality
                
                # Force/Load: [mass] * [length] / [time]^2 -> convert to kN
                if dims == '[mass] * [length] / [time] ** 2':
                    value = value.to('kN')
                # Moment/Torque: [mass] * [length]^2 / [time]^2 -> convert to kN·m  
                elif dims == '[mass] * [length] ** 2 / [time] ** 2':
                    value = value.to('kN * m')
                # Stress/Pressure: [mass] / [length] / [time]^2 -> convert to MPa
                elif dims == '[mass] / [length] / [time] ** 2':
                    value = value.to('MPa')
                # Length: convert to m or mm based on magnitude
                elif dims == '[length]':
                    mag = abs(value.to('m').magnitude)
                    if mag < 0.01:  # Less than 10mm, use mm
                        value = value.to('mm')
                    else:
                        value = value.to('m')
                # Area: convert to mm^2
                elif dims == '[length] ** 2':
                    value = value.to('mm**2')
                # Moment of Inertia: convert to mm^4
                elif dims == '[length] ** 4':
                    value = value.to('mm**4')
                # Otherwise leave as-is (will use compact format)
            except:
                # If conversion fails, just use the value as-is
                pass
            
            # Extract magnitude for the specific index
            magnitude = value.magnitude
            if isinstance(magnitude, pd.Series):
                num_val = float(magnitude.iloc[index])
            elif isinstance(magnitude, np.ndarray):
                num_val = float(magnitude[index])
            else:
                num_val = float(magnitude)
            
            # Get compact unit string (preserves original units as stored)
            unit_str = get_compact_unit_string(value)
            
            # Format the number with significant figures
            num_str = LaTeXFormatter._format_number_sigfigs(num_val, precision)
            
            # Format with units
            if unit_str and unit_str != 'dimensionless':
                # Split unit string into parts before and after superscript to handle LaTeX properly
                import re
                # Check if there's a superscript or multiplication
                if '^' in unit_str or '\\cdot' in unit_str:
                    # Split by \cdot to handle each unit separately
                    parts = unit_str.split(' \\cdot ')
                    formatted_parts = []
                    for part in parts:
                        part = part.strip()
                        # Match unit name with optional superscript
                        match = re.match(r'^([a-zA-Z]+)(\^\{\d+\})?$', part)
                        if match:
                            unit_name, superscript = match.groups()
                            formatted_parts.append(f'\\text{{{unit_name}}}{superscript if superscript else ""}')
                        else:
                            # Keep as-is if no match (shouldn't happen normally)
                            formatted_parts.append(part)
                    formatted_unit = ' \\cdot '.join(formatted_parts)
                    return f"{num_str} \\, {formatted_unit}"
                else:
                    return f"{num_str} \\, \\text{{{unit_str}}}"
            else:
                return num_str
        
        # Extract single value from various types
        if isinstance(value, (float, int)):
            num_val = float(value)
        elif isinstance(value, pd.Series):
            num_val = float(value.iloc[index])
        elif isinstance(value, np.ndarray):
            num_val = float(value[index])
        elif isinstance(value, str):
            return value  # Already a string (possibly LaTeX)
        else:
            # Assume it's a formula object with a result attribute
            if hasattr(value, 'result'):
                return LaTeXFormatter.format_value(value.result, index, precision)
            else:
                num_val = float(value)
        
        # Format the number with significant figures
        return LaTeXFormatter._format_number_sigfigs(num_val, precision)
    
    @staticmethod
    def format_parameter_table(params: Dict[str, Param]) -> str:
        """
        Generate LaTeX for a parameter definition table.
        
        Args:
            params: Dictionary of parameter name to Param object
            
        Returns:
            LaTeX string defining all parameters
        """
        if not params:
            return ""
        
        latex_lines = ["\\text{where,} \\\\"]
        
        for param_name, param in params.items():
            source_tag = f"\\tag{{{param.src}}}" if param.src else ""
            latex_lines.append(
                f"{param.latex} &= \\text{{{param.desc}}} {source_tag} \\\\"
            )
        
        return "\n".join(latex_lines)
    
    @staticmethod
    def format_formula_equation(
        name: str,
        template: callable,
        inputs: Dict[str, Any],
        params: Dict[str, Param],
        result: Any,
        index: int = 0,
        precision: int = 2
    ) -> str:
        """
        Generate LaTeX for a formula equation showing symbols, substitution, and result.
        
        Args:
            name: Formula name (left-hand side)
            template: LaTeX template function that takes symbols as arguments
            inputs: Dictionary of input values
            params: Dictionary of parameters
            result: Calculated result
            index: Index for array-like inputs
            precision: Decimal places for numbers
            
        Returns:
            LaTeX equation showing formula, substitution, and result
        """
        # Get LaTeX symbols from parameters
        symbols = [params[key].latex for key in inputs.keys() if key in params]
        
        # Generate symbolic formula
        symbolic = template(*symbols)
        
        # Generate substituted formula (replace symbols with values)
        substitutions = []
        for key, value in inputs.items():
            if isinstance(value, str):
                substitutions.append(value)
            else:
                substitutions.append(LaTeXFormatter.format_value(value, index, precision))
        
        substituted = template(*substitutions)
        
        # Format result
        result_str = LaTeXFormatter.format_value(result, index, precision)
        
        # Build complete equation
        equation = (
            f"{name} &= {symbolic} \\\\ "
            f"&= {substituted} \\\\ "
            f"&= {result_str}"
        )
        
        return equation
    
    @staticmethod
    def wrap_align(content: str) -> str:
        """
        Wrap content in align* environment.
        
        Args:
            content: LaTeX content to wrap
            
        Returns:
            Content wrapped in \\begin{align*}...\\end{align*}
        """
        return f"\\begin{{align*}}\n{content}\n\\end{{align*}}"
    
    @staticmethod
    def format_check_summary(
        checks: List[Any],
        index: int = 0,
        precision: int = 3
    ) -> str:
        """
        Generate LaTeX summary of all checks.
        
        Args:
            checks: List of EngineeringCheck objects
            index: Index for array-like results
            precision: Number of significant figures for numeric output (default 3)
            
        Returns:
            LaTeX string summarizing check results
        """
        if not checks:
            return ""
        
        check_lines = []
        for check in checks:
            latex = check.generate_latex(index, precision)
            if latex:  # Skip empty checks
                check_lines.append(latex)
        
        return " \\\\ ".join(check_lines)


class DisplayText:
    """
    Text display element for engineering procedures.
    
    Used to add section headers and descriptive text in procedure documentation.
    """
    
    def __init__(self, text: str, level: int = 3) -> None:
        """
        Initialize display text.
        
        Args:
            text: Text content
            level: Heading level (1-6 for markdown)
        """
        self.text = text
        self.level = level
    
    def generate_latex(self, index: int = 0) -> str:
        """Generate LaTeX representation."""
        return f"\\text{{{self.text}}}"
    
    def generate_markdown(self, index: int = 0) -> str:
        """Generate Markdown representation."""
        prefix = "#" * self.level
        return f"{prefix} {self.text}"
    
    def __repr__(self) -> str:
        return f"DisplayText('{self.text}')"


class InputGroup:
    """
    Group of related input parameters for display.
    
    Provides convenient formatting of multiple parameters as a LaTeX table.
    """
    
    def __init__(self, **kwargs: Param) -> None:
        """
        Initialize input group.
        
        Args:
            **kwargs: Named parameters as Param objects
        """
        for key, value in kwargs.items():
            if not isinstance(value, Param):
                raise TypeError(f"All inputs must be Param objects, got {type(value)} for {key}")
            setattr(self, key, value)
    
    def print_params(self) -> str:
        """
        Generate LaTeX representation of all parameters.
        
        Returns:
            LaTeX string showing all parameters with values and sources
        """
        latex_lines = ["\\begin{align}"]
        
        # Get all parameter attributes
        attributes = [
            a for a in dir(self)
            if not a.startswith('_') and not callable(getattr(self, a))
        ]
        
        for attr in attributes:
            param = getattr(self, attr)
            if isinstance(param, Param):
                source_tag = f"\\tag{{{param.src}}}" if param.src else ""
                latex_lines.append(
                    f"\\text{{{param.desc}}}, \\ {param.latex} &= {param.val} {source_tag} \\\\"
                )
        
        latex_lines.append("\\end{align}")
        return "\n".join(latex_lines)
    
    def __repr__(self) -> str:
        params = [
            f"{attr}={getattr(self, attr).latex}"
            for attr in dir(self)
            if not attr.startswith('_') and isinstance(getattr(self, attr), Param)
        ]
        return f"InputGroup({', '.join(params)})"


def format_result_with_unit(value: Any, unit: str = "", index: int = 0, precision: int = 2) -> str:
    """
    Format a result with its unit for LaTeX display.
    
    Args:
        value: Result value
        unit: Unit string (LaTeX format)
        index: Index for array-like values
        precision: Decimal places
        
    Returns:
        Formatted LaTeX string with value and unit
    """
    formatted_value = LaTeXFormatter.format_value(value, index, precision)
    
    if unit:
        return f"{formatted_value} \\, \\text{{{unit}}}"
    else:
        return formatted_value
