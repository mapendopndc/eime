"""
Simple test script for K_D (load duration factor) functionality.

Tests the load_duration_factor function with various scenarios.
"""

from eime.units import ureg
from design.csa_o86_2025.formulas.load_duration import load_duration_factor
from design.csa_o86_2025.tables import kd_from_load_type

# Unit shorthands
nd = ureg.dimensionless


def test_kd_dead_only():
    """Test K_D for dead load only (should be 0.65)."""
    print("\n" + "="*60)
    print("TEST 1: Dead Load Only")
    print("="*60)
    
    P_L = 100.0 * nd  # 100% dead load
    P_S = 0.0 * nd    # 0% other loads
    
    kd = load_duration_factor(
        P_L=P_L,
        P_S=P_S,
        kd_table=kd_from_load_type('dead_only')
    )
    
    print(f"P_L: {P_L}")
    print(f"P_S: {P_S}")
    print(f"Load Type: dead_only")
    print(f"K_D Result: {kd.result}")
    print(f"Expected: 0.65")
    print(f"Status: {'PASS' if abs(kd.result.magnitude - 0.65) < 0.01 else 'FAIL'}")


def test_kd_includes_live():
    """Test K_D for live/snow loads (should be 1.0)."""
    print("\n" + "="*60)
    print("TEST 2: Includes Live/Snow Load")
    print("="*60)
    
    P_L = 40.0 * nd   # 40% long-term
    P_S = 60.0 * nd   # 60% standard-term
    
    kd = load_duration_factor(
        P_L=P_L,
        P_S=P_S,
        kd_table=kd_from_load_type('includes_live')
    )
    
    print(f"P_L: {P_L}")
    print(f"P_S: {P_S}")
    print(f"P_L/P_S: {P_L/P_S:.2f}")
    print(f"Load Type: includes_live")
    print(f"K_D Result: {kd.result}")
    print(f"Expected: 1.0 (since P_L < P_S)")
    print(f"Status: {'PASS' if abs(kd.result.magnitude - 1.0) < 0.01 else 'FAIL'}")


def test_kd_includes_wind():
    """Test K_D for wind/seismic loads (should be 1.15)."""
    print("\n" + "="*60)
    print("TEST 3: Includes Wind/Seismic Load")
    print("="*60)
    
    P_L = 30.0 * nd   # 30% long-term
    P_S = 70.0 * nd   # 70% short-term
    
    kd = load_duration_factor(
        P_L=P_L,
        P_S=P_S,
        kd_table=kd_from_load_type('includes_wind_or_seismic')
    )
    
    print(f"P_L: {P_L}")
    print(f"P_S: {P_S}")
    print(f"P_L/P_S: {P_L/P_S:.2f}")
    print(f"Load Type: includes_wind_or_seismic")
    print(f"K_D Result: {kd.result}")
    print(f"Expected: 1.15 (since P_L < P_S)")
    print(f"Status: {'PASS' if abs(kd.result.magnitude - 1.15) < 0.01 else 'FAIL'}")


def test_kd_formula_method():
    """Test K_D using formula method when P_L > P_S."""
    print("\n" + "="*60)
    print("TEST 4: Formula Method (P_L > P_S)")
    print("="*60)
    
    P_L = 70.0 * nd   # 70% long-term
    P_S = 30.0 * nd   # 30% standard-term
    
    kd = load_duration_factor(
        P_L=P_L,
        P_S=P_S,
        kd_table=kd_from_load_type('includes_live')
    )
    
    # Calculate expected value: K_D = max(1.0 - 0.50*log10(P_L/P_S), 0.65)
    import numpy as np
    ratio = P_L.magnitude / P_S.magnitude
    expected = max(1.0 - 0.50 * np.log10(ratio), 0.65)
    
    print(f"P_L: {P_L}")
    print(f"P_S: {P_S}")
    print(f"P_L/P_S: {ratio:.2f}")
    print(f"Load Type: includes_live")
    print(f"K_D Result: {kd.result}")
    print(f"Expected (formula): {expected:.3f}")
    print(f"Status: {'PASS' if abs(kd.result.magnitude - expected) < 0.01 else 'FAIL'}")


def test_kd_array_inputs():
    """Test K_D with array inputs (multiple load cases)."""
    print("\n" + "="*60)
    print("TEST 5: Array Inputs (Multiple Load Cases)")
    print("="*60)
    
    # Three load combinations
    P_L = [100.0, 40.0, 30.0] * nd
    P_S = [0.0, 60.0, 70.0] * nd
    load_types = ['dead_only', 'includes_live', 'includes_wind_or_seismic']
    
    print(f"Testing {len(load_types)} load combinations...")
    
    for i, load_type in enumerate(load_types):
        pl = P_L[i]
        ps = P_S[i]
        
        kd = load_duration_factor(
            P_L=pl,
            P_S=ps,
            kd_table=kd_from_load_type(load_type)
        )
        
        print(f"\n  Case {i+1}: {load_type}")
        print(f"    P_L={pl}, P_S={ps}")
        print(f"    K_D={kd.result:.3f}")


def test_kd_edge_cases():
    """Test K_D edge cases."""
    print("\n" + "="*60)
    print("TEST 6: Edge Cases")
    print("="*60)
    
    # Case 1: P_L = P_S (ratio = 1.0, should use table)
    print("\nCase 1: P_L = P_S (threshold)")
    P_L = 50.0 * nd
    P_S = 50.0 * nd
    
    kd = load_duration_factor(
        P_L=P_L,
        P_S=P_S,
        kd_table=kd_from_load_type('includes_live')
    )
    
    print(f"  P_L={P_L}, P_S={P_S}, P_L/P_S={P_L/P_S:.2f}")
    print(f"  K_D={kd.result:.3f} (should use table value 1.0)")
    print(f"  Status: {'PASS' if abs(kd.result.magnitude - 1.0) < 0.01 else 'FAIL'}")
    
    # Case 2: Very high P_L/P_S ratio (should still be >= 0.65)
    print("\nCase 2: Very high P_L/P_S ratio")
    P_L = 95.0 * nd
    P_S = 5.0 * nd
    
    kd = load_duration_factor(
        P_L=P_L,
        P_S=P_S,
        kd_table=kd_from_load_type('includes_live')
    )
    
    print(f"  P_L={P_L}, P_S={P_S}, P_L/P_S={P_L/P_S:.2f}")
    print(f"  K_D={kd.result:.3f} (should be >= 0.65)")
    print(f"  Status: {'PASS' if kd.result.magnitude >= 0.65 else 'FAIL'}")


def main():
    """Run all K_D tests."""
    print("\n")
    print("#" * 60)
    print("# K_D (LOAD DURATION FACTOR) TEST SUITE")
    print("#" * 60)
    
    test_kd_dead_only()
    test_kd_includes_live()
    test_kd_includes_wind()
    test_kd_formula_method()
    test_kd_array_inputs()
    test_kd_edge_cases()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
