"""Quick test of refactored dashboard components."""

from pint import UnitRegistry
from model_builder import create_default_model, ModelBuilder, ModelConfig, BeamConfig, SectionConfig
from visualization import get_diagram_data

# Initialize unit registry
ureg = UnitRegistry()

print("Testing model builder...")

# Test 1: Default model
model_data = create_default_model(ureg)
print(f"✓ Default model created successfully!")
print(f"  Supports: {model_data['config'].beam.support_locations}")
print(f"  Section: {model_data['config'].section.width_mm} x {model_data['config'].section.depth_mm} mm")
print(f"  Load combos: {len(model_data['load_combos'])}")
print(f"  Members: {list(model_data['model'].members.keys())}")

# Test 2: Custom configuration
print("\nTesting custom configuration...")
config = ModelConfig(
    beam=BeamConfig(
        support_locations=[0, 3, 6],
        bracing_locations=[0, 1.5, 3, 4.5, 6],
        mesh_spacing=0.25
    ),
    section=SectionConfig(
        width_mm=200.0,
        depth_mm=500.0,
        grade="24f-E",
        species="Douglas Fir-Larch"
    )
)

builder = ModelBuilder(config, ureg)
custom_data = builder.build()
print(f"✓ Custom model created successfully!")
print(f"  Supports: {custom_data['config'].beam.support_locations}")
print(f"  Members: {list(custom_data['model'].members.keys())}")
print(f"  Stations: {len(custom_data['mesh'].x_stations)}")

# Test 3: Visualization
print("\nTesting visualization...")
x_data, y_data = get_diagram_data(
    model_data['model'],
    'M1',
    '1.25D+1.5L',
    'moment',
    model_data['load_combos']
)
print(f"✓ Diagram data extracted successfully!")
print(f"  Points: {len(x_data)}")
print(f"  Max moment: {max(abs(y_data)):.2f} kN·m")

print("\n✅ All tests passed!")
