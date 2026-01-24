"""Segmentation analysis utilities for category comparisons.

This module provides functions for comparing groups within categorical
data and discovering meaningful segment differences.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from scipy import stats

from .utils import (
    identify_numeric_columns,
    identify_categorical_columns,
    calculate_confidence_score,
    classify_importance,
    safe_numeric_conversion,
)
from .statistics import AnalysisFinding


@dataclass
class SegmentComparison:
    """Comparison of a metric across different category segments."""
    segment_column: str  # The column used for grouping
    metric_column: str  # The column being compared
    segments: Dict[str, Dict[str, float]]  # {segment_name: {mean, count, std, etc.}}
    variance_ratio: float  # Between-group vs within-group variance
    notable_differences: List[str] = field(default_factory=list)  # Human-readable

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'segment_column': self.segment_column,
            'metric_column': self.metric_column,
            'segments': self.segments,
            'variance_ratio': round(self.variance_ratio, 4),
            'notable_differences': self.notable_differences,
        }

    @property
    def segment_count(self) -> int:
        """Number of segments."""
        return len(self.segments)

    def describe(self) -> str:
        """Generate a human-readable description."""
        if not self.notable_differences:
            return (
                f"'{self.metric_column}' shows no significant differences "
                f"across '{self.segment_column}' segments."
            )

        return (
            f"'{self.metric_column}' varies across '{self.segment_column}' segments: "
            + "; ".join(self.notable_differences[:3])
        )


def calculate_group_statistics(
    df: pd.DataFrame,
    group_col: str
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate statistics for each group in a categorical column.

    Args:
        df: DataFrame to analyze
        group_col: Categorical column to group by

    Returns:
        Dictionary mapping group names to their statistics
    """
    numeric_cols = identify_numeric_columns(df)
    group_stats = {}

    for group_name, group_df in df.groupby(group_col):
        group_stats[str(group_name)] = {
            'count': len(group_df),
            'numeric_means': {},
            'numeric_stds': {},
        }

        for col in numeric_cols:
            if col == group_col:
                continue

            series = group_df[col]
            if not pd.api.types.is_numeric_dtype(series):
                series = safe_numeric_conversion(series)

            non_null = series.dropna()
            if len(non_null) > 0:
                group_stats[str(group_name)]['numeric_means'][col] = float(non_null.mean())
                group_stats[str(group_name)]['numeric_stds'][col] = float(non_null.std()) if len(non_null) > 1 else 0.0

    return group_stats


def compare_segments(
    df: pd.DataFrame,
    segment_col: str,
    metric_col: str
) -> SegmentComparison:
    """
    Compare a numeric metric across categorical segments.

    Uses ANOVA F-test to determine if differences are significant,
    and calculates variance ratio to quantify effect size.

    Args:
        df: DataFrame containing the data
        segment_col: Categorical column defining segments
        metric_col: Numeric column to compare

    Returns:
        SegmentComparison with statistics and notable differences
    """
    temp_df = df[[segment_col, metric_col]].copy()

    # Ensure metric is numeric
    if not pd.api.types.is_numeric_dtype(temp_df[metric_col]):
        temp_df[metric_col] = safe_numeric_conversion(temp_df[metric_col])

    temp_df = temp_df.dropna()

    # Calculate per-segment statistics
    segments = {}
    groups = []

    for segment_name, group_df in temp_df.groupby(segment_col):
        values = group_df[metric_col].values
        if len(values) > 0:
            segments[str(segment_name)] = {
                'count': len(values),
                'mean': float(np.mean(values)),
                'std': float(np.std(values)) if len(values) > 1 else 0.0,
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'median': float(np.median(values)),
            }
            groups.append(values)

    # Calculate variance ratio (eta-squared from ANOVA)
    variance_ratio = 0.0
    notable_differences = []

    if len(groups) >= 2:
        # Perform one-way ANOVA
        try:
            f_stat, p_value = stats.f_oneway(*groups)

            if not np.isnan(f_stat):
                # Calculate eta-squared (effect size)
                grand_mean = temp_df[metric_col].mean()
                ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)
                ss_total = sum((temp_df[metric_col] - grand_mean) ** 2)

                if ss_total > 0:
                    variance_ratio = ss_between / ss_total

                # Generate notable differences
                if p_value < 0.05:
                    # Find the segment with highest and lowest mean
                    sorted_segments = sorted(
                        segments.items(),
                        key=lambda x: x[1]['mean'],
                        reverse=True
                    )

                    if len(sorted_segments) >= 2:
                        highest = sorted_segments[0]
                        lowest = sorted_segments[-1]

                        diff_pct = 0
                        if lowest[1]['mean'] != 0:
                            diff_pct = ((highest[1]['mean'] - lowest[1]['mean']) / abs(lowest[1]['mean'])) * 100

                        notable_differences.append(
                            f"'{highest[0]}' has highest mean ({highest[1]['mean']:.2f})"
                        )
                        notable_differences.append(
                            f"'{lowest[0]}' has lowest mean ({lowest[1]['mean']:.2f})"
                        )

                        if abs(diff_pct) > 10:
                            notable_differences.append(
                                f"{abs(diff_pct):.0f}% difference between highest and lowest"
                            )

        except Exception:
            pass

    return SegmentComparison(
        segment_column=segment_col,
        metric_column=metric_col,
        segments=segments,
        variance_ratio=variance_ratio,
        notable_differences=notable_differences,
    )


def find_segment_insights(df: pd.DataFrame) -> List[AnalysisFinding]:
    """
    Analyze all categorical-numeric combinations for segment insights.

    Automatically discovers meaningful differences across categories.

    Args:
        df: DataFrame to analyze

    Returns:
        List of AnalysisFinding objects with segment insights
    """
    findings = []
    categorical_cols = identify_categorical_columns(df)
    numeric_cols = identify_numeric_columns(df)

    for cat_col in categorical_cols:
        # Skip if too many or too few categories
        n_unique = df[cat_col].nunique()
        if n_unique < 2 or n_unique > 20:
            continue

        for num_col in numeric_cols:
            comparison = compare_segments(df, cat_col, num_col)

            # Skip if no significant differences
            if not comparison.notable_differences or comparison.variance_ratio < 0.05:
                continue

            # Determine importance based on variance ratio (effect size)
            if comparison.variance_ratio >= 0.25:
                importance = 'high'
                effect = "large"
            elif comparison.variance_ratio >= 0.10:
                importance = 'medium'
                effect = "moderate"
            else:
                importance = 'low'
                effect = "small"

            title = f"Significant {num_col} differences by {cat_col}"
            description = (
                f"'{num_col}' shows {effect} differences across '{cat_col}' segments "
                f"(variance ratio: {comparison.variance_ratio:.1%}). "
                + comparison.notable_differences[0] + "."
            )

            # Generate recommendation
            recommendation = None
            if importance in ('high', 'medium'):
                sorted_segs = sorted(
                    comparison.segments.items(),
                    key=lambda x: x[1]['mean'],
                    reverse=True
                )
                if len(sorted_segs) >= 2:
                    recommendation = (
                        f"Consider segmenting analysis by '{cat_col}'. "
                        f"'{sorted_segs[0][0]}' and '{sorted_segs[-1][0]}' "
                        f"show the most different '{num_col}' patterns."
                    )

            findings.append(AnalysisFinding(
                category='segment',
                title=title,
                description=description,
                affected_columns=[cat_col, num_col],
                importance=importance,
                confidence=calculate_confidence_score(
                    sample_size=sum(s['count'] for s in comparison.segments.values()),
                    effect_size=comparison.variance_ratio,
                ),
                actionable=importance in ('high', 'medium'),
                recommendation=recommendation,
                supporting_data=comparison.to_dict(),
            ))

    return findings


def identify_top_performers(
    df: pd.DataFrame,
    segment_col: str,
    metric_col: str,
    top_n: int = 3
) -> List[Dict[str, Any]]:
    """
    Identify the top performing segments for a given metric.

    Args:
        df: DataFrame to analyze
        segment_col: Categorical column defining segments
        metric_col: Numeric column to rank by
        top_n: Number of top segments to return

    Returns:
        List of dictionaries with segment info sorted by mean metric
    """
    comparison = compare_segments(df, segment_col, metric_col)

    sorted_segments = sorted(
        comparison.segments.items(),
        key=lambda x: x[1]['mean'],
        reverse=True
    )

    return [
        {'segment': name, **stats}
        for name, stats in sorted_segments[:top_n]
    ]


def identify_bottom_performers(
    df: pd.DataFrame,
    segment_col: str,
    metric_col: str,
    bottom_n: int = 3
) -> List[Dict[str, Any]]:
    """
    Identify the bottom performing segments for a given metric.

    Args:
        df: DataFrame to analyze
        segment_col: Categorical column defining segments
        metric_col: Numeric column to rank by
        bottom_n: Number of bottom segments to return

    Returns:
        List of dictionaries with segment info sorted by mean metric (ascending)
    """
    comparison = compare_segments(df, segment_col, metric_col)

    sorted_segments = sorted(
        comparison.segments.items(),
        key=lambda x: x[1]['mean']
    )

    return [
        {'segment': name, **stats}
        for name, stats in sorted_segments[:bottom_n]
    ]
