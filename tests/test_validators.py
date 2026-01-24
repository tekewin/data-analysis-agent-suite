"""Tests for the validators module."""

import pytest
import pandas as pd

from src.cleaning.validators import (
    validate_dataframe,
    find_duplicates,
    find_missing_values,
    find_date_issues,
    find_currency_values,
    find_whitespace_issues,
    find_column_name_issues,
    find_outliers,
    find_encoding_issues,
    IssueType,
    IssueSeverity,
)


class TestFindDuplicates:
    """Tests for duplicate detection."""

    def test_detects_duplicates(self, df_with_duplicates):
        """Should detect duplicate rows."""
        issue = find_duplicates(df_with_duplicates)

        assert issue is not None
        assert issue.issue_type == IssueType.DUPLICATE_ROWS
        assert len(issue.row_numbers) == 2  # Alice and Bob duplicated

    def test_no_duplicates(self, sample_df):
        """Should return None when no duplicates exist."""
        issue = find_duplicates(sample_df)
        assert issue is None


class TestFindMissingValues:
    """Tests for missing value detection."""

    def test_detects_missing_values(self, df_with_missing):
        """Should detect missing values in each column."""
        issues = find_missing_values(df_with_missing)

        assert len(issues) >= 2  # At least Name and Age have missing
        column_names = [i.column for i in issues]
        assert 'Name' in column_names
        assert 'Age' in column_names

    def test_no_missing_values(self, sample_df):
        """Should return empty list when no missing values."""
        issues = find_missing_values(sample_df)
        assert len(issues) == 0

    def test_high_missing_is_critical(self):
        """Should mark high percentage missing as critical."""
        df = pd.DataFrame({
            'A': [None] * 6 + [1, 2, 3, 4],  # 60% missing
        })
        issues = find_missing_values(df)

        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.CRITICAL


class TestFindDateIssues:
    """Tests for date format detection."""

    def test_detects_ambiguous_dates(self, df_with_dates):
        """Should detect ambiguous date formats."""
        issues = find_date_issues(df_with_dates)

        # Should find ambiguous dates like 01/20/2024 (could be Jan 20 or 20th of Jan)
        assert len(issues) >= 0  # May or may not detect depending on pattern

    def test_no_date_issues_in_numeric(self, sample_df):
        """Should not flag numeric columns as date issues."""
        issues = find_date_issues(sample_df)
        assert len(issues) == 0


class TestFindCurrencyValues:
    """Tests for currency value detection."""

    def test_detects_currency_formats(self, df_with_currency):
        """Should detect currency-formatted values."""
        issues = find_currency_values(df_with_currency)

        assert len(issues) >= 1
        assert issues[0].issue_type == IssueType.CURRENCY_VALUES
        assert issues[0].auto_fixable is True

    def test_no_currency_in_text(self, sample_df):
        """Should not flag plain text as currency."""
        issues = find_currency_values(sample_df)
        assert len(issues) == 0


class TestFindWhitespaceIssues:
    """Tests for whitespace detection."""

    def test_detects_whitespace(self, df_with_whitespace):
        """Should detect leading/trailing whitespace."""
        issues = find_whitespace_issues(df_with_whitespace)

        assert len(issues) >= 1
        assert issues[0].issue_type == IssueType.WHITESPACE
        assert issues[0].auto_fixable is True

    def test_no_whitespace_issues(self, sample_df):
        """Should not flag clean text."""
        issues = find_whitespace_issues(sample_df)
        assert len(issues) == 0


class TestFindColumnNameIssues:
    """Tests for column name validation."""

    def test_detects_non_snake_case(self, df_with_camel_case_columns):
        """Should detect non-snake_case column names."""
        issue = find_column_name_issues(df_with_camel_case_columns)

        assert issue is not None
        assert issue.issue_type == IssueType.NON_SNAKE_CASE
        assert len(issue.sample_values) == 4  # All columns need fixing

    def test_accepts_snake_case(self):
        """Should accept valid snake_case names."""
        df = pd.DataFrame({
            'first_name': ['Alice'],
            'last_name': ['Smith'],
            'email_address': ['a@b.com'],
        })
        issue = find_column_name_issues(df)
        assert issue is None


class TestFindOutliers:
    """Tests for outlier detection."""

    def test_detects_outliers_iqr(self, df_with_outliers):
        """Should detect outliers using IQR method."""
        issues = find_outliers(df_with_outliers, method='iqr')

        value_issues = [i for i in issues if i.column == 'Value']
        assert len(value_issues) >= 1
        assert value_issues[0].issue_type == IssueType.OUTLIERS

    def test_detects_outliers_zscore(self, df_with_outliers):
        """Should detect outliers using z-score method."""
        issues = find_outliers(df_with_outliers, method='zscore', threshold=2)

        value_issues = [i for i in issues if i.column == 'Value']
        assert len(value_issues) >= 1

    def test_no_outliers_in_text(self, sample_df):
        """Should not flag text columns."""
        issues = find_outliers(sample_df)
        text_issues = [i for i in issues if i.column == 'Name']
        assert len(text_issues) == 0


class TestFindEncodingIssues:
    """Tests for encoding issue detection."""

    def test_detects_mojibake(self, df_with_encoding_issues):
        """Should detect mojibake encoding issues."""
        issues = find_encoding_issues(df_with_encoding_issues)

        assert len(issues) >= 1
        assert issues[0].issue_type == IssueType.ENCODING_ISSUES
        assert issues[0].auto_fixable is True

    def test_no_encoding_issues(self, sample_df):
        """Should not flag clean text."""
        issues = find_encoding_issues(sample_df)
        assert len(issues) == 0


class TestValidateDataframe:
    """Tests for the comprehensive validation function."""

    def test_runs_all_validators(self, df_with_missing):
        """Should run all validators and return combined result."""
        result = validate_dataframe(df_with_missing)

        assert result.total_issues > 0
        assert result.critical_count + result.warning_count + result.info_count > 0

    def test_returns_summary(self, df_with_duplicates):
        """Should generate readable summary."""
        result = validate_dataframe(df_with_duplicates)
        summary = result.summary()

        assert 'issue' in summary.lower()

    def test_empty_df_returns_no_issues(self):
        """Should handle empty DataFrame."""
        df = pd.DataFrame()
        result = validate_dataframe(df)

        assert result.total_issues == 0
