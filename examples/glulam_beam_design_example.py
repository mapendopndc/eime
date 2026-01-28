"""
Glulam Beam Design Example

This example demonstrates the design of a glulam beam
using the TimberBeamDesign class to check bending, shear, and compression capacity
per CSA O86:25.
"""
from pathlib import Path
from design.csa_o86_2025.calculators import (
    RectangularProfile,
    TimberMaterial,
    TimberSection,
    TimberDesignParameters,
    TimberLoads,
    TimberLoadingParameters,
    TimberBeamDesign
)
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
    Design a glulam beam with bending, shear, and compression checks.
    
    This example demonstrates a simply supported beam with distributed loads.
    """
    
    # ==========================================
    # USER INPUTS - Modify these as needed
    # ==========================================
    
    # Beam geometry
    span_length = 8.0 * m  # Beam span
    
    # Section properties: 175 x 456 mm glulam beam
    b = 175 * mm  # Width
    d = 456 * mm  # Depth
    
    # Material specification
    species = "Douglas Fir-Larch"
    grade = "20f-E"
    
    # Service conditions
    service_condition = "Dry-service conditions"
    
    # End conditions
    end_conditions = "Pin - Pin"  # Simply supported
    
    # Nominal distributed loads (unfactored)
    # Dead load: self-weight + floor system
    dead_load_kPa = 2.5 * kPa
    # Live load: floor live load
    live_load_kPa = 4.8 * kPa
    # Snow load: roof contribution
    snow_load_kPa = 2.0 * kPa
    
    # Tributary width for beam
    tributary_width = 3.6 * m
    
    # Convert to line loads (kN/m)
    w_dead = dead_load_kPa * tributary_width
    w_live = live_load_kPa * tributary_width
    w_snow = snow_load_kPa * tributary_width
    
    # Calculate maximum moment and shear for simply supported beam
    # M_max = w*L^2/8 at midspan
    # V_max = w*L/2 at supports
    
    # ==========================================
    # NBCC 2020 LOAD COMBINATIONS
    # ==========================================
    
    # Define nominal loads (using moments and shears)
    nominal_moments = {
        "D": w_dead * span_length**2 / 8,
        "L": w_live * span_length**2 / 8,
        "S": w_snow * span_length**2 / 8,
    }
    
    nominal_shears = {
        "D": w_dead * span_length / 2,
        "L": w_live * span_length / 2,
        "S": w_snow * span_length / 2,
    }
    
    # Small axial compression from lateral load transfer (example)
    nominal_axial = {
        "D": 5.0 * kN,
        "L": 3.0 * kN,
        "S": 2.0 * kN,
    }
    
    # Generate ULS load combinations per NBCC 2020
    moment_combos = nbcc_uls_combinations(nominal_moments)
    shear_combos = nbcc_uls_combinations(nominal_shears)
    axial_combos = nbcc_uls_combinations(nominal_axial)
    
    # Extract load combination data
    combo_names = moment_combos.names
    factored_moments = moment_combos.total
    factored_shears = shear_combos.total
    factored_axial = axial_combos.total
    
    # Create beam IDs for each load combination
    beam_ids = [f"BM-1-{combo}" for combo in combo_names]
    
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
    
    # Lateral support conditions
    # Assume compression flange is continuously supported by decking
    # Tension flange is unbraced over full span
    lu_strong = span_length  # Unbraced length for bending
    lu_weak = span_length    # Unbraced length (not critical for beams)
    
    # Total factored load on beam (for shear coefficient calculation)
    # Using worst case total load from all combinations
    total_factored_loads = []
    for i in range(len(factored_moments)):
        # Total load = factored distributed load * span
        # Back-calculate from moment: M = wL^2/8 => w = 8M/L^2
        w_total = 8 * factored_moments[i] / span_length**2
        total_load = w_total * span_length
        total_factored_loads.append(total_load.to(ureg.N))
    
    Wf = max(total_factored_loads)  # Use worst case
    
    # Sum of G factors for shear calculation (CSA O86 7.5.7.6)
    # For simply supported beam with uniform load: G = 5*w*L^4/(384*E*I)
    # Sum_G typically represents cumulative shear deformation
    # For this example, use a simplified approach
    I = profile.MomentofInertia()  # Will be calculated after profile is created
    E = material.E  # Will be from material
    # Placeholder calculation - in practice this depends on load distribution
    SumG = 1.0 * ureg.N**5 * ureg.mm  # Simplified placeholder

    # Create design parameters
    parameters = TimberDesignParameters(
        beam_ids=beam_ids,
        beam_length=span_length,
        end_conditions=end_conditions,
        service_conditions=service_condition,
        lu_strong=lu_strong,
        lu_weak=lu_weak,
        Wf=Wf,
        SumG=SumG,
        ureg=ureg
    )
    
    # Create loading parameters for K_D calculation
    loading_params = TimberLoadingParameters(
        P_L_M=moment_combos.duration_long_percent,
        P_S_M=moment_combos.duration_short_percent,
        P_L_V=shear_combos.duration_long_percent,
        P_S_V=shear_combos.duration_short_percent,
        P_L_P=axial_combos.duration_long_percent,
        P_S_P=axial_combos.duration_short_percent,
        load_combo_types=moment_combos.load_combo_types,
        ureg=ureg
    )
    
    # ==========================================
    # DEFINE LOADS
    # ==========================================
    
    # Create loads object
    loads = TimberLoads()
    
    # Set bending moments (strong axis - about major axis)
    loads.M3 = factored_moments
    
    # Set shear forces (weak axis direction)
    loads.V2 = factored_shears
    
    # Set axial compression
    loads.P = factored_axial
    
    # No weak axis bending or strong axis shear for this example
    loads.M2 = [0.0 * kN * m] * num_combos
    loads.V3 = [0.0 * kN] * num_combos
    
    # ==========================================
    # CREATE DESIGN CALCULATOR
    # ==========================================
    
    # Create timber beam design calculator
    design = TimberBeamDesign(
        section=section,
        loading=loads,
        parameters=parameters,
        loading_params=loading_params
    )
    
    # ==========================================
    # DISPLAY INPUT SUMMARY
    # ==========================================
    
    print("\n" + "="*70)
    print("GLULAM BEAM DESIGN")
    print("="*70)
    
    print(f"\nSection: {b.to(mm).magnitude:.0f} x {d.to(mm).magnitude:.0f} mm")
    print(f"Material: {grade} {species}")
    print(f"Span: {span_length.to(m).magnitude:.1f} m")
    print(f"End Conditions: {end_conditions}")
    print(f"Tributary Width: {tributary_width.to(m).magnitude:.1f} m")
    
    print(f"\nUnbraced Length (Bending): {lu_strong.to(m).magnitude:.1f} m")
    
    print("\nNominal Distributed Loads:")
    print(f"  Dead Load: {dead_load_kPa.to(kPa).magnitude:.2f} kPa ({w_dead.to(kN/m).magnitude:.2f} kN/m)")
    print(f"  Live Load: {live_load_kPa.to(kPa).magnitude:.2f} kPa ({w_live.to(kN/m).magnitude:.2f} kN/m)")
    print(f"  Snow Load: {snow_load_kPa.to(kPa).magnitude:.2f} kPa ({w_snow.to(kN/m).magnitude:.2f} kN/m)")
    
    print(f"\nNBCC 2020 Load Combinations: {num_combos} cases")
    
    # ==========================================
    # PERFORM DESIGN CHECKS
    # ==========================================
    
    print("\n" + "="*70)
    print("RUNNING DESIGN CHECKS...")
    print("="*70)
    
    # 1. Bending resistance check
    print("\n1. Bending Resistance Check...")
    bending_check = design.BendingResistance(axis='strong', sign='positive')
    
    # 2. Shear resistance check
    print("2. Shear Resistance Check...")
    shear_check = design.ShearResistance(axis='weak')
    
    # 3. Compression resistance check (for axial load)
    print("3. Compression Resistance Check...")
    compression_check = design.CompressionResistance(axis='both')
    
    # ==========================================
    # DISPLAY RESULTS - BENDING
    # ==========================================
    
    print("\n" + "="*70)
    print("BENDING CHECK RESULTS")
    print("="*70)
    
    # Get bending resistance from results
    if 'M_r' in bending_check.results:
        M_r_values = bending_check.results['M_r']
        if hasattr(M_r_values.magnitude, '__len__'):
            M_r_first = M_r_values[0].to(kN * m)
        else:
            M_r_first = M_r_values.to(kN * m)
        print(f"\nBending Resistance (Mr): {M_r_first.magnitude:.2f} kN·m")
    
    # Get lateral stability factor
    if 'KL' in bending_check.results:
        KL = bending_check.results['KL']
        if hasattr(KL, 'magnitude') and hasattr(KL.magnitude, '__len__'):
            KL_first = KL[0]
        elif hasattr(KL, '__len__'):
            KL_first = KL[0]
        else:
            KL_first = KL
        print(f"Lateral Stability Factor (KL): {KL_first:.3f}")
    
    bending_util = bending_check.get_worst_utilization()
    worst_bending = bending_util.max()
    print(f"\nWorst Utilization: {worst_bending:.3f} ({worst_bending*100:.1f}%)")
    bending_status = 'PASS' if worst_bending <= 1.0 else 'FAIL'
    print(f"Status: {bending_status}")
    
    # ==========================================
    # DISPLAY RESULTS - SHEAR
    # ==========================================
    
    print("\n" + "="*70)
    print("SHEAR CHECK RESULTS")
    print("="*70)
    
    # Get shear resistance from results
    if 'V_r' in shear_check.results:
        V_r_values = shear_check.results['V_r']
        if hasattr(V_r_values.magnitude, '__len__'):
            V_r_first = V_r_values[0].to(kN)
        else:
            V_r_first = V_r_values.to(kN)
        print(f"\nShear Resistance (Vr): {V_r_first.magnitude:.2f} kN")
    
    shear_util = shear_check.get_worst_utilization()
    worst_shear = shear_util.max()
    print(f"\nWorst Utilization: {worst_shear:.3f} ({worst_shear*100:.1f}%)")
    shear_status = 'PASS' if worst_shear <= 1.0 else 'FAIL'
    print(f"Status: {shear_status}")
    
    # ==========================================
    # DISPLAY RESULTS - COMPRESSION
    # ==========================================
    
    print("\n" + "="*70)
    print("COMPRESSION CHECK RESULTS")
    print("="*70)
    
    # Get compression resistance from results
    if 'P_r' in compression_check.results:
        P_r_values = compression_check.results['P_r']
        if hasattr(P_r_values.magnitude, '__len__'):
            P_r_first = P_r_values[0].to(kN)
        else:
            P_r_first = P_r_values.to(kN)
        print(f"\nCompression Resistance (Pr): {P_r_first.magnitude:.2f} kN")
    
    compression_util = compression_check.get_worst_utilization()
    worst_compression = compression_util.max()
    print(f"\nWorst Utilization: {worst_compression:.3f} ({worst_compression*100:.1f}%)")
    compression_status = 'PASS' if worst_compression <= 1.0 else 'FAIL'
    print(f"Status: {compression_status}")
    
    # ==========================================
    # DETAILED RESULTS BY LOAD COMBINATION
    # ==========================================
    
    print("\n" + "="*70)
    print("DETAILED RESULTS BY LOAD COMBINATION")
    print("="*70)
    
    # Get resistance values
    M_r_vals = bending_check.results.get('M_r', None)
    V_r_vals = shear_check.results.get('V_r', None)
    P_r_vals = compression_check.results.get('P_r', None)
    
    print(f"\n{'Combo':<12} {'M_f':<10} {'M_r':<10} {'V_f':<10} {'V_r':<10} {'P_f':<10} {'P_r':<10} {'Max Util':<10} {'Status':<8}")
    print(f"{'':12} {'(kN·m)':<10} {'(kN·m)':<10} {'(kN)':<10} {'(kN)':<10} {'(kN)':<10} {'(kN)':<10} {'':10} {'':8}")
    print("-" * 100)
    
    for i, combo in enumerate(combo_names):
        # Get factored loads
        M_f = factored_moments[i].to(kN * m).magnitude
        V_f = factored_shears[i].to(kN).magnitude
        P_f = factored_axial[i].to(kN).magnitude
        
        # Get resistances (handle both scalar and array)
        if M_r_vals is not None:
            M_r = M_r_vals[i].to(kN * m).magnitude if hasattr(M_r_vals.magnitude, '__len__') else M_r_vals.to(kN * m).magnitude
        else:
            M_r = 0.0
            
        if V_r_vals is not None:
            V_r = V_r_vals[i].to(kN).magnitude if hasattr(V_r_vals.magnitude, '__len__') else V_r_vals.to(kN).magnitude
        else:
            V_r = 0.0
            
        if P_r_vals is not None:
            P_r = P_r_vals[i].to(kN).magnitude if hasattr(P_r_vals.magnitude, '__len__') else P_r_vals.to(kN).magnitude
        else:
            P_r = 0.0
        
        # Get utilizations
        util_b = bending_util.iloc[i] if len(bending_util) > i else 0
        util_v = shear_util.iloc[i] if len(shear_util) > i else 0
        util_p = compression_util.iloc[i] if len(compression_util) > i else 0
        
        # Maximum utilization for this combination
        max_util = max(util_b, util_v, util_p)
        combo_status = 'PASS' if max_util <= 1.0 else 'FAIL'
        
        print(f"{combo:<12} {M_f:<10.2f} {M_r:<10.2f} {V_f:<10.2f} {V_r:<10.2f} {P_f:<10.2f} {P_r:<10.2f} {max_util:<10.3f} {combo_status:<8}")
    
    # ==========================================
    # OVERALL SUMMARY
    # ==========================================
    
    print("\n" + "="*70)
    print("DESIGN SUMMARY")
    print("="*70)
    
    print(f"\nBeam: {b.to(mm).magnitude:.0f} x {d.to(mm).magnitude:.0f} mm {grade} {species}")
    print(f"Span: {span_length.to(m).magnitude:.1f} m")
    print(f"Load Combinations Analyzed: {num_combos}")
    
    print(f"\nCheck Results:")
    print(f"  Bending:     {worst_bending:.1%} - {bending_status}")
    print(f"  Shear:       {worst_shear:.1%} - {shear_status}")
    print(f"  Compression: {worst_compression:.1%} - {compression_status}")
    
    # Determine overall status
    overall_util = max(worst_bending, worst_shear, worst_compression)
    overall_status = 'PASS' if overall_util <= 1.0 else 'FAIL'
    
    print(f"\nOverall Maximum Utilization: {overall_util:.1%}")
    print(f"Overall Design Status: **{overall_status}**")
    
    if overall_util <= 1.0:
        print(f"\nThe beam is ADEQUATE for all {num_combos} NBCC load combinations.")
    else:
        print(f"\nThe beam is NOT ADEQUATE. Consider increasing section size or reducing span.")
    
    print("\n" + "="*70 + "\n")
    
    # ==========================================
    # GENERATE LATEX DOCUMENTATION
    # ==========================================
    
    # Generate LaTeX for each check (using worst case - combo index 1)
    latex_bending = bending_check.generate_latex(index=1)
    latex_shear = shear_check.generate_latex(index=1)
    latex_compression = compression_check.generate_latex(index=1)
    
    # Combine all checks into one document
    combined_latex = f"""# Glulam Beam Design Calculations

## Beam Information
- Section: {b.to(mm).magnitude:.0f} x {d.to(mm).magnitude:.0f} mm
- Material: {grade} {species}
- Span: {span_length.to(m).magnitude:.1f} m

## Load Combination: {combo_names[1]}

---

{latex_bending}

---

{latex_shear}

---

{latex_compression}
"""
    
    # Save to markdown file in examples directory
    output_path = Path(__file__).parent / "glulam_beam_design_calcs.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(combined_latex)
    
    print(f"Calculation documentation saved to: {output_path}\n")


if __name__ == "__main__":
    main()
