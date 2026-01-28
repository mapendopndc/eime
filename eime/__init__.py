"""
EIME - Engineering Intelligence Management Engine

A framework for transparent, verifiable engineering calculations.
"""

__version__ = "0.1.0"

# Core formula components
from .formula import (
    EngineeringFunction,
    EngineeringFormula,
    EngineeringSwitch,
    formula,
    switch,
    create_formula,
    create_switch,
)

# Check system
from .checks import (
    STATUS,
    EngineeringCheck,
    Upperbound,
    Lowerbound,
    Equality,
    InvalidResult,
    Check,
)

# Output and formatting
from .output import (
    Param,
    LaTeXFormatter,
    DisplayText,
    InputGroup,
    format_result_with_unit,
)

# Procedure framework
from .procedure import EngineeringProcedure

# Calculator framework
from .calculator import (
    EngineeringCalculator,
    SimpleCalculator,
)

# Table management
from .tables import (
    load_table,
    table_to_dataframe,
    lookup_value,
    interpolate_table,
    DesignTable,
    TableCache,
)

# Testing utilities
from .testing import (
    FormulaTestCase,
    FormulaTestSuite,
    test_formula,
    compare_values,
    assert_formula_result,
    PropertyBasedTest,
)

# Expose key classes and functions at package level
__all__ = [
    # Version
    "__version__",
    
    # Formula
    "EngineeringFunction",
    "EngineeringFormula",
    "EngineeringSwitch",
    "formula",
    "create_formula",
    "create_switch",
    
    # Checks
    "STATUS",
    "EngineeringCheck",
    "Upperbound",
    "Lowerbound",
    "Equality",
    "InvalidResult",
    "Check",
    
    # Output
    "Param",
    "LaTeXFormatter",
    "DisplayText",
    "InputGroup",
    "format_result_with_unit",
    
    # Procedure
    "EngineeringProcedure",
    
    # Calculator
    "EngineeringCalculator",
    "SimpleCalculator",
    
    # Tables
    "load_table",
    "table_to_dataframe",
    "lookup_value",
    "interpolate_table",
    "DesignTable",
    "TableCache",
    
    # Testing
    "FormulaTestCase",
    "FormulaTestSuite",
    "test_formula",
    "compare_values",
    "assert_formula_result",
    "PropertyBasedTest",
]
