"""Tests for visualization generator and recommendation logic."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile

from src.visualization import (
    ChartSpec,
    ChartConfig,
    GeneratedChart,
    VisualizationResult,
    recommend_visualizations,
    generate_chart,
    generate_all_charts,
    save_chart_html,
    create_output_directory,
    get_chart_type_description,
    detect_column_types,
    detect_chart_candidates,
    identify_date_column,
    identify_numeric_columns,
    identify_categorical_columns,
    sanitize_filename,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def df_comprehensive():
    """DataFrame with all column types for recommendation testing."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'order_date': pd.date_range('2024-01-01', periods=n, freq='D'),
        'revenue': np.random.uniform(1000, 5000, n),
        'quantity': np.random.randint(10, 100, n),
        'profit': np.random.uniform(100, 1000, n),
        'discount': np.random.uniform(0, 0.3, n),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n),
        'category': np.random.choice(['Electronics', 'Clothing', 'Food'], n),
        'status': np.random.choice(['Completed', 'Pending', 'Cancelled'], n),
    })


@pytest.fixture
def df_numeric_only():
    """DataFrame with only numeric columns."""
    np.random.seed(42)
    return pd.DataFrame({
        'a': np.random.normal(100, 20, 50),
        'b': np.random.normal(50, 10, 50),
        'c': np.random.normal(75, 15, 50),
    })


@pytest.fixture
def df_categorical_only():
    """DataFrame with only categorical columns."""
    return pd.DataFrame({
        'color': ['red', 'blue', 'green', 'red', 'blue'] * 10,
        'size': ['S', 'M', 'L', 'S', 'M'] * 10,
    })


@pytest.fixture
def temp_output():
    """Temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# =============================================================================
# TEST COLUMN TYPE DETECTION
# =============================================================================

class TestColumnTypeDetection:
    """Tests for column type detection utilities."""

    def test_detect_all_types(self, df_comprehensive):
        """Should detect all column types correctly."""
        types = detect_column_types(df_comprehensive)

        assert 'order_date' in types['datetime']
        assert 'revenue' in types['numeric']
        assert 'region' in types['categorical']

    def test_detect_numeric_columns(self, df_comprehensive):
        """Should identify numeric columns."""
        numeric = identify_numeric_columns(df_comprehensive)

        assert 'revenue' in numeric
        assert 'quantity' in numeric
        assert 'profit' in numeric
        assert 'region' not in numeric

    def test_detect_categorical_columns(self, df_comprehensive):
        """Should identify categorical columns."""
        categorical = identify_categorical_columns(df_comprehensive)

        assert 'region' in categorical
        assert 'category' in categorical
        assert 'revenue' not in categorical

    def test_detect_date_column(self, df_comprehensive):
        """Should identify date column."""
        date_col = identify_date_column(df_comprehensive)

        assert date_col == 'order_date'

    def test_no_date_column(self, df_numeric_only):
        """Should return None when no date column."""
        date_col = identify_date_column(df_numeric_only)

        assert date_col is None


# =============================================================================
# TEST CHART RECOMMENDATIONS
# =============================================================================

class TestChartRecommendations:
    """Tests for automatic chart recommendation logic."""

    def test_recommend_for_comprehensive_data(self, df_comprehensive):
        """Should recommend diverse chart types for rich data."""
        recommendations = recommend_visualizations(df_comprehensive)

        assert len(recommendations) > 0
        assert len(recommendations) <= 8  # Max recommendations

        # Should have diverse chart types
        chart_types = {r.chart_type for r in recommendations}
        assert len(chart_types) >= 3  # At least 3 different types

    def test_recommend_prioritizes_diversity(self, df_comprehensive):
        """Should include one of each type before duplicates."""
        recommendations = recommend_visualizations(df_comprehensive)

        # First few recommendations should be unique types
        first_types = [r.chart_type for r in recommendations[:5]]
        assert len(set(first_types)) == len(first_types)

    def test_recommend_includes_time_series(self, df_comprehensive):
        """Should include line chart for time series data."""
        recommendations = recommend_visualizations(df_comprehensive)

        line_charts = [r for r in recommendations if r.chart_type == 'line']
        assert len(line_charts) >= 1
        assert line_charts[0].x_column == 'order_date'

    def test_recommend_includes_bar_chart(self, df_comprehensive):
        """Should include bar chart for categorical data."""
        recommendations = recommend_visualizations(df_comprehensive)

        bar_charts = [r for r in recommendations if r.chart_type == 'bar']
        assert len(bar_charts) >= 1

    def test_recommend_includes_correlation_heatmap(self, df_comprehensive):
        """Should include heatmap for multiple numeric columns."""
        recommendations = recommend_visualizations(df_comprehensive)

        heatmaps = [r for r in recommendations if r.chart_type == 'heatmap']
        assert len(heatmaps) >= 1

    def test_recommend_for_numeric_only(self, df_numeric_only):
        """Should recommend appropriate charts for numeric-only data."""
        recommendations = recommend_visualizations(df_numeric_only)

        chart_types = {r.chart_type for r in recommendations}

        # Should include scatter and heatmap for numeric relationships
        assert 'scatter' in chart_types or 'heatmap' in chart_types

    def test_max_recommendations_limit(self, df_comprehensive):
        """Should respect max_recommendations parameter."""
        recommendations = recommend_visualizations(df_comprehensive, max_recommendations=3)

        assert len(recommendations) <= 3

    def test_detect_chart_candidates(self, df_comprehensive):
        """Should detect chart candidates from data."""
        candidates = detect_chart_candidates(df_comprehensive)

        assert len(candidates) > 0
        assert all(isinstance(c, ChartSpec) for c in candidates)


# =============================================================================
# TEST CHART GENERATION
# =============================================================================

class TestChartGeneration:
    """Tests for chart generation functions."""

    def test_generate_single_chart(self, df_comprehensive):
        """Should generate a single chart from spec."""
        spec = ChartSpec(
            chart_type='line',
            title='Revenue Over Time',
            x_column='order_date',
            y_column='revenue',
        )

        fig = generate_chart(df_comprehensive, spec)

        assert fig is not None
        assert fig.layout.title.text == 'Revenue Over Time'

    def test_generate_all_charts(self, df_comprehensive, temp_output):
        """Should generate multiple charts and save to files."""
        specs = [
            ChartSpec(
                chart_type='line',
                title='Revenue Trend',
                x_column='order_date',
                y_column='revenue',
            ),
            ChartSpec(
                chart_type='bar',
                title='Revenue by Region',
                x_column='region',
                y_column='revenue',
            ),
        ]

        charts = generate_all_charts(df_comprehensive, specs, temp_output)

        assert len(charts) == 2
        assert all(isinstance(c, GeneratedChart) for c in charts)

        # Files should exist
        for chart in charts:
            assert Path(chart.filepath).exists()
            assert chart.filename.endswith('.html')

    def test_generated_chart_metadata(self, df_comprehensive, temp_output):
        """Should capture chart metadata correctly."""
        specs = [ChartSpec(
            chart_type='scatter',
            title='Revenue vs Quantity',
            x_column='revenue',
            y_column='quantity',
            description='Test description',
        )]

        charts = generate_all_charts(df_comprehensive, specs, temp_output)
        chart = charts[0]

        assert chart.chart_type == 'scatter'
        assert chart.title == 'Revenue vs Quantity'
        assert 'revenue' in chart.columns_used
        assert 'quantity' in chart.columns_used
        assert chart.description == 'Test description'

    def test_save_chart_html(self, df_comprehensive, temp_output):
        """Should save chart to HTML file."""
        spec = ChartSpec(
            chart_type='histogram',
            title='Test Histogram',
            x_column='revenue',
        )
        fig = generate_chart(df_comprehensive, spec)

        filepath = Path(temp_output) / 'test_chart.html'
        saved_path = save_chart_html(fig, str(filepath))

        assert Path(saved_path).exists()
        content = Path(saved_path).read_text()
        assert 'plotly' in content.lower()


# =============================================================================
# TEST OUTPUT DIRECTORY
# =============================================================================

class TestOutputDirectory:
    """Tests for output directory creation."""

    def test_create_output_directory(self, temp_output):
        """Should create timestamped output directory."""
        output_dir = create_output_directory(
            source_file='test_data.csv',
            base_dir=temp_output,
        )

        assert Path(output_dir).exists()
        assert 'test_data' in output_dir
        assert 'visualizations' in output_dir

    def test_sanitize_filename(self):
        """Should convert titles to safe filenames."""
        assert sanitize_filename('Revenue Over Time') == 'revenue_over_time'
        assert sanitize_filename('Test & Analysis!') == 'test_analysis'
        assert sanitize_filename('  Spaces  ') == 'spaces'
        assert sanitize_filename('') == 'chart'


# =============================================================================
# TEST CHART TYPE DESCRIPTIONS
# =============================================================================

class TestChartDescriptions:
    """Tests for chart type descriptions."""

    def test_get_description_for_all_types(self):
        """Should return descriptions for all chart types."""
        types = ['line', 'bar', 'scatter', 'heatmap', 'box', 'pie', 'histogram']

        for chart_type in types:
            desc = get_chart_type_description(chart_type)
            assert isinstance(desc, str)
            assert len(desc) > 10

    def test_unknown_type_description(self):
        """Should return generic description for unknown type."""
        desc = get_chart_type_description('unknown')

        assert isinstance(desc, str)


# =============================================================================
# TEST GENERATED CHART DATACLASS
# =============================================================================

class TestGeneratedChart:
    """Tests for GeneratedChart dataclass."""

    def test_to_dict(self):
        """Should serialize to dictionary."""
        chart = GeneratedChart(
            chart_type='line',
            title='Test Chart',
            filename='test.html',
            filepath='/path/to/test.html',
            columns_used=['x', 'y'],
            description='Test description',
            html_content='<html></html>',
        )

        d = chart.to_dict()

        assert d['chart_type'] == 'line'
        assert d['title'] == 'Test Chart'
        assert d['columns_used'] == ['x', 'y']
        # html_content should not be in dict (too large)
        assert 'html_content' not in d


# =============================================================================
# TEST VISUALIZATION RESULT DATACLASS
# =============================================================================

class TestVisualizationResult:
    """Tests for VisualizationResult dataclass."""

    def test_to_dict(self):
        """Should serialize complete result."""
        chart = GeneratedChart(
            chart_type='bar',
            title='Test',
            filename='test.html',
            filepath='/path/test.html',
            columns_used=['a', 'b'],
            description='Desc',
            html_content='<html></html>',
        )

        result = VisualizationResult(
            charts=[chart],
            dashboard_path='/path/index.html',
            manifest_path='/path/manifest.json',
            output_dir='/path/',
            total_charts=1,
            source_file='data.csv',
        )

        d = result.to_dict()

        assert d['total_charts'] == 1
        assert d['source_file'] == 'data.csv'
        assert len(d['charts']) == 1
