"""Correlation discovery and analysis utilities.

This module provides functions for finding and analyzing correlations
between numeric columns in a dataset.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np
from scipy import stats

from .utils import (
    identify_numeric_columns,
    classify_correlation_strength,
    calculate_confidence_score,
    classify_importance,
    safe_numeric_conversion,
)
from .statistics import AnalysisFinding


@dataclass
class Correlation:
    """Relationship between two numeric columns."""
    column1: str
    column2: str
    coefficient: float  # Pearson or Spearman coefficient
    method: str  # 'pearson', 'spearman'
    strength: str  # 'none', 'weak', 'moderate', 'strong', 'very_strong'
    direction: str  # 'positive', 'negative'
    p_value: Optional[float] = None
    is_significant: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'column1': self.column1,
            'column2': self.column2,
            'coefficient': round(self.coefficient, 4),
            'method': self.method,
            'strength': self.strength,
            'direction': self.direction,
            'p_value': round(self.p_value, 6) if self.p_value is not None else None,
            'is_significant': self.is_significant,
        }

    def describe(self) -> str:
        """Generate a human-readable description of the correlation."""
        sign = "positive" if self.direction == "positive" else "negative"
        return (
            f"{self.strength.replace('_', ' ').title()} {sign} correlation "
            f"between '{self.column1}' and '{self.column2}' "
            f"(r={self.coefficient:.3f})"
        )


def calculate_correlation(
    df: pd.DataFrame,
    col1: str,
    col2: str,
    method: str = 'pearson'
) -> Correlation:
    """
    Calculate the correlation between two columns.

    Args:
        df: DataFrame containing the columns
        col1: First column name
        col2: Second column name
        method: Correlation method ('pearson' or 'spearman')

    Returns:
        Correlation object with coefficient and significance
    """
    series1 = df[col1]
    series2 = df[col2]

    # Convert to numeric if needed
    if not pd.api.types.is_numeric_dtype(series1):
        series1 = safe_numeric_conversion(series1)
    if not pd.api.types.is_numeric_dtype(series2):
        series2 = safe_numeric_conversion(series2)

    # Create a combined DataFrame to handle NaN alignment
    combined = pd.DataFrame({'a': series1, 'b': series2}).dropna()

    if len(combined) < 3:
        # Not enough data points
        return Correlation(
            column1=col1,
            column2=col2,
            coefficient=0.0,
            method=method,
            strength='none',
            direction='positive',
            p_value=1.0,
            is_significant=False,
        )

    # Calculate correlation based on method
    if method == 'spearman':
        coef, p_value = stats.spearmanr(combined['a'], combined['b'])
    else:  # pearson
        coef, p_value = stats.pearsonr(combined['a'], combined['b'])

    # Handle edge cases
    if np.isnan(coef):
        coef = 0.0
        p_value = 1.0

    strength = classify_correlation_strength(coef)
    direction = 'positive' if coef >= 0 else 'negative'
    is_significant = p_value < 0.05 if p_value is not None else True

    return Correlation(
        column1=col1,
        column2=col2,
        coefficient=float(coef),
        method=method,
        strength=strength,
        direction=direction,
        p_value=float(p_value) if p_value is not None else None,
        is_significant=is_significant,
    )


def find_all_correlations(
    df: pd.DataFrame,
    min_strength: float = 0.3,
    method: str = 'pearson'
) -> List[Correlation]:
    """
    Find all significant correlations between numeric columns.

    Args:
        df: DataFrame to analyze
        min_strength: Minimum absolute correlation to include (default 0.3)
        method: Correlation method ('pearson' or 'spearman')

    Returns:
        List of Correlation objects sorted by strength (strongest first)
    """
    numeric_cols = identify_numeric_columns(df)
    correlations = []

    # Calculate correlations for all pairs
    for i, col1 in enumerate(numeric_cols):
        for col2 in numeric_cols[i + 1:]:  # Avoid duplicates and self-correlation
            corr = calculate_correlation(df, col1, col2, method)

            # Filter by minimum strength
            if abs(corr.coefficient) >= min_strength and corr.is_significant:
                correlations.append(corr)

    # Sort by absolute coefficient (strongest first)
    correlations.sort(key=lambda c: abs(c.coefficient), reverse=True)

    return correlations


def generate_correlation_matrix(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """
    Generate a correlation matrix for all numeric columns.

    Args:
        df: DataFrame to analyze
        method: Correlation method ('pearson' or 'spearman')

    Returns:
        DataFrame containing the correlation matrix
    """
    numeric_cols = identify_numeric_columns(df)

    if len(numeric_cols) == 0:
        return pd.DataFrame()

    # Get numeric data
    numeric_df = df[numeric_cols].copy()

    # Convert any non-numeric columns
    for col in numeric_df.columns:
        if not pd.api.types.is_numeric_dtype(numeric_df[col]):
            numeric_df[col] = safe_numeric_conversion(numeric_df[col])

    # Calculate correlation matrix
    if method == 'spearman':
        matrix = numeric_df.corr(method='spearman')
    else:
        matrix = numeric_df.corr(method='pearson')

    return matrix


def find_correlation_insights(
    correlations: List[Correlation],
    top_n: int = 10
) -> List[AnalysisFinding]:
    """
    Generate actionable insights from correlation analysis.

    Identifies:
    - Strong positive correlations (potential redundancy)
    - Strong negative correlations (inverse relationships)
    - Moderate correlations worth investigating

    Args:
        correlations: List of Correlation objects to analyze
        top_n: Maximum number of insights to return

    Returns:
        List of AnalysisFinding objects with insights
    """
    findings = []

    for corr in correlations[:top_n]:
        if corr.strength in ('very_strong', 'strong'):
            if corr.direction == 'positive':
                # Strong positive - potential redundancy or causal relationship
                title = f"Strong positive correlation: {corr.column1} ↔ {corr.column2}"
                description = (
                    f"'{corr.column1}' and '{corr.column2}' show a strong positive "
                    f"relationship (r={corr.coefficient:.3f}). "
                    f"When one increases, the other tends to increase as well."
                )
                recommendation = (
                    f"These columns may be measuring related concepts. "
                    f"Consider if one could predict the other, or if both "
                    f"are driven by a common underlying factor."
                )
                importance = 'high'
            else:
                # Strong negative - inverse relationship
                title = f"Strong inverse relationship: {corr.column1} ↔ {corr.column2}"
                description = (
                    f"'{corr.column1}' and '{corr.column2}' show a strong negative "
                    f"relationship (r={corr.coefficient:.3f}). "
                    f"When one increases, the other tends to decrease."
                )
                recommendation = (
                    f"Investigate why these variables move in opposite directions. "
                    f"This could indicate a trade-off or competing factors."
                )
                importance = 'high'

            findings.append(AnalysisFinding(
                category='correlation',
                title=title,
                description=description,
                affected_columns=[corr.column1, corr.column2],
                importance=importance,
                confidence=calculate_confidence_score(
                    sample_size=100,  # Approximate
                    effect_size=abs(corr.coefficient),
                    p_value=corr.p_value,
                ),
                actionable=True,
                recommendation=recommendation,
                supporting_data=corr.to_dict(),
            ))

        elif corr.strength == 'moderate':
            # Moderate correlation - worth noting
            title = f"Moderate correlation: {corr.column1} ↔ {corr.column2}"
            sign = "positive" if corr.direction == "positive" else "negative"
            description = (
                f"'{corr.column1}' and '{corr.column2}' show a moderate {sign} "
                f"relationship (r={corr.coefficient:.3f}). "
                f"This relationship may warrant further investigation."
            )

            findings.append(AnalysisFinding(
                category='correlation',
                title=title,
                description=description,
                affected_columns=[corr.column1, corr.column2],
                importance='medium',
                confidence=calculate_confidence_score(
                    sample_size=100,
                    effect_size=abs(corr.coefficient),
                    p_value=corr.p_value,
                ),
                actionable=False,
                supporting_data=corr.to_dict(),
            ))

    # Look for multicollinearity (multiple strong correlations with same variable)
    column_counts: Dict[str, int] = {}
    for corr in correlations:
        if corr.strength in ('very_strong', 'strong'):
            column_counts[corr.column1] = column_counts.get(corr.column1, 0) + 1
            column_counts[corr.column2] = column_counts.get(corr.column2, 0) + 1

    for col, count in column_counts.items():
        if count >= 3:
            findings.append(AnalysisFinding(
                category='correlation',
                title=f"Multicollinearity concern: {col}",
                description=(
                    f"'{col}' shows strong correlations with {count} other variables. "
                    f"This may indicate redundant information or a key central variable."
                ),
                affected_columns=[col],
                importance='high',
                confidence=0.85,
                actionable=True,
                recommendation=(
                    f"Consider removing correlated variables or using "
                    f"dimensionality reduction (e.g., PCA) if building models."
                ),
                supporting_data={'correlation_count': count},
            ))

    return findings
