"""
Streamlit Debug Dashboard for EIME Beam Analysis

A comprehensive debug dashboard for visualizing beam analysis and design
using the full EIME workflow with PyNite FEM analysis.
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from pint import UnitRegistry
from Pynite.FEModel3D import FEModel3D
import warnings

# Suppress division warnings from Pint
warnings.filterwarnings('ignore', 'invalid value encountered in divide', RuntimeWarning)

from preprocessor import Beam, BeamMesh, GeometryMapper, AnalysisMapper, LoadDurationMapper, ParameterAssembler
from preprocessor.analysis import map_pynite_to_stations
from design.csa_o86_2025.calculators.timber_member import (
    RectangularProfile, TimberMaterial, TimberSection,
    TimberDesignParameters, TimberLoads, TimberLoadingParameters, TimberBeamDesign
)
from load.nbcc2020 import nbcc_uls_combinations

# Initialize unit registry
ureg = UnitRegistry()
mm = ureg.mm
m = ureg.m
kN = ureg.kN
MPa = ureg.MPa
kPa = ureg.kPa
nd = ureg.dimensionless


@st.cache_resource
def create_beam_model():
    """Create and analyze simply supported beam model."""
    
    # ==========================================
    # 1. DEFINE BEAM GEOMETRY
    # ==========================================
    
    # Continuous beam: 2 spans of 4m each
    # Bracing every 2m
    beam = Beam(
        support_locations=[0, 4, 8],  # Continuous with middle support
        bracing_locations=[0, 2, 4, 6, 8]  # Bracing every 2m
    )
    
    # ==========================================
    # 2. GENERATE MESH
    # ==========================================
    
    mesh = BeamMesh(
        beam,
        spacing=0.2,  # 200mm spacing
        refine_at_discontinuities=True
    )
    
    # ==========================================
    # 3. DEFINE SECTION AND MATERIAL
    # ==========================================
    
    # 175 x 456 mm glulam beam
    profile = RectangularProfile(b=175*mm, d=456*mm)
    material = TimberMaterial(grade="20f-E", species="Douglas Fir-Larch", ureg=ureg)
    section = TimberSection(profile=profile, material=material)
    
    # ==========================================
    # 4. CREATE PYNITE FEM MODEL
    # ==========================================
    
    model = FEModel3D()
    
    # Material properties
    E_val = material.E.to(MPa).magnitude
    G_val = E_val * 0.4
    
    # Section properties
    I_val = profile.MomentofInertia().to(mm**4).magnitude / 1e12  # m^4
    A_val = profile.Area().to(mm**2).magnitude / 1e6  # m^2
    
    model.add_material('Glulam', E_val, G_val, 0.6, 500)
    model.add_section('Rect', A_val, I_val, I_val/2, I_val/2)
    
    # Add nodes
    model.add_node('N1', 0, 0, 0)
    model.add_node('N2', 4, 0, 0)
    model.add_node('N3', 8, 0, 0)
    
    # Add single continuous member
    model.add_member('M1', 'N1', 'N3', 'Glulam', 'Rect')
    
    # Add supports (pin at ends, roller at middle)
    model.def_support('N1', True, True, True, True, False, False)  # Pin
    model.def_support('N2', False, True, True, True, False, False)  # Roller (middle)
    model.def_support('N3', False, True, True, True, False, False)  # Roller
    
    # ==========================================
    # 5. APPLY LOADS
    # ==========================================
    
    # Distributed loads (kN/m)
    w_dead = 6.0
    w_live = 4.0
    w_snow = 5.0
    
    member_length = 8.0  # Full continuous beam length
    first_span_length = 4.0  # First span only
    
    # Apply dead load to entire beam
    model.add_member_dist_load('M1', 'Fy', -w_dead, -w_dead, 0, member_length, 'D')
    
    # Apply snow load to first span, live load to second span
    model.add_member_dist_load('M1', 'Fy', -w_snow, -w_snow, 0, first_span_length, 'S')
    model.add_member_dist_load('M1', 'Fy', -w_live, -w_live, first_span_length, member_length, 'L')
    
    # Add live load point load on snow side (first span) at midspan
    P_live = 20.0  # kN
    model.add_member_pt_load('M1', 'Fy', -P_live, first_span_length/3, 'L')
    
    # Define load combinations
    load_combos = {
        # Individual load cases (unfactored)
        'D': {'D': 1.0},
        'L': {'L': 1.0},
        'S': {'S': 1.0},
        # Factored combinations
        '1.4D': {'D': 1.4},
        '1.25D+1.5L': {'D': 1.25, 'L': 1.5},
        '1.25D+1.5S': {'D': 1.25, 'S': 1.5},
        '1.25D+1.5L+0.5S': {'D': 1.25, 'L': 1.5, 'S': 0.5},
        '1.25D+0.5L+1.5S': {'D': 1.25, 'L': 0.5, 'S': 1.5},
    }
    
    for combo_name, factors in load_combos.items():
        model.add_load_combo(combo_name, factors)
    
    # ==========================================
    # 6. ANALYZE MODEL
    # ==========================================
    
    model.analyze(check_statics=False)
    
    return {
        'beam': beam,
        'mesh': mesh,
        'section': section,
        'material': material,
        'model': model,
        'load_combos': load_combos,
        'loads': {'D': w_dead, 'L': w_live, 'S': w_snow, 'P_live': P_live}
    }


def get_diagram_data(model, member_names, load_combo, diagram_type, load_combos_dict, num_points=100):
    """Extract diagram data from PyNite model for multiple members."""
    if isinstance(member_names, str):
        member_names = [member_names]
    
    all_x = []
    all_y = []
    x_offset = 0.0
    
    for member_name in member_names:
        member = model.members[member_name]
        L = member.L()
        x = np.linspace(0, L, num_points)
        
        if diagram_type == 'loading':
            # Get distributed loads for this load combination
            y = np.zeros(num_points)
            
            # Check if this is a combination
            if load_combo in load_combos_dict:
                # Apply load combination factors
                combo_factors = load_combos_dict[load_combo]
                for load in member.DistLoads:
                    load_case = load[5]  # Load case name is at index 5
                    if load_case in combo_factors:
                        factor = combo_factors[load_case]
                        # Get load start and end positions
                        x_start = load[3]  # Start position along member
                        x_end = load[4]    # End position along member
                        w1 = load[1]       # Start magnitude (negative for downward)
                        w2 = load[2]       # End magnitude (negative for downward)
                        
                        # Apply load only within its defined range
                        for i, xi in enumerate(x):
                            if x_start <= xi <= x_end:
                                # Linear interpolation for varying loads
                                if x_end > x_start:
                                    w_at_x = w1 + (w2 - w1) * (xi - x_start) / (x_end - x_start)
                                else:
                                    w_at_x = w1
                                y[i] -= w_at_x * factor
            else:
                # Single load case (unfactored)
                for load in member.DistLoads:
                    if load[5] == load_combo:  # Load case name is at index 5
                        # Get load start and end positions
                        x_start = load[3]  # Start position along member
                        x_end = load[4]    # End position along member
                        w1 = load[1]       # Start magnitude (negative for downward)
                        w2 = load[2]       # End magnitude (negative for downward)
                        
                        # Apply load only within its defined range
                        for i, xi in enumerate(x):
                            if x_start <= xi <= x_end:
                                # Linear interpolation for varying loads
                                if x_end > x_start:
                                    w_at_x = w1 + (w2 - w1) * (xi - x_start) / (x_end - x_start)
                                else:
                                    w_at_x = w1
                                y[i] -= w_at_x
        
        elif diagram_type == 'shear':
            y = np.array([member.shear('Fy', xi, load_combo) for xi in x])
        
        elif diagram_type == 'moment':
            y = np.array([member.moment('Mz', xi, load_combo) for xi in x])
        
        else:
            y = np.zeros(num_points)
        
        all_x.append(x + x_offset)
        all_y.append(y)
        x_offset += L
    
    return np.concatenate(all_x), np.concatenate(all_y)


def analyze_station(beam_data, load_combo, station_idx):
    """Analyze a specific station for a given load combo."""
    
    model = beam_data['model']
    mesh = beam_data['mesh']
    beam = beam_data['beam']
    section = beam_data['section']
    active_loads = beam_data['load_combos'].get(load_combo, {})
    
    # Use the same ureg as the material to ensure consistency
    material_ureg = section.material.f_b._REGISTRY
    m = material_ureg.m
    mm = material_ureg.mm
    kN = material_ureg.kN
    nd = material_ureg.dimensionless
    N = material_ureg.N
    
    x_station = mesh.x_stations[station_idx]
    
    # ==========================================
    # Extract demands from PyNite
    # ==========================================
    
    # Get demands for ALL stations first (needed for proper mapper operation)
    all_demands = map_pynite_to_stations(
        model=model,
        member_name='M1',
        x_stations=mesh.x_stations,
        load_combo=load_combo,
        load_cases=['D', 'L', 'S'],
        beam_length=8.0,
        ureg=material_ureg
    )
    
    # ==========================================
    # Map parameters for all stations
    # ==========================================
    
    geom_mapper = GeometryMapper(beam, mesh)
    geom_params = geom_mapper.map()
    
    analysis_mapper = AnalysisMapper(mesh, all_demands, material_ureg)
    analysis_params = analysis_mapper.map()
    
    # Determine which load cases are active in this combination
    active_loads = list(beam_data['load_combos'][load_combo].keys())
    
    duration_mapper = LoadDurationMapper(mesh, analysis_params, active_load_cases=active_loads)
    duration_params = duration_mapper.map()
    
    # ==========================================
    # Extract single station data
    # ==========================================
    
    # Now extract the single station values for display and design
    
    # ==========================================
    # Extract single station data
    # ==========================================
    
    # Now extract the single station values for display and design
    
    assembler = ParameterAssembler(
        beam, mesh,
        geom_params, analysis_params, duration_params,
        ureg=material_ureg,
        beam_id_prefix='SSB'
    )
    params = assembler.assemble()
    
    # ==========================================
    # Create design inputs
    # ==========================================
    
    # Determine load combo type based on active loads
    has_live = 'L' in active_loads
    has_snow = 'S' in active_loads
    
    if has_live or has_snow:
        load_combo_type = 'includes_live'
    else:
        load_combo_type = 'dead_only'
    
    # Extract single station values from arrays
    design_params = TimberDesignParameters(
        beam_ids=[params['beam_ids'][station_idx]],
        beam_length=np.array([geom_params['span_lengths'][station_idx]]) * m,
        end_conditions="Pin - Pin",
        service_conditions="Dry-service conditions",
        lu_strong=np.array([geom_params['lu_strong'][station_idx]]) * m,
        lu_weak=np.array([geom_params['lu_weak'][station_idx]]) * m,
        Wf=np.array([analysis_params['W_f'][station_idx]]) * kN,
        SumG=np.array([analysis_params['Sum_G'][station_idx]]) * kN**5 * mm,
        L_zbg=np.array([analysis_params['L_zbg'][station_idx]]) * m,
        ureg=material_ureg
    )
    
    loads = TimberLoads()
    loads.M3 = np.array([analysis_params['M_f'][station_idx]]) * kN * m
    loads.V2 = np.array([analysis_params['V_f'][station_idx]]) * kN
    loads.P = np.array([analysis_params['P_f'][station_idx]]) * kN
    
    loading_params = TimberLoadingParameters(
        P_L_M=np.array([duration_params['P_L_M'][station_idx]]) * nd,
        P_S_M=np.array([duration_params['P_S_M'][station_idx]]) * nd,
        P_L_V=np.array([duration_params['P_L_V'][station_idx]]) * nd,
        P_S_V=np.array([duration_params['P_S_V'][station_idx]]) * nd,
        P_L_P=np.array([duration_params['P_L_P'][station_idx]]) * nd,
        P_S_P=np.array([duration_params['P_S_P'][station_idx]]) * nd,
        load_combo_types=[load_combo_type],
        ureg=material_ureg
    )
    
    # ==========================================
    # Run design
    # ==========================================
    
    design = TimberBeamDesign(
        section=section,
        loading=loads,
        parameters=design_params,
        loading_params=loading_params
    )
    
    bending_proc = design.BendingResistance(axis='strong', sign='pos')
    shear_proc = design.ShearResistance(axis='strong')
    
    return {
        'x_station': x_station,
        'active_loads': active_loads,
        'demands': {
            'M_f': all_demands['M_f'][station_idx],
            'V_f': all_demands['V_f'][station_idx],
            'P_f': all_demands['P_f'][station_idx],
            'W_f': all_demands['W_f'][station_idx],
            'Sum_G': all_demands['Sum_G'][station_idx],
        },
        'preprocessing': {
            'span_length': geom_params['span_lengths'][station_idx],
            'lu_strong': geom_params['lu_strong'][station_idx],
            'lu_weak': geom_params['lu_weak'][station_idx],
            'L_zbg': analysis_params['L_zbg'][station_idx],
            'P_L_M': duration_params['P_L_M'][station_idx],
            'P_S_M': duration_params['P_S_M'][station_idx],
            'P_L_V': duration_params['P_L_V'][station_idx],
            'P_S_V': duration_params['P_S_V'][station_idx],
            'governing_Ps_M': duration_params.get('governing_Ps_M', ['N/A']*len(duration_params['P_S_M']))[station_idx],
            'governing_Ps_V': duration_params.get('governing_Ps_V', ['N/A']*len(duration_params['P_S_V']))[station_idx],
            'governing_Ps_P': duration_params.get('governing_Ps_P', ['N/A']*len(duration_params['P_S_P']))[station_idx],
            'M_D': all_demands['M_D'][station_idx],
            'M_L': all_demands['M_L'][station_idx],
            'M_S': all_demands['M_S'][station_idx],
            'V_D': all_demands['V_D'][station_idx],
            'V_L': all_demands['V_L'][station_idx],
            'V_S': all_demands['V_S'][station_idx],
            'l_a': analysis_params['l_a'][station_idx],
            'l_b': analysis_params['l_b'][station_idx],
        },
        'design': {
            'bending_proc': bending_proc,
            'shear_proc': shear_proc,
        },
        'results': {
            'M_r': bending_proc.results.get('M_r', [None])[0] if 'M_r' in bending_proc.results and hasattr(bending_proc.results['M_r'], '__len__') else bending_proc.results.get('M_r', None),
            'V_r': shear_proc.results.get('V_r', [None])[0] if 'V_r' in shear_proc.results and hasattr(shear_proc.results['V_r'], '__len__') else shear_proc.results.get('V_r', None),
        }
    }


def calculate_all_resistances(beam_data, load_combos):
    """Calculate resistances for all stations and all load combinations in batch."""
    model = beam_data['model']
    mesh = beam_data['mesh']
    beam = beam_data['beam']
    section = beam_data['section']
    
    # Use the same ureg as the material to ensure consistency
    material_ureg = section.material.f_b._REGISTRY
    m = material_ureg.m
    mm = material_ureg.mm
    kN = material_ureg.kN
    nd = material_ureg.dimensionless
    
    all_resistances = {}
    
    # Process all load combinations
    for load_combo in load_combos:
        # ==========================================
        # Extract demands from PyNite for ALL stations at once
        # ==========================================
        
        all_demands = map_pynite_to_stations(
            model=model,
            member_name='M1',
            x_stations=mesh.x_stations,
            load_combo=load_combo,
            load_cases=['D', 'L', 'S'],
            beam_length=8.0,
            ureg=material_ureg
        )
    
        # ==========================================
        # Map parameters for ALL stations at once
        # ==========================================
        
        geom_mapper = GeometryMapper(beam, mesh)
        geom_params = geom_mapper.map()
        
        analysis_mapper = AnalysisMapper(mesh, all_demands, material_ureg)
        analysis_params = analysis_mapper.map()
        
        # Determine which load cases are active in this combination
        active_load_cases = list(beam_data['load_combos'][load_combo].keys())
        
        duration_mapper = LoadDurationMapper(mesh, analysis_params, active_load_cases=active_load_cases)
        duration_params = duration_mapper.map()
        
        # ==========================================
        # Assemble parameters for ALL stations
        # ==========================================
        
        assembler = ParameterAssembler(
            beam, mesh,
            geom_params, analysis_params, duration_params,
            ureg=material_ureg,
            beam_id_prefix='SSB'
        )
        params = assembler.assemble()
        
        # ==========================================
        # Determine load combo type
        # ==========================================
        
        has_live = 'L' in active_load_cases
        has_snow = 'S' in active_load_cases
        
        if has_live or has_snow:
            load_combo_type = 'includes_live'
        else:
            load_combo_type = 'dead_only'
        
        # ==========================================
        # Create design inputs for ALL stations
        # ==========================================
        
        num_stations = len(mesh.x_stations)
        
        design_params = TimberDesignParameters(
            beam_ids=params['beam_ids'],
            beam_length=np.array(geom_params['span_lengths']) * m,
            end_conditions="Pin - Pin",
            service_conditions="Dry-service conditions",
            lu_strong=np.array(geom_params['lu_strong']) * m,
            lu_weak=np.array(geom_params['lu_weak']) * m,
            Wf=np.array(analysis_params['W_f']) * kN,
            SumG=np.array(analysis_params['Sum_G']) * kN**5 * mm,
            L_zbg=np.array(analysis_params['L_zbg']) * m,
            ureg=material_ureg
        )
        
        loads = TimberLoads()
        loads.M3 = np.array(analysis_params['M_f']) * kN * m
        loads.V2 = np.array(analysis_params['V_f']) * kN
        loads.P = np.array(analysis_params['P_f']) * kN
        
        loading_params = TimberLoadingParameters(
            P_L_M=np.array(duration_params['P_L_M']) * nd,
            P_S_M=np.array(duration_params['P_S_M']) * nd,
            P_L_V=np.array(duration_params['P_L_V']) * nd,
            P_S_V=np.array(duration_params['P_S_V']) * nd,
            P_L_P=np.array(duration_params['P_L_P']) * nd,
            P_S_P=np.array(duration_params['P_S_P']) * nd,
            load_combo_types=[load_combo_type] * num_stations,
            ureg=material_ureg
        )
        
        # ==========================================
        # Run design for ALL stations at once
        # ==========================================
        
        design = TimberBeamDesign(
            section=section,
            loading=loads,
            parameters=design_params,
            loading_params=loading_params
        )
        
        bending_proc = design.BendingResistance(axis='strong', sign='pos')
        shear_proc = design.ShearResistance(axis='strong')
        
        # ==========================================
        # Extract resistance arrays
        # ==========================================
        
        M_r_array = bending_proc.results.get('M_r', np.zeros(num_stations))
        V_r_array = shear_proc.results.get('V_r', np.zeros(num_stations))
        
        # Convert to magnitudes for plotting
        if hasattr(M_r_array, 'to'):
            M_r_values = [M_r_array[i].to(kN*m).magnitude for i in range(num_stations)]
        else:
            M_r_values = [0] * num_stations
        
        if hasattr(V_r_array, 'to'):
            V_r_values = [V_r_array[i].to(kN).magnitude for i in range(num_stations)]
        else:
            V_r_values = [0] * num_stations
        
        # Store results for this load combo
        all_resistances[load_combo] = {
            'x_stations': mesh.x_stations.tolist() if hasattr(mesh.x_stations, 'tolist') else list(mesh.x_stations),
            'M_r': M_r_values,
            'V_r': V_r_values
        }
    
    return all_resistances


def main():
    """Main Streamlit app."""
    
    st.set_page_config(page_title="EIME Beam Debug Dashboard", layout="wide")
    
    st.title("🔍 EIME Beam Analysis Debug Dashboard")
    st.markdown("---")
    
    # ==========================================
    # CREATE MODEL
    # ==========================================
    
    with st.spinner("Creating beam model..."):
        beam_data = create_beam_model()
    
    model = beam_data['model']
    mesh = beam_data['mesh']
    load_combos = list(beam_data['load_combos'].keys())
    
    # ==========================================
    # TOP CONTROLS
    # ==========================================
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_combo = st.selectbox(
            "Load Combination",
            options=load_combos,
            index=3  # Default to '1.25D+1.5L+0.5S'
        )
    
    with col2:
        diagram_type = st.selectbox(
            "Diagram Type",
            options=['loading', 'shear', 'moment'],
            format_func=lambda x: x.capitalize()
        )
    
    # ==========================================
    # CALCULATE RESISTANCES FOR ALL LOAD COMBOS (cached)
    # ==========================================
    
    if diagram_type in ['shear', 'moment']:
        # Cache the resistances calculation in session state
        if 'all_resistances' not in st.session_state:
            with st.spinner("Calculating resistances for all load combinations..."):
                st.session_state.all_resistances = calculate_all_resistances(beam_data, load_combos)
        
        # Get resistances for the selected combo
        resistances = st.session_state.all_resistances.get(selected_combo, {})
    
    # ==========================================
    # DIAGRAM DISPLAY
    # ==========================================
    
    st.subheader(f"{diagram_type.capitalize()} Diagram - {selected_combo}")
    
    x_data, y_data = get_diagram_data(model, 'M1', selected_combo, diagram_type, beam_data['load_combos'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode='lines',
        name=diagram_type.capitalize(),
        line=dict(width=3, color='#1f77b4')
    ))
    
    # Add support markers
    fig.add_trace(go.Scatter(
        x=[0, 4, 8],
        y=[0, 0, 0],
        mode='markers',
        name='Supports',
        marker=dict(size=12, color='red', symbol='triangle-up')
    ))
    
    # Add resistance line series for moment and shear diagrams
    if diagram_type == 'moment' and 'resistances' in locals():
        # Add moment resistance as a line series
        fig.add_trace(go.Scatter(
            x=resistances['x_stations'],
            y=resistances['M_r'],
            mode='lines',
            name='M_r (Resistance)',
            line=dict(width=2, color='red', dash='dash')
        ))
    
    elif diagram_type == 'shear' and 'resistances' in locals():
        # Add shear resistance as line series (positive and negative)
        fig.add_trace(go.Scatter(
            x=resistances['x_stations'],
            y=resistances['V_r'],
            mode='lines',
            name='V_r (Resistance)',
            line=dict(width=2, color='red', dash='dash')
        ))
        # Add negative resistance line for shear
        fig.add_trace(go.Scatter(
            x=resistances['x_stations'],
            y=[-v for v in resistances['V_r']],
            mode='lines',
            name='-V_r (Resistance)',
            line=dict(width=2, color='red', dash='dash'),
            showlegend=False
        ))
    
    # Add bracing markers
    bracing = beam_data['beam'].bracing_locations
    fig.add_trace(go.Scatter(
        x=bracing,
        y=[0] * len(bracing),
        mode='markers',
        name='Bracing',
        marker=dict(size=8, color='green', symbol='diamond')
    ))
    
    # Add segment annotations for shear diagram
    if diagram_type == 'shear':
        try:
            from preprocessor.pynite_shear import prepare_shear_segment_arrays
            
            material_ureg = beam_data['section'].material.f_b._REGISTRY
            m = material_ureg.m
            
            # Process both members
            segment_counter = 0
            x_offset = 0.0
            y_min, y_max = min(y_data), max(y_data)
            
            for member_name in ['M1']:
                member = model.members[member_name]
                member_length = member.L()
                
                segment_data = prepare_shear_segment_arrays(
                    model=model,
                    member_name=member_name,
                    load_combo=selected_combo,
                    beam_length=member_length * m,
                    num_points=401,  # 401 points for 4m span = 0.01m (10mm) spacing
                    ureg=material_ureg
                )
                
                # Get segment boundaries
                cumulative_x = 0
                
                for i, l_a in enumerate(segment_data['l_a']):
                    l_a_val = l_a.to(m).magnitude
                    segment_counter += 1
                    
                    # Add vertical line at segment start
                    if i == 0:
                        fig.add_vline(
                            x=x_offset + cumulative_x,
                            line_dash="dot",
                            line_color="gray",
                            opacity=0.5
                        )
                    
                    # Calculate midpoint for label
                    segment_midpoint = x_offset + cumulative_x + l_a_val / 2
                    
                    # Add annotation at segment midpoint
                    fig.add_annotation(
                        x=segment_midpoint,
                        y=y_max if y_max > 0 else y_min,
                        text=f"Seg {segment_counter}",
                        showarrow=False,
                        yshift=10,
                        font=dict(size=10, color="purple"),
                        bgcolor="rgba(255,255,255,0.8)",
                        borderpad=2
                    )
                    
                    # Add vertical line at segment end
                    cumulative_x += l_a_val
                    fig.add_vline(
                        x=x_offset + cumulative_x,
                        line_dash="dot",
                        line_color="gray",
                        opacity=0.5
                    )
                
                x_offset += member_length
                
        except Exception as e:
            # Display error for debugging
            st.error(f"Error adding segment annotations: {e}")
            pass
    
    fig.update_layout(
        xaxis_title="Position (m)",
        yaxis_title="Value" if diagram_type == 'loading' else ("Shear (kN)" if diagram_type == 'shear' else "Moment (kN·m)"),
        height=400,
        hovermode='x unified',
        showlegend=True
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # ==========================================
    # STATION SELECTOR
    # ==========================================
    
    st.markdown("---")
    
    # Initialize default station index if not set
    if 'station_idx' not in st.session_state:
        st.session_state.station_idx = len(mesh.x_stations) // 2
    
    station_idx = st.slider(
        "Select Station",
        min_value=0,
        max_value=len(mesh.x_stations) - 1,
        value=st.session_state.station_idx,
        key='station_slider',
        help=f"Station at x = {mesh.x_stations[st.session_state.station_idx]:.3f} m"
    )
    
    # Update session state
    st.session_state.station_idx = station_idx
    
    # ==========================================
    # STATION ANALYSIS
    # ==========================================
    
    with st.spinner(f"Analyzing station {station_idx}..."):
        station_data = analyze_station(beam_data, selected_combo, station_idx)
    
    st.info(f"📍 Station {station_idx} at x = {station_data['x_station']:.3f} m")
    
    # ==========================================
    # TABS FOR DETAILED INFORMATION
    # ==========================================
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Analysis",
        "⚙️ Preprocessing",
        "🔧 Design",
        "✅ Results"
    ])
    
    with tab1:
        st.subheader("Factored Loads & Demands")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Factored Moment (M_f)", f"{station_data['demands']['M_f']:.2f} kN·m")
            st.metric("Factored Shear (V_f)", f"{station_data['demands']['V_f']:.2f} kN")
        
        with col2:
            st.metric("Factored Axial (P_f)", f"{station_data['demands']['P_f']:.2f} kN")
            st.metric("Total Load (W_f)", f"{station_data['demands']['W_f']:.2f} kN")
        
        with col3:
            st.metric("Sum G", f"{station_data['demands']['Sum_G']:.2e}")
        
        st.markdown("---")
        st.write("**Load Combination:**", selected_combo)
        st.write("**Load Case Breakdown:**")
        for load_type, value in beam_data['loads'].items():
            factor = beam_data['load_combos'][selected_combo].get(load_type, 0)
            if factor > 0:
                st.write(f"- {load_type}: {value:.1f} kN/m × {factor:.2f} = {value * factor:.2f} kN/m")
    
    with tab2:
        st.subheader("Station Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Geometry:**")
            st.write(f"- Span length: {station_data['preprocessing']['span_length']:.2f} m")
            st.write(f"- L_u (strong): {station_data['preprocessing']['lu_strong']:.2f} m")
            st.write(f"- L_u (weak): {station_data['preprocessing']['lu_weak']:.2f} m")
            st.write(f"- **L_zbg (zero moment segment)**: {station_data['preprocessing']['L_zbg']:.3f} m")
            st.caption("L_zbg: Distance between inflection points (used for K_Zbg bending size factor)")
        
        with col2:
            st.write("**Load Duration Factors:**")
            
            # Determine which load cases are active in this combination
            active_loads = beam_data['load_combos'].get(selected_combo, {})
            has_live = 'L' in active_loads
            has_snow = 'S' in active_loads
            
            # Always show duration factors (will be 0 when not applicable)
            st.write(f"- P_L (Dead proportion - Moment): {station_data['preprocessing']['P_L_M']:.3f}")
            st.write(f"- P_S (Live/Snow proportion - Moment): {station_data['preprocessing']['P_S_M']:.3f}")
            
            # Only show governing load type if both Live and Snow are present
            if has_live and has_snow:
                gov_m = station_data['preprocessing'].get('governing_Ps_M', 'N/A')
                st.write(f"  → **Governing:** {gov_m}")
            elif has_live:
                st.write(f"  → **Governing:** Live")
            elif has_snow:
                st.write(f"  → **Governing:** Snow")
            elif not has_live and not has_snow:
                st.write(f"  → **Governing:** N/A (Dead load only)")
            
            st.write(f"- P_L (Dead proportion - Shear): {station_data['preprocessing']['P_L_V']:.3f}")
            st.write(f"- P_S (Live/Snow proportion - Shear): {station_data['preprocessing']['P_S_V']:.3f}")
            
            # Only show governing load type if both Live and Snow are present
            if has_live and has_snow:
                gov_v = station_data['preprocessing'].get('governing_Ps_V', 'N/A')
                st.write(f"  → **Governing:** {gov_v}")
            elif has_live:
                st.write(f"  → **Governing:** Live")
            elif has_snow:
                st.write(f"  → **Governing:** Snow")
            elif not has_live and not has_snow:
                st.write(f"  → **Governing:** N/A (Dead load only)")
        
        st.markdown("---")
        
        # Load case demands
        st.subheader("Load Case Demands (Unfactored)")
        
        # Determine which load cases are active in this combination
        active_loads = beam_data['load_combos'].get(selected_combo, {})
        has_dead = 'D' in active_loads
        has_live = 'L' in active_loads
        has_snow = 'S' in active_loads
        
        # Create columns based on active loads
        active_columns = []
        if has_dead:
            active_columns.append('D')
        if has_live:
            active_columns.append('L')
        if has_snow:
            active_columns.append('S')
        
        if len(active_columns) == 1:
            col1 = st.columns(1)[0]
            cols = [col1]
        elif len(active_columns) == 2:
            col1, col2 = st.columns(2)
            cols = [col1, col2]
        else:
            col1, col2, col3 = st.columns(3)
            cols = [col1, col2, col3]
        
        for idx, load_type in enumerate(active_columns):
            with cols[idx]:
                if load_type == 'D':
                    st.write("**Dead Load (D):**")
                    st.write(f"- M_D: {station_data['preprocessing']['M_D']:.2f} kN·m")
                    st.write(f"- V_D: {station_data['preprocessing']['V_D']:.2f} kN")
                elif load_type == 'L':
                    st.write("**Live Load (L):**")
                    st.write(f"- M_L: {station_data['preprocessing']['M_L']:.2f} kN·m")
                    st.write(f"- V_L: {station_data['preprocessing']['V_L']:.2f} kN")
                elif load_type == 'S':
                    st.write("**Snow Load (S):**")
                    st.write(f"- M_S: {station_data['preprocessing']['M_S']:.2f} kN·m")
                    st.write(f"- V_S: {station_data['preprocessing']['V_S']:.2f} kN")
        
        st.markdown("---")
        
        # Shear segment parameters
        st.subheader("Shear Coefficient (C_v) Parameters")
        
        st.write("**All values from AnalysisMapper for this station:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Shear Loads:**")
            st.write(f"- W_f: {station_data['demands']['W_f']:.2f} kN")
            st.write(f"- Sum_G: {station_data['demands']['Sum_G']:.2e}")
        
        with col2:
            st.write("**Segment Lengths:**")
            st.write(f"- l_a: {station_data['preprocessing']['l_a']:.3f} m")
            st.write(f"- l_b: {station_data['preprocessing']['l_b']:.3f} m")
        
        # Show detailed segment breakdown for the segment containing this station
        with st.expander("View G Factor Parameters for This Station's Segment"):
            from preprocessor.pynite_shear import prepare_shear_segment_arrays, compute_sum_g
            from design.csa_o86_2025.formulas.glulam_shear import g_factor
            
            # Get unit registry from beam_data
            material_ureg = beam_data['section'].material.f_b._REGISTRY
            m = material_ureg.m
            kN = material_ureg.kN
            model = beam_data['model']
            
            try:
                # Process both members and combine segment data
                all_l_a = []
                all_V_A = []
                all_V_B = []
                all_V_C = []
                total_W_f = 0 * kN
                total_Sum_G = 0
                x_offset = 0.0
                
                for member_name in ['M1']:
                    member = model.members[member_name]
                    member_length = member.L()
                    
                    segment_data = prepare_shear_segment_arrays(
                        model=model,
                        member_name=member_name,
                        load_combo=selected_combo,
                        beam_length=member_length * m,
                        num_points=401,  # 401 points for 4m span = 0.01m (10mm) spacing
                        ureg=material_ureg
                    )
                    
                    all_l_a.extend(segment_data['l_a'])
                    all_V_A.extend(segment_data['V_A'])
                    all_V_B.extend(segment_data['V_B'])
                    all_V_C.extend(segment_data['V_C'])
                    total_W_f += segment_data['W_f']
                    
                    Sum_G = compute_sum_g(segment_data, g_factor)
                    total_Sum_G += Sum_G.magnitude
                
                # Find which segment contains the current station
                x_station = station_data['x_station']
                cumulative_x = 0.0
                station_segment_idx = None
                
                for i, l_a in enumerate(all_l_a):
                    l_a_val = l_a.to(m).magnitude
                    segment_end = cumulative_x + l_a_val
                    
                    if cumulative_x <= x_station <= segment_end:
                        station_segment_idx = i
                        break
                    
                    cumulative_x = segment_end
                
                if station_segment_idx is not None:
                    i = station_segment_idx
                    st.write(f"**Station is in Segment {i+1} (of {len(all_l_a)} total segments)**")
                    st.write(f"**Total W_f:** {total_W_f.to(kN).magnitude:.2f} kN")
                    st.write(f"**Total Sum(G):** {total_Sum_G:.2e}")
                    
                    st.markdown("---")
                    
                    l_a = all_l_a[i]
                    V_A = all_V_A[i]
                    V_B = all_V_B[i]
                    V_C = all_V_C[i]
                    
                    # Extract magnitudes
                    l_a_val = l_a.to(m).magnitude
                    V_A_val = V_A.to(kN).magnitude
                    V_B_val = V_B.to(kN).magnitude
                    V_C_val = V_C.to(kN).magnitude
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    with col_a:
                        st.metric("l_a", f"{l_a_val:.2f} m")
                    with col_b:
                        st.metric("V_A (start)", f"{V_A_val:.1f} kN")
                    with col_c:
                        st.metric("V_B (end)", f"{V_B_val:.1f} kN")
                    with col_d:
                        st.metric("V_C (center)", f"{V_C_val:.1f} kN")
                    
                    # Calculate G for this segment
                    G = g_factor(l_a=l_a, V_A=V_A, V_B=V_B, V_C=V_C)
                    G_val = G.result.magnitude
                    st.write(f"**G factor:** {G_val:.2e}")
                else:
                    st.warning(f"Could not determine which segment contains station at x = {x_station:.3f} m")
            
            except Exception as e:
                st.error(f"Error extracting segment details: {e}")
        
        st.markdown("---")
        st.write("**Section Properties:**")
        st.write(f"- Width (b): 175 mm")
        st.write(f"- Depth (d): 456 mm")
        st.write(f"- Area: {beam_data['section'].profile.Area().to(mm**2).magnitude:.0f} mm²")
        st.write(f"- I: {beam_data['section'].profile.MomentofInertia().to(mm**4).magnitude:.2e} mm⁴")
        
        st.write("**Material:**")
        st.write(f"- Grade: 20f-E Douglas Fir-Larch")
        st.write(f"- f_b: {beam_data['material'].f_b.to(MPa).magnitude:.1f} MPa")
        st.write(f"- f_v: {beam_data['material'].f_v.to(MPa).magnitude:.2f} MPa")
        st.write(f"- E: {beam_data['material'].E.to(MPa).magnitude:.0f} MPa")
    
    with tab3:
        st.subheader("Design Calculations")
        
        bending_proc = station_data['design']['bending_proc']
        shear_proc = station_data['design']['shear_proc']
        
        # Generate full LaTeX documentation for bending
        st.write("**Bending Resistance Procedure:**")
        bending_latex = bending_proc.generate_latex(index=0)
        st.markdown(bending_latex)
        
        st.markdown("---")
        
        # Generate full LaTeX documentation for shear
        st.write("**Shear Resistance Procedure:**")
        shear_latex = shear_proc.generate_latex(index=0)
        st.markdown(shear_latex)
    
    with tab4:
        st.subheader("Design Results")
        
        M_f = station_data['demands']['M_f']
        V_f = station_data['demands']['V_f']
        M_r = station_data['results']['M_r']
        V_r = station_data['results']['V_r']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Bending Check:**")
            if M_r is not None:
                M_r_val = M_r.to(kN*m).magnitude
                util_M = (M_f / M_r_val) * 100
                st.metric("Moment Resistance (M_r)", f"{M_r_val:.2f} kN·m")
                st.metric("Utilization", f"{util_M:.1f}%", 
                         delta=None,
                         delta_color="inverse" if util_M <= 100 else "normal")
                
                if util_M <= 100:
                    st.success("✅ PASS")
                else:
                    st.error("❌ FAIL")
        
        with col2:
            st.write("**Shear Check:**")
            if V_r is not None:
                V_r_val = V_r.to(kN).magnitude
                util_V = (abs(V_f) / V_r_val) * 100
                st.metric("Shear Resistance (V_r)", f"{V_r_val:.2f} kN")
                st.metric("Utilization", f"{util_V:.1f}%",
                         delta=None,
                         delta_color="inverse" if util_V <= 100 else "normal")
                
                if util_V <= 100:
                    st.success("✅ PASS")
                else:
                    st.error("❌ FAIL")
        
        st.markdown("---")
        
        # Overall status
        if M_r is not None and V_r is not None:
            max_util = max(util_M, util_V)
            st.write(f"**Maximum Utilization:** {max_util:.1f}%")
            
            if max_util <= 100:
                st.success("🎉 Station PASSES all checks!")
            else:
                st.error("⚠️ Station FAILS - requires larger section or reduced loads")


if __name__ == "__main__":
    main()
