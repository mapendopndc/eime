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
            - 'l_a', 'l_b': Shear segment distances
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
        l_b = self._extract_demand('l_b', x_stations, default_value=0.0)
        
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
            'l_b': l_b,
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
        if load_case not in load_cases:
            return np.zeros(len(x_stations))
        
        case_data = load_cases[load_case]
        demand_key = f'{demand_type}'
        
        return self._extract_demand(demand_key, x_stations, default_value=0.0) if demand_key in case_data else np.zeros(len(x_stations))


class LoadDurationMapper:
    """
    Maps load duration parameters to mesh stations.
    
    Determines which load combination governs at each station and calculates
    the corresponding load duration ratios (P_L/P_S).
    
    Parameters
    ----------
    mesh : BeamMesh
        Mesh defining design stations
    analysis_params : dict
        Analysis parameters from AnalysisMapper
    
    Examples
    --------
    >>> mapper = LoadDurationMapper(mesh, analysis_params)
    >>> params = mapper.map()
    >>> params['P_L_M']  # Long-term moment ratio at each station
    """
    
    def __init__(self, mesh: BeamMesh, analysis_params: Dict[str, np.ndarray]):
        self.mesh = mesh
        self.analysis_params = analysis_params
    
    def map(self) -> Dict[str, np.ndarray]:
        """
        Map load duration parameters to all mesh stations.
        
        Returns
        -------
        dict
            Dictionary with arrays aligned to mesh stations:
            - 'P_L_M': Long-term moment duration ratio
            - 'P_S_M': Short-term moment duration ratio
            - 'P_L_V': Long-term shear duration ratio
            - 'P_S_V': Short-term shear duration ratio
            - 'P_L_P': Long-term axial duration ratio
            - 'P_S_P': Short-term axial duration ratio
        """
        n = self.mesh.num_stations
        
        # Calculate duration ratios based on load case contributions
        P_L_M = self._calculate_duration_ratio('M', 'L')
        P_S_M = self._calculate_duration_ratio('M', 'S')
        
        P_L_V = self._calculate_duration_ratio('V', 'L')
        P_S_V = self._calculate_duration_ratio('V', 'S')
        
        P_L_P = self._calculate_duration_ratio('P', 'L')
        P_S_P = self._calculate_duration_ratio('P', 'S')
        
        return {
            'P_L_M': P_L_M,
            'P_S_M': P_S_M,
            'P_L_V': P_L_V,
            'P_S_V': P_S_V,
            'P_L_P': P_L_P,
            'P_S_P': P_S_P,
        }
    
    def _calculate_duration_ratio(self, demand_type: str, duration_type: str) -> np.ndarray:
        """Calculate duration ratio for specific demand and duration type."""
        # Extract demand arrays
        D_key = f'{demand_type}_D'
        L_key = f'{demand_type}_L'
        S_key = f'{demand_type}_S'
        total_key = f'{demand_type}_f'
        
        D = np.abs(self.analysis_params.get(D_key, 0.0))
        L = np.abs(self.analysis_params.get(L_key, 0.0))
        S = np.abs(self.analysis_params.get(S_key, 0.0))
        total = np.abs(self.analysis_params.get(total_key, 1.0))
        
        # Avoid division by zero
        total = np.where(total == 0, 1.0, total)
        
        if duration_type == 'L':
            # Long-term ratio: (D + L) / total
            ratio = (D + L) / total
        elif duration_type == 'S':
            # Short-term ratio: S / total
            ratio = S / total
        else:
            ratio = np.zeros_like(total)
        
        return ratio


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
