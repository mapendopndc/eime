"""
Unit tests for CSA O86-2025 timber design formulas.

Tests verify that migrated formulas produce correct results.
"""

import pytest
import numpy as np
from eime import FormulaTestSuite, FormulaTestCase, assert_formula_result
from design.csa_o86_2025.formulas import (
    # Section Properties
    moment_of_inertia,
    section_modulus,
    stiffness_modulus_of_elasticity,
    # Bending
    long_duration_factor,
    modified_bending_strength,
    bending_size_factor,
    slenderness_ratio,
    slenderness_ratio_limit,
    lateral_stability_factor_b,
    moment_resistance_a,
    # Shear
    modified_shear_strength,
    shear_resistance,
    # Compression
    modified_compression_strength,
    compression_size_factor,
    compression_slenderness_ratio,
    slenderness_factor,
    compression_resistance,
)


class TestSectionProperties:
    """Test section property calculations."""
    
    def test_moment_of_inertia(self):
        """Test moment of inertia for rectangular section."""
        I = moment_of_inertia(b=130, d=456)
        expected = 130 * 456**3 / 12
        assert_formula_result(I, expected, tolerance=1e-6)
    
    def test_section_modulus(self):
        """Test section modulus for rectangular section."""
        S = section_modulus(b=130, d=456)
        expected = 130 * 456**2 / 6
        assert_formula_result(S, expected, tolerance=1e-6)
    
    def test_stiffness_modulus(self):
        """Test stiffness modulus of elasticity."""
        E_s = stiffness_modulus_of_elasticity(E=11700, K_SE=1.0, K_T=1.0)
        assert_formula_result(E_s, 11700, tolerance=1e-6)


class TestBendingFormulas:
    """Test bending resistance formulas."""
    
    def test_long_duration_factor(self):
        """Test long duration factor calculation."""
        K_D = long_duration_factor(P_L=10.0, P_S=20.0)
        expected = max(1.0 - 0.50 * np.log10(10.0/20.0), 0.65)
        assert_formula_result(K_D, expected, tolerance=1e-6)
    
    def test_long_duration_factor_minimum(self):
        """Test that K_D doesn't go below 0.65."""
        K_D = long_duration_factor(P_L=50.0, P_S=10.0)
        assert K_D.result >= 0.65, "K_D should not be less than 0.65"
    
    def test_modified_bending_strength(self):
        """Test modified bending strength."""
        F_b = modified_bending_strength(
            f_b=30.8,
            K_D=0.65,
            K_H=1.0,
            K_Sb=1.0,
            K_T=1.0
        )
        expected = 30.8 * 0.65 * 1.0 * 1.0 * 1.0
        assert_formula_result(F_b, expected, tolerance=1e-6)
    
    def test_bending_size_factor(self):
        """Test bending size factor (K_Zbg)."""
        K_Zbg = bending_size_factor(b=130, d=456, L=5000)
        expected = (130/130)**0.1 * (610/456)**0.1 * (9100/5000)**0.1
        assert_formula_result(K_Zbg, expected, tolerance=1e-6)
        assert K_Zbg.result <= 1.3, "K_Zbg should not exceed 1.3"
    
    def test_slenderness_ratio(self):
        """Test slenderness ratio."""
        lambda_val = slenderness_ratio(L_u=3000, d=456, b=130)
        expected = np.sqrt(3000 * 456 / 130**2)
        assert_formula_result(lambda_val, expected, tolerance=1e-6)
    
    def test_slenderness_ratio_limit(self):
        """Test slenderness ratio limit."""
        lambda_e = slenderness_ratio_limit(
            E=11700,
            K_SE=1.0,
            K_T=1.0,
            F_b=20.0
        )
        expected = np.sqrt(0.97 * 11700 * 1.0 * 1.0 / 20.0)
        assert_formula_result(lambda_e, expected, tolerance=1e-6)
    
    def test_lateral_stability_factor_b(self):
        """Test lateral stability factor (case b)."""
        K_L = lateral_stability_factor_b(lambda_1=15.0, lambda_e=20.0)
        expected = 1 - (1/3) * (15.0/20.0)**4
        assert_formula_result(K_L, expected, tolerance=1e-6)
    
    def test_moment_resistance_a(self):
        """Test moment resistance (case a - fully braced)."""
        M_r = moment_resistance_a(
            phi=0.9,
            F_b=20.0,
            S=4500000,  # mm³
            K_x=1.0,
            K_Zbg=1.1
        )
        expected = 0.9 * 20.0 * 4500000 * 1.0 * 1.1
        assert_formula_result(M_r, expected, tolerance=1e-6)


class TestShearFormulas:
    """Test shear resistance formulas."""
    
    def test_modified_shear_strength(self):
        """Test modified shear strength."""
        F_v = modified_shear_strength(
            f_v=2.1,
            K_D=0.65,
            K_H=1.0,
            K_Sv=1.0,
            K_T=1.0
        )
        expected = 2.1 * 0.65 * 1.0 * 1.0 * 1.0
        assert_formula_result(F_v, expected, tolerance=1e-6)
    
    def test_shear_resistance(self):
        """Test shear resistance."""
        V_r = shear_resistance(
            phi=0.9,
            F_v=1.5,
            A_g=59280  # mm²
        )
        expected = 0.9 * 1.5 * 2 * 59280 / 3
        assert_formula_result(V_r, expected, tolerance=1e-6)


class TestCompressionFormulas:
    """Test compression resistance formulas."""
    
    def test_modified_compression_strength(self):
        """Test modified compression strength."""
        F_c = modified_compression_strength(
            f_c=27.5,
            K_D=0.65,
            K_H=1.0,
            K_Sc=1.0,
            K_T=1.0
        )
        expected = 27.5 * 0.65 * 1.0 * 1.0 * 1.0
        assert_formula_result(F_c, expected, tolerance=1e-6)
    
    def test_compression_size_factor(self):
        """Test compression size factor."""
        # Volume = b * d * L / 1e9 (convert to m³)
        Z = 130 * 456 * 5000 / 1e9  # 0.2964 m³
        K_Zcg = compression_size_factor(Z=Z)
        expected = 0.68 * Z**(-0.13)
        assert_formula_result(K_Zcg, expected, tolerance=1e-6)
        assert K_Zcg.result <= 1.0, "K_Zcg should not exceed 1.0"
    
    def test_compression_slenderness_ratio(self):
        """Test compression slenderness ratio."""
        C_C = compression_slenderness_ratio(L_e=3000, w=130)
        expected = 3000 / 130
        assert_formula_result(C_C, expected, tolerance=1e-6)
    
    def test_slenderness_factor(self):
        """Test slenderness factor."""
        K_c = slenderness_factor(
            F_c=17.875,
            K_Zcg=1.0,
            C_C=23.08,
            E_05=9800,
            K_SE=1.0,
            K_T=1.0
        )
        expected = 1 / (1 + 17.875 * 1.0 * 23.08**3 / (35 * 9800 * 1.0 * 1.0))
        assert_formula_result(K_c, expected, tolerance=1e-6)
    
    def test_compression_resistance(self):
        """Test compression resistance."""
        P_r = compression_resistance(
            phi=0.8,
            F_c=17.875,
            A=59280,
            K_Zcg=1.0,
            K_C=0.8
        )
        expected = 0.8 * 17.875 * 59280 * 1.0 * 0.8
        assert_formula_result(P_r, expected, tolerance=1e-6)


class TestBatchCalculations:
    """Test that formulas work with numpy arrays (batch mode)."""
    
    def test_long_duration_factor_batch(self):
        """Test K_D with array inputs."""
        P_L = np.array([10.0, 20.0, 30.0])
        P_S = np.array([20.0, 30.0, 40.0])
        K_D = long_duration_factor(P_L=P_L, P_S=P_S)
        results = K_D.result
        
        assert isinstance(results, np.ndarray)
        assert len(results) == 3
        assert all(results >= 0.65), "All K_D values should be >= 0.65"
    
    def test_section_modulus_batch(self):
        """Test section modulus with array inputs."""
        b = np.array([130, 175, 215])
        d = np.array([456, 608, 684])
        S = section_modulus(b=b, d=d)
        results = S.result
        
        assert isinstance(results, np.ndarray)
        assert len(results) == 3
        expected = b * d**2 / 6
        np.testing.assert_allclose(results, expected, rtol=1e-6)


# Create test suite for easy execution
def create_test_suite():
    """Create a FormulaTestSuite with all test cases."""
    suite = FormulaTestSuite("CSA O86-2025 Timber Formulas")
    
    # Add test cases here (would need to convert pytest tests to FormulaTestCase format)
    # This is a placeholder showing the pattern
    
    return suite


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])
