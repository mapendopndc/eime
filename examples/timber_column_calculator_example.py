"""
Timber Column Calculator Example

This example demonstrates the design of a glulam timber column
under axial compression using the TimberColumnCalculator class.
"""

from pint import UnitRegistry
from datetime import datetime

from design.csa_o86_2025.calculators import TimberColumnCalculator
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
    Design a timber column under axial compression using the calculator interface.
    
    This example demonstrates how the TimberColumnCalculator simplifies
    the design process for compression members.
    """
    
    # ==========================================
    # USER INPUTS - Modify these as needed
    # ==========================================
    
    # Column geometry
    height_m = 4.0 * m
    
    # Section properties: 175 x 304 mm glulam
    b = 175 * mm
    d = 304 * mm
    
    # Effective length factors (typically 1.0 for pinned-pinned)
    K_x = 1.0  # Effective length factor for buckling about x-axis
    K_y = 1.0  # Effective length factor for buckling about y-axis
    
    # Effective lengths
    L_ex = K_x * height_m
    L_ey = K_y * height_m
    
    # Applied loads
    dead_load_kN = 80.0 * kN
    live_load_kN = 50.0 * kN
    
    # Material: Douglas Fir-Larch 20f-E
    species = "Douglas Fir-Larch"
    grade = "20f-E"
    
    # Service condition: Dry
    service_condition = "Dry-service conditions"
    
    # Design factors
    K_H = 1.0 * nd  # System factor (single member)
    K_T = 1.0 * nd  # Treatment factor (untreated)
    phi_c = 0.8 * nd  # Compression resistance factor per CSA O86:24
    
    # ==========================================
    # LOAD MATERIAL PROPERTIES FROM TABLES
    # ==========================================
    
    # Load specified strengths from CSA O86-24 Table 7.2
    strengths_table = specified_strengths()
    material_props = strengths_table.data.loc[grade, species]
    
    # Extract material properties with units
    f_c = material_props['f_c'] * MPa
    E = material_props['E'] * MPa
    
    # Load service condition factors from CSA O86-24 Table 7.3
    service_table = service_condition_factors()
    K_Sc = service_table.data.loc['K_Sc', service_condition] * nd
    K_SE = service_table.data.loc['K_SE', service_condition] * nd
    
    # ==========================================
    # PREPARE DESIGN PARAMETERS
    # ==========================================
    
    # Load factors per NBC 2020
    alpha_D = 1.25  # Dead load factor
    alpha_L = 1.5   # Live load factor
    
    # Factored compression load
    P_f = alpha_D * dead_load_kN + alpha_L * live_load_kN
    
    # Load duration percentages (for K_D calculation)
    # Dead load is long-term (100%), live load is standard-term
    P_total = (dead_load_kN + live_load_kN).magnitude
    P_L_percent = (dead_load_kN.magnitude / P_total) * 100 * nd  # Long-term %
    P_S_percent = (live_load_kN.magnitude / P_total) * 100 * nd  # Standard-term %
    
    print("=" * 70)
    print("TIMBER COLUMN DESIGN - CSA O86:24")
    print("=" * 70)
    print(f"\nMaterial: {species} - {grade}")
    print(f"Section:  {b.magnitude:.0f} x {d.magnitude:.0f} mm")
    print(f"Height:   {height_m.to(m).magnitude:.1f} m")
    print(f"\nFactored Load: {P_f.to(kN).magnitude:.1f} kN")
    print(f"  Dead Load:   {dead_load_kN.magnitude:.1f} kN (factored: {(alpha_D * dead_load_kN).to(kN).magnitude:.1f} kN)")
    print(f"  Live Load:   {live_load_kN.magnitude:.1f} kN (factored: {(alpha_L * live_load_kN).to(kN).magnitude:.1f} kN)")
    
    # ==========================================
    # RUN DESIGN USING CALCULATOR
    # ==========================================
    
    calculator = TimberColumnCalculator()
    results = calculator.design(
        # Geometry
        b=b.to(m),
        d=d.to(m),
        L=height_m.to(m),
        L_ex=L_ex.to(mm),
        L_ey=L_ey.to(mm),
        # Material properties
        f_c=f_c,
        E=E,
        # Applied load
        P_f=P_f,
        # Load duration
        P_L_percent=P_L_percent,
        P_S_percent=P_S_percent,
        # Design factors
        K_H=K_H,
        K_Sc=K_Sc,
        K_SE=K_SE,
        K_T=K_T,
        phi_c=phi_c
    )
    
    # ==========================================
    # EXTRACT & DISPLAY RESULTS
    # ==========================================
    
    procedure = calculator.get_procedure()
    
    # Extract resistance results from formulas in the procedure
    P_r_values = []
    for item in procedure.procedure:
        if hasattr(item, 'name') and item.name == 'P_r':
            P_r_values.append(item.result)

    P_r_x = P_r_values[0] if len(P_r_values) > 0 else None  # X-axis
    P_r_y = P_r_values[1] if len(P_r_values) > 1 else None  # Y-axis
    
    # Calculate utilizations
    P_f_N = P_f.to('N')
    
    compression_util_x = (P_f_N / P_r_x).magnitude if P_r_x else float('inf')
    
    # Determine design status
    if compression_util_x <= 1.0:
        status = "PASS ✓"
    else:
        status = "FAIL ✗"
    
    print("\n" + "=" * 70)
    print("DESIGN CHECK RESULTS")
    print("=" * 70)
    print(f"\nCompression Resistance (X-Axis): {P_r_x.to('kN').magnitude:.2f} kN")
    print(f"Compression Utilization:          {compression_util_x:.1%}")
    print(f"\nSTATUS: {status}")
    print("=" * 70)
    
    # ==========================================
    # GENERATE DOCUMENTATION
    # ==========================================
    
    doc = generate_calculation_document(
        species=species,
        grade=grade,
        service_condition=service_condition,
        b=b,
        d=d,
        height_m=height_m,
        L_ex=L_ex,
        L_ey=L_ey,
        f_c=f_c,
        E=E,
        K_Sc=K_Sc,
        K_SE=K_SE,
        K_H=K_H,
        K_T=K_T,
        phi_c=phi_c,
        dead_load_kN=dead_load_kN,
        live_load_kN=live_load_kN,
        alpha_D=alpha_D,
        alpha_L=alpha_L,
        P_f=P_f,
        P_L_percent=P_L_percent,
        P_S_percent=P_S_percent,
        procedure=procedure,
        P_r_x=P_r_x,
        compression_util_x=compression_util_x,
        status=status
    )
    
    # Save to file
    output_filename = "examples/timber_column_calculator_output.md"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(doc)
    
    print(f"\nCalculation document saved to: {output_filename}")


def generate_calculation_document(
    species, grade, service_condition,
    b, d, height_m, L_ex, L_ey,
    f_c, E, K_Sc, K_SE, K_H, K_T, phi_c,
    dead_load_kN, live_load_kN, alpha_D, alpha_L,
    P_f, P_L_percent, P_S_percent,
    procedure, P_r_x, compression_util_x, status
):
    """Generate a formatted calculation document."""
    
    doc = []
    
    # Header
    doc.append("# Timber Column Design Calculation\n")
    doc.append("## Axial Compression - CSA O86:24\n\n")
    doc.append(f"*Calculation Date: {datetime.now().strftime('%B %d, %Y')}*\n\n")
    
    # Design Parameters
    doc.append("## 1. Design Parameters\n\n")
    
    doc.append("### Material\n")
    doc.append(f"- Species: {species}\n")
    doc.append(f"- Grade: {grade}\n")
    doc.append(f"- Service Condition: {service_condition}\n\n")
    
    doc.append("### Geometry\n")
    doc.append(f"- Column Height: {height_m.to(m).magnitude:.2f} m\n")
    doc.append(f"- Section: {b.magnitude:.0f} mm × {d.magnitude:.0f} mm\n")
    doc.append(f"- Effective Length (X-axis): {L_ex.to(m).magnitude:.2f} m\n")
    doc.append(f"- Effective Length (Y-axis): {L_ey.to(m).magnitude:.2f} m\n\n")
    
    doc.append("### Material Properties (CSA O86-24 Table 7.2)\n")
    doc.append(f"- Specified compression strength, f_c = {f_c.magnitude:.1f} MPa\n")
    doc.append(f"- Modulus of elasticity, E = {E.magnitude:.0f} MPa\n\n")
    
    doc.append("### Design Factors\n")
    doc.append(f"- Service condition factor (compression), K_Sc = {K_Sc.magnitude:.2f}\n")
    doc.append(f"- Service condition factor (modulus), K_SE = {K_SE.magnitude:.2f}\n")
    doc.append(f"- System factor, K_H = {K_H.magnitude:.2f}\n")
    doc.append(f"- Treatment factor, K_T = {K_T.magnitude:.2f}\n")
    doc.append(f"- Resistance factor (compression), φ_c = {phi_c.magnitude:.2f}\n\n")
    
    # Applied Forces
    doc.append("## 2. Applied Forces\n\n")
    
    doc.append("### Unfactored Loads\n")
    doc.append(f"- Dead Load: {dead_load_kN.magnitude:.1f} kN\n")
    doc.append(f"- Live Load: {live_load_kN.magnitude:.1f} kN\n\n")
    
    doc.append("### Load Factors (NBC 2020)\n")
    doc.append(f"- Dead load factor, α_D = {alpha_D:.2f}\n")
    doc.append(f"- Live load factor, α_L = {alpha_L:.2f}\n\n")
    
    doc.append("### Factored Compression Load\n")
    doc.append("$$\n")
    doc.append(f"P_f = \\alpha_D \\cdot P_D + \\alpha_L \\cdot P_L = ")
    doc.append(f"{alpha_D:.2f} \\times {dead_load_kN.magnitude:.1f} + ")
    doc.append(f"{alpha_L:.2f} \\times {live_load_kN.magnitude:.1f} = ")
    doc.append(f"{P_f.to(kN).magnitude:.1f} \\text{{ kN}}\n")
    doc.append("$$\n\n")
    
    doc.append("### Load Duration\n")
    doc.append(f"- Long-term load (dead): {P_L_percent:.1f}%\n")
    doc.append(f"- Standard-term load (live): {P_S_percent:.1f}%\n\n")
    
    # Resistance Calculations
    doc.append("## 3. Resistance Calculations\n\n")
    
    # Add LaTeX from procedure
    latex_output = procedure.generate_latex()
    doc.append(latex_output)
    doc.append("\n")
    
    # Design Checks
    doc.append("## 4. Design Checks\n\n")
    
    doc.append("### Compression Check (X-Axis Buckling)\n")
    doc.append("$$\n")
    doc.append(f"\\frac{{P_f}}{{P_r}} = \\frac{{{P_f.to('kN').magnitude:.1f}}}{{{P_r_x.to('kN').magnitude:.2f}}} = {compression_util_x:.3f} ")
    if compression_util_x <= 1.0:
        doc.append("\\le 1.0 \\quad \\checkmark\n")
    else:
        doc.append("> 1.0 \\quad \\text{FAIL}\n")
    doc.append("$$\n\n")
    
    # Summary
    doc.append("## 5. Summary\n\n")
    doc.append(f"**Material:** {species} {grade}\n\n")
    doc.append(f"**Section:** {b.magnitude:.0f} mm × {d.magnitude:.0f} mm\n\n")
    doc.append(f"**Height:** {height_m.to(m).magnitude:.2f} m\n\n")
    doc.append(f"**Factored Load:** {P_f.to(kN).magnitude:.1f} kN\n\n")
    doc.append(f"**Compression Resistance:** {P_r_x.to(kN).magnitude:.2f} kN\n\n")
    doc.append(f"**Utilization:** {compression_util_x:.1%}\n\n")
    doc.append(f"**Design Status:** {status}\n")
    
    return "".join(doc)


if __name__ == "__main__":
    main()
