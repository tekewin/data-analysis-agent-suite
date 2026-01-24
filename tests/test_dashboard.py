"""Tests for dashboard generation."""

import pytest
import tempfile
from pathlib import Path

from src.visualization import (
    GeneratedChart,
    generate_dashboard,
    create_chart_card_html,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_charts():
    """Sample GeneratedChart objects for testing."""
    return [
        GeneratedChart(
            chart_type='line',
            title='Revenue Over Time',
            filename='line_revenue_over_time.html',
            filepath='/path/to/line_revenue_over_time.html',
            columns_used=['date', 'revenue'],
            description='Trend of revenue over time',
            html_content='<html><body>Line Chart</body></html>',
        ),
        GeneratedChart(
            chart_type='bar',
            title='Sales by Region',
            filename='bar_sales_by_region.html',
            filepath='/path/to/bar_sales_by_region.html',
            columns_used=['region', 'sales'],
            description='Comparison of sales across regions',
            html_content='<html><body>Bar Chart</body></html>',
        ),
        GeneratedChart(
            chart_type='scatter',
            title='Price vs Quantity',
            filename='scatter_price_vs_quantity.html',
            filepath='/path/to/scatter_price_vs_quantity.html',
            columns_used=['price', 'quantity', 'category'],
            description='Relationship between price and quantity',
            html_content='<html><body>Scatter Chart</body></html>',
        ),
    ]


@pytest.fixture
def temp_output():
    """Temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# =============================================================================
# TEST CHART CARD HTML
# =============================================================================

class TestChartCardHtml:
    """Tests for individual chart card HTML generation."""

    def test_create_chart_card_basic(self, sample_charts):
        """Should create HTML card for a chart."""
        chart = sample_charts[0]
        html = create_chart_card_html(chart)

        assert 'Revenue Over Time' in html
        assert 'line' in html.lower()
        assert 'line_revenue_over_time.html' in html

    def test_chart_card_includes_columns(self, sample_charts):
        """Should include column tags in card."""
        chart = sample_charts[0]
        html = create_chart_card_html(chart)

        assert 'date' in html
        assert 'revenue' in html

    def test_chart_card_includes_description(self, sample_charts):
        """Should include description in card."""
        chart = sample_charts[0]
        html = create_chart_card_html(chart)

        assert 'Trend of revenue over time' in html

    def test_chart_card_limits_columns(self):
        """Should limit displayed columns to 5."""
        chart = GeneratedChart(
            chart_type='heatmap',
            title='Many Columns',
            filename='test.html',
            filepath='/path/test.html',
            columns_used=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],
            description='Test',
            html_content='<html></html>',
        )

        html = create_chart_card_html(chart)

        # Should show first 5 and "+3 more"
        assert '+3 more' in html


# =============================================================================
# TEST DASHBOARD GENERATION
# =============================================================================

class TestDashboardGeneration:
    """Tests for dashboard HTML generation."""

    def test_generate_dashboard_basic(self, sample_charts, temp_output):
        """Should generate dashboard HTML file."""
        dashboard_path = generate_dashboard(
            charts=sample_charts,
            source_file='test_data.csv',
            output_dir=temp_output,
        )

        assert Path(dashboard_path).exists()
        assert dashboard_path.endswith('index.html')

    def test_dashboard_contains_all_charts(self, sample_charts, temp_output):
        """Should include all charts in dashboard."""
        dashboard_path = generate_dashboard(
            charts=sample_charts,
            source_file='test_data.csv',
            output_dir=temp_output,
        )

        content = Path(dashboard_path).read_text()

        assert 'Revenue Over Time' in content
        assert 'Sales by Region' in content
        assert 'Price vs Quantity' in content

    def test_dashboard_includes_metadata(self, sample_charts, temp_output):
        """Should include source file and chart count."""
        dashboard_path = generate_dashboard(
            charts=sample_charts,
            source_file='sales_data.csv',
            output_dir=temp_output,
        )

        content = Path(dashboard_path).read_text()

        assert 'sales_data.csv' in content
        assert '3 charts' in content

    def test_dashboard_custom_title(self, sample_charts, temp_output):
        """Should use custom title when provided."""
        dashboard_path = generate_dashboard(
            charts=sample_charts,
            source_file='test.csv',
            output_dir=temp_output,
            title='My Custom Dashboard',
        )

        content = Path(dashboard_path).read_text()

        assert 'My Custom Dashboard' in content

    def test_dashboard_includes_iframes(self, sample_charts, temp_output):
        """Should include iframes for chart embedding."""
        dashboard_path = generate_dashboard(
            charts=sample_charts,
            source_file='test.csv',
            output_dir=temp_output,
        )

        content = Path(dashboard_path).read_text()

        assert '<iframe' in content
        assert 'line_revenue_over_time.html' in content

    def test_dashboard_includes_styling(self, sample_charts, temp_output):
        """Should include CSS styling."""
        dashboard_path = generate_dashboard(
            charts=sample_charts,
            source_file='test.csv',
            output_dir=temp_output,
        )

        content = Path(dashboard_path).read_text()

        assert '<style>' in content
        assert 'chart-grid' in content
        assert 'chart-card' in content

    def test_dashboard_empty_charts_error(self, temp_output):
        """Should raise error for empty chart list."""
        with pytest.raises(ValueError, match="no charts"):
            generate_dashboard(
                charts=[],
                source_file='test.csv',
                output_dir=temp_output,
            )

    def test_dashboard_creates_directory(self, sample_charts, temp_output):
        """Should create output directory if needed."""
        nested_dir = Path(temp_output) / 'nested' / 'path'

        dashboard_path = generate_dashboard(
            charts=sample_charts,
            source_file='test.csv',
            output_dir=str(nested_dir),
        )

        assert Path(dashboard_path).exists()


# =============================================================================
# TEST DASHBOARD STRUCTURE
# =============================================================================

class TestDashboardStructure:
    """Tests for dashboard HTML structure."""

    def test_dashboard_is_valid_html(self, sample_charts, temp_output):
        """Should generate valid HTML structure."""
        dashboard_path = generate_dashboard(
            charts=sample_charts,
            source_file='test.csv',
            output_dir=temp_output,
        )

        content = Path(dashboard_path).read_text()

        assert '<!DOCTYPE html>' in content
        assert '<html' in content
        assert '</html>' in content
        assert '<head>' in content
        assert '<body>' in content

    def test_dashboard_responsive_meta(self, sample_charts, temp_output):
        """Should include responsive viewport meta tag."""
        dashboard_path = generate_dashboard(
            charts=sample_charts,
            source_file='test.csv',
            output_dir=temp_output,
        )

        content = Path(dashboard_path).read_text()

        assert 'viewport' in content

    def test_dashboard_includes_header(self, sample_charts, temp_output):
        """Should include header section."""
        dashboard_path = generate_dashboard(
            charts=sample_charts,
            source_file='test.csv',
            output_dir=temp_output,
        )

        content = Path(dashboard_path).read_text()

        assert 'class="header"' in content

    def test_dashboard_includes_footer(self, sample_charts, temp_output):
        """Should include footer section."""
        dashboard_path = generate_dashboard(
            charts=sample_charts,
            source_file='test.csv',
            output_dir=temp_output,
        )

        content = Path(dashboard_path).read_text()

        assert 'class="footer"' in content
        assert 'Data Analysis Agent Suite' in content
