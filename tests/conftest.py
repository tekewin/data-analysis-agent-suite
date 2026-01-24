"""Pytest fixtures for data cleaning tests."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os


@pytest.fixture
def sample_df():
    """Basic DataFrame for testing."""
    return pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie', 'Diana'],
        'Age': [25, 30, 35, 40],
        'City': ['NYC', 'LA', 'Chicago', 'Houston'],
    })


@pytest.fixture
def df_with_whitespace():
    """DataFrame with leading/trailing whitespace."""
    return pd.DataFrame({
        'Name': [' Alice ', 'Bob  ', '  Charlie', 'Diana'],
        'City': ['NYC ', ' LA', '  Chicago  ', 'Houston'],
    })


@pytest.fixture
def df_with_duplicates():
    """DataFrame with duplicate rows."""
    return pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Alice', 'Charlie', 'Bob'],
        'Age': [25, 30, 25, 35, 30],
        'City': ['NYC', 'LA', 'NYC', 'Chicago', 'LA'],
    })


@pytest.fixture
def df_with_missing():
    """DataFrame with missing values."""
    return pd.DataFrame({
        'Name': ['Alice', 'Bob', None, 'Diana', 'Edward'],
        'Age': [25, None, 35, 40, None],
        'City': ['NYC', 'LA', 'Chicago', None, 'Houston'],
    })


@pytest.fixture
def df_with_currency():
    """DataFrame with currency-formatted values."""
    return pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Edward'],
        'Amount': ['$1,234.56', '€1.234,56', '($500.00)', '£750.25', '-$100.00'],
    })


@pytest.fixture
def df_with_dates():
    """DataFrame with mixed date formats."""
    return pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Edward'],
        'Date': ['2024-01-15', '01/20/2024', '02-15-2024', '15/03/2024', '2024-04-01'],
    })


@pytest.fixture
def df_with_outliers():
    """DataFrame with outliers in numeric column."""
    return pd.DataFrame({
        'Name': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
        'Value': [10, 12, 11, 13, 10, 12, 11, 100, 10, 12, 11, -50],  # 100 and -50 are outliers
    })


@pytest.fixture
def df_with_encoding_issues():
    """DataFrame with mojibake encoding issues."""
    return pd.DataFrame({
        'Name': ['CafÃ©', 'RÃ©sumÃ©', 'naÃ¯ve', 'Normal'],
        'Notes': ['Has café', 'Normal text', 'More naÃ¯ve', 'Clean'],
    })


@pytest.fixture
def df_with_camel_case_columns():
    """DataFrame with non-snake_case column names."""
    return pd.DataFrame({
        'FirstName': ['Alice', 'Bob'],
        'Last Name': ['Smith', 'Jones'],
        'emailAddress': ['a@b.com', 'b@c.com'],
        'Phone-Number': ['123', '456'],
    })


@pytest.fixture
def temp_csv_file(sample_df):
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_df.to_csv(f, index=False)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_excel_file(sample_df):
    """Create a temporary Excel file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        temp_path = f.name

    sample_df.to_excel(temp_path, index=False)

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# =============================================================================
# REPORTING FIXTURES
# =============================================================================

@pytest.fixture
def sample_analysis_result():
    """Sample AnalysisResult for testing report generation."""
    from src.analysis import (
        AnalysisResult,
        AnalysisFinding,
        DescriptiveStats,
        Correlation,
        TrendAnalysis,
        SegmentComparison,
    )

    findings = [
        AnalysisFinding(
            category='correlation',
            title='Strong correlation: revenue and quantity',
            description='Revenue and quantity show a strong positive correlation (r=0.85).',
            affected_columns=['revenue', 'quantity'],
            importance='high',
            confidence=0.92,
            actionable=True,
            recommendation='Investigate the relationship between revenue and quantity.',
            supporting_data={'coefficient': 0.85},
        ),
        AnalysisFinding(
            category='trend',
            title='Upward trend in sales',
            description='Sales show a consistent upward trend (+15% over period).',
            affected_columns=['sales', 'date'],
            importance='medium',
            confidence=0.78,
            actionable=True,
            recommendation='Monitor sales trajectory for sustainability.',
        ),
        AnalysisFinding(
            category='segment',
            title='Regional differences in profit',
            description='Profit varies significantly across regions.',
            affected_columns=['region', 'profit'],
            importance='low',
            confidence=0.65,
            actionable=False,
        ),
    ]

    descriptive_stats = {
        'revenue': DescriptiveStats(
            column='revenue',
            count=1000,
            missing_count=5,
            mean=5000.0,
            median=4500.0,
            std=1500.0,
            min=500.0,
            max=15000.0,
            q25=3500.0,
            q75=6500.0,
            skewness=0.5,
            kurtosis=0.2,
        ),
        'quantity': DescriptiveStats(
            column='quantity',
            count=1000,
            missing_count=0,
            mean=50.0,
            median=45.0,
            std=15.0,
            min=5.0,
            max=150.0,
            q25=35.0,
            q75=65.0,
            skewness=0.3,
            kurtosis=-0.1,
        ),
    }

    correlations = [
        Correlation(
            column1='revenue',
            column2='quantity',
            coefficient=0.85,
            method='pearson',
            strength='strong',
            direction='positive',
            p_value=0.001,
            is_significant=True,
        ),
    ]

    trends = [
        TrendAnalysis(
            column='sales',
            date_column='date',
            trend_direction='increasing',
            slope=10.5,
            r_squared=0.72,
            growth_rate_pct=15.0,
            seasonality_detected=False,
        ),
    ]

    segments = [
        SegmentComparison(
            segment_column='region',
            metric_column='profit',
            segments={
                'North': {'count': 300, 'mean': 5500.0, 'std': 1200.0},
                'South': {'count': 250, 'mean': 4200.0, 'std': 1100.0},
                'East': {'count': 280, 'mean': 5100.0, 'std': 1300.0},
                'West': {'count': 170, 'mean': 4800.0, 'std': 1000.0},
            },
            variance_ratio=0.15,
            notable_differences=['North has highest mean (5500.0)', 'South has lowest mean (4200.0)'],
        ),
    ]

    return AnalysisResult(
        findings=findings,
        descriptive_stats=descriptive_stats,
        correlations=correlations,
        trends=trends,
        segments=segments,
        depth_level='standard',
        columns_analyzed=10,
        rows_analyzed=1000,
    )


@pytest.fixture
def sample_analysis_json(sample_analysis_result, temp_output_dir):
    """Create a sample analysis JSON file."""
    import json

    data = sample_analysis_result.to_dict()
    data['metadata'] = {
        'source_file': 'test_data.csv',
        'generated_at': '20240124_143022',
    }

    filepath = Path(temp_output_dir) / 'test_analysis_20240124_143022.json'
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    return str(filepath)


@pytest.fixture
def sample_visualization_manifest(temp_output_dir):
    """Create a sample visualization manifest."""
    import json

    viz_dir = Path(temp_output_dir) / 'test_visualizations_20240124_143025'
    viz_dir.mkdir(parents=True)

    manifest = {
        'version': '1.0',
        'source_file': 'test_data.csv',
        'generated_at': '2024-01-24T14:30:25',
        'output_dir': str(viz_dir),
        'dashboard_file': 'index.html',
        'total_charts': 3,
        'charts': [
            {
                'id': 'abc123',
                'chart_type': 'line',
                'title': 'Sales Over Time',
                'filename': 'line_sales_over_time.html',
                'columns_used': ['date', 'sales'],
                'description': 'Trend of sales over time',
                'generated_at': '2024-01-24T14:30:25',
            },
            {
                'id': 'def456',
                'chart_type': 'bar',
                'title': 'Revenue by Region',
                'filename': 'bar_revenue_by_region.html',
                'columns_used': ['region', 'revenue'],
                'description': 'Revenue comparison across regions',
                'generated_at': '2024-01-24T14:30:26',
            },
            {
                'id': 'ghi789',
                'chart_type': 'scatter',
                'title': 'Revenue vs Quantity',
                'filename': 'scatter_revenue_vs_quantity.html',
                'columns_used': ['revenue', 'quantity'],
                'description': 'Correlation between revenue and quantity',
                'generated_at': '2024-01-24T14:30:27',
            },
        ],
    }

    manifest_path = viz_dir / 'chart_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return str(manifest_path)


@pytest.fixture
def sample_report_input(sample_analysis_result, sample_visualization_manifest):
    """Create a sample ReportInput for testing."""
    from src.reporting import ReportInput, load_visualization_manifest

    viz_manifest = load_visualization_manifest(sample_visualization_manifest)

    return ReportInput(
        source_file='test_data.csv',
        analysis_result=sample_analysis_result,
        visualization_manifest=viz_manifest,
        audience='business',
        context='Quarterly sales analysis for Q1 2024.',
        emphasis_areas=['revenue', 'region'],
    )


# =============================================================================
# SUMMARIZATION FIXTURES
# =============================================================================

@pytest.fixture
def sample_report_content():
    """Sample markdown report content for testing executive summary generation."""
    return """# Sales Data Analysis Report

**Generated:** 2024-01-24 14:45:00
**Source:** `test_data.csv`
**Style:** Business

---

## Executive Summary

Revenue increased 15% quarter-over-quarter, driven primarily by the North region.
The analysis identified 18 findings across correlations, trends, and segments.
Consider expanding the sales team in high-performing regions.

---

## 1. Introduction

### 1.1 Objective
This report analyzes quarterly sales data to identify trends and opportunities.

### 1.2 Data Source
Data was collected from the internal sales database covering Q1 2024.

---

## 2. Data Overview

### 2.1 Dataset Description
- **Rows**: 1,000
- **Columns**: 10
- **Period**: January - March 2024

---

## 3. Key Findings

### 3.1 Strong correlation: revenue and quantity
Revenue and quantity show a strong positive correlation (r=0.85).

### 3.2 Upward trend in sales
Sales show a consistent upward trend (+15% over period).

### 3.3 Regional differences in profit
Profit varies significantly across regions.

---

*Generated by @report-writer agent*
"""


@pytest.fixture
def sample_report_file(sample_report_content, temp_output_dir):
    """Create a sample report markdown file."""
    filepath = Path(temp_output_dir) / 'test_report_business_20240124_144500.md'
    with open(filepath, 'w') as f:
        f.write(sample_report_content)
    return str(filepath)


@pytest.fixture
def sample_summary_input(sample_analysis_result, sample_report_content):
    """Sample SummaryInput for testing executive summary generation."""
    from src.summarization import SummaryInput

    return SummaryInput(
        source_file='test_data.csv',
        report_content=sample_report_content,
        analysis_result=sample_analysis_result,
        visualization_manifest=None,
        context='Q1 2024 sales analysis',
        emphasis_areas=['revenue', 'region'],
    )


@pytest.fixture
def sample_extracted_metrics():
    """Sample ExtractedMetric objects for testing."""
    from src.summarization import ExtractedMetric

    return [
        ExtractedMetric(
            name='Revenue (avg)',
            value='$5.0K',
            change='+15%',
            status='good',
        ),
        ExtractedMetric(
            name='Quantity (avg)',
            value='50',
            change=None,
            status='neutral',
        ),
        ExtractedMetric(
            name='Sales Trend',
            value='Increasing',
            change='+15.0%',
            status='good',
        ),
    ]


@pytest.fixture
def sample_extracted_findings():
    """Sample ExtractedFinding objects for testing."""
    from src.summarization import ExtractedFinding

    return [
        ExtractedFinding(
            title='Strong correlation: revenue and quantity',
            impact='Revenue and quantity show a strong positive correlation (r=0.85).',
            action='Investigate the relationship between revenue and quantity.',
            importance='high',
        ),
        ExtractedFinding(
            title='Upward trend in sales',
            impact='Sales show a consistent upward trend (+15% over period).',
            action='Monitor sales trajectory for sustainability.',
            importance='medium',
        ),
        ExtractedFinding(
            title='Regional differences in profit',
            impact='Profit varies significantly across regions.',
            action='Monitor this metric for future changes.',
            importance='low',
        ),
    ]


@pytest.fixture
def sample_extracted_data(sample_extracted_metrics, sample_extracted_findings):
    """Sample ExtractedData for testing."""
    from src.summarization import ExtractedData

    return ExtractedData(
        bluf="Revenue increased 15% driven by strong correlation with quantity. Sales trend is positive with consistent growth. Consider expanding operations in high-performing regions.",
        metrics=sample_extracted_metrics,
        top_findings=sample_extracted_findings,
        recommended_actions=[
            'Investigate the relationship between revenue and quantity.',
            'Monitor sales trajectory for sustainability.',
            'Review regional performance for optimization.',
        ],
        risks=[
            'Data quality: Some columns have missing values',
            'Findings should be validated with domain expertise',
        ],
        source_report='test_data.csv',
        analysis_period='Based on date',
    )


@pytest.fixture
def sample_summary_config():
    """Sample SummaryConfig for testing."""
    from src.summarization import SummaryConfig

    return SummaryConfig(
        title='Test Data',
        max_findings=3,
        max_actions=3,
        max_risks=3,
        max_metrics=5,
        include_metrics_table=True,
        include_chart_references=True,
    )
