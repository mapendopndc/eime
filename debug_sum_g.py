"""Check Sum_G calculation in the real example."""
import numpy as np
from pint import UnitRegistry
from Pynite.FEModel3D import FEModel3D
from preprocessor import Beam, BeamMesh
from preprocessor.pynite_csa_mapper import map_pynite_to_stations

# Initialize
ureg = UnitRegistry()
mm = ureg.mm
m = ureg.m
kN = ureg.kN
MPa = ureg.MPa

# Create beam
beam = Beam(
    support_locations=[0, 6, 12],
    bracing_locations=[0, 2, 4, 6, 8, 10, 12]
)

mesh = BeamMesh(beam, spacing=0.3, refine_at_discontinuities=True)

# Create PyNite model
model = FEModel3D()

E_val = 11700  # MPa
G_val = E_val * 0.4
I_val = 175 * 456**3 / 12 / 1e12  # Convert mm^4 to m^4
A_val = 175 * 456 / 1e6  # Convert mm^2 to m^2

model.add_material('Glulam', E_val, G_val, 0.6, 500)
model.add_section('Rect', A_val, I_val, I_val/2, I_val/2)

model.add_node('N1', 0, 0, 0)
model.add_node('N2', 6, 0, 0)
model.add_node('N3', 12, 0, 0)

model.add_member('M1', 'N1', 'N2', 'Glulam', 'Rect')
model.add_member('M2', 'N2', 'N3', 'Glulam', 'Rect')

model.def_support('N1', True, True, True, True, False, False)
model.def_support('N2', False, True, True, True, False, False)
model.def_support('N3', False, True, True, True, False, False)

# Apply loads
w_dead = 6.0
w_live = 4.0
w_snow = 5.0

for member_name in ['M1', 'M2']:
    member_length = model.members[member_name].L()
    model.add_member_dist_load(member_name, 'Fy', -w_dead, -w_dead, 0, member_length, 'D')
    model.add_member_dist_load(member_name, 'Fy', -w_live, -w_live, 0, member_length, 'L')
    if member_name == 'M1':
        model.add_member_dist_load(member_name, 'Fy', -w_snow, -w_snow, 0, member_length, 'S')

model.add_load_combo('ULS', {'D': 1.25, 'L': 1.5, 'S': 0.5})
model.analyze(check_statics=False)

# Extract demands
demands = map_pynite_to_stations(
    model=model,
    member_name='M1',
    x_stations=mesh.x_stations[mesh.x_stations <= 6.0],
    load_combo='ULS',
    load_cases=['D', 'L', 'S'],
    beam_length=6.0,
    ureg=ureg
)

print("Sum_G values:")
print(f"  Shape: {demands['Sum_G'].shape}")
print(f"  Min: {np.min(demands['Sum_G'])}")
print(f"  Max: {np.max(demands['Sum_G'])}")
print(f"  Has zeros: {np.any(demands['Sum_G'] == 0)}")
print(f"  Has NaN: {np.any(np.isnan(demands['Sum_G']))}")
print(f"  Has inf: {np.any(np.isinf(demands['Sum_G']))}")
print(f"  Unique values: {np.unique(demands['Sum_G'])[:5]}")

print("\nW_f values:")
print(f"  Shape: {demands['W_f'].shape}")
print(f"  Min: {np.min(demands['W_f'])}")
print(f"  Max: {np.max(demands['W_f'])}")
