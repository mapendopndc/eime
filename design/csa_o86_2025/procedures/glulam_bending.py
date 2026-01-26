"""
Glulam Bending Procedure

Organizes the calculation sequence for determining glulam bending resistance
per CSA O86:24 Section 7.5.6.
"""

from eime import EngineeringProcedure


def glulam_bending_procedure(
    KD=None,
    Fb=None,
    KZbg=None,
    S=None,
    lambda1=None,
    lambda_e=None,
    KL_a=None,
    KL_b=None,
    KL=None,
    MrA=None,
    Mr1=None,
    Mr2=None,
    MrB=None,
    Mr=None
) -> EngineeringProcedure:
    """
    Glulam beam bending resistance procedure.
    
    Organizes the calculation sequence for determining glulam bending resistance
    per CSA O86:24 Section 7.5.6.
    
    Parameters
    ----------
    KD : EngineeringFormula
        Long duration factor calculation
    Fb : EngineeringFormula
        Modified bending strength calculation
    KZbg : EngineeringFormula
        Bending size factor calculation
    S : EngineeringFormula
        Section modulus calculation
    lambda1 : EngineeringFormula
        Slenderness ratio calculation
    lambda_e : EngineeringFormula
        Slenderness ratio limit calculation
    KL_a : EngineeringFormula
        Lateral stability factor (case a)
    KL_b : EngineeringFormula
        Lateral stability factor (case b)
    KL : EngineeringSwitch
        Lateral stability factor (selected)
    MrA : EngineeringFormula
        Moment resistance (case a - fully braced)
    Mr1 : EngineeringFormula
        Moment resistance (case b, part i)
    Mr2 : EngineeringFormula
        Moment resistance (case b, part ii)
    MrB : EngineeringSwitch
        Moment resistance (case b - selected)
    Mr : EngineeringSwitch
        Final moment resistance
        
    Returns
    -------
    EngineeringProcedure
        Organized bending resistance procedure
        
    References
    ----------
    CSA O86:24 Section 7.5.6
    """
    procedure = EngineeringProcedure("Glulam Beam Bending Procedure")
    
    if KD is not None:
        procedure.add_computation(KD)
    if Fb is not None:
        procedure.add_computation(Fb)
    if lambda1 is not None:
        procedure.add_computation(lambda1)
    if lambda_e is not None:
        procedure.add_computation(lambda_e)
    if KL is not None:
        procedure.add_computation(KL, show_util=False)
    if KZbg is not None:
        procedure.add_computation(KZbg, show_util=False)
    if S is not None:
        procedure.add_computation(S)
    if Mr is not None:
        procedure.add_computation(Mr)
    
    return procedure


__all__ = ["glulam_bending_procedure"]
