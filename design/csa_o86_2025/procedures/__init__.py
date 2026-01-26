"""
CSA O86-2025 Timber Design Procedures

Engineering procedures that organize timber design formulas into common workflows.
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


def glulam_shear_procedure(
    KD=None,
    CV=None,
    Fv=None,
    Wr=None,
    Vr=None
) -> EngineeringProcedure:
    """
    Glulam beam shear resistance procedure.
    
    Organizes the calculation sequence for determining glulam shear resistance
    per CSA O86:24 Section 7.5.7.
    
    Parameters
    ----------
    KD : EngineeringFormula
        Long duration factor calculation
    CV : EngineeringFormula
        Shear load coefficient calculation
    Fv : EngineeringFormula
        Modified shear strength calculation
    Wr : EngineeringFormula
        Total shear resistance calculation
    Vr : EngineeringFormula
        Shear resistance calculation
        
    Returns
    -------
    EngineeringProcedure
        Organized shear resistance procedure
        
    References
    ----------
    CSA O86:24 Section 7.5.7
    """
    procedure = EngineeringProcedure("Glulam Beam Shear Procedure")
    
    if KD is not None:
        procedure.add_computation(KD)
    if CV is not None:
        procedure.add_computation(CV)
    if Fv is not None:
        procedure.add_computation(Fv)
    if Wr is not None:
        procedure.add_computation(Wr)
    if Vr is not None:
        procedure.add_computation(Vr)
    
    return procedure


def glulam_compression_procedure(
    KD=None,
    Fc=None,
    KZcg=None,
    CC=None,
    KC=None,
    Pr=None
) -> EngineeringProcedure:
    """
    Glulam compression resistance procedure.
    
    Organizes the calculation sequence for determining glulam compression resistance
    per CSA O86:24 Section 7.5.8.
    
    Parameters
    ----------
    KD : EngineeringFormula
        Long duration factor calculation
    Fc : EngineeringFormula
        Modified compression strength calculation
    KZcg : EngineeringFormula
        Compression size factor calculation
    CC : EngineeringFormula
        Compression slenderness ratio calculation
    KC : EngineeringFormula
        Slenderness factor calculation
    Pr : EngineeringFormula
        Compression resistance calculation
        
    Returns
    -------
    EngineeringProcedure
        Organized compression resistance procedure
        
    References
    ----------
    CSA O86:24 Section 7.5.8
    """
    procedure = EngineeringProcedure("Glulam Compression Procedure")
    
    if KD is not None:
        procedure.add_computation(KD)
    if Fc is not None:
        procedure.add_computation(Fc)
    if KZcg is not None:
        procedure.add_computation(KZcg, show_util=False)
    if CC is not None:
        procedure.add_computation(CC)
    if KC is not None:
        procedure.add_computation(KC)
    if Pr is not None:
        procedure.add_computation(Pr)
    
    return procedure


__all__ = [
    "glulam_bending_procedure",
    "glulam_shear_procedure",
    "glulam_compression_procedure",
]
