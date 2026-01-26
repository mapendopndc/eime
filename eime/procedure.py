"""
Design procedure framework.

This module provides tools for organizing collections of formulas into
structured design procedures with automatic documentation and result tracking.
"""

from typing import Any, Dict, List, Optional, Union
import pandas as pd

from .formula import EngineeringFunction
from .output import DisplayText
from .checks import EngineeringCheck


class EngineeringProcedure:
    """
    A design procedure that orchestrates multiple formulas and checks.
    
    Tracks calculations, checks, and generates documentation showing the
    complete design workflow.
    
    Example:
        procedure = EngineeringProcedure("Beam Flexure Check")
        procedure.add_title("Section Properties")
        procedure.add_computation(section_modulus)
        procedure.add_title("Bending Resistance")
        procedure.add_computation(factored_resistance)
    """
    
    def __init__(self, name: str) -> None:
        """
        Initialize a design procedure.
        
        Args:
            name: Name of the procedure
        """
        self.name = name
        self.procedure: List[Union[EngineeringFunction, DisplayText]] = []
        self.checks: Dict[int, EngineeringCheck] = {}
        
        # Result tracking
        self.results: pd.DataFrame = pd.DataFrame()
        self.status_log: pd.DataFrame = pd.DataFrame()
        self.check_log: pd.DataFrame = pd.DataFrame()
        self.utilizations: pd.DataFrame = pd.DataFrame()
    
    def add_computation(
        self,
        formula: EngineeringFunction,
        suppress_check: bool = False,
        show_util: bool = True
    ) -> None:
        """
        Add a formula computation to the procedure.
        
        Args:
            formula: Formula to add (must be already solved)
            suppress_check: If True, don't track checks
            show_util: If True, track utilization ratios
        """
        # Add the formula
        self.procedure.append(formula)
        self.results[formula.name] = formula.result
        
        # Add checks if present
        if not formula.checks or suppress_check:
            return
        
        for check in formula.checks:
            self.procedure.append(check)
            self.checks[check.check_id] = check
            
            check_key = f"{formula.name}_code:{check.check_id}"
            self.check_log[check_key] = check.applied_check_ids
            self.status_log[check_key] = check.applied_status_codes
            
            if check.check_id and show_util and check.util is not None:
                self.utilizations[check_key] = check.util
    
    def add_title(self, text: str, level: int = 3) -> None:
        """
        Add a section title to the procedure.
        
        Args:
            text: Title text
            level: Heading level (1-6)
        """
        self.procedure.append(DisplayText(text, level=level))
    
    def merge(self, other: 'EngineeringProcedure', title: Optional[str] = None, level: int = 2) -> None:
        """
        Merge another procedure into this one.
        
        Args:
            other: Procedure to merge
            title: Optional section title to add before merging
            level: Heading level for title (default 2)
        """
        if title:
            self.add_title(title, level=level)
        
        self.procedure.extend(other.procedure)
        self.results = pd.concat([self.results, other.results], axis=1)
    
    def generate_latex(self, index: int = 0) -> str:
        """
        Generate complete LaTeX documentation for the procedure.
        
        Args:
            index: Index for array-like results
            
        Returns:
            LaTeX string showing complete procedure with properly separated blocks
        """
        latex_parts = []
        
        for display_obj in self.procedure:
            # Each formula/check generates its own complete LaTeX block
            if isinstance(display_obj, DisplayText):
                # Add display text as markdown header based on level
                latex_parts.append(f"\n{display_obj.generate_markdown()}\n")
            elif isinstance(display_obj, EngineeringCheck):
                # Skip standalone checks - they're already included in formulas
                continue
            else:
                # Add formula description as title if it has one
                if hasattr(display_obj, 'desc') and display_obj.desc:
                    latex_parts.append(f"\n**{display_obj.desc}**\n")
                # Generate LaTeX for formula - this already includes align* wrapper and checks
                latex_str = display_obj.generate_latex(index)
                # Wrap in $$ delimiters for proper markdown rendering
                latex_parts.append(f"$$\n{latex_str}\n$$\n")
        
        return "\n".join(latex_parts)
    
    def generate_display_objects(self, index: int = 0) -> List[Any]:
        """
        Generate list of display objects for rendering.
        
        Useful for Jupyter/Streamlit where you want separate LaTeX/Markdown blocks.
        
        Args:
            index: Index for array-like results
            
        Returns:
            List of display objects
        """
        display_objects = []
        
        for item in self.procedure:
            if isinstance(item, EngineeringFunction):
                # Wrap in LaTeX display
                try:
                    from IPython.display import Latex
                    latex_str = f"\\begin{{align*}}{item.generate_latex(index)}\\end{{align*}}"
                    display_objects.append(Latex(latex_str))
                except ImportError:
                    # If IPython not available, just add the string
                    display_objects.append(item.generate_latex(index))
            
            elif isinstance(item, DisplayText):
                # Convert to Markdown
                try:
                    from IPython.display import Markdown
                    display_objects.append(Markdown(item.generate_markdown(index)))
                except ImportError:
                    display_objects.append(item.generate_markdown(index))
            
            elif isinstance(item, EngineeringCheck):
                # Add check LaTeX
                check_latex = item.generate_latex(index)
                if check_latex:
                    try:
                        from IPython.display import Latex
                        latex_str = f"\\begin{{align*}}{check_latex}\\end{{align*}}"
                        display_objects.append(Latex(latex_str))
                    except ImportError:
                        display_objects.append(check_latex)
        
        return display_objects
    
    def get_worst_status(self) -> pd.Series:
        """
        Get the worst status code for each row.
        
        Returns:
            Series with worst status for each element
        """
        if self.status_log.empty:
            return pd.Series()
        
        return self.status_log.max(axis=1)
    
    def get_worst_utilization(self) -> pd.Series:
        """
        Get the worst (maximum) utilization for each row.
        
        Returns:
            Series with worst utilization for each element
        """
        if self.utilizations.empty:
            return pd.Series()
        
        return self.utilizations.max(axis=1)
    
    def get_governing_check(self) -> pd.Series:
        """
        Get the governing (worst) check for each row.
        
        Returns:
            Series with check IDs of governing checks
        """
        if self.utilizations.empty:
            return pd.Series()
        
        return self.utilizations.idxmax(axis=1)
    
    def summary(self) -> pd.DataFrame:
        """
        Generate summary DataFrame with key results.
        
        Returns:
            DataFrame with results, status, and utilization
        """
        summary_df = self.results.copy()
        
        if not self.status_log.empty:
            summary_df['worst_status'] = self.get_worst_status()
        
        if not self.utilizations.empty:
            summary_df['worst_util'] = self.get_worst_utilization()
            summary_df['governing_check'] = self.get_governing_check()
        
        return summary_df
    
    def __repr__(self) -> str:
        n_formulas = sum(1 for item in self.procedure if isinstance(item, EngineeringFunction))
        n_checks = len(self.checks)
        return f"<EngineeringProcedure '{self.name}': {n_formulas} formulas, {n_checks} checks>"
