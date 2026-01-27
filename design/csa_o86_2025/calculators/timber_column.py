"""
Timber Column Calculator

High-level calculator for timber column design using CSA O86-2025.
"""

from eime import EngineeringCalculator, EngineeringProcedure
from typing import Any
import pandas as pd


class TimberColumnCalculator(EngineeringCalculator):
    """
    Calculator for timber column design per CSA O86:24.
    
    This calculator orchestrates axial compression resistance
    calculations for glulam timber columns.
    """
    
    def __init__(self) -> None:
        super().__init__(name="Timber Column Calculator")
    
    def validate_inputs(self, **inputs: Any) -> None:
        """
        Validate input parameters.
        
        Args:
            **inputs: Named input parameters
            
        Raises:
            ValueError: If required inputs are missing or invalid
        """
        required = [
            'b', 'd', 'L', 'L_ex', 'L_ey', 'f_c', 'E', 'P_f',
            'P_L_percent', 'P_S_percent', 'K_H', 'K_Sc', 'K_SE',
            'K_T', 'phi_c'
        ]
        
        for param in required:
            if param not in inputs:
                raise ValueError(f"Missing required input: {param}")
    
    def run_design(self, **inputs: Any) -> EngineeringProcedure:
        """
        Execute the column design calculation.
        
        Args:
            **inputs: Named input parameters including:
                - b: column width
                - d: column depth
                - L: column length (member volume)
                - L_ex: effective length for buckling about x-axis
                - L_ey: effective length for buckling about y-axis
                - f_c: specified compression strength
                - E: specified modulus of elasticity
                - P_f: factored applied compression force
                - P_L_percent: percentage long-term load
                - P_S_percent: percentage standard-term load
                - K_H: system factor
                - K_Sc: service condition factor for compression
                - K_SE: service condition factor for modulus
                - K_T: treatment factor
                - phi_c: compression resistance factor
            
        Returns:
            EngineeringProcedure with complete design workflow
        """
        from design.csa_o86_2025.formulas import (
            long_duration_factor,
            modified_compression_strength,
            compression_size_factor,
            compression_slenderness_ratio,
            slenderness_factor,
            compression_resistance
        )
        from design.csa_o86_2025.procedures import (
            glulam_compression_procedure
        )
        from eime import EngineeringFunction, DisplayText
        
        # Calculate load duration factor
        KD = long_duration_factor(inputs['P_L_percent'], inputs['P_S_percent'])
        
        # Modified compression strength
        Fc = modified_compression_strength(
            inputs['f_c'],
            KD,
            inputs['K_H'],
            inputs['K_Sc'],
            inputs['K_T']
        )
        
        # Member volume for size factor
        # Convert to meters for volume calculation
        b_m = inputs['b']
        d_m = inputs['d']
        L_m = inputs['L']
        Z = b_m * d_m * L_m  # Will be in m³ when inputs are in m
        
        KZcg = compression_size_factor(Z)
        
        # Determine governing slenderness ratio
        # Check both axes - typically L_e/b and L_e/d
        CC_x = compression_slenderness_ratio(inputs['L_ex'], inputs['d'])
        CC_y = compression_slenderness_ratio(inputs['L_ey'], inputs['b'])
        
        # Use the larger slenderness ratio (more critical)
        # For now, we'll calculate both and use max - the procedure will show both
        # We need to determine which is governing
        
        # Calculate E_05 (5th percentile MOE)
        E_05 = 0.85 * inputs['E']
        
        # Calculate slenderness factor for x-axis buckling
        KC_x = slenderness_factor(
            Fc,
            KZcg,
            CC_x,
            E_05,
            inputs['K_SE'],
            inputs['K_T']
        )
        
        # Calculate slenderness factor for y-axis buckling
        KC_y = slenderness_factor(
            Fc,
            KZcg,
            CC_y,
            E_05,
            inputs['K_SE'],
            inputs['K_T']
        )
        
        # Cross-sectional area
        A = inputs['b'] * inputs['d']
        
        # Compression resistance for x-axis buckling
        Pr_x = compression_resistance(
            inputs['phi_c'],
            Fc,
            A,
            KZcg,
            KC_x
        )
        
        # Compression resistance for y-axis buckling
        Pr_y = compression_resistance(
            inputs['phi_c'],
            Fc,
            A,
            KZcg,
            KC_y
        )
        
        # Create procedure
        procedure = EngineeringProcedure("Timber Column Design")
        
        # Add compression procedure - for x-axis buckling
        compression_proc_x = glulam_compression_procedure(
            KD=KD,
            Fc=Fc,
            KZcg=KZcg,
            CC=CC_x,
            KC=KC_x,
            Pr=Pr_x
        )
        procedure.merge(compression_proc_x, title="Compression Resistance - X-Axis Buckling", level=3)
        
        # Add compression procedure - for y-axis buckling
        compression_proc_y = glulam_compression_procedure(
            KD=None,  # Already shown above
            Fc=None,  # Already shown above
            KZcg=None,  # Already shown above
            CC=CC_y,
            KC=KC_y,
            Pr=Pr_y
        )
        procedure.merge(compression_proc_y, title="Compression Resistance - Y-Axis Buckling", level=3)
        
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


__all__ = ["TimberColumnCalculator"]
