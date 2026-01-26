"""
Timber Beam Calculator

High-level calculator for timber beam design using CSA O86-2025.
"""

from eime import SimpleCalculator
from typing import Dict, Any


class TimberBeamCalculator(SimpleCalculator):
    """
    Calculator for timber beam design per CSA O86:24.
    
    This calculator orchestrates bending, shear, and compression resistance
    calculations for glulam timber beams.
    
    Parameters
    ----------
    section_properties : dict
        Dictionary containing:
        - b: width (mm)
        - d: depth (mm)
        - A: cross-sectional area (mm²)
    material_properties : dict
        Dictionary containing:
        - f_b: specified bending strength (MPa)
        - f_v: specified shear strength (MPa)
        - f_c: specified compression strength (MPa)
        - E: specified modulus of elasticity (MPa)
    design_parameters : dict
        Dictionary containing:
        - phi_b: bending resistance factor
        - phi_v: shear resistance factor
        - phi_c: compression resistance factor
        - K_H: system factor
        - K_Sb, K_Sv, K_Sc, K_SE: service condition factors
        - K_T: treatment factor
        - K_x: curvature factor
    loading : dict
        Dictionary containing:
        - M_f: factored applied moment (kNm)
        - V_f: factored applied shear (kN)
        - P_f: factored applied compression (kN)
        - P_L: long-term load for K_D calculation
        - P_S: standard-term load for K_D calculation
        
    Examples
    --------
    >>> calc = TimberBeamCalculator(
    ...     section_properties={'b': 130, 'd': 456, 'A': 59280},
    ...     material_properties={'f_b': 30.8, 'f_v': 2.1, 'f_c': 27.5, 'E': 11700},
    ...     design_parameters={
    ...         'phi_b': 0.9, 'phi_v': 0.9, 'phi_c': 0.8,
    ...         'K_H': 1.0, 'K_Sb': 1.0, 'K_Sv': 1.0, 'K_Sc': 1.0, 'K_SE': 1.0,
    ...         'K_T': 1.0, 'K_x': 1.0
    ...     },
    ...     loading={'M_f': 50, 'V_f': 25, 'P_f': 100, 'P_L': 10, 'P_S': 20}
    ... )
    >>> results = calc.calculate()
    """
    
    def __init__(
        self,
        section_properties: Dict[str, float],
        material_properties: Dict[str, float],
        design_parameters: Dict[str, float],
        loading: Dict[str, float]
    ):
        super().__init__(name="Timber Beam Calculator")
        self.section = section_properties
        self.material = material_properties
        self.params = design_parameters
        self.loads = loading
        
    def calculate(self) -> Dict[str, Any]:
        """
        Perform timber beam design calculations.
        
        Returns
        -------
        dict
            Dictionary containing:
            - bending_resistance: M_r (kNm)
            - shear_resistance: V_r (kN)
            - compression_resistance: P_r (kN)
            - bending_utilization: M_f / M_r
            - shear_utilization: V_f / V_r
            - compression_utilization: P_f / P_r
            - status: 'PASS' or 'FAIL'
        """
        from design.csa_o86_2025.formulas import (
            long_duration_factor,
            modified_bending_strength,
            section_modulus,
            bending_size_factor,
            moment_resistance_a,
            modified_shear_strength,
            shear_resistance,
            modified_compression_strength,
            compression_resistance
        )
        
        # Calculate K_D (long duration factor)
        KD = long_duration_factor(self.loads['P_L'], self.loads['P_S'])
        K_D_value = KD.calculate()
        
        # Bending resistance (simplified - assuming fully braced)
        Fb = modified_bending_strength(
            self.material['f_b'],
            K_D_value,
            self.params['K_H'],
            self.params['K_Sb'],
            self.params['K_T']
        )
        F_b_value = Fb.calculate()
        
        S = section_modulus(self.section['b'], self.section['d'])
        S_value = S.calculate()
        
        KZbg = bending_size_factor(
            self.section['b'],
            self.section['d'],
            self.params.get('L', 5000)  # Default 5m if not provided
        )
        K_Zbg_value = KZbg.calculate()
        
        Mr_a = moment_resistance_a(
            self.params['phi_b'],
            F_b_value,
            S_value,
            self.params['K_x'],
            K_Zbg_value
        )
        M_r = Mr_a.calculate() / 1e6  # Convert to kNm
        
        # Shear resistance
        Fv = modified_shear_strength(
            self.material['f_v'],
            K_D_value,
            self.params['K_H'],
            self.params['K_Sv'],
            self.params['K_T']
        )
        F_v_value = Fv.calculate()
        
        Vr = shear_resistance(
            self.params['phi_v'],
            F_v_value,
            self.section['A']
        )
        V_r = Vr.calculate() / 1000  # Convert to kN
        
        # Compression resistance (simplified - assuming short column)
        Fc = modified_compression_strength(
            self.material['f_c'],
            K_D_value,
            self.params['K_H'],
            self.params['K_Sc'],
            self.params['K_T']
        )
        F_c_value = Fc.calculate()
        
        # Simplified - assuming K_Zcg = 1.0 and K_C = 1.0 for short columns
        Pr = compression_resistance(
            self.params['phi_c'],
            F_c_value,
            self.section['A'],
            1.0,  # K_Zcg
            1.0   # K_C
        )
        P_r = Pr.calculate() / 1000  # Convert to kN
        
        # Calculate utilizations
        bending_util = self.loads['M_f'] / M_r if M_r > 0 else float('inf')
        shear_util = self.loads['V_f'] / V_r if V_r > 0 else float('inf')
        compression_util = self.loads['P_f'] / P_r if P_r > 0 else float('inf')
        
        # Determine overall status
        max_util = max(bending_util, shear_util, compression_util)
        status = 'PASS' if max_util <= 1.0 else 'FAIL'
        
        return {
            'bending_resistance_kNm': M_r,
            'shear_resistance_kN': V_r,
            'compression_resistance_kN': P_r,
            'bending_utilization': bending_util,
            'shear_utilization': shear_util,
            'compression_utilization': compression_util,
            'max_utilization': max_util,
            'status': status
        }


__all__ = ["TimberBeamCalculator"]
