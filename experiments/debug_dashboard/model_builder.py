"""
Model Builder for EIME Beam Analysis

Provides configurable beam model creation with flexible geometry, materials, and loading.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from pint import UnitRegistry
from Pynite.FEModel3D import FEModel3D
import numpy as np

from preprocessor import Beam, BeamMesh
from design.csa_o86_2025.calculators.timber_member import (
    RectangularProfile, TimberMaterial, TimberSection
)


@dataclass
class BeamConfig:
    """Configuration for beam geometry."""
    support_locations: List[float] = field(default_factory=lambda: [0, 4, 8])
    bracing_locations: List[float] = field(default_factory=lambda: [0, 2, 4, 6, 8])
    mesh_spacing: float = 0.2
    refine_at_discontinuities: bool = True


@dataclass
class SectionConfig:
    """Configuration for beam section properties."""
    width_mm: float = 175.0
    depth_mm: float = 456.0
    grade: str = "20f-E"
    species: str = "Douglas Fir-Larch"


@dataclass
class LoadConfig:
    """Configuration for applied loads."""
    # Distributed loads in kN/m
    dead_load: float = 6.0
    live_load: float = 4.0
    snow_load: float = 5.0
    
    # Point loads (list of tuples: (magnitude_kN, position_m, load_case))
    point_loads: List[Tuple[float, float, str]] = field(default_factory=list)
    
    # Load application ranges (for partial loading)
    # Format: {load_case: [(start, end), ...]}
    load_ranges: Dict[str, List[Tuple[float, float]]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set default load ranges if not provided."""
        if not self.load_ranges:
            # Default: apply all loads to entire beam
            # Will be determined based on beam length during model creation
            pass


@dataclass
class LoadCombinationConfig:
    """Configuration for load combinations."""
    # Dictionary of load combinations: {name: {load_case: factor, ...}}
    combinations: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set default load combinations if not provided."""
        if not self.combinations:
            self.combinations = {
                # Individual load cases (unfactored)
                'D': {'D': 1.0},
                'L': {'L': 1.0},
                'S': {'S': 1.0},
                # Factored combinations
                '1.4D': {'D': 1.4},
                '1.25D+1.5L': {'D': 1.25, 'L': 1.5},
                '1.25D+1.5S': {'D': 1.25, 'S': 1.5},
                '1.25D+1.5L+0.5S': {'D': 1.25, 'L': 1.5, 'S': 0.5},
                '1.25D+0.5L+1.5S': {'D': 1.25, 'L': 0.5, 'S': 1.5},
            }


@dataclass
class ModelConfig:
    """Complete model configuration."""
    beam: BeamConfig = field(default_factory=BeamConfig)
    section: SectionConfig = field(default_factory=SectionConfig)
    loads: LoadConfig = field(default_factory=LoadConfig)
    load_combinations: LoadCombinationConfig = field(default_factory=LoadCombinationConfig)


class ModelBuilder:
    """
    Builds PyNite FEM models from configuration.
    
    This class takes configuration objects and creates a complete beam model
    with geometry, materials, sections, loads, and load combinations.
    """
    
    def __init__(self, config: ModelConfig, ureg: UnitRegistry):
        """
        Initialize model builder.
        
        Parameters
        ----------
        config : ModelConfig
            Model configuration
        ureg : UnitRegistry
            Pint unit registry for unit handling
        """
        self.config = config
        self.ureg = ureg
        
        # Unit shortcuts
        self.mm = ureg.mm
        self.m = ureg.m
        self.kN = ureg.kN
        self.MPa = ureg.MPa
    
    def build(self) -> Dict:
        """
        Build complete beam model from configuration.
        
        Returns
        -------
        dict
            Dictionary containing:
            - 'beam': Beam object
            - 'mesh': BeamMesh object
            - 'section': TimberSection object
            - 'material': TimberMaterial object
            - 'model': FEModel3D object (analyzed)
            - 'load_combos': Dictionary of load combinations
            - 'loads': LoadConfig object
            - 'config': ModelConfig object
        """
        # Create beam geometry
        beam = Beam(
            support_locations=self.config.beam.support_locations,
            bracing_locations=self.config.beam.bracing_locations
        )
        
        # Generate mesh
        mesh = BeamMesh(
            beam,
            spacing=self.config.beam.mesh_spacing,
            refine_at_discontinuities=self.config.beam.refine_at_discontinuities
        )
        
        # Create section and material
        profile = RectangularProfile(
            b=self.config.section.width_mm * self.mm,
            d=self.config.section.depth_mm * self.mm
        )
        material = TimberMaterial(
            grade=self.config.section.grade,
            species=self.config.section.species,
            ureg=self.ureg
        )
        section = TimberSection(profile=profile, material=material)
        
        # Create PyNite FEM model
        model = self._create_pynite_model(beam, section, material)
        
        # Apply loads
        self._apply_loads(model, beam)
        
        # Define load combinations
        for combo_name, factors in self.config.load_combinations.combinations.items():
            model.add_load_combo(combo_name, factors)
        
        # Analyze model
        model.analyze(check_statics=False)
        
        return {
            'beam': beam,
            'mesh': mesh,
            'section': section,
            'material': material,
            'model': model,
            'load_combos': self.config.load_combinations.combinations,
            'loads': self.config.loads,
            'config': self.config
        }
    
    def _create_pynite_model(self, beam: Beam, section: TimberSection, material: TimberMaterial) -> FEModel3D:
        """Create PyNite FEM model with nodes, members, and supports."""
        model = FEModel3D()
        
        # Material properties
        E_val = material.E.to(self.MPa).magnitude
        G_val = E_val * 0.4
        
        # Section properties
        I_val = section.profile.MomentofInertia().to(self.mm**4).magnitude / 1e12  # m^4
        A_val = section.profile.Area().to(self.mm**2).magnitude / 1e6  # m^2
        
        model.add_material('Glulam', E_val, G_val, 0.6, 500)
        model.add_section('Rect', A_val, I_val, I_val/2, I_val/2)
        
        # Add nodes at support locations
        support_locs = self.config.beam.support_locations
        for i, x in enumerate(support_locs):
            model.add_node(f'N{i+1}', x, 0, 0)
        
        # Add members between consecutive supports
        for i in range(len(support_locs) - 1):
            model.add_member(f'M{i+1}', f'N{i+1}', f'N{i+2}', 'Glulam', 'Rect')
        
        # Add supports
        # First support is pin, rest are rollers
        for i, x in enumerate(support_locs):
            if i == 0:
                # Pin support (restrain X and Y)
                model.def_support(f'N{i+1}', True, True, True, True, False, False)
            else:
                # Roller support (restrain Y only)
                model.def_support(f'N{i+1}', False, True, True, True, False, False)
        
        return model
    
    def _apply_loads(self, model: FEModel3D, beam: Beam):
        """Apply loads to the model."""
        # Determine beam spans
        support_locs = self.config.beam.support_locations
        beam_spans = []
        for i in range(len(support_locs) - 1):
            span_start = support_locs[i]
            span_end = support_locs[i + 1]
            beam_spans.append((span_start, span_end, f'M{i+1}'))
        
        # Set default load ranges if not specified
        if not self.config.loads.load_ranges:
            total_length = support_locs[-1] - support_locs[0]
            self.config.loads.load_ranges = {
                'D': [(support_locs[0], support_locs[-1])],
                'L': [(support_locs[0], support_locs[-1])],
                'S': [(support_locs[0], support_locs[-1])]
            }
        
        # Apply distributed loads
        load_mapping = {
            'D': self.config.loads.dead_load,
            'L': self.config.loads.live_load,
            'S': self.config.loads.snow_load
        }
        
        for load_case, magnitude in load_mapping.items():
            if magnitude == 0:
                continue
            
            # Get ranges for this load case
            ranges = self.config.loads.load_ranges.get(load_case, [])
            
            for start_pos, end_pos in ranges:
                # Find which member(s) this load applies to
                for span_start, span_end, member_name in beam_spans:
                    # Check if load range overlaps with this member
                    if end_pos > span_start and start_pos < span_end:
                        # Calculate load start/end relative to member
                        load_start = max(0, start_pos - span_start)
                        load_end = min(span_end - span_start, end_pos - span_start)
                        
                        # Apply load to this member segment
                        model.add_member_dist_load(
                            member_name,
                            'Fy',
                            -magnitude,  # Negative for downward
                            -magnitude,
                            load_start,
                            load_end,
                            load_case
                        )
        
        # Apply point loads
        for P_magnitude, P_position, load_case in self.config.loads.point_loads:
            # Find which member this point load applies to
            for span_start, span_end, member_name in beam_spans:
                if span_start <= P_position <= span_end:
                    # Position relative to member start
                    local_pos = P_position - span_start
                    model.add_member_pt_load(
                        member_name,
                        'Fy',
                        -P_magnitude,  # Negative for downward
                        local_pos,
                        load_case
                    )
                    break


def create_default_model(ureg: UnitRegistry) -> Dict:
    """
    Create a default beam model with standard configuration.
    
    Parameters
    ----------
    ureg : UnitRegistry
        Pint unit registry
    
    Returns
    -------
    dict
        Model data dictionary from ModelBuilder.build()
    """
    # Create default configuration with custom loading
    config = ModelConfig()
    
    # Set up partial loading: Snow on first span, Live on second span
    support_locs = config.beam.support_locations
    first_span_end = support_locs[1]
    last_support = support_locs[-1]
    
    config.loads.load_ranges = {
        'D': [(support_locs[0], last_support)],  # Dead load on entire beam
        'S': [(support_locs[0], first_span_end)],  # Snow on first span only
        'L': [(first_span_end, last_support)]  # Live on second span only
    }
    
    # Add point load on first span
    config.loads.point_loads = [
        (20.0, first_span_end / 3, 'L')  # 20 kN at 1/3 of first span
    ]
    
    # Build and return model
    builder = ModelBuilder(config, ureg)
    return builder.build()
