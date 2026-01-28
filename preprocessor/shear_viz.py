"""
Visualization for PyNite Shear Segment Analysis

This module provides visualization tools for shear diagrams and segment identification
used in CSA O86 shear load coefficient (CV) calculations.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Tuple
from matplotlib.patches import Rectangle


def plot_shear_diagram_with_segments(
    positions: np.ndarray,
    shear_values: np.ndarray,
    segments: List[Dict],
    title: str = "Shear Diagram with Segments",
    ax: Optional[plt.Axes] = None,
    show_segment_details: bool = True,
    support_positions: Optional[List[float]] = None,
    point_loads: Optional[List[Tuple[float, float]]] = None
) -> plt.Figure:
    """
    Plot shear force diagram with identified segments highlighted.
    
    Parameters
    ----------
    positions : np.ndarray
        Array of positions along member [m]
    shear_values : np.ndarray
        Array of shear force values [kN] (signed values)
    segments : List[Dict]
        List of segment dictionaries from identify_shear_segments()
    title : str, optional
        Plot title (default: "Shear Diagram with Segments")
    ax : plt.Axes, optional
        Matplotlib axes to plot on (creates new figure if None)
    show_segment_details : bool, optional
        Whether to show detailed segment information (default: True)
    support_positions : List[float], optional
        List of x-coordinates where supports are located (default: None)
    point_loads : List[Tuple[float, float]], optional
        List of (position, magnitude) tuples for point loads [m, kN] (default: None)
        
    Returns
    -------
    fig : plt.Figure
        Matplotlib figure object
        
    Examples
    --------
    >>> from preprocessor.pynite_shear import extract_shear_diagram, identify_shear_segments
    >>> x, V = extract_shear_diagram(model, 'M1', 'ULS_1')
    >>> segments = identify_shear_segments(x, V)
    >>> fig = plot_shear_diagram_with_segments(x, V, segments)
    >>> plt.show()
    """
    # Create figure if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 6))
    else:
        fig = ax.get_figure()
    
    # Plot shear diagram
    ax.plot(positions, shear_values, 'b-', linewidth=2, label='Shear Force')
    ax.fill_between(positions, 0, shear_values, alpha=0.3, color='blue')
    
    # Define colors for segments (cycle through)
    colors = ['red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    
    # Highlight each segment
    for i, segment in enumerate(segments):
        color = colors[i % len(colors)]
        
        # Get segment bounds
        start_idx = segment['start_idx']
        end_idx = segment['end_idx']
        start_pos = segment['start_pos']
        end_pos = segment['end_pos']
        
        # Draw vertical lines at segment boundaries
        if i > 0:  # Don't draw at the very start
            ax.axvline(start_pos, color=color, linestyle='--', linewidth=1.5, alpha=0.7)
        
        # Mark the segment points V_A, V_B, V_C
        V_A = shear_values[start_idx]
        V_B = shear_values[end_idx]
        center_idx = (start_idx + end_idx) // 2
        V_C = shear_values[center_idx]
        x_C = positions[center_idx]
        
        # Plot markers
        ax.plot(start_pos, V_A, 'o', color=color, markersize=8, 
                label=f'Seg {i+1}: V_A' if show_segment_details else '')
        ax.plot(end_pos, V_B, 's', color=color, markersize=8,
                label=f'Seg {i+1}: V_B' if show_segment_details else '')
        ax.plot(x_C, V_C, '^', color=color, markersize=8,
                label=f'Seg {i+1}: V_C' if show_segment_details else '')
        
        # Add segment label at center
        mid_x = (start_pos + end_pos) / 2
        max_abs_V_in_seg = np.max(np.abs(shear_values[start_idx:end_idx+1]))
        # Position label above or below depending on shear sign
        label_y = max_abs_V_in_seg * 1.1 if np.mean(shear_values[start_idx:end_idx+1]) >= 0 else -max_abs_V_in_seg * 1.1
        label_va = 'bottom' if np.mean(shear_values[start_idx:end_idx+1]) >= 0 else 'top'
        ax.text(mid_x, label_y, f'Seg {i+1}', 
                ha='center', va=label_va, fontsize=10, color=color, fontweight='bold')
    
    # Draw final boundary line
    ax.axvline(segments[-1]['end_pos'], color=colors[len(segments)-1 % len(colors)], 
               linestyle='--', linewidth=1.5, alpha=0.7)
    
    # Draw support markers
    if support_positions is not None:
        for i, support_x in enumerate(support_positions):
            # Draw vertical line at support
            ax.axvline(support_x, color='black', linestyle=':', linewidth=2, alpha=0.5)
            # Add support symbol (triangle pointing up)
            ax.plot(support_x, 0, marker='^', markersize=12, color='black', 
                   markerfacecolor='cyan', markeredgewidth=2, zorder=5)
            # Add label
            y_range = np.max(shear_values) - np.min(shear_values)
            ax.text(support_x, np.min(shear_values) - y_range * 0.08, f'Support\n{i+1}', 
                   ha='center', va='top', fontsize=8, color='black', fontweight='bold')
    
    # Draw point load markers
    if point_loads is not None:
        y_max = np.max(shear_values)
        y_min = np.min(shear_values)
        y_range = y_max - y_min
        for i, (load_x, load_mag) in enumerate(point_loads):
            # Draw vertical dashed line at point load location
            ax.axvline(load_x, color='red', linestyle='-.', linewidth=1.5, alpha=0.6)
            # Add downward arrow to indicate point load
            arrow_y_start = y_max + y_range * 0.15
            arrow_y_end = y_max + y_range * 0.02
            ax.annotate('', xy=(load_x, arrow_y_end), xytext=(load_x, arrow_y_start),
                       arrowprops=dict(arrowstyle='->', color='red', lw=2.5))
            # Add label with magnitude
            ax.text(load_x, arrow_y_start + y_range * 0.02, f'P={abs(load_mag):.1f} kN', 
                   ha='center', va='bottom', fontsize=9, color='red', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='red', alpha=0.8))
    
    # Formatting
    ax.set_xlabel('Position along beam [m]', fontsize=12)
    ax.set_ylabel('Shear Force [kN]', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color='black', linewidth=0.5)
    
    # Add 20% padding to y-axis for annotations
    y_min = np.min(shear_values)
    y_max = np.max(shear_values)
    y_range = y_max - y_min
    ax.set_ylim(y_min - 0.2 * y_range, y_max + 0.2 * y_range)
    
    if show_segment_details and len(segments) <= 5:
        ax.legend(loc='best', fontsize=9)
    
    plt.tight_layout()
    
    return fig


def plot_segment_table(
    segments: List[Dict],
    V_A_list: List[float],
    V_B_list: List[float],
    V_C_list: List[float],
    ax: Optional[plt.Axes] = None
) -> plt.Figure:
    """
    Create a table showing segment details.
    
    Parameters
    ----------
    segments : List[Dict]
        List of segment dictionaries
    V_A_list : List[float]
        Shear values at start of each segment
    V_B_list : List[float]
        Shear values at end of each segment
    V_C_list : List[float]
        Shear values at center of each segment
    ax : plt.Axes, optional
        Matplotlib axes (creates new if None)
        
    Returns
    -------
    fig : plt.Figure
        Matplotlib figure object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 3))
    else:
        fig = ax.get_figure()
    
    ax.axis('off')
    
    # Prepare table data
    headers = ['Segment', 'Start [m]', 'End [m]', 'Length [m]', 'V_A [kN]', 'V_B [kN]', 'V_C [kN]']
    table_data = []
    
    for i, seg in enumerate(segments):
        # Extract magnitude if pint Quantity
        V_A = V_A_list[i].magnitude if hasattr(V_A_list[i], 'magnitude') else V_A_list[i]
        V_B = V_B_list[i].magnitude if hasattr(V_B_list[i], 'magnitude') else V_B_list[i]
        V_C = V_C_list[i].magnitude if hasattr(V_C_list[i], 'magnitude') else V_C_list[i]
        
        # Convert from N to kN if needed (check magnitude)
        if V_A > 1000:  # Likely in N
            V_A /= 1000
            V_B /= 1000
            V_C /= 1000
        
        row = [
            f"{i+1}",
            f"{seg['start_pos']:.2f}",
            f"{seg['end_pos']:.2f}",
            f"{seg['length']:.2f}",
            f"{V_A:.2f}",
            f"{V_B:.2f}",
            f"{V_C:.2f}"
        ]
        table_data.append(row)
    
    # Create table
    table = ax.table(cellText=table_data, colLabels=headers,
                    cellLoc='center', loc='center',
                    bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Style header row
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Alternate row colors
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')
    
    plt.tight_layout()
    
    return fig


def visualize_shear_analysis(
    positions: np.ndarray,
    shear_values: np.ndarray,
    segments: List[Dict],
    V_A_list: Optional[List[float]] = None,
    V_B_list: Optional[List[float]] = None,
    V_C_list: Optional[List[float]] = None,
    title: str = "Shear Analysis",
    save_path: Optional[str] = None,
    support_positions: Optional[List[float]] = None,
    point_loads: Optional[List[Tuple[float, float]]] = None
) -> plt.Figure:
    """
    Create comprehensive visualization with shear diagram and segment table.
    
    Parameters
    ----------
    positions : np.ndarray
        Array of positions along member [m]
    shear_values : np.ndarray
        Array of shear force values [kN]
    segments : List[Dict]
        List of segment dictionaries
    V_A_list, V_B_list, V_C_list : List[float], optional
        Shear values at segment points (extracted if not provided)
    title : str, optional
        Overall title for the visualization
    save_path : str, optional
        Path to save the figure (doesn't save if None)
    support_positions : List[float], optional
        List of x-coordinates where supports are located (default: None)
    point_loads : List[Tuple[float, float]], optional
        List of (position, magnitude) tuples for point loads [m, kN] (default: None)
        
    Returns
    -------
    fig : plt.Figure
        Matplotlib figure object
    """
    # Extract V_A, V_B, V_C if not provided
    if V_A_list is None or V_B_list is None or V_C_list is None:
        V_A_list = []
        V_B_list = []
        V_C_list = []
        for seg in segments:
            V_A_list.append(shear_values[seg['start_idx']])
            V_B_list.append(shear_values[seg['end_idx']])
            center_idx = (seg['start_idx'] + seg['end_idx']) // 2
            V_C_list.append(shear_values[center_idx])
    
    # Create figure with two subplots
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 1, height_ratios=[2, 1], hspace=0.3)
    
    ax_diagram = fig.add_subplot(gs[0])
    ax_table = fig.add_subplot(gs[1])
    
    # Plot shear diagram
    plot_shear_diagram_with_segments(
        positions, shear_values, segments,
        title=f"{title} - Shear Diagram",
        ax=ax_diagram,
        show_segment_details=False,
        support_positions=support_positions,
        point_loads=point_loads
    )
    
    # Plot segment table
    plot_segment_table(segments, V_A_list, V_B_list, V_C_list, ax=ax_table)
    
    # Overall title
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to: {save_path}")
    
    return fig


def main():
    """
    Demo client code showing how to use the shear visualization.
    
    Creates a PyNite beam model with loading and visualizes the segment analysis.
    """
    print("=" * 60)
    print("Shear Diagram Visualization Demo (PyNite)")
    print("=" * 60)
    
    # Import PyNite
    try:
        from Pynite.FEModel3D import FEModel3D
    except ImportError:
        print("\nError: PyNite is not installed.")
        print("Install it with: pip install PyNiteFEA")
        return
    
    # Beam parameters - continuous beam with 3 spans
    L1 = 6.0  # Left span [m]
    L2 = 8.0  # Middle span [m]
    L3 = 5.0  # Right span [m]
    L_total = L1 + L2 + L3
    
    # Asymmetric loading
    P1 = 40.0  # Point load on left span [kN]
    P2 = 60.0  # Point load on middle span [kN]
    w1 = 12.0  # Distributed load on left span [kN/m]
    w2 = 8.0   # Distributed load on middle span [kN/m]
    w3 = 15.0  # Distributed load on right span [kN/m]
    
    print(f"\nBeam Configuration:")
    print(f"  Continuous beam with intermediate supports")
    print(f"  Left span: {L1} m")
    print(f"  Middle span: {L2} m")
    print(f"  Right span: {L3} m")
    print(f"  Total length: {L_total} m")
    print(f"\nLoading:")
    print(f"  Left span: {w1} kN/m distributed + {P1} kN point load at {L1/3:.1f}m")
    print(f"  Middle span: {w2} kN/m distributed + {P2} kN point load at {L1 + L2/2:.1f}m")
    print(f"  Right span: {w3} kN/m distributed only")
    
    # Create PyNite model
    print("\nCreating PyNite FEM model...")
    model = FEModel3D()
    
    # Material and section properties
    E = 12000  # Elastic modulus [MPa]
    G = E * 0.4  # Shear modulus [MPa]
    model.add_material('Wood', E, G, 0.3, 500)  # E, G, nu, rho
    
    # Rectangular section: 175mm x 456mm
    b, d = 0.175, 0.456  # [m]
    A = b * d
    I = b * d**3 / 12
    model.add_section('Rect', A, I, I/2, I/2)  # A, Iy, Iz, J
    
    # Nodes - 4 nodes for 3-span continuous beam
    model.add_node('N1', 0, 0, 0)              # Left end
    model.add_node('N2', L1, 0, 0)             # First interior support
    model.add_node('N3', L1 + L2, 0, 0)        # Second interior support
    model.add_node('N4', L_total, 0, 0)        # Right end
    
    # Members - 3 continuous spans
    model.add_member('M1', 'N1', 'N2', 'Wood', 'Rect')  # Left span
    model.add_member('M2', 'N2', 'N3', 'Wood', 'Rect')  # Middle span
    model.add_member('M3', 'N3', 'N4', 'Wood', 'Rect')  # Right span
    
    # Supports: pin at left end, rollers at interior supports, roller at right end
    model.def_support('N1', True, True, True, False, False, False)   # Pin at left
    model.def_support('N2', False, True, True, True, False, False)   # Roller at first interior
    model.def_support('N3', False, True, True, True, False, False)   # Roller at second interior
    model.def_support('N4', False, True, True, True, False, False)   # Roller at right
    
    # Load combination
    model.add_load_combo('ULS', {'ULS': 1.0})
    
    # Add asymmetric distributed loads
    model.add_member_dist_load('M1', 'Fy', -w1, -w1, 0, L1, 'ULS')         # Left span
    model.add_member_dist_load('M2', 'Fy', -w2, -w2, 0, L2, 'ULS')         # Middle span
    model.add_member_dist_load('M3', 'Fy', -w3, -w3, 0, L3, 'ULS')         # Right span
    
    # Add point loads at different locations
    model.add_member_pt_load('M1', 'Fy', -P1, L1/3, 'ULS')                 # Point load on left span
    model.add_member_pt_load('M2', 'Fy', -P2, L2/2, 'ULS')                 # Point load on middle span
    
    # Analyze the model
    print("Analyzing model...")
    model.analyze(check_statics=False)
    print("Analysis complete.")
    
    # Define support locations for visualization
    support_positions = [0, L1, L1 + L2, L_total]  # All four support locations
    
    # Import the extraction and segment identification functions
    try:
        from preprocessor.pynite_shear import extract_shear_diagram, identify_shear_segments
        
        # Extract and combine shear diagrams from all members
        print("\nExtracting shear diagrams from PyNite model...")
        
        # Extract each span separately with signed values for visualization
        x1, V1 = extract_shear_diagram(model, 'M1', 'ULS', num_points=100, absolute=False)
        x2, V2 = extract_shear_diagram(model, 'M2', 'ULS', num_points=100, absolute=False)
        x3, V3 = extract_shear_diagram(model, 'M3', 'ULS', num_points=100, absolute=False)
        
        # Combine into continuous beam (offset x positions)
        x2_offset = x2 + L1
        x3_offset = x3 + L1 + L2
        
        x = np.concatenate([x1, x2_offset, x3_offset])
        V = np.concatenate([V1, V2, V3])
        
        print(f"Combined shear diagram with {len(x)} points")
        
        # Print extreme shear values
        max_shear_idx = np.argmax(np.abs(V))
        print(f"\nMaximum |shear|: {abs(V[max_shear_idx]):.2f} kN at x = {x[max_shear_idx]:.2f}m")
        print(f"Shear at supports:")
        print(f"  N1 (x=0): {V[0]:.2f} kN")
        print(f"  N2 (x={L1}m): {V1[-1]:.2f} kN / {V2[0]:.2f} kN")
        print(f"  N3 (x={L1+L2}m): {V2[-1]:.2f} kN / {V3[0]:.2f} kN")
        print(f"  N4 (x={L_total}m): {V[-1]:.2f} kN")
        
        # Identify segments using absolute values for CSA O86 segmentation
        segments = identify_shear_segments(x, np.abs(V))
        
        print(f"\nSegments identified: {len(segments)}")
        for i, seg in enumerate(segments):
            print(f"  Segment {i+1}: {seg['start_pos']:.2f}m to {seg['end_pos']:.2f}m (length: {seg['length']:.2f}m)")
        
        # Define point load locations for visualization
        point_load_locations = [
            (L1/3, -P1),                    # Point load on left span
            (L1 + L2/2, -P2)                # Point load on middle span
        ]
        
        # Create visualization
        print("\nGenerating visualization...")
        fig = visualize_shear_analysis(
            x, V, segments,
            title="3-Span Continuous Beam with Asymmetric Loading (PyNite)",
            support_positions=support_positions,
            point_loads=point_load_locations
        )
        
        print("\nVisualization complete!")
        print("Close the plot window to exit.")
        
        plt.show()
        
    except ImportError as e:
        print(f"\nError: Could not import required modules: {e}")
        print("Make sure utils.fem.pynite_shear is available.")
        print("Showing basic shear diagrams using PyNite's built-in plotting...")
        
        # Use PyNite's built-in plot as fallback for each span
        model.members['M1'].plot_shear('Fy', combo_name='ULS')
        model.members['M2'].plot_shear('Fy', combo_name='ULS')
        model.members['M3'].plot_shear('Fy', combo_name='ULS')
        plt.show()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
