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
    def format_value(value: Any, index: int = 0, precision: int = 2) -> str:
        """
        Format a value for LaTeX display.
        
        Handles Pint Quantities by extracting magnitude and unit.
        
        Args:
            value: Value to format (scalar, array, Series, Quantity, or formula)
            index: Index to extract if value is array-like
            precision: Number of decimal places
            
        Returns:
            Formatted LaTeX string with units if applicable
        """
        # Handle Pint Quantities
        if is_quantity(value):
            # Extract magnitude for the specific index
            magnitude = value.magnitude
            if isinstance(magnitude, pd.Series):
                num_val = float(magnitude.iloc[index])
            elif isinstance(magnitude, np.ndarray):
                num_val = float(magnitude[index])
            else:
                num_val = float(magnitude)
            
            # Get compact unit string
            unit_str = get_compact_unit_string(value)
            
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
                    return f"{num_val:.{precision}f} \\, {formatted_unit}"
                else:
                    return f"{num_val:.{precision}f} \\, \\text{{{unit_str}}}"
            else:
                return f"{num_val:.{precision}f}"
        
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
        
        # Format the number (no units for non-Quantity values)
        return f"{num_val:.{precision}f}"
    
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
        index: int = 0
    ) -> str:
        """
        Generate LaTeX summary of all checks.
        
        Args:
            checks: List of EngineeringCheck objects
            index: Index for array-like results
            
        Returns:
            LaTeX string summarizing check results
        """
        if not checks:
            return ""
        
        check_lines = []
        for check in checks:
            latex = check.generate_latex(index)
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
