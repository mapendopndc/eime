"""
Unit tests for EIME formula framework.
"""

import pytest
import numpy as np
import eime


def test_simple_formula():
    """Test basic formula creation and execution."""
    formula = eime.create_formula(
        name="test",
        params={"a": eime.Param("a"), "b": eime.Param("b")},
        logic=lambda a, b: a + b,
        latex_template=lambda a, b: f"{a} + {b}"
    )
    
    result = formula.add_inputs(a=5, b=3).solve()
    assert result.result == 8


def test_formula_with_checks():
    """Test formula with upper bound check."""
    formula = eime.create_formula(
        name="test",
        params={"a": eime.Param("a")},
        logic=lambda a: a * 2,
        latex_template=lambda a: f"2{a}",
        checks=[
            eime.Check.upperbound(10, eime.STATUS.FAIL, 1, "Exceeds limit")
        ]
    )
    
    result = formula.add_inputs(a=3).solve().run_checks()
    assert result.result == 6
    assert result.checks[0].applied_status_codes == eime.STATUS.PASS


def test_batch_calculation():
    """Test batch calculation with arrays."""
    formula = eime.create_formula(
        name="test",
        params={"a": eime.Param("a"), "b": eime.Param("b")},
        logic=lambda a, b: a * b,
        latex_template=lambda a, b: f"{a} \\times {b}"
    )
    
    a_vals = np.array([1, 2, 3, 4])
    b_vals = np.array([2, 3, 4, 5])
    
    result = formula.add_inputs(a=a_vals, b=b_vals).solve()
    
    expected = np.array([2, 6, 12, 20])
    np.testing.assert_array_equal(result.result, expected)


def test_check_upperbound():
    """Test upper bound check."""
    check = eime.Upperbound(
        upperbound=100,
        status_code=eime.STATUS.FAIL,
        check_id=1,
        message="Exceeds maximum"
    )
    
    # Create mock formula
    class MockFormula:
        def __init__(self):
            self.result = np.array([50, 100, 150])
            self.name = "test"
    
    formula = MockFormula()
    check.set_formula(formula)
    
    expected_status = np.array([eime.STATUS.PASS, eime.STATUS.PASS, eime.STATUS.FAIL])
    np.testing.assert_array_equal(check.applied_status_codes, expected_status)


def test_check_lowerbound():
    """Test lower bound check."""
    check = eime.Lowerbound(
        lowerbound=50,
        status_code=eime.STATUS.WARNING,
        check_id=2,
        message="Below minimum",
        inclusive=False  # Changed to False - fails when result < 50
    )
    
    class MockFormula:
        def __init__(self):
            self.result = np.array([40, 50, 60])
            self.name = "test"
    
    formula = MockFormula()
    check.set_formula(formula)
    
    # With inclusive=False: 40 < 50 (WARNING), 50 < 50 (PASS), 60 < 50 (PASS)
    expected_status = np.array([eime.STATUS.WARNING, eime.STATUS.PASS, eime.STATUS.PASS])
    np.testing.assert_array_equal(check.applied_status_codes, expected_status)


def test_procedure():
    """Test engineering procedure."""
    procedure = eime.EngineeringProcedure("Test Procedure")
    
    # Add some formulas - use arrays instead of scalars
    f1 = eime.create_formula(
        name="A",
        params={"x": eime.Param("x")},
        logic=lambda x: x * 2,
        latex_template=lambda x: f"2{x}"
    ).add_inputs(x=np.array([5])).solve().run_checks()
    
    f2 = eime.create_formula(
        name="B",
        params={"y": eime.Param("y")},
        logic=lambda y: y + 3,
        latex_template=lambda y: f"{y} + 3"
    ).add_inputs(y=f1.result).solve().run_checks()
    
    procedure.add_title("Section 1")
    procedure.add_computation(f1)
    procedure.add_computation(f2)
    
    assert "A" in procedure.results.columns
    assert "B" in procedure.results.columns
    assert procedure.results["A"][0] == 10
    assert procedure.results["B"][0] == 13


def test_formula_test_framework():
    """Test the formula testing utilities."""
    def my_formula(a, b):
        return eime.create_formula(
            name="result",
            params={"a": eime.Param("a"), "b": eime.Param("b")},
            logic=lambda a, b: a + b,
            latex_template=lambda a, b: f"{a}+{b}"
        ).add_inputs(a=a, b=b).solve()
    
    test_cases = [
        {"inputs": {"a": 1, "b": 2}, "expected": 3},
        {"inputs": {"a": 5, "b": 5}, "expected": 10}
    ]
    
    result = eime.test_formula(my_formula, test_cases, verbose=False)
    assert result is True


def test_param():
    """Test Param class."""
    param = eime.Param("x", val=10, desc="Test parameter", src="Example")
    
    assert param.latex == "x"
    assert param.val == 10
    assert param.desc == "Test parameter"
    assert param.src == "Example"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
