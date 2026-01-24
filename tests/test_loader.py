"""Tests for the loader module."""

import pytest
import pandas as pd
import tempfile
import os

from src.cleaning.loader import (
    load_file,
    load_csv,
    load_excel,
    detect_encoding,
    LoadError,
)


class TestDetectEncoding:
    """Tests for encoding detection."""

    def test_detect_utf8(self, temp_csv_file):
        """Should detect UTF-8 encoding."""
        encoding = detect_encoding(temp_csv_file)
        assert encoding.lower() in ['utf-8', 'ascii']

    def test_detect_handles_empty_file(self):
        """Should handle empty files gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('')
            temp_path = f.name

        try:
            encoding = detect_encoding(temp_path)
            assert encoding is not None
        finally:
            os.unlink(temp_path)


class TestLoadCSV:
    """Tests for CSV loading."""

    def test_load_basic_csv(self, temp_csv_file):
        """Should load a basic CSV file."""
        df, meta = load_csv(temp_csv_file)

        assert len(df) == 4
        assert 'Name' in df.columns
        assert meta['file_type'] == 'csv'
        assert meta['original_rows'] == 4

    def test_load_csv_with_encoding_override(self, temp_csv_file):
        """Should respect encoding override."""
        df, meta = load_csv(temp_csv_file, encoding='utf-8')

        assert len(df) == 4
        assert meta['detected_encoding'] == 'utf-8'

    def test_load_nonexistent_file(self):
        """Should raise LoadError for missing files."""
        with pytest.raises(LoadError, match="File not found"):
            load_csv('/nonexistent/path.csv')


class TestLoadExcel:
    """Tests for Excel loading."""

    def test_load_basic_excel(self, temp_excel_file):
        """Should load a basic Excel file."""
        df, meta = load_excel(temp_excel_file)

        assert len(df) == 4
        assert 'Name' in df.columns
        assert meta['file_type'] == 'excel'

    def test_load_excel_returns_sheet_info(self, temp_excel_file):
        """Should include sheet information in metadata."""
        df, meta = load_excel(temp_excel_file)

        assert 'available_sheets' in meta
        assert 'sheet_name' in meta

    def test_load_excel_nonexistent_sheet(self, temp_excel_file):
        """Should raise LoadError for missing sheets."""
        with pytest.raises(LoadError, match="Sheet .* not found"):
            load_excel(temp_excel_file, sheet_name='NonexistentSheet')


class TestLoadFile:
    """Tests for the unified load_file function."""

    def test_load_csv_by_extension(self, temp_csv_file):
        """Should detect CSV format by extension."""
        df, meta = load_file(temp_csv_file)

        assert meta['file_type'] == 'csv'
        assert len(df) == 4

    def test_load_excel_by_extension(self, temp_excel_file):
        """Should detect Excel format by extension."""
        df, meta = load_file(temp_excel_file)

        assert meta['file_type'] == 'excel'
        assert len(df) == 4

    def test_unsupported_format(self):
        """Should raise LoadError for unsupported formats."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'test')
            temp_path = f.name

        try:
            with pytest.raises(LoadError, match="Unsupported file format"):
                load_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_metadata_contains_column_names(self, temp_csv_file):
        """Should include column names in metadata."""
        df, meta = load_file(temp_csv_file)

        assert 'column_names' in meta
        assert meta['column_names'] == list(df.columns)
