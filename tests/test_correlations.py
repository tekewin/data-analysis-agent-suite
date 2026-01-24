"""Tests for the correlations module."""

import pytest
import pandas as pd
import numpy as np

from src.analysis.correlations import (
    Correlation,
    calculate_correlation,
    find_all_correlations,
    generate_correlation_matrix,
    find_correlation_insights,
)


@pytest.fixture
def correlated_df():
    """DataFrame with known correlations."""
    np.random.seed(42)
    n = 100

    x = np.random.normal(0, 1, n)
    y = 2 * x + np.random.normal(0, 0.5, n)  # Strong positive correlation
    z = -1.5 * x + np.random.normal(0, 0.5, n)  # Strong negative correlation
    w = np.random.normal(0, 1, n)  # No correlation

    return pd.DataFrame({
        'x': x,
        'y': y,
        'z': z,
        'w': w,
        'category': ['A', 'B'] * 50,  # Non-numeric column
    })


@pytest.fixture
def uncorrelated_df():
    """DataFrame with no significant correlations."""
    np.random.seed(42)
    n = 100

    return pd.DataFrame({
        'a': np.random.normal(0, 1, n),
        'b': np.random.normal(0, 1, n),
        'c': np.random.normal(0, 1, n),
    })


class TestCorrelation:
    """Tests for Correlation dataclass."""

    def test_create_correlation(self):
        """Test creating a correlation object."""
        corr = Correlation(
            column1='sales',
            column2='marketing',
            coefficient=0.85,
            method='pearson',
            strength='strong',
            direction='positive',
            p_value=0.001,
            is_significant=True,
        )

        assert corr.column1 == 'sales'
        assert corr.coefficient == 0.85
        assert corr.strength == 'strong'
        assert corr.direction == 'positive'

    def test_to_dict(self):
        """Test serialization to dictionary."""
        corr = Correlation(
            column1='a',
            column2='b',
            coefficient=0.75,
            method='spearman',
            strength='moderate',
            direction='positive',
        )
        corr_dict = corr.to_dict()

        assert corr_dict['column1'] == 'a'
        assert corr_dict['method'] == 'spearman'
        assert 'coefficient' in corr_dict

    def test_describe(self):
        """Test human-readable description."""
        corr = Correlation(
            column1='revenue',
            column2='customers',
            coefficient=0.82,
            method='pearson',
            strength='strong',
            direction='positive',
        )
        desc = corr.describe()

        assert 'Strong' in desc
        assert 'positive' in desc
        assert 'revenue' in desc
        assert 'customers' in desc


class TestCalculateCorrelation:
    """Tests for calculate_correlation function."""

    def test_strong_positive_correlation(self, correlated_df):
        """Test detection of strong positive correlation."""
        corr = calculate_correlation(correlated_df, 'x', 'y')

        assert corr.coefficient > 0.8
        assert corr.direction == 'positive'
        assert corr.strength in ('strong', 'very_strong')
        assert corr.is_significant == True  # Use == for numpy bool compatibility

    def test_strong_negative_correlation(self, correlated_df):
        """Test detection of strong negative correlation."""
        corr = calculate_correlation(correlated_df, 'x', 'z')

        assert corr.coefficient < -0.8
        assert corr.direction == 'negative'
        assert corr.strength in ('strong', 'very_strong')

    def test_no_correlation(self, correlated_df):
        """Test detection of no significant correlation."""
        corr = calculate_correlation(correlated_df, 'x', 'w')

        assert abs(corr.coefficient) < 0.3
        assert corr.strength in ('none', 'weak')

    def test_pearson_method(self, correlated_df):
        """Test Pearson correlation method."""
        corr = calculate_correlation(correlated_df, 'x', 'y', method='pearson')

        assert corr.method == 'pearson'

    def test_spearman_method(self, correlated_df):
        """Test Spearman correlation method."""
        corr = calculate_correlation(correlated_df, 'x', 'y', method='spearman')

        assert corr.method == 'spearman'
        # Should still detect strong correlation
        assert abs(corr.coefficient) > 0.7

    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        df = pd.DataFrame({
            'a': [1, 2],
            'b': [3, 4],
        })
        corr = calculate_correlation(df, 'a', 'b')

        assert corr.is_significant is False

    def test_with_missing_values(self):
        """Test handling of missing values."""
        df = pd.DataFrame({
            'a': [1, 2, None, 4, 5, 6, 7, 8, 9, 10],
            'b': [2, 4, 6, None, 10, 12, 14, 16, 18, 20],
        })
        corr = calculate_correlation(df, 'a', 'b')

        # Should still calculate correlation on available pairs
        assert corr.coefficient > 0.9


class TestFindAllCorrelations:
    """Tests for find_all_correlations function."""

    def test_finds_significant_correlations(self, correlated_df):
        """Test finding significant correlations."""
        correlations = find_all_correlations(correlated_df, min_strength=0.3)

        # Should find x-y and x-z correlations
        assert len(correlations) >= 2

        # Should not include non-numeric 'category' column
        for corr in correlations:
            assert 'category' not in (corr.column1, corr.column2)

    def test_sorted_by_strength(self, correlated_df):
        """Test that results are sorted by strength."""
        correlations = find_all_correlations(correlated_df)

        if len(correlations) >= 2:
            for i in range(len(correlations) - 1):
                assert abs(correlations[i].coefficient) >= abs(correlations[i + 1].coefficient)

    def test_no_self_correlation(self, correlated_df):
        """Test that self-correlations are not included."""
        correlations = find_all_correlations(correlated_df)

        for corr in correlations:
            assert corr.column1 != corr.column2

    def test_no_duplicates(self, correlated_df):
        """Test that correlations are not duplicated (A-B and B-A)."""
        correlations = find_all_correlations(correlated_df)

        pairs = set()
        for corr in correlations:
            pair = tuple(sorted([corr.column1, corr.column2]))
            assert pair not in pairs
            pairs.add(pair)

    def test_min_strength_filter(self, uncorrelated_df):
        """Test filtering by minimum correlation strength."""
        correlations = find_all_correlations(uncorrelated_df, min_strength=0.5)

        # Uncorrelated data should have few or no strong correlations
        for corr in correlations:
            assert abs(corr.coefficient) >= 0.5

    def test_empty_result_for_uncorrelated(self, uncorrelated_df):
        """Test empty result for uncorrelated data with high threshold."""
        correlations = find_all_correlations(uncorrelated_df, min_strength=0.7)

        # Should find very few or no correlations above 0.7
        assert len(correlations) <= 1


class TestGenerateCorrelationMatrix:
    """Tests for generate_correlation_matrix function."""

    def test_matrix_structure(self, correlated_df):
        """Test that matrix has correct structure."""
        matrix = generate_correlation_matrix(correlated_df)

        # Should only include numeric columns
        assert 'category' not in matrix.columns
        assert 'x' in matrix.columns
        assert 'y' in matrix.columns

        # Should be square
        assert matrix.shape[0] == matrix.shape[1]

    def test_diagonal_is_one(self, correlated_df):
        """Test that diagonal elements are 1.0."""
        matrix = generate_correlation_matrix(correlated_df)

        for col in matrix.columns:
            assert abs(matrix.loc[col, col] - 1.0) < 0.001

    def test_symmetric_matrix(self, correlated_df):
        """Test that matrix is symmetric."""
        matrix = generate_correlation_matrix(correlated_df)

        for i, col1 in enumerate(matrix.columns):
            for col2 in matrix.columns[i + 1:]:
                assert abs(matrix.loc[col1, col2] - matrix.loc[col2, col1]) < 0.001

    def test_spearman_method(self, correlated_df):
        """Test Spearman correlation matrix."""
        matrix = generate_correlation_matrix(correlated_df, method='spearman')

        assert matrix.shape[0] > 0


class TestFindCorrelationInsights:
    """Tests for find_correlation_insights function."""

    def test_generates_insights(self, correlated_df):
        """Test that insights are generated for correlations."""
        correlations = find_all_correlations(correlated_df)
        insights = find_correlation_insights(correlations)

        # Should generate at least one insight for strong correlations
        assert len(insights) > 0

    def test_insight_structure(self, correlated_df):
        """Test that insights have correct structure."""
        correlations = find_all_correlations(correlated_df)
        insights = find_correlation_insights(correlations)

        for insight in insights:
            assert insight.category == 'correlation'
            assert len(insight.affected_columns) >= 2
            assert insight.importance in ('high', 'medium', 'low')

    def test_strong_correlation_high_importance(self, correlated_df):
        """Test that strong correlations get high importance."""
        correlations = find_all_correlations(correlated_df)
        insights = find_correlation_insights(correlations)

        # At least one should be high importance for strong correlations
        high_importance = [i for i in insights if i.importance == 'high']
        assert len(high_importance) > 0

    def test_recommendations_for_strong(self, correlated_df):
        """Test that recommendations are provided for strong correlations."""
        correlations = find_all_correlations(correlated_df)
        insights = find_correlation_insights(correlations)

        # Strong correlations should have recommendations
        strong_insights = [i for i in insights if i.importance == 'high']
        for insight in strong_insights:
            assert insight.recommendation is not None

    def test_multicollinearity_detection(self):
        """Test detection of multicollinearity."""
        np.random.seed(42)
        n = 100

        x = np.random.normal(0, 1, n)
        # Multiple columns strongly correlated with x
        y1 = x + np.random.normal(0, 0.1, n)
        y2 = x + np.random.normal(0, 0.1, n)
        y3 = x + np.random.normal(0, 0.1, n)
        y4 = x + np.random.normal(0, 0.1, n)

        df = pd.DataFrame({'x': x, 'y1': y1, 'y2': y2, 'y3': y3, 'y4': y4})
        correlations = find_all_correlations(df)
        insights = find_correlation_insights(correlations)

        # Should detect multicollinearity
        multicollinearity = [i for i in insights if 'multicollinearity' in i.title.lower()]
        assert len(multicollinearity) > 0
