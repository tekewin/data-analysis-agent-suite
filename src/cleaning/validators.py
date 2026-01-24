"""Data validation utilities for detecting issues in DataFrames."""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import re


class IssueSeverity(Enum):
    """Severity levels for detected issues."""
    CRITICAL = "critical"  # Blocks analysis, must fix
    WARNING = "warning"    # May affect results
    INFO = "info"          # Cosmetic or minor


class IssueType(Enum):
    """Types of issues that can be detected."""
    DUPLICATE_ROWS = "duplicate_rows"
    MISSING_VALUES = "missing_values"
    INCONSISTENT_DATES = "inconsistent_dates"
    CURRENCY_VALUES = "currency_values"
    WHITESPACE = "whitespace"
    NON_SNAKE_CASE = "non_snake_case"
    OUTLIERS = "outliers"
    ENCODING_ISSUES = "encoding_issues"
    MIXED_TYPES = "mixed_types"


@dataclass
class ValidationIssue:
    """A detected issue in the data."""
    issue_type: IssueType
    severity: IssueSeverity
    column: Optional[str]  # None for row-level issues
    row_numbers: List[int]  # 1-indexed for human readability
    description: str
    sample_values: List[Any] = field(default_factory=list)
    auto_fixable: bool = False
    fix_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'issue_type': self.issue_type.value,
            'severity': self.severity.value,
            'column': self.column,
            'row_numbers': self.row_numbers,
            'affected_count': len(self.row_numbers),
            'description': self.description,
            'sample_values': self.sample_values[:5],
            'auto_fixable': self.auto_fixable,
            'fix_description': self.fix_description,
        }


@dataclass
class ValidationResult:
    """Complete validation result for a DataFrame."""
    issues: List[ValidationIssue] = field(default_factory=list)
    total_rows_affected: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    @property
    def total_issues(self) -> int:
        """Return total number of issues."""
        return len(self.issues)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add an issue and update counts."""
        self.issues.append(issue)
        self.total_rows_affected += len(issue.row_numbers)

        if issue.severity == IssueSeverity.CRITICAL:
            self.critical_count += 1
        elif issue.severity == IssueSeverity.WARNING:
            self.warning_count += 1
        else:
            self.info_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total_issues': len(self.issues),
            'total_rows_affected': self.total_rows_affected,
            'critical_count': self.critical_count,
            'warning_count': self.warning_count,
            'info_count': self.info_count,
            'issues': [issue.to_dict() for issue in self.issues],
        }

    def summary(self) -> str:
        """Generate a human-readable summary."""
        if not self.issues:
            return "No issues detected."

        lines = [
            f"Found {len(self.issues)} issue(s):",
            f"  • Critical: {self.critical_count}",
            f"  • Warnings: {self.warning_count}",
            f"  • Info: {self.info_count}",
            "",
        ]

        # Group by severity
        for severity in [IssueSeverity.CRITICAL, IssueSeverity.WARNING, IssueSeverity.INFO]:
            severity_issues = [i for i in self.issues if i.severity == severity]
            if severity_issues:
                lines.append(f"{severity.value.upper()}:")
                for issue in severity_issues:
                    col_info = f" in '{issue.column}'" if issue.column else ""
                    lines.append(f"  [{issue.issue_type.value}]{col_info}: {issue.description}")

        return "\n".join(lines)


def find_duplicates(df: pd.DataFrame) -> Optional[ValidationIssue]:
    """
    Find duplicate rows in the DataFrame.

    Returns:
        ValidationIssue if duplicates found, None otherwise
    """
    duplicates = df.duplicated(keep='first')
    duplicate_indices = duplicates[duplicates].index.tolist()

    if not duplicate_indices:
        return None

    # Convert to 1-indexed row numbers (add 2 for header + 0-index)
    row_numbers = [idx + 2 for idx in duplicate_indices]

    return ValidationIssue(
        issue_type=IssueType.DUPLICATE_ROWS,
        severity=IssueSeverity.WARNING,
        column=None,
        row_numbers=row_numbers,
        description=f"{len(row_numbers)} duplicate row(s) found",
        sample_values=df.iloc[duplicate_indices[:3]].to_dict('records') if duplicate_indices else [],
        auto_fixable=False,
        fix_description="Options: remove duplicates, keep first, keep last, or flag for review",
    )


def find_missing_values(df: pd.DataFrame) -> List[ValidationIssue]:
    """
    Find missing values in each column.

    Returns:
        List of ValidationIssue for each column with missing values
    """
    issues = []

    for col in df.columns:
        missing_mask = df[col].isna()
        missing_indices = missing_mask[missing_mask].index.tolist()

        if not missing_indices:
            continue

        row_numbers = [idx + 2 for idx in missing_indices]
        missing_pct = len(missing_indices) / len(df) * 100

        # Determine severity based on percentage
        if missing_pct > 50:
            severity = IssueSeverity.CRITICAL
        elif missing_pct > 10:
            severity = IssueSeverity.WARNING
        else:
            severity = IssueSeverity.INFO

        issues.append(ValidationIssue(
            issue_type=IssueType.MISSING_VALUES,
            severity=severity,
            column=col,
            row_numbers=row_numbers,
            description=f"{len(row_numbers)} missing value(s) ({missing_pct:.1f}%)",
            auto_fixable=False,
            fix_description="Options: fill with mean/median/mode, drop rows, or use custom value",
        ))

    return issues


def find_date_issues(df: pd.DataFrame) -> List[ValidationIssue]:
    """
    Find inconsistent date formats in columns.

    Returns:
        List of ValidationIssue for columns with date format inconsistencies
    """
    issues = []

    # Common date patterns
    date_patterns = {
        'iso': r'^\d{4}-\d{2}-\d{2}',
        'us_slash': r'^\d{1,2}/\d{1,2}/\d{4}',
        'eu_slash': r'^\d{1,2}/\d{1,2}/\d{4}',  # Same pattern, different interpretation
        'us_dash': r'^\d{1,2}-\d{1,2}-\d{4}',
        'eu_dash': r'^\d{1,2}-\d{1,2}-\d{4}',
    }

    for col in df.columns:
        if df[col].dtype == 'object':
            non_null = df[col].dropna()
            if len(non_null) == 0:
                continue

            # Check if any values match date patterns
            sample = non_null.head(100)
            format_counts = {}

            for idx, value in sample.items():
                s = str(value).strip()
                for fmt_name, pattern in date_patterns.items():
                    if re.match(pattern, s):
                        format_counts[fmt_name] = format_counts.get(fmt_name, 0) + 1
                        break

            # If we detect date patterns, check for ambiguous formats
            if format_counts:
                total_dates = sum(format_counts.values())
                if total_dates >= len(sample) * 0.5:  # At least 50% are dates
                    # Check for ambiguous dates (e.g., 01/02/2024)
                    ambiguous_rows = []

                    for idx, value in non_null.items():
                        s = str(value).strip()
                        # Check for M/D/YYYY or D/M/YYYY ambiguity
                        match = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})', s)
                        if match:
                            day_or_month = int(match.group(1))
                            month_or_day = int(match.group(2))
                            # Ambiguous if both could be month (1-12)
                            if day_or_month <= 12 and month_or_day <= 12:
                                ambiguous_rows.append(idx + 2)

                    if ambiguous_rows:
                        issues.append(ValidationIssue(
                            issue_type=IssueType.INCONSISTENT_DATES,
                            severity=IssueSeverity.WARNING,
                            column=col,
                            row_numbers=ambiguous_rows[:100],  # Limit for performance
                            description=f"Ambiguous date format detected (could be MM/DD or DD/MM)",
                            sample_values=non_null.head(5).tolist(),
                            auto_fixable=False,
                            fix_description="Please specify the date format (MM/DD/YYYY or DD/MM/YYYY)",
                        ))

    return issues


def _is_string_column(series: pd.Series) -> bool:
    """Check if a column contains string data."""
    dtype_str = str(series.dtype).lower()
    return dtype_str == 'object' or 'string' in dtype_str or dtype_str == 'str'


def find_currency_values(df: pd.DataFrame) -> List[ValidationIssue]:
    """
    Find columns containing currency-formatted values.

    Returns:
        List of ValidationIssue for columns with currency formatting
    """
    issues = []
    currency_pattern = r'^[\$€£¥]\s*[\d,]+\.?\d*$|^\([\$€£¥]?\s*[\d,]+\.?\d*\)$|^[\d,]+\.?\d*\s*[\$€£¥]$'

    for col in df.columns:
        if _is_string_column(df[col]):
            non_null = df[col].dropna()
            if len(non_null) == 0:
                continue

            currency_rows = []
            sample_values = []

            for i, (idx, value) in enumerate(non_null.items()):
                s = str(value).strip()
                if re.match(currency_pattern, s):
                    currency_rows.append(int(idx) + 2 if isinstance(idx, (int, np.integer)) else i + 2)
                    if len(sample_values) < 5:
                        sample_values.append(s)

            if currency_rows and len(currency_rows) >= len(non_null) * 0.5:
                issues.append(ValidationIssue(
                    issue_type=IssueType.CURRENCY_VALUES,
                    severity=IssueSeverity.INFO,
                    column=col,
                    row_numbers=currency_rows,
                    description=f"Currency formatting detected in {len(currency_rows)} values",
                    sample_values=sample_values,
                    auto_fixable=True,
                    fix_description="Will parse to numeric values (removing symbols and formatting)",
                ))

    return issues


def find_whitespace_issues(df: pd.DataFrame) -> List[ValidationIssue]:
    """
    Find columns with leading/trailing whitespace.

    Returns:
        List of ValidationIssue for columns with whitespace issues
    """
    issues = []

    for col in df.columns:
        if _is_string_column(df[col]):
            non_null = df[col].dropna()
            if len(non_null) == 0:
                continue

            whitespace_rows = []
            sample_values = []

            for i, (idx, value) in enumerate(non_null.items()):
                s = str(value)
                if s != s.strip():
                    whitespace_rows.append(int(idx) + 2 if isinstance(idx, (int, np.integer)) else i + 2)
                    if len(sample_values) < 5:
                        sample_values.append(repr(s))  # Show whitespace

            if whitespace_rows:
                issues.append(ValidationIssue(
                    issue_type=IssueType.WHITESPACE,
                    severity=IssueSeverity.INFO,
                    column=col,
                    row_numbers=whitespace_rows,
                    description=f"Leading/trailing whitespace in {len(whitespace_rows)} values",
                    sample_values=sample_values,
                    auto_fixable=True,
                    fix_description="Will trim whitespace from all values",
                ))

    return issues


def find_column_name_issues(df: pd.DataFrame) -> Optional[ValidationIssue]:
    """
    Find column names that are not in snake_case.

    Returns:
        ValidationIssue if non-snake_case names found, None otherwise
    """
    non_snake_case = []

    for col in df.columns:
        # Check if already snake_case
        snake_pattern = r'^[a-z][a-z0-9_]*$'
        if not re.match(snake_pattern, str(col)):
            non_snake_case.append(str(col))

    if not non_snake_case:
        return None

    return ValidationIssue(
        issue_type=IssueType.NON_SNAKE_CASE,
        severity=IssueSeverity.INFO,
        column=None,
        row_numbers=[],  # Column-level issue
        description=f"{len(non_snake_case)} column name(s) not in snake_case",
        sample_values=non_snake_case[:5],
        auto_fixable=True,
        fix_description="Will convert column names to snake_case",
    )


def find_outliers(
    df: pd.DataFrame,
    method: str = 'iqr',
    threshold: float = 1.5
) -> List[ValidationIssue]:
    """
    Find outliers in numeric columns.

    Args:
        df: DataFrame to analyze
        method: Detection method ('iqr' or 'zscore')
        threshold: Threshold for outlier detection (1.5 for IQR, 3 for z-score)

    Returns:
        List of ValidationIssue for columns with outliers
    """
    issues = []

    for col in df.columns:
        # Try to convert to numeric
        numeric_col = pd.to_numeric(df[col], errors='coerce')
        non_null = numeric_col.dropna()

        if len(non_null) < 10:  # Need sufficient data
            continue

        outlier_indices = []

        if method == 'iqr':
            q1 = non_null.quantile(0.25)
            q3 = non_null.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            outlier_mask = (numeric_col < lower_bound) | (numeric_col > upper_bound)
            outlier_indices = outlier_mask[outlier_mask].index.tolist()

        elif method == 'zscore':
            mean = non_null.mean()
            std = non_null.std()
            if std > 0:
                z_scores = (numeric_col - mean) / std
                outlier_mask = z_scores.abs() > threshold
                outlier_indices = outlier_mask[outlier_mask].index.tolist()

        if outlier_indices:
            row_numbers = [idx + 2 for idx in outlier_indices]
            outlier_values = numeric_col.iloc[outlier_indices].head(5).tolist()

            issues.append(ValidationIssue(
                issue_type=IssueType.OUTLIERS,
                severity=IssueSeverity.WARNING,
                column=col,
                row_numbers=row_numbers,
                description=f"{len(outlier_indices)} potential outlier(s) detected",
                sample_values=outlier_values,
                auto_fixable=False,
                fix_description="Options: flag for review, remove, or cap at bounds",
            ))

    return issues


def find_encoding_issues(df: pd.DataFrame) -> List[ValidationIssue]:
    """
    Find potential encoding issues (mojibake) in text columns.

    Returns:
        List of ValidationIssue for columns with encoding problems
    """
    issues = []

    # Common mojibake patterns
    mojibake_patterns = [
        r'Ã©',  # é
        r'Ã¨',  # è
        r'Ã ',  # à
        r'Ã¢',  # â
        r'â€™',  # '
        r'â€œ',  # "
        r'â€',   # —
        r'Ã§',  # ç
        r'Ã¼',  # ü
        r'Ã¶',  # ö
        r'Ã¤',  # ä
    ]

    combined_pattern = '|'.join(mojibake_patterns)

    for col in df.columns:
        if _is_string_column(df[col]):
            non_null = df[col].dropna()
            if len(non_null) == 0:
                continue

            encoding_rows = []
            sample_values = []

            for i, (idx, value) in enumerate(non_null.items()):
                s = str(value)
                if re.search(combined_pattern, s):
                    encoding_rows.append(int(idx) + 2 if isinstance(idx, (int, np.integer)) else i + 2)
                    if len(sample_values) < 5:
                        sample_values.append(s)

            if encoding_rows:
                issues.append(ValidationIssue(
                    issue_type=IssueType.ENCODING_ISSUES,
                    severity=IssueSeverity.WARNING,
                    column=col,
                    row_numbers=encoding_rows,
                    description=f"Potential encoding issues (mojibake) in {len(encoding_rows)} values",
                    sample_values=sample_values,
                    auto_fixable=True,
                    fix_description="Will attempt to fix common encoding issues",
                ))

    return issues


def validate_dataframe(df: pd.DataFrame) -> ValidationResult:
    """
    Run all validators on a DataFrame.

    This is the main entry point for validation. It runs all checks
    and returns a comprehensive ValidationResult.

    Args:
        df: The DataFrame to validate

    Returns:
        ValidationResult with all detected issues

    Example:
        >>> result = validate_dataframe(df)
        >>> print(result.summary())
    """
    result = ValidationResult()

    # Run all validators
    validators = [
        lambda: [find_duplicates(df)] if find_duplicates(df) else [],
        lambda: find_missing_values(df),
        lambda: find_date_issues(df),
        lambda: find_currency_values(df),
        lambda: find_whitespace_issues(df),
        lambda: [find_column_name_issues(df)] if find_column_name_issues(df) else [],
        lambda: find_outliers(df),
        lambda: find_encoding_issues(df),
    ]

    for validator in validators:
        for issue in validator():
            result.add_issue(issue)

    return result
