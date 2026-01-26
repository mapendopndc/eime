"""
Simple example demonstrating EIME core framework.

This example shows how to create formulas, run checks, and build procedures.
"""

import eime
import numpy as np

# Example 1: Simple stress formula
def example_stress_formula():
    """Calculate axial stress: σ = F / A"""
    
    # Create the formula
    stress = eime.create_formula(
        name="\\sigma",
        params={
            "F": eime.Param("F", desc="Axial force"),
            "A": eime.Param("A", desc="Cross-sectional area")
        },
        logic=lambda F, A: F / A,
        latex_template=lambda F, A: f"\\frac{{{F}}}{{{A}}}",
        source="Example 1",
        checks=[
            eime.Check.upperbound(
                upperbound=350,
                status_code=eime.STATUS.FAIL,
                check_id=101,
                message="Stress exceeds allowable (350 MPa)"
            )
        ],
        desc="Axial stress calculation"
    )
    
    # Solve with inputs
    result = stress.add_inputs(F=10000, A=50).solve().run_checks()
    
    print("\n" + "="*60)
    print("Example 1: Simple Stress Formula")
    print("="*60)
    print(f"Force: 10000 N")
    print(f"Area: 50 mm²")
    print(f"Stress: {result.result:.2f} MPa")
    print("\nLaTeX output:")
    print(result.generate_latex(0))
    
    # Test the result
    result.test(200.0)  # Expected: 10000/50 = 200 MPa
    
    return result


# Example 2: Batch calculation with arrays
def example_batch_calculation():
    """Demonstrate batch calculation with numpy arrays"""
    
    stress = eime.create_formula(
        name="\\sigma",
        params={
            "F": eime.Param("F", desc="Axial force"),
            "A": eime.Param("A", desc="Cross-sectional area")
        },
        logic=lambda F, A: F / A,
        latex_template=lambda F, A: f"\\frac{{{F}}}{{{A}}}",
        checks=[
            eime.Check.upperbound(350, eime.STATUS.FAIL, 101, "Exceeds allowable")
        ]
    )
    
    # Batch inputs
    forces = np.array([5000, 10000, 15000, 20000])
    areas = np.array([25, 50, 75, 100])
    
    result = stress.add_inputs(F=forces, A=areas).solve().run_checks()
    
    print("\n" + "="*60)
    print("Example 2: Batch Calculation")
    print("="*60)
    print(f"Number of elements: {len(forces)}")
    print(f"Forces: {forces}")
    print(f"Areas: {areas}")
    print(f"Stresses: {result.result}")
    
    # Show first element's LaTeX
    print("\nLaTeX for element 0:")
    print(result.generate_latex(0))
    
    return result


# Example 3: Engineering procedure
def example_procedure():
    """Demonstrate engineering procedure with multiple formulas"""
    
    # Create procedure
    procedure = eime.EngineeringProcedure("Beam Stress Check")
    
    # Formula 1: Moment
    moment = eime.create_formula(
        name="M",
        params={
            "w": eime.Param("w", desc="Uniform load"),
            "L": eime.Param("L", desc="Span length")
        },
        logic=lambda w, L: w * L**2 / 8,
        latex_template=lambda w, L: f"\\frac{{{w} {L}^2}}{{8}}",
        source="Beam theory",
        desc="Maximum moment for simply supported beam"
    )
    
    M = moment.add_inputs(w=10, L=5000).solve().run_checks()
    
    # Formula 2: Section modulus
    section_modulus = eime.create_formula(
        name="S",
        params={
            "b": eime.Param("b", desc="Width"),
            "d": eime.Param("d", desc="Depth")
        },
        logic=lambda b, d: b * d**2 / 6,
        latex_template=lambda b, d: f"\\frac{{{b} {d}^2}}{{6}}",
        desc="Elastic section modulus"
    )
    
    S = section_modulus.add_inputs(b=140, d=241).solve().run_checks()
    
    # Formula 3: Bending stress
    bending_stress = eime.create_formula(
        name="f_b",
        params={
            "M": eime.Param("M", desc="Bending moment"),
            "S": eime.Param("S", desc="Section modulus")
        },
        logic=lambda M, S: M / S,
        latex_template=lambda M, S: f"\\frac{{{M}}}{{{S}}}",
        checks=[
            eime.Check.upperbound(30, eime.STATUS.FAIL, 201, "Bending stress exceeds allowable")
        ],
        desc="Bending stress calculation"
    )
    
    fb = bending_stress.add_inputs(M=M.result, S=S.result).solve().run_checks()
    
    # Build procedure
    procedure.add_title("Applied Loading")
    procedure.add_computation(moment)
    
    procedure.add_title("Section Properties")
    procedure.add_computation(section_modulus)
    
    procedure.add_title("Bending Stress Check")
    procedure.add_computation(bending_stress)
    
    print("\n" + "="*60)
    print("Example 3: Engineering Procedure")
    print("="*60)
    print(f"Procedure: {procedure.name}")
    print(f"Results:\n{procedure.results}")
    print(f"\nStatus log:\n{procedure.status_log}")
    
    return procedure


# Example 4: Using the testing framework
def example_testing():
    """Demonstrate formula testing"""
    
    def stress_formula(F, A):
        return eime.create_formula(
            name="\\sigma",
            params={
                "F": eime.Param("F"),
                "A": eime.Param("A")
            },
            logic=lambda F, A: F / A,
            latex_template=lambda F, A: f"{F}/{A}"
        ).add_inputs(F=F, A=A).solve()
    
    # Create test suite
    test_cases = [
        {"name": "Test 1", "inputs": {"F": 1000, "A": 100}, "expected": 10.0},
        {"name": "Test 2", "inputs": {"F": 2000, "A": 100}, "expected": 20.0},
        {"name": "Test 3", "inputs": {"F": 5000, "A": 250}, "expected": 20.0}
    ]
    
    print("\n" + "="*60)
    print("Example 4: Formula Testing")
    print("="*60)
    
    eime.test_formula(stress_formula, test_cases, name="Stress Formula Tests")


if __name__ == "__main__":
    # Run all examples
    print("\n" + "="*70)
    print(" EIME Framework Examples")
    print("="*70)
    
    example_stress_formula()
    example_batch_calculation()
    example_procedure()
    example_testing()
    
    print("\n" + "="*70)
    print(" All examples completed successfully!")
    print("="*70 + "\n")
