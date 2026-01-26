"""
Glulam bending resistance formulas per CSA O86-2025.
"""

import numpy as np
from eime import create_formula, create_switch, Param, Check, STATUS, EngineeringFormula, EngineeringSwitch, formula


@formula
def long_duration_factor(P_L: float, P_S: float) -> EngineeringFormula:
    """
    Long duration load factor per CSA O86:24.
    
    Except as specified in Clause 5.3.2.3, when the specified long-term load, P_L, 
    is greater than the specified standard-term load, P_S, a load-duration factor 
    of 0.65 may be used, or K_D may be calculated using this formula.
    
    Parameters
    ----------
    P_L : float
        Specified long-term load
    P_S : float
        Specified standard-term load based on Snow (S) and Live (L) loads acting 
        alone or in combination = S, L, S + 0.5L, or 0.5S + L, determined using 
        importance factors equal to 1.0
        
    Returns
    -------
    EngineeringFormula
        Formula for long duration factor
        
    Notes
    -----
    LaTeX: $K_D = 1.0 - 0.50 \\log_{{10}}(P_L/P_S) \\ge 0.65$
    
    P_L and P_S must be non-zero.
    
    References
    ----------
    CSA O86:24 cl.5.3.2.2
    """
    return create_formula(
        name="K_D",
        params={
            "P_L": Param("P_L", desc="specified long-term load"),
            "P_S": Param("P_S", desc="specified standard-term load")
        },
        logic=lambda P_L, P_S: np.maximum(1.0 - 0.50 * np.log10(np.abs(P_L/P_S)), 0.65),
        latex_template=lambda P_L, P_S: f"1.0 - 0.50 \\log_{{10}}({P_L}/{P_S}) \\ge 0.65",
        source="CSA O86:24 cl.5.3.2.2",
        desc="Long Duration Factor"
    )


@formula
def modified_bending_strength(f_b: float, K_D: float, K_H: float, K_Sb: float, K_T: float) -> EngineeringFormula:
    """
    Modified strength in bending.
    
    Parameters
    ----------
    f_b : float
        Specified strength in bending
    K_D : float
        Load-duration factor
    K_H : float
        System factor
    K_Sb : float
        Service condition factor
    K_T : float
        Treatment factor
        
    Returns
    -------
    EngineeringFormula
        Formula for modified bending strength
        
    Notes
    -----
    LaTeX: $F_b = f_b \\cdot K_D \\cdot K_H \\cdot K_{{Sb}} \\cdot K_T$
    
    References
    ----------
    CSA O86:24 7.5.6.6.1
    """
    return create_formula(
        name="F_b",
        params={
            "f_b": Param("f_b", desc="specified bending strength"),
            "K_D": Param("K_D", desc="load-duration factor"),
            "K_H": Param("K_H", desc="system factor"),
            "K_Sb": Param("K_{{Sb}}", desc="service condition factor"),
            "K_T": Param("K_T", desc="treatment factor")
        },
        logic=lambda f_b, K_D, K_H, K_Sb, K_T: f_b * K_D * K_H * K_Sb * K_T,
        latex_template=lambda f_b, K_D, K_H, K_Sb, K_T: f"{f_b} \\cdot {K_D} \\cdot {K_H} \\cdot {K_Sb} \\cdot {K_T}",
        source="CSA O86:24 7.5.6.6.1",
        desc="Modified Bending Strength"
    )


@formula
def bending_size_factor(b: float, d: float, L: float) -> EngineeringFormula:
    """
    Size factor for bending for glued-laminated timber.
    
    **UNITS MUST BE MM**
    
    Parameters
    ----------
    b : float
        Width in mm
    d : float
        Depth in mm
    L : float
        Length in mm
        
    Returns
    -------
    EngineeringFormula
        Formula for bending size factor
        
    Notes
    -----
    LaTeX: $K_{{Zbg}} = \\left(\\frac{{130}}{{b}}\\right)^{{0.1}} \\left(\\frac{{610}}{{d}}\\right)^{{0.1}} \\left(\\frac{{9100}}{{L}}\\right)^{{0.1}}$
    
    Checks:
        - Size factor must be ≤ 1.3
    
    References
    ----------
    CSA O86:24 7.5.6.6.1
    """
    return create_formula(
        name="K_{Zbg}",
        params={
            "b": Param("b", desc="width"),
            "d": Param("d", desc="depth"),
            "L": Param("L", desc="length")
        },
        logic=lambda b, d, L: (130/b)**0.1 * (610/d)**0.1 * (9100/L)**0.1,
        latex_template=lambda b, d, L: f"\\left(\\frac{{130}}{{{b}}}\\right)^{{0.1}} \\left(\\frac{{610}}{{{d}}}\\right)^{{0.1}} \\left(\\frac{{9100}}{{{L}}}\\right)^{{0.1}}",
        source="CSA O86:24 7.5.6.6.1",
        checks=[
            Check.upperbound(1.3, STATUS.FAIL, 101, "Size factor must be ≤ 1.3", inclusive=True)
        ],
        desc="Bending Size Factor"
    )


@formula
def slenderness_ratio(L_u: float, d: float, b: float) -> EngineeringFormula:
    """
    Unbraced segment slenderness ratio.
    
    **SIMPLIFIED - NOT TO CODE**
    
    Parameters
    ----------
    L_u : float
        Unbraced segment length
    d : float
        Depth
    b : float
        Width
        
    Returns
    -------
    EngineeringFormula
        Formula for slenderness ratio
        
    Notes
    -----
    LaTeX: $\\lambda = \\sqrt{\\frac{{L_u \\cdot d}}{{b^2}}}$
    
    References
    ----------
    CSA O86:24 7.5.6.5.2
    """
    return create_formula(
        name="\\lambda",
        params={
            "L_u": Param("L_u", desc="unbraced segment length"),
            "d": Param("d", desc="depth"),
            "b": Param("b", desc="width")
        },
        logic=lambda L_u, d, b: np.sqrt(L_u * d / b**2),
        latex_template=lambda L_u, d, b: f"\\sqrt{{\\frac{{{L_u} \\cdot {d}}}{{{b}^2}}}}",
        source="CSA O86:24 7.5.6.5.2",
        desc="Slenderness Ratio"
    )


@formula
def slenderness_ratio_limit(E: float, K_SE: float, K_T: float, F_b: float) -> EngineeringFormula:
    """
    Slenderness ratio limit for elastic lateral-torsional buckling.
    
    **SIMPLIFIED - NOT TO CODE**
    
    Parameters
    ----------
    E : float
        Specified modulus of elasticity
    K_SE : float
        Service condition factor
    K_T : float
        Treatment factor
    F_b : float
        Modified bending strength
        
    Returns
    -------
    EngineeringFormula
        Formula for slenderness ratio limit
        
    Notes
    -----
    LaTeX: $\\lambda_e = \\sqrt{\\frac{{0.97 \\cdot E \\cdot K_{{SE}} \\cdot K_T}}{{F_b}}}$
    
    References
    ----------
    CSA O86:24 7.5.6.5.2 b)
    """
    return create_formula(
        name="\\lambda_e",
        params={
            "E": Param("E", desc="specified modulus of elasticity"),
            "K_SE": Param("K_{{SE}}", desc="service condition factor"),
            "K_T": Param("K_T", desc="treatment factor"),
            "F_b": Param("F_b", desc="modified bending strength")
        },
        logic=lambda E, K_SE, K_T, F_b: np.sqrt(0.97 * E * K_SE * K_T / F_b),
        latex_template=lambda E, K_SE, K_T, F_b: f"\\sqrt{{\\frac{{0.97 \\cdot {E} \\cdot {K_SE} \\cdot {K_T}}}{{{F_b}}}}}",
        source="CSA O86:24 7.5.6.5.2 b)",
        desc="Slenderness Ratio Limit"
    )


@formula
def lateral_stability_factor_a() -> EngineeringFormula:
    """
    Lateral stability factor for fully braced members (λ ≤ 10).
    
    Returns
    -------
    EngineeringFormula
        Formula for lateral stability factor (case a)
        
    Notes
    -----
    LaTeX: $K_L = 1.0$
    
    References
    ----------
    CSA O86:24 7.5.6.5.2 a)
    """
    return create_formula(
        name="K_L",
        params={},
        logic=lambda: 1.0,
        latex_template=lambda: "1.0",
        source="CSA O86:24 7.5.6.5.2 a)",
        desc="Lateral Stability Factor a)"
    )


@formula
def lateral_stability_factor_b(lambda_1: float, lambda_e: float) -> EngineeringFormula:
    """
    Lateral stability factor for intermediate slenderness (10 < λ ≤ λ_e).
    
    Parameters
    ----------
    lambda_1 : float
        Slenderness ratio
    lambda_e : float
        Slenderness ratio limit
        
    Returns
    -------
    EngineeringFormula
        Formula for lateral stability factor (case b)
        
    Notes
    -----
    LaTeX: $K_L = 1 - \\frac{{1}}{{3}}\\left(\\frac{{\\lambda}}{{\\lambda_e}}\\right)^4$
    
    References
    ----------
    CSA O86:24 7.5.6.5.2 b)
    """
    return create_formula(
        name="K_L",
        params={
            "lambda_1": Param("\\lambda", desc="slenderness ratio"),
            "lambda_e": Param("\\lambda_e", desc="slenderness ratio limit")
        },
        logic=lambda lambda_1, lambda_e: 1 - (1/3) * (lambda_1/lambda_e)**4,
        latex_template=lambda lambda_1, lambda_e: f"1 - \\frac{{1}}{{3}}\\left(\\frac{{{lambda_1}}}{{{lambda_e}}}\\right)^4",
        source="CSA O86:24 7.5.6.5.2 b)",
        desc="Lateral Stability Factor b)"
    )


def lateral_stability_factor(
    lambda1: float,
    lambda_e: float,
    KL_a: float,
    KL_b: float,
    KL_c: float,
    KL_d: float
) -> EngineeringSwitch:
    """
    Lateral stability factor for unbraced members (selects appropriate formula).
    
    Parameters
    ----------
    lambda1 : float
        Slenderness ratio
    lambda_e : float
        Slenderness ratio limit
    KL_a : float
        Lateral stability factor - case a) output
    KL_b : float
        Lateral stability factor - case b) output
    KL_c : float
        Lateral stability factor - case c) output
    KL_d : float
        Lateral stability factor - case d) output
        
    Returns
    -------
    EngineeringSwitch
        Switch formula for lateral stability factor
        
    Notes
    -----
    Selects the appropriate lateral stability factor based on slenderness ratio.
    
    Checks:
        - K_L must be ≤ 1.0
    
    References
    ----------
    CSA O86:24 7.5.6.5.2
    """
    return create_switch(
        name="K_L",
        params={
            "lambda1": Param("\\lambda", desc="slenderness ratio"),
            "lambda_e": Param("\\lambda_e", desc="slenderness ratio limit"),
            "KL_a": Param("K_L", desc="lateral stability factor output a)"),
            "KL_b": Param("K_L", desc="lateral stability factor output b)"),
            "KL_c": Param("K_L", desc="lateral stability factor output c)"),
            "KL_d": Param("K_L", desc="lateral stability factor output d)")
        },
        bounds=[10, lambda_e, 50],
        outputs=[KL_a, KL_b, KL_c, KL_d],
        source="CSA O86:24 7.5.6.5.2",
        checks=[
            Check.upperbound(1.01, STATUS.FAIL, 102, "K_L must be ≤ 1.0", inclusive=True)
        ],
        desc="Lateral Stability Factor for Unbraced Members"
    )


@formula
def moment_resistance_a(phi: float, F_b: float, S: float, K_x: float, K_Zbg: float) -> EngineeringFormula:
    """
    Factored bending moment resistance (fully braced, case a).
    
    Parameters
    ----------
    phi : float
        Resistance factor
    F_b : float
        Modified bending strength
    S : float
        Section modulus
    K_x : float
        Curvature factor
    K_Zbg : float
        Size factor
        
    Returns
    -------
    EngineeringFormula
        Formula for moment resistance (case a)
        
    Notes
    -----
    LaTeX: $M_{{r,a}} = \\phi \\cdot F_b \\cdot S \\cdot K_x \\cdot K_{{Zbg}}$
    
    References
    ----------
    CSA O86:24 7.5.6.6.1 a)
    """
    return create_formula(
        name="M_{r,a}",
        params={
            "phi": Param("\\phi", desc="resistance factor"),
            "F_b": Param("F_b", desc="modified bending strength"),
            "S": Param("S", desc="section modulus"),
            "K_x": Param("K_x", desc="curvature factor"),
            "K_Zbg": Param("K_{{Zbg}}", desc="size factor")
        },
        logic=lambda phi, F_b, S, K_x, K_Zbg: phi * F_b * S * K_x * K_Zbg,
        latex_template=lambda phi, F_b, S, K_x, K_Zbg: f"{phi} \\cdot {F_b} \\cdot {S} \\cdot {K_x} \\cdot {K_Zbg}",
        source="CSA O86:24 7.5.6.6.1 a)",
        desc="Moment Resistance a)"
    )


def moment_resistance_b1(phi: float, F_b: float, S: float, K_x: float, K_Zbg: float) -> EngineeringFormula:
    """
    Factored bending moment resistance (unbraced, case b, part i).
    
    Parameters
    ----------
    phi : float
        Resistance factor
    F_b : float
        Modified bending strength
    S : float
        Section modulus
    K_x : float
        Curvature factor
    K_Zbg : float
        Size factor
        
    Returns
    -------
    EngineeringFormula
        Formula for moment resistance (case b, part i)
        
    Notes
    -----
    LaTeX: $M_{{r1}} = \\phi \\cdot F_b \\cdot S \\cdot K_x \\cdot K_{{Zbg}}$
    
    References
    ----------
    CSA O86:24 7.5.6.6.1 b)
    """
    return create_formula(
        name="M_{r1}",
        params={
            "phi": Param("\\phi", desc="resistance factor"),
            "F_b": Param("F_b", desc="modified bending strength"),
            "S": Param("S", desc="section modulus"),
            "K_x": Param("K_x", desc="curvature factor"),
            "K_Zbg": Param("K_{{Zbg}}", desc="size factor")
        },
        logic=lambda phi, F_b, S, K_x, K_Zbg: phi * F_b * S * K_x * K_Zbg,
        latex_template=lambda phi, F_b, S, K_x, K_Zbg: f"{phi} \\cdot {F_b} \\cdot {S} \\cdot {K_x} \\cdot {K_Zbg}",
        source="CSA O86:24 7.5.6.6.1 b)",
        desc="Moment Resistance b) i)"
    )


def moment_resistance_b2(phi: float, F_b: float, S: float, K_x: float, K_L: float) -> EngineeringFormula:
    """
    Factored bending moment resistance (unbraced, case b, part ii).
    
    Parameters
    ----------
    phi : float
        Resistance factor
    F_b : float
        Modified bending strength
    S : float
        Section modulus
    K_x : float
        Curvature factor
    K_L : float
        Lateral-stability factor
        
    Returns
    -------
    EngineeringFormula
        Formula for moment resistance (case b, part ii)
        
    Notes
    -----
    LaTeX: $M_{{r2}} = \\phi \\cdot F_b \\cdot S \\cdot K_x \\cdot K_L$
    
    References
    ----------
    CSA O86:24 7.5.6.6.1 b)
    """
    return create_formula(
        name="M_{r2}",
        params={
            "phi": Param("\\phi", desc="resistance factor"),
            "F_b": Param("F_b", desc="modified bending strength"),
            "S": Param("S", desc="section modulus"),
            "K_x": Param("K_x", desc="curvature factor"),
            "K_L": Param("K_L", desc="lateral stability factor")
        },
        logic=lambda phi, F_b, S, K_x, K_L: phi * F_b * S * K_x * K_L,
        latex_template=lambda phi, F_b, S, K_x, K_L: f"{phi} \\cdot {F_b} \\cdot {S} \\cdot {K_x} \\cdot {K_L}",
        source="CSA O86:24 7.5.6.6.1 b)",
        desc="Moment Resistance b) ii)"
    )


@formula
def moment_resistance_b(M_r1: float, M_r2: float) -> EngineeringSwitch:
    """
    Factored bending moment resistance (selects minimum of case b formulas).
    
    Parameters
    ----------
    M_r1 : float
        Based on K_Zbg
    M_r2 : float
        Based on K_L
        
    Returns
    -------
    EngineeringSwitch
        Switch formula for moment resistance (case b)
        
    Notes
    -----
    Selects the minimum of M_r1 and M_r2.
    
    References
    ----------
    CSA O86:24 7.5.6.6.1 b)
    """
    return create_switch(
        name="M_{r,b}",
        params={
            "M_r1": Param("M_{{r1}}", desc="resistance based on K_Zbg"),
            "M_r2": Param("M_{{r2}}", desc="resistance based on K_L")
        },
        bounds=[M_r2],
        outputs=[M_r1, M_r2],
        source="CSA O86:24 7.5.6.6.1 b)",
        desc="Moment Resistance b)"
    )


@formula
def moment_resistance(K_L: float, M_rA: float, M_rB: float, M_f: float = None) -> EngineeringSwitch:
    """
    Factored bending moment resistance (selects based on bracing condition).
    
    Parameters
    ----------
    K_L : float
        Lateral stability factor
    M_rA : float
        Resistance for case a (fully braced)
    M_rB : float
        Resistance for case b (unbraced)
    M_f : float, optional
        Factored applied moment (for checks)
        
    Returns
    -------
    EngineeringSwitch
        Switch formula for moment resistance
        
    Notes
    -----
    Selects M_rA if K_L = 1.0 (fully braced), otherwise M_rB.
    
    Checks:
        - Factored force must not exceed resistance
    
    References
    ----------
    CSA O86:24 7.5.6.6.1
    """
    return create_switch(
        name="M_r",
        params={
            "K_L": Param("K_L", desc="lateral stability factor"),
            "M_rA": Param("M_r", desc="resistance A (braced)"),
            "M_rB": Param("M_r", desc="resistance B (unbraced)")
        },
        bounds=[1.0],
        outputs=[M_rB, M_rA],
        source="CSA O86:24 7.5.6.6.1",
        checks=[
            Check.lowerbound(M_f, STATUS.FAIL, 103, "Factored force exceeds resistance.")
        ] if M_f is not None else [],
        desc="Moment Resistance"
    )
