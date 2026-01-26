"""
Table management utilities for design code reference data.

This module provides tools for loading, caching, and querying JSON tables
containing design code data (material properties, factors, etc.).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd


class TableCache:
    """Simple cache for loaded tables."""
    
    _cache: Dict[str, Any] = {}
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Get table from cache."""
        return cls._cache.get(key)
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Store table in cache."""
        cls._cache[key] = value
    
    @classmethod
    def clear(cls) -> None:
        """Clear all cached tables."""
        cls._cache.clear()


def load_table(
    file_path: Union[str, Path],
    use_cache: bool = True
) -> Union[Dict, pd.DataFrame]:
    """
    Load a JSON table from file.
    
    Args:
        file_path: Path to JSON file
        use_cache: Whether to use caching (default True)
        
    Returns:
        Loaded table as dict or DataFrame
        
    Example:
        table = load_table("tables/CSA O86-24_T7-2.json")
    """
    file_path = Path(file_path)
    cache_key = str(file_path.absolute())
    
    # Check cache
    if use_cache:
        cached = TableCache.get(cache_key)
        if cached is not None:
            return cached
    
    # Load from file
    if not file_path.exists():
        raise FileNotFoundError(f"Table file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Cache the result
    if use_cache:
        TableCache.set(cache_key, data)
    
    return data


def table_to_dataframe(table: Dict) -> pd.DataFrame:
    """
    Convert a table dict to pandas DataFrame.
    
    Args:
        table: Table dictionary
        
    Returns:
        DataFrame representation
    """
    if isinstance(table, pd.DataFrame):
        return table
    
    # Try to create DataFrame from dict
    try:
        df = pd.DataFrame(table)
    except (ValueError, TypeError):
        # If direct conversion fails, try different approaches
        if 'data' in table:
            df = pd.DataFrame(table['data'])
        elif 'rows' in table:
            df = pd.DataFrame(table['rows'])
        else:
            # Assume it's a simple key-value table
            df = pd.DataFrame.from_dict(table, orient='index')
    
    return df


def lookup_value(
    table: Union[Dict, pd.DataFrame],
    key: Any,
    column: Optional[str] = None
) -> Any:
    """
    Look up a value in a table.
    
    Args:
        table: Table dict or DataFrame
        key: Key to look up
        column: Column name (for DataFrames)
        
    Returns:
        Looked up value
        
    Example:
        # Simple dict lookup
        value = lookup_value(table, "Grade_1")
        
        # DataFrame lookup
        df = table_to_dataframe(table)
        value = lookup_value(df, "D.Fir-L", "fb_MPa")
    """
    if isinstance(table, pd.DataFrame):
        if column is None:
            raise ValueError("column parameter required for DataFrame lookups")
        return table.loc[key, column]
    else:
        # Dict lookup
        return table[key]


def interpolate_table(
    table: pd.DataFrame,
    x_column: str,
    y_column: str,
    x_value: float,
    method: str = 'linear'
) -> float:
    """
    Interpolate a value from a table.
    
    Args:
        table: DataFrame with tabulated values
        x_column: Name of independent variable column
        y_column: Name of dependent variable column
        x_value: Value to interpolate at
        method: Interpolation method ('linear', 'nearest', 'cubic')
        
    Returns:
        Interpolated value
        
    Example:
        E = interpolate_table(
            table=props_table,
            x_column="depth_mm",
            y_column="E_MPa",
            x_value=241,
            method='linear'
        )
    """
    # Sort by x column
    sorted_table = table.sort_values(by=x_column)
    
    # Extract arrays
    x = sorted_table[x_column].values
    y = sorted_table[y_column].values
    
    # Interpolate
    if method == 'linear':
        result = float(np.interp(x_value, x, y))
    elif method == 'nearest':
        idx = (np.abs(x - x_value)).argmin()
        result = float(y[idx])
    elif method == 'cubic':
        from scipy.interpolate import interp1d
        f = interp1d(x, y, kind='cubic', fill_value='extrapolate')
        result = float(f(x_value))
    else:
        raise ValueError(f"Unknown interpolation method: {method}")
    
    return result


class DesignTable:
    """
    Wrapper class for design code tables with convenience methods.
    
    Example:
        table = DesignTable.from_file("tables/CSA O86-24_T7-2.json")
        fb = table.lookup("D.Fir-L", "fb_MPa")
    """
    
    def __init__(
        self,
        data: Union[Dict, pd.DataFrame],
        name: str = "",
        source: str = ""
    ) -> None:
        """
        Initialize a design table.
        
        Args:
            data: Table data (dict or DataFrame)
            name: Table name
            source: Source reference (e.g., "CSA O86-24 Table 7.2")
        """
        self.name = name
        self.source = source
        
        # Convert to DataFrame if dict
        if isinstance(data, dict):
            self.data = table_to_dataframe(data)
        else:
            self.data = data
    
    @classmethod
    def from_file(
        cls,
        file_path: Union[str, Path],
        name: str = "",
        source: str = "",
        use_cache: bool = True
    ) -> "DesignTable":
        """
        Load a design table from JSON file.
        
        Args:
            file_path: Path to JSON file
            name: Table name
            source: Source reference
            use_cache: Whether to cache the table
            
        Returns:
            DesignTable instance
        """
        data = load_table(file_path, use_cache=use_cache)
        
        # Extract name and source from data if present
        if isinstance(data, dict):
            name = name or data.get('name', '')
            source = source or data.get('source', '')
        
        return cls(data, name=name, source=source)
    
    def lookup(self, key: Any, column: str) -> Any:
        """
        Look up a value in the table.
        
        Args:
            key: Row key
            column: Column name
            
        Returns:
            Value at (key, column)
        """
        return lookup_value(self.data, key, column)
    
    def interpolate(
        self,
        x_column: str,
        y_column: str,
        x_value: float,
        method: str = 'linear'
    ) -> float:
        """
        Interpolate a value from the table.
        
        Args:
            x_column: Independent variable column
            y_column: Dependent variable column
            x_value: Value to interpolate at
            method: Interpolation method
            
        Returns:
            Interpolated value
        """
        return interpolate_table(self.data, x_column, y_column, x_value, method)
    
    def filter(self, **conditions) -> pd.DataFrame:
        """
        Filter table rows by conditions.
        
        Args:
            **conditions: Column=value conditions
            
        Returns:
            Filtered DataFrame
            
        Example:
            table.filter(grade="No.1", species="D.Fir-L")
        """
        result = self.data.copy()
        
        for column, value in conditions.items():
            result = result[result[column] == value]
        
        return result
    
    def __repr__(self) -> str:
        name_str = f" '{self.name}'" if self.name else ""
        source_str = f" from {self.source}" if self.source else ""
        return f"<DesignTable{name_str}{source_str}: {self.data.shape[0]} rows x {self.data.shape[1]} cols>"


# For backward compatibility
import numpy as np  # Used by interpolate_table
