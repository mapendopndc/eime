"""
NBCC Load Combination Vectorization Demo

Uses NBCC load combinations to generate factored loads and runs the
TimberBeamCalculator in a vectorized workflow.
"""

from __future__ import annotations

import warnings

from pint import UnitRegistry
from pint.errors import UnitStrippedWarning

from design.csa_o86_2025.calculators import TimberBeamCalculator
from design.csa_o86_2025.tables import specified_strengths, service_condition_factors
from load.nbcc2020 import nbcc_uls_combinations


ureg = UnitRegistry()

# Unit shorthands
m = ureg.m
mm = ureg.mm
kPa = ureg.kPa
MPa = ureg.MPa
nd = ureg.dimensionless


def build_base_inputs():
    """Return shared beam/material inputs."""
    span_m = 6.0 * m
    spacing_m = 0.4 * m
    b = 130 * mm
    d = 456 * mm
    L = span_m.to(mm)

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

    phi_b = 0.9 * nd
    phi_v = 0.9 * nd
    K_H = 1.0 * nd
    K_T = 1.0 * nd
    K_x = 1.0 * nd

    return {
        "span_m": span_m,
        "spacing_m": spacing_m,
        "b": b,
        "d": d,
        "L": L,
        "f_b": f_b,
        "f_v": f_v,
        "K_Sb": K_Sb,
        "K_Sv": K_Sv,
        "phi_b": phi_b,
        "phi_v": phi_v,
        "K_H": K_H,
        "K_T": K_T,
        "K_x": K_x,
    }


def compute_beam_effects(span_m, spacing_m, factored_pressure):
    """Compute factored moment and shear for a UDL."""
    w_factored = factored_pressure * spacing_m
    M_f = (w_factored * span_m**2) / 8
    V_f = (w_factored * span_m) / 2
    return M_f, V_f


def main():
    warnings.filterwarnings("error", category=UnitStrippedWarning)

    base_inputs = build_base_inputs()

    nominal_loads = {
        "D": 1.2 * kPa,
        "L": 1.9 * kPa,
        "S": 1.5 * kPa,
    }

    combos = nbcc_uls_combinations(
        nominal_loads,
        include_wind=False,
        include_seismic=False,
    )

    M_f, V_f = compute_beam_effects(
        base_inputs["span_m"],
        base_inputs["spacing_m"],
        combos.total,
    )

    calculator = TimberBeamCalculator()
    results = calculator.design(
        b=base_inputs["b"],
        d=base_inputs["d"],
        L=base_inputs["L"],
        f_b=base_inputs["f_b"],
        f_v=base_inputs["f_v"],
        M_f=M_f,
        V_f=V_f,
        P_L_percent=combos.duration_long_percent,
        P_S_percent=combos.duration_short_percent,
        K_H=base_inputs["K_H"],
        K_Sb=base_inputs["K_Sb"],
        K_Sv=base_inputs["K_Sv"],
        K_T=base_inputs["K_T"],
        K_x=base_inputs["K_x"],
        phi_b=base_inputs["phi_b"],
        phi_v=base_inputs["phi_v"],
    )

    print("=" * 72)
    print("NBCC LOAD COMBO VECTOR DEMO")
    print("=" * 72)
    print(f"Combinations: {len(combos.names)}")
    print(f"Factored load shape: {combos.total.shape}")
    print(f"Results shape: {results.shape}")
    print()
    
    print("Load Combinations:")
    print("-" * 72)
    for name, total in zip(combos.names, combos.total):
        print(f"{name:>20} -> {total.to(kPa).magnitude:.3f} kPa")
    
    print("\n" + "=" * 72)
    print("SUMMARY TABLE (units stripped - for display only)")
    print("=" * 72)
    print(results)
    
    print("\n" + "=" * 72)
    print("ACCESSING RESULTS WITH UNITS PRESERVED")
    print("=" * 72)
    
    # Access calculator's procedure directly to get results with units
    procedure = calculator.procedures[-1]  # Get the most recent procedure
    
    print(f"Available results: {list(procedure.results.keys())}")
    print()
    
    # Show a few key results with units
    if 'M_{r,a}' in procedure.results:
        Mr = procedure.results['M_{r,a}']
        print(f"Factored Moment Resistance (M_r):")
        print(f"  Type: {type(Mr)}")
        print(f"  Units: {Mr.units}")
        print(f"  Values: {Mr.to('kN*m')}")
    
    print()
    if 'V_r' in procedure.results:
        Vr = procedure.results['V_r']
        print(f"Factored Shear Resistance (V_r):")
        print(f"  Type: {type(Vr)}")
        print(f"  Units: {Vr.units}")
        print(f"  Values: {Vr.to('kN')}")
    
    # Demonstrate unit-safe arithmetic
    print()
    print("=" * 72)
    print("UNIT-SAFE OPERATIONS ON RESULTS")
    print("=" * 72)
    
    if 'M_{r,a}' in procedure.results and 'V_r' in procedure.results:
        Mr = procedure.results['M_{r,a}']
        Vr = procedure.results['V_r']
        
        # This is safe - units are preserved
        print(f"Maximum moment resistance: {Mr.to('kN*m').max()}")
        print(f"Minimum moment resistance: {Mr.to('kN*m').min()}")
        print(f"Maximum shear resistance: {Vr.to('kN').max()}")
        
        # This would catch unit errors
        # ratio = Mr / Vr  # Would work, giving units of length
        print(f"\nRatio M_r/V_r (has length units): {(Mr/Vr).to('m')}")
        
        print("\n" + "-" * 72)
        print("COMPARISON: What if we used the summary DataFrame?")
        print("-" * 72)
        
        # From summary table (no units)
        Mr_no_units = results['M_{r,a}'].max()
        Vr_no_units = results['V_r'].max()
        
        print(f"Maximum M_r from summary: {Mr_no_units:.2e} (unknown units!)")
        print(f"Maximum V_r from summary: {Vr_no_units:.2e} (unknown units!)")
        print(f"Ratio (no unit checking): {Mr_no_units / Vr_no_units:.2e} (unsafe!)")
        print("\n⚠️  Without units, you must manually track what units these are!")
        print("    The summary table is for DISPLAY ONLY, not calculations.")


if __name__ == "__main__":
    main()
