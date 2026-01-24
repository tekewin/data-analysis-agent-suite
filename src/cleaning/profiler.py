"""Data profiling utilities for analyzing DataFrame characteristics."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


@dataclass
class ColumnProfile:
    """Profile information for a single column."""
    name: str
    dtype: str
    inferred_type: str  # 'numeric', 'text', 'date', 'boolean', 'mixed'
    total_count: int
    missing_count: int
    unique_count: int
    sample_values: List[Any] = field(default_factory=list)

    # Numeric-specific stats
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_value: Optional[float] = None

    # Text-specific stats
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None

    # Date-specific info
    date_formats_detected: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'dtype': self.dtype,
            'inferred_type': self.inferred_type,
            'total_count': self.total_count,
            'missing_count': self.missing_count,
            'missing_percentage': round(self.missing_count / self.total_count * 100, 2) if self.total_count > 0 else 0,
            'unique_count': self.unique_count,
            'sample_values': self.sample_values[:5],  # Limit samples
            'min_value': self.min_value,
            'max_value': self.max_value,
            'mean_value': self.mean_value,
            'median_value': self.median_value,
            'std_value': self.std_value,
            'min_length': self.min_length,
            'max_length': self.max_length,
            'avg_length': self.avg_length,
            'date_formats_detected': self.date_formats_detected,
        }


@dataclass
class DataProfile:
    """Complete profile of a DataFrame."""
    total_rows: int
    total_columns: int
    columns: List[ColumnProfile]
    duplicate_row_count: int = 0
    memory_usage_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total_rows': self.total_rows,
            'total_columns': self.total_columns,
            'duplicate_row_count': self.duplicate_row_count,
            'memory_usage_bytes': self.memory_usage_bytes,
            'columns': [col.to_dict() for col in self.columns],
        }

    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            f"Dataset: {self.total_rows:,} rows × {self.total_columns} columns",
            f"Memory: {self.memory_usage_bytes / 1024:.1f} KB",
            f"Duplicates: {self.duplicate_row_count:,} rows",
            "",
            "Columns:",
        ]

        for col in self.columns:
            missing_pct = (col.missing_count / col.total_count * 100) if col.total_count > 0 else 0
            lines.append(
                f"  • {col.name}: {col.inferred_type} "
                f"({col.unique_count:,} unique, {missing_pct:.1f}% missing)"
            )

        return "\n".join(lines)


def infer_column_type(series: pd.Series) -> str:
    """
    Infer the semantic type of a column.

    Returns one of: 'numeric', 'text', 'date', 'boolean', 'mixed'
    """
    # Drop missing values for analysis
    non_null = series.dropna()

    if len(non_null) == 0:
        return 'text'  # Default for empty columns

    # Check if pandas already detected a specific type
    dtype_str = str(series.dtype).lower()

    if 'datetime' in dtype_str:
        return 'date'
    elif 'bool' in dtype_str:
        return 'boolean'
    elif 'int' in dtype_str or 'float' in dtype_str:
        return 'numeric'

    # For string-like dtypes (object, string, str), try to infer
    is_string_like = (
        dtype_str == 'object' or
        'string' in dtype_str or
        dtype_str == 'str'
    )

    if is_string_like:
        # Sample for performance on large datasets
        sample = non_null.head(100)

        # Check for boolean-like values
        bool_values = {'true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n'}
        if all(str(v).lower().strip() in bool_values for v in sample):
            return 'boolean'

        # Check for date-like values
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}',  # ISO date
            r'^\d{1,2}/\d{1,2}/\d{2,4}',  # US/EU date
            r'^\d{1,2}-\d{1,2}-\d{2,4}',  # Hyphenated date
        ]
        import re
        for pattern in date_patterns:
            if sum(1 for v in sample if re.match(pattern, str(v).strip())) >= len(sample) * 0.8:
                return 'date'

        # Check for numeric-like values (including currency)
        numeric_count = 0
        for v in sample:
            s = str(v).strip()
            # Remove currency symbols and formatting
            cleaned = re.sub(r'[$€£¥,\s()]', '', s)
            try:
                float(cleaned)
                numeric_count += 1
            except (ValueError, TypeError):
                pass

        if numeric_count >= len(sample) * 0.8:
            return 'numeric'

        # Default to text
        return 'text'

    return 'mixed'


def detect_date_formats(series: pd.Series) -> List[str]:
    """
    Detect the date formats present in a series.

    Returns a list of detected format patterns.
    """
    import re

    formats = set()
    sample = series.dropna().head(100)

    format_patterns = {
        r'^\d{4}-\d{2}-\d{2}$': 'YYYY-MM-DD',
        r'^\d{4}/\d{2}/\d{2}$': 'YYYY/MM/DD',
        r'^\d{2}-\d{2}-\d{4}$': 'DD-MM-YYYY or MM-DD-YYYY',
        r'^\d{2}/\d{2}/\d{4}$': 'DD/MM/YYYY or MM/DD/YYYY',
        r'^\d{1,2}/\d{1,2}/\d{4}$': 'D/M/YYYY or M/D/YYYY',
        r'^\d{1,2}-\d{1,2}-\d{4}$': 'D-M-YYYY or M-D-YYYY',
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}': 'ISO datetime',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}': 'YYYY-MM-DD HH:MM:SS',
    }

    for value in sample:
        s = str(value).strip()
        for pattern, fmt in format_patterns.items():
            if re.match(pattern, s):
                formats.add(fmt)
                break

    return list(formats)


def profile_column(series: pd.Series) -> ColumnProfile:
    """
    Generate a profile for a single column.

    Args:
        series: The pandas Series to profile

    Returns:
        ColumnProfile with detailed statistics
    """
    non_null = series.dropna()
    inferred_type = infer_column_type(series)

    profile = ColumnProfile(
        name=series.name or 'unnamed',
        dtype=str(series.dtype),
        inferred_type=inferred_type,
        total_count=len(series),
        missing_count=series.isna().sum(),
        unique_count=series.nunique(),
        sample_values=non_null.head(5).tolist() if len(non_null) > 0 else [],
    )

    # Add type-specific stats
    if inferred_type == 'numeric':
        try:
            # Try to convert to numeric for stats
            numeric_series = pd.to_numeric(
                non_null.astype(str).str.replace(r'[$€£¥,\s()]', '', regex=True),
                errors='coerce'
            ).dropna()

            if len(numeric_series) > 0:
                profile.min_value = float(numeric_series.min())
                profile.max_value = float(numeric_series.max())
                profile.mean_value = round(float(numeric_series.mean()), 2)
                profile.median_value = float(numeric_series.median())
                profile.std_value = round(float(numeric_series.std()), 2)
        except Exception:
            pass

    elif inferred_type == 'text':
        try:
            lengths = non_null.astype(str).str.len()
            if len(lengths) > 0:
                profile.min_length = int(lengths.min())
                profile.max_length = int(lengths.max())
                profile.avg_length = round(float(lengths.mean()), 1)
        except Exception:
            pass

    elif inferred_type == 'date':
        profile.date_formats_detected = detect_date_formats(series)

    return profile


def profile_dataframe(df: pd.DataFrame) -> DataProfile:
    """
    Generate a complete profile for a DataFrame.

    This analyzes each column and provides summary statistics,
    type inference, and quality metrics for the agent to use.

    Args:
        df: The DataFrame to profile

    Returns:
        DataProfile with complete analysis

    Example:
        >>> profile = profile_dataframe(df)
        >>> print(profile.summary())
    """
    columns = [profile_column(df[col]) for col in df.columns]

    profile = DataProfile(
        total_rows=len(df),
        total_columns=len(df.columns),
        columns=columns,
        duplicate_row_count=df.duplicated().sum(),
        memory_usage_bytes=df.memory_usage(deep=True).sum(),
    )

    return profile
