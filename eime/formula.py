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
    def generate_function_latex(self, index: int) -> str:
        """
        Generate LaTeX for the function equation.
        
        Args:
            index: Index for array-like results
            
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
    
    def generate_checks_latex(self, index: int) -> str:
        """
        Generate LaTeX for all checks.
        
        Args:
            index: Index for array-like results
            
        Returns:
            LaTeX string
        """
        if not self.checks:
            return ""
        
        return LaTeXFormatter.format_check_summary(self.checks, index)
    
    def generate_latex(self, index: int = 0) -> str:
        """
        Generate complete LaTeX representation.
        
        Args:
            index: Index for array-like results
            
        Returns:
            Complete LaTeX string with formula, params, and checks
        """
        content = self.generate_function_latex(index) + " \\\\ "
        
        param_latex = self.generate_param_latex()
        if param_latex:
            content += param_latex + " \\\\ "
        
        checks_latex = self.generate_checks_latex(index)
        if checks_latex:
            content += checks_latex
        
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
        comments: Optional[str] = None
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
        """
        super().__init__(name, checks, desc)
        self.params = params
        self.logic = logic
        self.latex_template = latex_template
        self.source = source
        self.comments = comments
        self.substitutions: List[EngineeringFunction] = []
        self.result_units: Optional[str] = None
    
    def solve(self) -> EngineeringFormula:
        """Execute the formula calculation."""
        # Track substitutions (when inputs are other formulas)
        for key, value in self.inputs.items():
            if isinstance(value, EngineeringFunction):
                self.substitutions.append(value)
                self.inputs[key] = value.result
        
        # Execute calculation
        self.result = self.logic(**self.inputs)
        
        return self
    
    def generate_function_latex(self, index: int) -> str:
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
                substitutions.append(LaTeXFormatter.format_value(value, index))
        
        substituted_formula = self.latex_template(*substitutions)
        
        # Format result
        result_str = LaTeXFormatter.format_value(self.result, index)
        
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
        """Execute the switch logic."""
        # Extract input values
        self.solved_inputs = list(self.inputs.values())
        for idx, key in enumerate(self.inputs.keys()):
            value = self.inputs[key]
            if isinstance(value, EngineeringFunction):
                self.solved_inputs[idx] = value.result
        
        # Extract output values
        self.solved_outputs = []
        for output in self.outputs:
            if isinstance(output, EngineeringFunction):
                self.solved_outputs.append(output.result)
            else:
                self.solved_outputs.append(output)
        
        # Extract bound values
        self.solved_bounds = []
        for bound in self.bounds:
            if isinstance(bound, EngineeringFunction):
                self.solved_bounds.append(bound.result)
            else:
                self.solved_bounds.append(bound)
        
        # Apply switch logic using numpy.where
        input_array = np.array(self.solved_inputs[0], dtype=float)
        result = self.solved_outputs[0]
        
        for i, bound in enumerate(self.solved_bounds):
            result = np.where(input_array > bound, self.solved_outputs[i + 1], result)
        
        self.result = result
        return self
    
    def generate_function_latex(self, index: int) -> str:
        """Generate LaTeX for the switch selection."""
        # Get current input value
        input_val = self._get_value_at_index(self.solved_inputs[0], index)
        
        # Get current bound values
        bounds_at_index = [self._get_value_at_index(b, index) for b in self.solved_bounds]
        
        # Determine which output is selected
        selected_idx = 0
        if input_val > bounds_at_index[-1]:
            selected_idx = len(bounds_at_index)
        else:
            for i, bound in enumerate(bounds_at_index):
                if i + 1 < len(bounds_at_index):
                    if input_val > bound and input_val <= bounds_at_index[i + 1]:
                        selected_idx = i + 1
                        break
        
        # Get bound strings (names or values)
        bound_strs = []
        for bound in self.bounds:
            if isinstance(bound, EngineeringFunction):
                bound_strs.append(bound.name)
            else:
                bound_strs.append(str(bound))
        
        # Get output strings
        output_strs = []
        for output in self.outputs:
            if isinstance(output, EngineeringFunction):
                output_strs.append(output.generate_latex(index))
            else:
                output_strs.append(str(self._get_value_at_index(output, index)))
        
        # Build condition text
        param_symbol = list(self.params.values())[0].latex
        
        if selected_idx == 0:
            condition = f"{param_symbol} \\leq {bound_strs[0]}"
        elif selected_idx == len(bounds_at_index):
            condition = f"{param_symbol} > {bound_strs[-1]}"
        else:
            condition = f"{bound_strs[selected_idx - 1]} < {param_symbol} \\leq {bound_strs[selected_idx]}"
        
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
        if isinstance(value, (float, int)):
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
        update_wrapper(self, func)
    
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


def formula(func: Callable) -> FormulaWrapper:
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
    return wraps(func)(FormulaWrapper(func))


def create_formula(
    name: str,
    params: Dict[str, Param],
    logic: Callable,
    latex_template: Callable,
    source: str = "",
    checks: Optional[List[EngineeringCheck]] = None,
    desc: str = "",
    comments: Optional[str] = None
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
        comments=comments
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
