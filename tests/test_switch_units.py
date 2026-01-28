"""
Unit tests for EngineeringSwitch with Pint quantities and vector operations.

Tests EIME's philosophy:
1. All inputs/outputs should be Pint quantities with units
2. Formulas should support vectorized (batch) operations with numpy arrays
3. Unit conversions should be automatic and transparent
"""

import pytest
import numpy as np
from eime import create_switch, Param, STATUS, Check
from eime.units import ureg


def test_switch_scalar_with_units():
    """Test switch with scalar Pint quantities."""
    # Create a simple switch for lateral stability factor
    # KL = 1.0 if lambda <= 10, else KL = f(lambda)
    switch = create_switch(
        name="K_L",
        params={"lambda1": Param("\\lambda", unit="dimensionless", desc="slenderness ratio")},
        bounds=[10.0 * ureg.dimensionless],
        outputs=[
            1.0 * ureg.dimensionless,  # lambda <= 10
            0.85 * ureg.dimensionless  # lambda > 10
        ],
        desc="Lateral stability factor"
    )
    
    # Test case 1: lambda = 8 (should return 1.0)
    result1 = switch.add_inputs(lambda1=8.0 * ureg.dimensionless).solve()
    assert result1.result.magnitude == pytest.approx(1.0)
    assert str(result1.result.units) == 'dimensionless'
    
    # Test case 2: lambda = 15 (should return 0.85)
    switch2 = create_switch(
        name="K_L",
        params={"lambda1": Param("\\lambda", unit="dimensionless", desc="slenderness ratio")},
        bounds=[10.0 * ureg.dimensionless],
        outputs=[
            1.0 * ureg.dimensionless,
            0.85 * ureg.dimensionless
        ],
        desc="Lateral stability factor"
    )
    result2 = switch2.add_inputs(lambda1=15.0 * ureg.dimensionless).solve()
    assert result2.result.magnitude == pytest.approx(0.85)


def test_switch_vector_with_units():
    """Test switch with vectorized Pint quantities (batch operations)."""
    # Create switch with multiple bounds
    switch = create_switch(
        name="K_factor",
        params={"ratio": Param("r", unit="dimensionless", desc="ratio")},
        bounds=[
            10.0 * ureg.dimensionless,
            20.0 * ureg.dimensionless,
            30.0 * ureg.dimensionless
        ],
        outputs=[
            1.0 * ureg.dimensionless,   # r <= 10
            0.9 * ureg.dimensionless,   # 10 < r <= 20
            0.8 * ureg.dimensionless,   # 20 < r <= 30
            0.7 * ureg.dimensionless    # r > 30
        ],
        desc="K-factor selection"
    )
    
    # Test with array of values
    ratios = np.array([5.0, 15.0, 25.0, 35.0]) * ureg.dimensionless
    result = switch.add_inputs(ratio=ratios).solve()
    
    # Verify results
    expected = np.array([1.0, 0.9, 0.8, 0.7])
    np.testing.assert_array_almost_equal(result.result.magnitude, expected)
    assert str(result.result.units) == 'dimensionless'


def test_switch_with_formula_inputs():
    """Test switch that receives results from other formulas."""
    from eime import create_formula
    
    # Create an upstream formula
    lambda_calc = create_formula(
        name="\\lambda",
        params={
            "L": Param("L", unit="mm", desc="length"),
            "d": Param("d", unit="mm", desc="depth")
        },
        logic=lambda L, d: L / d,
        latex_template=lambda L, d: f"{L} / {d}",
        result_unit="dimensionless"
    )
    
    # Calculate lambda values
    L_vals = np.array([3000, 6000, 9000]) * ureg.mm
    d_val = 300 * ureg.mm
    lambda_result = lambda_calc.add_inputs(L=L_vals, d=d_val).solve()
    
    # Use in switch
    switch = create_switch(
        name="K_L",
        params={"lambda1": Param("\\lambda", unit="dimensionless", desc="slenderness")},
        bounds=[10.0 * ureg.dimensionless, 20.0 * ureg.dimensionless],
        outputs=[
            1.0 * ureg.dimensionless,
            0.9 * ureg.dimensionless,
            0.8 * ureg.dimensionless
        ]
    )
    
    result = switch.add_inputs(lambda1=lambda_result).solve()
    
    # lambda values are [10, 20, 30], so outputs should be [1.0, 0.9, 0.8]
    expected = np.array([1.0, 0.9, 0.8])
    np.testing.assert_array_almost_equal(result.result.magnitude, expected)


def test_switch_with_formula_outputs():
    """Test switch where outputs come from other formulas."""
    from eime import create_formula
    
    # Create output formulas
    KL_a = create_formula(
        name="K_{L,a}",
        params={},
        logic=lambda: 1.0,
        latex_template=lambda: "1.0",
        result_unit="dimensionless"
    ).add_inputs().solve()
    
    KL_b = create_formula(
        name="K_{L,b}",
        params={"lambda1": Param("\\lambda", unit="dimensionless")},
        logic=lambda lambda1: 0.9 - 0.01 * lambda1,
        latex_template=lambda lambda1: f"0.9 - 0.01 {lambda1}",
        result_unit="dimensionless"
    )
    
    lambda_vals = np.array([5.0, 15.0]) * ureg.dimensionless
    KL_b_result = KL_b.add_inputs(lambda1=lambda_vals).solve()
    
    # Create switch using formula results
    switch = create_switch(
        name="K_L",
        params={"lambda1": Param("\\lambda", unit="dimensionless")},
        bounds=[10.0 * ureg.dimensionless],
        outputs=[KL_a, KL_b_result]
    )
    
    result = switch.add_inputs(lambda1=lambda_vals).solve()
    
    # For lambda=5: use KL_a = 1.0
    # For lambda=15: use KL_b = 0.9 - 0.01*15 = 0.75
    expected = np.array([1.0, 0.75])
    np.testing.assert_array_almost_equal(result.result.magnitude, expected)


def test_switch_with_checks():
    """Test switch with engineering checks."""
    switch = create_switch(
        name="K_L",
        params={"lambda1": Param("\\lambda", unit="dimensionless")},
        bounds=[10.0 * ureg.dimensionless],
        outputs=[
            1.0 * ureg.dimensionless,
            0.85 * ureg.dimensionless
        ],
        checks=[
            Check.upperbound(1.01 * ureg.dimensionless, STATUS.FAIL, 102, "K_L must be ≤ 1.0", inclusive=True)
        ]
    )
    
    # Test with values that pass and fail the check
    lambda_vals = np.array([8.0, 15.0]) * ureg.dimensionless
    result = switch.add_inputs(lambda1=lambda_vals).solve().run_checks()
    
    # First should pass (KL=1.0), second should pass (KL=0.85)
    assert result.checks[0].applied_status_codes[0] == STATUS.PASS
    assert result.checks[0].applied_status_codes[1] == STATUS.PASS


def test_switch_unit_conversion():
    """Test that switch handles unit conversion correctly."""
    # Create switch with bounds in meters
    switch = create_switch(
        name="category",
        params={"length": Param("L", unit="m", desc="length")},
        bounds=[
            5.0 * ureg.m,
            10.0 * ureg.m
        ],
        outputs=[
            1.0 * ureg.dimensionless,  # Short
            2.0 * ureg.dimensionless,  # Medium
            3.0 * ureg.dimensionless   # Long
        ]
    )
    
    # Provide input in millimeters
    lengths = np.array([3000, 7000, 12000]) * ureg.mm
    result = switch.add_inputs(length=lengths).solve()
    
    # 3000mm = 3m -> 1.0, 7000mm = 7m -> 2.0, 12000mm = 12m -> 3.0
    expected = np.array([1.0, 2.0, 3.0])
    np.testing.assert_array_almost_equal(result.result.magnitude, expected)


def test_switch_idempotent():
    """Test that calling solve() multiple times doesn't change result."""
    switch = create_switch(
        name="K",
        params={"x": Param("x", unit="dimensionless")},
        bounds=[10.0 * ureg.dimensionless],
        outputs=[1.0 * ureg.dimensionless, 0.5 * ureg.dimensionless]
    )
    
    x_val = 15.0 * ureg.dimensionless
    result1 = switch.add_inputs(x=x_val).solve()
    first_result = result1.result.magnitude
    
    # Call solve again
    result2 = result1.solve()
    second_result = result2.result.magnitude
    
    assert first_result == second_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
