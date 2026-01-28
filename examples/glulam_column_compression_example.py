"""
Glulam Column Compression Example

This example demonstrates the design of a glulam column
using the TimberBeamDesign class to check compression capacity
per CSA O86:25 Section 7.5.8.
"""

from pint import UnitRegistry
import pandas as pd

from design.csa_o86_2025.calculators import (
    RectangularProfile,
    TimberMaterial,
    TimberSection,
    TimberDesignParameters,
    TimberLoads,
    TimberBeamDesign
)
from design.csa_o86_2025 import formulas as TimberDesign
from load.nbcc2020 import nbcc_uls_combinations
from eime.units import ureg

# Unit shorthands
m = ureg.m
mm = ureg.mm
kPa = ureg.kPa
MPa = ureg.MPa
kN = ureg.kN
nd = ureg.dimensionless


def main():
    """
    Design a glulam column with compression checks.
    
    This example focuses on axial compression capacity using the 
    TimberBeamDesign calculator interface.
    """
    
    # ==========================================
    # USER INPUTS - Modify these as needed
    # ==========================================
    
    # Column geometry
    height_m = 7.0 * m  # Column height
    
    # Section properties: 130 x 190 mm glulam column
    b = 130 * mm
    d = 190 * mm
    
    # Material specification
    species = "Douglas Fir-Larch"
    grade = "16c-E"
    
    # Service conditions
    service_condition = "Dry-service conditions"
    
    # End conditions for buckling
    end_conditions = "Pin - Pin"  # Both ends pinned
    
    # Nominal axial loads (unfactored)
    dead_axial_kN = 25.0 * kN   # Dead load
    live_axial_kN = 17.5 * kN   # Live load
    snow_axial_kN = 23.0 * kN   # Snow load
    
    # ==========================================
    # NBCC 2020 LOAD COMBINATIONS
    # ==========================================
    
    # Define nominal loads
    nominal_axial_loads = {
        "D": dead_axial_kN,
        "L": live_axial_kN,
        "S": snow_axial_kN,
    }
    
    # Generate ULS load combinations per NBCC 2020
    load_combos = nbcc_uls_combinations(nominal_axial_loads)
    
    # Extract load combination data
    combo_names = load_combos.names
    factored_loads = load_combos.total
    
    # Create beam IDs for each load combination
    beam_ids = [f"COL-1-{combo}" for combo in combo_names]
    
    num_combos = len(beam_ids)
    
    # ==========================================
    # CREATE PROFILE AND MATERIAL
    # ==========================================
    
    # Create rectangular profile
    profile = RectangularProfile(b=b, d=d)
    
    # Create material from tables
    material = TimberMaterial(grade=grade, species=species, ureg=ureg)
    
    # Create section
    section = TimberSection(profile=profile, material=material)
    
    # ==========================================
    # DESIGN PARAMETERS
    # ==========================================
    
    # Unsupported lengths for biaxial compression check
    # Column is braced in weak direction at 5.1m from base
    # Strong axis (about 190mm depth): unbraced length = 7.0m (full height, unbraced)
    # Weak axis (about 130mm width): unbraced length = 5.1m (braced)
    lu_strong = height_m  # Strong axis unbraced length (full height, unbraced)
    lu_weak = 5.1 * m     # Weak axis unbraced length (braced)
    
    # Width factor (for compression, typically 1.0)
    Wf = 1.0 * nd
    
    # Sum of G for load duration (not critical for compression-only)
    SumG = 0.0 * nd
    
    # Create design parameters with biaxial compression support
    parameters = TimberDesignParameters(
        beam_ids=beam_ids,
        beam_length=height_m,
        end_conditions=end_conditions,
        service_conditions=service_condition,
        lu_strong=lu_strong,
        lu_weak=lu_weak,
        Wf=Wf,
        SumG=SumG,
        ureg=ureg
    )
    
    # ==========================================
    # DEFINE LOADS
    # ==========================================
    
    # Calculate load duration factor (K_D) using simplified method
    # Per CSA O86:25 Table 5.3.2.2:
    #   - Dead only: K_D = 0.65
    #   - Includes live: K_D = 1.0
    #   - Includes wind or seismic: K_D = 1.15
    import numpy as np
    
    kd_values = []
    for combo_type in load_combos.load_combo_types:
        if combo_type == "dead_only":
            kd_values.append(0.65)
        elif combo_type == "includes_live":
            kd_values.append(1.0)
        elif combo_type == "includes_wind_or_seismic":
            kd_values.append(1.15)
        else:
            kd_values.append(1.0)  # Default to standard duration
    
    KD = np.array(kd_values) * nd
    
    # Create loads object with KD factor
    loads = TimberLoads(KD=KD)
    
    # Set compression loads from NBCC combinations
    loads.P = factored_loads
    
    # No moments or shear for this column example
    loads.M3 = [0.0 * kN * m] * num_combos
    loads.M2 = [0.0 * kN * m] * num_combos
    loads.V2 = [0.0 * kN] * num_combos
    loads.V3 = [0.0 * kN] * num_combos
    
    # ==========================================
    # CREATE DESIGN CALCULATOR
    # ==========================================
    
    # Create timber beam design calculator
    # (works for both beams and columns)
    design = TimberBeamDesign(
        section=section,
        loading=loads,
        parameters=parameters
    )
    
    # ==========================================
    # RUN COMPRESSION CHECKS
    # ==========================================
    
    print("\n" + "="*60)
    print("GLULAM COLUMN COMPRESSION DESIGN")
    print("="*60)
    
    print(f"\nSection: {b.to(mm).magnitude:.0f} x {d.to(mm).magnitude:.0f} mm")
    print(f"Material: {grade} {species}")
    print(f"Height: {height_m.to(m).magnitude:.1f} m")
    print(f"End Conditions: {end_conditions}")
    
    print(f"\nUnbraced Lengths:")
    print(f"  Strong Axis (about {d.to(mm).magnitude:.0f}mm): {lu_strong.to(m).magnitude:.1f} m")
    print(f"  Weak Axis (about {b.to(mm).magnitude:.0f}mm): {lu_weak.to(m).magnitude:.1f} m")
    
    print("\nNominal Loads:")
    print(f"  Dead Load: {dead_axial_kN.to(kN).magnitude:.1f} kN")
    print(f"  Live Load: {live_axial_kN.to(kN).magnitude:.1f} kN")
    print(f"  Snow Load: {snow_axial_kN.to(kN).magnitude:.1f} kN")
    
    print(f"\nNBCC 2020 Load Combinations: {num_combos} cases")
    print("\nLoad Combination Summary:")
    for i, combo in enumerate(combo_names):
        print(f"  {combo}: {factored_loads[i].to(kN).magnitude:.1f} kN")
    
    # ==========================================
    # PERFORM COMPRESSION CHECKS (BIAXIAL)
    # ==========================================
    
    print("\n" + "="*60)
    print("RUNNING COMPRESSION CHECKS...")
    print("="*60)
    
    # Run biaxial compression check
    compression_check = design.CompressionResistance(axis='both')
    
    # ==========================================
    # DISPLAY RESULTS
    # ==========================================
    
    print("\n" + "="*60)
    print("COMPRESSION CHECK RESULTS")
    print("="*60)
    
    # Get compression resistance from results
    P_r_values = None
    if 'P_r' in compression_check.results:
        P_r_values = compression_check.results['P_r']
        # Handle scalar quantities (pint Quantity with scalar magnitude)
        if hasattr(P_r_values.magnitude, '__len__'):
            P_r_first = P_r_values[0].to(kN)
        else:
            P_r_first = P_r_values.to(kN)
        print(f"\nCompression Resistance (Pr): {P_r_first.magnitude:.2f} kN")
    
    # Get slenderness information
    if 'CC' in compression_check.results:
        CC = compression_check.results['CC']
        if hasattr(CC, 'magnitude') and hasattr(CC.magnitude, '__len__'):
            CC_first = CC[0]
        elif hasattr(CC, '__len__'):
            CC_first = CC[0]
        else:
            CC_first = CC
        print(f"Slenderness Ratio (CC): {CC_first:.2f}")
    
    if 'KC' in compression_check.results:
        KC = compression_check.results['KC']
        if hasattr(KC, 'magnitude') and hasattr(KC.magnitude, '__len__'):
            KC_first = KC[0]
        elif hasattr(KC, '__len__'):
            KC_first = KC[0]
        else:
            KC_first = KC
        print(f"Slenderness Factor (Kc): {KC_first:.3f}")
    
    print(f"\nGoverning Axis: {compression_check.name}")
    
    # Get worst utilization from the core library
    worst_util_series = compression_check.get_worst_utilization()
    worst_util = worst_util_series.max()
    
    print(f"\nWorst Utilization: {worst_util:.3f} ({worst_util*100:.1f}%)")
    
    # Determine status
    status = 'PASS' if worst_util <= 1.0 else 'FAIL'
    print(f"Status: {status}")
    
    # Display detailed results for each load combination
    print("\n" + "="*60)
    print("DETAILED RESULTS BY LOAD COMBINATION")
    print("="*60)
    print(f"\n{'Combination':<15} {'P_f (kN)':<12} {'P_r (kN)':<12} {'Utilization':<12} {'Status':<8}")
    print("-" * 60)
    
    # Get utilization values from the core library
    utilization_values = compression_check.get_worst_utilization()
    
    # Get resistance values from results
    if P_r_values is not None:
        for i, combo in enumerate(combo_names):
            P_f = factored_loads[i].to(kN).magnitude
            # Handle both scalar and array P_r values
            if hasattr(P_r_values.magnitude, '__len__'):
                P_r_val = P_r_values[i].to(kN).magnitude
            else:
                P_r_val = P_r_values.to(kN).magnitude
            
            # Use utilization from the core library
            util = utilization_values.iloc[i] if len(utilization_values) > i else 0
            combo_status = 'PASS' if util <= 1.0 else 'FAIL'
            
            print(f"{combo:<15} {P_f:<12.2f} {P_r_val:<12.2f} {util:<12.3f} {combo_status:<8}")
    else:
        print("No resistance values available in results.")
    
    # Summary
    print("\n" + "="*60)
    print("DESIGN SUMMARY")
    print("="*60)
    
    print(f"\nColumn: {b.to(mm).magnitude:.0f} x {d.to(mm).magnitude:.0f} mm {grade} {species}")
    print(f"Height: {height_m.to(m).magnitude:.1f} m")
    print(f"Governing Axis: {compression_check.name}")
    print(f"Load Combinations Analyzed: {num_combos}")
    print(f"Maximum Utilization: {worst_util:.1%}")
    print(f"Design Status: **{status}**")
    
    if worst_util <= 1.0:
        print(f"\nThe column is ADEQUATE for all {num_combos} NBCC load combinations.")
    else:
        print(f"\nThe column is NOT ADEQUATE. Consider increasing section size or reducing unbraced length.")
    
    print("\n" + "="*60 + "\n")
    
    # ==========================================
    # GENERATE LATEX DOCUMENTATION
    # ==========================================
    
    # Generate LaTeX for the compression resistance calculation
    latex_output = compression_check.generate_latex(index=1)
    
    # Save to markdown file
    with open("glulam_column_compression_calcs.md", "w", encoding="utf-8") as f:
        f.write(latex_output)
    
    print("Calculation documentation saved to: glulam_column_compression_calcs.md\n")


if __name__ == "__main__":
    main()
