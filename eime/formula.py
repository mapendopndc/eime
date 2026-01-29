"""
Formula framework for engineering calculations.

This module provides the core building blocks for defining engineering formulas
with automatic documentation, check flagging, and batch calculation support.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from functools import wraps, update_wrapper
from inspect import signature
from typing import Any, Callable, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from .checks import EngineeringCheck, InvalidResult, STATUS
from .output import Param, LaTeXFormatter
from .units import (
    is_quantity,
    validate_quantity,
    extract_magnitude,
    make_quantity,
    UnitError
)


class EngineeringFunction(ABC):
    """
    Base class for all engineering calculation functions.
    
    Provides common functionality for formulas and switches including:
    - Input management
    - Check execution
    - LaTeX generation
    - Result testing
    """
    
    def __init__(
        self,
        name: str,
        checks: Optional[List[EngineeringCheck]],
        desc: str
    ) -> None:
        """
        Initialize an engineering function.
        
        Args:
            name: LaTeX name/symbol for this function
            checks: List of checks to apply to results
            desc: Human-readable description
        """
        self.name = name
        self.desc = desc
        self.checks: List[EngineeringCheck] = checks if checks else []
        self.result: Optional[Any] = None
        self.inputs: Optional[Dict[str, Any]] = None
    
    def add_inputs(self, **kwargs) -> EngineeringFunction:
        """
        Add input values to the function.
        
        Args:
            **kwargs: Named input values
            
        Returns:
            Self for method chaining
        """
        self.inputs = kwargs
        return self
    
    def run_checks(self) -> EngineeringFunction:
        """
        Execute all checks on the result.
        
        Automatically adds an InvalidResult check to catch NaN/Inf values.
        
        Returns:
            Self for method chaining
        """
        # Add invalid result check automatically
        self.checks.append(InvalidResult(STATUS.ERROR, 0, "Invalid result (NaN or Inf)"))
        
        # Run all checks
        self.checks = [check.set_formula(self) for check in self.checks]
        
        return self
    
    @abstractmethod
    def solve(self) -> EngineeringFunction:
        """
        Execute the calculation logic.
        
        Must populate self.result.
        
        Returns:
            Self for method chaining
        """
        pass
    
    @abstractmethod
    def generate_function_latex(self, index: int, precision: int = 3) -> str:
        """
        Generate LaTeX for the function equation.
        
        Args:
            index: Index for array-like results
            precision: Number of significant figures for numeric output (default 3)
            
        Returns:
            LaTeX string
        """
        pass
    
    @abstractmethod
    def generate_param_latex(self) -> str:
        """
        Generate LaTeX for parameter definitions.
        
        Returns:
            LaTeX string
        """
        pass
    
    def generate_checks_latex(self, index: int, precision: int = 3) -> str:
        """
        Generate LaTeX for all checks.
        
        Args:
            index: Index for array-like results
            precision: Number of significant figures for numeric output (default 3)
            
        Returns:
            LaTeX string
        """
        if not self.checks:
            return ""
        
        return LaTeXFormatter.format_check_summary(self.checks, index, precision)
    
    def generate_latex(self, index: int = 0, precision: int = 3) -> str:
        """
        Generate complete LaTeX representation.
        
        Args:
            index: Index for array-like results
            precision: Number of significant figures for numeric output (default 3)
            
        Returns:
            Complete LaTeX string with formula, params, and checks wrapped in align*
        """
        content = self.generate_function_latex(index, precision) + " \\\\ "
        
        param_latex = self.generate_param_latex()
        if param_latex:
            content += param_latex
            # Remove trailing space and add line break only if we have more content
        
        checks_latex = self.generate_checks_latex(index, precision)
        if checks_latex:
            if param_latex:
                content += " \\\\ "
            content += checks_latex
        else:
            # Remove trailing \\ if no checks
            content = content.rstrip(" \\\\ ")
        
        return LaTeXFormatter.wrap_align(content)
    
    def test(self, expected_value: float, tolerance: float = 0.001) -> bool:
        """
        Test if result matches expected value.
        
        Args:
            expected_value: Expected result
            tolerance: Relative tolerance (default 0.1%)
            
        Returns:
            True if test passes
        """
        if self.result is None:
            print("Test Failed: No result computed")
            return False
        
        # Get scalar result for testing
        result_val = self.result
        if isinstance(result_val, (pd.Series, np.ndarray)):
            result_val = float(result_val.iloc[0] if isinstance(result_val, pd.Series) else result_val[0])
        
        passed = abs(expected_value - result_val) < (abs(expected_value) * tolerance)
        
        if passed:
            print(f"Test Passed: {result_val:.6f} ≈ {expected_value:.6f}")
        else:
            print(f"Test Failed: {result_val:.6f} ≠ {expected_value:.6f}")
        
        return passed


class EngineeringFormula(EngineeringFunction):
    """
    A standard engineering formula with explicit calculation logic.
    
    Example:
        def calc_stress(F, A):
            return F / A
        
        stress = EngineeringFormula(
            name="\\sigma",
            params={"F": Param("F", desc="Force"), "A": Param("A", desc="Area")},
            logic=calc_stress,
            latex_template=lambda F, A: f"{F} / {A}",
            source="Example 1.1",
            checks=[Check.upperbound(350, STATUS.FAIL, 101, "Exceeds allowable")],
            desc="Axial stress calculation"
        )
    """
    
    def __init__(
        self,
        name: str,
        params: Dict[str, Param],
        logic: Callable,
        latex_template: Callable,
        source: str = "",
        checks: Optional[List[EngineeringCheck]] = None,
        desc: str = "",
        comments: Optional[str] = None,
        result_unit: Optional[str] = None
    ) -> None:
        """
        Initialize an engineering formula.
        
        Args:
            name: LaTeX symbol (e.g., "\\sigma", "M_r")
            params: Dictionary of parameter definitions
            logic: Function implementing the calculation
            latex_template: Function returning LaTeX equation template
            source: Reference source (code clause, standard, etc.)
            checks: List of checks to apply
            desc: Description of the formula
            comments: Additional comments
            result_unit: Optional unit for result. If specified, formula logic receives
                        magnitudes (floats) instead of Quantities, and result is wrapped
                        with this unit. Use for formulas with complex unit handling.
        """
        super().__init__(name, checks, desc)
        self.params = params
        self.logic = logic
        self.latex_template = latex_template
        self.source = source
        self.comments = comments
        self.substitutions: List[EngineeringFunction] = []
        self.result_unit = result_unit
        self.result_units: Optional[str] = None  # For display (legacy)
    
    def solve(self) -> EngineeringFormula:
        """
        Execute the formula calculation with unit validation.
        
        Validates that all inputs are Pint Quantities with correct dimensionality.
        
        If result_unit is specified:
          - Extracts magnitudes from inputs (formula receives floats)
          - Wraps result with specified unit
          
        If result_unit is NOT specified:
          - Passes Quantities to formula (Pint handles unit propagation)
          - Result must be a Quantity
        
        Returns:
            Self for method chaining
            
        Raises:
            UnitError: If inputs lack proper units or have wrong dimensionality
        """
        # If already solved, return immediately (idempotent behavior)
        if self.result is not None:
            return self
        
        # Validate inputs
        validated_inputs = {}
        first_quantity = None  # Store first quantity to get registry
        
        for key, value in self.inputs.items():
            # Handle formula substitutions
            if isinstance(value, EngineeringFunction):
                self.substitutions.append(value)
                value = value.result
                self.inputs[key] = value
            
            # Validate that input is a Quantity with proper units
            if key in self.params:
                param = self.params[key]
                validate_quantity(value, key, param.unit)
                
                # Store first quantity for registry access
                if first_quantity is None:
                    first_quantity = value
                
                # Store for calculation
                validated_inputs[key] = value
            else:
                # Parameter not defined - this shouldn't happen in strict mode
                raise ValueError(
                    f"Input '{key}' is not defined in formula parameters. "
                    f"Valid parameters: {list(self.params.keys())}"
                )
        
        # Execute calculation based on result_unit setting
        try:
            if self.result_unit is not None:
                # Magnitude mode: convert inputs to expected units, compute floats
                magnitude_inputs = {}
                for key, value in validated_inputs.items():
                    param = self.params[key]
                    magnitude_inputs[key] = extract_magnitude(value, param.unit)

                result_magnitude = self.logic(**magnitude_inputs)

                # Wrap result in the declared unit using the input registry when available
                if first_quantity is not None:
                    ureg = first_quantity._REGISTRY
                else:
                    from pint import UnitRegistry
                    ureg = UnitRegistry()

                self.result = result_magnitude * ureg(self.result_unit)
            else:
                # Quantity mode: let Pint propagate units
                result = self.logic(**validated_inputs)

                # Validate result is a Quantity
                if not is_quantity(result):
                    raise UnitError(
                        f"Formula '{self.name}' must return a Pint Quantity. "
                        f"Ensure the calculation function returns a Quantity object."
                    )

                self.result = result

        except Exception as e:
            raise RuntimeError(
                f"Error executing formula '{self.name}': {str(e)}\n"
                f"Inputs: {validated_inputs}"
            ) from e
        
        return self
    
    def generate_function_latex(self, index: int, precision: int = 3) -> str:
        """Generate LaTeX equation for the formula."""
        # Get LaTeX symbols
        symbols = [self.params[key].latex for key in self.inputs.keys() if key in self.params]
        symbolic_formula = self.latex_template(*symbols)
        
        # Get substituted values
        substitutions = []
        for key, value in self.inputs.items():
            if isinstance(value, str):
                substitutions.append(value)
            else:
                substitutions.append(LaTeXFormatter.format_value(value, index, precision))
        
        substituted_formula = self.latex_template(*substitutions)
        
        # Format result (result_unit already handled conversion if specified)
        result_str = LaTeXFormatter.format_value(self.result, index, precision)
        
        # Add source tag if provided
        source_tag = f"\\tag{{{self.source}}}" if self.source else ""
        
        equation = (
            f"{self.name} &= {symbolic_formula} \\\\ "
            f"&= {substituted_formula} \\\\ "
            f"&= {result_str} {source_tag}"
        )
        
        return equation
    
    def generate_param_latex(self) -> str:
        """Generate LaTeX for parameter definitions."""
        return LaTeXFormatter.format_parameter_table(self.params)
    
    def show_in(self, unit: str) -> EngineeringFormula:
        """
        Specify the unit for result display.
        
        Args:
            unit: Unit string
            
        Returns:
            Self for method chaining
        """
        self.result_units = unit
        return self


class EngineeringSwitch(EngineeringFunction):
    """
    A conditional formula that selects from multiple outputs based on bounds.
    
    Used for piecewise functions, table lookups, and conditional logic.
    
    Example:
        # K_factor selection based on slenderness ratio
        K_factor = EngineeringSwitch(
            name="K",
            params={"lambda": Param("\\lambda", desc="Slenderness ratio")},
            bounds=[10, 20, 30],
            outputs=[1.0, 0.9, 0.8, 0.7],
            source="Table 5.3"
        )
    """
    
    def __init__(
        self,
        name: str,
        params: Dict[str, Param],
        bounds: List[Union[float, EngineeringFunction]],
        outputs: List[Union[float, EngineeringFunction]],
        source: str = "",
        checks: Optional[List[EngineeringCheck]] = None,
        desc: str = "",
        comments: Optional[str] = None
    ) -> None:
        """
        Initialize an engineering switch.
        
        Args:
            name: LaTeX symbol
            params: Parameter definitions (typically single input parameter)
            bounds: List of boundary values (length n)
            outputs: List of output values (length n+1)
            source: Reference source
            checks: Checks to apply
            desc: Description
            comments: Additional comments
        """
        super().__init__(name, checks, desc)
        self.params = params
        self.bounds = bounds
        self.outputs = outputs
        self.source = source
        self.comments = comments
        
        self.solved_inputs: Optional[List] = None
        self.solved_bounds: Optional[List] = None
        self.solved_outputs: Optional[List] = None
        self.selected_output: Optional[Any] = None
        self.substitutions: List[EngineeringFunction] = []
        self.result_units: Optional[str] = None
        
        if len(outputs) != len(bounds) + 1:
            raise ValueError(
                f"outputs length ({len(outputs)}) must be bounds length ({len(bounds)}) + 1"
            )
    
    def solve(self) -> EngineeringSwitch:
        """Execute the switch logic with unit-aware vectorized operations."""
        # If already solved, return immediately (idempotent behavior)
        if self.result is not None:
            return self
        
        # Extract input values and handle formula substitutions
        self.solved_inputs = list(self.inputs.values())
        for idx, key in enumerate(self.inputs.keys()):
            value = self.inputs[key]
            if isinstance(value, EngineeringFunction):
                self.substitutions.append(value)
                # Auto-solve if not already solved
                if value.result is None:
                    value = value.solve()
                self.solved_inputs[idx] = value.result
                self.inputs[key] = value.result
        
        # Validate input parameter units
        for key, value in self.inputs.items():
            if key in self.params:
                param = self.params[key]
                validate_quantity(value, key, param.unit)
        
        # Extract output values and track units
        self.solved_outputs = []
        output_unit = None
        first_quantity = None
        
        for output in self.outputs:
            if isinstance(output, EngineeringFunction):
                # Auto-solve if not already solved
                if output.result is None:
                    output = output.solve()
                output_val = output.result
            else:
                output_val = output
            
            # Track unit from first Pint Quantity output
            if is_quantity(output_val) and output_unit is None:
                output_unit = str(output_val.units)
                first_quantity = output_val
                
            self.solved_outputs.append(output_val)
        
        # Extract bound values
        self.solved_bounds = []
        for bound in self.bounds:
            if isinstance(bound, EngineeringFunction):
                # Auto-solve if not already solved
                if bound.result is None:
                    bound = bound.solve()
                self.solved_bounds.append(bound.result)
            else:
                self.solved_bounds.append(bound)
        
        # Get input value and convert to Quantity if needed
        input_val = self.solved_inputs[0]
        param = list(self.params.values())[0]
        
        if is_quantity(input_val):
            # Let Pint handle unit conversion, then extract magnitude
            input_array = extract_magnitude(input_val, param.unit)
            if first_quantity is None:
                first_quantity = input_val
        else:
            # Legacy support for raw floats/arrays
            input_array = np.atleast_1d(input_val).astype(float)
        
        # Convert bounds to same units as input, then extract magnitudes
        bounds_array = []
        for bound in self.solved_bounds:
            if is_quantity(bound):
                # Convert to input's unit for comparison
                bounds_array.append(extract_magnitude(bound, param.unit))
            else:
                bounds_array.append(float(bound))
        
        # Convert outputs to output_unit, then extract magnitudes
        outputs_array = []
        for output in self.solved_outputs:
            if is_quantity(output):
                # Convert to output unit
                outputs_array.append(extract_magnitude(output, output_unit))
            else:
                outputs_array.append(output)
        
        # Apply switch logic using numpy.where for vectorization
        result_magnitude = outputs_array[0]
        
        for i, bound in enumerate(bounds_array):
            result_magnitude = np.where(
                input_array > bound, 
                outputs_array[i + 1], 
                result_magnitude
            )
        
        # Wrap result back in appropriate units
        if output_unit is not None and first_quantity is not None:
            ureg = first_quantity._REGISTRY
            self.result = result_magnitude * ureg(output_unit)
            self.result_units = output_unit
        else:
            self.result = result_magnitude
        
        return self
    
    def generate_function_latex(self, index: int, precision: int = 3) -> str:
        """Generate LaTeX for the switch selection."""
        # Get current input value
        input_val = self._get_value_at_index(self.solved_inputs[0], index)
        
        # Get current bound values
        bounds_at_index = [self._get_value_at_index(b, index) for b in self.solved_bounds]
        
        # Determine which output is selected based on bounds
        # Switch logic: outputs[0] if input <= bounds[0], outputs[1] if bounds[0] < input <= bounds[1], etc.
        selected_idx = 0
        for i, bound in enumerate(bounds_at_index):
            if input_val > bound:
                selected_idx = i + 1
            else:
                break
        
        # Get bound strings (names or values)
        bound_strs = []
        for bound in self.bounds:
            if isinstance(bound, EngineeringFunction):
                bound_strs.append(bound.name)
            else:
                bound_strs.append(str(bound))
        
        # Get output strings and track if they are functions (already have LHS)
        output_strs = []
        output_is_function = []
        for output in self.outputs:
            if isinstance(output, EngineeringFunction):
                # Use generate_function_latex to get just the equation without align* wrapper
                # Don't wrap in aligned - let it participate in parent align* alignment
                func_latex = output.generate_function_latex(index, precision)
                output_strs.append(func_latex)
                output_is_function.append(True)
            else:
                output_strs.append(str(self._get_value_at_index(output, index)))
                output_is_function.append(False)
        
        # Build condition text
        param_symbol = list(self.params.values())[0].latex
        
        if selected_idx == 0:
            condition = f"{param_symbol} \\leq {bound_strs[0]}"
        elif selected_idx == len(bounds_at_index):
            condition = f"{param_symbol} > {bound_strs[-1]}"
        else:
            condition = f"{bound_strs[selected_idx - 1]} < {param_symbol} \\leq {bound_strs[selected_idx]}"
        
        # If output is a function, it already includes LHS (symbol &= ...), otherwise add it
        if output_is_function[selected_idx]:
            equation = (
                f"\\text{{Condition:}} & \\quad {condition} \\\\ "
                f"{output_strs[selected_idx]}"
            )
        else:
            equation = (
                f"\\text{{Condition:}} & \\quad {condition} \\\\ "
                f"{self.name} &= {output_strs[selected_idx]}"
            )
        
        return equation
    
    def generate_param_latex(self) -> str:
        """Generate LaTeX for parameter definitions."""
        return LaTeXFormatter.format_parameter_table(self.params)
    
    def _get_value_at_index(self, value: Any, index: int) -> float:
        """Extract value at specific index from various types."""
        # Handle Pint Quantities
        if is_quantity(value):
            mag = value.magnitude
            if isinstance(mag, (float, int)):
                return float(mag)
            elif isinstance(mag, pd.Series):
                return float(mag.iloc[index])
            elif isinstance(mag, np.ndarray):
                return float(mag[index])
            else:
                return float(mag)
        # Handle raw values
        elif isinstance(value, (float, int)):
            return float(value)
        elif isinstance(value, pd.Series):
            return float(value.iloc[index])
        elif isinstance(value, np.ndarray):
            return float(value[index])
        else:
            return float(value)
    
    def show_in(self, unit: str) -> EngineeringSwitch:
        """Specify the unit for result display."""
        self.result_units = unit
        return self


# Wrapper for formula decorator
class FormulaWrapper:
    """Wrapper class for @formula decorator."""
    
    def __init__(self, func: Callable) -> None:
        """Initialize wrapper."""
        self._func = func
        # Preserve function metadata including docstring
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__qualname__ = func.__qualname__
        self.__annotations__ = func.__annotations__
        self.__wrapped__ = func
    
    def __call__(self, *args, **kwargs) -> EngineeringFunction:
        """Execute the wrapped function."""
        # Get parameter names from function signature
        param_names = list(signature(self._func).parameters.keys())
        
        # Convert positional args to kwargs
        for i, arg in enumerate(args):
            if i < len(param_names):
                kwargs[param_names[i]] = arg
        
        # Call the function to get EngineeringFunction object
        result = self._func(**kwargs)
        
        # Add inputs, solve, and run checks
        return result.add_inputs(**kwargs).solve().run_checks()
    
    def __repr__(self) -> str:
        return f"<Formula: {self._func.__name__}>"


def formula(func: Callable) -> Callable:
    """
    Decorator for creating formula functions.
    
    Example:
        @formula
        def stress(F, A):
            return EngineeringFormula(
                name="\\sigma",
                params={"F": Param("F"), "A": Param("A")},
                logic=lambda F, A: F / A,
                latex_template=lambda F, A: f"{F}/{A}"
            )
    
    Args:
        func: Function returning an EngineeringFormula
        
    Returns:
        Wrapped function that auto-executes the formula
    """
    return FormulaWrapper(func)


# Switch wrapper (same pattern as FormulaWrapper)
class SwitchWrapper:
    """Wrapper class for @switch decorator."""
    
    def __init__(self, func: Callable) -> None:
        """Initialize wrapper."""
        self._func = func
        # Preserve function metadata
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__qualname__ = func.__qualname__
        self.__annotations__ = func.__annotations__
        self.__wrapped__ = func
    
    def __call__(self, *args, **kwargs) -> EngineeringSwitch:
        """Execute the wrapped function."""
        # Get parameter names from function signature
        param_names = list(signature(self._func).parameters.keys())
        
        # Convert positional args to kwargs
        for i, arg in enumerate(args):
            if i < len(param_names):
                kwargs[param_names[i]] = arg
        
        # Call the function to get EngineeringSwitch object
        result = self._func(**kwargs)
        
        # Add inputs, solve, and run checks
        return result.add_inputs(**kwargs).solve().run_checks()
    
    def __repr__(self) -> str:
        return f"<Switch: {self._func.__name__}>"


def switch(func: Callable) -> Callable:
    """
    Decorator for creating switch functions.
    
    Example:
        @switch
        def K_factor(lambda1, lambda_e, KL_a, KL_b):
            return create_switch(
                name="K_L",
                params={"lambda1": Param("\\lambda", unit="dimensionless")},
                bounds=[10, lambda_e],
                outputs=[KL_a, KL_b]
            )
    
    Args:
        func: Function returning an EngineeringSwitch
        
    Returns:
        Wrapped function that auto-executes the switch
    """
    return SwitchWrapper(func)



def create_formula(
    name: str,
    params: Dict[str, Param],
    logic: Callable,
    latex_template: Callable,
    source: str = "",
    checks: Optional[List[EngineeringCheck]] = None,
    desc: str = "",
    comments: Optional[str] = None,
    result_unit: Optional[str] = None
) -> EngineeringFormula:
    """
    Factory function for creating formulas.
    
    Provides a convenient way to create formulas without importing the class.
    
    Args:
        name: LaTeX symbol
        params: Parameter definitions
        logic: Calculation function
        latex_template: LaTeX template function
        source: Reference source
        checks: Checks to apply
        desc: Description
        comments: Additional comments
        result_unit: Optional unit for result. If specified, formula logic receives
                    magnitudes (floats) instead of Quantities, and result is wrapped
                    with this unit. Use for formulas with complex unit handling.
        
    Returns:
        EngineeringFormula instance
    """
    return EngineeringFormula(
        name=name,
        params=params,
        logic=logic,
        latex_template=latex_template,
        source=source,
        checks=checks if checks else [],
        desc=desc,
        comments=comments,
        result_unit=result_unit
    )


def create_switch(
    name: str,
    params: Dict[str, Param],
    bounds: List[Union[float, EngineeringFunction]],
    outputs: List[Union[float, EngineeringFunction]],
    source: str = "",
    checks: Optional[List[EngineeringCheck]] = None,
    desc: str = "",
    comments: Optional[str] = None
) -> EngineeringSwitch:
    """
    Factory function for creating switches.
    
    Args:
        name: LaTeX symbol
        params: Parameter definitions
        bounds: Boundary values
        outputs: Output values
        source: Reference source
        checks: Checks to apply
        desc: Description
        comments: Additional comments
        
    Returns:
        EngineeringSwitch instance
    """
    return EngineeringSwitch(
        name=name,
        params=params,
        bounds=bounds,
        outputs=outputs,
        source=source,
        checks=checks if checks else [],
        desc=desc,
        comments=comments
    )
