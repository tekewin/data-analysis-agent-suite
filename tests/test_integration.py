"""Integration tests for the data cleaning pipeline."""

import pytest
import pandas as pd
import os
from pathlib import Path

from src.cleaning.loader import load_file
from src.cleaning.profiler import profile_dataframe
from src.cleaning.validators import validate_dataframe
from src.cleaning.transformers import (
    trim_whitespace,
    standardize_column_names,
    parse_currency,
    fix_encoding,
    handle_duplicates,
    handle_missing_values,
)
from src.cleaning.reporter import generate_cleaning_report, save_cleaning_results


class TestEndToEndPipeline:
    """Tests for the complete cleaning pipeline."""

    def test_load_profile_validate_sample_csv(self):
        """Should load, profile, and validate the sample CSV."""
        sample_path = Path(__file__).parent.parent / "examples" / "sample_data.csv"

        if not sample_path.exists():
            pytest.skip("Sample data not found")

        # Load
        df, meta = load_file(str(sample_path))
        assert len(df) == 100
        assert meta['file_type'] == 'csv'

        # Profile
        profile = profile_dataframe(df)
        assert profile.total_rows == 100
        assert profile.total_columns == 10

        # Validate
        result = validate_dataframe(df)
        assert result.total_issues > 0  # Sample data has intentional issues

    def test_load_excel_with_merged_cells(self):
        """Should load Excel and handle merged cells."""
        sample_path = Path(__file__).parent.parent / "examples" / "sample_data.xlsx"

        if not sample_path.exists():
            pytest.skip("Sample Excel not found")

        df, meta = load_file(str(sample_path))

        assert len(df) > 0
        assert meta['merged_cell_count'] > 0
        assert 'Region' in df.columns

        # Merged cells should be forward-filled
        region_values = df['Region'].dropna().unique()
        assert len(region_values) == 4  # North, South, East, West

    def test_full_cleaning_pipeline(self, df_with_whitespace, temp_output_dir):
        """Should run full pipeline from raw to cleaned."""
        all_changes = []

        # Step 1: Standardize column names
        result = standardize_column_names(df_with_whitespace)
        df = result.df
        all_changes.extend([c.to_dict() for c in result.changes])

        # Step 2: Trim whitespace
        result = trim_whitespace(df)
        df = result.df
        all_changes.extend([c.to_dict() for c in result.changes])

        # Verify cleaning worked
        assert ' Alice ' not in df['name'].values
        assert 'Alice' in df['name'].values

        # Generate report
        report = generate_cleaning_report(
            original_df=df_with_whitespace,
            cleaned_df=df,
            source_file='test_data.csv',
            changes=all_changes,
            output_dir=temp_output_dir,
        )

        assert 'Data Cleaning Report' in report
        assert 'trim' in report.lower() or 'whitespace' in report.lower()

    def test_save_results(self, sample_df, temp_output_dir):
        """Should save cleaned data and report to files."""
        report = generate_cleaning_report(
            original_df=sample_df,
            cleaned_df=sample_df,
            source_file='test.csv',
            changes=[],
            output_dir=temp_output_dir,
        )

        paths = save_cleaning_results(
            cleaned_df=sample_df,
            report=report,
            source_file='test.csv',
            output_dir=temp_output_dir,
        )

        assert os.path.exists(paths['csv'])
        assert os.path.exists(paths['report'])

        # Verify CSV content
        loaded_df = pd.read_csv(paths['csv'])
        assert len(loaded_df) == len(sample_df)

        # Verify report content
        with open(paths['report']) as f:
            content = f.read()
        assert 'Data Cleaning Report' in content


class TestEdgeCases:
    """Tests for edge cases in the pipeline."""

    def test_handles_all_missing_column(self):
        """Should handle columns with all missing values."""
        df = pd.DataFrame({
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Empty': [None, None, None],
        })

        result = validate_dataframe(df)
        profile = profile_dataframe(df)

        # Should detect missing values
        missing_issues = [i for i in result.issues if i.column == 'Empty']
        assert len(missing_issues) >= 1

    def test_handles_single_row(self):
        """Should handle single-row DataFrames."""
        df = pd.DataFrame({'Name': ['Alice'], 'Age': [25]})

        profile = profile_dataframe(df)
        result = validate_dataframe(df)

        assert profile.total_rows == 1
        assert profile.duplicate_row_count == 0

    def test_handles_empty_dataframe(self):
        """Should handle empty DataFrames gracefully."""
        df = pd.DataFrame()

        profile = profile_dataframe(df)
        result = validate_dataframe(df)

        assert profile.total_rows == 0
        assert result.total_issues == 0

    def test_handles_unicode_content(self):
        """Should handle various Unicode characters."""
        df = pd.DataFrame({
            'Name': ['日本語', 'Ελληνικά', 'العربية', 'עברית'],
            'Emoji': ['😀', '🎉', '✨', '🚀'],
        })

        profile = profile_dataframe(df)
        result = validate_dataframe(df)

        assert profile.total_rows == 4
        # Unicode should not trigger encoding issues
        encoding_issues = [i for i in result.issues if i.column == 'Name']
        # True Unicode should not be flagged as mojibake
        assert len([i for i in encoding_issues if 'encoding' in str(i.issue_type).lower()]) == 0

    def test_handles_very_long_strings(self):
        """Should handle very long string values."""
        long_string = 'x' * 10000
        df = pd.DataFrame({
            'Content': [long_string, 'short', long_string],
        })

        profile = profile_dataframe(df)
        result = validate_dataframe(df)

        assert profile.total_rows == 3
        text_col = next(c for c in profile.columns if c.name == 'Content')
        assert text_col.max_length == 10000


class TestRowNumberTracking:
    """Tests for accurate row number tracking in audit trail."""

    def test_row_numbers_are_1_indexed(self, df_with_duplicates):
        """Row numbers should be 1-indexed for human readability."""
        from src.cleaning.validators import find_duplicates

        issue = find_duplicates(df_with_duplicates)

        # Row numbers should start from 2 (1 for header, 2+ for data)
        assert all(rn >= 2 for rn in issue.row_numbers)

    def test_change_records_include_row_numbers(self, df_with_whitespace):
        """Transformation changes should include affected row numbers."""
        result = trim_whitespace(df_with_whitespace)

        for change in result.changes:
            assert 'row_numbers' in change.to_dict()
            assert len(change.row_numbers) > 0
