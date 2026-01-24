"""Tests for the transformers module."""

import pytest
import pandas as pd
import numpy as np

from src.cleaning.transformers import (
    trim_whitespace,
    standardize_column_names,
    normalize_dates,
    parse_currency,
    handle_duplicates,
    handle_missing_values,
    handle_outliers,
    fix_encoding,
)


class TestTrimWhitespace:
    """Tests for whitespace trimming."""

    def test_trims_leading_whitespace(self, df_with_whitespace):
        """Should trim leading whitespace."""
        result = trim_whitespace(df_with_whitespace)

        assert result.df['Name'].iloc[2] == 'Charlie'  # Was '  Charlie'

    def test_trims_trailing_whitespace(self, df_with_whitespace):
        """Should trim trailing whitespace."""
        result = trim_whitespace(df_with_whitespace)

        assert result.df['Name'].iloc[1] == 'Bob'  # Was 'Bob  '

    def test_records_changes(self, df_with_whitespace):
        """Should record changes with row numbers."""
        result = trim_whitespace(df_with_whitespace)

        assert len(result.changes) > 0
        assert result.rows_affected > 0

    def test_preserves_clean_data(self, sample_df):
        """Should not modify already clean data."""
        result = trim_whitespace(sample_df)

        assert len(result.changes) == 0
        assert result.df.equals(sample_df)


class TestStandardizeColumnNames:
    """Tests for column name standardization."""

    def test_converts_camel_case(self, df_with_camel_case_columns):
        """Should convert CamelCase to snake_case."""
        result = standardize_column_names(df_with_camel_case_columns)

        assert 'first_name' in result.df.columns

    def test_converts_spaces(self, df_with_camel_case_columns):
        """Should convert spaces to underscores."""
        result = standardize_column_names(df_with_camel_case_columns)

        assert 'last_name' in result.df.columns

    def test_converts_hyphens(self, df_with_camel_case_columns):
        """Should convert hyphens to underscores."""
        result = standardize_column_names(df_with_camel_case_columns)

        assert 'phone_number' in result.df.columns

    def test_handles_duplicate_names(self):
        """Should handle resulting duplicate names."""
        df = pd.DataFrame({
            'First Name': ['A'],
            'first_name': ['B'],
        })
        result = standardize_column_names(df)

        assert len(result.df.columns) == 2
        assert 'first_name' in result.df.columns
        assert 'first_name_1' in result.df.columns


class TestNormalizeDates:
    """Tests for date normalization."""

    def test_normalizes_iso_dates(self, df_with_dates):
        """Should parse ISO format dates."""
        result = normalize_dates(df_with_dates, 'Date', output_format='%Y-%m-%d')

        # First row is already ISO
        assert '2024-01-15' in result.df['Date'].values

    def test_normalizes_us_dates(self):
        """Should parse US format dates (MM/DD/YYYY)."""
        df = pd.DataFrame({'Date': ['01/15/2024', '12/25/2024']})
        result = normalize_dates(df, 'Date', output_format='%Y-%m-%d', dayfirst=False)

        assert result.df['Date'].iloc[0] == '2024-01-15'
        assert result.df['Date'].iloc[1] == '2024-12-25'

    def test_normalizes_eu_dates(self):
        """Should parse EU format dates (DD/MM/YYYY) when dayfirst=True."""
        df = pd.DataFrame({'Date': ['15/01/2024', '25/12/2024']})
        result = normalize_dates(df, 'Date', output_format='%Y-%m-%d', dayfirst=True)

        assert result.df['Date'].iloc[0] == '2024-01-15'
        assert result.df['Date'].iloc[1] == '2024-12-25'

    def test_handles_missing_column(self):
        """Should handle missing column gracefully."""
        df = pd.DataFrame({'Other': ['A', 'B']})
        result = normalize_dates(df, 'Date')

        assert len(result.changes) == 0


class TestParseCurrency:
    """Tests for currency parsing."""

    def test_parses_us_currency(self):
        """Should parse US currency format ($1,234.56)."""
        df = pd.DataFrame({'Amount': ['$1,234.56', '$100.00', '$0.99']})
        result = parse_currency(df, 'Amount')

        assert result.df['Amount'].iloc[0] == 1234.56
        assert result.df['Amount'].iloc[1] == 100.00

    def test_parses_european_currency(self):
        """Should parse European currency format (1.234,56)."""
        df = pd.DataFrame({'Amount': ['1.234,56', '100,00', '0,99']})
        result = parse_currency(df, 'Amount')

        assert result.df['Amount'].iloc[0] == 1234.56
        assert result.df['Amount'].iloc[1] == 100.00

    def test_parses_negative_parentheses(self):
        """Should parse accounting negative format (1,234.56)."""
        df = pd.DataFrame({'Amount': ['($500.00)', '(1,000.00)']})
        result = parse_currency(df, 'Amount')

        assert result.df['Amount'].iloc[0] == -500.00
        assert result.df['Amount'].iloc[1] == -1000.00

    def test_parses_negative_sign(self):
        """Should parse negative with minus sign."""
        df = pd.DataFrame({'Amount': ['-$100.00', '-€50.00']})
        result = parse_currency(df, 'Amount')

        assert result.df['Amount'].iloc[0] == -100.00
        assert result.df['Amount'].iloc[1] == -50.00

    def test_records_changes(self, df_with_currency):
        """Should record changes with row numbers."""
        result = parse_currency(df_with_currency, 'Amount')

        assert len(result.changes) > 0
        assert result.rows_affected > 0


class TestHandleDuplicates:
    """Tests for duplicate handling."""

    def test_remove_duplicates(self, df_with_duplicates):
        """Should remove duplicate rows."""
        result = handle_duplicates(df_with_duplicates, strategy='remove')

        assert len(result.df) == 3  # 5 rows - 2 duplicates
        assert len(result.changes) == 1

    def test_flag_duplicates(self, df_with_duplicates):
        """Should flag duplicates with new column."""
        result = handle_duplicates(df_with_duplicates, strategy='flag')

        assert 'is_duplicate' in result.df.columns
        assert result.df['is_duplicate'].sum() == 2

    def test_keep_last(self, df_with_duplicates):
        """Should keep last occurrence when specified."""
        result = handle_duplicates(df_with_duplicates, strategy='remove', keep='last')

        assert len(result.df) == 3


class TestHandleMissingValues:
    """Tests for missing value handling."""

    def test_drop_missing(self, df_with_missing):
        """Should drop rows with missing values."""
        result = handle_missing_values(df_with_missing, 'Name', strategy='drop')

        # One None in Name column
        assert len(result.df) == 4

    def test_fill_with_mean(self):
        """Should fill with mean for numeric columns."""
        df = pd.DataFrame({'Value': [10.0, 20.0, None, 40.0]})
        result = handle_missing_values(df, 'Value', strategy='mean')

        # Mean of 10, 20, 40 is about 23.33
        assert pd.notna(result.df['Value'].iloc[2])
        assert abs(result.df['Value'].iloc[2] - 23.33) < 0.1

    def test_fill_with_median(self):
        """Should fill with median for numeric columns."""
        df = pd.DataFrame({'Value': [10.0, 20.0, None, 100.0]})
        result = handle_missing_values(df, 'Value', strategy='median')

        # Median of 10, 20, 100 is 20
        assert result.df['Value'].iloc[2] == 20.0

    def test_fill_with_custom_value(self, df_with_missing):
        """Should fill with custom value."""
        result = handle_missing_values(df_with_missing, 'Name', strategy='custom', fill_value='Unknown')

        assert 'Unknown' in result.df['Name'].values

    def test_forward_fill(self):
        """Should forward-fill missing values."""
        df = pd.DataFrame({'Value': [1, None, None, 4]})
        result = handle_missing_values(df, 'Value', strategy='forward')

        assert result.df['Value'].iloc[1] == 1
        assert result.df['Value'].iloc[2] == 1


class TestHandleOutliers:
    """Tests for outlier handling."""

    def test_flag_outliers(self, df_with_outliers):
        """Should flag outliers with new column."""
        result = handle_outliers(df_with_outliers, 'Value', strategy='flag')

        assert 'Value_is_outlier' in result.df.columns
        assert result.df['Value_is_outlier'].sum() >= 1

    def test_remove_outliers(self, df_with_outliers):
        """Should remove rows with outliers."""
        original_len = len(df_with_outliers)
        result = handle_outliers(df_with_outliers, 'Value', strategy='remove')

        assert len(result.df) < original_len

    def test_cap_outliers(self, df_with_outliers):
        """Should cap outliers at bounds."""
        result = handle_outliers(df_with_outliers, 'Value', strategy='cap')

        # The extreme value 100 should be capped
        assert result.df['Value'].max() < 100


class TestFixEncoding:
    """Tests for encoding fix."""

    def test_fixes_mojibake(self, df_with_encoding_issues):
        """Should fix common mojibake patterns."""
        result = fix_encoding(df_with_encoding_issues)

        assert 'Café' in result.df['Name'].values
        assert 'Résumé' in result.df['Name'].values

    def test_preserves_clean_text(self, sample_df):
        """Should not modify clean text."""
        result = fix_encoding(sample_df)

        assert len(result.changes) == 0
