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
    
SpecifiedStrengthTable:dict = _getSpecifiedStrengths()
ServiceConditionFactorTable:dict = _getServiceConditionFactor()
EffectiveLengthFactorTable:dict = _getEffectiveLengthFactor()