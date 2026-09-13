"""
PyNite FEM result extraction utilities.

This module provides low-level functions to extract structural analysis results
from PyNite models. These are general-purpose utilities independent of any
specific design code.
"""

import numpy as np
from typing import Dict, List, Optional


def extract_member_demands(
    model,
    member_name: str,
    x_coords: np.ndarray,
    load_combo: Optional[str] = None
) -> Dict[str, np.ndarray]:
    """
    Extract demands from PyNite member at specified x-coordinates.
    
    Parameters
    ----------
    model : PyNite.FEModel3D
        Analyzed PyNite model
    member_name : str
        Name of member to extract demands from
    x_coords : array-like
        x-coordinates along member where demands are needed
    load_combo : str, optional
        Load combination name. If None, uses 'Combo 1' default.
        For individual load cases, the load case name should be passed.
    
    Returns
    -------
    dict
        Dictionary containing:
        - 'M': Bending moments at x_coords
        - 'V': Shear forces at x_coords
        - 'P': Axial forces at x_coords
    
    Examples
    --------
    >>> demands = extract_member_demands(model, 'M1', [0, 2, 4, 6, 8])
    >>> demands['M']  # Moments at specified locations
    """
    member = model.members[member_name]
    n = len(x_coords)
    
    M = np.zeros(n)
    V = np.zeros(n)
    P = np.zeros(n)
    
    for i, x in enumerate(x_coords):
        try:
            # PyNite can accept both load combos and load cases
            # If load_combo is a valid load case or combo, it will be found
            M[i] = abs(member.moment('Mz', x, load_combo))
            V[i] = abs(member.shear('Fy', x, load_combo))
            # Axial force method has different signature than moment/shear
            P[i] = abs(member.axial(x, load_combo))
        except (KeyError, ValueError) as e:
            # If the combo/case doesn't exist, try without it (default combo)
            print(f"Warning: Load combo/case '{load_combo}' not found, trying default")
            try:
                M[i] = abs(member.moment('Mz', x))
                V[i] = abs(member.shear('Fy', x))
                P[i] = abs(member.axial(x))
            except Exception as e2:
                print(f"Error extracting demands at x={x}: {e2}")
                M[i] = 0.0
                V[i] = 0.0
                P[i] = 0.0
        except Exception as e:
            print(f"Error extracting demands at x={x} for combo '{load_combo}': {e}")
            print(f"  Member: {member.name}, Load combo: {load_combo}")
            M[i] = 0.0
            V[i] = 0.0
            P[i] = 0.0
    
    return {'M': M, 'V': V, 'P': P}


def extract_load_case_demands(
    model,
    member_name: str,
    x_coords: np.ndarray,
    load_cases: List[str]
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Extract demands by load case from PyNite member.
    
    Parameters
    ----------
    model : PyNite.FEModel3D
        Analyzed PyNite model
    member_name : str
        Name of member to extract demands from
    x_coords : array-like
        x-coordinates along member where demands are needed
    load_cases : list of str
        Load case names (e.g., ['D', 'L', 'S'])
    
    Returns
    -------
    dict
        Nested dictionary: {load_case: {'M': array, 'V': array, 'P': array}}
    
    Examples
    --------
    >>> case_demands = extract_load_case_demands(model, 'M1', x_coords, ['D', 'L', 'S'])
    >>> case_demands['L']['M']  # Live load moments
    """
    results = {}
    
    for load_case in load_cases:
        results[load_case] = extract_member_demands(model, member_name, x_coords, load_case)
    
    return results


def extract_all_demands(
    model,
    member_name: str,
    x_coords: np.ndarray,
    load_combo: str,
    load_cases: Optional[List[str]] = None
) -> Dict[str, np.ndarray]:
    """
    Extract all demands (factored combo + individual load cases) in a single loop.
    
    Consolidates demand extraction to minimize PyNite member queries. Instead of
    looping N times for factored combo, then N times for each load case (total
    N×(M+1) loops), this extracts everything in a single N-station loop.
    
    Parameters
    ----------
    model : PyNite.FEModel3D
        Analyzed PyNite model
    member_name : str
        Name of member to extract demands from
    x_coords : array-like
        x-coordinates along member where demands are needed
    load_combo : str
        Factored load combination name
    load_cases : list of str, optional
        Individual load case names (e.g., ['D', 'L', 'S'])
    
    Returns
    -------
    dict
        Dictionary containing:
        - 'M_f', 'V_f', 'P_f': Factored combo demands
        - 'load_cases': {case: {'M': array, 'V': array, 'P': array}}
        - 'M_{case}', 'V_{case}', 'P_{case}': Flattened load case arrays
    
    Examples
    --------
    >>> demands = extract_all_demands(model, 'M1', x_coords, 'ULS', ['D', 'L', 'S'])
    >>> demands['M_f']  # Factored moments
    >>> demands['M_D']  # Dead load moments
    """
    member = model.members[member_name]
    n = len(x_coords)
    
    # Initialize arrays for factored combo
    M_f = np.zeros(n)
    V_f = np.zeros(n)
    P_f = np.zeros(n)
    
    # Initialize load case arrays
    load_case_data = {}
    if load_cases:
        for case in load_cases:
            load_case_data[case] = {
                'M': np.zeros(n),
                'V': np.zeros(n),
                'P': np.zeros(n),
            }
    
    # Single loop over all stations
    for i, x in enumerate(x_coords):
        try:
            # Extract factored combo demands
            # Note: Preserve moment sign for proper f_b selection (pos/neg bending)
            M_f[i] = member.moment('Mz', x, load_combo)
            V_f[i] = abs(member.shear('Fy', x, load_combo))
            P_f[i] = abs(member.axial(x, load_combo))
            
            # Extract individual load case demands
            if load_cases:
                for case in load_cases:
                    # Preserve moment sign for load case moments too
                    load_case_data[case]['M'][i] = member.moment('Mz', x, case)
                    load_case_data[case]['V'][i] = abs(member.shear('Fy', x, case))
                    load_case_data[case]['P'][i] = abs(member.axial(x, case))
        
        except (KeyError, ValueError) as e:
            # Handle missing combo/case - try default
            print(f"Warning: Issue at x={x}, trying defaults")
            try:
                M_f[i] = member.moment('Mz', x)
                V_f[i] = abs(member.shear('Fy', x))
                P_f[i] = abs(member.axial(x))
            except Exception:
                M_f[i] = V_f[i] = P_f[i] = 0.0
            
            # Zero out load case values on error
            if load_cases:
                for case in load_cases:
                    load_case_data[case]['M'][i] = 0.0
                    load_case_data[case]['V'][i] = 0.0
                    load_case_data[case]['P'][i] = 0.0
        
        except Exception as e:
            print(f"Error extracting demands at x={x}: {e}")
            M_f[i] = V_f[i] = P_f[i] = 0.0
            if load_cases:
                for case in load_cases:
                    load_case_data[case]['M'][i] = 0.0
                    load_case_data[case]['V'][i] = 0.0
                    load_case_data[case]['P'][i] = 0.0
    
    # Build results dictionary
    results = {
        'M_f': M_f,
        'V_f': V_f,
        'P_f': P_f,
    }
    
    # Add load case data
    if load_cases:
        results['load_cases'] = load_case_data
        # Also add flattened arrays for convenience
        for case in load_cases:
            results[f'M_{case}'] = load_case_data[case]['M']
            results[f'V_{case}'] = load_case_data[case]['V']
            results[f'P_{case}'] = load_case_data[case]['P']
    
    return results


def extract_shear_diagram(
    model,
    member_name: str,
    load_combo: str,
    num_points: int = 100,
    absolute: bool = True
) -> tuple[np.ndarray, np.ndarray]:
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
        If True, return absolute values (for design calculations).
        If False, return signed values (for visualization). Default: True
        
    Returns
    -------
    positions : np.ndarray
        Array of positions along member [m]
    shear_values : np.ndarray
        Array of shear force values [kN]
        
    Notes
    -----
    For design calculations requiring absolute values, set absolute=True.
    For visualization of shear diagrams, set absolute=False to preserve signs.
    
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
            # Take absolute value if requested
            shear_values[i] = abs(V) if absolute else V
        except Exception as e:
            # If extraction fails, use zero
            shear_values[i] = 0.0
    
    return positions, shear_values
