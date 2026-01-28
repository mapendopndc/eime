"""Debug span length calculations."""
import numpy as np
from preprocessor import Beam, BeamMesh
from preprocessor.parameters import GeometryMapper

# Create beam and mesh
beam = Beam(
    support_locations=[0, 6, 12],
    bracing_locations=[0, 2, 4, 6, 8, 10, 12]
)

mesh = BeamMesh(beam, spacing=0.3, refine_at_discontinuities=True)

# Map parameters
mapper = GeometryMapper(beam, mesh)
params = mapper.map()

print(f"Number of stations: {len(mesh.x_stations)}")
print(f"Span lengths shape: {params['span_lengths'].shape}")
print(f"Unique span lengths: {np.unique(params['span_lengths'])}")
print(f"Zero span lengths: {np.sum(params['span_lengths'] == 0)}")
print(f"\nFirst 10 stations:")
for i in range(min(10, len(mesh.x_stations))):
    x = mesh.x_stations[i]
    span_len = params['span_lengths'][i]
    span_idx = beam.get_span_at(x)
    print(f"  x={x:.3f}m -> span_idx={span_idx}, span_length={span_len:.3f}m")
