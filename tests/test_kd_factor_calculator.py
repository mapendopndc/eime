"""
Test K_D (load duration factor) functionality using the calculator interface.

Tests should produce identical results to test_kd_factor.py
"""

from eime.units import ureg
from design.csa_o86_2025.calculators import (
    RectangularProfile,
    TimberMaterial,
    TimberSection,
    TimberDesignParameters,
    TimberLoads,
    TimberBeamDesign
)

# Unit shorthands
m = ureg.m
mm = ureg.mm
kN = ureg.kN
nd = ureg.dimensionless


def setup_calculator(P_L, P_S, load_combo_type, P_axial=10.0):
    """
    Set up a simple calculator for testing K_D.
    
    Parameters
    ----------
    P_L : Quantity
        Long-term load percentage
    P_S : Quantity
        Short-term load percentage
    load_combo_type : str
        Load combination type
    P_axial : float
        Axial load magnitude in kN (default 10.0)
    """
    # Create a simple section (size doesn't matter for K_D test)
    profile = RectangularProfile(b=130*mm, d=190*mm)
    material = TimberMaterial(grade="16c-E", species="Douglas Fir-Larch", ureg=ureg)
    section = TimberSection(profile=profile, material=material)
    
    # Create parameters
    parameters = TimberDesignParameters(
        beam_ids=["TEST-1"],
        beam_length=3.0*m,
        end_conditions="Pin - Pin",
        service_conditions="Dry-service conditions",
        lu=3.0*m,
        Wf=1.0*nd,
        SumG=0.0*nd,
        ureg=ureg
    )
    
    # Create loads with K_D inputs
    loads = TimberLoads(
        P_L=[P_L],
        P_S=[P_S],
        load_combo_types=[load_combo_type],
        ureg=ureg
    )
    
    # Set axial load
    loads.P = [P_axial * kN]
    loads.M3 = [0.0 * kN * m]
    loads.M2 = [0.0 * kN * m]
    loads.V2 = [0.0 * kN]
    loads.V3 = [0.0 * kN]
    
    # Create calculator
    design = TimberBeamDesign(
        section=section,
        loading=loads,
        parameters=parameters
    )
    
    return design, loads


def test_kd_dead_only():
    """Test K_D for dead load only (should be 0.65)."""
    print("\n" + "="*60)
    print("TEST 1: Dead Load Only (Calculator)")
    print("="*60)
    
    P_L = 100.0 * nd
    P_S = 0.0 * nd
    
    design, loads = setup_calculator(P_L, P_S, 'dead_only')
    
    # Get K_D from the loads object
    kd_formulas = loads.get_KD_formulas()
    kd_result = kd_formulas[0].result
    
    print(f"P_L: {P_L}")
    print(f"P_S: {P_S}")
    print(f"Load Type: dead_only")
    print(f"K_D Result: {kd_result}")
    print(f"Expected: 0.65")
    print(f"Status: {'PASS' if abs(kd_result.magnitude - 0.65) < 0.01 else 'FAIL'}")


def test_kd_includes_live():
    """Test K_D for live/snow loads (should be 1.0)."""
    print("\n" + "="*60)
    print("TEST 2: Includes Live/Snow Load (Calculator)")
    print("="*60)
    
    P_L = 40.0 * nd
    P_S = 60.0 * nd
    
    design, loads = setup_calculator(P_L, P_S, 'includes_live')
    
    kd_formulas = loads.get_KD_formulas()
    kd_result = kd_formulas[0].result
    
    print(f"P_L: {P_L}")
    print(f"P_S: {P_S}")
    print(f"P_L/P_S: {P_L/P_S:.2f}")
    print(f"Load Type: includes_live")
    print(f"K_D Result: {kd_result}")
    print(f"Expected: 1.0 (since P_L < P_S)")
    print(f"Status: {'PASS' if abs(kd_result.magnitude - 1.0) < 0.01 else 'FAIL'}")


def test_kd_includes_wind():
    """Test K_D for wind/seismic loads (should be 1.15)."""
    print("\n" + "="*60)
    print("TEST 3: Includes Wind/Seismic Load (Calculator)")
    print("="*60)
    
    P_L = 30.0 * nd
    P_S = 70.0 * nd
    
    design, loads = setup_calculator(P_L, P_S, 'includes_wind_or_seismic')
    
    kd_formulas = loads.get_KD_formulas()
    kd_result = kd_formulas[0].result
    
    print(f"P_L: {P_L}")
    print(f"P_S: {P_S}")
    print(f"P_L/P_S: {P_L/P_S:.2f}")
    print(f"Load Type: includes_wind_or_seismic")
    print(f"K_D Result: {kd_result}")
    print(f"Expected: 1.15 (since P_L < P_S)")
    print(f"Status: {'PASS' if abs(kd_result.magnitude - 1.15) < 0.01 else 'FAIL'}")


def test_kd_formula_method():
    """Test K_D using formula method when P_L > P_S."""
    print("\n" + "="*60)
    print("TEST 4: Formula Method (P_L > P_S) (Calculator)")
    print("="*60)
    
    P_L = 70.0 * nd
    P_S = 30.0 * nd
    
    design, loads = setup_calculator(P_L, P_S, 'includes_live')
    
    kd_formulas = loads.get_KD_formulas()
    kd_result = kd_formulas[0].result
    
    # Calculate expected value
    import numpy as np
    ratio = P_L.magnitude / P_S.magnitude
    expected = max(1.0 - 0.50 * np.log10(ratio), 0.65)
    
    print(f"P_L: {P_L}")
    print(f"P_S: {P_S}")
    print(f"P_L/P_S: {ratio:.2f}")
    print(f"Load Type: includes_live")
    print(f"K_D Result: {kd_result}")
    print(f"Expected (formula): {expected:.3f}")
    print(f"Status: {'PASS' if abs(kd_result.magnitude - expected) < 0.01 else 'FAIL'}")


def test_kd_multiple_load_cases():
    """Test K_D with multiple load combinations in one calculator."""
    print("\n" + "="*60)
    print("TEST 5: Multiple Load Cases (Calculator)")
    print("="*60)
    
    # Create a simple section
    profile = RectangularProfile(b=130*mm, d=190*mm)
    material = TimberMaterial(grade="16c-E", species="Douglas Fir-Larch", ureg=ureg)
    section = TimberSection(profile=profile, material=material)
    
    # Create parameters for 3 load combinations
    parameters = TimberDesignParameters(
        beam_ids=["TEST-1", "TEST-2", "TEST-3"],
        beam_length=3.0*m,
        end_conditions="Pin - Pin",
        service_conditions="Dry-service conditions",
        lu=3.0*m,
        Wf=1.0*nd,
        SumG=0.0*nd,
        ureg=ureg
    )
    
    # Three load combinations
    P_L_values = [100.0, 40.0, 30.0] * nd
    P_S_values = [0.0, 60.0, 70.0] * nd
    load_types = ['dead_only', 'includes_live', 'includes_wind_or_seismic']
    
    # Create loads
    loads = TimberLoads(
        P_L=P_L_values,
        P_S=P_S_values,
        load_combo_types=load_types,
        ureg=ureg
    )
    
    loads.P = [10.0*kN, 15.0*kN, 20.0*kN]
    loads.M3 = [0.0*kN*m, 0.0*kN*m, 0.0*kN*m]
    loads.M2 = [0.0*kN*m, 0.0*kN*m, 0.0*kN*m]
    loads.V2 = [0.0*kN, 0.0*kN, 0.0*kN]
    loads.V3 = [0.0*kN, 0.0*kN, 0.0*kN]
    
    # Create calculator
    design = TimberBeamDesign(
        section=section,
        loading=loads,
        parameters=parameters
    )
    
    # Get K_D values
    kd_formulas = loads.get_KD_formulas()
    
    print(f"Testing {len(load_types)} load combinations...")
    
    for i, load_type in enumerate(load_types):
        pl = P_L_values[i]
        ps = P_S_values[i]
        kd = kd_formulas[i].result
        
        print(f"\n  Case {i+1}: {load_type}")
        print(f"    P_L={pl}, P_S={ps}")
        print(f"    K_D={kd:.3f}")


def test_kd_edge_cases():
    """Test K_D edge cases."""
    print("\n" + "="*60)
    print("TEST 6: Edge Cases (Calculator)")
    print("="*60)
    
    # Case 1: P_L = P_S
    print("\nCase 1: P_L = P_S (threshold)")
    P_L = 50.0 * nd
    P_S = 50.0 * nd
    
    design, loads = setup_calculator(P_L, P_S, 'includes_live')
    kd_formulas = loads.get_KD_formulas()
    kd_result = kd_formulas[0].result
    
    print(f"  P_L={P_L}, P_S={P_S}, P_L/P_S={P_L/P_S:.2f}")
    print(f"  K_D={kd_result:.3f} (should use table value 1.0)")
    print(f"  Status: {'PASS' if abs(kd_result.magnitude - 1.0) < 0.01 else 'FAIL'}")
    
    # Case 2: Very high P_L/P_S ratio
    print("\nCase 2: Very high P_L/P_S ratio")
    P_L = 95.0 * nd
    P_S = 5.0 * nd
    
    design, loads = setup_calculator(P_L, P_S, 'includes_live')
    kd_formulas = loads.get_KD_formulas()
    kd_result = kd_formulas[0].result
    
    print(f"  P_L={P_L}, P_S={P_S}, P_L/P_S={P_L/P_S:.2f}")
    print(f"  K_D={kd_result:.3f} (should be >= 0.65)")
    print(f"  Status: {'PASS' if kd_result.magnitude >= 0.65 else 'FAIL'}")


def main():
    """Run all K_D tests using calculator interface."""
    print("\n")
    print("#" * 60)
    print("# K_D (LOAD DURATION FACTOR) TEST SUITE - CALCULATOR")
    print("#" * 60)
    
    test_kd_dead_only()
    test_kd_includes_live()
    test_kd_includes_wind()
    test_kd_formula_method()
    test_kd_multiple_load_cases()
    test_kd_edge_cases()
    
    print("\n" + "="*60)
    print("ALL CALCULATOR TESTS COMPLETED")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
