"""
Section property calculations for timber members.
"""

import numpy as np
from eime import create_formula, Param, EngineeringFormula, formula


@formula
def moment_of_inertia(b: float, d: float) -> EngineeringFormula:
    """
    Computes the moment of inertia of a rectangular shape.
    
    Parameters
    ----------
    b : float
        Width of the section
    d : float
        Depth of the section
        
    Returns
    -------
    EngineeringFormula
        Formula for moment of inertia
        
    Notes
    -----
    LaTeX: $I = \\frac{b \\cdot d^3}{12}$
    """
    return create_formula(
        name="I",
        params={
            "b": Param("b", desc="width"),
            "d": Param("d", desc="depth")
        },
        logic=lambda b, d: b * d**3 / 12,
        latex_template=lambda b, d: f"\\frac{{{b} \\cdot {d}^{{3}}}}{{12}}",
        source="",
        desc="Moment of Inertia"
    )


@formula
def section_modulus(b: float, d: float) -> EngineeringFormula:
    """
    Computes the section modulus of a rectangular shape.
    
    Parameters
    ----------
    b : float
        Width of the section
    d : float
        Depth of the section
        
    Returns
    -------
    EngineeringFormula
        Formula for section modulus
        
    Notes
    -----
    LaTeX: $S = \\frac{b \\cdot d^2}{6}$
    """
    return create_formula(
        name="S",
        params={
            "b": Param("b", desc="width"),
            "d": Param("d", desc="depth")
        },
        logic=lambda b, d: b * d**2 / 6,
        latex_template=lambda b, d: f"\\frac{{{b} \\cdot {d}^{{2}}}}{{6}}",
        source="",
        desc="Section Modulus"
    )


@formula
def stiffness_modulus_of_elasticity(E: float, K_SE: float, K_T: float) -> EngineeringFormula:
    """
    Modulus of elasticity for stiffness calculations.
    
    Parameters
    ----------
    E : float
        Specified modulus of elasticity
    K_SE : float
        Service-condition factor
    K_T : float
        Treatment factor
        
    Returns
    -------
    EngineeringFormula
        Formula for stiffness modulus of elasticity
        
    Notes
    -----
    LaTeX: $E_S = E \\cdot K_{{SE}} \\cdot K_T$
    
    References
    ----------
    CSA O86:24 cl.5.4.1
    """
    return create_formula(
        name="E_S",
        params={
            "E": Param("E", desc="specified modulus of elasticity"),
            "K_SE": Param("K_{{SE}}", desc="service-condition factor"),
            "K_T": Param("K_T", desc="treatment factor")
        },
        logic=lambda E, K_SE, K_T: E * K_SE * K_T,
        latex_template=lambda E, K_SE, K_T: f"{E} \\cdot {K_SE} \\cdot {K_T}",
        source="CSA O86:24 cl.5.4.1",
        desc="Stiffness Modulus of Elasticity"
    )
