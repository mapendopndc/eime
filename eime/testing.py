"""
Testing framework for engineering formulas.

This module provides utilities for unit testing engineering formulas
with tolerance-based comparisons and clear test reporting.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from .formula import EngineeringFunction


class FormulaTestCase:
    """
    A single test case for an engineering formula.
    
    Example:
        test = FormulaTestCase(
            name="Stress test 1",
            inputs={"F": 1000, "A": 100},
            expected_result=10.0,
            tolerance=0.001
        )
    """
    
    def __init__(
        self,
        name: str,
        inputs: Dict[str, Any],
        expected_result: float,
        tolerance: float = 0.001,
        description: str = ""
    ) -> None:
        """
        Initialize a test case.
        
        Args:
            name: Test case name
            inputs: Dictionary of input values
            expected_result: Expected formula result
            tolerance: Relative tolerance for comparison
            description: Optional description
        """
        self.name = name
        self.inputs = inputs
        self.expected_result = expected_result
        self.tolerance = tolerance
        self.description = description
        self.passed: Optional[bool] = None
        self.actual_result: Optional[float] = None
        self.error: Optional[str] = None
    
    def run(self, formula_func: Callable) -> bool:
        """
        Run this test case.
        
        Args:
            formula_func: Function that creates and returns a formula
            
        Returns:
            True if test passes
        """
        try:
            # Execute formula
            formula = formula_func(**self.inputs)
            
            # Extract scalar result
            result = formula.result
            if isinstance(result, (pd.Series, np.ndarray)):
                result = float(result.iloc[0] if isinstance(result, pd.Series) else result[0])
            
            self.actual_result = float(result)
            
            # Compare with tolerance
            relative_error = abs(self.actual_result - self.expected_result) / abs(self.expected_result)
            self.passed = relative_error <= self.tolerance
            
            if not self.passed:
                self.error = f"Expected {self.expected_result}, got {self.actual_result} (error: {relative_error:.2%})"
            
        except Exception as e:
            self.passed = False
            self.error = f"Exception: {str(e)}"
        
        return self.passed
    
    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL" if self.passed is False else "NOT RUN"
        return f"<TestCase '{self.name}': {status}>"


class FormulaTestSuite:
    """
    Collection of test cases for a formula.
    
    Example:
        suite = FormulaTestSuite("Stress formula")
        suite.add_test("Test 1", {"F": 1000, "A": 100}, 10.0)
        suite.add_test("Test 2", {"F": 2000, "A": 200}, 10.0)
        suite.run(stress_formula)
    """
    
    def __init__(self, name: str) -> None:
        """
        Initialize test suite.
        
        Args:
            name: Suite name
        """
        self.name = name
        self.test_cases: List[FormulaTestCase] = []
    
    def add_test(
        self,
        name: str,
        inputs: Dict[str, Any],
        expected_result: float,
        tolerance: float = 0.001,
        description: str = ""
    ) -> None:
        """
        Add a test case to the suite.
        
        Args:
            name: Test name
            inputs: Input values
            expected_result: Expected result
            tolerance: Relative tolerance
            description: Optional description
        """
        test = FormulaTestCase(name, inputs, expected_result, tolerance, description)
        self.test_cases.append(test)
    
    def add_test_case(self, test_case: FormulaTestCase) -> None:
        """Add an existing test case."""
        self.test_cases.append(test_case)
    
    def run(self, formula_func: Callable, verbose: bool = True) -> Tuple[int, int]:
        """
        Run all test cases.
        
        Args:
            formula_func: Function that creates the formula
            verbose: If True, print results
            
        Returns:
            Tuple of (passed_count, failed_count)
        """
        passed = 0
        failed = 0
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"Running test suite: {self.name}")
            print(f"{'='*60}\n")
        
        for test in self.test_cases:
            result = test.run(formula_func)
            
            if result:
                passed += 1
                if verbose:
                    print(f"✓ {test.name}: PASS")
            else:
                failed += 1
                if verbose:
                    print(f"✗ {test.name}: FAIL")
                    print(f"  {test.error}")
        
        if verbose:
            print(f"\n{'-'*60}")
            print(f"Results: {passed} passed, {failed} failed")
            print(f"{'='*60}\n")
        
        return passed, failed
    
    def __repr__(self) -> str:
        return f"<FormulaTestSuite '{self.name}': {len(self.test_cases)} tests>"


def test_formula(
    formula_func: Callable,
    test_cases: List[Dict[str, Any]],
    name: str = "Formula Test",
    tolerance: float = 0.001,
    verbose: bool = True
) -> bool:
    """
    Convenience function for testing a formula.
    
    Args:
        formula_func: Function that creates the formula
        test_cases: List of test case dicts with 'inputs' and 'expected'
        name: Test suite name
        tolerance: Default tolerance
        verbose: Print results
        
    Returns:
        True if all tests pass
        
    Example:
        tests = [
            {"inputs": {"F": 1000, "A": 100}, "expected": 10.0},
            {"inputs": {"F": 2000, "A": 200}, "expected": 10.0}
        ]
        
        test_formula(stress_formula, tests)
    """
    suite = FormulaTestSuite(name)
    
    for i, test_data in enumerate(test_cases):
        test_name = test_data.get('name', f"Test {i+1}")
        inputs = test_data['inputs']
        expected = test_data['expected']
        test_tolerance = test_data.get('tolerance', tolerance)
        description = test_data.get('description', '')
        
        suite.add_test(test_name, inputs, expected, test_tolerance, description)
    
    passed, failed = suite.run(formula_func, verbose=verbose)
    
    return failed == 0


def compare_values(
    actual: Any,
    expected: Any,
    tolerance: float = 0.001,
    relative: bool = True
) -> Tuple[bool, float]:
    """
    Compare two values with tolerance.
    
    Args:
        actual: Actual value
        expected: Expected value
        tolerance: Tolerance threshold
        relative: If True, use relative tolerance; if False, absolute
        
    Returns:
        Tuple of (passed, error)
    """
    # Convert to floats
    if isinstance(actual, (pd.Series, np.ndarray)):
        actual = float(actual.iloc[0] if isinstance(actual, pd.Series) else actual[0])
    else:
        actual = float(actual)
    
    if isinstance(expected, (pd.Series, np.ndarray)):
        expected = float(expected.iloc[0] if isinstance(expected, pd.Series) else expected[0])
    else:
        expected = float(expected)
    
    # Calculate error
    if relative:
        if expected == 0:
            error = abs(actual)
        else:
            error = abs(actual - expected) / abs(expected)
    else:
        error = abs(actual - expected)
    
    # Check tolerance
    passed = error <= tolerance
    
    return passed, error


def assert_formula_result(
    formula: EngineeringFunction,
    expected: float,
    tolerance: float = 0.001,
    message: str = ""
) -> None:
    """
    Assert that a formula result matches expected value.
    
    Args:
        formula: Solved formula
        expected: Expected result
        tolerance: Relative tolerance
        message: Custom error message
        
    Raises:
        AssertionError: If result doesn't match
    """
    passed, error = compare_values(formula.result, expected, tolerance)
    
    if not passed:
        if message:
            error_msg = message
        else:
            actual = formula.result
            if isinstance(actual, (pd.Series, np.ndarray)):
                actual = float(actual.iloc[0] if isinstance(actual, pd.Series) else actual[0])
            
            error_msg = (
                f"Formula result mismatch:\n"
                f"  Expected: {expected}\n"
                f"  Actual: {actual}\n"
                f"  Relative error: {error:.2%}"
            )
        
        raise AssertionError(error_msg)


class PropertyBasedTest:
    """
    Property-based testing for formulas.
    
    Tests that certain properties hold for randomly generated inputs.
    
    Example:
        # Test that doubling force doubles stress
        def test_linearity(inputs):
            F1 = inputs['F']
            F2 = 2 * F1
            
            result1 = stress_formula(F=F1, A=inputs['A']).result
            result2 = stress_formula(F=F2, A=inputs['A']).result
            
            return abs(result2 - 2 * result1) < 0.001
        
        prop_test = PropertyBasedTest(test_linearity)
        prop_test.run(100)  # Run 100 random tests
    """
    
    def __init__(
        self,
        property_func: Callable,
        name: str = "Property Test"
    ) -> None:
        """
        Initialize property test.
        
        Args:
            property_func: Function that tests a property, returns bool
            name: Test name
        """
        self.property_func = property_func
        self.name = name
    
    def generate_random_inputs(
        self,
        input_ranges: Dict[str, Tuple[float, float]]
    ) -> Dict[str, Any]:
        """
        Generate random inputs within ranges.
        
        Args:
            input_ranges: Dict of {param: (min, max)}
            
        Returns:
            Random input dict
        """
        import random
        
        inputs = {}
        for param, (min_val, max_val) in input_ranges.items():
            inputs[param] = random.uniform(min_val, max_val)
        
        return inputs
    
    def run(
        self,
        n_tests: int,
        input_ranges: Dict[str, Tuple[float, float]],
        verbose: bool = True
    ) -> bool:
        """
        Run property-based tests.
        
        Args:
            n_tests: Number of random tests to run
            input_ranges: Input parameter ranges
            verbose: Print results
            
        Returns:
            True if all tests pass
        """
        passed = 0
        failed = 0
        
        if verbose:
            print(f"\nRunning property test: {self.name} ({n_tests} tests)")
        
        for i in range(n_tests):
            inputs = self.generate_random_inputs(input_ranges)
            
            try:
                result = self.property_func(inputs)
                if result:
                    passed += 1
                else:
                    failed += 1
                    if verbose:
                        print(f"  Test {i+1} failed with inputs: {inputs}")
            except Exception as e:
                failed += 1
                if verbose:
                    print(f"  Test {i+1} raised exception: {e}")
        
        if verbose:
            print(f"Results: {passed}/{n_tests} passed\n")
        
        return failed == 0
