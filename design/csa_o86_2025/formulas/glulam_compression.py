"""
Glulam compression resistance formulas per CSA O86-2025.
"""

import numpy as np
from eime import create_formula, Param, Check, STATUS, EngineeringFormula, formula


@formula
def modified_compression_strength(f_c: float, K_D: float, K_H: float, K_Sc: float, K_T: float) -> EngineeringFormula:
    """
    Modified strength in compression parallel to grain.
    
    Parameters
    ----------
    f_c : float
        Specified strength in compression parallel to grain
    K_D : float
        Load-duration factor
    K_H : float
        System factor
    K_Sc : float
        Service condition factor
    K_T : float
        Treatment factor
        
    Returns
    -------
    EngineeringFormula
        Formula for modified compression strength
        
    Notes
    -----
    LaTeX: $F_c = f_c \\cdot K_D \\cdot K_H \\cdot K_{{Sc}} \\cdot K_T$
    
    References
    ----------
    CSA O86:24 7.5.8.5
    """
    return create_formula(
        name="F_c",
        params={
            "f_c": Param("f_c", desc="specified compression strength"),
            "K_D": Param("K_D", desc="load-duration factor"),
            "K_H": Param("K_H", desc="system factor"),
            "K_Sc": Param("K_{{Sc}}", desc="service condition factor"),
            "K_T": Param("K_T", desc="treatment factor")
        },
        logic=lambda f_c, K_D, K_H, K_Sc, K_T: f_c * K_D * K_H * K_Sc * K_T,
        latex_template=lambda f_c, K_D, K_H, K_Sc, K_T: f"{f_c} \\cdot {K_D} \\cdot {K_H} \\cdot {K_Sc} \\cdot {K_T}",
        source="CSA O86:24 7.5.8.5",
        desc="Modified Compression Strength"
    )


@formula
def compression_size_factor(Z: float) -> EngineeringFormula:
    """
    Size factor for compression members, K_Zcg ≤ 1.0.
    
    Parameters
    ----------
    Z : float
        Member volume, m³
        
    Returns
    -------
    EngineeringFormula
        Formula for compression size factor
        
    Notes
    -----
    LaTeX: $K_{{Zcg}} = 0.68 \\cdot Z^{{-0.13}}$
    
    Checks:
        - Compression size factor must be ≤ 1.0
    
    References
    ----------
    CSA O86:24 7.5.8.5
    """
    return create_formula(
        name="K_{Zcg}",
        params={
            "Z": Param("Z", desc="member volume, m³")
        },
        logic=lambda Z: 0.68 * Z**(-0.13),
        latex_template=lambda Z: f"0.68 \\cdot {Z}^{{-0.13}}",
        source="CSA O86:24 7.5.8.5",
        checks=[
            Check.upperbound(1.0, STATUS.FAIL, 301, "Compression size factor must be ≤ 1.0", inclusive=True)
        ],
        desc="Compression Size Factor"
    )


@formula
def compression_slenderness_ratio(L_e: float, w: float) -> EngineeringFormula:
    """
    Slenderness ratio, C_C. 
    
    w is either depth or width depending on the effective length being considered.
    
    Parameters
    ----------
    L_e : float
        Effective length associated with width
    w : float
        Width (or depth)
        
    Returns
    -------
    EngineeringFormula
        Formula for compression slenderness ratio
        
    Notes
    -----
    LaTeX: $C_C = \\frac{{L_e}}{{w}}$
    
    References
    ----------
    CSA O86:24 7.5.8.2
    """
    return create_formula(
        name="C_C",
        params={
            "L_e": Param("L_e", desc="effective length associated with width"),
            "w": Param("w", desc="width")
        },
        logic=lambda L_e, w: L_e / w,
        latex_template=lambda L_e, w: f"\\frac{{{L_e}}}{{{w}}}",
        source="CSA O86:24 7.5.8.2",
        desc="Compression Slenderness Ratio"
    )


@formula
def slenderness_factor(F_c: float, K_Zcg: float, C_C: float, E_05: float, K_SE: float, K_T: float) -> EngineeringFormula:
    """
    Slenderness factor, K_c.
    
    Parameters
    ----------
    F_c : float
        Factored strength in compression parallel to grain
    K_Zcg : float
        Compression size factor
    C_C : float
        Compression slenderness ratio
    E_05 : float
        Fifth percentile of specified modulus of elasticity, MPa
    K_SE : float
        Service condition factor
    K_T : float
        Treatment factor
        
    Returns
    -------
    EngineeringFormula
        Formula for slenderness factor
        
    Notes
    -----
    LaTeX: $K_c = \\left[ 1.0 + \\frac{{F_c \\cdot K_{{Zcg}} \\cdot C_C^3}}{{35 \\cdot E_{{05}} \\cdot K_{{SE}} \\cdot K_T}} \\right]^{{-1}}$
    
    References
    ----------
    CSA O86:24 7.5.8.6
    """
    return create_formula(
        name="K_c",
        params={
            "F_c": Param("F_c", desc="factored strength in compression"),
            "K_Zcg": Param("K_{{Zcg}}", desc="compression size factor"),
            "C_C": Param("C_C", desc="compression slenderness ratio"),
            "E_05": Param("E_{{05}}", desc="fifth percentile modulus of elasticity"),
            "K_SE": Param("K_{{SE}}", desc="service condition factor"),
            "K_T": Param("K_T", desc="treatment factor")
        },
        logic=lambda F_c, K_Zcg, C_C, E_05, K_SE, K_T: 1 / (1 + F_c * K_Zcg * C_C**3 / (35 * E_05 * K_SE * K_T)),
        latex_template=lambda F_c, K_Zcg, C_C, E_05, K_SE, K_T: f"\\left[ 1.0 + \\frac{{{F_c} \\cdot {K_Zcg} \\cdot {C_C}^3}}{{35 \\cdot {E_05} \\cdot {K_SE} \\cdot {K_T}}} \\right]^{{-1}}",
        source="CSA O86:24 7.5.8.6",
        desc="Slenderness Factor"
    )


@formula
def compression_resistance(phi: float, F_c: float, A: float, K_Zcg: float, K_C: float, P_f: float = None) -> EngineeringFormula:
    """
    Factored compressive resistance parallel to grain, P_r.
    
    Parameters
    ----------
    phi : float
        Compression resistance modification factor
    F_c : float
        Factored strength in compression parallel to grain, MPa
    A : float
        Cross-sectional area, mm²
    K_Zcg : float
        Compression size factor
    K_C : float
        Compression slenderness factor
    P_f : float, optional
        Factored compressive force (for checks)
        
    Returns
    -------
    EngineeringFormula
        Formula for compression resistance
        
    Notes
    -----
    LaTeX: $P_r = \\phi \\cdot F_c \\cdot A \\cdot K_{{Zcg}} \\cdot K_C$
    
    Checks:
        - Factored force must not exceed resistance
    
    References
    ----------
    CSA O86:24 7.5.8.5
    """
    return create_formula(
        name="P_r",
        params={
            "phi": Param("\\phi", desc="compression resistance modification factor"),
            "F_c": Param("F_c", desc="factored strength in compression"),
            "A": Param("A", desc="cross-sectional area, mm²"),
            "K_Zcg": Param("K_{{Zcg}}", desc="compression size factor"),
            "K_C": Param("K_C", desc="compression slenderness factor")
        },
        logic=lambda phi, F_c, A, K_Zcg, K_C: phi * F_c * A * K_Zcg * K_C,
        latex_template=lambda phi, F_c, A, K_Zcg, K_C: f"{phi} \\cdot {F_c} \\cdot {A} \\cdot {K_Zcg} \\cdot {K_C}",
        source="CSA O86:24 7.5.8.5",
        checks=[
            Check.lowerbound(P_f, STATUS.FAIL, 302, "Factored force exceeds resistance.")
        ] if P_f is not None else [],
        desc="Compression Resistance"
    )
