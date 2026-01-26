"""
Simple Timber Beam Example

This example demonstrates the design of a simply supported glulam beam
under gravity loading using CSA O86:24, with full LaTeX output.
"""

from design.csa_o86_2025.formulas import (
    long_duration_factor,
    modified_bending_strength,
    section_modulus,
    bending_size_factor,
    moment_resistance_a,
    modified_shear_strength,
    shear_resistance
)


def main():
    """
    Design a simply supported glulam beam for a residential floor.
    
    Design scenario:
    - Span: 6.0 m
    - Beam spacing: 400 mm (0.4 m)
    - Dead load: 1.5 kPa
    - Live load: 1.9 kPa (residential)
    - Glulam: 20f-E D.Fir-L (130 x 456 mm)
    """
    
    # Beam geometry
    span_m = 6.0  # m
    spacing_m = 0.4  # m
    
    # Loads
    dead_load_kPa = 1.5  # kPa
    live_load_kPa = 1.9  # kPa
    
    # Load combinations (CSA O86:24, factored)
    w_dead = dead_load_kPa * spacing_m  # kN/m
    w_live = live_load_kPa * spacing_m  # kN/m
    w_factored = 1.25 * w_dead + 1.5 * w_live  # kN/m (ULS)
    
    # Maximum moment and shear for simply supported beam
    M_f = (w_factored * span_m**2) / 8  # kNm
    V_f = (w_factored * span_m) / 2  # kN
    
    # Section properties: 130 x 456 mm glulam
    section_properties = {
        'b': 130,  # mm
        'd': 456,  # mm
        'A': 130 * 456  # mm²
    }
    
    # Material properties: 20f-E D.Fir-L (from CSA O86:24 Table 7.3)
    material_properties = {
        'f_b': 30.8,  # MPa (bending strength)
        'f_v': 2.1,   # MPa (shear strength)
        'f_c': 27.5,  # MPa (compression strength)
        'E': 11700    # MPa (modulus of elasticity)
    }
    
    # Design parameters
    design_parameters = {
        # Resistance factors
        'phi_b': 0.9,  # Bending
        'phi_v': 0.9,  # Shear
        'phi_c': 0.8,  # Compression
        
        # System factor
        'K_H': 1.0,  # No load sharing
        
        # Service condition factors (dry service)
        'K_Sb': 1.0,
        'K_Sv': 1.0,
        'K_Sc': 1.0,
        'K_SE': 1.0,
        
        # Treatment factor (untreated)
        'K_T': 1.0,
        
        # Curvature factor (straight beam)
        'K_x': 1.0,
        
        # Span for size factor calculation
        'L': span_m * 1000  # mm
    }
    
    # Loading for duration factor calculation
    # Assume 50% dead load, 50% live load for K_D
    total_load = w_dead + w_live
    P_L = w_dead / total_load * 100  # Percentage long-term (dead)
    P_S = w_live / total_load * 100  # Percentage standard-term (live)
    
    # Storage for formulas and LaTeX output
    formulas = []
    latex_output = []
    
    # ==========================================
    # STEP 1: Load Duration Factor
    # ==========================================
    KD = long_duration_factor(P_L, P_S)
    K_D_value = KD.solve().result
    formulas.append(KD)
    latex_output.append("### Load Duration Factor\n")
    latex_output.append(f"$$\n{KD.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 2: Modified Bending Strength
    # ==========================================
    Fb = modified_bending_strength(
        material_properties['f_b'],
        K_D_value,
        design_parameters['K_H'],
        design_parameters['K_Sb'],
        design_parameters['K_T']
    )
    F_b_value = Fb.solve().result
    formulas.append(Fb)
    latex_output.append("### Modified Bending Strength\n")
    latex_output.append(f"$$\n{Fb.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 3: Section Modulus
    # ==========================================
    S = section_modulus(section_properties['b'], section_properties['d'])
    S_value = S.solve().result
    formulas.append(S)
    latex_output.append("### Section Modulus\n")
    latex_output.append(f"$$\n{S.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 4: Bending Size Factor
    # ==========================================
    KZbg = bending_size_factor(
        section_properties['b'],
        section_properties['d'],
        design_parameters['L']
    )
    K_Zbg_value = KZbg.solve().result
    formulas.append(KZbg)
    latex_output.append("### Bending Size Factor\n")
    latex_output.append(f"$$\n{KZbg.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 5: Moment Resistance
    # ==========================================
    Mr_a = moment_resistance_a(
        design_parameters['phi_b'],
        F_b_value,
        S_value,
        design_parameters['K_x'],
        K_Zbg_value
    )
    M_r = Mr_a.solve().result / 1e6  # Convert to kNm
    formulas.append(Mr_a)
    latex_output.append("### Moment Resistance (Method A)\n")
    latex_output.append(f"$$\n{Mr_a.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 6: Modified Shear Strength
    # ==========================================
    Fv = modified_shear_strength(
        material_properties['f_v'],
        K_D_value,
        design_parameters['K_H'],
        design_parameters['K_Sv'],
        design_parameters['K_T']
    )
    F_v_value = Fv.solve().result
    formulas.append(Fv)
    latex_output.append("### Modified Shear Strength\n")
    latex_output.append(f"$$\n{Fv.generate_latex()}\n$$\n")
    
    # ==========================================
    # STEP 7: Shear Resistance
    # ==========================================
    Vr = shear_resistance(
        design_parameters['phi_v'],
        F_v_value,
        section_properties['A']
    )
    V_r = Vr.solve().result / 1000  # Convert to kN
    formulas.append(Vr)
    latex_output.append("### Shear Resistance\n")
    latex_output.append(f"$$\n{Vr.generate_latex()}\n$$\n")
    
    # Calculate utilizations
    bending_util = M_f / M_r if M_r > 0 else float('inf')
    shear_util = V_f / V_r if V_r > 0 else float('inf')
    
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
    
    # Print results
    print("=" * 70)
    print("TIMBER BEAM DESIGN CALCULATION")
    print("=" * 70)
    print()
    print("INPUTS:")
    print(f"  Span:                {span_m} m")
    print(f"  Beam spacing:        {spacing_m * 1000} mm")
    print(f"  Dead load:           {dead_load_kPa} kPa")
    print(f"  Live load:           {live_load_kPa} kPa")
    print(f"  Section:             {section_properties['b']} x {section_properties['d']} mm")
    print(f"  Material:            20f-E D.Fir-L")
    print()
    print("LOADING:")
    print(f"  Factored UDL:        {w_factored:.2f} kN/m")
    print(f"  Factored moment:     {M_f:.2f} kNm")
    print(f"  Factored shear:      {V_f:.2f} kN")
    print()
    print("RESULTS:")
    print(f"  Bending resistance:  {results['bending_resistance_kNm']:.2f} kNm")
    print(f"  Shear resistance:    {results['shear_resistance_kN']:.2f} kN")
    print(f"  Bending util.:       {results['bending_utilization']:.3f} ({results['bending_utilization']*100:.1f}%)")
    print(f"  Shear util.:         {results['shear_utilization']:.3f} ({results['shear_utilization']*100:.1f}%)")
    print(f"  Max utilization:     {results['max_utilization']:.3f} ({results['max_utilization']*100:.1f}%)")
    print()
    print(f"STATUS: {results['status']}")
    print("=" * 70)
    
    # ==========================================
    # Generate LaTeX Calculation Document
    # ==========================================
    markdown_content = generate_calculation_document(
        span_m, spacing_m, dead_load_kPa, live_load_kPa,
        section_properties, material_properties,
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
    section_properties, material_properties,
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
    doc.append(f"- Span: $L = {span_m}$ m\n")
    doc.append(f"- Beam spacing: $s = {spacing_m * 1000}$ mm\n")
    doc.append(f"- Section: ${section_properties['b']} \\times {section_properties['d']}$ mm\n")
    doc.append("\n")
    
    doc.append("### Material Properties (20f-E D.Fir-L)\n")
    doc.append(f"- Specified bending strength: $f_b = {material_properties['f_b']}$ MPa\n")
    doc.append(f"- Specified shear strength: $f_v = {material_properties['f_v']}$ MPa\n")
    doc.append(f"- Modulus of elasticity: $E = {material_properties['E']}$ MPa\n")
    doc.append("\n")
    
    doc.append("### Loading\n")
    doc.append(f"- Dead load: $D = {dead_load_kPa}$ kPa\n")
    doc.append(f"- Live load: $L = {live_load_kPa}$ kPa\n")
    doc.append(f"- Factored UDL: $w_f = {w_factored:.3f}$ kN/m\n")
    doc.append("\n")
    
    # Applied Forces
    doc.append("## 2. Applied Forces\n")
    doc.append("For a simply supported beam:\n")
    doc.append("$$\n")
    doc.append("\\begin{align}\n")
    doc.append(f"M_f &= \\frac{{w_f L^2}}{{8}} = \\frac{{{w_factored:.3f} \\times {span_m}^2}}{{8}} = {M_f:.2f} \\text{{ kNm}} \\\\\n")
    doc.append(f"V_f &= \\frac{{w_f L}}{{2}} = \\frac{{{w_factored:.3f} \\times {span_m}}}{{2}} = {V_f:.2f} \\text{{ kN}}\n")
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
    doc.append(f"\\frac{{M_f}}{{M_r}} = \\frac{{{M_f:.2f}}}{{{results['bending_resistance_kNm']:.2f}}} = {results['bending_utilization']:.3f} ")
    if results['bending_utilization'] <= 1.0:
        doc.append("\\le 1.0 \\quad \\checkmark\n")
    else:
        doc.append("> 1.0 \\quad \\text{FAIL}\n")
    doc.append("$$\n")
    doc.append("\n")
    
    doc.append("### Shear Check\n")
    doc.append("$$\n")
    doc.append(f"\\frac{{V_f}}{{V_r}} = \\frac{{{V_f:.2f}}}{{{results['shear_resistance_kN']:.2f}}} = {results['shear_utilization']:.3f} ")
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
        doc.append(f"The ${section_properties['b']} \\times {section_properties['d']}$ mm 20f-E D.Fir-L glulam beam is adequate for the applied loading.\n")
    else:
        doc.append(f"The ${section_properties['b']} \\times {section_properties['d']}$ mm 20f-E D.Fir-L glulam beam is **NOT** adequate for the applied loading. Consider increasing section size.\n")
    
    doc.append("\n---\n")
    doc.append("*Calculation performed using EIME Engineering Framework*\n")
    
    return "".join(doc)


if __name__ == "__main__":
    main()
