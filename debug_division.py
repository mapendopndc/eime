"""Trace through the bending resistance calculation to find division by zero."""
import numpy as np
from pint import UnitRegistry
import warnings

# Capture warnings
warnings.filterwarnings('error')

from preprocessor import Beam, BeamMesh, GeometryMapper, AnalysisMapper, LoadDurationMapper, ParameterAssembler
from Pynite.FEModel3D import FEModel3D
from design.csa_o86_2025.calculators.timber_member import (
    RectangularProfile, TimberMaterial, TimberSection,
    TimberDesignParameters, TimberLoads, TimberLoadingParameters, TimberBeamDesign
)

# Initialize unit registry
ureg = UnitRegistry()
mm = ureg.mm
m = ureg.m
kN = ureg.kN
MPa = ureg.MPa
nd = ureg.dimensionless

# Create beam
beam = Beam(
    support_locations=[0, 6, 12],
    bracing_locations=[0, 2, 4, 6, 8, 10, 12]
)

mesh = BeamMesh(beam, spacing=0.3, refine_at_discontinuities=True)

# Create section
profile = RectangularProfile(b=175*mm, d=456*mm)
material = TimberMaterial(grade="20f-E", species="Douglas Fir-Larch", ureg=ureg)
section = TimberSection(profile=profile, material=material)

# Simple mock parameters for testing
geom_params = GeometryMapper(beam, mesh).map()

# Mock analysis params
analysis_params = {
    'M_f': np.full(mesh.num_stations, 50.0),  # 50 kN·m
    'V_f': np.full(mesh.num_stations, 30.0),  # 30 kN
    'P_f': np.full(mesh.num_stations, 5.0),   # 5 kN
    'W_f': np.full(mesh.num_stations, 90.0),  # 90 kN
    'Sum_G': np.full(mesh.num_stations, 1e10), # Large value
}

duration_params = {
    'P_L_M': np.full(mesh.num_stations, 0.6),
    'P_S_M': np.full(mesh.num_stations, 0.4),
    'P_L_V': np.full(mesh.num_stations, 0.6),
    'P_S_V': np.full(mesh.num_stations, 0.4),
    'P_L_P': np.full(mesh.num_stations, 0.6),
    'P_S_P': np.full(mesh.num_stations, 0.4),
}

assembler = ParameterAssembler(
    beam, mesh,
    geom_params, analysis_params, duration_params,
    ureg=ureg,
    beam_id_prefix='CB'
)
params = assembler.assemble()

# Create design parameters
design_params = TimberDesignParameters(
    beam_ids=params['beam_ids'],
    beam_length=geom_params['span_lengths'] * m,
    end_conditions="Pin - Pin",
    service_conditions="Dry-service conditions",
    lu_strong=geom_params['lu_strong'] * m,
    lu_weak=geom_params['lu_weak'] * m,
    Wf=analysis_params['W_f'] * kN,
    SumG=analysis_params['Sum_G'] * kN**5 * mm,
    ureg=ureg
)

# Create loads
loads = TimberLoads()
loads.M3 = analysis_params['M_f'] * kN * m
loads.V2 = analysis_params['V_f'] * kN
loads.P = analysis_params['P_f'] * kN

# Create loading parameters
loading_params = TimberLoadingParameters(
    P_L_M=duration_params['P_L_M'] * nd,
    P_S_M=duration_params['P_S_M'] * nd,
    P_L_V=duration_params['P_L_V'] * nd,
    P_S_V=duration_params['P_S_V'] * nd,
    P_L_P=duration_params['P_L_P'] * nd,
    P_S_P=duration_params['P_S_P'] * nd,
    load_combo_types=['includes_live' for _ in range(mesh.num_stations)],
    ureg=ureg
)

print("Creating TimberBeamDesign...")
design = TimberBeamDesign(
    section=section,
    loading=loads,
    parameters=design_params,
    loading_params=loading_params
)

print("Running bending resistance...")
try:
    bending_proc = design.BendingResistance(axis='strong', sign='pos')
    print("SUCCESS!")
except Warning as w:
    print(f"WARNING: {w}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
