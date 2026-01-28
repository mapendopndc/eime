"""
CSA O86-2025 design tables and reference data.

This module provides access to design tables from CSA O86-2025:
- Table 7.2: Specified strengths and moduli of elasticity for glue-laminated timber
- Table 7.3: Service-condition factors
- Table A.4: Effective length factors
"""

import json
import os

_current_dir = os.path.dirname(__file__)


# Specified strengths and moduli of elasticity for glue-laminated timber, MPa
def _getSpecifiedStrengths():
    with open(os.path.join(_current_dir, "CSA O86-24_T7-2.json")) as f:
        return json.load(f)
    
# Service-condition factor
def _getServiceConditionFactor():
    with open(os.path.join(_current_dir, "CSA O86-24_T7-3.json")) as f:
        return json.load(f)
    
# Effective Length Factor
def _getEffectiveLengthFactor():
    with open(os.path.join(_current_dir, "CSA O86-24_TA-4.json")) as f:
        return json.load(f)
    
SpecifiedStrengthTable: dict = _getSpecifiedStrengths()
ServiceConditionFactorTable: dict = _getServiceConditionFactor()
EffectiveLengthFactorTable: dict = _getEffectiveLengthFactor()


# Load K_D table
def _getKdFactors():
    with open(os.path.join(_current_dir, "kd_factors.json")) as f:
        return json.load(f)

KdFactorTable: dict = _getKdFactors()


def kd_from_load_type(load_combo_type: str) -> float:
    """
    Get K_D value from table based on load combination type.
    
    Parameters
    ----------
    load_combo_type : str
        One of: 'dead_only', 'includes_live', 'includes_wind_or_seismic'
    
    Returns
    -------
    float
        K_D factor from table
        
    Examples
    --------
    >>> kd_from_load_type('dead_only')
    0.65
    >>> kd_from_load_type('includes_live')
    1.0
    >>> kd_from_load_type('includes_wind_or_seismic')
    1.15
    """
    return KdFactorTable['kd_by_load_type'][load_combo_type]

