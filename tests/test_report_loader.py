"""Tests for report data loading utilities."""

import pytest
import json
import tempfile
from pathlib import Path
from src.reporting.loader import (
    ReportInput,
    load_analysis_result,
    load_visualization_manifest,
    create_report_input,
    find_analysis_files,
    find_visualization_manifest,
    _reconstruct_finding,
    _reconstruct_descriptive_stats,
    _reconstruct_correlation,
    _reconstruct_trend,
    _reconstruct_segment,
)
from src.analysis import (
    AnalysisResult,
    AnalysisFinding,
    DescriptiveStats,
    Correlation,
    TrendAnalysis,
    SegmentComparison,
)


class TestReportInput:
    """Tests for ReportInput dataclass."""

    def test_has_visualizations_true(self, sample_report_input):
        """has_visualizations returns True when manifest exists."""
        assert sample_report_input.has_visualizations is True

    def test_has_visualizations_false(self, sample_analysis_result):
        """has_visualizations returns False when no manifest."""
        report_input = ReportInput(
            source_file='test.csv',
            analysis_result=sample_analysis_result,
            visualization_manifest=None,
        )
        assert report_input.has_visualizations is False

    def test_finding_count(self, sample_report_input):
        """finding_count returns total findings."""
        assert sample_report_input.finding_count == 3

    def test_chart_count(self, sample_report_input):
        """chart_count returns number of charts."""
        assert sample_report_input.chart_count == 3

    def test_to_dict(self, sample_report_input):
        """Can serialize to dictionary."""
        result = sample_report_input.to_dict()

        assert isinstance(result, dict)
        assert result['source_file'] == 'test_data.csv'
        assert result['audience'] == 'business'


class TestLoadAnalysisResult:
    """Tests for load_analysis_result function."""

    def test_load_valid_file(self, sample_analysis_json):
        """Can load a valid analysis JSON file."""
        result = load_analysis_result(sample_analysis_json)

        assert isinstance(result, AnalysisResult)
        assert len(result.findings) == 3
        assert result.rows_analyzed == 1000

    def test_load_nonexistent_file(self, temp_output_dir):
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_analysis_result(f"{temp_output_dir}/nonexistent.json")

    def test_load_invalid_json(self, temp_output_dir):
        """Raises error for invalid JSON."""
        invalid_file = Path(temp_output_dir) / 'invalid.json'
        invalid_file.write_text('not valid json')

        with pytest.raises(json.JSONDecodeError):
            load_analysis_result(str(invalid_file))


class TestReconstructFinding:
    """Tests for _reconstruct_finding helper."""

    def test_reconstruct_full_finding(self):
        """Can reconstruct a finding with all fields."""
        data = {
            'category': 'correlation',
            'title': 'Test Finding',
            'description': 'A test description',
            'affected_columns': ['col1', 'col2'],
            'importance': 'high',
            'confidence': 0.85,
            'actionable': True,
            'recommendation': 'Do something',
            'supporting_data': {'key': 'value'},
        }

        result = _reconstruct_finding(data)

        assert isinstance(result, AnalysisFinding)
        assert result.title == 'Test Finding'
        assert result.importance == 'high'
        assert result.confidence == 0.85

    def test_reconstruct_minimal_finding(self):
        """Can reconstruct a finding with minimal fields."""
        data = {'title': 'Minimal'}

        result = _reconstruct_finding(data)

        assert result.title == 'Minimal'
        assert result.category == 'unknown'
        assert result.importance == 'low'


class TestReconstructDescriptiveStats:
    """Tests for _reconstruct_descriptive_stats helper."""

    def test_reconstruct_stats(self):
        """Can reconstruct descriptive stats."""
        data = {
            'column': 'revenue',
            'count': 1000,
            'missing_count': 5,
            'mean': 5000.0,
            'median': 4500.0,
            'std': 1500.0,
            'min': 500.0,
            'max': 15000.0,
            'q25': 3500.0,
            'q75': 6500.0,
            'skewness': 0.5,
            'kurtosis': 0.2,
        }

        result = _reconstruct_descriptive_stats(data)

        assert isinstance(result, DescriptiveStats)
        assert result.column == 'revenue'
        assert result.mean == 5000.0


class TestReconstructCorrelation:
    """Tests for _reconstruct_correlation helper."""

    def test_reconstruct_correlation(self):
        """Can reconstruct a correlation."""
        data = {
            'column1': 'revenue',
            'column2': 'quantity',
            'coefficient': 0.85,
            'method': 'pearson',
            'strength': 'strong',
            'direction': 'positive',
            'p_value': 0.001,
            'is_significant': True,
        }

        result = _reconstruct_correlation(data)

        assert isinstance(result, Correlation)
        assert result.column1 == 'revenue'
        assert result.coefficient == 0.85


class TestReconstructTrend:
    """Tests for _reconstruct_trend helper."""

    def test_reconstruct_trend(self):
        """Can reconstruct a trend analysis."""
        data = {
            'column': 'sales',
            'date_column': 'date',
            'trend_direction': 'increasing',
            'slope': 10.5,
            'r_squared': 0.72,
            'growth_rate_pct': 15.0,
            'seasonality_detected': True,
            'seasonal_period': 'monthly',
        }

        result = _reconstruct_trend(data)

        assert isinstance(result, TrendAnalysis)
        assert result.column == 'sales'
        assert result.trend_direction == 'increasing'


class TestReconstructSegment:
    """Tests for _reconstruct_segment helper."""

    def test_reconstruct_segment(self):
        """Can reconstruct a segment comparison."""
        data = {
            'segment_column': 'region',
            'metric_column': 'profit',
            'segments': {
                'North': {'count': 300, 'mean': 5500.0},
            },
            'variance_ratio': 0.15,
            'notable_differences': ['North has highest mean'],
        }

        result = _reconstruct_segment(data)

        assert isinstance(result, SegmentComparison)
        assert result.segment_column == 'region'
        assert 'North' in result.segments


class TestLoadVisualizationManifest:
    """Tests for load_visualization_manifest function."""

    def test_load_valid_manifest(self, sample_visualization_manifest):
        """Can load a valid visualization manifest."""
        from src.visualization import ChartManifest

        result = load_visualization_manifest(sample_visualization_manifest)

        assert isinstance(result, ChartManifest)
        assert len(result.charts) == 3
        assert result.charts[0].chart_type == 'line'

    def test_load_nonexistent_returns_none(self, temp_output_dir):
        """Returns None for missing manifest."""
        result = load_visualization_manifest(f"{temp_output_dir}/nonexistent.json")

        assert result is None


class TestFindAnalysisFiles:
    """Tests for find_analysis_files function."""

    def test_find_files(self, sample_analysis_json):
        """Can find analysis files in directory."""
        directory = str(Path(sample_analysis_json).parent)

        result = find_analysis_files(directory)

        assert len(result) >= 1
        assert any('analysis' in f for f in result)

    def test_find_no_files(self, temp_output_dir):
        """Returns empty list when no files found."""
        result = find_analysis_files(temp_output_dir)

        assert result == []

    def test_nonexistent_directory(self):
        """Returns empty list for nonexistent directory."""
        result = find_analysis_files('/nonexistent/path')

        assert result == []


class TestFindVisualizationManifest:
    """Tests for find_visualization_manifest function."""

    def test_find_manifest_in_subdir(self, sample_visualization_manifest):
        """Can find manifest in subdirectory."""
        parent_dir = str(Path(sample_visualization_manifest).parent.parent)

        result = find_visualization_manifest(parent_dir)

        assert result is not None
        assert 'chart_manifest.json' in result

    def test_find_no_manifest(self, temp_output_dir):
        """Returns None when no manifest found."""
        result = find_visualization_manifest(temp_output_dir)

        assert result is None


class TestCreateReportInput:
    """Tests for create_report_input function."""

    def test_create_with_analysis_only(self, sample_analysis_json):
        """Can create input with just analysis file."""
        result = create_report_input(
            analysis_path=sample_analysis_json,
            audience='technical',
        )

        assert isinstance(result, ReportInput)
        assert result.audience == 'technical'
        assert result.visualization_manifest is None

    def test_create_with_visualizations(self, sample_analysis_json, sample_visualization_manifest):
        """Can create input with visualizations."""
        result = create_report_input(
            analysis_path=sample_analysis_json,
            viz_path=sample_visualization_manifest,
            audience='business',
        )

        assert result.has_visualizations is True
        assert result.chart_count == 3

    def test_create_with_emphasis(self, sample_analysis_json):
        """Can specify emphasis areas."""
        result = create_report_input(
            analysis_path=sample_analysis_json,
            emphasis_areas=['revenue', 'profit'],
        )

        assert 'revenue' in result.emphasis_areas
        assert 'profit' in result.emphasis_areas
