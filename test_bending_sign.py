"""
Test that the correct bending strength (f_b_pos or f_b_neg) is selected
based on the sign of the bending moment.
"""

import numpy as np
from pint import UnitRegistry

from design.csa_o86_2025.calculators.timber_member import (
    RectangularProfile, TimberMaterial, TimberSection,
    TimberDesignParameters, TimberLoads, TimberLoadingParameters,
    TimberBeamDesign
)

# Initialize units
ureg = UnitRegistry()
mm = ureg.mm
m = ureg.m
kN = ureg.kN
MPa = ureg.MPa
nd = ureg.dimensionless

print("="*70)
print("TESTING BENDING STRENGTH SELECTION BASED ON MOMENT SIGN")
print("="*70)

# Create material with different f_b_pos and f_b_neg
# Douglas Fir-Larch 24f-E has f_b_pos=30.6 MPa and f_b_neg=23.0 MPa
species = "Douglas Fir-Larch"
grade = "24f-E"

material = TimberMaterial(grade=grade, species=species, ureg=ureg)

print(f"\nMaterial: {grade} {species}")
print(f"  f_b_pos = {material.f_b_pos.to(MPa).magnitude:.1f} MPa")
print(f"  f_b_neg = {material.f_b_neg.to(MPa).magnitude:.1f} MPa")
print(f"  Difference = {(material.f_b_pos - material.f_b_neg).to(MPa).magnitude:.1f} MPa")

# Create section
profile = RectangularProfile(b=175*mm, d=456*mm)
section = TimberSection(profile=profile, material=material)

# Create design parameters for 3 stations
num_stations = 3
beam_ids = [f"TEST-{i+1}" for i in range(num_stations)]

parameters = TimberDesignParameters(
    beam_ids=beam_ids,
    beam_length=np.array([8.0, 8.0, 8.0]) * m,
    end_conditions="Pin - Pin",
    service_conditions="Dry-service conditions",
    lu_strong=np.array([8.0, 8.0, 8.0]) * m,
    lu_weak=np.array([2.0, 2.0, 2.0]) * m,
    L_zbg=np.array([8000.0, 8000.0, 8000.0]) * mm,
    ureg=ureg
)

# Create loads with positive, zero, and negative moments
loads = TimberLoads()
loads.M3 = np.array([100.0, 0.0, -80.0]) * kN * m  # Positive, zero, negative
loads.V2 = np.array([50.0, 50.0, 50.0]) * kN
loads.P = np.array([0.0, 0.0, 0.0]) * kN

print(f"\nTest Moments:")
print(f"  Station 1: M = {loads.M3[0].to(kN*m).magnitude:+.1f} kN·m (POSITIVE - should use f_b_neg)")
print(f"  Station 2: M = {loads.M3[1].to(kN*m).magnitude:+.1f} kN·m (ZERO - should use f_b_neg)")
print(f"  Station 3: M = {loads.M3[2].to(kN*m).magnitude:+.1f} kN·m (NEGATIVE - should use f_b_pos)")

# Create loading parameters (simplified - all dead load)
loading_params = TimberLoadingParameters(
    P_L_M=np.array([0.0, 0.0, 0.0]) * nd,
    P_S_M=np.array([1.0, 1.0, 1.0]) * nd,
    P_L_V=np.array([0.0, 0.0, 0.0]) * nd,
    P_S_V=np.array([1.0, 1.0, 1.0]) * nd,
    P_L_P=np.array([0.0, 0.0, 0.0]) * nd,
    P_S_P=np.array([1.0, 1.0, 1.0]) * nd,
    load_combo_types=['dead_only'] * num_stations,
    ureg=ureg
)

# Run bending resistance calculation
design = TimberBeamDesign(
    section=section,
    loading=loads,
    parameters=parameters,
    loading_params=loading_params
)

print("\n" + "="*70)
print("RUNNING BENDING RESISTANCE CALCULATION")
print("="*70)

bending_proc = design.BendingResistance(axis='strong', sign='pos')

# Extract F_b values from the procedure
print("\nResults from BendingResistance procedure:")

# Get the Fb calculation result
Fb_result = bending_proc.results.get('F_b')
if Fb_result is not None:
    print(f"\nModified Bending Strength (F_b) at each station:")
    for i in range(num_stations):
        if hasattr(Fb_result, '__getitem__'):
            fb_value = Fb_result[i].to(MPa).magnitude
        else:
            fb_value = Fb_result.to(MPa).magnitude
        
        moment = loads.M3[i].to(kN*m).magnitude
        expected_fb_base = material.f_b_neg.magnitude if moment >= 0 else material.f_b_pos.magnitude
        
        print(f"  Station {i+1}: F_b = {fb_value:.2f} MPa (M = {moment:+.1f} kN·m)")
        print(f"             Expected f_b base = {expected_fb_base:.1f} MPa")

# Get moment resistance
Mr_result = bending_proc.results.get('M_r')
if Mr_result is not None:
    print(f"\nMoment Resistance (M_r) at each station:")
    for i in range(num_stations):
        if hasattr(Mr_result, '__getitem__'):
            mr_value = Mr_result[i].to(kN*m).magnitude
        else:
            mr_value = Mr_result.to(kN*m).magnitude
        
        moment = loads.M3[i].to(kN*m).magnitude
        print(f"  Station {i+1}: M_r = {mr_value:.2f} kN·m (M_f = {moment:+.1f} kN·m)")

print("\n" + "="*70)
print("TEST VALIDATION")
print("="*70)

# Verify the correct f_b was selected
# For station 1 (positive moment): should use f_b_pos (30.6 MPa)
# For station 3 (negative moment): should use f_b_neg (23.0 MPa)

if Fb_result is not None and hasattr(Fb_result, '__getitem__'):
    # Extract base f_b by dividing out K_D and other factors
    # F_b = f_b * K_D * K_H * K_Sb * K_T
    # For this test: K_H=1.0, K_Sb=1.0, K_T=1.0, K_D varies
    
    # Get K_D from procedure
    KD_result = bending_proc.results.get('K_D')
    if KD_result is not None:
        print("\nVerification (extracting base f_b from F_b):")
        for i in range(num_stations):
            fb_modified = Fb_result[i].to(MPa).magnitude
            kd = KD_result[i].magnitude if hasattr(KD_result, '__getitem__') else KD_result.magnitude
            
            # Back-calculate base f_b
            # F_b = f_b * K_D (since K_H=K_Sb=K_T=1.0)
            fb_base_calculated = fb_modified / kd
            
            moment = loads.M3[i].to(kN*m).magnitude
            fb_expected = material.f_b_neg.magnitude if moment >= 0 else material.f_b_pos.magnitude
            
            match = abs(fb_base_calculated - fb_expected) < 0.1
            status = "✓ PASS" if match else "✗ FAIL"
            
            print(f"  Station {i+1} (M={moment:+.1f}): f_b = {fb_base_calculated:.2f} MPa, " +
                  f"expected {fb_expected:.1f} MPa {status}")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
