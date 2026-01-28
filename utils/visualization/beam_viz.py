"""
Beam utilization visualization.

This module provides functions to visualize design results along beam length
with support and bracing annotations.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, List


def plot_beam_utilization(
    x_stations: np.ndarray,
    utilizations: dict,
    support_locations: Optional[np.ndarray] = None,
    bracing_locations: Optional[np.ndarray] = None,
    figsize: tuple = (12, 8),
    title: str = "Beam Design Utilization"
):
    """
    Plot utilization ratios along beam length.
    
    Parameters
    ----------
    x_stations : array-like
        x-coordinates along beam
    utilizations : dict
        Dictionary of utilization arrays, e.g.:
        {'bending': array, 'shear': array, 'compression': array}
    support_locations : array-like, optional
        x-coordinates of supports
    bracing_locations : array-like, optional
        x-coordinates of lateral bracing
    figsize : tuple
        Figure size (width, height)
    title : str
        Plot title
    
    Examples
    --------
    >>> plot_beam_utilization(
    ...     x_stations=mesh.x_stations,
    ...     utilizations={'bending': bend_util, 'shear': shear_util},
    ...     support_locations=beam.support_locations,
    ...     bracing_locations=beam.bracing_locations
    ... )
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot utilization curves
    colors = {'bending': 'blue', 'shear': 'green', 'compression': 'red'}
    
    for check_name, util_array in utilizations.items():
        color = colors.get(check_name, 'gray')
        ax.plot(x_stations, util_array, label=check_name.capitalize(), 
                color=color, linewidth=2)
    
    # Add limit line
    ax.axhline(y=1.0, color='red', linestyle='--', linewidth=1, 
               label='Unity (100%)', alpha=0.7)
    
    # Add support markers
    if support_locations is not None:
        y_max = max([util.max() for util in utilizations.values()] + [1.0])
        for x_sup in support_locations:
            ax.axvline(x=x_sup, color='black', linestyle='-', linewidth=2, alpha=0.3)
            ax.plot(x_sup, 0, 'k^', markersize=12, label='Support' if x_sup == support_locations[0] else '')
    
    # Add bracing markers
    if bracing_locations is not None:
        for x_brace in bracing_locations:
            if support_locations is None or x_brace not in support_locations:
                ax.axvline(x=x_brace, color='orange', linestyle=':', linewidth=1, alpha=0.5)
                ax.plot(x_brace, 0, 'o', color='orange', markersize=6, 
                       label='Bracing' if x_brace == bracing_locations[0] else '')
    
    # Formatting
    ax.set_xlabel('Position along beam (m)', fontsize=12)
    ax.set_ylabel('Utilization Ratio', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    
    # Set y-limits
    y_max = max([util.max() for util in utilizations.values()] + [1.0]) * 1.1
    ax.set_ylim(0, y_max)
    
    plt.tight_layout()
    return fig, ax


def plot_demand_diagrams(
    x_stations: np.ndarray,
    demands: dict,
    support_locations: Optional[np.ndarray] = None,
    figsize: tuple = (12, 10),
    title: str = "Beam Demand Diagrams"
):
    """
    Plot moment, shear, and axial demand diagrams.
    
    Parameters
    ----------
    x_stations : array-like
        x-coordinates along beam
    demands : dict
        Dictionary of demand arrays, e.g.:
        {'M_f': moment_array, 'V_f': shear_array, 'P_f': axial_array}
    support_locations : array-like, optional
        x-coordinates of supports
    figsize : tuple
        Figure size (width, height)
    title : str
        Plot title
    
    Examples
    --------
    >>> plot_demand_diagrams(
    ...     x_stations=mesh.x_stations,
    ...     demands={'M_f': moments, 'V_f': shears, 'P_f': axial},
    ...     support_locations=beam.support_locations
    ... )
    """
    fig, axes = plt.subplots(3, 1, figsize=figsize, sharex=True)
    
    demand_config = [
        ('M_f', 'Bending Moment (kN·m)', axes[0], 'blue'),
        ('V_f', 'Shear Force (kN)', axes[1], 'green'),
        ('P_f', 'Axial Force (kN)', axes[2], 'red')
    ]
    
    for demand_key, ylabel, ax, color in demand_config:
        if demand_key in demands:
            demand_array = demands[demand_key]
            ax.plot(x_stations, demand_array, color=color, linewidth=2)
            ax.fill_between(x_stations, 0, demand_array, alpha=0.2, color=color)
            ax.set_ylabel(ylabel, fontsize=11)
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='black', linewidth=0.5)
            
            # Add support markers
            if support_locations is not None:
                for x_sup in support_locations:
                    ax.axvline(x=x_sup, color='black', linestyle='-', 
                              linewidth=1.5, alpha=0.3)
    
    axes[-1].set_xlabel('Position along beam (m)', fontsize=12)
    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    return fig, axes


def annotate_critical_sections(
    ax,
    x_critical: List[float],
    y_critical: List[float],
    labels: Optional[List[str]] = None
):
    """
    Annotate critical sections on a plot.
    
    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to annotate
    x_critical : list of float
        x-coordinates of critical sections
    y_critical : list of float
        y-coordinates of critical sections
    labels : list of str, optional
        Labels for each critical section
    """
    if labels is None:
        labels = [f"Critical {i+1}" for i in range(len(x_critical))]
    
    for x, y, label in zip(x_critical, y_critical, labels):
        ax.plot(x, y, 'ro', markersize=10)
        ax.annotate(
            label,
            xy=(x, y),
            xytext=(10, 10),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )
