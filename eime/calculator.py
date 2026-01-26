"""
Calculator framework for high-level engineering design interfaces.

This module provides base classes for building design calculators that
orchestrate procedures and provide user-friendly APIs.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd

from .procedure import EngineeringProcedure


class EngineeringCalculator(ABC):
    """
    Base class for engineering design calculators.
    
    A calculator provides a high-level interface for performing complete
    design checks, managing input validation, and formatting results.
    
    Subclasses should implement:
    - validate_inputs(): Check input validity
    - run_design(): Execute design procedures
    - format_results(): Structure output data
    
    Example:
        class BeamDesignCalculator(EngineeringCalculator):
            def validate_inputs(self, **inputs):
                # Check inputs are valid
                pass
            
            def run_design(self, **inputs):
                # Run design procedures
                procedure = EngineeringProcedure("Beam Design")
                # ... add computations
                return procedure
            
            def format_results(self, procedure):
                return procedure.summary()
    """
    
    def __init__(self, name: str = "") -> None:
        """
        Initialize calculator.
        
        Args:
            name: Calculator name
        """
        self.name = name or self.__class__.__name__
        self.procedures: List[EngineeringProcedure] = []
        self.results: Optional[pd.DataFrame] = None
        self.last_inputs: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def validate_inputs(self, **inputs: Any) -> None:
        """
        Validate input parameters.
        
        Should raise ValueError or TypeError if inputs are invalid.
        
        Args:
            **inputs: Named input parameters
            
        Raises:
            ValueError: If inputs are invalid
        """
        pass
    
    @abstractmethod
    def run_design(self, **inputs: Any) -> EngineeringProcedure:
        """
        Execute the design calculation.
        
        Args:
            **inputs: Named input parameters
            
        Returns:
            EngineeringProcedure with complete design workflow
        """
        pass
    
    @abstractmethod
    def format_results(self, procedure: EngineeringProcedure) -> pd.DataFrame:
        """
        Format procedure results for output.
        
        Args:
            procedure: Completed design procedure
            
        Returns:
            DataFrame with formatted results
        """
        pass
    
    def design(self, **inputs: Any) -> pd.DataFrame:
        """
        Main entry point for design calculations.
        
        Validates inputs, runs design, and formats results.
        
        Args:
            **inputs: Named input parameters
            
        Returns:
            DataFrame with design results
            
        Example:
            results = calculator.design(
                length=5000,
                width=140,
                depth=241,
                load=10.5
            )
        """
        # Store inputs
        self.last_inputs = inputs
        
        # Validate
        self.validate_inputs(**inputs)
        
        # Run design
        procedure = self.run_design(**inputs)
        self.procedures.append(procedure)
        
        # Format results
        self.results = self.format_results(procedure)
        
        return self.results
    
    def batch_design(self, input_df: pd.DataFrame) -> pd.DataFrame:
        """
        Run design for multiple elements from a DataFrame.
        
        Args:
            input_df: DataFrame where each row is a set of inputs
            
        Returns:
            DataFrame with results for all elements
        """
        # Convert DataFrame rows to dict of arrays
        input_dict = {}
        for column in input_df.columns:
            input_dict[column] = input_df[column].values
        
        return self.design(**input_dict)
    
    def get_procedure(self, index: int = -1) -> Optional[EngineeringProcedure]:
        """
        Get a specific procedure from history.
        
        Args:
            index: Procedure index (default -1 for most recent)
            
        Returns:
            EngineeringProcedure or None
        """
        if not self.procedures:
            return None
        
        return self.procedures[index]
    
    def display_procedure(self, index: int = -1, element_index: int = 0) -> List[Any]:
        """
        Get display objects for a procedure.
        
        Args:
            index: Procedure index (default -1 for most recent)
            element_index: Element index for array results
            
        Returns:
            List of display objects (LaTeX, Markdown)
        """
        procedure = self.get_procedure(index)
        
        if procedure is None:
            return []
        
        return procedure.generate_display_objects(element_index)
    
    def export_results(self, file_path: str, **kwargs) -> None:
        """
        Export results to file.
        
        Args:
            file_path: Output file path
            **kwargs: Additional arguments for pandas to_csv/to_excel
        """
        if self.results is None:
            raise ValueError("No results to export. Run design() first.")
        
        # Determine format from extension
        if file_path.endswith('.csv'):
            self.results.to_csv(file_path, **kwargs)
        elif file_path.endswith('.xlsx'):
            self.results.to_excel(file_path, **kwargs)
        elif file_path.endswith('.json'):
            self.results.to_json(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
    
    def __repr__(self) -> str:
        n_procedures = len(self.procedures)
        has_results = self.results is not None
        return f"<{self.name}: {n_procedures} procedures, results={'available' if has_results else 'none'}>"


class SimpleCalculator(EngineeringCalculator):
    """
    Simple calculator implementation with minimal boilerplate.
    
    Useful for quick prototyping or simple single-procedure designs.
    
    Example:
        def my_design(length, load):
            procedure = EngineeringProcedure("Simple Design")
            # ... add computations
            return procedure
        
        calc = SimpleCalculator(design_func=my_design)
        results = calc.design(length=5000, load=10)
    """
    
    def __init__(
        self,
        design_func: callable,
        name: str = "SimpleCalculator",
        input_validator: Optional[callable] = None
    ) -> None:
        """
        Initialize simple calculator.
        
        Args:
            design_func: Function that takes inputs and returns EngineeringProcedure
            name: Calculator name
            input_validator: Optional function to validate inputs
        """
        super().__init__(name)
        self.design_func = design_func
        self.input_validator = input_validator
    
    def validate_inputs(self, **inputs: Any) -> None:
        """Validate inputs using provided validator."""
        if self.input_validator:
            self.input_validator(**inputs)
    
    def run_design(self, **inputs: Any) -> EngineeringProcedure:
        """Run the design function."""
        return self.design_func(**inputs)
    
    def format_results(self, procedure: EngineeringProcedure) -> pd.DataFrame:
        """Return procedure summary as results."""
        return procedure.summary()
