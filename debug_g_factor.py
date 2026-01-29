"""Debug g_factor calculation."""
import numpy as np
from pint import UnitRegistry
from Pynite.FEModel3D import FEModel3D
from design.csa_o86_2025.shear_segments import prepare_shear_segment_arrays, compute_sum_g
from design.csa_o86_2025.formulas.glulam_shear import g_factor

# Initialize
ureg = UnitRegistry()

# Create simple PyNite model
model = FEModel3D()

E_val = 11700
G_val = E_val * 0.4
I_val = 175 * 456**3 / 12 / 1e12
A_val = 175 * 456 / 1e6

model.add_material('Glulam', E_val, G_val, 0.6, 500)
model.add_section('Rect', A_val, I_val, I_val/2, I_val/2)

model.add_node('N1', 0, 0, 0)
model.add_node('N2', 6, 0, 0)

model.add_member('M1', 'N1', 'N2', 'Glulam', 'Rect')

model.def_support('N1', True, True, True, True, False, False)
model.def_support('N2', False, True, True, True, False, False)

# Apply loads
model.add_member_dist_load('M1', 'Fy', -6.0, -6.0, 0, 6, 'D')
model.add_member_dist_load('M1', 'Fy', -4.0, -4.0, 0, 6, 'L')
model.add_member_dist_load('M1', 'Fy', -5.0, -5.0, 0, 6, 'S')

model.add_load_combo('ULS', {'D': 1.25, 'L': 1.5, 'S': 0.5})
model.analyze(check_statics=False)

print("Preparing shear segment data...")
segment_data = prepare_shear_segment_arrays(
    model=model,
    member_name='M1',
    load_combo='ULS',
    beam_length=6.0 * ureg.m,
    num_points=100,
    ureg=ureg
)

print(f"\nSegment data:")
print(f"  Number of segments: {len(segment_data['l_a'])}")
print(f"  W_f: {segment_data['W_f']}")
print(f"  L: {segment_data['L']}")

for i, (la, va, vb, vc) in enumerate(zip(
    segment_data['l_a'][:5], 
    segment_data['V_A'][:5], 
    segment_data['V_B'][:5], 
    segment_data['V_C'][:5]
)):
    print(f"\n  Segment {i}:")
    print(f"    l_a: {la}")
    print(f"    V_A: {va}")
    print(f"    V_B: {vb}")
    print(f"    V_C: {vc}")

print("\nComputing Sum_G...")
try:
    Sum_G = compute_sum_g(segment_data, g_factor)
    print(f"Sum_G: {Sum_G}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
