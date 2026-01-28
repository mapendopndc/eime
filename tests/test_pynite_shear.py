"""
Unit tests for PyNite shear preprocessor utilities.

Tests the extraction and segmentation of shear diagrams for CV calculation
per CSA O86 7.5.7.6.
"""

import pytest
import numpy as np
from preprocessor.pynite_shear import (
    identify_shear_segments,
    prepare_shear_segment_arrays,
    compute_sum_g
)

try:
    from Pynite.FEModel3D import FEModel3D
    PYNITE_AVAILABLE = True
except ImportError:
    PYNITE_AVAILABLE = False


class TestIdentifyShearSegments:
    """Tests for the identify_shear_segments function."""
    
    def test_uniform_load_single_segment(self):
        """Test that uniform load creates a single segment."""
        # Simply supported beam with uniform load has linear shear diagram
        positions = np.linspace(0, 8, 100)
        # Linear shear: V = V_max - w*x (constant slope)
        shear_values = 40 - 10 * positions  # kN
        shear_values = np.abs(shear_values)  # Absolute values
        
        segments = identify_shear_segments(positions, shear_values)
        
        # Should identify as single segment (uniform slope)
        assert len(segments) >= 1
        assert segments[0]['start_pos'] == pytest.approx(0.0)
        assert segments[-1]['end_pos'] == pytest.approx(8.0)
    
    def test_point_load_discontinuity(self):
        """Test that point load creates discontinuity."""
        positions = np.array([0, 2, 2, 4, 6, 8])
        # Shear with jump at x=2 (point load)
        shear_values = np.array([40, 30, 10, 0, 0, 0])
        
        segments = identify_shear_segments(positions, shear_values, tolerance=1e-6)
        
        # Should identify the discontinuity
        assert len(segments) >= 1
    
    def test_zero_length_arrays(self):
        """Test error handling for invalid inputs."""
        with pytest.raises(ValueError):
            identify_shear_segments(np.array([]), np.array([]))
    
    def test_mismatched_arrays(self):
        """Test error handling for mismatched array lengths."""
        positions = np.array([0, 1, 2])
        shear_values = np.array([10, 5])
        
        with pytest.raises(ValueError):
            identify_shear_segments(positions, shear_values)


@pytest.mark.skipif(not PYNITE_AVAILABLE, reason="PyNite not installed")
class TestPyNiteIntegration:
    """Integration tests with PyNite FEM model."""
    
    def create_simple_beam(self, span=8.0, w=10.0):
        """
        Create a simple beam with uniform load for testing.
        
        Parameters
        ----------
        span : float
            Beam span in meters
        w : float
            Uniform load in kN/m
            
        Returns
        -------
        FEModel3D
            Analyzed PyNite model
        """
        model = FEModel3D()
        
        # Material and section
        E = 12000  # MPa
        G = E * 0.4
        model.add_material('Wood', E, G, 0.3, 500)
        
        # Rectangular section: 175mm x 456mm
        b, d = 0.175, 0.456  # m
        A = b * d
        I = b * d**3 / 12
        model.add_section('Rect', A, I, I/2, I/2)
        
        # Nodes and member
        model.add_node('N1', 0, 0, 0)
        model.add_node('N2', span, 0, 0)
        model.add_member('M1', 'N1', 'N2', 'Wood', 'Rect')
        
        # Supports
        model.def_support('N1', True, True, True, False, False, False)
        model.def_support('N2', False, True, True, True, False, False)
        
        # Load
        model.add_load_combo('ULS', {'ULS': 1.0})
        model.add_member_dist_load('M1', 'Fy', -w, -w, 0, span, 'ULS')
        
        # Analyze
        model.analyze(check_statics=False)
        
        return model
    
    def test_prepare_shear_segment_arrays_simple_beam(self):
        """Test preprocessor with simple uniform load case."""
        from eime.units import ureg
        from design.csa_o86_2025.formulas.glulam_shear import g_factor
        
        # Create test model
        span = 8.0  # m
        w = 10.0    # kN/m
        model = self.create_simple_beam(span, w)
        
        # Prepare segment arrays
        segment_data = prepare_shear_segment_arrays(
            model=model,
            member_name='M1',
            load_combo='ULS',
            beam_length=span * ureg.m,
            num_points=50,
            ureg=ureg
        )
        
        # Verify output structure
        assert 'l_a' in segment_data
        assert 'V_A' in segment_data
        assert 'V_B' in segment_data
        assert 'V_C' in segment_data
        assert 'W_f' in segment_data
        assert 'L' in segment_data
        
        # Verify at least one segment
        assert len(segment_data['l_a']) >= 1
        
        # Verify units (should be Pint quantities)
        assert hasattr(segment_data['L'], 'units')
        assert hasattr(segment_data['W_f'], 'units')
        
        # Verify total load is approximately correct
        # For uniform load: W_f = w * L
        expected_Wf = w * span  # kN
        actual_Wf = segment_data['W_f'].to(ureg.kN).magnitude
        # Allow some error due to numerical integration
        assert actual_Wf == pytest.approx(expected_Wf, rel=0.15)
    
    def test_compute_sum_g_simple_beam(self):
        """Test Sum_G calculation with g_factor formula."""
        from eime.units import ureg
        from design.csa_o86_2025.formulas.glulam_shear import g_factor
        
        # Create test model
        span = 8.0
        w = 10.0
        model = self.create_simple_beam(span, w)
        
        # Prepare segment arrays
        segment_data = prepare_shear_segment_arrays(
            model=model,
            member_name='M1',
            load_combo='ULS',
            beam_length=span * ureg.m,
            num_points=50,
            ureg=ureg
        )
        
        # Compute Sum_G
        Sum_G = compute_sum_g(segment_data, g_factor)
        
        # Verify it's a quantity with correct units
        assert hasattr(Sum_G, 'units')
        
        # Verify it's positive and non-zero
        assert Sum_G.magnitude > 0
        
        # Verify units are N^5 * mm
        expected_units = ureg.N**5 * ureg.mm
        assert Sum_G.dimensionality == expected_units.dimensionality
    
    def test_point_load_segmentation(self):
        """Test that point loads create proper segments."""
        from eime.units import ureg
        
        # Create model with point load
        model = FEModel3D()
        
        span = 6.0
        E = 12000
        G = E * 0.4
        model.add_material('Wood', E, G, 0.3, 500)
        
        b, d = 0.175, 0.456
        A = b * d
        I = b * d**3 / 12
        model.add_section('Rect', A, I, I/2, I/2)
        
        model.add_node('N1', 0, 0, 0)
        model.add_node('N2', span, 0, 0)
        model.add_member('M1', 'N1', 'N2', 'Wood', 'Rect')
        
        model.def_support('N1', True, True, True, False, False, False)
        model.def_support('N2', False, True, True, True, False, False)
        
        # Add point load at midspan
        model.add_load_combo('ULS', {'ULS': 1.0})
        model.add_member_pt_load('M1', 'Fy', -50, span/2, 'ULS')
        
        model.analyze(check_statics=False)
        
        # Prepare segments
        segment_data = prepare_shear_segment_arrays(
            model=model,
            member_name='M1',
            load_combo='ULS',
            beam_length=span * ureg.m,
            num_points=100,
            ureg=ureg
        )
        
        # Point load should create segments
        # (though exact number depends on discretization)
        assert len(segment_data['l_a']) >= 1


class TestComputeSumG:
    """Tests for the compute_sum_g helper function."""
    
    def test_compute_sum_g_with_mock_data(self):
        """Test Sum_G calculation with mock segment data."""
        from eime.units import ureg
        from design.csa_o86_2025.formulas.glulam_shear import g_factor
        
        # Create mock segment data with proper scalar values (not arrays)
        segment_data = {
            'l_a': [4000.0 * ureg.mm, 4000.0 * ureg.mm],
            'V_A': [40000.0 * ureg.N, 20000.0 * ureg.N],
            'V_B': [20000.0 * ureg.N, 0.1 * ureg.N],  # Avoid exact zero
            'V_C': [30000.0 * ureg.N, 10000.0 * ureg.N],
            'W_f': 80000.0 * ureg.N,
            'L': 8000.0 * ureg.mm
        }
        
        # Compute Sum_G
        Sum_G = compute_sum_g(segment_data, g_factor)
        
        # Verify result
        assert hasattr(Sum_G, 'units')
        assert Sum_G.magnitude > 0
        
        # Manually verify for first segment
        G1 = g_factor(
            l_a=segment_data['l_a'][0],
            V_A=segment_data['V_A'][0],
            V_B=segment_data['V_B'][0],
            V_C=segment_data['V_C'][0]
        )
        
        # Sum_G should be at least as large as G1
        assert Sum_G.magnitude >= G1.result.magnitude


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
