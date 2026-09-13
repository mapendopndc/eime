"""
Visualization utilities for EIME Beam Analysis Dashboard

Provides functions for creating diagrams and plots from PyNite FEM models.
"""

import numpy as np
import plotly.graph_objects as go
from typing import List, Dict, Union, Tuple


def get_diagram_data(
    model,
    member_names: Union[str, List[str]],
    load_combo: str,
    diagram_type: str,
    load_combos_dict: Dict,
    num_points: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract diagram data from PyNite model for multiple members.
    
    Parameters
    ----------
    model : FEModel3D
        PyNite finite element model
    member_names : str or list of str
        Name(s) of member(s) to extract data from
    load_combo : str
        Load combination name
    diagram_type : str
        Type of diagram: 'loading', 'shear', or 'moment'
    load_combos_dict : dict
        Dictionary mapping load combo names to factors
    num_points : int, optional
        Number of points to sample along each member (default: 100)
    
    Returns
    -------
    x_data : np.ndarray
        Array of x-coordinates along the beam
    y_data : np.ndarray
        Array of y-values (load, shear, or moment)
    """
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


def create_diagram_figure(
    x_data: np.ndarray,
    y_data: np.ndarray,
    diagram_type: str,
    load_combo: str,
    support_locations: List[float] = None,
    bracing_locations: List[float] = None,
    resistances: Dict = None,
    height: int = 400
) -> go.Figure:
    """
    Create a Plotly figure for beam diagrams.
    
    Parameters
    ----------
    x_data : np.ndarray
        X-coordinates along the beam
    y_data : np.ndarray
        Y-values (load, shear, or moment)
    diagram_type : str
        Type of diagram: 'loading', 'shear', or 'moment'
    load_combo : str
        Load combination name (for title)
    support_locations : list of float, optional
        Locations of supports along the beam
    bracing_locations : list of float, optional
        Locations of bracing points along the beam
    resistances : dict, optional
        Dictionary with 'x_stations', 'M_r', and/or 'V_r' keys for resistance lines
    height : int, optional
        Figure height in pixels (default: 400)
    
    Returns
    -------
    fig : go.Figure
        Plotly figure object
    """
    fig = go.Figure()
    
    # Main diagram trace
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode='lines',
        name=diagram_type.capitalize(),
        line=dict(width=3, color='#1f77b4')
    ))
    
    # Add support markers
    if support_locations:
        fig.add_trace(go.Scatter(
            x=support_locations,
            y=[0] * len(support_locations),
            mode='markers',
            name='Supports',
            marker=dict(size=12, color='red', symbol='triangle-up')
        ))
    
    # Add resistance lines
    if resistances:
        if diagram_type == 'moment' and 'M_r' in resistances:
            # Positive resistance line
            fig.add_trace(go.Scatter(
                x=resistances['x_stations'],
                y=resistances['M_r'],
                mode='lines',
                name='M_r (Resistance)',
                line=dict(width=2, color='red', dash='dash')
            ))
            # Negative resistance line
            fig.add_trace(go.Scatter(
                x=resistances['x_stations'],
                y=[-m for m in resistances['M_r']],
                mode='lines',
                name='-M_r (Resistance)',
                line=dict(width=2, color='red', dash='dash'),
                showlegend=False
            ))
        
        elif diagram_type == 'shear' and 'V_r' in resistances:
            # Positive resistance line
            fig.add_trace(go.Scatter(
                x=resistances['x_stations'],
                y=resistances['V_r'],
                mode='lines',
                name='V_r (Resistance)',
                line=dict(width=2, color='red', dash='dash')
            ))
            # Negative resistance line
            fig.add_trace(go.Scatter(
                x=resistances['x_stations'],
                y=[-v for v in resistances['V_r']],
                mode='lines',
                name='-V_r (Resistance)',
                line=dict(width=2, color='red', dash='dash'),
                showlegend=False
            ))
    
    # Add bracing markers
    if bracing_locations:
        fig.add_trace(go.Scatter(
            x=bracing_locations,
            y=[0] * len(bracing_locations),
            mode='markers',
            name='Bracing',
            marker=dict(size=8, color='green', symbol='diamond')
        ))
    
    # Determine y-axis label
    if diagram_type == 'loading':
        y_label = "Load (kN/m)"
    elif diagram_type == 'shear':
        y_label = "Shear (kN)"
    else:
        y_label = "Moment (kN·m)"
    
    fig.update_layout(
        xaxis_title="Position (m)",
        yaxis_title=y_label,
        height=height,
        hovermode='x unified',
        showlegend=True
    )
    
    return fig


def add_shear_segment_annotations(
    fig: go.Figure,
    model,
    member_names: Union[str, List[str]],
    load_combo: str,
    beam_length,
    ureg,
    y_data: np.ndarray = None
) -> go.Figure:
    """
    Add segment annotations to a shear diagram.
    
    Parameters
    ----------
    fig : go.Figure
        Plotly figure to add annotations to
    model : FEModel3D
        PyNite finite element model
    member_names : str or list of str
        Name(s) of member(s)
    load_combo : str
        Load combination name
    beam_length : Quantity
        Total beam length with units
    ureg : UnitRegistry
        Pint unit registry
    y_data : np.ndarray, optional
        Y-data from diagram (for positioning annotations)
    
    Returns
    -------
    fig : go.Figure
        Modified figure with annotations
    """
    try:
        from design.csa_o86_2025.preprocessing.pynite_helpers import prepare_shear_segment_arrays
        
        if isinstance(member_names, str):
            member_names = [member_names]
        
        m = ureg.m
        
        # Determine y-position for annotations
        if y_data is not None:
            y_min, y_max = min(y_data), max(y_data)
        else:
            y_min, y_max = 0, 1
        
        segment_counter = 0
        x_offset = 0.0
        
        for member_name in member_names:
            member = model.members[member_name]
            member_length = member.L()
            
            segment_data = prepare_shear_segment_arrays(
                model=model,
                member_name=member_name,
                load_combo=load_combo,
                beam_length=member_length * m,
                num_points=401,  # Fine resolution for segment detection
                ureg=ureg
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
        # Silently skip if segment annotations fail
        pass
    
    return fig
