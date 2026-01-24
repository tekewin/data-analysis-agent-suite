"""Data transformation utilities for cleaning operations."""

from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
import re

from .utils import to_snake_case


@dataclass
class ChangeRecord:
    """Record of a single change made during transformation."""
    operation: str
    column: Optional[str]
    row_numbers: List[int]  # 1-indexed
    old_values: List[Any] = field(default_factory=list)
    new_values: List[Any] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'operation': self.operation,
            'column': self.column,
            'row_numbers': self.row_numbers,
            'affected_count': len(self.row_numbers),
            'old_values': self.old_values[:5],  # Limit samples
            'new_values': self.new_values[:5],
            'description': self.description,
        }


@dataclass
class TransformResult:
    """Result of a transformation operation."""
    df: pd.DataFrame
    changes: List[ChangeRecord] = field(default_factory=list)
    rows_affected: int = 0

    def add_change(self, change: ChangeRecord) -> None:
        """Add a change record."""
        self.changes.append(change)
        self.rows_affected += len(change.row_numbers)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'rows_affected': self.rows_affected,
            'changes': [c.to_dict() for c in self.changes],
        }


def _is_string_column(series: pd.Series) -> bool:
    """Check if a column contains string data."""
    dtype_str = str(series.dtype).lower()
    return dtype_str == 'object' or 'string' in dtype_str or dtype_str == 'str'


def trim_whitespace(df: pd.DataFrame) -> TransformResult:
    """
    Trim leading/trailing whitespace from all string columns.

    Args:
        df: DataFrame to clean

    Returns:
        TransformResult with cleaned DataFrame and change log
    """
    result = TransformResult(df=df.copy())

    for col in df.columns:
        if _is_string_column(df[col]):
            original = result.df[col].copy()

            # Strip whitespace, preserving NaN
            def strip_value(x):
                if pd.isna(x):
                    return x
                return str(x).strip()

            trimmed = result.df[col].apply(strip_value)

            # Find changed rows - compare original string to trimmed
            changed_indices = []
            for i, idx in enumerate(result.df.index):
                orig_val = original.iloc[i]
                trim_val = trimmed.iloc[i]
                if pd.notna(orig_val) and str(orig_val) != str(trim_val):
                    changed_indices.append(i)

            if changed_indices:
                row_numbers = [idx + 2 for idx in changed_indices]
                old_vals = [original.iloc[i] for i in changed_indices[:5]]
                new_vals = [trimmed.iloc[i] for i in changed_indices[:5]]

                result.df[col] = trimmed

                result.add_change(ChangeRecord(
                    operation='trim_whitespace',
                    column=col,
                    row_numbers=row_numbers,
                    old_values=[repr(v) for v in old_vals],
                    new_values=[repr(v) for v in new_vals],
                    description=f"Trimmed whitespace from {len(row_numbers)} values",
                ))

    return result


def standardize_column_names(df: pd.DataFrame) -> TransformResult:
    """
    Convert all column names to snake_case.

    Args:
        df: DataFrame with columns to rename

    Returns:
        TransformResult with renamed columns and change log
    """
    result = TransformResult(df=df.copy())

    old_names = list(df.columns)
    new_names = [to_snake_case(str(col)) for col in df.columns]

    # Handle duplicate names by appending numbers
    seen = {}
    unique_names = []
    for name in new_names:
        if name in seen:
            seen[name] += 1
            unique_names.append(f"{name}_{seen[name]}")
        else:
            seen[name] = 0
            unique_names.append(name)

    # Find changed names
    changed = [(old, new) for old, new in zip(old_names, unique_names) if old != new]

    if changed:
        result.df.columns = unique_names
        result.add_change(ChangeRecord(
            operation='standardize_column_names',
            column=None,
            row_numbers=[],
            old_values=[c[0] for c in changed[:5]],
            new_values=[c[1] for c in changed[:5]],
            description=f"Renamed {len(changed)} column(s) to snake_case",
        ))

    return result


def normalize_dates(
    df: pd.DataFrame,
    column: str,
    input_format: Optional[str] = None,
    output_format: str = '%Y-%m-%d',
    dayfirst: bool = False,
) -> TransformResult:
    """
    Normalize dates in a column to a consistent format.

    Args:
        df: DataFrame to modify
        column: Column name containing dates
        input_format: Optional strptime format for parsing (auto-detect if None)
        output_format: strftime format for output (default: ISO format)
        dayfirst: If True, interpret ambiguous dates as DD/MM (European style)

    Returns:
        TransformResult with normalized dates and change log
    """
    result = TransformResult(df=df.copy())

    if column not in df.columns:
        return result

    original = df[column].copy()

    try:
        # Parse dates
        if input_format:
            parsed = pd.to_datetime(df[column], format=input_format, errors='coerce')
        else:
            parsed = pd.to_datetime(df[column], dayfirst=dayfirst, errors='coerce')

        # Format to string
        formatted = parsed.dt.strftime(output_format)

        # Find changed rows (exclude NaT)
        changed_mask = (
            original.notna() &
            parsed.notna() &
            (original.astype(str) != formatted)
        )
        changed_indices = changed_mask[changed_mask].index.tolist()

        if changed_indices:
            row_numbers = [idx + 2 for idx in changed_indices]

            result.df[column] = formatted.where(parsed.notna(), original)

            result.add_change(ChangeRecord(
                operation='normalize_dates',
                column=column,
                row_numbers=row_numbers,
                old_values=original.iloc[changed_indices[:5]].tolist(),
                new_values=formatted.iloc[changed_indices[:5]].tolist(),
                description=f"Normalized {len(row_numbers)} dates to {output_format}",
            ))

    except Exception as e:
        # Log error but don't fail
        result.add_change(ChangeRecord(
            operation='normalize_dates',
            column=column,
            row_numbers=[],
            description=f"Date normalization failed: {str(e)}",
        ))

    return result


def parse_currency(
    df: pd.DataFrame,
    column: str,
    currency_symbol: Optional[str] = None,
) -> TransformResult:
    """
    Parse currency-formatted strings to numeric values.

    Handles:
    - $1,234.56 (US format)
    - EUR 1.234,56 (European format)
    - (1,234.56) (accounting negative)
    - -$1,234.56 (negative with symbol)

    Args:
        df: DataFrame to modify
        column: Column name containing currency values
        currency_symbol: Optional symbol to remove (auto-detect if None)

    Returns:
        TransformResult with parsed values and change log
    """
    result = TransformResult(df=df.copy())

    if column not in df.columns:
        return result

    original = df[column].copy()
    parsed_values = []

    for value in df[column]:
        if pd.isna(value):
            parsed_values.append(np.nan)
            continue

        s = str(value).strip()

        # Check for accounting negative format (parentheses)
        is_negative = s.startswith('(') and s.endswith(')')
        if is_negative:
            s = s[1:-1]

        # Remove currency symbols
        s = re.sub(r'[$€£¥]', '', s)

        # Detect format (European vs US)
        # European: 1.234,56 (dot as thousands, comma as decimal)
        # US: 1,234.56 (comma as thousands, dot as decimal)

        if ',' in s and '.' in s:
            # Both present - check which is last (that's the decimal)
            if s.rfind(',') > s.rfind('.'):
                # European format
                s = s.replace('.', '').replace(',', '.')
            else:
                # US format
                s = s.replace(',', '')
        elif ',' in s:
            # Only comma - could be thousands or decimal
            # If exactly 2 digits after comma, treat as decimal
            parts = s.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')

        # Remove spaces and other non-numeric chars except . and -
        s = re.sub(r'[^\d.\-]', '', s)

        # Check for negative sign
        if s.startswith('-'):
            is_negative = True
            s = s[1:]

        try:
            value_float = float(s)
            if is_negative:
                value_float = -value_float
            parsed_values.append(value_float)
        except (ValueError, TypeError):
            parsed_values.append(np.nan)

    # Create series with parsed values
    parsed_series = pd.Series(parsed_values, index=df.index)

    # Find changed rows
    changed_mask = (
        original.notna() &
        parsed_series.notna() &
        (original.astype(str) != parsed_series.astype(str))
    )
    changed_indices = changed_mask[changed_mask].index.tolist()

    if changed_indices:
        row_numbers = [idx + 2 for idx in changed_indices]

        result.df[column] = parsed_series

        result.add_change(ChangeRecord(
            operation='parse_currency',
            column=column,
            row_numbers=row_numbers,
            old_values=original.iloc[changed_indices[:5]].tolist(),
            new_values=parsed_series.iloc[changed_indices[:5]].tolist(),
            description=f"Parsed {len(row_numbers)} currency values to numeric",
        ))

    return result


def handle_duplicates(
    df: pd.DataFrame,
    strategy: str = 'remove',
    keep: str = 'first',
    subset: Optional[List[str]] = None,
) -> TransformResult:
    """
    Handle duplicate rows in the DataFrame.

    Args:
        df: DataFrame to deduplicate
        strategy: How to handle duplicates:
            - 'remove': Remove duplicate rows
            - 'flag': Add a column flagging duplicates
        keep: Which duplicate to keep ('first', 'last', or False for none)
        subset: Columns to consider for duplicates (None = all columns)

    Returns:
        TransformResult with deduplicated DataFrame and change log
    """
    result = TransformResult(df=df.copy())

    # Find duplicate rows
    if keep == 'none':
        duplicates = df.duplicated(subset=subset, keep=False)
    else:
        duplicates = df.duplicated(subset=subset, keep=keep)

    duplicate_indices = duplicates[duplicates].index.tolist()

    if not duplicate_indices:
        return result

    row_numbers = [idx + 2 for idx in duplicate_indices]

    if strategy == 'remove':
        result.df = df[~duplicates].reset_index(drop=True)

        result.add_change(ChangeRecord(
            operation='remove_duplicates',
            column=None,
            row_numbers=row_numbers,
            description=f"Removed {len(row_numbers)} duplicate row(s)",
        ))

    elif strategy == 'flag':
        result.df['is_duplicate'] = duplicates

        result.add_change(ChangeRecord(
            operation='flag_duplicates',
            column='is_duplicate',
            row_numbers=row_numbers,
            description=f"Flagged {len(row_numbers)} duplicate row(s) in 'is_duplicate' column",
        ))

    return result


def handle_missing_values(
    df: pd.DataFrame,
    column: str,
    strategy: str = 'drop',
    fill_value: Optional[Any] = None,
) -> TransformResult:
    """
    Handle missing values in a column.

    Args:
        df: DataFrame to modify
        column: Column name to process
        strategy: How to handle missing values:
            - 'drop': Remove rows with missing values
            - 'mean': Fill with column mean (numeric only)
            - 'median': Fill with column median (numeric only)
            - 'mode': Fill with most frequent value
            - 'zero': Fill with 0
            - 'forward': Forward fill
            - 'backward': Backward fill
            - 'custom': Fill with fill_value
        fill_value: Value to use when strategy is 'custom'

    Returns:
        TransformResult with handled missing values and change log
    """
    result = TransformResult(df=df.copy())

    if column not in df.columns:
        return result

    missing_mask = df[column].isna()
    missing_indices = missing_mask[missing_mask].index.tolist()

    if not missing_indices:
        return result

    row_numbers = [idx + 2 for idx in missing_indices]

    if strategy == 'drop':
        result.df = df[~missing_mask].reset_index(drop=True)
        result.add_change(ChangeRecord(
            operation='drop_missing',
            column=column,
            row_numbers=row_numbers,
            description=f"Dropped {len(row_numbers)} row(s) with missing values",
        ))

    else:
        # Calculate fill value based on strategy
        if strategy == 'mean':
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            computed_fill = numeric_col.mean()
        elif strategy == 'median':
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            computed_fill = numeric_col.median()
        elif strategy == 'mode':
            mode_result = df[column].mode()
            computed_fill = mode_result.iloc[0] if len(mode_result) > 0 else None
        elif strategy == 'zero':
            computed_fill = 0
        elif strategy == 'forward':
            result.df[column] = df[column].ffill()
            result.add_change(ChangeRecord(
                operation='forward_fill',
                column=column,
                row_numbers=row_numbers,
                description=f"Forward-filled {len(row_numbers)} missing value(s)",
            ))
            return result
        elif strategy == 'backward':
            result.df[column] = df[column].bfill()
            result.add_change(ChangeRecord(
                operation='backward_fill',
                column=column,
                row_numbers=row_numbers,
                description=f"Backward-filled {len(row_numbers)} missing value(s)",
            ))
            return result
        elif strategy == 'custom':
            computed_fill = fill_value
        else:
            return result

        if computed_fill is not None and not (isinstance(computed_fill, float) and np.isnan(computed_fill)):
            result.df[column] = df[column].fillna(computed_fill)
            result.add_change(ChangeRecord(
                operation=f'fill_missing_{strategy}',
                column=column,
                row_numbers=row_numbers,
                new_values=[computed_fill] * min(5, len(row_numbers)),
                description=f"Filled {len(row_numbers)} missing value(s) with {strategy} ({computed_fill})",
            ))

    return result


def handle_outliers(
    df: pd.DataFrame,
    column: str,
    strategy: str = 'flag',
    method: str = 'iqr',
    threshold: float = 1.5,
) -> TransformResult:
    """
    Handle outliers in a numeric column.

    Args:
        df: DataFrame to modify
        column: Column name to process
        strategy: How to handle outliers:
            - 'flag': Add a column flagging outliers
            - 'remove': Remove rows with outliers
            - 'cap': Cap outliers at threshold bounds
        method: Detection method ('iqr' or 'zscore')
        threshold: Threshold for detection (1.5 for IQR, 3 for z-score)

    Returns:
        TransformResult with handled outliers and change log
    """
    result = TransformResult(df=df.copy())

    if column not in df.columns:
        return result

    # Convert to numeric
    numeric_col = pd.to_numeric(df[column], errors='coerce')
    non_null = numeric_col.dropna()

    if len(non_null) < 10:
        return result

    # Calculate bounds
    if method == 'iqr':
        q1 = non_null.quantile(0.25)
        q3 = non_null.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
    elif method == 'zscore':
        mean = non_null.mean()
        std = non_null.std()
        lower_bound = mean - threshold * std
        upper_bound = mean + threshold * std
    else:
        return result

    # Find outliers
    outlier_mask = (numeric_col < lower_bound) | (numeric_col > upper_bound)
    outlier_indices = outlier_mask[outlier_mask].index.tolist()

    if not outlier_indices:
        return result

    row_numbers = [idx + 2 for idx in outlier_indices]

    if strategy == 'flag':
        flag_col = f'{column}_is_outlier'
        result.df[flag_col] = outlier_mask

        result.add_change(ChangeRecord(
            operation='flag_outliers',
            column=flag_col,
            row_numbers=row_numbers,
            description=f"Flagged {len(row_numbers)} outlier(s) in '{flag_col}' column",
        ))

    elif strategy == 'remove':
        result.df = df[~outlier_mask].reset_index(drop=True)

        result.add_change(ChangeRecord(
            operation='remove_outliers',
            column=column,
            row_numbers=row_numbers,
            old_values=numeric_col.iloc[outlier_indices[:5]].tolist(),
            description=f"Removed {len(row_numbers)} row(s) with outliers",
        ))

    elif strategy == 'cap':
        capped = numeric_col.clip(lower=lower_bound, upper=upper_bound)
        result.df[column] = capped

        result.add_change(ChangeRecord(
            operation='cap_outliers',
            column=column,
            row_numbers=row_numbers,
            old_values=numeric_col.iloc[outlier_indices[:5]].tolist(),
            new_values=capped.iloc[outlier_indices[:5]].tolist(),
            description=f"Capped {len(row_numbers)} outlier(s) to [{lower_bound:.2f}, {upper_bound:.2f}]",
        ))

    return result


def fix_encoding(df: pd.DataFrame) -> TransformResult:
    """
    Attempt to fix common encoding issues (mojibake) in text columns.

    Args:
        df: DataFrame to clean

    Returns:
        TransformResult with fixed encoding and change log
    """
    result = TransformResult(df=df.copy())

    # Common mojibake replacements (UTF-8 interpreted as Latin-1)
    replacements = {
        'Ã©': 'é',
        'Ã¨': 'è',
        'Ã ': 'à',
        'Ã¢': 'â',
        'Ã§': 'ç',
        'Ã¼': 'ü',
        'Ã¶': 'ö',
        'Ã¤': 'ä',
        'Ã±': 'ñ',
        'â€™': "'",
        'â€œ': '"',
        'â€': '—',
        'â€"': '–',
        'Â ': ' ',
        'Â': '',
    }

    for col in df.columns:
        if _is_string_column(df[col]):
            original = result.df[col].copy()
            fixed = result.df[col].copy().astype(str)

            for bad, good in replacements.items():
                fixed = fixed.str.replace(bad, good, regex=False)

            # Find changed rows
            changed_indices = []
            for i in range(len(result.df)):
                orig_val = original.iloc[i]
                fixed_val = fixed.iloc[i]
                if pd.notna(orig_val) and str(orig_val) != str(fixed_val):
                    changed_indices.append(i)

            if changed_indices:
                row_numbers = [idx + 2 for idx in changed_indices]

                result.df[col] = fixed

                result.add_change(ChangeRecord(
                    operation='fix_encoding',
                    column=col,
                    row_numbers=row_numbers,
                    old_values=original.iloc[changed_indices[:5]].tolist(),
                    new_values=fixed.iloc[changed_indices[:5]].tolist(),
                    description=f"Fixed encoding issues in {len(row_numbers)} values",
                ))

    return result
