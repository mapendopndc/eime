"""
Glulam Shear Procedure

Organizes the calculation sequence for determining glulam shear resistance
per CSA O86:24 Section 7.5.7.
"""

from eime import EngineeringProcedure


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
        Load duration factor calculation
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
        procedure.add_computation(KD, show_util=False)
    if CV is not None:
        procedure.add_computation(CV)
    if Fv is not None:
        procedure.add_computation(Fv)
    if Wr is not None:
        procedure.add_computation(Wr)
    if Vr is not None:
        procedure.add_computation(Vr)
    
    return procedure


__all__ = ["glulam_shear_procedure"]
