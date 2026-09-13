from design.csa_o86_2025 import tables as TimberTables
from design.csa_o86_2025 import formulas as TimberDesign
from design.csa_o86_2025 import procedures as TimberProcedures
from eime import EngineeringProcedure, EngineeringCheck
from typing import Dict
import pandas as pd
import numpy as np
import warnings


class RectangularProfile:
    """Rectangular cross-section with width b and depth d (Pint quantities)."""
    def __init__(self, b, d):
        self.b = b
        self.d = d
        
    def MomentofInertia(self):
        """Calculate moment of inertia."""
        I_value = self.b * pow(self.d, 3) / 12
        return I_value
    
    def Area(self):
        """Calculate cross-sectional area."""
        return self.b * self.d


class TimberMaterial:
    """Timber material properties from CSA O86 tables (grade, species)."""
    def __init__(self, grade, species, ureg):
        # Load raw values from tables
        props = TimberTables.SpecifiedStrengthTable[species][grade]
        
        # Store as Pint quantities with units
        self.f_b_pos = props["f_b_pos"] * ureg.MPa  # Positive bending strength
        self.f_b_neg = props["f_b_neg"] * ureg.MPa  # Negative bending strength
        self.f_v = props["f_v"] * ureg.MPa
        self.f_c = props["f_c"] * ureg.MPa
        self.E = props["E"] * ureg.MPa
        self.grade = grade
        self.species = species


class TimberSection:
    def __init__(self, profile: RectangularProfile, material: TimberMaterial):
        self.profile = profile
        self.material = material


class TimberDesignParameters:
    """Design parameters: beam_ids, beam_length, end_conditions, service_conditions, lu, Wf, SumG."""
    def __init__(self, beam_ids, beam_length, end_conditions, service_conditions, 
                 lu=None, Wf=None, SumG=None, ureg=None, lu_strong=None, lu_weak=None, L_zbg=None):
        self.K_e = TimberTables.EffectiveLengthFactorTable[end_conditions] * ureg.dimensionless
        
        # Service Factors (dimensionless from tables)
        self.K_Sb = TimberTables.ServiceConditionFactorTable[service_conditions]["K_Sb"] * ureg.dimensionless
        self.K_Sv = TimberTables.ServiceConditionFactorTable[service_conditions]["K_Sv"] * ureg.dimensionless
        self.K_Sc = TimberTables.ServiceConditionFactorTable[service_conditions]["K_Sc"] * ureg.dimensionless
        self.K_SE = TimberTables.ServiceConditionFactorTable[service_conditions]["K_SE"] * ureg.dimensionless

        self.beam_ids = beam_ids
        self.L = beam_length
        
        # Support both old (lu) and new (lu_strong, lu_weak) interfaces
        if lu_strong is not None and lu_weak is not None:
            self.lu_strong = lu_strong  # Unbraced length about strong axis (d)
            self.lu_weak = lu_weak      # Unbraced length about weak axis (b)
            self.lu = lu_strong  # For backward compatibility with bending checks
        elif lu is not None:
            self.lu = lu
            self.lu_strong = lu
            self.lu_weak = lu
        else:
            raise ValueError("Must provide either 'lu' or both 'lu_strong' and 'lu_weak'")
        
        # L_zbg: segment length between zero moment points (for K_Zbg size factor)
        # Defaults to beam_length if not provided
        self.L_zbg = L_zbg if L_zbg is not None else beam_length
        
        self.Wf = Wf if Wf is not None else 1.0 * ureg.dimensionless
        self.SumG = SumG if SumG is not None else 0.0 * ureg.dimensionless

        # Design factors (dimensionless)
        self.phi_b = 0.9 * ureg.dimensionless
        self.phi_v = 0.9 * ureg.dimensionless
        self.phi_c = 0.8 * ureg.dimensionless
        self.K_H = 1.0 * ureg.dimensionless  # Could apply 1.1 system factor if spacing < 0.610 acc. 7.4.4
        self.K_T = 1.0 * ureg.dimensionless  # No treatment
        self.K_x = 1.0 * ureg.dimensionless  # No curvature
        
        self.ureg = ureg


class TimberLoads:
    """Applied loads: M3, M2 (moments), V2, V3 (shear), P (axial)."""
    def __init__(self):
        # Load components
        self.M3 = None
        self.M2 = None
        self.V2 = None
        self.V3 = None
        self.P = None


class TimberLoadingParameters:
    """Load duration parameters for K_D calculation: P_L/P_S ratios for each force type."""
    def __init__(self, P_L_M, P_S_M, P_L_V, P_S_V, P_L_P, P_S_P, load_combo_types, ureg):
        # Moment ratios (for bending checks)
        self.P_L_M = P_L_M
        self.P_S_M = P_S_M
        # Shear ratios (for shear checks)
        self.P_L_V = P_L_V
        self.P_S_V = P_S_V
        # Axial ratios (for compression checks)
        self.P_L_P = P_L_P
        self.P_S_P = P_S_P
        # Load combination types
        self.load_combo_types = load_combo_types
        self.ureg = ureg


class TimberBeamDesign:
    """Timber beam design per CSA O86: bending, shear, compression checks."""

    def __init__(self, section:TimberSection, loading:TimberLoads, parameters:TimberDesignParameters, loading_params:TimberLoadingParameters):
        self.section: TimberSection = section
        self.loading: TimberLoads = loading
        self.parameters: TimberDesignParameters = parameters
        self.loading_params: TimberLoadingParameters = loading_params
        self.utilization: pd.DataFrame = pd.DataFrame({"beam_id": parameters.beam_ids})
        self.status_log: pd.DataFrame = pd.DataFrame({"beam_id": parameters.beam_ids})
        self.checklist: Dict[int, EngineeringCheck] = {}

    def BendingResistance(self, axis, sign) -> EngineeringProcedure:
        """Calculate bending resistance per CSA O86.
        
        The method automatically detects the sign of bending moment at each station
        and uses the appropriate bending strength (f_b_pos or f_b_neg).
        """
        
        loads = self.loading
        params = self.parameters
        loading_params = self.loading_params
        dim = self.section.profile
        mat = self.section.material

        calcs = {}
        
        nd = params.ureg.dimensionless
        ratio_vector = (loading_params.P_L_M / loading_params.P_S_M).magnitude * nd
        kd_table_vector = np.array([TimberTables.kd_from_load_type(t) for t in loading_params.load_combo_types]) * nd
        
        calcs["KD"] = TimberDesign.load_duration_factor(ratio=ratio_vector, P_L=loading_params.P_L_M, P_S=loading_params.P_S_M, kd_table=kd_table_vector)
        
        # Determine which f_b to use based on moment sign
        # Convention: Positive applied moment → negative bending (compression on bottom)
        #            Negative applied moment → positive bending (compression on top)
        # Detect moment sign from loads.M3 (can be scalar or array)
        if loads.M3 is not None:
            # Convert to array if scalar
            M_values = np.atleast_1d(loads.M3.magnitude if hasattr(loads.M3, 'magnitude') else loads.M3)
            # Use f_b_neg for positive moments, f_b_pos for negative moments
            # Create array of f_b values matching the moment sign at each station
            f_b_array = np.where(M_values >= 0, mat.f_b_neg.magnitude, mat.f_b_pos.magnitude) * params.ureg.MPa
        else:
            # If no moment specified, default to negative bending strength
            f_b_array = mat.f_b_neg
        
        calcs["Fb"] = TimberDesign.modified_bending_strength(f_b_array, calcs["KD"].result, params.K_H, params.K_Sb, params.K_T)
        calcs["KZbg"] = TimberDesign.bending_size_factor(dim.b, dim.d, params.L_zbg)
        calcs["S"] = TimberDesign.section_modulus(dim.b, dim.d)
        calcs["lambda1"] = TimberDesign.slenderness_ratio(params.lu, dim.d, dim.b)
        calcs["lambda_e"] = TimberDesign.slenderness_ratio_limit(mat.E, params.K_SE, params.K_T, calcs["Fb"])
        calcs["KL_a"] = TimberDesign.lateral_stability_factor_a()
        calcs["KL_b"] = TimberDesign.lateral_stability_factor_b(calcs["lambda1"], calcs["lambda_e"])
        calcs["KL"] = TimberDesign.lateral_stability_factor(calcs["lambda1"], calcs["lambda_e"], calcs["KL_a"], calcs["KL_b"], calcs["KL_b"], calcs["KL_b"])
        calcs["MrA"] = TimberDesign.moment_resistance_a(params.phi_b, calcs["Fb"], calcs["S"], params.K_x, calcs["KZbg"])
        calcs["Mr1"] = TimberDesign.moment_resistance_b1(params.phi_b, calcs["Fb"], calcs["S"], params.K_x, calcs["KZbg"])
        calcs["Mr2"] = TimberDesign.moment_resistance_b2(params.phi_b, calcs["Fb"], calcs["S"], params.K_x, calcs["KL"])
        calcs["MrB"] = TimberDesign.moment_resistance_b(calcs["Mr1"], calcs["Mr2"])
        calcs["Mr"] = TimberDesign.moment_resistance(calcs["KL"], calcs["MrA"], calcs["MrB"], loads.M3)

        return TimberProcedures.glulam_bending_procedure(**calcs)
    
    def ShearResistance(self, axis) -> EngineeringProcedure:
        """Calculate shear resistance per CSA O86."""
                
        loads = self.loading
        params = self.parameters
        loading_params = self.loading_params
        dim = self.section.profile
        mat = self.section.material

        calcs = {}
        
        nd = params.ureg.dimensionless
        ratio_vector = (loading_params.P_L_V / loading_params.P_S_V).magnitude * nd
        kd_table_vector = np.array([TimberTables.kd_from_load_type(t) for t in loading_params.load_combo_types]) * nd
        
        calcs["KD"] = TimberDesign.load_duration_factor(ratio=ratio_vector, P_L=loading_params.P_L_V, P_S=loading_params.P_S_V, kd_table=kd_table_vector)
        calcs["CV"] = TimberDesign.shear_load_coefficient(params.Wf, params.L.to('mm'), params.SumG)
        calcs["Fv"] = TimberDesign.modified_shear_strength(mat.f_v, calcs["KD"].result, params.K_H, params.K_Sv, params.K_T)
        calcs["Wr"] = TimberDesign.total_shear_resistance(params.phi_v, calcs["Fv"], dim.b*dim.d, calcs["CV"], (dim.b*dim.d*params.L).to('mm**3'))
        calcs["Vr"] = TimberDesign.shear_resistance(params.phi_v, calcs["Fv"], dim.b*dim.d, loads.V2)

        return TimberProcedures.glulam_shear_procedure(**calcs)

    def CompressionResistance(self, axis='both') -> EngineeringProcedure:
        """Calculate compression resistance per CSA O86.
        
        Parameters
        ----------
        axis : str, optional
            Which axis to check: 'strong', 'weak', or 'both' (default).
            'both' returns the governing (worst) case.
            
        Returns
        -------
        EngineeringProcedure
            Compression resistance procedure for the specified axis
        """
        
        if axis == 'both':
            # Check both axes and return the governing case
            strong_proc = self._CompressionResistance_SingleAxis('strong')
            weak_proc = self._CompressionResistance_SingleAxis('weak')
            
            # Compare utilizations - higher is governing
            strong_util = strong_proc.get_worst_utilization().max()
            weak_util = weak_proc.get_worst_utilization().max()
            
            if strong_util >= weak_util:
                return strong_proc
            else:
                return weak_proc
        else:
            return self._CompressionResistance_SingleAxis(axis)
    
    def _CompressionResistance_SingleAxis(self, axis) -> EngineeringProcedure:
        """Calculate compression resistance checking both axes for slenderness.
        
        Per CSA O86:24 7.5.8.2, the slenderness factor K_c shall be based on 
        the maximum slenderness ratio considering both axes of buckling.
        """
                
        loads = self.loading
        params = self.parameters
        loading_params = self.loading_params
        dim = self.section.profile
        mat = self.section.material
        
        # Determine which axis governs for naming
        if axis == 'strong':
            axis_name = "Strong Axis"
        elif axis == 'weak':
            axis_name = "Weak Axis"
        else:
            raise ValueError(f"Invalid axis '{axis}'. Must be 'strong' or 'weak'.")

        calcs = {}

        nd = params.ureg.dimensionless
        ratio_vector = (loading_params.P_L_P / loading_params.P_S_P).magnitude * nd
        kd_table_vector = np.array([TimberTables.kd_from_load_type(t) for t in loading_params.load_combo_types]) * nd
        
        calcs["KD"] = TimberDesign.load_duration_factor(ratio=ratio_vector, P_L=loading_params.P_L_P, P_S=loading_params.P_S_P, kd_table=kd_table_vector)
        calcs["Fc"] = TimberDesign.modified_compression_strength(mat.f_c, calcs["KD"].result, params.K_H, params.K_Sc, params.K_T)
        calcs["KZcg"] = TimberDesign.compression_size_factor(dim.b*dim.d*params.L)
        
        # Calculate slenderness ratio in both directions
        # Strong axis buckling: controlled by strong dimension (d)
        # Weak axis buckling: controlled by weak dimension (b)
        calcs["CC_strong"] = TimberDesign.compression_slenderness_ratio_strong_axis(
            params.lu_strong * params.K_e, dim.d
        )
        calcs["CC_weak"] = TimberDesign.compression_slenderness_ratio_weak_axis(
            params.lu_weak * params.K_e, dim.b
        )
        
        # Take maximum slenderness ratio for K_c calculation
        calcs["CC"] = TimberDesign.compression_slenderness_ratio_max(
            calcs["CC_strong"], calcs["CC_weak"]
        )
        
        # Slenderness factor uses the maximum Cc
        calcs["KC"] = TimberDesign.slenderness_factor(calcs["Fc"].result, calcs["KZcg"].result, calcs["CC"].result, mat.E*0.87, params.K_SE, params.K_T)
        
        if loads.P is not None:
            calcs["Pr"] = TimberDesign.compression_resistance(params.phi_c, calcs["Fc"].result, dim.b*dim.d, calcs["KZcg"].result, calcs["KC"].result, loads.P)
        else:
            calcs["Pr"] = TimberDesign.compression_resistance(params.phi_c, calcs["Fc"].result, dim.b*dim.d, calcs["KZcg"].result, calcs["KC"].result)

        procedure = TimberProcedures.glulam_compression_procedure(**calcs)
        procedure.name = f"Glulam Compression ({axis_name})"
        return procedure

    def _add_check_results(self, procedure: EngineeringProcedure, util_key: str, suffix: str):
        """Add check results to utilization, status log, and checklist."""
        self.utilization[util_key] = procedure.get_worst_utilization()
        status = pd.DataFrame(procedure.status_log).add_suffix(suffix)
        self.status_log = self.status_log.join(status)
        self.checklist.update(procedure.checks)

    def checkAll(self):
        self.strongAxisPosBendingCheck = self.BendingResistance(0, 0)
        self._add_check_results(self.strongAxisPosBendingCheck, 'uM3', '_M3')

        self.strongAxisShearCheck = self.ShearResistance(0)
        self._add_check_results(self.strongAxisShearCheck, 'uV2', '_V2')

        # Check both axes for compression and use governing case
        self.parallelCompressionCheck = self.CompressionResistance(axis='both')
        self._add_check_results(self.parallelCompressionCheck, 'uP', '_P')
