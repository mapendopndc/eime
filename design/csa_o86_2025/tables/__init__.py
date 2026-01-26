"""
CSA O86-2025 design tables and reference data.

This module provides access to design tables from CSA O86-2025:
- Table 7.2: Specified strengths and moduli of elasticity for glue-laminated timber
- Table 7.3: Service-condition factors
- Table A.4: Effective length factors
"""

import os
from eime import DesignTable

# Get the directory containing this file
_current_dir = os.path.dirname(__file__)


def get_specified_strengths() -> DesignTable:
    """
    Load CSA O86-24 Table 7.2: Specified strengths and moduli of elasticity 
    for glue-laminated timber, MPa.
    
    Returns
    -------
    DesignTable
        Table containing specified strengths organized by species and grade
        
    Notes
    -----
    Table includes:
    - f_b_pos: Specified bending strength (tension face stressed in bending)
    - f_v: Specified shear strength
    - f_c: Specified compression strength parallel to grain
    - E: Specified modulus of elasticity
    """
    table_path = os.path.join(_current_dir, "CSA O86-24_T7-2.json")
    return DesignTable.from_file(table_path)


def get_service_condition_factors() -> DesignTable:
    """
    Load CSA O86-24 Table 7.3: Service-condition factors.
    
    Returns
    -------
    DesignTable
        Table containing service condition factors organized by service condition
        
    Notes
    -----
    Table includes:
    - K_Sb: Service condition factor for bending
    - K_Sv: Service condition factor for shear
    - K_Sc: Service condition factor for compression
    - K_SE: Service condition factor for modulus of elasticity
    """
    table_path = os.path.join(_current_dir, "CSA O86-24_T7-3.json")
    return DesignTable.from_file(table_path)


def get_effective_length_factors() -> DesignTable:
    """
    Load CSA O86-24 Table A.4: Effective length factors.
    
    Returns
    -------
    DesignTable
        Table containing effective length factors organized by end condition
        
    Notes
    -----
    Provides K_e factors for different member end conditions:
    - Fixed-Fixed
    - Fixed-Pinned
    - Pinned-Pinned
    - Fixed-Free
    """
    table_path = os.path.join(_current_dir, "CSA O86-24_TA-4.json")
    return DesignTable.from_file(table_path)


# Cached table instances
_specified_strengths_table = None
_service_condition_table = None
_effective_length_table = None


def specified_strengths() -> DesignTable:
    """Get cached specified strengths table."""
    global _specified_strengths_table
    if _specified_strengths_table is None:
        _specified_strengths_table = get_specified_strengths()
    return _specified_strengths_table


def service_condition_factors() -> DesignTable:
    """Get cached service condition factors table."""
    global _service_condition_table
    if _service_condition_table is None:
        _service_condition_table = get_service_condition_factors()
    return _service_condition_table


def effective_length_factors() -> DesignTable:
    """Get cached effective length factors table."""
    global _effective_length_table
    if _effective_length_table is None:
        _effective_length_table = get_effective_length_factors()
    return _effective_length_table


__all__ = [
    "get_specified_strengths",
    "get_service_condition_factors",
    "get_effective_length_factors",
    "specified_strengths",
    "service_condition_factors",
    "effective_length_factors",
]
