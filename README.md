# EIME - Engineering Intelligence Management Engine

A Python framework for transparent, verifiable engineering calculations.

## Vision

EIME enables engineers to write and review engineering formulas in simple, well-documented Python functions with transparency equivalent to hand calculations. It provides a scalable, production-ready framework for building libraries of atomic, human-verified formulas that can be used across multiple output formats (Streamlit apps, Jupyter notebooks, API endpoints, Python scripts).

## Key Features

- **Transparent Formulas**: Write engineering calculations as simple, readable Python functions
- **Documentation Generation**: Automatic documentation with LaTeX representation
- **Check Flagging**: Built-in system for tracking design checks and warnings
- **Batch Calculations**: Native support for numpy arrays for large-scale computations
- **Modular Design**: Clear separation between core framework and design code implementations
- **Testing Framework**: Unit testing utilities specifically for engineering formulas

## Installation

### Using UV (Recommended)

```bash
# Install UV if not already installed
pip install uv

# Clone the repository
git clone https://github.com/yourusername/eime.git
cd eime

# Create virtual environment and install
uv venv
uv pip install -e .

# Install with optional dependencies
uv pip install -e ".[dev]"           # Development tools
uv pip install -e ".[visualization]" # Plotting tools
uv pip install -e ".[all]"          # Everything
```

### Using pip

```bash
pip install -e .
```

## Quick Start

```python
import eime
from design.csa_o86_2025.calculators import TimberCalculator

# Example usage (to be implemented in later phases)
# calculator = TimberCalculator()
# results = calculator.design_beam(...)
```

## Project Structure

```
eime/                          # Core library
├── formula.py                 # Formula framework
├── procedure.py               # Design procedure framework
├── calculator.py              # Calculator framework
├── tables.py                  # Table loading utilities
├── checks.py                  # Check flagging system
├── output.py                  # Output formatting
└── testing.py                 # Testing framework

design/                        # Design code implementations
└── csa_o86_2025/             # CSA O86-2025 timber design
    ├── formulas/             # Timber formulas
    ├── procedures/           # Timber procedures
    ├── calculators/          # Timber calculators
    └── tables/               # JSON reference tables

utils/                         # Utility tools
├── fem/                      # 2D FEM solver
└── visualization/            # Plotting utilities

examples/                     # Usage examples
tests/                        # Test suite
experiments/                  # Personal experimentation
```

## Core Concepts

### Formula
The atomic building block - a single engineering calculation with:
- Clear inputs and outputs
- Comprehensive documentation
- LaTeX representation
- Design checks and warnings
- Support for batch calculations

### Design Procedure
A collection of formulas commonly used together for specific engineering tasks.

### Calculator
Higher-level interface that orchestrates design procedures and manages workflow.

### Tables
Design-code-specific reference data stored as JSON for easy parsing and versioning.

## Development Status

🚧 **Currently in active development - Phase 1: Foundation** 🚧

- [x] Directory structure created
- [x] Package configuration (pyproject.toml)
- [ ] Core framework implementation
- [ ] Timber design migration
- [ ] Testing framework
- [ ] Documentation and examples

## Contributing

This is currently a personal project under active refactoring. Contribution guidelines will be added in future releases.

## Design Codes Supported

- **CSA O86-2025**: Engineering Design in Wood (Canadian timber design standard)

Additional design codes can be added by following the pattern in `design/csa_o86_2025/`.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=eime --cov=design

# Run specific test file
pytest tests/test_formulas.py
```

## Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy eime/ design/ utils/
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Documentation

For detailed documentation, see:
- [Product Requirements Document](artifacts/PRD%20-%20EIME%20Refactor.md)
- [Project Requirements](artifacts/Project%20Requirements.md)

## Roadmap

### Phase 1: Foundation ✅
- Directory structure
- Package configuration
- UV setup

### Phase 2: Core Framework (In Progress)
- Formula framework
- Procedure framework
- Calculator framework
- Table management
- Testing utilities

### Phase 3: Timber Design Migration
- Migrate formulas from legacy code
- Implement procedures
- Build calculators
- Unit tests

### Phase 4: Utilities & Examples
- 2D FEM solver
- Visualization tools
- Working examples

### Phase 5: Testing & Documentation
- Comprehensive test suite
- API documentation
- Migration guide

## Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with transparency and verification in mind.**