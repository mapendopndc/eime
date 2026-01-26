# Product Requirements Document: EIME Framework Refactor

**Project Name:** EIME (Engineering Intelligence Management Engine) - Complete Refactor  
**Version:** 1.0  
**Date:** January 26, 2026  
**Status:** Planning

---

## 1. Executive Summary

This PRD outlines the complete refactor of the EIME codebase from a monolithic structure to a production-ready Python library. The refactor will transform the current legacy implementation into a well-organized, maintainable framework that follows modern software design principles while maintaining similar complexity levels for developer accessibility.

**Key Driver:** Enable non-technical engineers to write and review engineering formulas in Python with transparency equivalent to hand calculations, while providing a scalable, production-ready framework.

---

## 2. Product Vision

EIME is the next generation of engineering calculation software designed to:
- Allow engineers to write and review engineering formulas in simple, well-documented Python functions
- Build a library of atomic, human-verified formulas presented with hand-calculation-level transparency
- Enable rapid, large-scale engineering calculations using numpy arrays
- Support multiple output formats (Streamlit apps, Jupyter/Marimo notebooks, API endpoints, Python scripts)

---

## 3. Project Objectives

### 3.1 Primary Objectives
1. **Modularize the codebase**: Break down the monolithic `eime.py` file into focused, single-responsibility modules
2. **Separate concerns**: Decouple the core EIME framework from design-code-specific implementations
3. **Production readiness**: Transform the codebase into a pip-installable Python library with proper packaging
4. **Maintain simplicity**: Keep overall complexity similar to current implementation for developer accessibility
5. **Enable extensibility**: Provide clear patterns for users to build custom design code implementations

### 3.2 Secondary Objectives
- Implement unit testing framework for engineering formulas
- Migrate to UV package manager
- Provide comprehensive documentation and examples
- Discard all unused/legacy code (no backwards compatibility required)

---

## 4. Scope

### 4.1 In Scope
- Complete restructuring of the `eime.py` monolithic file into modular components
- Creation of installable `eime` Python library (core framework)
- Separation of design-code-specific logic into `design/` directory
- Implementation of CSA O86-2025 timber design as reference example
- Creation of utility tools directory (2D FEM solver, visualization)
- Setup of UV package manager and proper Python packaging
- Unit testing framework for engineering formulas
- Documentation and usage examples
- Personal testing/experimentation directory structure

### 4.2 Out of Scope
- Backwards compatibility with existing code
- Support for design codes other than CSA O86-2025 timber (can be added later by users)
- GUI development (visualization layers like Streamlit are separate concerns)
- Cloud deployment or hosting infrastructure
- Database integration

---

## 5. Core Framework Components

### 5.1 EIME Building Blocks

#### 5.1.1 Formula
**Definition:** The atomic building block - a single engineering calculation.

**Requirements:**
- Takes inputs, performs calculations, returns outputs
- Includes checks that get flagged in documentation
- Must remain simple and human-readable
- Contains clear, comprehensive documentation
- Includes LaTeX representation for visualization
- Supports numpy arrays for batch calculations

**Technical Specifications:**
- Function-based implementation
- Type hints required
- Docstring format: must include description, parameters, returns, LaTeX representation
- Check flagging mechanism must be standardized

#### 5.1.2 Design Procedure
**Definition:** Collection of formulas commonly used together for specific engineering tasks.

**Requirements:**
- Groups related formulas logically
- Maintains transparency of underlying formula calls
- Streamlines workflow and ensures consistency
- Provides clear API for formula orchestration

#### 5.1.3 Calculator
**Definition:** Higher-level construct exposing API to interact with design procedures.

**Requirements:**
- User-friendly interface for input collection
- Orchestrates design procedure calls
- Returns results in structured format
- Handles error propagation and validation

#### 5.1.4 Tables
**Definition:** Design-code-specific reference data stored as JSON.

**Requirements:**
- JSON format for easy parsing
- Versioned by design code (e.g., CSA O86-24)
- Easily loadable into formulas
- Schema validation for data integrity

---

## 6. Directory Structure

### 6.1 Required Structure
```
eime/                          # Core library (pip installable)
├── __init__.py
├── formula.py                 # Formula base classes and decorators
├── procedure.py               # Design procedure framework
├── calculator.py              # Calculator framework
├── tables.py                  # Table loading and management
├── checks.py                  # Check flagging system
├── output.py                  # Output formatting (LaTeX, documentation)
├── testing.py                 # Unit testing framework for formulas
└── utils.py                   # Core utilities

design/                        # Design-code-specific implementations
└── csa_o86_2025/             # CSA O86-2025 timber design
    ├── __init__.py
    ├── formulas/             # Timber-specific formulas
    ├── procedures/           # Timber design procedures
    ├── calculators/          # Timber calculators
    └── tables/               # JSON tables from CSA O86-2025
        ├── CSA O86-24_T7-2.json
        ├── CSA O86-24_T7-3.json
        └── CSA O86-24_TA-4.json

utils/                         # Additional utility tools
├── __init__.py
├── fem/                      # 2D FEM solver
│   ├── __init__.py
│   ├── solver.py
│   └── elements.py
└── visualization/            # Visualization tools
    ├── __init__.py
    └── plotting.py

tests/                        # Test directory
├── test_formulas.py
├── test_procedures.py
└── test_calculators.py

experiments/                  # Personal tests and experimentation
└── README.md

examples/                     # Usage examples
├── timber_design_example.py
└── streamlit_app_example.py

pyproject.toml               # UV/pip package configuration
requirements.txt             # Dependencies (if needed)
README.md                    # Main documentation
LICENSE                      # License file
```

---

## 7. Functional Requirements

### 7.1 Core EIME Library (eime/)

#### FR-1: Formula Framework
- **FR-1.1**: Formula decorator to standardize formula creation
- **FR-1.2**: Automatic documentation generation from docstrings
- **FR-1.3**: LaTeX rendering support for formulas
- **FR-1.4**: Check flagging mechanism with severity levels
- **FR-1.5**: Numpy array support for batch calculations
- **FR-1.6**: Type validation for inputs and outputs

#### FR-2: Design Procedure Framework
- **FR-2.1**: Procedure class/decorator for grouping formulas
- **FR-2.2**: Sequential formula execution with state management
- **FR-2.3**: Automatic propagation of intermediate results
- **FR-2.4**: Documentation generation for procedures

#### FR-3: Calculator Framework
- **FR-3.1**: Calculator base class with input validation
- **FR-3.2**: Integration with design procedures
- **FR-3.3**: Result formatting and export capabilities
- **FR-3.4**: Error handling and reporting

#### FR-4: Table Management
- **FR-4.1**: JSON table loading utilities
- **FR-4.2**: Table schema validation
- **FR-4.3**: Table interpolation/lookup methods
- **FR-4.4**: Caching for performance

#### FR-5: Testing Framework
- **FR-5.1**: Formula unit test decorator
- **FR-5.2**: Test case definition format
- **FR-5.3**: Tolerance-based comparison for floating point
- **FR-5.4**: Automatic test discovery and execution

### 7.2 Design Code Implementation (design/csa_o86_2025/)

#### FR-6: Timber Design Formulas
- **FR-6.1**: Migrate existing timber formulas from eime.py
- **FR-6.2**: Organize formulas by design code section
- **FR-6.3**: Include all checks from current implementation
- **FR-6.4**: Add unit tests for all formulas

#### FR-7: Timber Design Procedures
- **FR-7.1**: Migrate existing procedures from eime.py
- **FR-7.2**: Document procedure workflows
- **FR-7.3**: Add integration tests

#### FR-8: Timber Calculators
- **FR-8.1**: Migrate existing calculators from eime.py
- **FR-8.2**: Ensure compatibility with existing data pipeline
- **FR-8.3**: Maintain batch calculation capabilities

### 7.3 Utility Tools (utils/)

#### FR-9: 2D FEM Solver
- **FR-9.1**: Simple 2D frame element implementation
- **FR-9.2**: Static analysis solver
- **FR-9.3**: Result extraction methods
- **FR-9.4**: Basic visualization

#### FR-10: Visualization Tools
- **FR-10.1**: Plot generation utilities
- **FR-10.2**: LaTeX rendering helpers
- **FR-10.3**: Integration with matplotlib/plotly

---

## 8. Non-Functional Requirements

### 8.1 Performance
- **NFR-1**: Batch calculations must support numpy arrays without performance degradation
- **NFR-2**: Table lookups must be cached for repeated access
- **NFR-3**: Formula execution overhead must be minimal (<10% of calculation time)

### 8.2 Maintainability
- **NFR-4**: All modules must follow single responsibility principle
- **NFR-5**: Code complexity must remain accessible to junior developers
- **NFR-6**: Maximum function length: 50 lines (excluding docstrings)
- **NFR-7**: Type hints required for all public APIs

### 8.3 Usability
- **NFR-8**: Formulas must be human-readable and verifiable
- **NFR-9**: Documentation must be comprehensive and include examples
- **NFR-10**: Error messages must be clear and actionable

### 8.4 Testability
- **NFR-11**: All formulas must have unit tests
- **NFR-12**: Test coverage minimum: 80% for core library
- **NFR-13**: Integration tests for all procedures

### 8.5 Compatibility
- **NFR-14**: Python 3.10+ support
- **NFR-15**: Cross-platform compatibility (Windows, macOS, Linux)
- **NFR-16**: UV package manager integration

---

## 9. Technical Specifications

### 9.1 Technology Stack
- **Language**: Python 3.10+
- **Package Manager**: UV
- **Core Dependencies**:
  - numpy (numerical computations)
  - pandas (data handling)
  - pydantic (data validation)
  - pytest (testing)
- **Optional Dependencies**:
  - matplotlib/plotly (visualization)
  - streamlit (web interface, not in core library)
  - jupyter/marimo (notebooks, not in core library)

### 9.2 Packaging
- Use `pyproject.toml` for package configuration
- Follow PEP 517/518 standards
- Include entry points for CLI tools (if needed)
- Semantic versioning (SemVer)

### 9.3 Code Standards
- Follow PEP 8 style guide
- Use type hints (PEP 484)
- Docstring format: Google or NumPy style
- Maximum line length: 100 characters
- Use ruff for linting and formatting

---

## 10. Migration Strategy

### 10.1 From libraries/eime.py to eime/

**Phase 1: Analysis**
1. Audit all functions/classes in current eime.py
2. Categorize by component type (formula, procedure, calculator, utility)
3. Identify dependencies and coupling
4. Mark unused/dead code for removal

**Phase 2: Core Framework Extraction**
1. Create base classes and decorators for formulas
2. Extract check flagging system
3. Extract documentation/LaTeX generation
4. Create procedure and calculator frameworks
5. Extract table management utilities

**Phase 3: Timber Design Migration**
1. Move timber-specific formulas to design/csa_o86_2025/formulas/
2. Move timber procedures to design/csa_o86_2025/procedures/
3. Move timber calculators to design/csa_o86_2025/calculators/
4. Move JSON tables to design/csa_o86_2025/tables/

**Phase 4: Testing Implementation**
1. Create testing framework in eime/testing.py
2. Write unit tests for all migrated formulas
3. Write integration tests for procedures
4. Write end-to-end tests for calculators

**Phase 5: Documentation & Examples**
1. Write comprehensive README
2. Create usage examples
3. Document migration guide for users
4. Create API reference documentation

---

## 11. Acceptance Criteria

### 11.1 Core Library Acceptance Criteria
- [ ] AC-1: eime library can be installed via `uv pip install -e .`
- [ ] AC-2: All core modules (formula, procedure, calculator, tables) are separate files
- [ ] AC-3: Formula decorator works and generates documentation
- [ ] AC-4: Check flagging system works and flags are captured
- [ ] AC-5: LaTeX rendering produces valid output
- [ ] AC-6: Numpy array batch calculations work correctly
- [ ] AC-7: Testing framework allows easy formula unit tests
- [ ] AC-8: No design-code-specific logic exists in core eime/ directory

### 11.2 Design Code Acceptance Criteria
- [ ] AC-9: All timber formulas migrated and functional
- [ ] AC-10: All timber procedures migrated and functional
- [ ] AC-11: All timber calculators migrated and functional
- [ ] AC-12: All JSON tables loaded correctly
- [ ] AC-13: Existing timber design workflow still works (Etabs preprocessing → EIME batch design → output)
- [ ] AC-14: All timber formulas have unit tests with >80% coverage

### 11.3 Utilities Acceptance Criteria
- [ ] AC-15: 2D FEM solver can solve simple frame problems
- [ ] AC-16: Visualization tools can generate basic plots

### 11.4 Packaging Acceptance Criteria
- [ ] AC-17: pyproject.toml is properly configured
- [ ] AC-18: UV can install all dependencies
- [ ] AC-19: Package can be imported after installation: `import eime`
- [ ] AC-20: All tests pass with pytest

### 11.5 Documentation Acceptance Criteria
- [ ] AC-21: README.md explains EIME concept and usage
- [ ] AC-22: Examples directory contains working examples
- [ ] AC-23: Each module has comprehensive docstrings
- [ ] AC-24: Migration guide exists for updating existing code

---

## 12. Implementation Phases

### Phase 1: Foundation (Week 1)
**Deliverables:**
- Directory structure created
- pyproject.toml configured
- UV setup complete
- Basic eime/__init__.py

**Tasks:**
- Create all directories per section 6.1
- Configure pyproject.toml with dependencies
- Set up UV virtual environment
- Create placeholder __init__.py files

---

### Phase 2: Core Framework (Week 2-3)
**Deliverables:**
- eime/formula.py with base classes and decorators
- eime/checks.py with flagging system
- eime/output.py with LaTeX rendering
- eime/procedure.py with procedure framework
- eime/calculator.py with calculator framework
- eime/tables.py with JSON loading utilities
- eime/testing.py with unit test framework

**Tasks:**
- Extract and refactor formula creation logic
- Build check flagging system
- Implement documentation generation
- Create procedure orchestration framework
- Build calculator base classes
- Implement table loading and caching
- Create formula testing utilities

---

### Phase 3: Timber Design Migration (Week 4-5)
**Deliverables:**
- All timber formulas in design/csa_o86_2025/formulas/
- All timber procedures in design/csa_o86_2025/procedures/
- All timber calculators in design/csa_o86_2025/calculators/
- All JSON tables in design/csa_o86_2025/tables/
- Unit tests for all formulas

**Tasks:**
- Categorize and migrate timber formulas
- Migrate timber design procedures
- Migrate timber calculators
- Move JSON tables
- Write unit tests for each formula
- Verify batch calculation compatibility

---

### Phase 4: Utilities & Examples (Week 6)
**Deliverables:**
- utils/fem/ with basic 2D FEM solver
- utils/visualization/ with plotting tools
- examples/ with working examples
- experiments/ directory set up

**Tasks:**
- Implement simple 2D frame element
- Create basic static solver
- Build visualization utilities
- Create timber design example
- Create Streamlit app example
- Set up experiments directory

---

### Phase 5: Testing & Documentation (Week 7)
**Deliverables:**
- Comprehensive test suite
- README.md
- Migration guide
- API documentation
- All acceptance criteria met

**Tasks:**
- Achieve >80% test coverage
- Write comprehensive README
- Document all APIs
- Create migration guide
- Run end-to-end tests
- Verify all acceptance criteria

---

## 13. Success Metrics

1. **Code Quality:**
   - Test coverage ≥ 80%
   - Zero critical linting errors
   - All type hints pass mypy check

2. **Usability:**
   - Example code runs without modification
   - Documentation completeness score ≥ 90%
   - Installation time < 2 minutes

3. **Performance:**
   - Batch calculations match current performance
   - Formula overhead < 10%
   - Table lookups < 1ms (cached)

4. **Maintainability:**
   - Average module length < 500 lines
   - Cyclomatic complexity < 10 per function
   - Clear separation of concerns achieved

---

## 14. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Over-engineering core framework | High | Medium | Maintain complexity similar to current implementation; regular simplicity reviews |
| Breaking existing workflows | High | Medium | Comprehensive integration testing; maintain example use cases |
| Performance degradation | Medium | Low | Benchmark against current implementation; optimize hotspots |
| Incomplete migration | High | Low | Systematic audit of eime.py; checkklist for all functions |
| Poor documentation | Medium | Medium | Documentation as deliverable in each phase; examples required |

---

## 15. Dependencies & Assumptions

### Dependencies
- Python 3.10+ available
- UV package manager can be installed
- Current eime.py code is functional
- CSA O86-2025 JSON tables are valid

### Assumptions
- Developers have basic Python knowledge
- Engineering formulas are already validated
- Existing Etabs preprocessing workflow is stable
- Streamlit output layer remains separate from core library

---

## 16. Open Questions

1. Should the testing framework support property-based testing (hypothesis)?
2. Do we need a plugin system for custom design codes?
3. Should visualization tools be part of core library or separate package?
4. What level of backwards compatibility (if any) should examples maintain?

---

## 17. References

- Current codebase: `libraries/eime.py`
- Example use case: Timber design (CSA O86-2025)
- Related files: `TimberCalculator.py`, `TimberDesign.py`, `TimberProcedures.py`, `TimberTables.py`
- Tables: `CSA O86-24_T7-2.json`, `CSA O86-24_T7-3.json`, `CSA O86-24_TA-4.json`

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-26 | AI Agent | Initial PRD creation from project requirements |

---

**Approval Status:** Draft - Pending Review

**Next Steps:** Review PRD → Approve → Begin Phase 1 Implementation
