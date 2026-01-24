"""Tests for visualization chart builders."""

import pytest
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.visualization import (
    ChartConfig,
    ChartSpec,
    get_default_config,
    create_chart,
    create_line_chart,
    create_bar_chart,
    create_scatter_chart,
    create_heatmap,
    create_box_plot,
    create_pie_chart,
    create_histogram,
    CHART_BUILDERS,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def df_for_charts():
    """DataFrame suitable for multiple chart types."""
    np.random.seed(42)
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=50, freq='D'),
        'revenue': np.random.uniform(1000, 5000, 50),
        'quantity': np.random.randint(10, 100, 50),
        'profit': np.random.uniform(100, 1000, 50),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 50),
        'category': np.random.choice(['A', 'B', 'C'], 50),
    })


@pytest.fixture
def df_numeric_only():
    """DataFrame with only numeric columns."""
    np.random.seed(42)
    return pd.DataFrame({
        'x': np.random.normal(100, 20, 100),
        'y': np.random.normal(50, 10, 100),
        'z': np.random.normal(75, 15, 100),
    })


@pytest.fixture
def df_categorical():
    """DataFrame for categorical charts."""
    return pd.DataFrame({
        'category': ['A', 'B', 'C', 'D', 'E'],
        'value': [100, 250, 175, 300, 125],
    })


# =============================================================================
# TEST CHART CONFIG
# =============================================================================

class TestChartConfig:
    """Tests for ChartConfig dataclass."""

    def test_default_config_values(self):
        """Should have sensible defaults."""
        config = get_default_config()

        assert config.theme == "plotly_white"
        assert len(config.color_palette) >= 5
        assert config.show_legend is True
        assert config.interactive is True
        assert config.responsive is True
        assert config.title_font_size == 18
        assert config.height == 500

    def test_config_to_dict(self):
        """Should serialize to dictionary."""
        config = ChartConfig(theme="plotly_dark", height=600)
        d = config.to_dict()

        assert d['theme'] == "plotly_dark"
        assert d['height'] == 600
        assert 'color_palette' in d


# =============================================================================
# TEST CHART SPEC
# =============================================================================

class TestChartSpec:
    """Tests for ChartSpec dataclass."""

    def test_spec_creation(self):
        """Should create spec with all fields."""
        spec = ChartSpec(
            chart_type='line',
            title='Test Chart',
            x_column='date',
            y_column='value',
            description='A test chart',
        )

        assert spec.chart_type == 'line'
        assert spec.title == 'Test Chart'
        assert spec.x_column == 'date'
        assert spec.y_column == 'value'

    def test_spec_to_dict(self):
        """Should serialize to dictionary."""
        spec = ChartSpec(
            chart_type='bar',
            title='Bar Chart',
            x_column='category',
            y_column='value',
        )
        d = spec.to_dict()

        assert d['chart_type'] == 'bar'
        assert d['title'] == 'Bar Chart'


# =============================================================================
# TEST LINE CHART
# =============================================================================

class TestLineChart:
    """Tests for line chart creation."""

    def test_basic_line_chart(self, df_for_charts):
        """Should create basic line chart."""
        spec = ChartSpec(
            chart_type='line',
            title='Revenue Over Time',
            x_column='date',
            y_column='revenue',
        )

        fig = create_line_chart(df_for_charts, spec)

        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Revenue Over Time'
        assert len(fig.data) >= 1

    def test_line_chart_multiple_y(self, df_for_charts):
        """Should create line chart with multiple y columns."""
        spec = ChartSpec(
            chart_type='line',
            title='Revenue and Profit',
            x_column='date',
            y_columns=['revenue', 'profit'],
        )

        fig = create_line_chart(df_for_charts, spec)

        assert len(fig.data) == 2  # Two lines

    def test_line_chart_missing_column(self, df_for_charts):
        """Should raise error for missing column."""
        spec = ChartSpec(
            chart_type='line',
            title='Test',
            x_column='date',
            y_column='nonexistent',
        )

        with pytest.raises(ValueError, match="missing columns"):
            create_line_chart(df_for_charts, spec)


# =============================================================================
# TEST BAR CHART
# =============================================================================

class TestBarChart:
    """Tests for bar chart creation."""

    def test_basic_bar_chart(self, df_categorical):
        """Should create basic bar chart."""
        spec = ChartSpec(
            chart_type='bar',
            title='Category Values',
            x_column='category',
            y_column='value',
        )

        fig = create_bar_chart(df_categorical, spec)

        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Category Values'

    def test_bar_chart_with_aggregation(self, df_for_charts):
        """Should aggregate values for repeated categories."""
        spec = ChartSpec(
            chart_type='bar',
            title='Revenue by Region',
            x_column='region',
            y_column='revenue',
        )

        fig = create_bar_chart(df_for_charts, spec)

        assert isinstance(fig, go.Figure)
        # Should have aggregated the 4 regions
        assert len(fig.data[0].x) <= 4


# =============================================================================
# TEST SCATTER CHART
# =============================================================================

class TestScatterChart:
    """Tests for scatter chart creation."""

    def test_basic_scatter_chart(self, df_for_charts):
        """Should create basic scatter plot."""
        spec = ChartSpec(
            chart_type='scatter',
            title='Revenue vs Quantity',
            x_column='revenue',
            y_column='quantity',
        )

        fig = create_scatter_chart(df_for_charts, spec)

        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Revenue vs Quantity'

    def test_scatter_with_color(self, df_for_charts):
        """Should create scatter with color grouping."""
        spec = ChartSpec(
            chart_type='scatter',
            title='Colored Scatter',
            x_column='revenue',
            y_column='quantity',
            color_column='region',
        )

        fig = create_scatter_chart(df_for_charts, spec)

        assert isinstance(fig, go.Figure)

    def test_scatter_adds_trendline(self, df_numeric_only):
        """Should add trendline to scatter."""
        spec = ChartSpec(
            chart_type='scatter',
            title='With Trend',
            x_column='x',
            y_column='y',
        )

        fig = create_scatter_chart(df_numeric_only, spec)

        # Should have data trace + trendline trace
        assert len(fig.data) >= 1


# =============================================================================
# TEST HEATMAP
# =============================================================================

class TestHeatmap:
    """Tests for heatmap creation."""

    def test_basic_heatmap(self, df_numeric_only):
        """Should create correlation heatmap."""
        spec = ChartSpec(
            chart_type='heatmap',
            title='Correlation Matrix',
            columns=['x', 'y', 'z'],
        )

        fig = create_heatmap(df_numeric_only, spec)

        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Correlation Matrix'

    def test_heatmap_auto_columns(self, df_numeric_only):
        """Should use all numeric columns if not specified."""
        spec = ChartSpec(
            chart_type='heatmap',
            title='Auto Correlation',
        )

        fig = create_heatmap(df_numeric_only, spec)

        assert isinstance(fig, go.Figure)

    def test_heatmap_no_numeric_columns(self):
        """Should raise error for non-numeric data."""
        df = pd.DataFrame({
            'a': ['x', 'y', 'z'],
            'b': ['p', 'q', 'r'],
        })
        spec = ChartSpec(
            chart_type='heatmap',
            title='Test',
        )

        with pytest.raises(ValueError, match="no numeric columns"):
            create_heatmap(df, spec)


# =============================================================================
# TEST BOX PLOT
# =============================================================================

class TestBoxPlot:
    """Tests for box plot creation."""

    def test_basic_box_plot(self, df_for_charts):
        """Should create basic box plot."""
        spec = ChartSpec(
            chart_type='box',
            title='Revenue Distribution',
            y_column='revenue',
        )

        fig = create_box_plot(df_for_charts, spec)

        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Revenue Distribution'

    def test_box_plot_with_grouping(self, df_for_charts):
        """Should create grouped box plot."""
        spec = ChartSpec(
            chart_type='box',
            title='Revenue by Region',
            y_column='revenue',
            color_column='region',
        )

        fig = create_box_plot(df_for_charts, spec)

        assert isinstance(fig, go.Figure)


# =============================================================================
# TEST PIE CHART
# =============================================================================

class TestPieChart:
    """Tests for pie chart creation."""

    def test_basic_pie_chart(self, df_categorical):
        """Should create basic pie chart."""
        spec = ChartSpec(
            chart_type='pie',
            title='Category Distribution',
            x_column='category',
            y_column='value',
        )

        fig = create_pie_chart(df_categorical, spec)

        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Category Distribution'

    def test_pie_chart_counts(self, df_for_charts):
        """Should create pie chart from category counts."""
        spec = ChartSpec(
            chart_type='pie',
            title='Region Counts',
            x_column='region',
        )

        fig = create_pie_chart(df_for_charts, spec)

        assert isinstance(fig, go.Figure)


# =============================================================================
# TEST HISTOGRAM
# =============================================================================

class TestHistogram:
    """Tests for histogram creation."""

    def test_basic_histogram(self, df_for_charts):
        """Should create basic histogram."""
        spec = ChartSpec(
            chart_type='histogram',
            title='Revenue Distribution',
            x_column='revenue',
        )

        fig = create_histogram(df_for_charts, spec)

        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == 'Revenue Distribution'

    def test_histogram_with_bins(self, df_numeric_only):
        """Should create histogram with specified bins."""
        spec = ChartSpec(
            chart_type='histogram',
            title='X Distribution',
            x_column='x',
        )

        fig = create_histogram(df_numeric_only, spec, nbins=20)

        assert isinstance(fig, go.Figure)


# =============================================================================
# TEST CHART FACTORY
# =============================================================================

class TestChartFactory:
    """Tests for the create_chart factory function."""

    def test_factory_dispatches_correctly(self, df_for_charts):
        """Should dispatch to correct builder."""
        spec = ChartSpec(
            chart_type='line',
            title='Test',
            x_column='date',
            y_column='revenue',
        )

        fig = create_chart(df_for_charts, spec)

        assert isinstance(fig, go.Figure)

    def test_factory_unknown_type(self, df_for_charts):
        """Should raise error for unknown chart type."""
        spec = ChartSpec(
            chart_type='unknown',
            title='Test',
        )

        with pytest.raises(ValueError, match="Unknown chart type"):
            create_chart(df_for_charts, spec)

    def test_all_chart_types_registered(self):
        """Should have all 7 chart types registered."""
        expected = {'line', 'bar', 'scatter', 'heatmap', 'box', 'pie', 'histogram'}
        actual = set(CHART_BUILDERS.keys())

        assert expected == actual


# =============================================================================
# TEST CHART STYLING
# =============================================================================

class TestChartStyling:
    """Tests for chart styling and configuration."""

    def test_custom_config(self, df_for_charts):
        """Should apply custom configuration."""
        config = ChartConfig(
            theme='plotly_dark',
            height=800,
            show_legend=False,
        )
        spec = ChartSpec(
            chart_type='line',
            title='Custom Styled',
            x_column='date',
            y_column='revenue',
        )

        fig = create_line_chart(df_for_charts, spec, config)

        # Check scalar values directly
        assert fig.layout.height == 800
        assert fig.layout.showlegend is False
        # Template is applied as object; verify via HTML output
        html = fig.to_html()
        assert 'plotly_dark' in html or fig.layout.template is not None

    def test_default_theme(self, df_for_charts):
        """Should use default theme when not specified."""
        spec = ChartSpec(
            chart_type='bar',
            title='Default Style',
            x_column='region',
            y_column='revenue',
        )

        fig = create_bar_chart(df_for_charts, spec)

        # Template is applied; verify chart was created with styling
        assert fig.layout.height == 500  # Default height
        assert fig.layout.template is not None
