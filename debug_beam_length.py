"""Debug beam_length parameter."""
import numpy as np
from pint import UnitRegistry
from preprocessor import Beam, BeamMesh
from preprocessor.parameters import GeometryMapper

# Initialize unit registry
ureg = UnitRegistry()
mm = ureg.mm
m = ureg.m

# Create beam and mesh
beam = Beam(
    support_locations=[0, 6, 12],
    bracing_locations=[0, 2, 4, 6, 8, 10, 12]
)

mesh = BeamMesh(beam, spacing=0.3, refine_at_discontinuities=True)

# Map parameters
mapper = GeometryMapper(beam, mesh)
geom_params = mapper.map()

# Apply units
beam_length = geom_params['span_lengths'] * m

print(f"beam_length shape: {beam_length.shape}")
print(f"beam_length values: {beam_length}")
print(f"Has zeros: {np.any(beam_length.magnitude == 0)}")
print(f"Has NaN: {np.any(np.isnan(beam_length.magnitude))}")
print(f"Has inf: {np.any(np.isinf(beam_length.magnitude))}")
print(f"\nConverted to mm:")
beam_length_mm = beam_length.to(mm)
print(f"beam_length_mm: {beam_length_mm[:5]}")

# Test division
print(f"\nTesting division:")
try:
    test = 9100*mm / beam_length_mm
    print(f"9100/L: {test[:5]}")
except Exception as e:
    print(f"Error: {e}")
