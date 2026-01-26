"""
Applied load formulas for timber design (placeholders for design inputs).
"""

from eime import create_formula, Param, EngineeringFormula, formula


@formula
def applied_moment(M_f: float) -> EngineeringFormula:
    """
    Factored applied moment.
    
    Parameters
    ----------
    M_f : float
        Factored applied moment
        
    Returns
    -------
    EngineeringFormula
        Formula for applied moment (pass-through)
    """
    return create_formula(
        name="M_f",
        params={"M_f": Param("M_f", desc="factored applied moment")},
        logic=lambda M_f: M_f,
        latex_template=lambda M_f: f"{M_f}",
        source="",
        desc="Factored Applied Moment"
    )


@formula
def applied_shear(V_f: float) -> EngineeringFormula:
    """
    Factored applied shear.
    
    Parameters
    ----------
    V_f : float
        Factored applied shear
        
    Returns
    -------
    EngineeringFormula
        Formula for applied shear (pass-through)
    """
    return create_formula(
        name="V_f",
        params={"V_f": Param("V_f", desc="factored applied shear")},
        logic=lambda V_f: V_f,
        latex_template=lambda V_f: f"{V_f}",
        source="",
        desc="Factored Applied Shear"
    )


@formula
def applied_compression(P_f: float) -> EngineeringFormula:
    """
    Factored applied compression.
    
    Parameters
    ----------
    P_f : float
        Factored applied compression
        
    Returns
    -------
    EngineeringFormula
        Formula for applied compression (pass-through)
    """
    return create_formula(
        name="P_f",
        params={"P_f": Param("P_f", desc="factored applied compression")},
        logic=lambda P_f: P_f,
        latex_template=lambda P_f: f"{P_f}",
        source="",
        desc="Factored Applied Compression"
    )
