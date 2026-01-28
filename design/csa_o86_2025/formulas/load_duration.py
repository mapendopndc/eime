"""
Load duration factor formulas per CSA O86-2025.

Handles both table-based K_D selection and formula-based calculation
for mixed long/standard duration loads.
"""

import numpy as np
from eime import (
    create_formula, 
    create_switch, 
    Param, 
    Check, 
    STATUS, 
    EngineeringFormula, 
    EngineeringSwitch,
    formula,
    switch
)



@formula
def kd_formula(P_L: float, P_S: float) -> EngineeringFormula:
    """
    Load duration factor formula for mixed long/standard loads when PL > PS.
    
    Parameters
    ----------
    P_L : float
        Long-term load (Dead load), dimensionless percent or absolute value
    P_S : float
        Standard-term load (Snow, Live, or S+0.5L, or 0.5S+L), dimensionless
        
    Returns
    -------
    EngineeringFormula
        Formula for load duration factor
        
    Notes
    -----
    Used when long-term load exceeds standard-term load.
    LaTeX: $K_D = \\max\\left(1.0 - 0.50 \\log_{10}\\left(\\frac{P_L}{P_S}\\right), 0.65\\right)$
    
    The formula ensures K_D is never less than 0.65 (permanent load case).
    
    References
    ----------
    CSA O86:24 cl.5.3.2.2
    """
    return create_formula(
        name="K_D",
        params={
            "P_L": Param("P_L", unit="dimensionless", desc="long-term load"),
            "P_S": Param("P_S", unit="dimensionless", desc="standard-term load")
        },
        logic=lambda P_L, P_S: (
            lambda pl, ps: np.maximum(1.0 - 0.50 * np.log10(np.maximum(np.abs(pl/ps), 1e-10)), 0.65)
        )(P_L, np.where(P_S == 0, 1e-10, P_S)),  # Replace zero with small value to avoid warning
        latex_template=lambda P_L, P_S: f"\\max\\left(1.0 - 0.50 \\log_{{10}}\\left(\\frac{{{P_L}}}{{{P_S}}}\\right), 0.65\\right)",
        source="CSA O86:24 cl.5.3.2.2",
        checks=[
            Check.lowerbound(0.65, STATUS.FAIL, 1, "K_D must be ≥ 0.65", inclusive=True),
            Check.upperbound(1.15, STATUS.WARNING, 2, "K_D unusually high (> 1.15)", inclusive=False)
        ],
        desc="Load Duration Factor (Formula Method)"
    )


@switch
def load_duration_factor(
    ratio: float,
    P_L: float,
    P_S: float,
    kd_table: float,
    use_formula_threshold: float = 1.0
) -> EngineeringSwitch:
    """
    Load duration factor with automatic selection between table and formula.
    
    Selects K_D based on load characteristics:
    - If ratio ≤ 1.0: Use table value (passed as parameter)
    - If ratio > 1.0: Use formula method (indicates mixed long/standard loads)
    
    Parameters
    ----------
    ratio : float
        Load duration ratio (P_L/P_S), safely computed by caller
    P_L : float
        Long-term load percentage or magnitude
    P_S : float
        Standard-term load percentage or magnitude
    kd_table : float
        K_D value from table for standard load case:
        0.65 (permanent/dead only), 1.0 (standard/live), or 1.15 (short/wind/seismic)
    use_formula_threshold : float, optional
        Threshold ratio for switching to formula (default 1.0)
        
    Returns
    -------
    EngineeringSwitch
        Switch formula for load duration factor
        
    Notes
    -----
    **Table values (CSA O86:24 cl.5.3.2):**
    - Dead only: K_D = 0.65 (permanent load)
    - Includes live/snow: K_D = 1.0 (standard duration)
    - Includes wind/seismic: K_D = 1.15 (short duration)
    
    **Formula method (CSA O86:24 cl.5.3.2.2):**
    When long-term load dominates (PL > PS), the formula accounts for
    the actual load duration mix: K_D = max(1.0 - 0.50*log₁₀(PL/PS), 0.65)
    
    Examples
    --------
    >>> # Standard case - use table
    >>> kd = load_duration_factor(P_L=25.0, P_S=40.0, kd_table=1.0)
    >>> # PL < PS, so K_D = 1.0 from table
    
    >>> # Formula case - PL dominates
    >>> kd = load_duration_factor(P_L=100.0, P_S=50.0, kd_table=1.0)
    >>> # PL > PS, so formula is used and displayed in procedure
    
    References
    ----------
    CSA O86:24 cl.5.3.2
    """
    # Note: ratio is passed as a parameter and used directly
    # The caller has already handled safe division and edge cases
    
    return create_switch(
        name="K_D",
        params={
            "ratio": Param("P_L/P_S", unit="dimensionless", desc="load ratio"),
        },
        bounds=[use_formula_threshold],
        outputs=[
            kd_table,  # ratio ≤ 1.0: use table value (simple constant)
            kd_formula(P_L=P_L, P_S=P_S)  # ratio > 1.0: use formula (shows calculation)
        ],
        source="CSA O86:24 cl.5.3.2",
        checks=[
            Check.lowerbound(0.65, STATUS.FAIL, 10, "K_D must be ≥ 0.65", inclusive=True),
            Check.upperbound(1.15, STATUS.WARNING, 11, "K_D exceeds typical maximum", inclusive=False)
        ],
        desc="Load Duration Factor",
        comments=f"Table K_D = {kd_table}"
    )

