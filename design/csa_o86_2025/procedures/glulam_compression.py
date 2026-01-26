"""
Glulam Compression Procedure

Organizes the calculation sequence for determining glulam compression resistance
per CSA O86:24 Section 7.5.8.
"""

from eime import EngineeringProcedure


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


__all__ = ["glulam_compression_procedure"]
