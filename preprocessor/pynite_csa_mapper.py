"""
PyNite FEM analysis orchestration for CSA O86 design.

This module coordinates extraction of PyNite analysis results and preparation
for CSA O86 design checks. Acts as a bridge between PyNite models and the
design workflow.
"""

import numpy as np
from typing import Dict, List, Optional

# Import low-level PyNite extraction utilities
from preprocessor.pynite_extraction import (
    extract_all_demands,
)

# Import CSA O86-specific shear segment analysis
from design.csa_o86_2025.shear_segments import (
    calculate_zero_moment_segments,
    calculate_shear_segment_parameters,
)


def map_pynite_to_stations(
    model,
    member_name: str,
    x_stations: np.ndarray,
    load_combo: str,
    load_cases: Optional[List[str]] = None,
    beam_length: Optional[float] = None,
    ureg=None
) -> Dict[str, np.ndarray]:
    """
    Complete mapping of PyNite results to beam mesh stations.
    
    Combines all extraction functions to provide complete demand data
    ready for AnalysisMapper, including sophisticated shear segment analysis.
    
    Parameters
    ----------
    model : PyNite.FEModel3D
        Analyzed PyNite model
    member_name : str
        Name of member to extract from
    x_stations : array-like
        Station coordinates for extraction [m]
    load_combo : str
        Factored load combination
    load_cases : list of str, optional
        Individual load cases for K_D calculation
    beam_length : float, optional
        Beam length [m]. If None, will be extracted from model.
    ureg : pint.UnitRegistry, optional
        Unit registry
    
    Returns
    -------
    dict
        Complete demands dictionary ready for AnalysisMapper
    
    Examples
    --------
    >>> demands = map_pynite_to_stations(
    ...     model, 'M1', mesh.x_stations, 'ULS', 
    ...     load_cases=['D', 'L', 'S'],
    ...     beam_length=8.0,
    ...     ureg=ureg
    ... )
    >>> mapper = AnalysisMapper(mesh, demands, ureg)
    """
    # Get beam length if not provided
    if beam_length is None:
        member = model.members[member_name]
        beam_length = member.L()
    
    # Extract all demands in a single consolidated loop (more efficient)
    results = extract_all_demands(model, member_name, x_stations, load_combo, load_cases)
    
    # Calculate shear segment parameters using sophisticated analysis
    shear_params = calculate_shear_segment_parameters(
        model=model,
        member_name=member_name,
        x_stations=x_stations,
        load_combo=load_combo,
        beam_length=beam_length,
        ureg=ureg
    )
    
    # Add shear parameters to results
    results.update(shear_params)
    
    # Calculate zero-moment segment lengths for K_Zbg
    L_zbg = calculate_zero_moment_segments(
        model=model,
        member_name=member_name,
        x_stations=x_stations,
        load_combo=load_combo
    )
    results['L_zbg'] = L_zbg
    
    return results
