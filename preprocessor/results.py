"""
Beam design results with spatial mapping.

This module provides classes for working with design results in the context
of beam geometry and mesh stations.
"""

import numpy as np
import pandas as pd
from typing import Optional, List, Tuple, Dict
from .mesh import BeamMesh


class BeamDesignResults:
    """
    Wraps TimberMember design results with beam-aware functionality.
    
    Provides methods to query results by position, find governing locations,
    and extract spatially-aware design summaries.
    
    Parameters
    ----------
    results : pd.DataFrame
        Design results DataFrame from TimberMember
    mesh : BeamMesh
        Mesh defining station locations
    x_stations : array-like, optional
        Station x-coordinates (if not in results DataFrame)
    
    Examples
    --------
    >>> beam_results = BeamDesignResults(member.design_results, mesh)
    >>> worst = beam_results.find_governing_stations()
    >>> util = beam_results.get_utilization_at(4.5)  # Utilization at x=4.5m
    """
    
    def __init__(
        self, 
        results: pd.DataFrame, 
        mesh: BeamMesh,
        x_stations: Optional[np.ndarray] = None
    ):
        self.results = results
        self.mesh = mesh
        
        # Get x-coordinates
        if x_stations is not None:
            self.x_stations = np.array(x_stations)
        elif 'x_station' in results.columns:
            self.x_stations = results['x_station'].values
        else:
            self.x_stations = mesh.x_stations
        
        # Validate alignment
        if len(self.results) != len(self.x_stations):
            raise ValueError("Results length does not match stations length")
    
    def find_governing_stations(self) -> Dict[str, Tuple[int, float, float]]:
        """
        Find stations with maximum utilization for each check type.
        
        Returns
        -------
        dict
            Dictionary with keys for each check type (e.g., 'bending', 'shear')
            and values as (station_index, x_position, utilization)
        
        Examples
        --------
        >>> governing = beam_results.find_governing_stations()
        >>> idx, x, util = governing['bending']
        >>> print(f"Worst bending at x={x:.2f}m with util={util:.1%}")
        """
        governing = {}
        
        # Check for common utilization columns
        util_columns = {
            'bending': 'bending_utilization',
            'shear': 'shear_utilization',
            'compression': 'compression_utilization',
        }
        
        for check_name, col_name in util_columns.items():
            if col_name in self.results.columns:
                idx = self.results[col_name].idxmax()
                util = self.results.loc[idx, col_name]
                x = self.x_stations[idx]
                governing[check_name] = (idx, x, util)
        
        return governing
    
    def get_utilization_at(self, x: float, check_type: str = 'bending') -> float:
        """
        Get utilization at specific x-coordinate.
        
        Interpolates if x is not exactly at a station.
        
        Parameters
        ----------
        x : float
            Position along beam
        check_type : str
            Type of check ('bending', 'shear', 'compression')
        
        Returns
        -------
        float
            Utilization ratio at position x
        """
        col_name = f'{check_type}_utilization'
        
        if col_name not in self.results.columns:
            raise ValueError(f"No utilization data for check type '{check_type}'")
        
        utils = self.results[col_name].values
        return float(np.interp(x, self.x_stations, utils))
    
    def get_results_at(self, x: float) -> pd.Series:
        """
        Get all results at specific x-coordinate.
        
        Parameters
        ----------
        x : float
            Position along beam
        
        Returns
        -------
        pd.Series
            All result values at position x (interpolated)
        """
        # Find nearest station
        idx = np.argmin(np.abs(self.x_stations - x))
        return self.results.iloc[idx]
    
    def get_critical_sections(self, utilization_threshold: float = 0.8) -> pd.DataFrame:
        """
        Find all sections exceeding utilization threshold.
        
        Parameters
        ----------
        utilization_threshold : float
            Minimum utilization to be considered critical
        
        Returns
        -------
        pd.DataFrame
            Results for critical sections with x-coordinates
        """
        # Find maximum utilization across all check types
        util_cols = [col for col in self.results.columns if 'utilization' in col]
        
        if not util_cols:
            return pd.DataFrame()
        
        max_util = self.results[util_cols].max(axis=1)
        critical_mask = max_util >= utilization_threshold
        
        critical_results = self.results[critical_mask].copy()
        critical_results['x_position'] = self.x_stations[critical_mask]
        critical_results['max_utilization'] = max_util[critical_mask]
        
        return critical_results.sort_values('max_utilization', ascending=False)
    
    def summary(self) -> str:
        """
        Generate text summary of design results.
        
        Returns
        -------
        str
            Formatted summary of governing results
        """
        governing = self.find_governing_stations()
        
        lines = ["Beam Design Results Summary", "=" * 50]
        
        for check_name, (idx, x, util) in governing.items():
            status = "PASS" if util <= 1.0 else "FAIL"
            lines.append(
                f"{check_name.capitalize():<15} "
                f"x={x:6.2f}m  "
                f"util={util:6.1%}  "
                f"{status}"
            )
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"BeamDesignResults(stations={len(self.x_stations)}, checks={len(self.results.columns)})"
