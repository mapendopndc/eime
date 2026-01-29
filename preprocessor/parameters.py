"""
Parameter mapping for beam design stations.

This module provides mappers that extract design parameters at each mesh station
and an assembler that combines them for vectorized design calculations.
"""

import numpy as np
from typing import Dict, Any, Optional
from .geometry import Beam
from .mesh import BeamMesh


class GeometryMapper:
    """
    Maps geometric parameters to mesh stations.
    
    Extracts beam geometry parameters (span length, unbraced length, etc.)
    at each station in the mesh.
    
    Parameters
    ----------
    beam : Beam
        Beam geometry
    mesh : BeamMesh
        Mesh defining design stations
    
    Examples
    --------
    >>> beam = Beam(support_locations=[0, 6, 12])
    >>> mesh = BeamMesh(beam, spacing=0.5)
    >>> mapper = GeometryMapper(beam, mesh)
    >>> params = mapper.map()
    >>> params['span_lengths']  # Array of span lengths at each station
    """
    
    def __init__(self, beam: Beam, mesh: BeamMesh):
        self.beam = beam
        self.mesh = mesh
    
    def map(self) -> Dict[str, np.ndarray]:
        """
        Map geometric parameters to all mesh stations.
        
        Returns
        -------
        dict
            Dictionary with arrays aligned to mesh stations:
            - 'span_lengths': Span length at each station
            - 'lu_strong': Unbraced length (strong axis) at each station
            - 'lu_weak': Unbraced length (weak axis) at each station
            - 'support_proximity': Distance to nearest support
            - 'span_indices': Which span each station belongs to
        """
        x_stations = self.mesh.x_stations
        n = len(x_stations)
        
        span_lengths = np.zeros(n)
        lu_strong = np.zeros(n)
        lu_weak = np.zeros(n)
        support_proximity = np.zeros(n)
        span_indices = np.zeros(n, dtype=int)
        
        for i, x in enumerate(x_stations):
            span_lengths[i] = self.beam.get_span_length_at(x)
            lu_strong[i] = self.beam.get_unbraced_length(x)
            lu_weak[i] = self.beam.get_unbraced_length(x)  # Same for now, could differ
            support_proximity[i] = self.beam.get_support_proximity(x)
            span_indices[i] = self.beam.get_span_at(x)
        
        return {
            'span_lengths': span_lengths,
            'lu_strong': lu_strong,
            'lu_weak': lu_weak,
            'support_proximity': support_proximity,
            'span_indices': span_indices,
        }


class AnalysisMapper:
    """
    Maps structural analysis results to mesh stations.
    
    Extracts demand values (M, V, P) and shear segment parameters from
    structural analysis at each station.
    
    Parameters
    ----------
    mesh : BeamMesh
        Mesh defining design stations
    demands : dict
        Analysis results containing demand arrays or functions
    ureg : pint.UnitRegistry, optional
        Unit registry for unit handling
    
    Examples
    --------
    >>> demands = {
    ...     'M_f': moment_array,
    ...     'V_f': shear_array,
    ...     'P_f': axial_array,
    ...     'load_cases': {'D': {...}, 'L': {...}, 'S': {...}}
    ... }
    >>> mapper = AnalysisMapper(mesh, demands)
    >>> params = mapper.map()
    """
    
    def __init__(self, mesh: BeamMesh, demands: Dict[str, Any], ureg=None):
        self.mesh = mesh
        self.demands = demands
        self.ureg = ureg
    
    def map(self) -> Dict[str, np.ndarray]:
        """
        Map analysis results to all mesh stations.
        
        Returns
        -------
        dict
            Dictionary with arrays aligned to mesh stations:
            - 'M_f': Factored moment at each station
            - 'V_f': Factored shear at each station
            - 'P_f': Factored axial force at each station
            - 'M_D', 'M_L', 'M_S': Moments by load case (for K_D)
            - 'V_D', 'V_L', 'V_S': Shears by load case (for K_D)
            - 'W_f': Total factored load for shear coefficient
            - 'Sum_G': Sum of G factors for shear coefficient
            - 'l_a': Shear segment distance
        """
        x_stations = self.mesh.x_stations
        n = len(x_stations)
        
        # Extract factored demands
        M_f = self._extract_demand('M_f', x_stations)
        V_f = self._extract_demand('V_f', x_stations)
        P_f = self._extract_demand('P_f', x_stations, default_value=0.0)
        
        # Extract load case demands (for K_D calculation)
        load_cases = self.demands.get('load_cases', {})
        M_D = self._extract_load_case('M', 'D', x_stations, load_cases)
        M_L = self._extract_load_case('M', 'L', x_stations, load_cases)
        M_S = self._extract_load_case('M', 'S', x_stations, load_cases)
        
        V_D = self._extract_load_case('V', 'D', x_stations, load_cases)
        V_L = self._extract_load_case('V', 'L', x_stations, load_cases)
        V_S = self._extract_load_case('V', 'S', x_stations, load_cases)
        
        # Shear segment parameters
        W_f = self._extract_demand('W_f', x_stations, default_value=0.0)
        Sum_G = self._extract_demand('Sum_G', x_stations, default_value=0.0)
        l_a = self._extract_demand('l_a', x_stations, default_value=0.0)
        
        # Bending size factor segment length (distance between zero moment points)
        L_zbg = self._extract_demand('L_zbg', x_stations, default_value=0.0)
        
        return {
            'M_f': M_f,
            'V_f': V_f,
            'P_f': P_f,
            'M_D': M_D,
            'M_L': M_L,
            'M_S': M_S,
            'V_D': V_D,
            'V_L': V_L,
            'V_S': V_S,
            'W_f': W_f,
            'Sum_G': Sum_G,
            'l_a': l_a,
            'L_zbg': L_zbg,
        }
    
    def _extract_demand(self, key: str, x_stations: np.ndarray, default_value: float = 0.0) -> np.ndarray:
        """Extract demand values at stations."""
        demand = self.demands.get(key, None)
        
        if demand is None:
            return np.full(len(x_stations), default_value)
        
        # If it's already an array
        if isinstance(demand, (np.ndarray, list)):
            demand_array = np.array(demand)
            # Check if same length as stations
            if len(demand_array) == len(x_stations):
                return demand_array
            # Otherwise interpolate
            # Assume uniform spacing for now
            x_orig = np.linspace(0, x_stations[-1], len(demand_array))
            return np.interp(x_stations, x_orig, demand_array)
        
        # If it's a callable (function of x)
        if callable(demand):
            return np.array([demand(x) for x in x_stations])
        
        # If it's a scalar
        return np.full(len(x_stations), float(demand))
    
    def _extract_load_case(
        self, 
        demand_type: str, 
        load_case: str, 
        x_stations: np.ndarray,
        load_cases: Dict
    ) -> np.ndarray:
        """Extract demand for specific load case."""
        # First check if demand is already flattened (e.g., M_D, V_L, etc.)
        flattened_key = f'{demand_type}_{load_case}'
        if flattened_key in self.demands:
            return self._extract_demand(flattened_key, x_stations, default_value=0.0)
        
        # Otherwise extract from load_cases structure
        if load_case not in load_cases:
            return np.zeros(len(x_stations))
        
        case_data = load_cases[load_case]
        demand_key = f'{demand_type}'
        
        if demand_key not in case_data:
            return np.zeros(len(x_stations))
        
        # Extract directly from case_data
        demand = case_data[demand_key]
        if isinstance(demand, (np.ndarray, list)):
            demand_array = np.array(demand)
            if len(demand_array) == len(x_stations):
                return demand_array
        
        return np.zeros(len(x_stations))


class LoadDurationMapper:
    """
    Maps load duration parameters to mesh stations.
    
    Determines which load combination governs at each station and calculates
    the corresponding load duration ratios (P_L/P_S). Automatically detects
    which load cases are active based on the actual load values.
    
    Parameters
    ----------
    mesh : BeamMesh
        Mesh defining design stations
    analysis_params : dict
        Analysis parameters from AnalysisMapper
    active_load_cases : list of str, optional
        List of load cases that are active in the current combination.
        e.g., ['D', 'L'] or ['D', 'S']. If None, auto-detects from data.
    
    Examples
    --------
    >>> mapper = LoadDurationMapper(mesh, analysis_params, active_load_cases=['D', 'L'])
    >>> params = mapper.map()
    >>> params['P_L_M']  # Long-term moment ratio at each station
    """
    
    def __init__(self, mesh: BeamMesh, analysis_params: Dict[str, np.ndarray], active_load_cases: Optional[List[str]] = None):
        self.mesh = mesh
        self.analysis_params = analysis_params
        self.active_load_cases = active_load_cases
    
    def map(self) -> Dict[str, np.ndarray]:
        """
        Map load duration parameters to all mesh stations.
        
        Returns
        -------
        dict
            Dictionary with arrays aligned to mesh stations:
            - 'P_L_M': Long-term (Dead) moment load proportion
            - 'P_S_M': Standard-term (Live or Snow) moment load proportion
            - 'P_L_V': Long-term (Dead) shear load proportion
            - 'P_S_V': Standard-term (Live or Snow) shear load proportion
            - 'P_L_P': Long-term (Dead) axial load proportion
            - 'P_S_P': Standard-term (Live or Snow) axial load proportion
            - 'governing_Ps_M': Governing P_S combination for moment (str array)
            - 'governing_Ps_V': Governing P_S combination for shear (str array)
            - 'governing_Ps_P': Governing P_S combination for axial (str array)
        """
        n = self.mesh.num_stations
        
        # Calculate duration ratios based on load case contributions
        P_L_M = self._calculate_duration_ratio('M', 'L')
        P_S_M, governing_Ps_M = self._calculate_duration_ratio_with_governing('M', 'S')
        
        P_L_V = self._calculate_duration_ratio('V', 'L')
        P_S_V, governing_Ps_V = self._calculate_duration_ratio_with_governing('V', 'S')
        
        P_L_P = self._calculate_duration_ratio('P', 'L')
        P_S_P, governing_Ps_P = self._calculate_duration_ratio_with_governing('P', 'S')
        
        return {
            'P_L_M': P_L_M,
            'P_S_M': P_S_M,
            'P_L_V': P_L_V,
            'P_S_V': P_S_V,
            'P_L_P': P_L_P,
            'P_S_P': P_S_P,
            'governing_Ps_M': governing_Ps_M,
            'governing_Ps_V': governing_Ps_V,
            'governing_Ps_P': governing_Ps_P,
        }
    
    def _calculate_duration_ratio(self, demand_type: str, duration_type: str) -> np.ndarray:
        """
        Calculate duration ratio for specific demand and duration type.
        
        Per CSA O86:24 cl.5.3.2.2:
        - P_L (long-term): Dead load proportion = D / (D + L + S)
        - P_S (standard-term): Minimum of possible standard-term combinations
          to get most conservative (lowest) K_D when dead dominates.
          P_S = min(L, S, S+0.5L, 0.5S+L) / (D + L + S)
        
        Automatically detects which loads are active by checking for non-zero values.
        
        Note: Proportions are based on UNFACTORED loads and should sum to ≤ 1.0
        """
        # Extract demand arrays
        D_key = f'{demand_type}_D'
        L_key = f'{demand_type}_L'
        S_key = f'{demand_type}_S'
        
        # Get zero array with correct shape for missing demands
        n = self.mesh.num_stations
        zeros = np.zeros(n)
        
        D = np.abs(self.analysis_params.get(D_key, zeros))
        L = np.abs(self.analysis_params.get(L_key, zeros))
        S = np.abs(self.analysis_params.get(S_key, zeros))
        
        # Detect which loads are active
        # If active_load_cases was explicitly provided, use that
        # Otherwise, auto-detect from non-zero values
        if self.active_load_cases is not None:
            has_dead = 'D' in self.active_load_cases
            has_live = 'L' in self.active_load_cases
            has_snow = 'S' in self.active_load_cases
        else:
            # Auto-detect using a small tolerance to account for numerical precision
            tolerance = 1e-10
            has_dead = np.any(D > tolerance)
            has_live = np.any(L > tolerance)
            has_snow = np.any(S > tolerance)
        
        # Zero out inactive loads
        if not has_dead:
            D = zeros
        if not has_live:
            L = zeros
        if not has_snow:
            S = zeros
        
        # Total UNFACTORED load (not factored total)
        total_unfactored = D + L + S
        
        # Avoid division by zero
        total_unfactored = np.where(total_unfactored == 0, 1.0, total_unfactored)
        
        if duration_type == 'L':
            # P_L: Long-term (Dead) load proportion only
            ratio = D / total_unfactored
        elif duration_type == 'S':
            # P_S: Standard-term load proportion
            # Use minimum of standard-term combinations for most conservative K_D
            # Possible combinations: L, S, S+0.5L, 0.5S+L
            combo1 = L
            combo2 = S
            combo3 = S + 0.5 * L
            combo4 = 0.5 * S + L
            
            # Find minimum standard-term load
            min_standard = np.minimum(
                np.minimum(combo1, combo2),
                np.minimum(combo3, combo4)
            )
            
            ratio = min_standard / total_unfactored
        else:
            ratio = np.zeros_like(total_unfactored)
        
        return ratio
    
    def _calculate_duration_ratio_with_governing(self, demand_type: str, duration_type: str):
        """
        Calculate P_S duration ratio and track which combination is governing.
        
        Automatically detects which loads are active by checking for non-zero values.
        
        Returns
        -------
        tuple
            (ratio_array, governing_combo_array) where governing_combo_array contains
            strings indicating which combination governed: 'L', 'S', 'S+0.5L', or '0.5S+L'
        """
        # Extract demand arrays
        D_key = f'{demand_type}_D'
        L_key = f'{demand_type}_L'
        S_key = f'{demand_type}_S'
        
        # Get zero array with correct shape for missing demands
        n = self.mesh.num_stations
        zeros = np.zeros(n)
        
        D = np.abs(self.analysis_params.get(D_key, zeros))
        L = np.abs(self.analysis_params.get(L_key, zeros))
        S = np.abs(self.analysis_params.get(S_key, zeros))
        
        # Detect which loads are active
        # If active_load_cases was explicitly provided, use that
        # Otherwise, auto-detect from non-zero values
        if self.active_load_cases is not None:
            has_dead = 'D' in self.active_load_cases
            has_live = 'L' in self.active_load_cases
            has_snow = 'S' in self.active_load_cases
        else:
            # Auto-detect using a small tolerance to account for numerical precision
            tolerance = 1e-10
            has_dead = np.any(D > tolerance)
            has_live = np.any(L > tolerance)
            has_snow = np.any(S > tolerance)
        
        # Zero out inactive loads
        if not has_dead:
            D = zeros
        if not has_live:
            L = zeros
        if not has_snow:
            S = zeros
        
        # Total UNFACTORED load (not factored total)
        total_unfactored = D + L + S
        
        # Avoid division by zero
        total_unfactored = np.where(total_unfactored == 0, 1.0, total_unfactored)
        
        if duration_type == 'S':
            # P_S: Standard-term load proportion
            # Only consider combinations based on which loads are present
            
            if has_live and has_snow:
                # Both L and S present: consider all 4 combinations
                combo1 = L
                combo2 = S
                combo3 = S + 0.5 * L
                combo4 = 0.5 * S + L
                
                # Stack all combinations for comparison
                combos = np.stack([combo1, combo2, combo3, combo4], axis=0)
                combo_names = ['L', 'S', 'S+0.5L', '0.5S+L']
                
            elif has_live and not has_snow:
                # Only L present: use L only
                combos = np.stack([L], axis=0)
                combo_names = ['L']
                
            elif has_snow and not has_live:
                # Only S present: use S only
                combos = np.stack([S], axis=0)
                combo_names = ['S']
                
            else:
                # Neither L nor S present: use zeros
                combos = np.stack([zeros], axis=0)
                combo_names = ['None']
            
            # Find which combination is minimum at each station
            min_indices = np.argmin(combos, axis=0)
            min_standard = np.min(combos, axis=0)
            
            # Map indices to combination names
            governing_combo = np.array([combo_names[idx] for idx in min_indices])
            
            ratio = min_standard / total_unfactored
            return ratio, governing_combo
        else:
            # For other duration types, no governing tracking needed
            ratio = self._calculate_duration_ratio(demand_type, duration_type)
            governing_combo = np.array(['N/A'] * n)
            return ratio, governing_combo


class ParameterAssembler:
    """
    Assembles all mapped parameters for vectorized design.
    
    Combines outputs from GeometryMapper, AnalysisMapper, and LoadDurationMapper
    into a unified parameter dictionary ready for TimberMember design.
    
    Parameters
    ----------
    beam : Beam
        Beam geometry
    mesh : BeamMesh
        Mesh defining design stations
    geometry_params : dict
        Output from GeometryMapper
    analysis_params : dict
        Output from AnalysisMapper
    duration_params : dict
        Output from LoadDurationMapper
    ureg : pint.UnitRegistry, optional
        Unit registry for unit handling
    beam_id_prefix : str, optional
        Prefix for beam IDs. Default is 'Beam'.
    
    Examples
    --------
    >>> assembler = ParameterAssembler(beam, mesh, geom, analysis, duration, ureg=ureg)
    >>> params = assembler.assemble()
    >>> # params ready for TimberMember(section, loading=params['loading'], ...)
    """
    
    def __init__(
        self,
        beam: Beam,
        mesh: BeamMesh,
        geometry_params: Dict[str, np.ndarray],
        analysis_params: Dict[str, np.ndarray],
        duration_params: Dict[str, np.ndarray],
        ureg=None,
        beam_id_prefix: str = 'Beam'
    ):
        self.beam = beam
        self.mesh = mesh
        self.geometry_params = geometry_params
        self.analysis_params = analysis_params
        self.duration_params = duration_params
        self.ureg = ureg
        self.beam_id_prefix = beam_id_prefix
        
        # Validate alignment
        self._validate_alignment()
    
    def _validate_alignment(self):
        """Ensure all parameter arrays have same length as mesh."""
        expected_length = self.mesh.num_stations
        
        all_params = {
            **self.geometry_params,
            **self.analysis_params,
            **self.duration_params
        }
        
        for key, value in all_params.items():
            if isinstance(value, np.ndarray):
                if len(value) != expected_length:
                    raise ValueError(
                        f"Parameter '{key}' has length {len(value)}, "
                        f"expected {expected_length} to match mesh"
                    )
    
    def assemble(self) -> Dict[str, Any]:
        """
        Assemble all parameters into unified structure.
        
        Returns
        -------
        dict
            Dictionary containing:
            - 'beam_ids': List of beam identifiers
            - 'x_stations': Station x-coordinates
            - 'geometry': Geometry parameters
            - 'demands': Demand parameters
            - 'duration': Load duration parameters
            - All individual parameter arrays
        """
        n = self.mesh.num_stations
        
        # Generate beam IDs
        beam_ids = [f"{self.beam_id_prefix}-{i:04d}" for i in range(n)]
        
        # Combine all parameters
        params = {
            'beam_ids': beam_ids,
            'x_stations': self.mesh.x_stations,
            'geometry': self.geometry_params,
            'demands': self.analysis_params,
            'duration': self.duration_params,
        }
        
        # Add flattened access to all arrays
        params.update(self.geometry_params)
        params.update(self.analysis_params)
        params.update(self.duration_params)
        
        return params
    
    def __repr__(self) -> str:
        return (f"ParameterAssembler(stations={self.mesh.num_stations}, "
                f"beam_id='{self.beam_id_prefix}')")
