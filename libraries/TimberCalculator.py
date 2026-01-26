from libraries import TimberTables, TimberDesign,TimberProcedures
from libraries.eime import EngineeringProcedure, EngineeringDesign, EngineeringCheck
from typing import Dict
import pandas as pd

class RectangularProfile:
    def __init__(self, b, d):
        self.b = b
        self.d = d
    def MomentofInertia(self):
        return self.b * pow(self.d, 3) / 12

class TimberMaterial:
    def __init__(self, grade, species):
        self.f_b = TimberTables.SpecifiedStrengthTable[species][grade]["f_b_pos"]
        self.f_v = TimberTables.SpecifiedStrengthTable[species][grade]["f_v"]
        self.f_c= TimberTables.SpecifiedStrengthTable[species][grade]["f_c"]
        self.E = TimberTables.SpecifiedStrengthTable[species][grade]["E"]

class TimberSection:
    def __init__(self, profile: RectangularProfile, material: TimberMaterial):
        self.profile = profile
        self.material = material
    
class TimberDesignParameters:
    def __init__(self, beam_ids, beam_length, end_conditions, service_conditions, lu, Wf, SumG):
        self.K_e = TimberTables.EffectiveLengthFactorTable[end_conditions]
        # Service Factors
        self.K_Sb = TimberTables.ServiceConditionFactorTable[service_conditions]["K_Sb"]
        self.K_Sv = TimberTables.ServiceConditionFactorTable[service_conditions]["K_Sv"]
        self.K_Sc = TimberTables.ServiceConditionFactorTable[service_conditions]["K_Sc"]
        self.K_SE = TimberTables.ServiceConditionFactorTable[service_conditions]["K_SE"]

        self.beam_ids = beam_ids
        self.L = beam_length
        self.lu = lu
        self.Wf = Wf
        self.SumG = SumG

        self.phi_b = 0.9
        self.phi_v = 0.9
        self.phi_c = 0.8
        self.K_H = 1.0 # Could apply 1.1 system factor is spacing < 0.610 acc. 7.4.4
        self.K_T = 1.0 # No treatment
        self.K_x = 1.0 # No curvature

class TimberLoads:
    M3=PL_M3=PS_M3 = []
    M2=PL_M2=PS_M2 = []
    V3=PL_V3=PS_V3 = []
    V2=PL_V2=PS_V2 = []
    P=PL_P=PS_P = []

class TimberBeamDesign(EngineeringDesign):

    def __init__(self, section:TimberSection, loading:TimberLoads, parameters:TimberDesignParameters):
        self.section: TimberSection = section
        self.loading: TimberLoads = loading
        self.parameters: TimberDesignParameters = parameters
        self.utilization: pd.DataFrame = pd.DataFrame({"beam_id": parameters.beam_ids})
        self.status_log: pd.DataFrame = pd.DataFrame({"beam_id": parameters.beam_ids})
        self.checklist: Dict[int, EngineeringCheck] = {}

    def BendingResistance(self, axis, sign) -> EngineeringProcedure:
        
        loads = self.loading
        params = self.parameters
        dim = self.section.profile
        mat = self.section.material

        calcs = {}
        calcs["KD"] = TimberDesign.LongDurationFactor(loads.PL_M3, loads.PS_M3)
        calcs["Fb"] = TimberDesign.ModifiedBendingStrength(mat.f_b, calcs["KD"], params.K_H, params.K_Sb, params.K_T)
        calcs["KZbg"] = TimberDesign.BendingSizeFactor(dim.b,dim.d,params.L*1000)
        calcs["S"] = TimberDesign.SectionModulus(dim.b,dim.d/1000)
        calcs["lambda1"] = TimberDesign.SlendernessRatio(params.lu*1000, dim.d, dim.b)
        calcs["lambda_e"] = TimberDesign.SlendernessRatioLimit(mat.E, params.K_SE, params.K_T, calcs["Fb"])
        calcs["KL_a"] = TimberDesign.LateralStabilityFactorA()
        calcs["KL_b"] = TimberDesign.LateralStabilityFactorB(calcs["lambda1"], calcs["lambda_e"])
        calcs["KL"] = TimberDesign.LateralStabilityFactor(calcs["lambda1"], calcs["lambda_e"], calcs["KL_a"], calcs["KL_b"], None, None)
        calcs["MrA"] = TimberDesign.MomentResistanceA(params.phi_b,calcs["Fb"],calcs["S"],params.K_x,calcs["KZbg"])
        calcs["Mr1"] = TimberDesign.MomentResistanceB1(params.phi_b,calcs["Fb"],calcs["S"],params.K_x,calcs["KZbg"])
        calcs["Mr2"] = TimberDesign.MomentResistanceB2(params.phi_b,calcs["Fb"],calcs["S"],params.K_x,calcs["KL"])
        calcs["MrB"] = TimberDesign.MomentResistanceB(calcs["Mr1"],calcs["Mr2"])
        Mf = TimberDesign.AppliedMoment(loads.M3)
        calcs["Mr"] = TimberDesign.MomentResistance(calcs["KL"], calcs["MrA"], calcs["MrB"], Mf)

        return TimberProcedures.GlulamBending(**calcs)
    
    def ShearResistance(self, axis) -> EngineeringProcedure:
                
        loads = self.loading
        params = self.parameters
        dim = self.section.profile
        mat = self.section.material

        calcs ={}
        calcs["KD"] = TimberDesign.LongDurationFactor(loads.PL_V2, loads.PS_V2)
        calcs["CV"] = TimberDesign.ShearLoadCoefficient(params.Wf,params.L,params.SumG)
        calcs["Fv"] = TimberDesign.ModifiedShearStrength(mat.f_v,calcs["KD"],params.K_H,params.K_Sv,params.K_T)
        calcs["Wr"] = TimberDesign.TotalShearResistance(params.phi_v,calcs["Fv"],dim.b*dim.d/1000,calcs["CV"],dim.b*dim.d*params.L/1000/1000)
        Vf = TimberDesign.AppliedShear(abs(loads.V2))
        calcs["Vr"] = TimberDesign.ShearResistance(params.phi_v,calcs["Fv"],dim.b*dim.d/1000, Vf)

        return TimberProcedures.GlulamShear(**calcs)

    def CompressionResistance(self) -> EngineeringProcedure:
                
        loads = self.loading
        params = self.parameters
        dim = self.section.profile
        mat = self.section.material

        calcs ={}
        calcs["KD"] = TimberDesign.LongDurationFactor(loads.PL_P, loads.PS_P)
        calcs["Fc"] = TimberDesign.ModifiedCompressionStrength(mat.f_c,calcs["KD"],params.K_H,params.K_Sc,params.K_T)
        calcs["KZcg"] = TimberDesign.CompressionSizeFactor(dim.b*dim.d*params.L/1000/1000)
        calcs["CC"] = TimberDesign.CompressionSlendernessRatio(params.L * params.K_e * 1000, dim.b)
        calcs["KC"] = TimberDesign.SlendernessFactor(calcs["Fc"], calcs["KZcg"], calcs["CC"], mat.E*0.87, params.K_SE, params.K_T)
        P = TimberDesign.AppliedShear(abs(loads.P))
        calcs["Pr"] = TimberDesign.CompressionResistance(params.phi_c, calcs["Fc"], dim.b*dim.d/1000, calcs["KZcg"], calcs["KC"], P)

        return TimberProcedures.GlulamCompression(**calcs)

    def checkAll(self):
        self.strongAxisPosBendingCheck = self.BendingResistance(0, 0)
        self.utilization['uM3'] = self.strongAxisPosBendingCheck.utilizations.max(1)
        self.status_log = self.status_log.join(self.strongAxisPosBendingCheck.status_log, rsuffix='_M3')
        self.checklist.update(self.strongAxisPosBendingCheck.checks)

        self.strongAxisShearCheck = self.ShearResistance(0)
        self.utilization['uV2'] = self.strongAxisShearCheck.utilizations.max(1)
        self.status_log = self.status_log.join(self.strongAxisShearCheck.status_log, rsuffix='_V2')
        self.checklist.update(self.strongAxisShearCheck.checks)

        self.parallelCompressionCheck = self.CompressionResistance()
        self.utilization['uP'] = self.parallelCompressionCheck.utilizations.max(1)
        self.status_log = self.status_log.join(self.parallelCompressionCheck.status_log, rsuffix='_P')
        self.checklist.update(self.parallelCompressionCheck.checks)
