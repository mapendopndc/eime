"""
Simple Timber Beam Calculator Example

This example demonstrates the design of a simply supported glulam beam
using the TimberBeamCalculator class - a high-level interface that encapsulates
the entire design workflow.

Compare this to simple_timber_beam_example.py which shows the manual
step-by-step formula chaining approach.
"""

from pint import UnitRegistry

from design.csa_o86_2025.calculators import TimberBeamCalculator
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
    Design a simply supported glulam beam using the calculator interface.
    
    This example demonstrates how the TimberBeamCalculator simplifies
    the design process by encapsulating all the formula chaining logic.
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
    species = "Douglas Fir-Larch"
    grade = "20f-E"
    
    # Service conditions
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
    f_b = material_props_dict['f_b_pos'] * MPa
    f_v = material_props_dict['f_v'] * MPa
    E = material_props_dict['E'] * MPa
    
    # Load service condition factors from table
    service_table = service_condition_factors()
    
    # Service condition factors (from CSA O86:24 Table 7.3)
    K_Sb = service_table.data.loc['K_Sb', service_condition] * nd
    K_Sv = service_table.data.loc['K_Sv', service_condition] * nd
    
    # ==========================================
    # ADDITIONAL DESIGN PARAMETERS
    # ==========================================
    
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
    K_H = 1.0 * nd   # System factor
    K_T = 0.75 * nd if is_treated else 1.0 * nd  # Treatment factor
    K_x = 1.0 * nd   # Curvature factor (straight beam)
    
    # Span for size factor calculation
    L = span_m.to(mm)  # Convert to mm
    
    # Loading for duration factor calculation
    total_load = w_dead + w_live
    P_L_percent = (w_dead / total_load * 100)  # Percentage long-term (dead)
    P_S_percent = (w_live / total_load * 100)  # Percentage standard-term (live)
    
    # ==========================================
    # RUN DESIGN USING CALCULATOR
    # ==========================================
    
    print("=" * 70)
    print("TIMBER BEAM DESIGN - CALCULATOR APPROACH")
    print("=" * 70)
    print()
    print("Running design calculation...")
    print()
    
    # Create calculator instance
    calculator = TimberBeamCalculator()
    
    # Run design - all formula chaining happens inside the calculator
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
        phi_v=phi_v
    )
    
    # ==========================================
    # EXTRACT RESULTS
    # ==========================================
    
    # Extract key values from the procedure
    procedure = calculator.get_procedure()
    
    # Get resistance values from formulas in the procedure
    M_r = None
    V_r = None
    for item in procedure.procedure:
        if hasattr(item, 'name'):
            if item.name == 'M_{r,a}':
                M_r = item.result
            elif item.name == 'V_r':
                V_r = item.result
    
    # Calculate utilizations (convert to dimensionless to handle unit mismatches)
    bending_util = (M_f / M_r).to('dimensionless').magnitude if M_r and M_r.magnitude > 0 else float('inf')
    shear_util = (V_f / V_r).to('dimensionless').magnitude if V_r and V_r.magnitude > 0 else float('inf')
    
    # Determine overall status
    max_util = max(bending_util, shear_util)
    status = 'PASS' if max_util <= 1.0 else 'FAIL'
    
    # ==========================================
    # DISPLAY RESULTS
    # ==========================================
    
    print("=" * 70)
    print("TIMBER BEAM DESIGN SUMMARY")
    print("=" * 70)
    print(f"  Section:             {b.magnitude:.0f} x {d.magnitude:.0f} mm {grade} {species}")
    print(f"  Span:                {span_m.magnitude} m")
    print()
    print(f"  Bending resistance:  {M_r.to('kN*m').magnitude:.2f} kNm")
    print(f"  Shear resistance:    {V_r.to('kN').magnitude:.2f} kN")
    print()
    print(f"  Bending util.:       {bending_util:.1%}")
    print(f"  Shear util.:         {shear_util:.1%}")
    print(f"  Max utilization:     {max_util:.1%}")
    print()
    print(f"  STATUS: {status}")
    
    # ==========================================
    # OPTIONAL: Save calculation document
    # ==========================================
    
    # Generate markdown document with LaTeX equations
    markdown_content = generate_calculation_document(
        span_m, spacing_m, dead_load_kPa, live_load_kPa,
        b, d, f_b, f_v, E,
        species, grade, service_condition, is_treated,
        w_factored, M_f, V_f,
        procedure, M_r, V_r, bending_util, shear_util, status
    )
    
    # Save to markdown file
    output_file = "examples/timber_beam_calculator_output.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print()
    print(f"Full calculation saved to: {output_file}")
    
    return {
        'bending_resistance_kNm': M_r.to('kN*m').magnitude,
        'shear_resistance_kN': V_r.to('kN').magnitude,
        'bending_utilization': bending_util,
        'shear_utilization': shear_util,
        'max_utilization': max_util,
        'status': status
    }


def generate_calculation_document(
    span_m, spacing_m, dead_load_kPa, live_load_kPa,
    b, d, f_b, f_v, E,
    species, grade, service_condition, is_treated,
    w_factored, M_f, V_f,
    procedure, M_r, V_r, bending_util, shear_util, status
):
    """Generate complete calculation document in Markdown with LaTeX."""
    
    doc = []
    
    # Header
    doc.append("# Timber Beam Design Calculation\n")
    doc.append("## Calculator Approach - CSA O86:24\n")
    doc.append(f"*Calculation Date: January 26, 2026*\n")
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
    doc.append(f"M_f &= \\frac{{w_f L^2}}{{8}} = {M_f.to('kN*m').magnitude:.2f} \\text{{ kNm}} \\\\\n")
    doc.append(f"V_f &= \\frac{{w_f L}}{{2}} = {V_f.to('kN').magnitude:.2f} \\text{{ kN}}\n")
    doc.append("\\end{align}\n")
    doc.append("$$\n")
    doc.append("\n")
    
    # Resistance Calculations (from procedure)
    doc.append("## 3. Resistance Calculations\n")
    doc.append("\n")
    doc.append(procedure.generate_latex())
    doc.append("\n")
    
    # Design Checks
    doc.append("## 4. Design Checks\n")
    doc.append("### Bending Check\n")
    doc.append("$$\n")
    doc.append(f"\\frac{{M_f}}{{M_r}} = \\frac{{{M_f.to('kN*m').magnitude:.2f}}}{{{M_r.to('kN*m').magnitude:.2f}}} = {bending_util:.3f} ")
    if bending_util <= 1.0:
        doc.append("\\le 1.0 \\quad \\checkmark\n")
    else:
        doc.append("> 1.0 \\quad \\text{FAIL}\n")
    doc.append("$$\n")
    doc.append("\n")
    
    doc.append("### Shear Check\n")
    doc.append("$$\n")
    doc.append(f"\\frac{{V_f}}{{V_r}} = \\frac{{{V_f.to('kN').magnitude:.2f}}}{{{V_r.to('kN').magnitude:.2f}}} = {shear_util:.3f} ")
    if shear_util <= 1.0:
        doc.append("\\le 1.0 \\quad \\checkmark\n")
    else:
        doc.append("> 1.0 \\quad \\text{FAIL}\n")
    doc.append("$$\n")
    doc.append("\n")
    
    # Summary
    doc.append("## 5. Summary\n")
    doc.append(f"- **Maximum Utilization:** {max(bending_util, shear_util):.1%}\n")
    doc.append(f"- **Design Status:** **{status}**\n")
    doc.append("\n")
    
    if status == 'PASS':
        doc.append(f"The ${b.magnitude:.0f} \\times {d.magnitude:.0f}$ mm {grade} {species} glulam beam is adequate for the applied loading.\n")
    else:
        doc.append(f"The ${b.magnitude:.0f} \\times {d.magnitude:.0f}$ mm {grade} {species} glulam beam is **NOT** adequate. Consider increasing section size.\n")
    
    doc.append("\n---\n")
    doc.append("*Calculation performed using EIME TimberBeamCalculator*\n")
    
    return "".join(doc)


if __name__ == "__main__":
    main()
