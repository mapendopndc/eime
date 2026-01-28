"""
Check flagging system for engineering calculations.

This module provides a framework for defining and evaluating engineering design checks,
including upper/lower bounds, equality checks, and custom validation logic.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any, Optional, Union
import numpy as np
import pandas as pd

# Import unit handling
try:
    from .units import is_quantity, extract_magnitude, get_compact_unit_string
except ImportError:
    def is_quantity(value):
        return False
    def extract_magnitude(value, target_unit=None):
        return value
    def get_compact_unit_string(value):
        return ""


class STATUS(IntEnum):
    """Status codes for engineering checks."""
    PASS = 0
    WARNING = 1
    FAIL = 2
    ERROR = 3


# Human-readable status descriptions
STATUS_DESCRIPTIONS = {
    STATUS.PASS: "Pass",
    STATUS.WARNING: "Pass with warnings",
    STATUS.FAIL: "Fail",
    STATUS.ERROR: "Error",
}


class EngineeringCheck(ABC):
    """
    Base class for all engineering checks.
    
    An engineering check evaluates a formula result against design criteria
    and flags violations with appropriate status codes and messages.
    """
    
    def __init__(
        self,
        status_code: STATUS,
        check_id: int,
        message: str
    ) -> None:
        """
        Initialize an engineering check.
        
        Args:
            status_code: Status to apply if check fails (WARNING, FAIL, or ERROR)
            check_id: Unique identifier for this check
            message: Description of the check failure condition
        """
        self.check_id: int = check_id
        self.status_code: STATUS = status_code
        self.message: str = message
        
        # Results populated after check is run
        self.applied_check_ids: Optional[np.ndarray] = None
        self.applied_status_codes: Optional[np.ndarray] = None
        self.applied_messages: Optional[np.ndarray] = None
        self.util: Optional[np.ndarray] = None
        
        # Reference to the formula being checked
        self.formula: Optional[Any] = None
    
    def set_formula(self, formula: Any) -> EngineeringCheck:
        """
        Attach this check to a formula and run the check.
        
        Args:
            formula: The formula object to check
            
        Returns:
            Self for method chaining
        """
        self.formula = formula
        self.check()
        return self
    
    @abstractmethod
    def check(self) -> EngineeringCheck:
        """
        Evaluate the check against the formula result.
        
        Must populate:
        - applied_check_ids: Array of check IDs where check failed
        - applied_status_codes: Array of status codes
        - applied_messages: Array of failure messages
        - util: Utilization ratio (if applicable)
        
        Returns:
            Self for method chaining
        """
        pass
    
    @abstractmethod
    def generate_latex(self, index: int) -> str:
        """
        Generate LaTeX representation of the check for a specific index.
        
        Args:
            index: Index of the result to display
            
        Returns:
            LaTeX string representing the check
        """
        pass
    
    def _get_single_value(self, value: Any, index: int) -> float:
        """Extract a single value from various data types, including Pint Quantities."""
        # Handle Pint Quantities first
        if is_quantity(value):
            magnitude = value.magnitude
            if isinstance(magnitude, (float, int)):
                return float(magnitude)
            elif isinstance(magnitude, pd.Series):
                return float(magnitude.iloc[index])
            elif isinstance(magnitude, np.ndarray):
                return float(magnitude[index])
            else:
                return float(magnitude)
        
        # Handle standard types
        if isinstance(value, (float, int)):
            return float(value)
        elif isinstance(value, pd.Series):
            return float(value.iloc[index])
        elif isinstance(value, np.ndarray):
            return float(value[index])
        else:
            return float(value)


class Upperbound(EngineeringCheck):
    """
    Check that a formula result does not exceed an upper bound.
    
    Example:
        check = Upperbound(1.0, STATUS.FAIL, 101, "Utilization exceeds capacity")
    """
    
    def __init__(
        self,
        upperbound: Union[float, Any],
        status_code: STATUS,
        check_id: int,
        message: str,
        inclusive: bool = False
    ) -> None:
        """
        Initialize upper bound check.
        
        Args:
            upperbound: Maximum allowed value (or formula producing the bound)
            status_code: Status to apply if check fails
            check_id: Unique check identifier
            message: Failure message
            inclusive: If True, use <= instead of <
        """
        super().__init__(status_code, check_id, message)
        self.upperbound = upperbound
        self.inclusive = inclusive
    
    def check(self) -> EngineeringCheck:
        """Evaluate upper bound check.
        
        Philosophy: Work with Quantities directly and let Pint handle unit
        conversions. Only extract magnitudes at the end for numpy operations.
        """
        # Get result (keep as Quantity if it has units)
        result = self.formula.result
        
        # Get bound value (from formula or direct value)
        from .formula import EngineeringFunction
        if isinstance(self.upperbound, EngineeringFunction):
            bound = self.upperbound.result
        else:
            bound = self.upperbound
        
        # If result has units, ensure bound is converted to same units
        if is_quantity(result) and is_quantity(bound):
            # Pint will automatically handle unit conversion in comparisons
            bound = bound.to(result.units)
        
        # Extract magnitudes for numpy operations (after unit conversion)
        result_mag = extract_magnitude(result) if is_quantity(result) else np.array(result, dtype=float)
        bound_mag = extract_magnitude(bound) if is_quantity(bound) else np.array(bound, dtype=float)
        
        # Apply check
        if self.inclusive:
            failed = result_mag >= bound_mag
        else:
            failed = result_mag > bound_mag
        
        self.applied_check_ids = np.where(failed, self.check_id, None)
        self.applied_status_codes = np.where(failed, self.status_code, STATUS.PASS)
        self.applied_messages = np.where(failed, self.message, None)
        self.util = result_mag / bound_mag
        
        return self
    
    def generate_latex(self, index: int) -> str:
        """Generate LaTeX representation of upper bound check."""
        result_val = self._get_single_value(self.formula.result, index)
        
        # Get unit string from the formula result
        unit_str = get_compact_unit_string(self.formula.result)
        if unit_str:
            # Handle composite units with \cdot properly
            if '\\cdot' in unit_str:
                import re
                parts = unit_str.split(' \\cdot ')
                formatted_parts = []
                for part in parts:
                    part = part.strip()
                    match = re.match(r'^([a-zA-Z]+)(\^\{\d+\})?$', part)
                    if match:
                        unit_name, superscript = match.groups()
                        formatted_parts.append(f'\\text{{{unit_name}}}{superscript if superscript else ""}')
                    else:
                        formatted_parts.append(f'\\text{{{part}}}')
                unit_str = f" \\, {' \\cdot '.join(formatted_parts)}"
            else:
                unit_str = f" \\, \\text{{{unit_str}}}"
        
        # Get bound value
        from .formula import EngineeringFunction
        if isinstance(self.upperbound, EngineeringFunction):
            bound_val = self._get_single_value(self.upperbound.result, index)
            bound_str = self.upperbound.name
        else:
            bound_val = self._get_single_value(self.upperbound, index)
            bound_str = str(bound_val)
        
        # Determine pass/fail
        if self.inclusive:
            passed = result_val <= bound_val
            operator = "\\leq"
        else:
            passed = result_val < bound_val
            operator = "<"
        
        status_msg = STATUS_DESCRIPTIONS[STATUS.PASS] if passed else \
                     f"{STATUS_DESCRIPTIONS[self.status_code]}; {self.message}"
        
        check_text = (
            f"{self.formula.name} {operator} {bound_str}"
            f"&= {result_val:.2f}{unit_str} {operator} {bound_val:.2f}{unit_str} \\\\ "
            f"\\text{{Check}} &= \\text{{{status_msg}}}"
        )
        
        return check_text


class Lowerbound(EngineeringCheck):
    """
    Check that a formula result meets or exceeds a lower bound.
    
    Example:
        check = Lowerbound(0.5, STATUS.WARNING, 102, "Value below recommended minimum")
    """
    
    def __init__(
        self,
        lowerbound: Union[float, Any],
        status_code: STATUS,
        check_id: int,
        message: str,
        inclusive: bool = False
    ) -> None:
        """
        Initialize lower bound check.
        
        Args:
            lowerbound: Minimum allowed value (or formula producing the bound)
            status_code: Status to apply if check fails
            check_id: Unique check identifier
            message: Failure message
            inclusive: If True, use >= instead of >
        """
        super().__init__(status_code, check_id, message)
        self.lowerbound = lowerbound
        self.inclusive = inclusive
    
    def check(self) -> EngineeringCheck:
        """Evaluate lower bound check.
        
        Philosophy: Work with Quantities directly and let Pint handle unit
        conversions. Only extract magnitudes at the end for numpy operations.
        """
        # Get result (keep as Quantity if it has units)
        result = self.formula.result
        
        # Get bound value (from formula or direct value)
        from .formula import EngineeringFunction
        if isinstance(self.lowerbound, EngineeringFunction):
            bound = self.lowerbound.result
        else:
            bound = self.lowerbound
        
        # If result has units, ensure bound is converted to same units
        if is_quantity(result) and is_quantity(bound):
            # Pint will automatically handle unit conversion in comparisons
            bound = bound.to(result.units)
        
        # Extract magnitudes for numpy operations (after unit conversion)
        result_mag = extract_magnitude(result) if is_quantity(result) else np.array(result, dtype=float)
        bound_mag = extract_magnitude(bound) if is_quantity(bound) else np.array(bound, dtype=float)
        
        # Apply check
        if self.inclusive:
            failed = result_mag <= bound_mag
        else:
            failed = result_mag < bound_mag
        
        self.applied_check_ids = np.where(failed, self.check_id, None)
        self.applied_status_codes = np.where(failed, self.status_code, STATUS.PASS)
        self.applied_messages = np.where(failed, self.message, None)
        self.util = bound_mag / result_mag
        
        return self
    
    def generate_latex(self, index: int) -> str:
        """Generate LaTeX representation of lower bound check."""
        result_val = self._get_single_value(self.formula.result, index)
        
        # Get unit string from the formula result
        unit_str = get_compact_unit_string(self.formula.result)
        if unit_str:
            # Handle composite units with \cdot properly
            if '\\cdot' in unit_str:
                import re
                parts = unit_str.split(' \\cdot ')
                formatted_parts = []
                for part in parts:
                    part = part.strip()
                    match = re.match(r'^([a-zA-Z]+)(\^\{\d+\})?$', part)
                    if match:
                        unit_name, superscript = match.groups()
                        formatted_parts.append(f'\\text{{{unit_name}}}{superscript if superscript else ""}')
                    else:
                        formatted_parts.append(f'\\text{{{part}}}')
                unit_str = f" \\, {' \\cdot '.join(formatted_parts)}"
            else:
                unit_str = f" \\, \\text{{{unit_str}}}"
        
        # Get bound value
        from .formula import EngineeringFunction
        if isinstance(self.lowerbound, EngineeringFunction):
            bound_val = self._get_single_value(self.lowerbound.result, index)
            bound_str = self.lowerbound.name
        else:
            bound_val = self._get_single_value(self.lowerbound, index)
            bound_str = str(bound_val)
        
        # Determine pass/fail
        if self.inclusive:
            passed = result_val >= bound_val
            operator = "\\geq"
        else:
            passed = result_val > bound_val
            operator = ">"
        
        status_msg = STATUS_DESCRIPTIONS[STATUS.PASS] if passed else \
                     f"{STATUS_DESCRIPTIONS[self.status_code]}; {self.message}"
        
        check_text = (
            f"{self.formula.name} {operator} {bound_str}"
            f"&= {result_val:.2f}{unit_str} {operator} {bound_val:.2f}{unit_str} \\\\ "
            f"\\text{{Check}} &= \\text{{{status_msg}}}"
        )
        
        return check_text


class Equality(EngineeringCheck):
    """
    Check that a formula result equals an expected value within tolerance.
    
    Example:
        check = Equality(10.0, STATUS.FAIL, 103, "Value does not match expected", tolerance=0.01)
    """
    
    def __init__(
        self,
        expected_value: Union[float, Any],
        status_code: STATUS,
        check_id: int,
        message: str,
        tolerance: float = 0.001
    ) -> None:
        """
        Initialize equality check.
        
        Args:
            expected_value: Expected value (or formula producing it)
            status_code: Status to apply if check fails
            check_id: Unique check identifier
            message: Failure message
            tolerance: Relative tolerance for equality (default 0.001 = 0.1%)
        """
        super().__init__(status_code, check_id, message)
        self.expected_value = expected_value
        self.tolerance = tolerance
    
    def check(self) -> EngineeringCheck:
        """Evaluate equality check.
        
        Philosophy: Work with Quantities directly and let Pint handle unit
        conversions. Only extract magnitudes at the end for numpy operations.
        """
        # Get result (keep as Quantity if it has units)
        result = self.formula.result
        
        # Get expected value (from formula or direct value)
        from .formula import EngineeringFunction
        if isinstance(self.expected_value, EngineeringFunction):
            expected = self.expected_value.result
        else:
            expected = self.expected_value
        
        # If result has units, ensure expected is converted to same units
        if is_quantity(result) and is_quantity(expected):
            expected = expected.to(result.units)
        
        # Extract magnitudes for numpy operations (after unit conversion)
        result_mag = extract_magnitude(result) if is_quantity(result) else np.array(result, dtype=float)
        expected_mag = extract_magnitude(expected) if is_quantity(expected) else np.array(expected, dtype=float)
        
        # Check if within tolerance
        relative_diff = np.abs((result_mag - expected_mag) / expected_mag)
        failed = relative_diff > self.tolerance
        
        self.applied_check_ids = np.where(failed, self.check_id, None)
        self.applied_status_codes = np.where(failed, self.status_code, STATUS.PASS)
        self.applied_messages = np.where(failed, self.message, None)
        self.util = relative_diff
        
        return self
    
    def generate_latex(self, index: int) -> str:
        """Generate LaTeX representation of equality check."""
        result_val = self._get_single_value(self.formula.result, index)
        
        # Get unit string from the formula result
        unit_str = get_compact_unit_string(self.formula.result)
        if unit_str:
            # Handle composite units with \cdot properly
            if '\\cdot' in unit_str:
                import re
                parts = unit_str.split(' \\cdot ')
                formatted_parts = []
                for part in parts:
                    part = part.strip()
                    match = re.match(r'^([a-zA-Z]+)(\^\{\d+\})?$', part)
                    if match:
                        unit_name, superscript = match.groups()
                        formatted_parts.append(f'\\text{{{unit_name}}}{superscript if superscript else ""}')
                    else:
                        formatted_parts.append(f'\\text{{{part}}}')
                unit_str = f" \\, {' \\cdot '.join(formatted_parts)}"
            else:
                unit_str = f" \\, \\text{{{unit_str}}}"
        
        from .formula import EngineeringFunction
        if isinstance(self.expected_value, EngineeringFunction):
            expected_val = self._get_single_value(self.expected_value.result, index)
            expected_str = self.expected_value.name
        else:
            expected_val = self._get_single_value(self.expected_value, index)
            expected_str = str(expected_val)
        
        relative_diff = abs((result_val - expected_val) / expected_val)
        passed = relative_diff <= self.tolerance
        
        status_msg = STATUS_DESCRIPTIONS[STATUS.PASS] if passed else \
                     f"{STATUS_DESCRIPTIONS[self.status_code]}; {self.message}"
        
        check_text = (
            f"{self.formula.name} \\approx {expected_str}"
            f"&= {result_val:.2f}{unit_str} \\approx {expected_val:.2f}{unit_str} \\\\ "
            f"\\text{{Check}} &= \\text{{{status_msg}}}"
        )
        
        return check_text


class InvalidResult(EngineeringCheck):
    """
    Check for invalid results (NaN, Inf, etc.).
    
    This check is automatically applied to all formulas to catch calculation errors.
    """
    
    def __init__(
        self,
        status_code: STATUS = STATUS.ERROR,
        check_id: int = 0,
        message: str = "Invalid result (NaN or Inf)"
    ) -> None:
        """
        Initialize invalid result check.
        
        Args:
            status_code: Status to apply if check fails (default ERROR)
            check_id: Unique check identifier (default 0)
            message: Failure message
        """
        super().__init__(status_code, check_id, message)
    
    def check(self) -> EngineeringCheck:
        """Check for NaN or Inf values."""
        # Extract magnitude from result (Quantities are fine, just get the numbers)
        result = self.formula.result
        result_mag = extract_magnitude(result) if is_quantity(result) else np.array(result, dtype=float)
        
        invalid = np.isnan(result_mag) | np.isinf(result_mag)
        
        self.applied_check_ids = np.where(invalid, self.check_id, None)
        self.applied_status_codes = np.where(invalid, self.status_code, STATUS.PASS)
        self.applied_messages = np.where(invalid, self.message, None)
        
        return self
    
    def generate_latex(self, index: int) -> str:
        """Generate LaTeX representation of invalid result check."""
        if self.applied_status_codes is None:
            return ""
        
        # Handle scalar and array status codes
        try:
            # Try to index it
            status = self.applied_status_codes[index]
            msg = self.applied_messages[index] if self.applied_messages is not None else self.message
        except (IndexError, TypeError):
            # It's a scalar or 0-d array
            status = self.applied_status_codes
            msg = self.message
        
        if status == STATUS.PASS:
            return ""
        
        return f"\\text{{Error}} &= \\text{{{msg}}}"


# Convenience class for creating checks
class Check:
    """
    Factory class for creating engineering checks.
    
    Example:
        checks = [
            Check.upperbound(1.0, STATUS.FAIL, 101, "Exceeds capacity"),
            Check.lowerbound(0.5, STATUS.WARNING, 102, "Below minimum")
        ]
    """
    
    @staticmethod
    def upperbound(
        upperbound: Union[float, Any],
        status_code: STATUS,
        check_id: int,
        message: str,
        inclusive: bool = False
    ) -> Upperbound:
        """Create an upper bound check."""
        return Upperbound(upperbound, status_code, check_id, message, inclusive)
    
    @staticmethod
    def lowerbound(
        lowerbound: Union[float, Any],
        status_code: STATUS,
        check_id: int,
        message: str,
        inclusive: bool = False
    ) -> Lowerbound:
        """Create a lower bound check."""
        return Lowerbound(lowerbound, status_code, check_id, message, inclusive)
    
    @staticmethod
    def equality(
        expected_value: Union[float, Any],
        status_code: STATUS,
        check_id: int,
        message: str,
        tolerance: float = 0.001
    ) -> Equality:
        """Create an equality check."""
        return Equality(expected_value, status_code, check_id, message, tolerance)
    
    @staticmethod
    def invalid_result(
        status_code: STATUS = STATUS.ERROR,
        check_id: int = 0,
        message: str = "Invalid result (NaN or Inf)"
    ) -> InvalidResult:
        """Create an invalid result check."""
        return InvalidResult(status_code, check_id, message)
