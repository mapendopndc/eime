"""
Streamlit Debug Dashboard for EIME Beam Analysis

A comprehensive debug dashboard for visualizing beam analysis and design
using the full EIME workflow with PyNite FEM analysis.
"""

import streamlit as st
import numpy as np
from pint import UnitRegistry
import warnings
import json
from pathlib import Path

# Suppress division warnings from Pint
warnings.filterwarnings('ignore', 'invalid value encountered in divide', RuntimeWarning)

from preprocessor import GeometryMapper, AnalysisMapper, LoadDurationMapper, ParameterAssembler
from preprocessor.pynite_csa_mapper import map_pynite_to_stations
from design.csa_o86_2025.calculators.timber_member import (
    TimberDesignParameters, TimberLoads, TimberLoadingParameters, TimberBeamDesign
)

# Import new modular components
from model_builder import ModelBuilder, ModelConfig, BeamConfig, SectionConfig, LoadConfig, LoadCombinationConfig, create_default_model
from visualization import get_diagram_data, create_diagram_figure, add_shear_segment_annotations

# Initialize unit registry
ureg = UnitRegistry()
mm = ureg.mm
m = ureg.m
kN = ureg.kN
MPa = ureg.MPa
kPa = ureg.kPa
nd = ureg.dimensionless

@st.cache_data
def load_glulam_table():
    """Load glulam table from JSON file."""
    table_path = Path(__file__).parent.parent.parent / "design" / "csa_o86_2025" / "tables" / "CSA O86-24_T7-2.json"
    with open(table_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@st.cache_resource
def create_beam_model(_config: ModelConfig = None, cache_key: str = "default"):
    """Create and analyze beam model from configuration.
    
    Args:
        _config: ModelConfig object (prefixed with _ to exclude from cache key)
        cache_key: Explicit cache key based on config values
    """
    if _config is None:
        # Use default configuration
        return create_default_model(ureg)
    else:
        # Use custom configuration
        builder = ModelBuilder(_config, ureg)
        return builder.build()


def get_member_names(beam_data):
    """Extract member names from model based on beam configuration."""
    num_supports = len(beam_data['config'].beam.support_locations)
    num_members = num_supports - 1
    return [f'M{i+1}' for i in range(num_members)]


def get_total_beam_length(beam_data):
    """Get total beam length from configuration."""
    support_locs = beam_data['config'].beam.support_locations
    return support_locs[-1] - support_locs[0]



def analyze_station(beam_data, design_data, load_combo, station_idx):
    """Extract analysis for a specific station from pre-calculated design data."""
    
    mesh = beam_data['mesh']
    material_ureg = beam_data['section'].material.f_b_pos._REGISTRY
    kN = material_ureg.kN
    m = material_ureg.m
    
    x_station = mesh.x_stations[station_idx]
    
    # Get pre-calculated data for this load combo
    combo_data = design_data[load_combo]
    all_demands = combo_data['all_demands']
    geom_params = combo_data['geom_params']
    analysis_params = combo_data['analysis_params']
    duration_params = combo_data['duration_params']
    active_loads = combo_data['active_loads']
    bending_proc = combo_data['bending_proc']
    shear_proc = combo_data['shear_proc']
    M_r_array = combo_data['M_r_array']
    V_r_array = combo_data['V_r_array']
    
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
        },
        'design': {
            'bending_proc': bending_proc,
            'shear_proc': shear_proc,
        },
        'results': {
            'M_r': M_r_array[station_idx] if hasattr(M_r_array, '__getitem__') else M_r_array,
            'V_r': V_r_array[station_idx] if hasattr(V_r_array, '__getitem__') else V_r_array,
        }
    }


def calculate_all_design_data(beam_data, load_combos):
    """Calculate complete design data for all stations and all load combinations in batch.
    
    This runs TimberBeamDesign once for each load combination and caches all results.
    """
    model = beam_data['model']
    mesh = beam_data['mesh']
    beam = beam_data['beam']
    section = beam_data['section']
    
    # Use the same ureg as the material to ensure consistency
    material_ureg = section.material.f_b_pos._REGISTRY
    m = material_ureg.m
    mm = material_ureg.mm
    kN = material_ureg.kN
    nd = material_ureg.dimensionless
    
    # Get beam length, member names, and support locations
    beam_length = get_total_beam_length(beam_data)
    member_names = get_member_names(beam_data)
    support_locs = beam_data['config'].beam.support_locations
    
    # ==========================================
    # Calculate geometry parameters ONCE (load-independent)
    # ==========================================
    geom_mapper = GeometryMapper(beam, mesh)
    geom_params = geom_mapper.map()
    
    all_design_data = {}
    
    # Process all load combinations
    for load_combo in load_combos:
        # Extract demands from PyNite for ALL members and combine
        num_stations = len(mesh.x_stations)
        all_demands = {
            'M_f': np.zeros(num_stations),
            'V_f': np.zeros(num_stations),
            'P_f': np.zeros(num_stations),
            'W_f': np.zeros(num_stations),
            'Sum_G': np.zeros(num_stations),
            'M_D': np.zeros(num_stations),
            'M_L': np.zeros(num_stations),
            'M_S': np.zeros(num_stations),
            'V_D': np.zeros(num_stations),
            'V_L': np.zeros(num_stations),
            'V_S': np.zeros(num_stations),
            'l_a': np.zeros(num_stations),
            'L_zbg': np.zeros(num_stations),
        }
        
        # Process each member
        for i, member_name in enumerate(member_names):
            member_start = support_locs[i]
            member_end = support_locs[i + 1]
            member_length = member_end - member_start
            
            # Find stations that belong to this member
            member_stations_mask = (mesh.x_stations >= member_start) & (mesh.x_stations <= member_end)
            member_station_indices = np.where(member_stations_mask)[0]
            
            if len(member_station_indices) == 0:
                continue
            
            # Get local x-coordinates for this member
            local_x_stations = mesh.x_stations[member_station_indices] - member_start
            
            # Extract demands for this member
            member_demands = map_pynite_to_stations(
                model=model,
                member_name=member_name,
                x_stations=local_x_stations,
                load_combo=load_combo,
                load_cases=['D', 'L', 'S'],
                beam_length=member_length * m,
                ureg=material_ureg
            )
            
            # Copy demands to combined arrays
            for key in all_demands.keys():
                if key in member_demands:
                    all_demands[key][member_station_indices] = member_demands[key]
    
        # ==========================================
        # Map parameters for ALL stations at once
        # ==========================================
        # Note: geom_params calculated once outside loop (load-independent)
        
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
        loads.M3 = np.array(all_demands['M_f']) * kN * m
        loads.V2 = np.array(all_demands['V_f']) * kN
        loads.P = np.array(all_demands['P_f']) * kN
        
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
        # Extract and store all results
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
        
        # Store complete results for this load combo
        all_design_data[load_combo] = {
            'x_stations': mesh.x_stations.tolist() if hasattr(mesh.x_stations, 'tolist') else list(mesh.x_stations),
            'M_r': M_r_values,
            'V_r': V_r_values,
            'M_r_array': M_r_array,
            'V_r_array': V_r_array,
            'all_demands': all_demands,
            'geom_params': geom_params,
            'analysis_params': analysis_params,
            'duration_params': duration_params,
            'active_loads': active_load_cases,
            'bending_proc': bending_proc,
            'shear_proc': shear_proc
        }
    
    return all_design_data


def main():
    """Main Streamlit app."""
    
    st.set_page_config(page_title="EIME Beam Debug Dashboard", layout="wide")
    
    st.title("🔍 EIME Beam Analysis Debug Dashboard")
    st.markdown("---")
    
    # ==========================================
    # SIDEBAR CONFIGURATION
    # ==========================================
    
    st.sidebar.header("⚙️ Model Configuration")
    
    # Create configuration from sidebar inputs
    with st.sidebar.expander("📐 Geometry", expanded=False):
        st.write("**Support Locations (m):**")
        support_input = st.text_input(
            "Comma-separated values",
            value="0, 4, 8",
            key="supports"
        )
        support_locations = [float(x.strip()) for x in support_input.split(",")]
        
        st.write("**Bracing Locations (m):**")
        bracing_input = st.text_input(
            "Comma-separated values",
            value="0, 2, 4, 6, 8",
            key="bracing"
        )
        bracing_locations = [float(x.strip()) for x in bracing_input.split(",")]
        
        mesh_spacing = st.number_input(
            "Mesh spacing (m)",
            min_value=0.05,
            max_value=1.0,
            value=0.2,
            step=0.05,
            key="mesh_spacing"
        )
    
    with st.sidebar.expander("📏 Section Properties", expanded=False):
        width_mm = st.number_input(
            "Width (mm)",
            min_value=50.0,
            max_value=500.0,
            value=175.0,
            step=5.0,
            key="width"
        )
        
        depth_mm = st.number_input(
            "Depth (mm)",
            min_value=100.0,
            max_value=1000.0,
            value=456.0,
            step=10.0,
            key="depth"
        )
        
        # Load glulam table to get available species and grades
        glulam_table = load_glulam_table()
        available_species = list(glulam_table.keys())
        
        # Species selection first
        species = st.selectbox(
            "Species",
            options=available_species,
            index=0,
            key="species"
        )
        
        # Grade options depend on selected species
        available_grades = list(glulam_table[species].keys())
        
        grade = st.selectbox(
            "Grade",
            options=available_grades,
            index=0,
            key="grade"
        )
    
    with st.sidebar.expander("📦 Applied Loads", expanded=False):
        dead_load = st.number_input(
            "Dead Load (kN/m)",
            min_value=0.0,
            max_value=50.0,
            value=6.0,
            step=0.5,
            key="dead_load"
        )
        
        live_load = st.number_input(
            "Live Load (kN/m)",
            min_value=0.0,
            max_value=50.0,
            value=4.0,
            step=0.5,
            key="live_load"
        )
        
        snow_load = st.number_input(
            "Snow Load (kN/m)",
            min_value=0.0,
            max_value=50.0,
            value=5.0,
            step=0.5,
            key="snow_load"
        )
        
        st.write("**Load Ranges:**")
        st.caption("Leave empty to apply to entire beam")
        
        # Simplified: just specify if snow is on first span
        apply_snow_first_span = st.checkbox(
            "Apply Snow to first span only",
            value=True,
            key="snow_first_span"
        )
        
        apply_live_second_span = st.checkbox(
            "Apply Live to second span only",
            value=True,
            key="live_second_span"
        )
        
        add_point_load = st.checkbox(
            "Add point load",
            value=True,
            key="add_point"
        )
        
        if add_point_load:
            point_magnitude = st.number_input(
                "Point Load (kN)",
                min_value=0.0,
                max_value=100.0,
                value=20.0,
                step=5.0,
                key="point_mag"
            )
            
            point_position = st.number_input(
                "Point Load Position (m)",
                min_value=0.0,
                max_value=support_locations[-1],
                value=support_locations[1] / 3 if len(support_locations) > 1 else 1.0,
                step=0.1,
                key="point_pos"
            )
            
            point_case = st.selectbox(
                "Point Load Case",
                options=["D", "L", "S"],
                index=1,
                key="point_case"
            )
    
    # Build configuration object
    beam_config = BeamConfig(
        support_locations=support_locations,
        bracing_locations=bracing_locations,
        mesh_spacing=mesh_spacing,
        refine_at_discontinuities=True
    )
    
    section_config = SectionConfig(
        width_mm=width_mm,
        depth_mm=depth_mm,
        grade=grade,
        species=species
    )
    
    # Setup load ranges
    load_ranges = {'D': [(support_locations[0], support_locations[-1])]}
    
    if apply_snow_first_span and len(support_locations) > 1:
        load_ranges['S'] = [(support_locations[0], support_locations[1])]
    else:
        load_ranges['S'] = [(support_locations[0], support_locations[-1])]
    
    if apply_live_second_span and len(support_locations) > 2:
        load_ranges['L'] = [(support_locations[1], support_locations[-1])]
    else:
        load_ranges['L'] = [(support_locations[0], support_locations[-1])]
    
    point_loads = []
    if add_point_load:
        point_loads.append((point_magnitude, point_position, point_case))
    
    load_config = LoadConfig(
        dead_load=dead_load,
        live_load=live_load,
        snow_load=snow_load,
        point_loads=point_loads,
        load_ranges=load_ranges
    )
    
    model_config = ModelConfig(
        beam=beam_config,
        section=section_config,
        loads=load_config,
        load_combinations=LoadCombinationConfig()  # Use defaults
    )
    
    # ==========================================
    # CREATE MODEL
    # ==========================================
    
    # Create hierarchical cache keys for different calculation stages
    geometry_key = f"{tuple(support_locations)}_{tuple(bracing_locations)}_{mesh_spacing}"
    loads_key = f"{geometry_key}_{dead_load}_{live_load}_{snow_load}_{apply_snow_first_span}_{apply_live_second_span}_{add_point_load}"
    if add_point_load:
        loads_key += f"_{point_magnitude}_{point_position}_{point_case}"
    section_key = f"{width_mm}_{depth_mm}_{grade}_{species}"
    design_cache_key = f"design_{loads_key}_{section_key}"
    
    with st.spinner("Creating beam model..."):
        beam_data = create_beam_model(model_config, cache_key=loads_key)
    
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
    # CALCULATE ALL DESIGN DATA ONCE (cached)
    # ==========================================
    
    # Cache design calculations with section-aware key
    # This allows reusing analysis/preprocessing when only section properties change
    if design_cache_key not in st.session_state:
        with st.spinner("Running design calculations for all load combinations..."):
            st.session_state[design_cache_key] = calculate_all_design_data(beam_data, load_combos)
    
    design_data = st.session_state[design_cache_key]
    
    # Extract resistances for plotting if needed
    if diagram_type in ['shear', 'moment']:
        resistances = {
            'x_stations': design_data[selected_combo]['x_stations'],
            'M_r': design_data[selected_combo]['M_r'],
            'V_r': design_data[selected_combo]['V_r']
        }
    else:
        resistances = None
    
    # ==========================================
    # DIAGRAM DISPLAY
    # ==========================================
    
    st.subheader(f"{diagram_type.capitalize()} Diagram - {selected_combo}")
    
    # Get member names and diagram data
    member_names = get_member_names(beam_data)
    x_data, y_data = get_diagram_data(
        model, 
        member_names, 
        selected_combo, 
        diagram_type, 
        beam_data['load_combos']
    )
    
    # Create figure
    fig = create_diagram_figure(
        x_data=x_data,
        y_data=y_data,
        diagram_type=diagram_type,
        load_combo=selected_combo,
        support_locations=beam_data['config'].beam.support_locations,
        bracing_locations=beam_data['config'].beam.bracing_locations,
        resistances=resistances,
        height=400
    )
    
    # Add shear segment annotations if needed
    if diagram_type == 'shear':
        material_ureg = beam_data['section'].material.f_b_pos._REGISTRY
        beam_length = get_total_beam_length(beam_data)
        fig = add_shear_segment_annotations(
            fig=fig,
            model=model,
            member_names=member_names,
            load_combo=selected_combo,
            beam_length=beam_length * material_ureg.m,
            ureg=material_ureg,
            y_data=y_data
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
    # STATION ANALYSIS (extract from cached data)
    # ==========================================
    
    station_data = analyze_station(beam_data, design_data, selected_combo, station_idx)
    
    st.info(f"📍 Station {station_idx} at x = {station_data['x_station']:.3f} m")
    
    # ==========================================
    # TABS FOR DETAILED INFORMATION
    # ==========================================
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Analysis",
        "⚙️ Preprocessing",
        "🔧 Design",
        "📋 Procedure Data",
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
        
        # Display load information from configuration
        load_config = beam_data['loads']
        load_mapping = {
            'D': load_config.dead_load,
            'L': load_config.live_load,
            'S': load_config.snow_load
        }
        
        for load_type, value in load_mapping.items():
            factor = beam_data['load_combos'][selected_combo].get(load_type, 0)
            if factor > 0 and value > 0:
                st.write(f"- {load_type}: {value:.1f} kN/m × {factor:.2f} = {value * factor:.2f} kN/m")
        
        # Display point loads if any
        if load_config.point_loads:
            st.write("**Point Loads:**")
            for P_mag, P_pos, P_case in load_config.point_loads:
                factor = beam_data['load_combos'][selected_combo].get(P_case, 0)
                if factor > 0:
                    st.write(f"- {P_case} @ {P_pos:.2f}m: {P_mag:.1f} kN × {factor:.2f} = {P_mag * factor:.2f} kN")
    
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
        
        st.write("**Shear Loads:**")
        st.write(f"- W_f: {station_data['demands']['W_f']:.2f} kN")
        st.write(f"- Sum_G: {station_data['demands']['Sum_G']:.2e}")
        
        # Show detailed segment breakdown for the segment containing this station
        with st.expander("View G Factor Parameters for This Station's Segment"):
            from design.csa_o86_2025.preprocessing.pynite_helpers import prepare_shear_segment_arrays, compute_sum_g
            from design.csa_o86_2025.formulas.glulam_shear import g_factor
            
            # Get unit registry from beam_data
            material_ureg = beam_data['section'].material.f_b_pos._REGISTRY
            m = material_ureg.m
            kN = material_ureg.kN
            model = beam_data['model']
            
            try:
                # Get member names and total length
                member_names = get_member_names(beam_data)
                
                # Process all members and combine segment data
                all_l_a = []
                all_V_A = []
                all_V_B = []
                all_V_C = []
                total_W_f = 0 * kN
                total_Sum_G = 0
                x_offset = 0.0
                
                for member_name in member_names:
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
        section_config = beam_data['config'].section
        st.write(f"- Width (b): {section_config.width_mm} mm")
        st.write(f"- Depth (d): {section_config.depth_mm} mm")
        st.write(f"- Area: {beam_data['section'].profile.Area().to(mm**2).magnitude:.0f} mm²")
        st.write(f"- I: {beam_data['section'].profile.MomentofInertia().to(mm**4).magnitude:.2e} mm⁴")
        
        st.write("**Material:**")
        st.write(f"- Grade: {section_config.grade} {section_config.species}")
        st.write(f"- f_b (positive): {beam_data['material'].f_b_pos.to(MPa).magnitude:.1f} MPa (compression on top)")
        st.write(f"- f_b (negative): {beam_data['material'].f_b_neg.to(MPa).magnitude:.1f} MPa (compression on bottom)")
        st.caption("Convention: Positive applied moment → use f_b_neg | Negative applied moment → use f_b_pos")
        st.write(f"- f_v: {beam_data['material'].f_v.to(MPa).magnitude:.2f} MPa")
        st.write(f"- E: {beam_data['material'].E.to(MPa).magnitude:.0f} MPa")
    
    with tab3:
        st.subheader("Design Calculations")
        
        bending_proc = station_data['design']['bending_proc']
        shear_proc = station_data['design']['shear_proc']
        
        # Show which bending strength is being used based on moment sign
        M_f = station_data['demands']['M_f']
        
        st.info(f"**Applied Moment:** M_f = {M_f:+.2f} kN·m")
        
        # Determine which f_b is being used based on convention
        # Positive moment → f_b_neg (compression on bottom)
        # Negative moment → f_b_pos (compression on top)
        if M_f >= 0:
            fb_used = "f_b_neg (negative bending - compression on bottom fiber)"
            fb_value = beam_data['material'].f_b_neg.to(MPa).magnitude
        else:
            fb_used = "f_b_pos (positive bending - compression on top fiber)"
            fb_value = beam_data['material'].f_b_pos.to(MPa).magnitude
        
        st.write(f"**Bending Strength Used:** {fb_used} = {fb_value:.1f} MPa")
        
        st.markdown("---")
        
        # Generate full LaTeX documentation for bending
        st.write("**Bending Resistance Procedure:**")
        bending_latex = bending_proc.generate_latex(index=station_idx)
        st.markdown(bending_latex)
        
        st.markdown("---")
        
        # Generate full LaTeX documentation for shear
        st.write("**Shear Resistance Procedure:**")
        shear_latex = shear_proc.generate_latex(index=station_idx)
        st.markdown(shear_latex)
    
    with tab4:
        st.subheader("Procedure Summary Data")
        
        bending_proc = station_data['design']['bending_proc']
        shear_proc = station_data['design']['shear_proc']
        
        st.write("**Bending Resistance Procedure Summary:**")
        bending_summary = bending_proc.summary()
        if len(bending_summary) > 0:
            # Show only the row for the current station
            st.dataframe(bending_summary.iloc[[station_idx]], width='stretch')
        else:
            st.info("No summary data available")
        
        st.markdown("---")
        
        st.write("**Shear Resistance Procedure Summary:**")
        shear_summary = shear_proc.summary()
        if len(shear_summary) > 0:
            # Show only the row for the current station
            st.dataframe(shear_summary.iloc[[station_idx]], width='stretch')
        else:
            st.info("No summary data available")
    
    with tab5:
        st.subheader("Design Results")
        
        # Get procedures for all stations
        bending_proc = station_data['design']['bending_proc']
        shear_proc = station_data['design']['shear_proc']
        
        # Calculate utilization for all stations using get_worst_utilization()
        bending_util = bending_proc.get_worst_utilization()
        shear_util = shear_proc.get_worst_utilization()
        
        # Find worst-case utilization and governing stations
        max_bending_util_idx = bending_util.idxmax()
        max_shear_util_idx = shear_util.idxmax()
        max_bending_util = bending_util.max() * 100
        max_shear_util = shear_util.max() * 100
        
        # Current station values
        M_f = station_data['demands']['M_f']
        V_f = station_data['demands']['V_f']
        M_r = station_data['results']['M_r']
        V_r = station_data['results']['V_r']
        
        # Display worst-case utilization across all stations
        st.write("### Worst-Case Utilization (All Stations)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Moment:**")
            st.metric("Maximum Utilization", f"{max_bending_util:.1f}%",
                     delta=None,
                     delta_color="inverse" if max_bending_util <= 100 else "normal")
            gov_x = mesh.x_stations[max_bending_util_idx]
            st.write(f"Governing Station: **{max_bending_util_idx}** (x = {gov_x:.3f} m)")
            
            if max_bending_util <= 100:
                st.success("✅ PASS")
            else:
                st.error("❌ FAIL")
        
        with col2:
            st.write("**Shear:**")
            st.metric("Maximum Utilization", f"{max_shear_util:.1f}%",
                     delta=None,
                     delta_color="inverse" if max_shear_util <= 100 else "normal")
            gov_x = mesh.x_stations[max_shear_util_idx]
            st.write(f"Governing Station: **{max_shear_util_idx}** (x = {gov_x:.3f} m)")
            
            if max_shear_util <= 100:
                st.success("✅ PASS")
            else:
                st.error("❌ FAIL")
        
        st.markdown("---")
        
        # Current station results
        st.write("### Current Station Results")
        
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
        overall_max_util = max(max_bending_util, max_shear_util)
        st.write(f"**Overall Maximum Utilization:** {overall_max_util:.1f}%")
        
        if overall_max_util <= 100:
            st.success("🎉 Design PASSES all checks!")
        else:
            st.error("⚠️ Design FAILS - requires larger section or reduced loads")


if __name__ == "__main__":
    main()
