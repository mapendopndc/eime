"""
Beam geometry definition and parameter queries.

This module provides the Beam class for defining beam geometry including
spans, supports, and lateral bracing locations.
"""

import numpy as np
from typing import List, Tuple, Optional


class Beam:
    """
    Defines beam geometry with supports and bracing.
    
    A beam is defined by support locations along its length. Supports divide
    the beam into spans. Bracing locations define lateral support points.
    
    Parameters
    ----------
    support_locations : array-like
        x-coordinates of supports along beam length (must include start and end).
        Units should be consistent (e.g., all in meters).
    bracing_locations : array-like, optional
        x-coordinates of lateral bracing points. If None, no intermediate bracing.
    
    Examples
    --------
    Single span beam with three bracing points:
    >>> beam = Beam(support_locations=[0, 8], bracing_locations=[0, 4, 8])
    
    Three-span continuous beam:
    >>> beam = Beam(support_locations=[0, 6, 12, 18])
    """
    
    def __init__(self, support_locations: List[float], bracing_locations: Optional[List[float]] = None):
        self.support_locations = np.array(sorted(support_locations))
        
        if bracing_locations is None:
            self.bracing_locations = self.support_locations.copy()
        else:
            self.bracing_locations = np.array(sorted(bracing_locations))
        
        if len(self.support_locations) < 2:
            raise ValueError("Beam must have at least two supports (start and end)")
        
        if self.support_locations[0] != 0:
            raise ValueError("First support must be at x=0")
    
    @property
    def total_length(self) -> float:
        """Total length of beam from first to last support."""
        return self.support_locations[-1]
    
    @property
    def num_spans(self) -> int:
        """Number of spans (segments between supports)."""
        return len(self.support_locations) - 1
    
    @property
    def span_lengths(self) -> np.ndarray:
        """Length of each span."""
        return np.diff(self.support_locations)
    
    def get_span_at(self, x: float) -> int:
        """
        Get span number containing position x.
        
        Parameters
        ----------
        x : float
            Position along beam
            
        Returns
        -------
        int
            Span index (0-based). Returns -1 if x is outside beam.
        """
        if x < 0 or x > self.total_length:
            return -1
        
        for i in range(self.num_spans):
            if self.support_locations[i] <= x <= self.support_locations[i + 1]:
                return i
        
        return -1
    
    def get_span_length_at(self, x: float) -> float:
        """
        Get length of span containing position x.
        
        Parameters
        ----------
        x : float
            Position along beam
            
        Returns
        -------
        float
            Length of span containing x. Returns 0 if x is outside beam.
        """
        span_idx = self.get_span_at(x)
        if span_idx < 0:
            return 0.0
        return self.span_lengths[span_idx]
    
    def get_nearest_supports(self, x: float) -> Tuple[float, float]:
        """
        Get support locations on either side of position x.
        
        Parameters
        ----------
        x : float
            Position along beam
            
        Returns
        -------
        tuple of (left_support, right_support)
            Support locations bounding x. Returns (0, 0) if x is outside beam.
        """
        span_idx = self.get_span_at(x)
        if span_idx < 0:
            return (0.0, 0.0)
        
        return (self.support_locations[span_idx], self.support_locations[span_idx + 1])
    
    def get_unbraced_length(self, x: float) -> float:
        """
        Get unbraced length at position x.
        
        Returns the distance between bracing points on either side of x.
        
        Parameters
        ----------
        x : float
            Position along beam
            
        Returns
        -------
        float
            Distance between adjacent bracing points. Returns 0 if x is outside beam.
        """
        if x < 0 or x > self.total_length:
            return 0.0
        
        # Find bracing points on either side
        left_brace = self.bracing_locations[self.bracing_locations <= x]
        right_brace = self.bracing_locations[self.bracing_locations >= x]
        
        if len(left_brace) == 0 or len(right_brace) == 0:
            return 0.0
        
        return right_brace[0] - left_brace[-1]
    
    def get_support_proximity(self, x: float) -> float:
        """
        Get distance from x to nearest support.
        
        Parameters
        ----------
        x : float
            Position along beam
            
        Returns
        -------
        float
            Distance to nearest support. Returns inf if x is outside beam.
        """
        if x < 0 or x > self.total_length:
            return np.inf
        
        distances = np.abs(self.support_locations - x)
        return np.min(distances)
    
    def __repr__(self) -> str:
        return (f"Beam(length={self.total_length:.2f}, "
                f"spans={self.num_spans}, "
                f"supports={len(self.support_locations)}, "
                f"bracing_pts={len(self.bracing_locations)})")
