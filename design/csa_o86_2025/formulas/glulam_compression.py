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
            "f_c": Param("f_c", unit="MPa", desc="specified compression strength"),
            "K_D": Param("K_D", unit="dimensionless", desc="load-duration factor"),
            "K_H": Param("K_H", unit="dimensionless", desc="system factor"),
            "K_Sc": Param("K_{Sc}", unit="dimensionless", desc="service condition factor"),
            "K_T": Param("K_T", unit="dimensionless", desc="treatment factor")
        },
        logic=lambda f_c, K_D, K_H, K_Sc, K_T: f_c * K_D * K_H * K_Sc * K_T,
        result_unit='MPa',  # Result is in MPa
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
            "Z": Param("Z", unit="m^3", desc="member volume, m³")
        },
        logic=lambda Z: 0.68 * Z**(-0.13),
        result_unit='dimensionless',  # EIME extracts magnitudes, wraps result
        latex_template=lambda Z: f"0.68 \\cdot \\left({Z}\\right)^{{-0.13}}",
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
            "L_e": Param("L_e", unit="mm", desc="effective length associated with width"),
            "w": Param("w", unit="mm", desc="width")
        },
        logic=lambda L_e, w: L_e / w,
        result_unit='dimensionless',  # EIME extracts magnitudes, wraps result
        latex_template=lambda L_e, w: f"\\frac{{{L_e}}}{{{w}}}",
        source="CSA O86:24 7.5.8.2",
        desc="Compression Slenderness Ratio"
    )


@formula
def compression_slenderness_ratio_strong_axis(L_e_strong: float, d: float) -> EngineeringFormula:
    """
    Slenderness ratio for strong axis buckling, C_C_strong.
    
    For strong axis buckling, the strong dimension d controls (radius of gyration proportional to d).
    
    Parameters
    ----------
    L_e_strong : float
        Effective length for strong axis buckling
    d : float
        Depth (strong dimension)
        
    Returns
    -------
    EngineeringFormula
        Formula for compression slenderness ratio about strong axis
        
    Notes
    -----
    LaTeX: $C_{{C,strong}} = \\frac{{L_{{e,strong}}}}{{d}}$
    
    References
    ----------
    CSA O86:24 7.5.8.2
    """
    return create_formula(
        name="C_{C,strong}",
        params={
            "L_e_strong": Param("L_{e,strong}", unit="mm", desc="effective length for strong axis buckling"),
            "d": Param("d", unit="mm", desc="depth (strong dimension)")
        },
        logic=lambda L_e_strong, d: L_e_strong / d,
        result_unit='dimensionless',
        latex_template=lambda L_e_strong, d: f"\\frac{{{L_e_strong}}}{{{d}}}",
        source="CSA O86:24 7.5.8.2",
        desc="Compression Slenderness Ratio (Strong Axis)"
    )


@formula
def compression_slenderness_ratio_weak_axis(L_e_weak: float, b: float) -> EngineeringFormula:
    """
    Slenderness ratio for weak axis buckling, C_C_weak.
    
    For weak axis buckling, the weak dimension b controls (radius of gyration proportional to b).
    
    Parameters
    ----------
    L_e_weak : float
        Effective length for weak axis buckling
    b : float
        Width (weak dimension)
        
    Returns
    -------
    EngineeringFormula
        Formula for compression slenderness ratio about weak axis
        
    Notes
    -----
    LaTeX: $C_{{C,weak}} = \\frac{{L_{{e,weak}}}}{{b}}$
    
    References
    ----------
    CSA O86:24 7.5.8.2
    """
    return create_formula(
        name="C_{C,weak}",
        params={
            "L_e_weak": Param("L_{e,weak}", unit="mm", desc="effective length for weak axis buckling"),
            "b": Param("b", unit="mm", desc="width (weak dimension)")
        },
        logic=lambda L_e_weak, b: L_e_weak / b,
        result_unit='dimensionless',
        latex_template=lambda L_e_weak, b: f"\\frac{{{L_e_weak}}}{{{b}}}",
        source="CSA O86:24 7.5.8.2",
        desc="Compression Slenderness Ratio (Weak Axis)"
    )


@formula
def compression_slenderness_ratio_max(C_C_strong: float, C_C_weak: float) -> EngineeringFormula:
    """
    Maximum slenderness ratio from both directions, C_C.
    
    The slenderness factor K_c shall be based on the maximum slenderness ratio
    considering both axes of buckling.
    
    Parameters
    ----------
    C_C_strong : float
        Slenderness ratio for strong axis buckling
    C_C_weak : float
        Slenderness ratio for weak axis buckling
        
    Returns
    -------
    EngineeringFormula
        Formula for maximum compression slenderness ratio
        
    Notes
    -----
    LaTeX: $C_C = \\max(C_{{C,strong}}, C_{{C,weak}})$
    
    References
    ----------
    CSA O86:24 7.5.8.2
    """
    return create_formula(
        name="C_C",
        params={
            "C_C_strong": Param("C_{C,strong}", unit="dimensionless", desc="slenderness ratio for strong axis"),
            "C_C_weak": Param("C_{C,weak}", unit="dimensionless", desc="slenderness ratio for weak axis")
        },
        logic=lambda C_C_strong, C_C_weak: np.maximum(C_C_strong, C_C_weak),
        result_unit='dimensionless',
        latex_template=lambda C_C_strong, C_C_weak: f"\\max({C_C_strong}, {C_C_weak})",
        source="CSA O86:24 7.5.8.2",
        desc="Maximum Compression Slenderness Ratio"
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
            "F_c": Param("F_c", unit="MPa", desc="factored strength in compression"),
            "K_Zcg": Param("K_{Zcg}", unit="dimensionless", desc="compression size factor"),
            "C_C": Param("C_C", unit="dimensionless", desc="compression slenderness ratio"),
            "E_05": Param("E_{05}", unit="MPa", desc="fifth percentile modulus of elasticity"),
            "K_SE": Param("K_{SE}", unit="dimensionless", desc="service condition factor"),
            "K_T": Param("K_T", unit="dimensionless", desc="treatment factor")
        },
        logic=lambda F_c, K_Zcg, C_C, E_05, K_SE, K_T: 1 / (1 + F_c * K_Zcg * C_C**3 / (35 * E_05 * K_SE * K_T)),
        result_unit='dimensionless',  # EIME extracts magnitudes, wraps result
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
            "phi": Param("\\phi", unit="dimensionless", desc="compression resistance modification factor"),
            "F_c": Param("F_c", unit="MPa", desc="factored strength in compression"),
            "A": Param("A", unit="mm^2", desc="cross-sectional area, mm²"),
            "K_Zcg": Param("K_{Zcg}", unit="dimensionless", desc="compression size factor"),
            "K_C": Param("K_C", unit="dimensionless", desc="compression slenderness factor"),
            "P_f": Param("P_f", unit="N", desc="factored compressive force")
        },
        logic=lambda phi, F_c, A, K_Zcg, K_C, P_f=None: phi * F_c * A * K_Zcg * K_C,
        result_unit='N',  # MPa * mm^2 = N
        latex_template=lambda phi, F_c, A, K_Zcg, K_C, P_f=None: f"{phi} \\cdot {F_c} \\cdot {A} \\cdot {K_Zcg} \\cdot {K_C}",
        source="CSA O86:24 7.5.8.5",
        checks=[
            Check.lowerbound(P_f, STATUS.FAIL, 302, "Factored force exceeds resistance.")
        ] if P_f is not None else [],
        desc="Compression Resistance"
    )
