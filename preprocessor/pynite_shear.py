"""
PyNite Preprocessor for Shear Load Coefficient Calculation

This module provides utilities to extract shear diagrams from PyNite FEM models
and prepare data for CSA O86 shear load coefficient (CV) calculation per 7.5.7.6.

The preprocessor is FEM-aware but outputs generic arrays that can be used by
PyNite-agnostic calculators and formulas.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
try:
    from Pynite.FEModel3D import FEModel3D
except ImportError:
    FEModel3D = None  # Allow module to be imported even if PyNite not installed


def extract_shear_diagram(
    model,
    member_name: str,
    load_combo: str,
    num_points: int = 100,
    absolute: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract shear force diagram from a PyNite beam member.
    
    Parameters
    ----------
    model : FEModel3D
        Analyzed PyNite finite element model
    member_name : str
        Name of the member to extract shear from
    load_combo : str
        Name of the load combination
    num_points : int, optional
        Number of points to sample along the member (default: 100)
    absolute : bool, optional
        If True, return absolute values (for CSA O86 calculations).
        If False, return signed values (for visualization). Default: True
        
    Returns
    -------
    positions : np.ndarray
        Array of positions along member [m]
    shear_values : np.ndarray
        Array of shear force values [kN]
        
    Notes
    -----
    Per CSA O86 7.5.7.6 a), for maximum shear forces, positive and negative
    values are both treated as positive (absolute values). Set absolute=True
    for design calculations, absolute=False for visualization.
    
    Examples
    --------
    >>> model = FEModel3D()
    >>> # ... setup and analyze model ...
    >>> x, V = extract_shear_diagram(model, 'M1', 'ULS_1')  # Absolute values
    >>> x, V_signed = extract_shear_diagram(model, 'M1', 'ULS_1', absolute=False)  # Signed
    """
    if model is None:
        raise ValueError("PyNite model is required")
    
    member = model.members.get(member_name)
    if member is None:
        raise ValueError(f"Member '{member_name}' not found in model")
    
    # Get member length
    L = member.L()
    
    # Sample shear forces along the member
    positions = np.linspace(0, L, num_points)
    shear_values = np.zeros(num_points)
    
    for i, x in enumerate(positions):
        try:
            # Extract shear force at position x for the given load combo
            # Note: Using 'Fy' for vertical shear in 2D beam
            V = member.shear('Fy', x, load_combo)
            # Take absolute value per CSA O86 7.5.7.6 a) if requested
            shear_values[i] = abs(V) if absolute else V
        except Exception as e:
            # If extraction fails, use zero
            shear_values[i] = 0.0
    
    return positions, shear_values


def identify_shear_segments(
    positions: np.ndarray,
    shear_values: np.ndarray,
    tolerance: float = 1e-6
) -> List[Dict]:
    """
    Divide beam into segments for CV calculation per CSA O86 7.5.7.6 b).
    
    Segments are created such that within each segment there are neither
    abrupt changes nor changes from negative to positive in shear force.
    
    Parameters
    ----------
    positions : np.ndarray
        Array of positions along member [m]
    shear_values : np.ndarray
        Array of shear force values [kN]
    tolerance : float, optional
        Tolerance for detecting slope changes (default: 1e-6)
        
    Returns
    -------
    segments : List[Dict]
        List of segment dictionaries, each containing:
        - 'start_idx': Starting index in arrays
        - 'end_idx': Ending index in arrays
        - 'start_pos': Starting position [m]
        - 'end_pos': Ending position [m]
        - 'length': Segment length [m]
        
    Notes
    -----
    The algorithm identifies:
    1. Sign changes in shear (already handled by absolute values)
    2. Abrupt changes in shear magnitude (discontinuities)
    3. Changes in shear slope (indicating load discontinuities)
    
    Examples
    --------
    >>> x = np.array([0, 1, 2, 3, 4])
    >>> V = np.array([10, 8, 6, 4, 2])  # Linearly decreasing
    >>> segments = identify_shear_segments(x, V)
    """
    if len(positions) != len(shear_values):
        raise ValueError("positions and shear_values must have same length")
    
    if len(positions) < 2:
        raise ValueError("Need at least 2 points to define segments")
    
    segments = []
    segment_start_idx = 0
    
    # Calculate finite differences to detect discontinuities
    dx = np.diff(positions)
    dV = np.diff(shear_values)
    
    # Avoid division by zero using safe division
    # np.where evaluates both branches, so we need to mask the division
    with np.errstate(divide='ignore', invalid='ignore'):
        slopes = np.divide(dV, dx, out=np.zeros_like(dV), where=dx > tolerance)
    
    # Detect slope changes (indicating load discontinuities or abrupt changes)
    if len(slopes) > 1:
        slope_changes = np.abs(np.diff(slopes))
        # Normalize by maximum slope change to make threshold relative
        max_slope_change = np.max(slope_changes) if np.max(slope_changes) > 0 else 1.0
        relative_changes = slope_changes / max_slope_change
        
        # Find significant slope changes
        # Using 20% as threshold - can be adjusted based on requirements
        discontinuity_threshold = 0.2
        discontinuity_indices = np.where(relative_changes > discontinuity_threshold)[0]
        
        # Group consecutive discontinuity indices (they represent the same physical discontinuity)
        # and take the one with maximum slope change
        if len(discontinuity_indices) > 0:
            grouped_discontinuities = []
            current_group = [discontinuity_indices[0]]
            
            for i in range(1, len(discontinuity_indices)):
                if discontinuity_indices[i] - discontinuity_indices[i-1] <= 2:
                    # Consecutive or very close, same discontinuity
                    current_group.append(discontinuity_indices[i])
                else:
                    # New discontinuity
                    # Find the index with maximum slope change in current group
                    max_change_idx = current_group[np.argmax([slope_changes[idx] for idx in current_group])]
                    grouped_discontinuities.append(max_change_idx)
                    current_group = [discontinuity_indices[i]]
            
            # Don't forget the last group
            max_change_idx = current_group[np.argmax([slope_changes[idx] for idx in current_group])]
            grouped_discontinuities.append(max_change_idx)
            
            # Create segments at discontinuities
            for disc_idx in grouped_discontinuities:
                # disc_idx is in the slope_changes array (one shorter than slopes)
                # The discontinuity occurs between slopes[disc_idx] and slopes[disc_idx+1]
                # Which corresponds to position index disc_idx+1
                end_idx = disc_idx + 1
                
                if end_idx > segment_start_idx:
                    segments.append({
                        'start_idx': segment_start_idx,
                        'end_idx': end_idx,
                        'start_pos': positions[segment_start_idx],
                        'end_pos': positions[end_idx],
                        'length': positions[end_idx] - positions[segment_start_idx]
                    })
                    segment_start_idx = end_idx
    
    # Add final segment
    if segment_start_idx < len(positions) - 1:
        segments.append({
            'start_idx': segment_start_idx,
            'end_idx': len(positions) - 1,
            'start_pos': positions[segment_start_idx],
            'end_pos': positions[-1],
            'length': positions[-1] - positions[segment_start_idx]
        })
    
    # If no segments were created (uniform load), create single segment
    if len(segments) == 0:
        segments.append({
            'start_idx': 0,
            'end_idx': len(positions) - 1,
            'start_pos': positions[0],
            'end_pos': positions[-1],
            'length': positions[-1] - positions[0]
        })
    
    return segments


def prepare_shear_segment_arrays(
    model,
    member_name: str,
    load_combo: str,
    beam_length: float,
    num_points: int = 100,
    ureg = None
) -> Dict:
    """
    Prepare shear segment arrays for CV calculation per CSA O86 7.5.7.6.
    
    This is the main preprocessor function that extracts shear diagrams from
    PyNite and prepares data arrays for the g_factor and shear_load_coefficient
    formulas.
    
    Parameters
    ----------
    model : FEModel3D
        Analyzed PyNite finite element model
    member_name : str
        Name of the member to analyze
    load_combo : str
        Name of the load combination
    beam_length : float
        Total beam length (with units if ureg provided, otherwise [m])
    num_points : int, optional
        Number of points to sample (default: 100)
    ureg : UnitRegistry, optional
        Pint unit registry for dimensional analysis
        
    Returns
    -------
    segment_data : Dict
        Dictionary containing arrays ready for formulas:
        - 'l_a': List of segment lengths [mm if ureg, else m]
        - 'V_A': List of shear at start of each segment [N if ureg, else kN]
        - 'V_B': List of shear at end of each segment [N if ureg, else kN]
        - 'V_C': List of shear at center of each segment [N if ureg, else kN]
        - 'W_f': Total factored load on beam [N if ureg, else kN]
        - 'L': Beam length [mm if ureg, else m]
        - 'segments': Raw segment information
        
    Notes
    -----
    Per CSA O86 7.5.7.6:
    - V_A = factored shear at beginning of segment
    - V_B = factored shear at end of segment
    - V_C = factored shear at centre of segment
    - All shear values are absolute values (positive)
    
    Examples
    --------
    >>> from eime.units import ureg
    >>> segment_data = prepare_shear_segment_arrays(
    ...     model, 'M1', 'ULS_1', 8.0 * ureg.m, ureg=ureg
    ... )
    >>> # Use with formulas:
    >>> from design.csa_o86_2025.formulas.glulam_shear import g_factor
    >>> G_values = [g_factor(l, va, vb, vc) for l, va, vb, vc in zip(
    ...     segment_data['l_a'], segment_data['V_A'],
    ...     segment_data['V_B'], segment_data['V_C']
    ... )]
    """
    # Extract shear diagram
    positions, shear_values = extract_shear_diagram(
        model, member_name, load_combo, num_points
    )
    
    # Identify segments
    segments = identify_shear_segments(positions, shear_values)
    
    # Prepare arrays for each segment
    l_a_list = []
    V_A_list = []
    V_B_list = []
    V_C_list = []
    
    for segment in segments:
        # Segment length
        l_a = segment['length']
        
        # Shear at start (V_A)
        V_A = shear_values[segment['start_idx']]
        
        # Shear at end (V_B)
        V_B = shear_values[segment['end_idx']]
        
        # Shear at center (V_C)
        center_idx = (segment['start_idx'] + segment['end_idx']) // 2
        V_C = shear_values[center_idx]
        
        # Apply units if ureg provided
        if ureg is not None:
            l_a = l_a * ureg.m  # positions are in meters
            l_a = l_a.to(ureg.mm)  # Convert to mm for formulas
            V_A = V_A * ureg.kN  # shear values are in kN
            V_A = V_A.to(ureg.N)  # Convert to N for formulas
            V_B = V_B * ureg.kN
            V_B = V_B.to(ureg.N)
            V_C = V_C * ureg.kN
            V_C = V_C.to(ureg.N)
        
        l_a_list.append(l_a)
        V_A_list.append(V_A)
        V_B_list.append(V_B)
        V_C_list.append(V_C)
    
    # Calculate total factored load (W_f)
    # For a simply supported beam, total load = sum of reactions
    # We can get this from the maximum shear at the supports
    member = model.members[member_name]
    L = member.L()
    
    # Method 1: Use shear values at supports
    # For a simply supported beam with distributed/point loads:
    # Shear at left support = left reaction (positive upward)
    # Shear at right support = right reaction (negative)
    # Total load = left reaction + right reaction
    try:
        V_left = abs(shear_values[0])   # Shear at start
        V_right = abs(shear_values[-1])  # Shear at end
        
        # Total load is sum of reactions
        W_f = V_left + V_right
        
        if ureg is not None:
            W_f = W_f * ureg.kN
            W_f = W_f.to(ureg.N)
    except Exception:
        # Fallback: use max shear * 2 (for symmetric loading)
        W_f = max(shear_values) * 2
        if ureg is not None:
            W_f = W_f * ureg.kN
            W_f = W_f.to(ureg.N)
    
    # Prepare beam length
    if ureg is not None:
        if hasattr(beam_length, 'magnitude'):
            L_out = beam_length.to(ureg.mm)
        else:
            L_out = beam_length * ureg.m
            L_out = L_out.to(ureg.mm)
    else:
        L_out = beam_length
    
    return {
        'l_a': l_a_list,
        'V_A': V_A_list,
        'V_B': V_B_list,
        'V_C': V_C_list,
        'W_f': W_f,
        'L': L_out,
        'segments': segments
    }


def compute_sum_g(segment_data: Dict, g_factor_formula) -> float:
    """
    Compute Sum(G) from segment data using the g_factor formula.
    
    This helper function takes the output from prepare_shear_segment_arrays
    and computes the sum of G factors needed for CV calculation.
    
    Parameters
    ----------
    segment_data : Dict
        Output from prepare_shear_segment_arrays containing l_a, V_A, V_B, V_C arrays
    g_factor_formula : callable
        The g_factor formula function from design.csa_o86_2025.formulas.glulam_shear
        
    Returns
    -------
    Sum_G : float or Quantity
        Sum of all G factors with proper units
        
    Examples
    --------
    >>> from design.csa_o86_2025.formulas.glulam_shear import g_factor
    >>> from eime.units import ureg
    >>> segment_data = prepare_shear_segment_arrays(model, 'M1', 'ULS_1', 
    ...                                               8.0*ureg.m, ureg=ureg)
    >>> Sum_G = compute_sum_g(segment_data, g_factor)
    """
    G_values = []
    
    for i in range(len(segment_data['l_a'])):
        G_formula = g_factor_formula(
            l_a=segment_data['l_a'][i],
            V_A=segment_data['V_A'][i],
            V_B=segment_data['V_B'][i],
            V_C=segment_data['V_C'][i]
        )
        G_values.append(G_formula.result)
    
    # Sum all G values
    Sum_G = sum(G_values)
    
    return Sum_G


__all__ = [
    'extract_shear_diagram',
    'identify_shear_segments',
    'prepare_shear_segment_arrays',
    'compute_sum_g'
]
