# EIME - Engineering Intelligence Management Engine

Transparent, verifiable engineering calculations in Python — built for engineers who want results they can audit and trust.

## Who this is for

- Structural and civil engineers who want calculation workflows that read like hand calcs.
- Teams that need traceable formulas, checks, and clear outputs.
- Anyone building repeatable design calculations in Python.

## What you can do with EIME

- **Run engineering calculations with transparency**: formulas are readable and documented.
- **Generate clear outputs**: calculations are designed to be inspectable and review-ready.
- **Flag checks and warnings**: built-in check tracking for design constraints.
- **Scale up**: batch-ready calculations for multiple cases.

## Why structural engineers move from Excel to EIME

- **Less hidden logic**: no cell references buried across tabs.
- **Units are enforced**: missing/incorrect units fail fast.
- **Checks live beside the math**: utilization limits, bounds, warnings.
- **Reviewable + versionable**: formulas are plain Python, ideal for peer review and git.
- **Easy param studies**: run dozens of cases without copy/paste.

## Feature highlights (with better examples)

### 1) A full formula is compact — and still contains everything

This is a complete, usable formula definition (no docstring) with:
named parameters, unit validation, LaTeX, a design-code reference, and a pass/fail check.

```python
from pint import UnitRegistry
from eime import Param, STATUS, Check, create_formula, formula

ureg = UnitRegistry()


@formula
def bending_utilization(demand, capacity):

    return create_formula(
        name="U",
        params={
            "demand": Param("M_u", unit="kN*m", desc="factored moment demand"),
            "capacity": Param("M_r", unit="kN*m", desc="factored moment resistance"),
        },
        logic=lambda demand, capacity: demand / capacity,
        latex_template=lambda demand, capacity: f"\\frac{{{demand}}}{{{capacity}}}",
        source="CSA O86 (example)",
        checks=[
            Check.upperbound(1.0, STATUS.FAIL, 101, "Demand exceeds capacity", inclusive=True)
        ],
        desc="Bending utilization",
    )


u = bending_utilization(

    demand=45 * ureg("kN*m"),
    capacity=52 * ureg("kN*m"),
)

print(u.result)           # 0.865... dimensionless
print(u.generate_latex()) # equation + substitutions + check summary
```

### 2) Unit safety (fail fast instead of “looks right”)

If you accidentally pass unitless inputs (Excel-style), EIME raises a clear error instead of silently proceeding.

### 3) Param studies without copy/paste (batch support)

```python
from pint import UnitRegistry
import numpy as np

ureg = UnitRegistry()

demands = np.array([30, 40, 55]) * ureg("kN*m")
capacity = 52 * ureg("kN*m")

u = bending_utilization(demand=demands, capacity=capacity)
print(u.result)  # array of utilizations
```

### 4) Compose calculations (formula-to-formula substitution)

Because formulas are objects, you can build calculations from smaller pieces.

```python
from pint import UnitRegistry
from eime import Param, create_formula, formula

ureg = UnitRegistry()


@formula
def rect_area(b, d):

    return create_formula(
        name="A",
        params={
            "b": Param("b", unit="mm", desc="width"),
            "d": Param("d", unit="mm", desc="depth"),
        },
        logic=lambda b, d: b * d,
        latex_template=lambda b, d: f"{b}\\cdot {d}",
        desc="Rectangular area",
    )


@formula
def axial_stress(P, A):

    return create_formula(
        name="\\sigma",
        params={
            "P": Param("P", unit="kN", desc="axial load"),
            "A": Param("A", unit="mm^2", desc="area"),
        },
        logic=lambda P, A: P / A,
        latex_template=lambda P, A: f"\\frac{{{P}}}{{{A}}}",
        result_unit="MPa",
        desc="Axial stress",
    )


A = rect_area(b=140 * ureg.mm, d=235 * ureg.mm)
sigma = axial_stress(P=350 * ureg.kN, A=A)  # pass the formula, not just the number
print(sigma.result)
```

## Design codes available

- **CSA O86-2025**: Engineering Design in Wood (Canadian timber design standard)

## Install

> EIME is currently installed from source.

### Using uv (recommended)

```bash
pip install uv
git clone https://github.com/yourusername/eime.git
cd eime
uv venv
uv pip install -e .
```

### Using pip

```bash
git clone https://github.com/yourusername/eime.git
cd eime
pip install -e .
```

## Quick start

Run a ready-to-use example:

```bash
python examples/simple_timber_beam_calculator_example.py
```

See example outputs:

- [examples/timber_beam_calculator_output.md](examples/timber_beam_calculator_output.md)
- [examples/timber_column_calculator_output.md](examples/timber_column_calculator_output.md)

## How EIME is organized (high level)

- **Formulas**: the atomic calculations
- **Procedures**: common sequences of formulas for a design task
- **Calculators**: friendly interfaces that orchestrate procedures
- **Tables**: code-specific reference data

## Current status

🚧 **Active development** 🚧

EIME is in the foundation and migration phases. Some APIs are still evolving.

## Documentation

- [Product Requirements Document](artifacts/PRD%20-%20EIME%20Refactor.md)
- [Project Requirements](artifacts/Project%20Requirements.md)

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

This is currently a personal project under active refactoring. Contribution guidelines will be added in future releases.

---

**Built with transparency and verification in mind.**