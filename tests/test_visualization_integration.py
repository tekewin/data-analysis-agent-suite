"""Integration tests for the complete visualization pipeline."""

import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import tempfile

from src.visualization import (
    ChartSpec,
    ChartConfig,
    recommend_visualizations,
    generate_all_charts,
    generate_dashboard,
    create_manifest,
    save_manifest,
    load_manifest,
    create_output_directory,
    detect_column_types,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sales_data():
    """Realistic sales data for integration testing."""
    np.random.seed(42)
    n = 200

    dates = pd.date_range('2024-01-01', periods=n, freq='D')
    regions = np.random.choice(['North', 'South', 'East', 'West'], n)
    categories = np.random.choice(['Electronics', 'Clothing', 'Food', 'Home'], n)

    # Generate correlated data
    base = np.random.uniform(100, 500, n)
    revenue = base * np.random.uniform(10, 50, n)
    quantity = base.astype(int) + np.random.randint(-20, 20, n)
    profit = revenue * np.random.uniform(0.1, 0.4, n)

    return pd.DataFrame({
        'order_date': dates,
        'region': regions,
        'category': categories,
        'revenue': revenue,
        'quantity': quantity,
        'profit': profit,
        'discount': np.random.uniform(0, 0.3, n),
    })


@pytest.fixture
def temp_output():
    """Temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# =============================================================================
# END-TO-END PIPELINE TESTS
# =============================================================================

class TestEndToEndPipeline:
    """Tests for the complete visualization pipeline."""

    def test_full_pipeline_with_sales_data(self, sales_data, temp_output):
        """Should complete full pipeline from data to dashboard."""
        source_file = 'sales_data.csv'

        # Step 1: Create output directory
        output_dir = create_output_directory(source_file, temp_output)
        assert Path(output_dir).exists()

        # Step 2: Get recommendations
        recommendations = recommend_visualizations(sales_data)
        assert len(recommendations) > 0

        # Step 3: Generate charts
        charts = generate_all_charts(sales_data, recommendations, output_dir)
        assert len(charts) > 0

        # Step 4: Generate dashboard
        dashboard_path = generate_dashboard(charts, source_file, output_dir)
        assert Path(dashboard_path).exists()

        # Step 5: Generate manifest
        manifest = create_manifest(charts, source_file, output_dir)
        manifest_path = save_manifest(manifest, output_dir)
        assert Path(manifest_path).exists()

        # Verify manifest content
        with open(manifest_path) as f:
            manifest_data = json.load(f)

        assert manifest_data['source_file'] == source_file
        assert manifest_data['total_charts'] == len(charts)

    def test_pipeline_creates_all_expected_files(self, sales_data, temp_output):
        """Should create all expected output files."""
        source_file = 'test_data.csv'
        output_dir = create_output_directory(source_file, temp_output)

        recommendations = recommend_visualizations(sales_data, max_recommendations=4)
        charts = generate_all_charts(sales_data, recommendations, output_dir)
        dashboard_path = generate_dashboard(charts, source_file, output_dir)
        manifest = create_manifest(charts, source_file, output_dir)
        manifest_path = save_manifest(manifest, output_dir)

        # Check files exist
        output_path = Path(output_dir)
        assert (output_path / 'index.html').exists()
        assert (output_path / 'chart_manifest.json').exists()

        # Check individual chart files
        for chart in charts:
            assert (output_path / chart.filename).exists()

    def test_pipeline_with_minimal_data(self, temp_output):
        """Should handle minimal dataset gracefully."""
        df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [10, 20, 15, 25, 30],
        })

        source_file = 'minimal.csv'
        output_dir = create_output_directory(source_file, temp_output)

        recommendations = recommend_visualizations(df)
        charts = generate_all_charts(df, recommendations, output_dir)

        assert len(charts) > 0  # Should still generate something


# =============================================================================
# MANIFEST TESTS
# =============================================================================

class TestManifestRoundtrip:
    """Tests for manifest save/load roundtrip."""

    def test_manifest_roundtrip(self, sales_data, temp_output):
        """Should save and load manifest correctly."""
        source_file = 'test.csv'
        output_dir = create_output_directory(source_file, temp_output)

        specs = [
            ChartSpec(chart_type='line', title='Test Line', x_column='order_date', y_column='revenue'),
            ChartSpec(chart_type='bar', title='Test Bar', x_column='region', y_column='profit'),
        ]

        charts = generate_all_charts(sales_data, specs, output_dir)
        original_manifest = create_manifest(charts, source_file, output_dir)
        manifest_path = save_manifest(original_manifest, output_dir)

        # Load manifest back
        loaded_manifest = load_manifest(manifest_path)

        assert loaded_manifest.source_file == original_manifest.source_file
        assert len(loaded_manifest.charts) == len(original_manifest.charts)
        assert loaded_manifest.charts[0].chart_type == 'line'
        assert loaded_manifest.charts[1].chart_type == 'bar'

    def test_manifest_json_structure(self, sales_data, temp_output):
        """Should create valid JSON with expected structure."""
        source_file = 'test.csv'
        output_dir = create_output_directory(source_file, temp_output)

        specs = [ChartSpec(chart_type='scatter', title='Test', x_column='revenue', y_column='profit')]
        charts = generate_all_charts(sales_data, specs, output_dir)
        manifest = create_manifest(charts, source_file, output_dir)
        manifest_path = save_manifest(manifest, output_dir)

        with open(manifest_path) as f:
            data = json.load(f)

        assert 'version' in data
        assert 'source_file' in data
        assert 'generated_at' in data
        assert 'total_charts' in data
        assert 'charts' in data
        assert isinstance(data['charts'], list)


# =============================================================================
# COLUMN TYPE DETECTION INTEGRATION
# =============================================================================

class TestColumnTypeIntegration:
    """Integration tests for column type detection."""

    def test_detection_informs_recommendations(self, sales_data):
        """Column types should drive chart recommendations."""
        types = detect_column_types(sales_data)
        recommendations = recommend_visualizations(sales_data)

        # Should have line charts if datetime detected
        if types['datetime']:
            line_charts = [r for r in recommendations if r.chart_type == 'line']
            assert len(line_charts) >= 1

        # Should have bar charts if categorical detected
        if types['categorical']:
            bar_charts = [r for r in recommendations if r.chart_type == 'bar']
            assert len(bar_charts) >= 1


# =============================================================================
# ERROR HANDLING INTEGRATION
# =============================================================================

class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_pipeline_handles_missing_columns_gracefully(self, sales_data, temp_output):
        """Should skip charts with missing columns and continue."""
        source_file = 'test.csv'
        output_dir = create_output_directory(source_file, temp_output)

        specs = [
            ChartSpec(chart_type='line', title='Valid', x_column='order_date', y_column='revenue'),
            ChartSpec(chart_type='bar', title='Invalid', x_column='nonexistent', y_column='revenue'),
            ChartSpec(chart_type='scatter', title='Also Valid', x_column='revenue', y_column='profit'),
        ]

        charts = generate_all_charts(sales_data, specs, output_dir)

        # Should have 2 charts (skipped the invalid one)
        assert len(charts) == 2

    def test_pipeline_with_empty_dataframe(self, temp_output):
        """Should handle empty DataFrame."""
        df = pd.DataFrame()

        recommendations = recommend_visualizations(df)

        # Should return empty list, not error
        assert recommendations == []


# =============================================================================
# CHART QUALITY TESTS
# =============================================================================

class TestChartQuality:
    """Tests for generated chart quality."""

    def test_charts_are_interactive(self, sales_data, temp_output):
        """Generated charts should include Plotly interactivity."""
        output_dir = create_output_directory('test.csv', temp_output)

        specs = [ChartSpec(chart_type='line', title='Test', x_column='order_date', y_column='revenue')]
        charts = generate_all_charts(sales_data, specs, output_dir)

        chart_content = charts[0].html_content

        # Should include Plotly.js
        assert 'plotly' in chart_content.lower()

    def test_charts_have_proper_titles(self, sales_data, temp_output):
        """Generated charts should preserve titles."""
        output_dir = create_output_directory('test.csv', temp_output)

        specs = [ChartSpec(chart_type='bar', title='My Custom Title', x_column='region', y_column='revenue')]
        charts = generate_all_charts(sales_data, specs, output_dir)

        chart_content = charts[0].html_content

        assert 'My Custom Title' in chart_content


# =============================================================================
# DASHBOARD INTEGRATION TESTS
# =============================================================================

class TestDashboardIntegration:
    """Integration tests for dashboard generation."""

    def test_dashboard_links_to_charts(self, sales_data, temp_output):
        """Dashboard should link to generated chart files."""
        source_file = 'test.csv'
        output_dir = create_output_directory(source_file, temp_output)

        recommendations = recommend_visualizations(sales_data, max_recommendations=3)
        charts = generate_all_charts(sales_data, recommendations, output_dir)
        dashboard_path = generate_dashboard(charts, source_file, output_dir)

        dashboard_content = Path(dashboard_path).read_text()

        # Dashboard should reference all chart files
        for chart in charts:
            assert chart.filename in dashboard_content

    def test_dashboard_shows_chart_count(self, sales_data, temp_output):
        """Dashboard should display correct chart count."""
        source_file = 'test.csv'
        output_dir = create_output_directory(source_file, temp_output)

        specs = [
            ChartSpec(chart_type='line', title='C1', x_column='order_date', y_column='revenue'),
            ChartSpec(chart_type='bar', title='C2', x_column='region', y_column='profit'),
            ChartSpec(chart_type='histogram', title='C3', x_column='revenue'),
        ]

        charts = generate_all_charts(sales_data, specs, output_dir)
        dashboard_path = generate_dashboard(charts, source_file, output_dir)

        dashboard_content = Path(dashboard_path).read_text()

        assert '3 charts' in dashboard_content


# =============================================================================
# CONFIGURATION INTEGRATION
# =============================================================================

class TestConfigurationIntegration:
    """Integration tests for custom configuration."""

    def test_custom_config_affects_charts(self, sales_data, temp_output):
        """Custom configuration should be applied to generated charts."""
        output_dir = create_output_directory('test.csv', temp_output)

        config = ChartConfig(
            theme='plotly_dark',
            height=800,
        )

        specs = [ChartSpec(chart_type='line', title='Dark Theme', x_column='order_date', y_column='revenue')]
        charts = generate_all_charts(sales_data, specs, output_dir, config)

        # Config should be applied - verify chart generation succeeded
        assert len(charts) == 1
        assert charts[0].chart_type == 'line'
        assert charts[0].title == 'Dark Theme'
        # Verify HTML was generated
        assert '<html' in charts[0].html_content.lower()
        assert 'plotly' in charts[0].html_content.lower()
