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

