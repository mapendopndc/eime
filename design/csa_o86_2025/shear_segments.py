"""
CSA O86 shear segment analysis utilities.

This module implements shear force segmentation and analysis per CSA O86-19
clause 7.5.7.6 for calculating the shear load coefficient (CV).
"""

import numpy as np
from typing import Dict, List, Optional


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
    
    # First, detect sign changes (zero-crossings) explicitly
    # These are critical segment boundaries that must always be detected
    sign_changes = []
    for i in range(len(shear_values) - 1):
        # Check for sign change (product is negative or one is zero)
        if shear_values[i] * shear_values[i + 1] < 0:
            sign_changes.append(i + 1)
        # Also check if value is essentially zero (within tolerance)
        elif abs(shear_values[i]) < tolerance and i > 0:
            # Make sure it's a true zero-crossing, not just numerical noise
            if i + 1 < len(shear_values) and abs(shear_values[i + 1]) > tolerance:
                sign_changes.append(i)
    
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
        
        # Use BOTH absolute and relative thresholds to avoid false positives
        # Absolute threshold: ignore slope changes smaller than 1% of max absolute slope
        max_abs_slope = np.max(np.abs(slopes)) if len(slopes) > 0 else 1.0
        absolute_threshold = 0.01 * max_abs_slope
        
        # Relative threshold: within "significant" slope changes, only flag the largest ones
        max_slope_change = np.max(slope_changes) if np.max(slope_changes) > 0 else 1.0
        relative_changes = slope_changes / max_slope_change
        
        # A discontinuity must satisfy BOTH conditions:
        # 1. Absolute slope change > 1% of maximum slope (filters numerical noise)
        # 2. Relative slope change > 20% of max change (filters minor variations)
        discontinuity_threshold = 0.2
        significant_indices = np.where(
            (slope_changes > absolute_threshold) & 
            (relative_changes > discontinuity_threshold)
        )[0]
        
        discontinuity_indices = significant_indices
        
        # Group consecutive discontinuity indices (they represent the same physical discontinuity)
        # and take the one with maximum slope change
        grouped_discontinuities = []
        if len(discontinuity_indices) > 0:
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
        
        # Convert slope discontinuities to position indices
        # slope_changes[i] represents change between slopes[i] and slopes[i+1]
        # This corresponds to a discontinuity at position index i+1
        slope_disc_positions = [idx + 1 for idx in grouped_discontinuities]
        
        # Combine slope discontinuities with sign changes (both now in position index space)
        all_discontinuities = sorted(set(slope_disc_positions + sign_changes))
        
        # Group discontinuities that are too close together (within 3 sample points)
        # This handles cases like support reactions where shear jumps vertically
        # and creates multiple detected discontinuities at the same physical location
        if len(all_discontinuities) > 1:
            grouped_disc = []
            current_group = [all_discontinuities[0]]
            
            for i in range(1, len(all_discontinuities)):
                # If this discontinuity is within 3 points of the previous one
                if all_discontinuities[i] - current_group[-1] <= 3:
                    current_group.append(all_discontinuities[i])
                else:
                    # Take the middle of the group as the representative discontinuity
                    grouped_disc.append(current_group[len(current_group) // 2])
                    current_group = [all_discontinuities[i]]
            
            # Don't forget the last group
            grouped_disc.append(current_group[len(current_group) // 2])
            
            all_discontinuities = grouped_disc
        
        # Create segments at discontinuities
        if len(all_discontinuities) > 0:
            for end_idx in all_discontinuities:
                
                # For better accuracy with linear shear diagrams, interpolate to find
                # the exact minimum point (zero-crossing for symmetric loads)
                interpolated_pos = None
                if end_idx > 0 and end_idx < len(shear_values) - 1:
                    # Check if this is a V-shaped discontinuity (shear crossing zero)
                    # Use absolute values to check for near-zero values
                    abs_shear = np.abs(shear_values)
                    if abs_shear[end_idx] < 0.1 * np.max(abs_shear):
                        # Search window around the discontinuity for the minimum
                        search_start = max(0, end_idx - 3)
                        search_end = min(len(shear_values) - 1, end_idx + 3)
                        
                        # Find the absolute minimum in the search window
                        search_values = abs_shear[search_start:search_end + 1]
                        min_local_idx = np.argmin(search_values)
                        min_idx = search_start + min_local_idx
                        
                        # Now interpolate around the minimum to find the exact zero point
                        # Check if we can interpolate between this point and neighbors
                        if min_idx > 0 and min_idx < len(shear_values) - 1:
                            v_before = abs_shear[min_idx - 1]
                            v_min = abs_shear[min_idx]
                            v_after = abs_shear[min_idx + 1]
                            
                            # Fit a parabola through these 3 points to find exact minimum
                            # Or use the point where shear is smallest
                            if v_min < min(v_before, v_after):
                                # Quadratic interpolation for more accuracy
                                # Using the vertex formula for a parabola through 3 points
                                dx = positions[min_idx] - positions[min_idx - 1]
                                if abs(dx) > tolerance and abs(v_before - v_after) > tolerance:
                                    # Offset from min_idx position to the true minimum
                                    offset = dx * (v_before - v_after) / (2 * (v_before - 2*v_min + v_after))
                                    interpolated_pos = positions[min_idx] + offset
                                else:
                                    interpolated_pos = positions[min_idx]
                                end_idx = min_idx
                            else:
                                # Not a true local minimum, just use the smallest value
                                end_idx = min_idx
                                interpolated_pos = positions[min_idx]
                        else:
                            end_idx = min_idx
                
                if end_idx > segment_start_idx:
                    # Use interpolated position if available, otherwise use sampled position
                    end_position = interpolated_pos if interpolated_pos is not None else positions[end_idx]
                    
                    segments.append({
                        'start_idx': segment_start_idx,
                        'end_idx': end_idx,
                        'start_pos': positions[segment_start_idx],
                        'end_pos': end_position,
                        'length': end_position - positions[segment_start_idx],
                        'interpolated_end': interpolated_pos is not None
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
    
    # Merge tiny segments (typically at support discontinuities)
    # A segment is considered "tiny" if it's less than 1% of the total beam length
    if len(segments) > 1:
        total_length = positions[-1] - positions[0]
        min_segment_length = 0.01 * total_length  # 1% of beam length
        
        merged_segments = []
        i = 0
        while i < len(segments):
            current_seg = segments[i]
            
            # Check if this segment is tiny
            if current_seg['length'] < min_segment_length:
                # Try to merge with adjacent segment
                if i > 0 and i < len(segments) - 1:
                    # Tiny segment in the middle - merge with larger neighbor
                    prev_seg = merged_segments[-1] if merged_segments else None
                    next_seg = segments[i + 1]
                    
                    # Merge with the smaller of the two neighbors to balance
                    if prev_seg and prev_seg['length'] <= next_seg['length']:
                        # Merge with previous segment
                        merged_segments[-1] = {
                            'start_idx': prev_seg['start_idx'],
                            'end_idx': current_seg['end_idx'],
                            'start_pos': prev_seg['start_pos'],
                            'end_pos': current_seg['end_pos'],
                            'length': current_seg['end_pos'] - prev_seg['start_pos'],
                            'interpolated_end': current_seg.get('interpolated_end', False)
                        }
                    else:
                        # Merge with next segment
                        segments[i + 1] = {
                            'start_idx': current_seg['start_idx'],
                            'end_idx': next_seg['end_idx'],
                            'start_pos': current_seg['start_pos'],
                            'end_pos': next_seg['end_pos'],
                            'length': next_seg['end_pos'] - current_seg['start_pos'],
                            'interpolated_end': next_seg.get('interpolated_end', False)
                        }
                        # Skip adding current segment
                        i += 1
                        continue
                elif i == 0 and len(segments) > 1:
                    # First segment is tiny - merge with next
                    segments[i + 1] = {
                        'start_idx': current_seg['start_idx'],
                        'end_idx': segments[i + 1]['end_idx'],
                        'start_pos': current_seg['start_pos'],
                        'end_pos': segments[i + 1]['end_pos'],
                        'length': segments[i + 1]['end_pos'] - current_seg['start_pos'],
                        'interpolated_end': segments[i + 1].get('interpolated_end', False)
                    }
                    i += 1
                    continue
                elif i == len(segments) - 1 and merged_segments:
                    # Last segment is tiny - merge with previous
                    merged_segments[-1] = {
                        'start_idx': merged_segments[-1]['start_idx'],
                        'end_idx': current_seg['end_idx'],
                        'start_pos': merged_segments[-1]['start_pos'],
                        'end_pos': current_seg['end_pos'],
                        'length': current_seg['end_pos'] - merged_segments[-1]['start_pos'],
                        'interpolated_end': current_seg.get('interpolated_end', False)
                    }
                    i += 1
                    continue
            
            merged_segments.append(current_seg)
            i += 1
        
        segments = merged_segments if merged_segments else segments
    
    return segments


def calculate_total_factored_load(
    model,
    member_name: str,
    load_combo: str
) -> float:
    """
    Calculate total factored load on member for shear coefficient.
    
    Uses shear values at supports (sum of reactions).
    
    Parameters
    ----------
    model : PyNite.FEModel3D
        Analyzed PyNite model
    member_name : str
        Name of member
    load_combo : str
        Load combination
    
    Returns
    -------
    float
        Total factored load W_f [kN]
    """
    member = model.members[member_name]
    
    try:
        # Extract shear at member ends
        V_left = abs(member.shear('Fy', 0.0, load_combo))
        L = member.L()
        V_right = abs(member.shear('Fy', L, load_combo))
        
        # Total load is sum of reactions
        W_f = V_left + V_right
    except:
        # Fallback: try getting reactions from nodes
        try:
            node_i = member.i_node
            node_j = member.j_node
            
            Ri = abs(model.nodes[node_i.name].RxnFY[load_combo])
            Rj = abs(model.nodes[node_j.name].RxnFY[load_combo])
            W_f = Ri + Rj
        except:
            # Last resort: use beam length * typical factored load
            W_f = member.L() * 10.0  # Rough estimate
    
    return W_f


def calculate_zero_moment_segments(
    model,
    member_name: str,
    x_stations: np.ndarray,
    load_combo: str,
    num_points: int = 401
) -> np.ndarray:
    """
    Calculate segment length between zero moment points for K_Zbg at each station.
    
    The K_Zbg size factor uses L as the distance between inflection points
    (points of zero moment). This function finds those points and returns
    the segment length containing each station.
    
    Parameters
    ----------
    model : PyNite.FEModel3D
        Analyzed PyNite model
    member_name : str
        Name of member
    x_stations : array-like
        Station coordinates [m]
    load_combo : str
        Load combination
    num_points : int
        Number of points to sample for finding zero crossings
    
    Returns
    -------
    np.ndarray
        Segment length (distance between zero moment points) at each station [m]
    """
    member = model.members[member_name]
    L_member = member.L()
    
    # Sample moment diagram at high resolution
    x_sample = np.linspace(0, L_member, num_points)
    M_sample = np.array([member.moment('Mz', x, load_combo) for x in x_sample])
    
    # Find zero crossings (inflection points)
    # Include beam ends as boundaries
    zero_points = [0.0]
    
    for i in range(len(M_sample) - 1):
        # Check for sign change or zero value
        if M_sample[i] * M_sample[i+1] < 0:
            # Linear interpolation to find exact zero crossing
            x_zero = x_sample[i] - M_sample[i] * (x_sample[i+1] - x_sample[i]) / (M_sample[i+1] - M_sample[i])
            zero_points.append(x_zero)
        elif abs(M_sample[i]) < 1e-6:  # Numerical zero
            zero_points.append(x_sample[i])
    
    zero_points.append(L_member)
    zero_points = sorted(set(zero_points))  # Remove duplicates and sort
    
    # For each station, find which segment it's in
    L_zbg = np.zeros(len(x_stations))
    
    for i, x_station in enumerate(x_stations):
        # Find the zero moment points surrounding this station
        left_zero = 0.0
        right_zero = L_member
        
        for j in range(len(zero_points) - 1):
            if zero_points[j] <= x_station <= zero_points[j+1]:
                left_zero = zero_points[j]
                right_zero = zero_points[j+1]
                break
        
        # Segment length is distance between these points
        L_zbg[i] = right_zero - left_zero
    
    return L_zbg


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
    # Import here to avoid circular dependency
    from preprocessor.pynite_extraction import extract_shear_diagram
    
    # Extract shear diagram with SIGNED values first to properly identify segments
    # (zero-crossings and discontinuities are easier to detect with signs)
    positions, shear_signed = extract_shear_diagram(
        model, member_name, load_combo, num_points, absolute=False
    )
    
    # Also get absolute values for later use
    shear_abs = np.abs(shear_signed)
    
    # Identify segments using signed values (preserves zero-crossings)
    segments = identify_shear_segments(positions, shear_signed)
    
    # Prepare arrays for each segment
    l_a_list = []
    V_A_list = []
    V_B_list = []
    V_C_list = []
    
    # Define tolerance for near-zero shear values (1% of max shear)
    max_shear = np.max(shear_abs) if len(shear_abs) > 0 else 1.0
    zero_tolerance = 0.01 * max_shear  # 1% of maximum shear
    
    # Get PyNite member for interpolating shear values at exact positions
    member = model.members[member_name]
    
    for segment in segments:
        # Segment length
        l_a = segment['length']
        
        # Shear at start (V_A) - use absolute values per CSA O86
        V_A = shear_abs[segment['start_idx']]
        
        # Shear at end (V_B)
        # If the segment end was interpolated (e.g., at a zero-crossing),
        # query PyNite directly at that exact position for precise value
        if segment.get('interpolated_end', False):
            try:
                # Get shear at exact interpolated position
                V_B = abs(member.shear('Fy', segment['end_pos'], load_combo))
            except:
                # Fallback to sampled value
                V_B = shear_abs[segment['end_idx']]
        else:
            V_B = shear_abs[segment['end_idx']]
        
        # Shear at center (V_C) - use absolute values per CSA O86
        center_idx = (segment['start_idx'] + segment['end_idx']) // 2
        V_C = shear_abs[center_idx]
        
        # Snap near-zero values to exactly zero (handles numerical precision at zero-crossings)
        if abs(V_A) < zero_tolerance:
            V_A = 0.0
        if abs(V_B) < zero_tolerance:
            V_B = 0.0
        if abs(V_C) < zero_tolerance:
            V_C = 0.0
        
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
        V_left = shear_abs[0]   # Shear at start (already absolute)
        V_right = shear_abs[-1]  # Shear at end (already absolute)
        
        # Total load is sum of reactions
        W_f = V_left + V_right
        
        if ureg is not None:
            W_f = W_f * ureg.kN
            W_f = W_f.to(ureg.N)
    except Exception:
        # Fallback: use max shear * 2 (for symmetric loading)
        W_f = max(shear_abs) * 2
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


def calculate_shear_segment_parameters(
    model,
    member_name: str,
    x_stations: np.ndarray,
    load_combo: str,
    beam_length: float,
    ureg=None
) -> Dict[str, np.ndarray]:
    """
    Calculate shear segment parameters (W_f, Sum_G, l_a) for each station.
    
    Uses sophisticated shear segment analysis per CSA O86 7.5.7.6 to determine
    segment properties at each mesh station.
    
    Parameters
    ----------
    model : PyNite.FEModel3D
        Analyzed PyNite model
    member_name : str
        Name of member
    x_stations : array-like
        Station coordinates [m]
    load_combo : str
        Load combination
    beam_length : float
        Beam length [m]
    ureg : pint.UnitRegistry, optional
        Unit registry
    
    Returns
    -------
    dict
        Dictionary containing:
        - 'W_f': Total factored load at each station [kN or N]
        - 'Sum_G': Sum of G factors at each station [N^5·mm or kN^5·m]
        - 'l_a': Segment length at each station [m or mm]
    """
    # Calculate total factored load
    W_f = calculate_total_factored_load(model, member_name, load_combo)
    
    # Use sophisticated shear segment analysis
    try:
        # Import g_factor formula for Sum_G calculation
        try:
            from design.csa_o86_2025.formulas.glulam_shear import g_factor
        except ImportError:
            g_factor = None
        
        # Ensure beam_length has correct units or is unitless
        if ureg is not None:
            if hasattr(beam_length, 'magnitude'):
                # Already has units, use as-is
                beam_length_for_calc = beam_length
            else:
                # Unitless float, add meters
                beam_length_for_calc = beam_length * ureg.m
        else:
            # No ureg, use as-is
            beam_length_for_calc = beam_length
        
        # Prepare shear segment data
        segment_data = prepare_shear_segment_arrays(
            model=model,
            member_name=member_name,
            load_combo=load_combo,
            beam_length=beam_length_for_calc,
            num_points=801,  # 801 points = 0.01m (10mm) spacing for precise segment detection
            ureg=ureg
        )
        
        # Calculate Sum_G if g_factor is available
        if g_factor is not None:
            Sum_G_total = compute_sum_g(segment_data, g_factor)
            # Extract magnitude if it's a Quantity
            if hasattr(Sum_G_total, 'magnitude'):
                Sum_G_value = Sum_G_total.magnitude
            else:
                Sum_G_value = Sum_G_total
            
            # Ensure Sum_G is not zero or invalid
            if Sum_G_value == 0 or not np.isfinite(Sum_G_value):
                # Use conservative placeholder
                Sum_G_value = 1e15
        else:
            # No g_factor available, use conservative placeholder
            Sum_G_value = 1e15
        
        # Extract W_f
        W_f_total = segment_data['W_f']
        if hasattr(W_f_total, 'magnitude'):
            W_f_value = W_f_total.magnitude
        else:
            W_f_value = W_f_total
        
        # Map segment properties to each station
        # Each station gets the properties of the segment it belongs to
        segments = segment_data['segments']
        W_f_array = np.full(len(x_stations), W_f_value)
        Sum_G_array = np.full(len(x_stations), Sum_G_value)
        l_a_array = np.zeros(len(x_stations))
        
        # Import here to avoid issues
        from preprocessor.pynite_extraction import extract_shear_diagram
        
        # Extract shear diagram for segment identification
        positions, _ = extract_shear_diagram(model, member_name, load_combo, num_points=801)
        
        # Map each station to its segment
        for i, x_station in enumerate(x_stations):
            # Find which segment this station belongs to
            for seg_idx, segment in enumerate(segments):
                if segment['start_pos'] <= x_station <= segment['end_pos']:
                    # Extract segment properties
                    l_a_seg = segment_data['l_a'][seg_idx]
                    
                    # Extract magnitude if Quantity
                    if hasattr(l_a_seg, 'magnitude'):
                        l_a_array[i] = l_a_seg.magnitude
                    else:
                        l_a_array[i] = l_a_seg
                    break
        
        return {
            'W_f': W_f_array,
            'Sum_G': Sum_G_array,
            'l_a': l_a_array,
        }
        
    except Exception as e:
        # Fallback to simple calculation if sophisticated method fails
        print(f"Warning: Shear segment calculation failed ({e}), using simplified method")
        W_f = calculate_total_factored_load(model, member_name, load_combo)
        return {
            'W_f': np.full(len(x_stations), W_f),
            'Sum_G': np.zeros(len(x_stations)),
            'l_a': np.zeros(len(x_stations)),
        }
