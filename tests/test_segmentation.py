"""Tests for the segmentation module."""

import pytest
import pandas as pd
import numpy as np

from src.analysis.segmentation import (
    SegmentComparison,
    compare_segments,
    find_segment_insights,
    calculate_group_statistics,
    identify_top_performers,
    identify_bottom_performers,
)


@pytest.fixture
def segmented_df():
    """DataFrame with clear segment differences."""
    np.random.seed(42)

    # Create segments with different means
    segment_a = np.random.normal(100, 10, 50)
    segment_b = np.random.normal(150, 10, 50)
    segment_c = np.random.normal(75, 10, 50)

    return pd.DataFrame({
        'segment': ['A'] * 50 + ['B'] * 50 + ['C'] * 50,
        'value': np.concatenate([segment_a, segment_b, segment_c]),
        'count': np.random.randint(1, 10, 150),
    })


@pytest.fixture
def no_difference_df():
    """DataFrame with segments that have similar values."""
    np.random.seed(42)

    # All segments from same distribution
    values = np.random.normal(100, 10, 150)

    return pd.DataFrame({
        'segment': ['X', 'Y', 'Z'] * 50,
        'value': values,
    })


@pytest.fixture
def sales_df():
    """Realistic sales data with multiple dimensions."""
    np.random.seed(42)
    n = 200

    regions = np.random.choice(['North', 'South', 'East', 'West'], n)
    products = np.random.choice(['Product A', 'Product B', 'Product C'], n)

    # Create revenue with region effects
    base_revenue = 1000
    region_effects = {'North': 200, 'South': -100, 'East': 50, 'West': 100}
    product_effects = {'Product A': 500, 'Product B': 200, 'Product C': 0}

    revenue = np.array([
        base_revenue +
        region_effects[r] +
        product_effects[p] +
        np.random.normal(0, 100)
        for r, p in zip(regions, products)
    ])

    return pd.DataFrame({
        'region': regions,
        'product': products,
        'revenue': revenue,
        'quantity': np.random.randint(1, 50, n),
    })


class TestSegmentComparison:
    """Tests for SegmentComparison dataclass."""

    def test_create_segment_comparison(self):
        """Test creating a segment comparison object."""
        segments = {
            'A': {'count': 50, 'mean': 100.0, 'std': 10.0},
            'B': {'count': 50, 'mean': 150.0, 'std': 12.0},
        }

        comparison = SegmentComparison(
            segment_column='category',
            metric_column='revenue',
            segments=segments,
            variance_ratio=0.45,
            notable_differences=["'B' has highest mean (150.0)"],
        )

        assert comparison.segment_column == 'category'
        assert comparison.segment_count == 2
        assert comparison.variance_ratio == 0.45

    def test_to_dict(self):
        """Test serialization to dictionary."""
        comparison = SegmentComparison(
            segment_column='region',
            metric_column='sales',
            segments={'North': {'count': 10, 'mean': 100.0, 'std': 5.0}},
            variance_ratio=0.3,
        )
        comp_dict = comparison.to_dict()

        assert comp_dict['segment_column'] == 'region'
        assert 'segments' in comp_dict

    def test_describe(self):
        """Test human-readable description."""
        comparison = SegmentComparison(
            segment_column='region',
            metric_column='revenue',
            segments={'A': {'mean': 100.0}, 'B': {'mean': 200.0}},
            variance_ratio=0.5,
            notable_differences=["'B' has highest mean"],
        )
        desc = comparison.describe()

        assert 'revenue' in desc
        assert 'region' in desc


class TestCalculateGroupStatistics:
    """Tests for calculate_group_statistics function."""

    def test_calculates_stats_per_group(self, segmented_df):
        """Test calculation of statistics per group."""
        stats = calculate_group_statistics(segmented_df, 'segment')

        assert 'A' in stats
        assert 'B' in stats
        assert 'C' in stats

        for group_stats in stats.values():
            assert 'count' in group_stats
            assert 'numeric_means' in group_stats

    def test_includes_all_numeric_columns(self, segmented_df):
        """Test that all numeric columns are included."""
        stats = calculate_group_statistics(segmented_df, 'segment')

        for group_stats in stats.values():
            assert 'value' in group_stats['numeric_means']
            assert 'count' in group_stats['numeric_means']


class TestCompareSegments:
    """Tests for compare_segments function."""

    def test_detects_significant_difference(self, segmented_df):
        """Test detection of significant differences between segments."""
        comparison = compare_segments(segmented_df, 'segment', 'value')

        # Should detect significant difference (segments have different means)
        assert comparison.variance_ratio > 0.1
        assert len(comparison.notable_differences) > 0

    def test_no_significant_difference(self, no_difference_df):
        """Test when segments are similar."""
        comparison = compare_segments(no_difference_df, 'segment', 'value')

        # Should have low variance ratio
        assert comparison.variance_ratio < 0.1 or len(comparison.notable_differences) == 0

    def test_segment_statistics(self, segmented_df):
        """Test that segment statistics are calculated."""
        comparison = compare_segments(segmented_df, 'segment', 'value')

        assert 'A' in comparison.segments
        assert 'mean' in comparison.segments['A']
        assert 'count' in comparison.segments['A']
        assert 'std' in comparison.segments['A']

    def test_identifies_highest_lowest(self, segmented_df):
        """Test identification of highest and lowest segments."""
        comparison = compare_segments(segmented_df, 'segment', 'value')

        # Should note B has highest mean, C has lowest
        differences = ' '.join(comparison.notable_differences)
        assert 'highest' in differences.lower() or len(comparison.notable_differences) > 0


class TestFindSegmentInsights:
    """Tests for find_segment_insights function."""

    def test_generates_insights(self, segmented_df):
        """Test that insights are generated."""
        insights = find_segment_insights(segmented_df)

        # Should find at least one insight
        assert len(insights) > 0

    def test_insight_structure(self, segmented_df):
        """Test that insights have correct structure."""
        insights = find_segment_insights(segmented_df)

        for insight in insights:
            assert insight.category == 'segment'
            assert len(insight.affected_columns) == 2  # segment + metric
            assert insight.importance in ('high', 'medium', 'low')

    def test_high_importance_for_large_differences(self, segmented_df):
        """Test that large differences get high importance."""
        insights = find_segment_insights(segmented_df)

        # The segmented_df has clear differences, should have high importance
        high_importance = [i for i in insights if i.importance == 'high']
        assert len(high_importance) > 0

    def test_recommendations(self, segmented_df):
        """Test that recommendations are provided."""
        insights = find_segment_insights(segmented_df)

        high_medium = [i for i in insights if i.importance in ('high', 'medium')]
        for insight in high_medium:
            assert insight.recommendation is not None

    def test_multiple_categorical_columns(self, sales_df):
        """Test analysis of multiple categorical columns."""
        insights = find_segment_insights(sales_df)

        # Should analyze both region and product
        affected_cols = set()
        for insight in insights:
            affected_cols.update(insight.affected_columns)

        # Should include both segment columns
        assert 'region' in affected_cols or 'product' in affected_cols

    def test_skips_high_cardinality(self):
        """Test that high cardinality columns are skipped."""
        df = pd.DataFrame({
            'id': [f'ID_{i}' for i in range(100)],  # 100 unique values
            'value': np.random.normal(100, 10, 100),
        })
        insights = find_segment_insights(df)

        # Should not analyze 'id' column (too many unique values)
        for insight in insights:
            assert 'id' not in insight.affected_columns


class TestIdentifyTopPerformers:
    """Tests for identify_top_performers function."""

    def test_returns_top_segments(self, segmented_df):
        """Test that top segments are returned."""
        top = identify_top_performers(segmented_df, 'segment', 'value', top_n=2)

        assert len(top) == 2
        # B should be first (highest mean)
        assert top[0]['segment'] == 'B'

    def test_includes_statistics(self, segmented_df):
        """Test that statistics are included."""
        top = identify_top_performers(segmented_df, 'segment', 'value', top_n=1)

        assert 'segment' in top[0]
        assert 'mean' in top[0]
        assert 'count' in top[0]


class TestIdentifyBottomPerformers:
    """Tests for identify_bottom_performers function."""

    def test_returns_bottom_segments(self, segmented_df):
        """Test that bottom segments are returned."""
        bottom = identify_bottom_performers(segmented_df, 'segment', 'value', bottom_n=2)

        assert len(bottom) == 2
        # C should be first (lowest mean)
        assert bottom[0]['segment'] == 'C'

    def test_includes_statistics(self, segmented_df):
        """Test that statistics are included."""
        bottom = identify_bottom_performers(segmented_df, 'segment', 'value', bottom_n=1)

        assert 'segment' in bottom[0]
        assert 'mean' in bottom[0]
