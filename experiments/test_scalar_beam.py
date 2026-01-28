"""
Test scalar (single value) beam calculation to check for UnitStrippedWarning.
"""

import warnings

from pint import UnitRegistry
from pint.errors import UnitStrippedWarning

from design.csa_o86_2025.calculators import TimberBeamCalculator
from design.csa_o86_2025.tables import specified_strengths, service_condition_factors


ureg = UnitRegistry()

# Unit shorthands
mm = ureg.mm
kN = ureg.kN
kNm = ureg.kN * ureg.m
MPa = ureg.MPa
nd = ureg.dimensionless


def main():
    # Enable strict warning filter - convert warnings to errors
    warnings.filterwarnings("error", category=UnitStrippedWarning)
    
    # Beam geometry
    b = 130 * mm
    d = 456 * mm
    L = 6000 * mm
    
    # Get material properties
    species = "Douglas Fir-Larch"
    grade = "20f-E"
    service_condition = "Dry-service conditions"
    
    strengths_table = specified_strengths()
    material_props = strengths_table.data.loc[grade, species]
    
    f_b = material_props["f_b_pos"] * MPa
    f_v = material_props["f_v"] * MPa
    
    service_table = service_condition_factors()
    K_Sb = service_table.data.loc["K_Sb", service_condition] * nd
    K_Sv = service_table.data.loc["K_Sv", service_condition] * nd
    
    # Scalar factored loads
    M_f = 25.0 * kNm
    V_f = 10.0 * kN
    
    # Load duration - mixed long and short term
    P_L_percent = 60.0 * nd
    P_S_percent = 40.0 * nd
    
    # Other factors
    phi_b = 0.9 * nd
    phi_v = 0.9 * nd
    K_H = 1.0 * nd
    K_T = 1.0 * nd
    K_x = 1.0 * nd
    
    print("Testing SCALAR beam calculation with strict UnitStrippedWarning filter...")
    print("=" * 72)
    
    calculator = TimberBeamCalculator()
    
    try:
        results = calculator.design(
            b=b,
            d=d,
            L=L,
            f_b=f_b,
            f_v=f_v,
            M_f=M_f,
            V_f=V_f,
            P_L_percent=P_L_percent,
            P_S_percent=P_S_percent,
            K_H=K_H,
            K_Sb=K_Sb,
            K_Sv=K_Sv,
            K_T=K_T,
            K_x=K_x,
            phi_b=phi_b,
            phi_v=phi_v,
        )
        
        print("✓ SUCCESS - No UnitStrippedWarning raised")
        print(f"Results shape: {results.shape}")
        print(f"Results type: {type(results)}")
        
    except UnitStrippedWarning as e:
        print("✗ FAILED - UnitStrippedWarning was raised:")
        print(f"  {e}")
        raise


if __name__ == "__main__":
    main()
