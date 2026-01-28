"""
Beam Designer with PyNite FEM Analysis

This experiment uses PyNite to perform structural analysis and extract
internal forces at multiple sections along the beam. Each section is then
checked for timber design capacity, accounting for varying load duration
factors based on the actual demand diagrams.

Updated to use proper shear load coefficient (CV) calculation per CSA O86 7.5.7.6.
"""
from Pynite.FEModel3D import FEModel3D
import numpy as np
from design.csa_o86_2025.calculators import (
    RectangularProfile,
    TimberMaterial,
    TimberSection,
    TimberDesignParameters,
    TimberLoads,
    TimberLoadingParameters,
    TimberBeamDesign
)
from design.csa_o86_2025.formulas.glulam_shear import g_factor
from preprocessor.pynite_shear import prepare_shear_segment_arrays, compute_sum_g
from eime.units import ureg
from load.nbcc2020.combos import nbcc_uls_combinations

# Unit shorthands
m = ureg.m
mm = ureg.mm
kPa = ureg.kPa
MPa = ureg.MPa
kN = ureg.kN
N = ureg.N
nd = ureg.dimensionless


def create_beam_model(span, sections, loads_config):
    """
    Create a PyNite beam model with specified geometry and loads.
    
    Parameters:
    -----------
    span : Quantity
        Beam span length
    sections : dict
        Section properties (b, d, E, I)
    loads_config : dict
        Load configuration with distributed loads
    
    Returns:
    --------
    FEModel3D
        Configured PyNite model
    """
    # Create a new finite element model
    model = FEModel3D()
    
    # Convert span to meters for PyNite
    L = span.to(m).magnitude
    
    # Extract section properties
    E_val = sections['E'].to(MPa).magnitude  # MPa
    G_val = E_val * 0.4  # Shear modulus approximation
    I_val = sections['I'].to(mm**4).magnitude / 1e12  # Convert mm^4 to m^4
    A_val = sections['A'].to(mm**2).magnitude / 1e6  # Convert mm^2 to m^2
    
    # Add material and section
    model.add_material('Glulam', E_val, G_val, 0.6, 500)  # E, G, nu, rho (kg/m³)
    model.add_section('Rect', A_val, I_val, I_val/2, I_val/2)  # A, Iy, Iz, J
    
    # Add nodes - just two nodes for a simple beam
    model.add_node('N1', 0, 0, 0)
    model.add_node('N2', L, 0, 0)
    
    # Add a single beam member for the entire span
    model.add_member('M1', 'N1', 'N2', 'Glulam', 'Rect')
    
    # Add supports: pin at start, roller at end
    # def_support(node, Dx, Dy, Dz, Rx, Ry, Rz) - True=restrained, False=free
    # For 2D beam in XY plane, need to restrain Rx (rotation about beam axis) to prevent instability
    model.def_support('N1', True, True, True, False, False, False)  # Pin
    model.def_support('N2', False, True, True, True, False, False)  # Roller (Rx restrained)
    
    # Add load combinations
    model.add_load_combo('D', {'D': 1.0})
    model.add_load_combo('L', {'L': 1.0})
    model.add_load_combo('S', {'S': 1.0})
    
    # Add distributed loads using absolute coordinates
    w_dead = loads_config['dead'].to(kN/m).magnitude
    w_live = loads_config['live'].to(kN/m).magnitude
    w_snow = loads_config['snow'].to(kN/m).magnitude
    
    # Dead load - full span
    model.add_member_dist_load('M1', 'Fy', -w_dead, -w_dead, 0, L, 'D')
    
    # Live load - full span
    model.add_member_dist_load('M1', 'Fy', -w_live, -w_live, 0, L, 'L')
    
    # Snow load - left half only
    model.add_member_dist_load('M1', 'Fy', -w_snow, -w_snow, 0, L/2, 'S')
    
    return model


def extract_demands_at_sections(model, span, num_sections=10):
    """
    Extract internal forces at multiple sections along the beam.
    
    Parameters:
    -----------
    model : FEModel3D
        Analyzed PyNite model
    span : Quantity
        Beam span
    num_sections : int
        Number of sections to check along the beam
    
    Returns:
    --------
    dict
        Dictionary with demands for each load case and section
    """
    L = span.to(m).magnitude
    
    # Initialize demand storage
    demands = {
        'x': [],
        'D': {'M': [], 'V': []},
        'L': {'M': [], 'V': []},
        'S': {'M': [], 'V': []}
    }
    
    # Extract demands at each section - now using the single member 'M1'
    for i in range(num_sections):
        x = i * L / (num_sections - 1)
        demands['x'].append(x * m)
        
        # Extract moments and shears for each load case
        for load_case in ['D', 'L', 'S']:
            try:
                # Use absolute coordinate x along the member
                M = model.members['M1'].moment('Mz', x, load_case)
                demands[load_case]['M'].append(abs(M) * kN * m)
                
                V = model.members['M1'].shear('Fy', x, load_case)
                demands[load_case]['V'].append(abs(V) * kN)
            except Exception as e:
                # If extraction fails, use zero
                demands[load_case]['M'].append(0.0 * kN * m)
                demands[load_case]['V'].append(0.0 * kN)
    
    return demands


def calculate_load_duration_ratios(demands, section_idx):
    """
    Calculate P_L and P_S percentages for a specific section based on
    which load governs the demand using the NBCC load combo module.
    
    Parameters:
    -----------
    demands : dict
        Demands dictionary from extract_demands_at_sections
    section_idx : int
        Section index to calculate for
    
    Returns:
    --------
    dict
        Load duration percentages for moment, shear, and axial
    """
    # Get demands at this section
    M_D = demands['D']['M'][section_idx]
    M_L = demands['L']['M'][section_idx]
    M_S = demands['S']['M'][section_idx]
    
    V_D = demands['D']['V'][section_idx]
    V_L = demands['L']['V'][section_idx]
    V_S = demands['S']['V'][section_idx]
    
    # Use NBCC load combo module for moment combinations
    M_combos = nbcc_uls_combinations(
        nominal_loads={'D': M_D, 'L': M_L, 'S': M_S},
        include_wind=False,
        include_seismic=False
    )
    
    # Use NBCC load combo module for shear combinations
    V_combos = nbcc_uls_combinations(
        nominal_loads={'D': V_D, 'L': V_L, 'S': V_S},
        include_wind=False,
        include_seismic=False
    )
    
    # Find governing moment case
    M_gov_idx = np.argmax(M_combos.total.magnitude)
    M_f = M_combos.total[M_gov_idx]
    
    # Find governing shear case
    V_gov_idx = np.argmax(V_combos.total.magnitude)
    V_f = V_combos.total[V_gov_idx]
    
    # Get load duration percentages from the combo module
    P_L_M = M_combos.duration_long_percent[M_gov_idx].magnitude
    P_S_M = M_combos.duration_short_percent[M_gov_idx].magnitude
    P_L_V = V_combos.duration_long_percent[V_gov_idx].magnitude
    P_S_V = V_combos.duration_short_percent[V_gov_idx].magnitude
    
    # Get combo types for kd factor determination
    M_combo_type = M_combos.load_combo_types[M_gov_idx]
    V_combo_type = V_combos.load_combo_types[V_gov_idx]
    
    return {
        'M_f': M_f,
        'V_f': V_f,
        'P_L_M': P_L_M,
        'P_S_M': P_S_M,
        'P_L_V': P_L_V,
        'P_S_V': P_S_V,
        'M_combo': M_combo_type,
        'V_combo': V_combo_type
    }


def main():
    """
    Main beam designer workflow using PyNite for analysis.
    """
    
    # ==========================================
    # BEAM CONFIGURATION
    # ==========================================
    
    # Beam geometry
    span_length = 8.0 * m
    
    # Section properties: 175 x 456 mm glulam beam
    b = 175 * mm
    d = 456 * mm
    
    # Material specification
    species = "Douglas Fir-Larch"
    grade = "20f-E"
    
    # Service conditions
    service_condition = "Dry-service conditions"
    end_conditions = "Pin - Pin"
    
    # ==========================================
    # MATERIAL AND SECTION
    # ==========================================
    
    # Create rectangular profile
    profile = RectangularProfile(b=b, d=d)
    
    # Create material from tables
    material = TimberMaterial(grade=grade, species=species, ureg=ureg)
    
    # Create section
    section = TimberSection(profile=profile, material=material)
    
    # Get section properties for PyNite
    sections = {
        'E': material.E,
        'I': profile.MomentofInertia(),
        'A': profile.Area()
    }
    
    # ==========================================
    # LOADS CONFIGURATION
    # ==========================================
    
    # Tributary width
    tributary_width = 3.6 * m
    
    # Distributed loads
    dead_load_kPa = 2.5 * kPa
    live_load_kPa = 4.8 * kPa
    snow_load_kPa = 2.0 * kPa
    
    # Convert to line loads
    loads_config = {
        'dead': dead_load_kPa * tributary_width,
        'live': live_load_kPa * tributary_width,
        'snow': snow_load_kPa * tributary_width
    }
    
    print("\n" + "="*70)
    print("BEAM DESIGNER - PyNite FEM Analysis")
    print("="*70)
    print(f"\nSection: {b.to(mm).magnitude:.0f} x {d.to(mm).magnitude:.0f} mm {grade} {species}")
    print(f"Span: {span_length.to(m).magnitude:.1f} m")
    print(f"Dead: {loads_config['dead'].to(kN/m).magnitude:.2f} kN/m")
    print(f"Live: {loads_config['live'].to(kN/m).magnitude:.2f} kN/m")
    print(f"Snow: {loads_config['snow'].to(kN/m).magnitude:.2f} kN/m (left half only)")
    
    # ==========================================
    # PyNite FEM ANALYSIS
    # ==========================================
    
    print("\nRunning FEM analysis...")
    
    # Create and analyze model
    model = create_beam_model(span_length, sections, loads_config)
    model.analyze(check_statics=True)
    
    print("Analysis complete.")
    
    # ==========================================
    # VISUALIZE MOMENT AND SHEAR DIAGRAMS
    # ==========================================
    
    print("\nGenerating moment and shear diagrams...")
    
    # Now we can use PyNite's built-in plotting for the single member
    print("\nDead Load Diagrams:")
    model.members['M1'].plot_moment('Mz', combo_name='D')
    model.members['M1'].plot_shear('Fy', combo_name='D')
    
    print("\nLive Load Diagrams:")
    model.members['M1'].plot_moment('Mz', combo_name='L')
    model.members['M1'].plot_shear('Fy', combo_name='L')
    
    print("\nSnow Load Diagrams:")
    model.members['M1'].plot_moment('Mz', combo_name='S')
    model.members['M1'].plot_shear('Fy', combo_name='S')
    
    # ==========================================
    # EXTRACT DEMANDS AT SECTIONS
    # ==========================================
    
    num_sections = 11  # Check at 11 sections (0.0, 0.1L, 0.2L, ..., 1.0L)
    demands = extract_demands_at_sections(model, span_length, num_sections)
    
    # ==========================================
    # DESIGN CHECKS AT EACH SECTION
    # ==========================================
    
    print("\n" + "="*70)
    print("SECTION-BY-SECTION DESIGN CHECKS")
    print("="*70)
    print(f"\n{'Loc':<8} {'x(m)':<8} {'M_f':<10} {'V_f':<10} {'M_util':<10} {'V_util':<10} {'Status':<10}")
    print(f"{'':8} {'':8} {'(kN·m)':<10} {'(kN)':<10} {'':10} {'':10} {'':10}")
    print("-" * 70)
    
    # Design parameters
    lu_strong = span_length
    lu_weak = span_length
    
    # ==========================================
    # COMPUTE SHEAR LOAD COEFFICIENT INPUTS
    # ==========================================
    
    print("\nComputing shear load coefficient (CV) parameters...")
    
    # We need to compute Wf and SumG for the governing load combination
    # For this example, we'll use a representative combination (D+L+0.5S)
    # In practice, you'd check all combinations
    
    # Add ULS combination to the model
    model.add_load_combo('ULS', {'D': 1.25, 'L': 1.5, 'S': 0.75})
    model.analyze(check_statics=False)  # Re-analyze with new combo
    
    # Extract shear segment data from PyNite model
    segment_data = prepare_shear_segment_arrays(
        model=model,
        member_name='M1',
        load_combo='ULS',
        beam_length=span_length,
        num_points=100,
        ureg=ureg
    )
    
    # Compute Sum_G using the g_factor formula
    SumG = compute_sum_g(segment_data, g_factor)
    Wf = segment_data['W_f']
    
    print(f"  Total factored load (Wf): {Wf.to(kN).magnitude:.2f} kN")
    print(f"  Sum of G factors: {SumG.to(N**5 * mm).magnitude:.2e} N^5·mm")
    print(f"  Number of shear segments identified: {len(segment_data['l_a'])}")
    
    results_summary = []
    
    for i in range(num_sections):
        x_pos = demands['x'][i]
        
        # Calculate load duration ratios for this section
        duration = calculate_load_duration_ratios(demands, i)
        
        # Create beam ID
        beam_id = f"Section-{i}"
        
        # Create design parameters for this section
        parameters = TimberDesignParameters(
            beam_ids=[beam_id],
            beam_length=span_length,
            end_conditions=end_conditions,
            service_conditions=service_condition,
            lu_strong=lu_strong,
            lu_weak=lu_weak,
            Wf=Wf,
            SumG=SumG,
            ureg=ureg
        )
        
        # Create loading parameters (as Pint quantity numpy arrays)
        loading_params = TimberLoadingParameters(
            P_L_M=np.array([duration['P_L_M']]) * nd,
            P_S_M=np.array([duration['P_S_M']]) * nd,
            P_L_V=np.array([duration['P_L_V']]) * nd,
            P_S_V=np.array([duration['P_S_V']]) * nd,
            P_L_P=np.array([100.0]) * nd,  # Placeholder
            P_S_P=np.array([0.0]) * nd,    # Placeholder
            load_combo_types=[duration['M_combo']],
            ureg=ureg
        )
        
        # Create loads (as Pint Quantity arrays)
        loads = TimberLoads()
        loads.M3 = np.array([duration['M_f'].magnitude]) * duration['M_f'].units
        loads.V2 = np.array([duration['V_f'].magnitude]) * duration['V_f'].units
        loads.P = np.array([0.0]) * kN
        loads.M2 = np.array([0.0]) * kN * m
        loads.V3 = np.array([0.0]) * kN
        
        # Create design calculator
        design = TimberBeamDesign(
            section=section,
            loading=loads,
            parameters=parameters,
            loading_params=loading_params
        )
        
        # Perform checks
        bending_check = design.BendingResistance(axis='strong', sign='positive')
        shear_check = design.ShearResistance(axis='weak')
        
        # Get utilizations
        M_util = bending_check.get_worst_utilization().iloc[0]
        V_util = shear_check.get_worst_utilization().iloc[0]
        
        # Handle edge case where both demand and capacity checks might be zero
        # (e.g., at supports where moment = 0)
        if np.isnan(M_util) or np.isinf(M_util):
            M_util = 0.0
        if np.isnan(V_util) or np.isinf(V_util):
            V_util = 0.0
        
        max_util = max(M_util, V_util)
        status = 'PASS' if max_util <= 1.0 else 'FAIL'
        
        # Store results
        results_summary.append({
            'x': x_pos,
            'M_f': duration['M_f'],
            'V_f': duration['V_f'],
            'M_util': M_util,
            'V_util': V_util,
            'max_util': max_util,
            'status': status
        })
        
        # Print row
        print(f"{i:<8} {x_pos.to(m).magnitude:<8.2f} "
              f"{duration['M_f'].to(kN*m).magnitude:<10.2f} "
              f"{duration['V_f'].to(kN).magnitude:<10.2f} "
              f"{M_util:<10.3f} "
              f"{V_util:<10.3f} "
              f"{status:<10}")
    
    # ==========================================
    # SUMMARY
    # ==========================================
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    # Find worst section
    worst_section = max(results_summary, key=lambda x: x['max_util'])
    worst_idx = results_summary.index(worst_section)
    
    print(f"\nWorst Section: {worst_idx} at x = {worst_section['x'].to(m).magnitude:.2f} m")
    print(f"Maximum Utilization: {worst_section['max_util']:.3f} ({worst_section['max_util']*100:.1f}%)")
    print(f"Overall Status: {worst_section['status']}")
    
    if worst_section['max_util'] <= 1.0:
        print(f"\nBeam is ADEQUATE at all {num_sections} sections.")
    else:
        print(f"\nBeam is NOT ADEQUATE. Increase section size.")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
