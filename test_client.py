from libraries import TimberTables
from libraries.TimberCalculator import *
from libraries.eime import status_desc
import pandas as pd

import time

if __name__=="__main__":
    #import data
    df = pd.read_csv("test_data/design_results.csv")
    data = df
    start = time.time()

    # Section
    profile = RectangularProfile(100,600)

    species = list(TimberTables.SpecifiedStrengthTable.keys())[0]
    grade = list(TimberTables.SpecifiedStrengthTable[species].keys())[0]
    material = TimberMaterial(grade, species)

    section = TimberSection(profile, material)

    # Loading
    loading = TimberLoads()
    loading.M3,loading.PL_M3,loading.PS_M3 = data["M3f"], data["PL - M3"], data["PS - M3"]
    loading.V2,loading.PL_V2,loading.PS_V2 = data["V2f"], data["PL - V2"], data["PS - V2"]
    loading.P,loading.PL_P,loading.PS_P = data["Pf"], data["PL - P"], data["PS - P"]

    # Design
    end_conditions = list(TimberTables.EffectiveLengthFactorTable.keys())[0]
    service_conditions = list(TimberTables.ServiceConditionFactorTable.keys())[0]
    parameters = TimberDesignParameters(data["Beam Id"], data["Length"], end_conditions, service_conditions, data["Lu"], data["Wf"], data["Sum G"])

    beam_design = TimberBeamDesign(section, loading, parameters)
    beam_design.checkAll()
    
    end = time.time()
    
    print("\nRuntime", end-start)
    #print(beam_design.strongAxisPosBendingCheck.results.head()) #table of all the results
    logs = beam_design.status_log.loc[:, beam_design.status_log.columns != 'beam_id']
    print(logs.head())
    worst_status = beam_design.strongAxisShearCheck.status_log.max(1)
 
    #print([status_desc[status] for status in worst_status.unique()]) # table of (error,status,util) combos
    #print(worst_status.value_counts())

    #print(beam_design.strongAxisShearCheck.utilizations[30:40])

    #print(beam_design.strongAxisPosBendingCheck.displayLatex(30).data) # full latex str with checks and util
    #print(beam_design.strongAxisPosBendingCheck.displayLatex(0).data)

