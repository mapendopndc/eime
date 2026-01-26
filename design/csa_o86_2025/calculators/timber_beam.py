"""
Timber Beam Calculator

High-level calculator for timber beam design using CSA O86-2025.
"""

from eime import EngineeringCalculator, EngineeringProcedure
from typing import Any
import pandas as pd


class TimberBeamCalculator(EngineeringCalculator):
    """
    Calculator for timber beam design per CSA O86:24.
    
    This calculator orchestrates bending and shear resistance
    calculations for glulam timber beams.
    
    Examples
    --------
    >>> from pint import UnitRegistry
    >>> ureg = UnitRegistry()
    >>> 
    >>> calc = TimberBeamCalculator()
    >>> results = calc.design(
    ...     b=130 * ureg.mm,
    ...     d=456 * ureg.mm,
    ...     L=6000 * ureg.mm,
    ...     f_b=30.8 * ureg.MPa,
    ...     f_v=2.1 * ureg.MPa,
    ...     M_f=50.5 * ureg.kN * ureg.m,
    ...     V_f=25.2 * ureg.kN,
    ...     P_L_percent=44.1,
    ...     P_S_percent=55.9,
    ...     K_H=1.0,
    ...     K_Sb=1.0,
    ...     K_Sv=1.0,
    ...     K_T=1.0,
    ...     K_x=1.0,
    ...     phi_b=0.9,
    ...     phi_v=0.9
    ... )
    """
    
    def __init__(self) -> None:
        super().__init__(name="Timber Beam Calculator")
    
    def validate_inputs(self, **inputs: Any) -> None:
        """
        Validate input parameters.
        
        Args:
            **inputs: Named input parameters
            
        Raises:
            ValueError: If required inputs are missing or invalid
        """
        required = [
            'b', 'd', 'L', 'f_b', 'f_v', 'M_f', 'V_f',
            'P_L_percent', 'P_S_percent', 'K_H', 'K_Sb', 'K_Sv',
            'K_T', 'K_x', 'phi_b', 'phi_v'
        ]
        
        for param in required:
            if param not in inputs:
                raise ValueError(f"Missing required input: {param}")
    
    def run_design(self, **inputs: Any) -> EngineeringProcedure:
        """
        Execute the beam design calculation.
        
        Args:
            **inputs: Named input parameters including:
                - b: beam width
                - d: beam depth
                - L: beam span
                - f_b: specified bending strength
                - f_v: specified shear strength
                - M_f: factored applied moment
                - V_f: factored applied shear
                - P_L_percent: percentage long-term load
                - P_S_percent: percentage standard-term load
                - K_H: system factor
                - K_Sb, K_Sv: service condition factors
                - K_T: treatment factor
                - K_x: curvature factor
                - phi_b, phi_v: resistance factors
            
        Returns:
            EngineeringProcedure with complete design workflow
        """
        from design.csa_o86_2025.formulas import (
            long_duration_factor,
            modified_bending_strength,
            section_modulus,
            bending_size_factor,
            moment_resistance_a,
            modified_shear_strength,
            shear_resistance
        )
        from design.csa_o86_2025.procedures import (
            glulam_bending_procedure,
            glulam_shear_procedure
        )
        from eime import EngineeringFunction, DisplayText
        
        # Calculate load duration factor (shared by bending and shear)
        KD = long_duration_factor(inputs['P_L_percent'], inputs['P_S_percent'])
        
        # Bending calculations - pass formulas directly without extracting values
        Fb = modified_bending_strength(
            inputs['f_b'],
            KD,  # Pass formula directly
            inputs['K_H'],
            inputs['K_Sb'],
            inputs['K_T']
        )
        
        S = section_modulus(inputs['b'], inputs['d'])
        
        KZbg = bending_size_factor(inputs['b'], inputs['d'], inputs['L'])
        
        Mr_a = moment_resistance_a(
            inputs['phi_b'],
            Fb,      # Pass formula directly
            S,       # Pass formula directly
            inputs['K_x'],
            KZbg     # Pass formula directly
        )
        
        # Shear calculations - pass formulas directly without extracting values
        Fv = modified_shear_strength(
            inputs['f_v'],
            KD,  # Pass formula directly (reused)
            inputs['K_H'],
            inputs['K_Sv'],
            inputs['K_T']
        )
        
        A = inputs['b'] * inputs['d']
        Vr = shear_resistance(inputs['phi_v'], Fv, A)  # Pass formula directly
        
        # Create and combine procedures
        procedure = EngineeringProcedure("Timber Beam Design")
        
        bending_proc = glulam_bending_procedure(KD=KD, Fb=Fb, KZbg=KZbg, S=S, Mr=Mr_a)
        procedure.merge(bending_proc, title="Bending Resistance", level=3)
        
        shear_proc = glulam_shear_procedure(Fv=Fv, Vr=Vr)
        procedure.merge(shear_proc, title="Shear Resistance", level=3)
        
        return procedure
    
    def format_results(self, procedure: EngineeringProcedure) -> pd.DataFrame:
        """
        Format procedure results for output.
        
        Args:
            procedure: Completed design procedure
            
        Returns:
            DataFrame with formatted results
        """
        return procedure.summary()


__all__ = ["TimberBeamCalculator"]
