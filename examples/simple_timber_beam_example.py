"""
Simple Timber Beam Example

This example demonstrates the design of a simply supported glulam beam
under gravity loading using CSA O86:24, with full LaTeX output and Pint units.
"""

from pint import UnitRegistry

from design.csa_o86_2025.formulas import (
    long_duration_factor,
    modified_bending_strength,
    section_modulus,
    bending_size_factor,
    moment_resistance_a,
    modified_shear_strength,
    shear_resistance
)
from design.csa_o86_2025.tables import specified_strengths, service_condition_factors

# Create unit registry
ureg = UnitRegistry()

# Unit shorthands
m = ureg.m
mm = ureg.mm
kPa = ureg.kPa
MPa = ureg.MPa
kN = ureg.kN
nd = ureg.dimensionless


def main():
    """
    Design a simply supported glulam beam for a residential floor.
    
    This example demonstrates automatic table lookups for material properties
    and service condition factors based on user inputs.
    
    Material properties (f_b, f_v, f_c, E) are looked up from CSA O86-24 Table 7.2
    based on species and grade. Service condition factors (K_Sb, K_Sv, K_Sc, K_SE)
    are looked up from CSA O86-24 Table 7.3 based on service condition.
    """
    
    # ==========================================
    # USER INPUTS - Modify these as needed
    # ==========================================
    
    # Beam geometry
    span_m = 6.0 * m
    spacing_m = 0.4 * m
    
    # Loads
    dead_load_kPa = 1.5 * kPa
    live_load_kPa = 1.9 * kPa
    
    # Section properties: 130 x 456 mm glulam
    b = 130 * mm
    d = 456 * mm
    
    # Material specification
    # Available species: "Douglas Fir-Larch", "Spruce-Lodgepole Pine-Jack Pine"
    # Available grades: "24f-E", "24f-EX", "20f-E", "20f-EX", "18t-E", "16c-E"
    #   (Note: not all grades available for all species)
    species = "Douglas Fir-Larch"
    grade = "20f-E"
    
    # Service conditions
    # Options: "Dry-service conditions", "Wet-service conditions"
    service_condition = "Dry-service conditions"
    
    # Treatment (for K_T factor)
    is_treated = False  # Untreated wood
    
    # ==========================================
    # LOAD MATERIAL PROPERTIES FROM TABLES
    # ==========================================
    
    # Load specified strengths table
    strengths_table = specified_strengths()
    material_props_dict = strengths_table.data.loc[grade, species]
    
    # Material properties with units (from CSA O86:24 Table 7.2)
    f_b = material_props_dict['f_b_pos'] * MPa  # bending strength (positive/tension face)
    f_v = material_props_dict['f_v'] * MPa       # shear strength
    f_c = material_props_dict['f_c'] * MPa       # compression strength
    E = material_props_dict['E'] * MPa           # modulus of elasticity
    
    # Load service condition factors from table
    service_table = service_condition_factors()
    
    # Service condition factors (from CSA O86:24 Table 7.3)
    K_Sb = service_table.data.loc['K_Sb', service_condition] * nd
    K_Sv = service_table.data.loc['K_Sv', service_condition] * nd
    K_Sc = service_table.data.loc['K_Sc', service_condition] * nd
    K_SE = service_table.data.loc['K_SE', service_condition] * nd
    
    # ==========================================
    # ADDITIONAL DESIGN PARAMETERS
    # ==========================================
    
    A = b * d  # Cross-sectional area
    
    A = b * d  # Cross-sectional area
    
    # Load combinations (CSA O86:24, factored)
    w_dead = dead_load_kPa * spacing_m  # kN/m
    w_live = live_load_kPa * spacing_m  # kN/m
    w_factored = 1.25 * w_dead + 1.5 * w_live  # kN/m (ULS)
    
    # Maximum moment and shear for simply supported beam
    M_f = (w_factored * span_m**2) / 8  # kNm
    V_f = (w_factored * span_m) / 2  # kN
    
    # Design parameters (dimensionless factors)
    phi_b = 0.9 * nd  # Bending resistance factor
    phi_v = 0.9 * nd  # Shear resistance factor
    phi_c = 0.8 * nd  # Compression resistance factor
    
    K_H = 1.0 * nd   # System factor
    
    # Treatment factor
    K_T = 0.75 * nd if is_treated else 1.0 * nd
    
    # Curvature factor (straight beam)
    K_x = 1.0 * nd
    
    # Span for size factor calculation
    L = span_m.to(mm)  # Convert to mm
    
    # Loading for duration factor calculation
    # Assume 50% dead load, 50% live load for K_D
    total_load = w_dead + w_live
    P_L_percent = (w_dead / total_load * 100)  # Percentage long-term (dead)
    P_S_percent = (w_live / total_load * 100)  # Percentage standard-term (live)
    
    # Storage for formulas and LaTeX output
    formulas = []
    latex_output = []
    
    # ==========================================
    # STEP 1: Load Duration Factor
    # ==========================================
    KD = long_duration_factor(P_L_percent, P_S_percent)
    K_D_value = KD.solve().result
    formulas.append(KD)
    latex_output.append("### Load Duration Factor\n")
    latex_output.append(f"$$\n{KD.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 2: Modified Bending Strength
    # ==========================================
    Fb = modified_bending_strength(
        f_b,
        K_D_value,
        K_H,
        K_Sb,
        K_T
    )
    F_b_value = Fb.solve().result
    formulas.append(Fb)
    latex_output.append("### Modified Bending Strength\n")
    latex_output.append(f"$$\n{Fb.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 3: Section Modulus
    # ==========================================
    S = section_modulus(b, d)
    S_value = S.solve().result
    formulas.append(S)
    latex_output.append("### Section Modulus\n")
    latex_output.append(f"$$\n{S.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 4: Bending Size Factor
    # ==========================================
    KZbg = bending_size_factor(b, d, L)
    K_Zbg_value = KZbg.solve().result
    formulas.append(KZbg)
    latex_output.append("### Bending Size Factor\n")
    latex_output.append(f"$$\n{KZbg.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 5: Moment Resistance
    # ==========================================
    Mr_a = moment_resistance_a(
        phi_b,
        F_b_value,
        S_value,
        K_x,
        K_Zbg_value
    )
    M_r_result = Mr_a.solve().result
    M_r = M_r_result.to('kN*m').magnitude  # Convert to kNm for display
    formulas.append(Mr_a)
    latex_output.append("### Moment Resistance (Method A)\n")
    latex_output.append(f"$$\n{Mr_a.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 6: Modified Shear Strength
    # ==========================================
    Fv = modified_shear_strength(
        f_v,
        K_D_value,
        K_H,
        K_Sv,
        K_T
    )
    F_v_value = Fv.solve().result
    formulas.append(Fv)
    latex_output.append("### Modified Shear Strength\n")
    latex_output.append(f"$$\n{Fv.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 7: Shear Resistance
    # ==========================================
    Vr = shear_resistance(
        phi_v,
        F_v_value,
        A
    )
    V_r_result = Vr.solve().result
    V_r = V_r_result.to('kN').magnitude  # Convert to kN for display
    formulas.append(Vr)
    latex_output.append("### Shear Resistance\n")
    latex_output.append(f"$$\n{Vr.generate_latex()}\n$$\n")
    
    # Calculate utilizations
    bending_util = (M_f / M_r).magnitude if M_r > 0 else float('inf')
    shear_util = (V_f / V_r).magnitude if V_r > 0 else float('inf')
    
    # Determine overall status
    max_util = max(bending_util, shear_util)
    status = 'PASS' if max_util <= 1.0 else 'FAIL'
    
    # Package results
    results = {
        'bending_resistance_kNm': M_r,
        'shear_resistance_kN': V_r,
        'bending_utilization': bending_util,
        'shear_utilization': shear_util,
        'max_utilization': max_util,
        'status': status
    }
    
    # Print results summary
    print("=" * 70)
    print("TIMBER BEAM DESIGN SUMMARY")
    print("=" * 70)
    print(f"  Section:             {b.magnitude:.0f} x {d.magnitude:.0f} mm {grade} {species}")
    print(f"  Span:                {span_m.magnitude} m")
    print()
    print(f"  Bending util.:       {results['bending_utilization']:.1%}")
    print(f"  Shear util.:         {results['shear_utilization']:.1%}")
    print(f"  Max utilization:     {results['max_utilization']:.1%}")
    print()
    print(f"  STATUS: {results['status']}")
    print("=" * 70)
    
    # ==========================================
    # Generate LaTeX Calculation Document
    # ==========================================
    markdown_content = generate_calculation_document(
        span_m, spacing_m, dead_load_kPa, live_load_kPa,
        b, d, f_b, f_v, E,
        species, grade, service_condition, is_treated,
        w_factored, M_f, V_f,
        latex_output, results
    )
    
    # Save to markdown file
    output_file = "examples/timber_beam_calculation.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print()
    print(f"Full calculation saved to: {output_file}")
    
    return results


def generate_calculation_document(
    span_m, spacing_m, dead_load_kPa, live_load_kPa,
    b, d, f_b, f_v, E,
    species, grade, service_condition, is_treated,
    w_factored, M_f, V_f,
    latex_output, results
):
    """Generate complete calculation document in Markdown with LaTeX."""
    
    doc = []
    
    # Header
    doc.append("# Timber Beam Design Calculation\n")
    doc.append("## Simply Supported Glulam Beam - CSA O86:24\n")
    doc.append(f"*Calculation Date: January 26, 2026*\n")
    doc.append("\n---\n")
    
    # Project Information
    doc.append("## 1. Design Parameters\n")
    doc.append("### Geometry\n")
    doc.append(f"- Span: $L = {span_m.magnitude}$ m\n")
    doc.append(f"- Beam spacing: $s = {spacing_m.to(mm).magnitude}$ mm\n")
    doc.append(f"- Section: ${b.magnitude:.0f} \\times {d.magnitude:.0f}$ mm\n")
    doc.append("\n")
    
    doc.append("### Material Properties (20f-E D.Fir-L)\n")
    doc.append(f"- Species: {species}\n")
    doc.append(f"- Grade: {grade}\n")
    doc.append(f"- Specified bending strength: $f_b = {f_b.magnitude}$ MPa\n")
    doc.append(f"- Specified shear strength: $f_v = {f_v.magnitude}$ MPa\n")
    doc.append(f"- Modulus of elasticity: $E = {E.magnitude}$ MPa\n")
    doc.append(f"- Service condition: {service_condition}\n")
    doc.append(f"- Treatment: {'Treated' if is_treated else 'Untreated'}\n")
    doc.append("\n")
    
    doc.append("### Loading\n")
    doc.append(f"- Dead load: $D = {dead_load_kPa.magnitude}$ kPa\n")
    doc.append(f"- Live load: $L = {live_load_kPa.magnitude}$ kPa\n")
    doc.append(f"- Factored UDL: $w_f = {w_factored.to('kN/m').magnitude:.3f}$ kN/m\n")
    doc.append("\n")
    
    # Applied Forces
    doc.append("## 2. Applied Forces\n")
    doc.append("For a simply supported beam:\n")
    doc.append("$$\n")
    doc.append("\\begin{align}\n")
    doc.append(f"M_f &= \\frac{{w_f L^2}}{{8}} = \\frac{{{w_factored.to('kN/m').magnitude:.3f} \\times {span_m.magnitude}^2}}{{8}} = {M_f.to('kN*m').magnitude:.2f} \\text{{ kNm}} \\\\\n")
    doc.append(f"V_f &= \\frac{{w_f L}}{{2}} = \\frac{{{w_factored.to('kN/m').magnitude:.3f} \\times {span_m.magnitude}}}{{2}} = {V_f.to('kN').magnitude:.2f} \\text{{ kN}}\n")
    doc.append("\\end{align}\n")
    doc.append("$$\n")
    doc.append("\n")
    
    # Resistance Calculations
    doc.append("## 3. Resistance Calculations\n")
    doc.append("\n")
    
    # Add all the LaTeX formulas
    for section in latex_output:
        doc.append(section)
        doc.append("\n")
    
    # Utilization Checks
    doc.append("## 4. Design Checks\n")
    doc.append("### Bending Check\n")
    doc.append("$$\n")
    doc.append(f"\\frac{{M_f}}{{M_r}} = \\frac{{{M_f.to('kN*m').magnitude:.2f}}}{{{results['bending_resistance_kNm']:.2f}}} = {results['bending_utilization']:.3f} ")
    if results['bending_utilization'] <= 1.0:
        doc.append("\\le 1.0 \\quad \\checkmark\n")
    else:
        doc.append("> 1.0 \\quad \\text{FAIL}\n")
    doc.append("$$\n")
    doc.append("\n")
    
    doc.append("### Shear Check\n")
    doc.append("$$\n")
    doc.append(f"\\frac{{V_f}}{{V_r}} = \\frac{{{V_f.to('kN').magnitude:.2f}}}{{{results['shear_resistance_kN']:.2f}}} = {results['shear_utilization']:.3f} ")
    if results['shear_utilization'] <= 1.0:
        doc.append("\\le 1.0 \\quad \\checkmark\n")
    else:
        doc.append("> 1.0 \\quad \\text{FAIL}\n")
    doc.append("$$\n")
    doc.append("\n")
    
    # Summary
    doc.append("## 5. Summary\n")
    doc.append(f"- **Maximum Utilization:** {results['max_utilization']:.1%}\n")
    doc.append(f"- **Design Status:** **{results['status']}**\n")
    doc.append("\n")
    
    if results['status'] == 'PASS':
        doc.append(f"The ${b.magnitude:.0f} \\times {d.magnitude:.0f}$ mm {grade} {species} glulam beam is adequate for the applied loading.\n")
    else:
        doc.append(f"The ${b.magnitude:.0f} \\times {d.magnitude:.0f}$ mm {grade} {species} glulam beam is **NOT** adequate for the applied loading. Consider increasing section size.\n")
    
    doc.append("\n---\n")
    doc.append("*Calculation performed using EIME Engineering Framework*\n")
    
    return "".join(doc)


if __name__ == "__main__":
    main()
