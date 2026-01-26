"""
Glulam shear resistance formulas per CSA O86-2025.
"""

import numpy as np
from eime import create_formula, Param, Check, STATUS, EngineeringFormula, formula


@formula
def g_factor(l_a: float, V_A: float, V_B: float, V_C: float) -> EngineeringFormula:
    """
    G factor used to compute the shear-load coefficient, C_V.
    
    Parameters
    ----------
    l_a : float
        Segment length
    V_A : float
        Absolute value of factored shear force at beginning of segment
    V_B : float
        Absolute value of factored shear force at end of segment
    V_C : float
        Absolute value of factored shear force at centre of segment
        
    Returns
    -------
    EngineeringFormula
        Formula for G factor
        
    Notes
    -----
    LaTeX: $G = l_a \\left[ V_A^5 + V_B^5 + 4 \\cdot V_C^5 \\right]$
    
    References
    ----------
    CSA O86:24 7.5.7.6 c)
    """
    return create_formula(
        name="G",
        params={
            "l_a": Param("l_a", desc="segment length"),
            "V_A": Param("V_A", desc="shear force at beginning of segment"),
            "V_B": Param("V_B", desc="shear force at end of segment"),
            "V_C": Param("V_C", desc="shear force at centre of segment")
        },
        logic=lambda l_a, V_A, V_B, V_C: np.abs(l_a * (V_A**5 + V_B**5 + (4*V_C)**5)),
        latex_template=lambda l_a, V_A, V_B, V_C: f"{l_a} \\left[ {V_A}^5 + {V_B}^5 + 4 \\cdot {V_C}^5 \\right]",
        source="CSA O86:24 7.5.7.6 c)",
        desc="Shear Factor G"
    )


@formula
def shear_load_coefficient(W_f: float, L: float, Sum_G: float) -> EngineeringFormula:
    """
    Shear-load coefficient, C_V.
    
    Parameters
    ----------
    W_f : float
        The total of all factored loads applied to the beam
    L : float
        Length of beam
    Sum_G : float
        Sum of G factors
        
    Returns
    -------
    EngineeringFormula
        Formula for shear-load coefficient
        
    Notes
    -----
    LaTeX: $C_V = 1.825 \\cdot W_f \\left( \\frac{{L}}{{\\sum G}} \\right)^{{0.2}}$
    
    References
    ----------
    CSA O86:24 7.5.7.6 d) i)
    """
    return create_formula(
        name="C_V",
        params={
            "W_f": Param("W_f", desc="total factored loads on beam"),
            "L": Param("L", desc="length of beam"),
            "Sum_G": Param("\\sum G", desc="sum of G factors")
        },
        logic=lambda W_f, L, Sum_G: 1.825 * W_f * (L / Sum_G)**0.2,
        latex_template=lambda W_f, L, Sum_G: f"1.825 \\cdot {W_f} \\left( \\frac{{{L}}}{{{Sum_G}}} \\right)^{{0.2}}",
        source="CSA O86:24 7.5.7.6 d) i)",
        desc="Shear-Load Coefficient"
    )


@formula
def modified_shear_strength(f_v: float, K_D: float, K_H: float, K_Sv: float, K_T: float) -> EngineeringFormula:
    """
    Modified strength in shear.
    
    Parameters
    ----------
    f_v : float
        Specified strength in shear
    K_D : float
        Load-duration factor
    K_H : float
        System factor
    K_Sv : float
        Service condition factor
    K_T : float
        Treatment factor
        
    Returns
    -------
    EngineeringFormula
        Formula for modified shear strength
        
    Notes
    -----
    LaTeX: $F_v = f_v \\cdot K_D \\cdot K_H \\cdot K_{{Sv}} \\cdot K_T$
    
    References
    ----------
    CSA O86:24 7.5.7.3 b)
    """
    return create_formula(
        name="F_v",
        params={
            "f_v": Param("f_v", unit="MPa", desc="specified shear strength"),
            "K_D": Param("K_D", unit="dimensionless", desc="load-duration factor"),
            "K_H": Param("K_H", unit="dimensionless", desc="system factor"),
            "K_Sv": Param("K_{{Sv}}", unit="dimensionless", desc="service condition factor"),
            "K_T": Param("K_T", unit="dimensionless", desc="treatment factor")
        },
        logic=lambda f_v, K_D, K_H, K_Sv, K_T: f_v * K_D * K_H * K_Sv * K_T,
        latex_template=lambda f_v, K_D, K_H, K_Sv, K_T: f"{f_v} \\cdot {K_D} \\cdot {K_H} \\cdot {K_Sv} \\cdot {K_T}",
        source="CSA O86:24 7.5.7.3 b)",
        desc="Modified Shear Strength"
    )


@formula
def total_shear_resistance(phi: float, F_v: float, A_g: float, C_V: float, Z: float) -> EngineeringFormula:
    """
    Total factored shear resistance, W_r.
    
    Parameters
    ----------
    phi : float
        Shear resistance modification factor
    F_v : float
        Factored strength in shear
    A_g : float
        Gross cross-sectional area, mm²
    C_V : float
        Shear load coefficient
    Z : float
        Beam volume, m³
        
    Returns
    -------
    EngineeringFormula
        Formula for total shear resistance
        
    Notes
    -----
    LaTeX: $W_r = \\phi \\cdot F_v \\cdot 0.48 \\cdot A_g \\cdot C_V \\cdot Z^{{-0.18}}$
    
    References
    ----------
    CSA O86:24 7.5.7.3 a)
    """
    return create_formula(
        name="W_r",
        params={
            "phi": Param("\\phi", desc="shear resistance modification factor"),
            "F_v": Param("F_v", desc="factored strength in shear"),
            "A_g": Param("A_g", desc="gross cross-sectional area, mm²"),
            "C_V": Param("C_V", desc="shear load coefficient"),
            "Z": Param("Z", desc="beam volume, m³")
        },
        logic=lambda phi, F_v, A_g, C_V, Z: phi * F_v * 0.48 * A_g * C_V * Z**(-0.18),
        latex_template=lambda phi, F_v, A_g, C_V, Z: f"{phi} \\cdot {F_v} \\cdot 0.48 \\cdot {A_g} \\cdot {C_V} \\cdot {Z}^{{-0.18}}",
        source="CSA O86:24 7.5.7.3 a)",
        desc="Total Shear Resistance"
    )


@formula
def shear_resistance(phi: float, F_v: float, A_g: float, V_f: float = None) -> EngineeringFormula:
    """
    Factored shear resistance, V_r.
    
    Parameters
    ----------
    phi : float
        Shear resistance modification factor
    F_v : float
        Factored strength in shear
    A_g : float
        Gross cross-sectional area, mm²
    V_f : float, optional
        Factored shear force (for checks)
        
    Returns
    -------
    EngineeringFormula
        Formula for shear resistance
        
    Notes
    -----
    LaTeX: $V_r = \\phi \\cdot F_v \\cdot \\frac{{2 \\cdot A_g}}{{3}}$
    
    Checks:
        - Factored force must not exceed resistance
    
    References
    ----------
    CSA O86:24 7.5.7.3 b)
    """
    return create_formula(
        name="V_r",
        params={
            "phi": Param("\phi", unit="dimensionless", desc="shear resistance modification factor"),
            "F_v": Param("F_v", unit="MPa", desc="factored strength in shear"),
            "A_g": Param("A_g", unit="mm**2", desc="gross cross-sectional area, mm²")
        },
        logic=lambda phi, F_v, A_g: phi * F_v * 2 * A_g / 3,
        latex_template=lambda phi, F_v, A_g: f"{phi} \\cdot {F_v} \\cdot \\frac{{2 \\cdot {A_g}}}{{3}}",
        source="CSA O86:24 7.5.7.3 b)",
        checks=[
            Check.lowerbound(V_f, STATUS.FAIL, 201, "Factored force exceeds resistance.")
        ] if V_f is not None else [],
        desc="Shear Resistance"
    )
