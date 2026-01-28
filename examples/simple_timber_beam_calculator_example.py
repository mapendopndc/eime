"""
Simple Timber Beam Calculator Example

This example demonstrates the design of a simply supported glulam beam
using the TimberMemberDesign class - a high-level interface that encapsulates
the entire design workflow including bending, shear, and compression checks.

Compare this to simple_timber_beam_example.py which shows the manual
step-by-step formula chaining approach.
"""

from pint import UnitRegistry
import pandas as pd
import time

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
    Design a simply supported glulam beam using the calculator interface.
    
    This example demonstrates how the TimberMemberDesign class simplifies
    the design process by encapsulating all the formula chaining logic.
    """
    
    # ==========================================
    # USER INPUTS - Modify these as needed
    # ==========================================
    
    # Beam geometry
    span_m = 6.0 * m
    spacing_m = 0.4 * m
    
    # Loads - define nominal loads for NBCC load combinations
    dead_load_kPa = 1.5 * kPa
    live_load_kPa = 1.9 * kPa
    snow_load_kPa = 1.2 * kPa
    
    # Axial loads (compression positive)
    dead_axial_kN = 5.0 * kN
    live_axial_kN = 10.0 * kN
    snow_axial_kN = 8.0 * kN
    
    # Section properties: 130 x 456 mm glulam
    b = 130 * mm
    d = 456 * mm
    
    # Material specification
    species = "Douglas Fir-Larch"
    grade = "20f-E"
    
    # Service conditions
    service_condition = "Dry-service conditions"
    
    # Treatment (for K_T factor)
    is_treated = False  # Untreated wood
    
    # ==========================================
    # LOAD MATERIAL PROPERTIES FROM TABLES
    # ==========================================
    
    # Material properties are loaded automatically by TimberMaterial
    # No need to manually load from tables
    
    # ==========================================
    # ADDITIONAL DESIGN PARAMETERS
    # ==========================================
    
    # ==========================================
    # NBCC LOAD COMBINATIONS (BATCH ANALYSIS)
    # ==========================================
    
    # Generate all ULS load combinations per NBCC 2020
    nominal_loads = {
        "D": dead_load_kPa,
        "L": live_load_kPa,
        "S": snow_load_kPa,
    }
    
    nominal_axial_loads = {
        "D": dead_axial_kN,
        "L": live_axial_kN,
        "S": snow_axial_kN,
    }
    
    print("Generating NBCC ULS load combinations...")
    combos = nbcc_uls_combinations(
        nominal_loads,
        include_wind=False,
        include_seismic=False,
    )
    
    print(f"Generated {len(combos.names)} load combinations:")
    for name in combos.names:
        print(f"  - {name}")
    print()
    
    # Compute beam effects for all load combinations (vectorized)
    w_factored = (combos.total * spacing_m).to('kN/m')  # Convert kPa·m to kN/m
    M_f = (w_factored * span_m**2) / 8  # kN·m for all combinations
    V_f = (w_factored * span_m) / 2  # kN for all combinations
    
    # Compute axial compression forces (vectorized) using load components
    import numpy as np
    P_f = np.zeros(len(combos.names)) * kN
    # Use the components dictionary from combos to get factored loads
    if 'D' in combos.components:
        # Components are already factored, get the scalar factors from the total
        D_factors = combos.components['D'] / dead_load_kPa if dead_load_kPa.magnitude != 0 else np.zeros(len(combos.names))
        P_f += D_factors * dead_axial_kN
    if 'L' in combos.components:
        L_factors = combos.components['L'] / live_load_kPa if live_load_kPa.magnitude != 0 else np.zeros(len(combos.names))
        P_f += L_factors * live_axial_kN
    if 'S' in combos.components:
        S_factors = combos.components['S'] / snow_load_kPa if snow_load_kPa.magnitude != 0 else np.zeros(len(combos.names))
        P_f += S_factors * snow_axial_kN
    
    # Loading duration percentages from NBCC combinations
    P_L_percent = combos.duration_long_percent
    P_S_percent = combos.duration_short_percent
    
    # ==========================================
    # RUN DESIGN USING CALCULATOR
    # ==========================================
    
    print("=" * 70)
    print("TIMBER BEAM DESIGN - BATCH CALCULATOR APPROACH")
    print("=" * 70)
    print()
    print(f"Running design for {len(combos.names)} load combinations...")
    print()
    
    # Start timing the calculator execution
    start_time = time.perf_counter()
    
    # Create section components - pass Pint quantities directly
    profile = RectangularProfile(b=b, d=d)
    material = TimberMaterial(grade=grade, species=species, ureg=ureg)
    section = TimberSection(profile=profile, material=material)
    
    # Compute total factored loads for shear coefficient
    w_factored_array = combos.total * spacing_m
    Wf_total = (w_factored_array * span_m).to('N')  # Convert to N for consistent units with g_factor
    V_f_abs = abs(V_f.to('N'))
    sum_g = TimberDesign.g_factor(
        l_a=span_m.to('mm'),
        V_A=V_f_abs,
        V_B=V_f_abs,
        V_C=0 * ureg.N
    ).result
    
    # Create design parameters - pass Pint quantities directly
    parameters = TimberDesignParameters(
        beam_ids=combos.names,
        beam_length=span_m,
        end_conditions="Pin - Pin",
        service_conditions=service_condition,
        lu=span_m,  # Assume full span for lateral stability
        Wf=Wf_total,
        SumG=sum_g,
        ureg=ureg
    )
    
    # Create loads - explicitly convert to expected formula units
    loading = TimberLoads()
    loading.M3 = M_f.to('N*mm')  # Formulas expect N·mm
    loading.V2 = V_f.to('N')  # Formulas expect N
    loading.PL_M3 = P_L_percent
    loading.PS_M3 = P_S_percent
    loading.PL_V2 = P_L_percent
    loading.PS_V2 = P_S_percent
    loading.P = P_f.to('N')  # Compression loads
    loading.PL_P = P_L_percent
    loading.PS_P = P_S_percent
    
    # Set load combination types for kd factor calculation
    loading.combo_type = combos.load_combo_types
    
    # Create design instance and run all checks
    design = TimberBeamDesign(section=section, loading=loading, parameters=parameters)
    procedure = design.checkAll()
    
    # Stop timing
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    # ==========================================
    # EXTRACT RESULTS FROM BATCH CALCULATION
    # ==========================================
    
    # Get utilizations from design instance (DataFrame with columns: beam_id, uM3, uV2, uP)
    max_bending_util = design.utilization['uM3'].max() if 'uM3' in design.utilization.columns else 0.0
    max_shear_util = design.utilization['uV2'].max() if 'uV2' in design.utilization.columns else 0.0
    max_compression_util = design.utilization['uP'].max() if 'uP' in design.utilization.columns else 0.0
    
    max_util = max(max_bending_util, max_shear_util, max_compression_util)
    
    # Find governing combination
    util_cols = [col for col in ['uM3', 'uV2', 'uP'] if col in design.utilization.columns]
    if util_cols:
        governing_idx = design.utilization[util_cols].max(axis=1).idxmax()
    else:
        governing_idx = 0
    governing_combo = combos.names[governing_idx] if len(combos.names) > governing_idx else combos.names[0]
    
    # Determine overall status
    status = 'PASS' if max_util <= 1.0 else 'FAIL'
    
    # Extract resistance values from stored procedure results
    M_r = None
    V_r = None
    P_r = None
    
    if hasattr(design, 'strongAxisPosBendingCheck'):
        bending_results = design.strongAxisPosBendingCheck.results
        if 'Mr' in bending_results:
            # Results are in N·mm, convert to kN·m for display
            M_r = bending_results['Mr'] * ureg('N*mm')
    
    if hasattr(design, 'strongAxisShearCheck'):
        shear_results = design.strongAxisShearCheck.results
        if 'Vr' in shear_results:
            # Results are in N, convert to kN for display
            V_r = shear_results['Vr'] * ureg('N')
    
    if hasattr(design, 'compressionCheck'):
        compression_results = design.compressionCheck.results
        if 'Pr' in compression_results:
            # Results are in N, convert to kN for display
            P_r = compression_results['Pr'] * ureg('N')
    
    # Create results DataFrame from actual per-combination utilizations
    results = design.utilization.copy()
    # Rename columns for consistency
    if 'uM3' in results.columns:
        results.rename(columns={'uM3': 'Bending_Util'}, inplace=True)
    if 'uV2' in results.columns:
        results.rename(columns={'uV2': 'Shear_Util'}, inplace=True)
    if 'uP' in results.columns:
        results.rename(columns={'uP': 'Compression_Util'}, inplace=True)
    # Calculate worst utilization per combination
    util_cols = [col for col in ['Bending_Util', 'Shear_Util', 'Compression_Util'] if col in results.columns]
    if util_cols:
        results['worst_util'] = results[util_cols].max(axis=1)
    else:
        results['worst_util'] = 0.0
    
    # ==========================================
    # DISPLAY RESULTS
    # ==========================================
    
    print("=" * 70)
    print("TIMBER BEAM DESIGN SUMMARY")
    print("=" * 70)
    print(f"  Section:             {b.magnitude:.0f} x {d.magnitude:.0f} mm {grade} {species}")
    print(f"  Span:                {span_m.magnitude} m")
    print(f"  Load combinations:   {len(combos.names)}")
    print(f"  Execution time:      {execution_time:.4f} seconds")
    print()
    if M_r is not None:
        M_r_val = M_r[0] if hasattr(M_r, '__len__') else M_r
        print(f"  Bending resistance:  {M_r_val.to('kN*m').magnitude:.2f} kN·m (constant for all combos)")
    if V_r is not None:
        V_r_val = V_r[0] if hasattr(V_r, '__len__') else V_r
        print(f"  Shear resistance:    {V_r_val.to('kN').magnitude:.2f} kN (constant for all combos)")
    if P_r is not None:
        P_r_val = P_r[0] if hasattr(P_r, '__len__') else P_r
        print(f"  Compression resist.: {P_r_val.to('kN').magnitude:.2f} kN (constant for all combos)")
    print()
    print(f"  Max bending util.:   {max_bending_util:.1%}")
    print(f"  Max shear util.:     {max_shear_util:.1%}")
    print(f"  Max compression util.: {max_compression_util:.1%}")
    print(f"  Max utilization:     {max_util:.1%}")
    print(f"  Governing combo:     {governing_combo}")
    print()
    print(f"  STATUS: {status}")
    print()
    print("\nDesign Summary:")
    # Create simple summary from utilization DataFrame
    summary_data = {
        'Check': ['Bending M3', 'Shear V2', 'Compression P'],
        'Max Utilization': [max_bending_util, max_shear_util, max_compression_util],
        'Status': ['PASS' if max_bending_util <= 1.0 else 'FAIL', 
                   'PASS' if max_shear_util <= 1.0 else 'FAIL',
                   'PASS' if max_compression_util <= 1.0 else 'FAIL']
    }
    summary_df = pd.DataFrame(summary_data)
    print(summary_df)
    
    # ==========================================
    # OPTIONAL: Save calculation document
    # ==========================================
    
    # Generate markdown document with LaTeX equations
    markdown_content = generate_calculation_document(
        span_m, spacing_m, nominal_loads, nominal_axial_loads,
        dead_load_kPa, live_load_kPa, snow_load_kPa,
        dead_axial_kN, live_axial_kN, snow_axial_kN,
        b, d,
        species, grade, service_condition, is_treated,
        combos, results, procedure, design,
        M_r, V_r, P_r, governing_combo, governing_idx,
        max_bending_util, max_shear_util, max_compression_util, status
    )
    
    # Save to markdown file
    output_file = "examples/timber_beam_calculator_output.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print()
    print(f"Full calculation saved to: {output_file}")
    
    return {
        'num_combinations': len(combos.names),
        'bending_resistance_kNm': M_r[0].to('kN*m').magnitude if M_r is not None else None,
        'shear_resistance_kN': V_r[0].to('kN').magnitude if V_r is not None else None,
        'compression_resistance_kN': P_r[0].to('kN').magnitude if P_r is not None else None,
        'max_bending_utilization': max_bending_util,
        'max_shear_utilization': max_shear_util,
        'max_compression_utilization': max_compression_util,
        'max_utilization': max_util,
        'governing_combination': governing_combo,
        'status': status,
        'results_df': results
    }


def generate_calculation_document(
    span_m, spacing_m, nominal_loads, nominal_axial_loads,
    dead_load_kPa, live_load_kPa, snow_load_kPa,
    dead_axial_kN, live_axial_kN, snow_axial_kN,
    b, d,
    species, grade, service_condition, is_treated,
    combos, results_df, procedure, design,
    M_r, V_r, P_r, governing_combo, governing_idx,
    max_bending_util, max_shear_util, max_compression_util, status
):
    """Generate complete calculation document in Markdown with LaTeX for batch results."""
    
    doc = []
    
    # Header
    doc.append("# Timber Beam Design Calculation\n")
    doc.append("## Batch Calculator Approach - CSA O86:24 with NBCC Load Combinations\n")
    doc.append(f"*Calculation Date: January 27, 2026*\n")
    doc.append("\n---\n")
    
    # Project Information
    doc.append("## 1. Design Parameters\n")
    doc.append("### Geometry\n")
    doc.append(f"- Span: $L = {span_m.magnitude}$ m\n")
    doc.append(f"- Beam spacing: $s = {spacing_m.to('mm').magnitude}$ mm\n")
    doc.append(f"- Section: ${b.magnitude:.0f} \\times {d.magnitude:.0f}$ mm\n")
    doc.append("\n")
    
    doc.append("### Material Properties\n")
    doc.append(f"- Species: {species}\n")
    doc.append(f"- Grade: {grade}\n")
    doc.append(f"- Service condition: {service_condition}\n")
    doc.append(f"- Treatment: {'Treated' if is_treated else 'Untreated'}\n")
    doc.append(f"*Material properties loaded automatically from CSA O86:24 Table 7.2*\n")
    doc.append("\n")
    
    doc.append("### Nominal Loading\n")
    doc.append("**Distributed Loads:**\n")
    for load_type, load_value in nominal_loads.items():
        doc.append(f"- {load_type}: ${load_value.magnitude}$ kPa\n")
    doc.append("\n**Axial Loads (Compression):**\n")
    for load_type, load_value in nominal_axial_loads.items():
        doc.append(f"- {load_type}: ${load_value.magnitude}$ kN\n")
    doc.append("\n")
    
    # Load Combinations
    doc.append("## 2. NBCC 2020 ULS Load Combinations\n")
    doc.append(f"Generated **{len(combos.names)}** load combinations:\n\n")
    doc.append("| Combination | Factored Load (kPa) |\n")
    doc.append("|-------------|---------------------|\n")
    for name, total in zip(combos.names, combos.total):
        doc.append(f"| {name} | {total.magnitude:.3f} |\n")
    doc.append("\n")
    
    # Applied Forces for Governing Case
    M_f_gov = combos.total[governing_idx] * spacing_m * span_m**2 / 8
    V_f_gov = combos.total[governing_idx] * spacing_m * span_m / 2
    # Compute P_f_gov using the same logic as the main computation
    P_f_gov = 0 * ureg.kN
    if 'D' in combos.components and dead_load_kPa.magnitude != 0:
        D_factor = (combos.components['D'][governing_idx] / dead_load_kPa).magnitude
        P_f_gov += D_factor * dead_axial_kN
    if 'L' in combos.components and live_load_kPa.magnitude != 0:
        L_factor = (combos.components['L'][governing_idx] / live_load_kPa).magnitude
        P_f_gov += L_factor * live_axial_kN
    if 'S' in combos.components and snow_load_kPa.magnitude != 0:
        S_factor = (combos.components['S'][governing_idx] / snow_load_kPa).magnitude
        P_f_gov += S_factor * snow_axial_kN
    
    doc.append("## 3. Applied Forces (Governing Combination)\n")
    doc.append(f"Governing combination: **{governing_combo}**\n\n")
    doc.append("For a simply supported beam with axial compression:\n")
    doc.append("$$\n")
    doc.append("\\begin{align}\n")
    doc.append(f"M_f &= \\frac{{w_f L^2}}{{8}} = {M_f_gov.to('kN*m').magnitude:.2f} \\text{{ kNm}} \\\\\n")
    doc.append(f"V_f &= \\frac{{w_f L}}{{2}} = {V_f_gov.to('kN').magnitude:.2f} \\text{{ kN}} \\\\\n")
    doc.append(f"P_f &= {P_f_gov.to('kN').magnitude:.2f} \\text{{ kN}}\n")
    doc.append("\\end{align}\n")
    doc.append("$$\n")
    doc.append("\n")
    
    # Resistance Calculations (using procedure's built-in LaTeX generation)
    doc.append("## 4. Resistance Calculations\n\n")
    doc.append("Showing calculations for the first load combination.\n\n")
    
    # Display bending check procedure
    if hasattr(design, 'strongAxisPosBendingCheck'):
        doc.append("### Bending Resistance\n\n")
        doc.append(design.strongAxisPosBendingCheck.generate_latex(index=0))
        doc.append("\n")
    
    # Display shear check procedure
    if hasattr(design, 'strongAxisShearCheck'):
        doc.append("### Shear Resistance\n\n")
        doc.append(design.strongAxisShearCheck.generate_latex(index=0))
        doc.append("\n")
    
    # Display compression check procedure
    if hasattr(design, 'parallelCompressionCheck'):
        doc.append("### Compression Resistance\n\n")
        doc.append(design.parallelCompressionCheck.generate_latex(index=0))
        doc.append("\n")
    
    # Batch Results Summary Table
    doc.append("## 5. Batch Results Summary\n")
    doc.append("\nComplete results for all load combinations:\n\n")
    doc.append("*Note: Units are stripped in this table for display. M_r values are in N·mm, V_r in N.*\n\n")
    
    # Select columns to display (replace worst_status with worst_util)
    display_df = results_df.copy()
    if 'worst_status' in display_df.columns and 'worst_util' in display_df.columns:
        display_df = display_df.drop(columns=['worst_status'])
    
    # Format the DataFrame as markdown table manually
    doc.append("| Combination | " + " | ".join(display_df.columns) + " |\n")
    doc.append("|" + "|".join(["---"] * (len(display_df.columns) + 1)) + "|\n")
    for combo_name, row in zip(combos.names, display_df.itertuples(index=False)):
        values = " | ".join([f"{v:.4f}" if isinstance(v, (int, float)) else str(v) for v in row])
        doc.append(f"| {combo_name} | {values} |\n")
    doc.append("\n\n")
    
    # Design Checks for Governing Case
    doc.append("## 6. Design Checks (Governing Case)\n")
    doc.append("### Bending Check\n")
    doc.append("$$\n")
    if M_r is not None:
        M_r_val = M_r[governing_idx] if hasattr(M_r, '__len__') and len(M_r) > governing_idx else M_r[0] if hasattr(M_r, '__len__') else M_r
        doc.append(f"\\frac{{M_f}}{{M_r}} = \\frac{{{M_f_gov.to('kN*m').magnitude:.2f}}}{{{M_r_val.to('kN*m').magnitude:.2f}}} = {max_bending_util:.3f} ")
    else:
        doc.append(f"\\frac{{M_f}}{{M_r}} = {max_bending_util:.3f} ")
    if max_bending_util <= 1.0:
        doc.append("\\le 1.0 \\quad \\checkmark\n")
    else:
        doc.append("> 1.0 \\quad \\text{FAIL}\n")
    doc.append("$$\n")
    doc.append("\n")
    
    doc.append("### Shear Check\n")
    doc.append("$$\n")
    if V_r is not None:
        V_r_val = V_r[governing_idx] if hasattr(V_r, '__len__') and len(V_r) > governing_idx else V_r[0] if hasattr(V_r, '__len__') else V_r
        doc.append(f"\\frac{{V_f}}{{V_r}} = \\frac{{{V_f_gov.to('kN').magnitude:.2f}}}{{{V_r_val.to('kN').magnitude:.2f}}} = {max_shear_util:.3f} ")
    else:
        doc.append(f"\\frac{{V_f}}{{V_r}} = {max_shear_util:.3f} ")
    if max_shear_util <= 1.0:
        doc.append("\\le 1.0 \\quad \\checkmark\n")
    else:
        doc.append("> 1.0 \\quad \\text{FAIL}\n")
    doc.append("$$\n")
    doc.append("\n")
    
    doc.append("### Compression Check\n")
    doc.append("$$\n")
    if P_r is not None:
        P_r_val = P_r[governing_idx] if hasattr(P_r, '__len__') and len(P_r) > governing_idx else P_r[0] if hasattr(P_r, '__len__') else P_r
        doc.append(f"\\frac{{P_f}}{{P_r}} = \\frac{{{P_f_gov.to('kN').magnitude:.2f}}}{{{P_r_val.to('kN').magnitude:.2f}}} = {max_compression_util:.3f} ")
    else:
        doc.append(f"\\frac{{P_f}}{{P_r}} = {max_compression_util:.3f} ")
    if max_compression_util <= 1.0:
        doc.append("\\le 1.0 \\quad \\checkmark\n")
    else:
        doc.append("> 1.0 \\quad \\text{FAIL}\n")
    doc.append("$$\n")
    doc.append("\n")
    
    # Summary
    doc.append("## 7. Summary\n")
    doc.append(f"- **Load Combinations Analyzed:** {len(combos.names)}\n")
    doc.append(f"- **Governing Combination:** {governing_combo}\n")
    doc.append(f"- **Maximum Bending Utilization:** {max_bending_util:.1%}\n")
    doc.append(f"- **Maximum Shear Utilization:** {max_shear_util:.1%}\n")
    doc.append(f"- **Maximum Compression Utilization:** {max_compression_util:.1%}\n")
    doc.append(f"- **Maximum Utilization:** {max(max_bending_util, max_shear_util, max_compression_util):.1%}\n")
    doc.append(f"- **Design Status:** **{status}**\n")
    doc.append("\n")
    
    if status == 'PASS':
        doc.append(f"The ${b.magnitude:.0f} \\times {d.magnitude:.0f}$ mm {grade} {species} glulam beam is adequate for all {len(combos.names)} NBCC load combinations including axial compression.\n")
    else:
        doc.append(f"The ${b.magnitude:.0f} \\times {d.magnitude:.0f}$ mm {grade} {species} glulam beam is **NOT** adequate. Consider increasing section size.\n")
    
    doc.append("\n---\n")
    doc.append("*Calculation performed using EIME TimberMemberDesign with NBCC 2020 load combinations*\n")
    
    return "".join(doc)


if __name__ == "__main__":
    main()
