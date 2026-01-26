# Design Check Skill Guide

This guide provides essential knowledge for creating design calculation examples using the EIME Engineering Framework, based on CSA O86 timber design standards.

## Overview

Design examples use **Calculator classes** to encapsulate complete engineering calculations following code standards (e.g., CSA O86:24). Calculators provide:
- Clean, reusable API with single `.design()` method
- Automatic formula chaining and dependency management
- Material property integration from code tables
- Unit-aware calculations with automatic validation
- LaTeX-formatted calculation documentation via Procedures
- Design utilization checks and pass/fail status

**Important:** Always use calculators for design examples. Manual formula chaining is only for framework development and testing.

## Library Structure

### Key Components

```
eime/
  ├── formula.py          # EngineeringFormula base class, @formula decorator
  ├── calculator.py       # Calculator base class for design workflows
  ├── procedure.py        # Calculation sequence organization & LaTeX output
  ├── units.py            # Pint unit handling, validation
  └── tables.py           # Engineering table lookups

design/csa_o86_2025/
  ├── calculators/        # High-level calculator classes
  │   └── timber_beam.py
  ├── procedures/         # Formula chaining logic
  │   ├── glulam_bending.py
  │   ├── glulam_compression.py
  │   └── glulam_shear.py
  ├── formulas/           # Engineering formulas by design type
  │   ├── glulam_bending.py
  │   ├── glulam_compression.py
  │   ├── glulam_shear.py
  │   └── section_properties.py
  └── tables/             # CSA O86 code tables (JSON)
      ├── CSA O86-24_T7-2.json  # Material strengths
      └── CSA O86-24_T7-3.json  # Service condition factors
```

## Creating Calculator-Based Design Examples

### Example File Structure

```python
"""
<Title> Calculator Example

Demonstrates <design type> using the <Calculator> class.
"""

from pint import UnitRegistry
from design.csa_o86_2025.calculators import TimberBeamCalculator
from design.csa_o86_2025.tables import specified_strengths, service_condition_factors

# Create unit registry
ureg = UnitRegistry()

# Unit shorthands
m = ureg.m
mm = ureg.mm
kPa = ureg.kPa
MPa = ureg.MPa
kN = ureg.kN
nd = ureg.dimensionless

def main():
    """Main calculation using calculator approach."""
    
    # ==========================================
    # USER INPUTS
    # ==========================================
    # Geometry, loads, material specs
    
    # ==========================================
    # LOAD MATERIAL PROPERTIES FROM TABLES
    # ==========================================
    strengths_table = specified_strengths()
    material_props = strengths_table.data.loc[grade, species]
    
    # ==========================================
    # PREPARE DESIGN PARAMETERS
    # ==========================================
    # Calculate factored loads, factors, etc.
    
    # ==========================================
    # RUN DESIGN USING CALCULATOR
    # ==========================================
    calculator = TimberBeamCalculator()
    results = calculator.design(
        # All required inputs
    )
    
    # ==========================================
    # EXTRACT & DISPLAY RESULTS
    # ==========================================
    procedure = calculator.get_procedure()
    # Extract resistances, calculate utilizations
    
    # ==========================================
    # GENERATE DOCUMENTATION
    # ==========================================
    doc = generate_calculation_document(...)
    # Save to markdown file
```

### Calculator Architecture

Calculators consist of three layers:

**1. Formulas** (`design/csa_o86_2025/formulas/`)
- Atomic engineering calculations
- Unit-aware with Pint
- Self-documenting with LaTeX templates
- Example: `modified_bending_strength(f_b, K_D, K_H, K_Sb, K_T)`

**2. Procedures** (`design/csa_o86_2025/procedures/`)
- Chain formulas in correct sequence
- Handle intermediate calculations
- Return `Procedure` object for documentation
- Example: `glulam_bending_procedure(inputs) -> Procedure`

**3. Calculators** (`design/csa_o86_2025/calculators/`)
- High-level API with `.design()` method
- Input validation and unit conversion
- Call appropriate procedures
- Organize results
- Example: `TimberBeamCalculator.design(...) -> dict`

### Creating a Procedure

Procedures organize formula chains and enable documentation:

```python
from eime.procedure import Procedure

def glulam_bending_procedure(
    b, d, L,
    f_b, K_D, K_H, K_Sb, K_T, K_x,
    phi_b
):
    """Execute glulam bending resistance calculation."""
    
    # Initialize procedure
    proc = Procedure(
        title="Glulam Bending Resistance",
        reference="CSA O86:24 Cl. 7.5.5.2"
    )
    
    # Add formulas in sequence
    S = section_modulus(b, d)
    proc.add_formula(S, section="Section Properties")
    
    K_Zbg = bending_size_factor(L, b, d)
    proc.add_formula(K_Zbg, section="Size Factor")
    
    F_b = modified_bending_strength(f_b, K_D, K_H, K_Sb, K_T)
    proc.add_formula(F_b, section="Modified Strength")
    
    M_r = moment_resistance_a(phi_b, F_b, S, K_x, K_Zbg)
    proc.add_formula(M_r, section="Moment Resistance")
    
    return proc
```

**Key points:**
- Procedures are **linear sequences** of formulas
- Use `.add_formula()` to append to the procedure
- Organize with section headings for clarity
- Formulas auto-solve when added to procedure
- Results accessible via `formula.result`

### Creating a Calculator

Calculators provide clean APIs around procedures:

```python
from eime.calculator import Calculator

class TimberBeamCalculator(Calculator):
    """Calculator for glulam beam bending and shear design."""
    
    def design(
        self,
        b, d, L,          # Geometry
        f_b, f_v,         # Material properties
        M_f, V_f,         # Applied forces
        # ... all other design parameters
    ):
        """
        Execute complete beam design.
        
        Returns:
            dict: Design results including resistances and checks
        """
        
        # Run bending procedure
        bending_proc = glulam_bending_procedure(
            b, d, L, f_b, K_D, K_H, K_Sb, K_T, K_x, phi_b
        )
        
        # Run shear procedure
        shear_proc = glulam_shear_procedure(
            b, d, f_v, K_D, K_H, K_Sv, K_T, phi_v
        )
        
        # Combine procedures
        self._procedure = Procedure(title="Glulam Beam Design")
        self._procedure.add_sub_procedure(bending_proc)
        self._procedure.add_sub_procedure(shear_proc)
        
        # Extract results
        M_r = bending_proc.get_result('M_{r,a}')
        V_r = shear_proc.get_result('V_r')
        
        return {
            'M_r': M_r,
            'V_r': V_r,
            # ... other results
        }
    
    def get_procedure(self):
        """Return procedure for documentation."""
        return self._procedure
```

**Key points:**
- Inherit from `Calculator` base class
- Single `.design()` method with all inputs
- Call procedures and combine them
- Store combined procedure in `self._procedure`
- Provide `.get_procedure()` for LaTeX generation

## Material Properties and Tables

### Table Lookups

Always use table lookups rather than hardcoding values:

```python
# Load material strengths from CSA O86-24 Table 7.2
strengths_table = specified_strengths()
material_props_dict = strengths_table.data.loc[grade, species]

# Extract with units
f_c = material_props_dict['f_c'] * MPa
E = material_props_dict['E'] * MPa

# Load service condition factors from CSA O86-24 Table 7.3
service_table = service_condition_factors()
K_Sc = service_table.data.loc['K_Sc', service_condition] * nd
```

**Available Material Properties (Table 7.2):**
- `f_b_pos`, `f_b_neg` - Bending strength (MPa)
- `f_v` - Shear strength (MPa)
- `f_c` - Compression strength (MPa)
- `E` - Modulus of elasticity (MPa)
- Note: `E_05` (5th percentile MOE) is NOT in the table - calculate as `0.85 * E`

**Available Species/Grades:**
- "Douglas Fir-Larch": 24f-E, 24f-EX, 20f-E, 20f-EX, 18t-E, 16c-E
- "Spruce-Lodgepole Pine-Jack Pine": 20f-E, 20f-EX, 16c-E

## Unit Handling (Critical!)

### Pint Quantities

**All formula parameters MUST be Pint Quantities:**

```python
# ✅ CORRECT
b = 175 * mm
d = 456 * mm
L_e = 3500 * mm
Z = (b.to(m) * d.to(m) * L.to(m))  # Keep as Quantity

# ❌ WRONG
Z = (b.to(m) * d.to(m) * L.to(m)).magnitude  # Strips units!
```

### Unit Conversions

When comparing or displaying results, convert units appropriately:

```python
# Solving formulas
P_r_result = Pr.solve().result  # Result is a Pint Quantity
P_r = P_r_result.to('kN').magnitude  # For display only

# Utilization calculations - ensure matching units
compression_util = (P_f.to('N') / P_r_result).magnitude
# Not: (P_f / P_r_result).magnitude  # May have unit mismatch
```

## Formula Definition Requirements

### Param Definitions

**Every Param MUST have a unit specified:**

```python
# ✅ CORRECT
return create_formula(
    name="F_c",
    params={
        "f_c": Param("f_c", unit="MPa", desc="specified compression strength"),
        "K_D": Param("K_D", unit="dimensionless", desc="load-duration factor"),
    },
    logic=lambda f_c, K_D: f_c * K_D,
    result_unit='MPa',  # Specify result unit
    ...
)

# ❌ WRONG - Missing unit parameter
params={
    "f_c": Param("f_c", desc="specified compression strength"),  # ERROR!
}
```

### Result Units

**Always specify `result_unit` for formulas:**

```python
# For dimensionless results (factors, ratios)
result_unit='dimensionless'

# For results with units
result_unit='MPa'      # Strengths
result_unit='N'        # Forces
result_unit='N*m'      # Moments
```

**Why this matters:** EIME extracts magnitudes from input quantities and needs to know what units to wrap the result in.

## Common Issues & Solutions

### Issue 1: Missing Unit Parameter

**Error:**
```
TypeError: Param.__init__() missing 1 required positional argument: 'unit'
```

**Solution:**
Add `unit` parameter to all Param definitions:
```python
"K_D": Param("K_D", unit="dimensionless", desc="load-duration factor")
```

### Issue 2: Unit Mismatch in Results

**Error:**
```
UnitError: Parameter 'K_Zcg' must be dimensionless. Received: 1 / meter ** 0.39
```

**Solution:**
Add `result_unit='dimensionless'` to the formula:
```python
return create_formula(
    name="K_{Zcg}",
    params={"Z": Param("Z", unit="m^3", desc="member volume")},
    logic=lambda Z: 0.68 * Z**(-0.13),
    result_unit='dimensionless',  # <-- Add this
    ...
)
```

### Issue 3: Double Superscript in LaTeX

**Error:**
```
KaTeX parse error: Double superscript at position 85: …\text{m}^{3}^{-0.13}
```

**Problem:** When a quantity with units (e.g., `0.11 m³`) is raised to a power, it creates invalid LaTeX: `\text{m}^{3}^{-0.13}`

**Solution:**
Wrap the entire quantity in parentheses in the latex_template:
```python
# ✅ CORRECT
latex_template=lambda Z: f"0.68 \\cdot \\left({Z}\\right)^{{-0.13}}"

# ❌ WRONG
latex_template=lambda Z: f"0.68 \\cdot {Z}^{{-0.13}}"
```

### Issue 4: Incorrect Utilization (0% or wrong value)

**Problem:** Unit mismatch between factored load and resistance

**Solution:**
Convert to matching units before division:
```python
# Ensure both in same units (e.g., Newtons)
util = (P_f.to('N') / P_r_result).magnitude
```

## Common Patterns in Design Examples

### Using Calculators in Examples

```python
def main():
    # 1. Define inputs (geometry, loads, materials)
    span_m = 6.0 * m
    b = 130 * mm
    # ...
    
    # 2. Load material properties from tables
    strengths_table = specified_strengths()
    f_b = strengths_table.data.loc[grade, species]['f_b_pos'] * MPa
    
    # 3. Calculate design parameters (factored loads, factors)
    w_factored = 1.25 * w_dead + 1.5 * w_live
    M_f = (w_factored * span_m**2) / 8
    
    # 4. Run calculator
    calculator = TimberBeamCalculator()
    results = calculator.design(b=b, d=d, L=L, ...)
    
    # 5. Extract results and calculate utilizations
    procedure = calculator.get_procedure()
    M_r = procedure.get_result('M_{r,a}')
    util = (M_f / M_r).to('dimensionless').magnitude
    
    # 6. Display summary and generate documentation
    print_summary(...)
    doc = generate_calculation_document(...)
```

### Step-by-Step Pattern (Legacy - For Reference Only)

**Note:** This pattern is deprecated. Use calculators instead.

The manual approach requires explicitly solving each formula:

```python
# DON'T USE THIS APPROACH IN EXAMPLES
KD = long_duration_factor(P_L_percent, P_S_percent)
K_D_value = KD.solve().result

Fc = modified_compression_strength(f_c, K_D_value, K_H, K_Sc, K_T)
F_c_value = Fc.solve().result
```

This is only shown for understanding the underlying mechanism. **Always use calculators in examples.**

## LaTeX Documentation Generation

The calculator's procedure automatically generates LaTeX output:

```python
# Get procedure from calculator
procedure = calculator.get_procedure()

# Generate LaTeX
latex_output = procedure.generate_latex()

# Include in documentation
doc.append("## 3. Resistance Calculations\n")
doc.append(latex_output)
```

### Document Structure

```python
def generate_calculation_document(...):
    doc = []
    
    # 1. Header
    doc.append("# <Title> Design Calculation\n")
    doc.append("## <Subtitle> - CSA O86:24\n")
    doc.append(f"*Calculation Date: {current_date}*\n")
    
    # 2. Design Parameters
    doc.append("## 1. Design Parameters\n")
    # Geometry, materials, loads
    
    # 3. Applied Forces
    doc.append("## 2. Applied Forces\n")
    # Show load calculations
    
    # 4. Resistance Calculations
    doc.append("## 3. Resistance Calculations\n")
    doc.append(procedure.generate_latex())  # From calculator
    
    # 5. Design Checks
    doc.append("## 4. Design Checks\n")
    # Utilization checks with ✓ or FAIL
    
    # 6. Summary
    doc.append("## 5. Summary\n")
    
    return "".join(doc)
```

### Utilization Check Format

```python
doc.append("### <Check Type> Check\n")
doc.append("$$\n")
doc.append(f"\\frac{{P_f}}{{P_r}} = \\frac{{{P_f_val:.1f}}}{{{P_r_val:.2f}}} = {util:.3f} ")
if util <= 1.0:
    doc.append("\\le 1.0 \\quad \\checkmark\n")
else:
    doc.append("> 1.0 \\quad \\text{FAIL}\n")
doc.append("$$\n")
```

## Best Practices

### 1. Always Use Calculators
Design examples should use calculator classes, not manual formula chaining.

### 2. Clear Section Comments
Use clear section headers in code:
```python
# ==========================================
# RUN DESIGN USING CALCULATOR
# ==========================================
```

### 3. Descriptive Variable Names
```python
# ✅ Good
M_r = procedure.get_result('M_{r,a}')
bending_util = (M_f / M_r).to('dimensionless').magnitude

# ❌ Confusing
mr = procedure.get_result('M_{r,a}')
util = (M_f / mr).magnitude
```

### 4. Unit Annotations
Always show what units you're using:
```python
span_m = 6.0 * m          # Clear intent
dead_load_kPa = 1.5 * kPa # Clear units
```

### 5. User Input Section
Make inputs easy to find and modify:
```python
# ==========================================
# USER INPUTS - Modify these as needed
# ==========================================
species = "Douglas Fir-Larch"
grade = "20f-E"
service_condition = "Dry-service conditions"
```

### 6. Results Summary
Provide clear terminal output:
```python
print("=" * 70)
print("TIMBER BEAM DESIGN SUMMARY")
print("=" * 70)
print(f"  Section:             {b.magnitude:.0f} x {d.magnitude:.0f} mm")
print(f"  Bending util.:       {bending_util:.1%}")
print(f"  STATUS: {status}")
print("=" * 70)
```

## Example Types & Available Calculators

### Timber Beam (Available)
- **Calculator:** `TimberBeamCalculator`
- **Checks:** Bending resistance, shear resistance
- **Example:** [simple_timber_beam_calculator_example.py](../examples/simple_timber_beam_calculator_example.py)

### Timber Column (Coming Soon)
- **Calculator:** To be implemented
- **Checks:** Axial compression, buckling
- **Status:** Use procedure-based approach until calculator available

## Testing Your Example

1. **Run the script** - Should execute without errors
2. **Check utilization** - Should be reasonable (not 0%, not > 100% for passing design)
3. **Verify LaTeX** - Open the generated .md file, check for parse errors
4. **Unit consistency** - All calculations should have proper units
5. **Code references** - Verify CSA O86 clause references are correct

## Quick Checklist

Before finalizing a design example:

**Calculator Usage:**
- [ ] Uses calculator class (not manual formula chaining)
- [ ] Single `.design()` call with all inputs
- [ ] Extracts procedure with `.get_procedure()`
- [ ] Uses `procedure.generate_latex()` for documentation

**Standard Requirements:**
- [ ] All imports present
- [ ] Unit registry created with shorthands
- [ ] Material properties from tables (not hardcoded)
- [ ] All formula parameters are Pint Quantities
- [ ] Utilization calculations use matching units
- [ ] Results summary prints to terminal
- [ ] Markdown document generates without LaTeX errors
- [ ] Example runs without warnings
- [ ] Comments explain each major section

## Reference

**Primary Example:** [simple_timber_beam_calculator_example.py](../examples/simple_timber_beam_calculator_example.py)

Study this for the standard calculator-based pattern.
