"""
Beam mesh generation for design stations.

This module provides the BeamMesh class for generating discretization points
along a beam where design calculations will be performed.
"""

import numpy as np
from typing import Optional, List
from .geometry import Beam


class BeamMesh:
    """
    Generates mesh of design stations along a beam.
    
    Creates discretization points (x-coordinates) where design calculations
    will be performed. Supports uniform spacing and adaptive refinement at
    discontinuities.
    
    Parameters
    ----------
    beam : Beam
        Beam geometry to mesh
    spacing : float, optional
        Target spacing between stations. Default is beam_length/100.
    refine_at_discontinuities : bool, optional
        If True, add stations at supports and bracing points. Default is True.
    custom_stations : array-like, optional
        Additional x-coordinates to include in mesh.
    
    Examples
    --------
    Uniform mesh with 50 stations:
    >>> beam = Beam(support_locations=[0, 8])
    >>> mesh = BeamMesh(beam, spacing=0.16)
    
    Mesh refined at supports and bracing:
    >>> beam = Beam(support_locations=[0, 6, 12], bracing_locations=[0, 2, 4, 6, 8, 10, 12])
    >>> mesh = BeamMesh(beam, refine_at_discontinuities=True)
    """
    
    def __init__(
        self, 
        beam: Beam,
        spacing: Optional[float] = None,
        refine_at_discontinuities: bool = True,
        custom_stations: Optional[List[float]] = None
    ):
        self.beam = beam
        self.spacing = spacing or beam.total_length / 100
        self.refine_at_discontinuities = refine_at_discontinuities
        self.custom_stations = custom_stations
        
        self._x_stations = self._generate_stations()
    
    def _generate_stations(self) -> np.ndarray:
        """Generate mesh stations along beam."""
        stations = []
        
        # Start with uniform spacing
        num_points = int(np.ceil(self.beam.total_length / self.spacing)) + 1
        uniform_stations = np.linspace(0, self.beam.total_length, num_points)
        stations.append(uniform_stations)
        
        # Add discontinuities if requested
        if self.refine_at_discontinuities:
            # Add all supports
            stations.append(self.beam.support_locations)
            
            # Add all bracing points
            stations.append(self.beam.bracing_locations)
        
        # Add custom stations
        if self.custom_stations is not None:
            stations.append(np.array(self.custom_stations))
        
        # Combine and sort, removing duplicates
        all_stations = np.concatenate(stations)
        all_stations = np.unique(all_stations)
        
        # Filter to beam bounds
        all_stations = all_stations[
            (all_stations >= 0) & (all_stations <= self.beam.total_length)
        ]
        
        return all_stations
    
    @property
    def x_stations(self) -> np.ndarray:
        """Array of x-coordinates for design stations."""
        return self._x_stations
    
    @property
    def num_stations(self) -> int:
        """Number of design stations in mesh."""
        return len(self._x_stations)
    
    def add_stations(self, x_coords: List[float]):
        """
        Add additional stations to mesh and regenerate.
        
        Parameters
        ----------
        x_coords : array-like
            x-coordinates to add
        """
        if self.custom_stations is None:
            self.custom_stations = []
        
        self.custom_stations.extend(x_coords)
        self._x_stations = self._generate_stations()
    
    def __repr__(self) -> str:
        return (f"BeamMesh(num_stations={self.num_stations}, "
                f"spacing={self.spacing:.3f}, "
                f"range=[{self._x_stations[0]:.2f}, {self._x_stations[-1]:.2f}])")
    
    def __len__(self) -> int:
        return self.num_stations
