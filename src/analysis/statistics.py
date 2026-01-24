"""Statistical analysis utilities for descriptive statistics and distributions.

This module provides core statistical calculations, distribution analysis,
and the main dataclasses used throughout the analysis pipeline.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from scipy import stats

from .utils import (
    identify_numeric_columns,
    calculate_confidence_score,
    classify_importance,
    safe_numeric_conversion,
)

if TYPE_CHECKING:
    from .correlations import Correlation
    from .trends import TrendAnalysis
    from .segmentation import SegmentComparison


@dataclass
class DescriptiveStats:
    """Statistics for a single numeric column."""
    column: str
    count: int
    missing_count: int
    mean: float
    median: float
    std: float
    min: float
    max: float
    q25: float
    q75: float
    skewness: float
    kurtosis: float

    @property
    def iqr(self) -> float:
        """Interquartile range."""
        return self.q75 - self.q25

    @property
    def missing_pct(self) -> float:
        """Percentage of missing values."""
        total = self.count + self.missing_count
        return (self.missing_count / total * 100) if total > 0 else 0.0

    @property
    def cv(self) -> float:
        """Coefficient of variation (std/mean)."""
        if self.mean == 0:
            return float('inf')
        return abs(self.std / self.mean)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'column': self.column,
            'count': self.count,
            'missing_count': self.missing_count,
            'missing_pct': round(self.missing_pct, 2),
            'mean': round(self.mean, 4),
            'median': round(self.median, 4),
            'std': round(self.std, 4),
            'min': round(self.min, 4),
            'max': round(self.max, 4),
            'q25': round(self.q25, 4),
            'q75': round(self.q75, 4),
            'iqr': round(self.iqr, 4),
            'skewness': round(self.skewness, 4),
            'kurtosis': round(self.kurtosis, 4),
            'cv': round(self.cv, 4) if self.cv != float('inf') else 'inf',
        }


@dataclass
class DistributionAnalysis:
    """Distribution shape analysis for a numeric column."""
    column: str
    distribution_type: str  # 'normal', 'skewed_left', 'skewed_right', 'bimodal', 'uniform'
    confidence: float
    notable_features: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'column': self.column,
            'distribution_type': self.distribution_type,
            'confidence': self.confidence,
            'notable_features': self.notable_features,
        }


@dataclass
class AnalysisFinding:
    """A single analytical insight discovered during analysis."""
    category: str  # 'statistic', 'correlation', 'trend', 'segment', 'anomaly'
    title: str
    description: str
    affected_columns: List[str]
    importance: str  # 'high', 'medium', 'low'
    confidence: float  # 0.0 - 1.0
    actionable: bool
    recommendation: Optional[str] = None
    supporting_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'affected_columns': self.affected_columns,
            'importance': self.importance,
            'confidence': self.confidence,
            'actionable': self.actionable,
            'recommendation': self.recommendation,
            'supporting_data': self.supporting_data,
        }


@dataclass
class AnalysisResult:
    """Complete analysis output containing all findings and statistics."""
    findings: List[AnalysisFinding]
    descriptive_stats: Dict[str, DescriptiveStats]
    correlations: List['Correlation']
    trends: List['TrendAnalysis']
    segments: List['SegmentComparison']
    depth_level: str  # 'quick_scan', 'standard', 'deep_dive'
    columns_analyzed: int
    rows_analyzed: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'findings': [f.to_dict() for f in self.findings],
            'descriptive_stats': {k: v.to_dict() for k, v in self.descriptive_stats.items()},
            'correlations': [c.to_dict() for c in self.correlations],
            'trends': [t.to_dict() for t in self.trends],
            'segments': [s.to_dict() for s in self.segments],
            'depth_level': self.depth_level,
            'columns_analyzed': self.columns_analyzed,
            'rows_analyzed': self.rows_analyzed,
        }

    def get_findings_by_importance(self, importance: str) -> List[AnalysisFinding]:
        """Filter findings by importance level."""
        return [f for f in self.findings if f.importance == importance]

    def get_top_findings(self, n: int = 5) -> List[AnalysisFinding]:
        """Get top N findings sorted by importance and confidence."""
        importance_order = {'high': 0, 'medium': 1, 'low': 2}
        sorted_findings = sorted(
            self.findings,
            key=lambda f: (importance_order.get(f.importance, 3), -f.confidence)
        )
        return sorted_findings[:n]

    def summary(self) -> str:
        """Generate a human-readable summary of the analysis."""
        lines = [
            f"Analysis Summary ({self.depth_level})",
            f"{'='*40}",
            f"Data: {self.rows_analyzed:,} rows × {self.columns_analyzed} columns",
            f"",
            f"Findings: {len(self.findings)} total",
            f"  - High importance: {len(self.get_findings_by_importance('high'))}",
            f"  - Medium importance: {len(self.get_findings_by_importance('medium'))}",
            f"  - Low importance: {len(self.get_findings_by_importance('low'))}",
            f"",
            f"Statistics: {len(self.descriptive_stats)} numeric columns analyzed",
            f"Correlations: {len(self.correlations)} significant relationships",
            f"Trends: {len(self.trends)} time-based patterns",
            f"Segments: {len(self.segments)} category comparisons",
        ]
        return "\n".join(lines)


def calculate_descriptive_stats(df: pd.DataFrame, column: str) -> DescriptiveStats:
    """
    Calculate comprehensive descriptive statistics for a numeric column.

    Args:
        df: DataFrame containing the column
        column: Name of the numeric column to analyze

    Returns:
        DescriptiveStats with all calculated metrics
    """
    series = df[column]

    # Convert to numeric if needed
    if not pd.api.types.is_numeric_dtype(series):
        series = safe_numeric_conversion(series)

    non_null = series.dropna()

    if len(non_null) == 0:
        # Return zeros for empty columns
        return DescriptiveStats(
            column=column,
            count=0,
            missing_count=len(series),
            mean=0.0,
            median=0.0,
            std=0.0,
            min=0.0,
            max=0.0,
            q25=0.0,
            q75=0.0,
            skewness=0.0,
            kurtosis=0.0,
        )

    return DescriptiveStats(
        column=column,
        count=len(non_null),
        missing_count=series.isna().sum(),
        mean=float(non_null.mean()),
        median=float(non_null.median()),
        std=float(non_null.std()) if len(non_null) > 1 else 0.0,
        min=float(non_null.min()),
        max=float(non_null.max()),
        q25=float(non_null.quantile(0.25)),
        q75=float(non_null.quantile(0.75)),
        skewness=float(stats.skew(non_null)) if len(non_null) > 2 else 0.0,
        kurtosis=float(stats.kurtosis(non_null)) if len(non_null) > 3 else 0.0,
    )


def analyze_distribution(df: pd.DataFrame, column: str) -> DistributionAnalysis:
    """
    Analyze the distribution shape of a numeric column.

    Determines distribution type and identifies notable features
    like heavy tails, potential outliers, or multimodality.

    Args:
        df: DataFrame containing the column
        column: Name of the numeric column to analyze

    Returns:
        DistributionAnalysis with type classification and features
    """
    series = df[column]

    if not pd.api.types.is_numeric_dtype(series):
        series = safe_numeric_conversion(series)

    non_null = series.dropna()
    features = []

    if len(non_null) < 10:
        return DistributionAnalysis(
            column=column,
            distribution_type='unknown',
            confidence=0.0,
            notable_features=['Insufficient data for distribution analysis'],
        )

    # Calculate distribution metrics
    skewness = float(stats.skew(non_null))
    kurtosis_val = float(stats.kurtosis(non_null))

    # Determine distribution type based on skewness
    if abs(skewness) < 0.5:
        # Check for normality
        if len(non_null) >= 20:
            _, p_value = stats.normaltest(non_null)
            if p_value > 0.05:
                dist_type = 'normal'
                confidence = min(0.9, 0.5 + p_value)
            else:
                dist_type = 'symmetric'
                confidence = 0.6
        else:
            dist_type = 'symmetric'
            confidence = 0.5
    elif skewness > 0.5:
        dist_type = 'skewed_right'
        confidence = min(0.9, 0.5 + abs(skewness) / 2)
        features.append(f'Right-skewed (skewness: {skewness:.2f})')
    else:
        dist_type = 'skewed_left'
        confidence = min(0.9, 0.5 + abs(skewness) / 2)
        features.append(f'Left-skewed (skewness: {skewness:.2f})')

    # Check for heavy tails (high kurtosis)
    if kurtosis_val > 3:
        features.append(f'Heavy tails (excess kurtosis: {kurtosis_val:.2f})')

    # Check for potential outliers using IQR method
    q1 = non_null.quantile(0.25)
    q3 = non_null.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outlier_count = ((non_null < lower_bound) | (non_null > upper_bound)).sum()

    if outlier_count > 0:
        pct = outlier_count / len(non_null) * 100
        features.append(f'{outlier_count} potential outliers ({pct:.1f}%)')

    # Check for possible bimodality (simplified heuristic)
    # A more robust approach would use kernel density estimation
    hist, bin_edges = np.histogram(non_null, bins='auto')
    if len(hist) >= 5:
        # Look for two distinct peaks
        peaks = []
        for i in range(1, len(hist) - 1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1]:
                peaks.append(i)
        if len(peaks) >= 2:
            # Check if peaks are substantial (at least 20% of max)
            max_height = max(hist)
            substantial_peaks = [p for p in peaks if hist[p] >= max_height * 0.2]
            if len(substantial_peaks) >= 2:
                dist_type = 'bimodal'
                features.append('Possible bimodal distribution')
                confidence = 0.6  # Bimodality is hard to confirm

    return DistributionAnalysis(
        column=column,
        distribution_type=dist_type,
        confidence=round(confidence, 2),
        notable_features=features,
    )


def analyze_all_numeric(df: pd.DataFrame) -> Dict[str, DescriptiveStats]:
    """
    Calculate descriptive statistics for all numeric columns.

    Args:
        df: DataFrame to analyze

    Returns:
        Dictionary mapping column names to DescriptiveStats
    """
    numeric_cols = identify_numeric_columns(df)
    stats_dict = {}

    for col in numeric_cols:
        stats_dict[col] = calculate_descriptive_stats(df, col)

    return stats_dict


def find_statistical_anomalies(df: pd.DataFrame) -> List[AnalysisFinding]:
    """
    Find statistical anomalies and unusual patterns in the data.

    Looks for:
    - Columns with extremely high variance
    - Columns with unexpected value ranges
    - Highly skewed distributions
    - Columns dominated by a single value

    Args:
        df: DataFrame to analyze

    Returns:
        List of AnalysisFinding objects describing anomalies
    """
    findings = []
    numeric_cols = identify_numeric_columns(df)

    for col in numeric_cols:
        series = df[col]
        if not pd.api.types.is_numeric_dtype(series):
            series = safe_numeric_conversion(series)

        non_null = series.dropna()

        if len(non_null) < 10:
            continue

        stats_obj = calculate_descriptive_stats(df, col)
        dist = analyze_distribution(df, col)

        # Check for extreme skewness
        if abs(stats_obj.skewness) > 2:
            direction = 'right' if stats_obj.skewness > 0 else 'left'
            findings.append(AnalysisFinding(
                category='statistic',
                title=f'Highly skewed distribution in {col}',
                description=(
                    f"The column '{col}' shows extreme {direction} skewness "
                    f"(skewness={stats_obj.skewness:.2f}). This may indicate "
                    f"outliers or a need for log transformation."
                ),
                affected_columns=[col],
                importance=classify_importance(abs(stats_obj.skewness) / 4, 0.8),
                confidence=0.85,
                actionable=True,
                recommendation=(
                    f"Consider applying a log transformation to '{col}' "
                    f"or investigating extreme values."
                ),
                supporting_data={
                    'skewness': stats_obj.skewness,
                    'distribution_type': dist.distribution_type,
                },
            ))

        # Check for high coefficient of variation
        if stats_obj.cv > 2 and stats_obj.cv != float('inf'):
            findings.append(AnalysisFinding(
                category='statistic',
                title=f'High variance in {col}',
                description=(
                    f"The column '{col}' has a very high coefficient of variation "
                    f"(CV={stats_obj.cv:.2f}), indicating highly variable data."
                ),
                affected_columns=[col],
                importance='medium',
                confidence=0.75,
                actionable=True,
                recommendation=(
                    f"Review '{col}' for data quality issues or "
                    f"consider segmenting analysis by categories."
                ),
                supporting_data={
                    'cv': stats_obj.cv,
                    'std': stats_obj.std,
                    'mean': stats_obj.mean,
                },
            ))

        # Check for columns dominated by a single value
        value_counts = non_null.value_counts()
        if len(value_counts) > 0:
            top_freq = value_counts.iloc[0] / len(non_null)
            if top_freq > 0.9:
                dominant_value = value_counts.index[0]
                findings.append(AnalysisFinding(
                    category='statistic',
                    title=f'Low variability in {col}',
                    description=(
                        f"The column '{col}' is dominated by a single value "
                        f"({dominant_value}) appearing in {top_freq*100:.1f}% of rows."
                    ),
                    affected_columns=[col],
                    importance='low',
                    confidence=0.95,
                    actionable=False,
                    recommendation=(
                        f"This column may not provide useful variation for analysis."
                    ),
                    supporting_data={
                        'dominant_value': dominant_value,
                        'frequency': top_freq,
                    },
                ))

        # Check for potential data entry errors (values far from typical range)
        q1, q3 = stats_obj.q25, stats_obj.q75
        iqr = q3 - q1
        if iqr > 0:
            extreme_lower = q1 - 3 * iqr  # More extreme than standard outliers
            extreme_upper = q3 + 3 * iqr
            extreme_count = ((non_null < extreme_lower) | (non_null > extreme_upper)).sum()

            if extreme_count > 0:
                pct = extreme_count / len(non_null) * 100
                extreme_values = non_null[(non_null < extreme_lower) | (non_null > extreme_upper)]
                findings.append(AnalysisFinding(
                    category='anomaly',
                    title=f'Extreme outliers in {col}',
                    description=(
                        f"Found {extreme_count} extreme values ({pct:.1f}%) in '{col}' "
                        f"that are very far from the typical range. "
                        f"Range: {stats_obj.min:.2f} to {stats_obj.max:.2f}, "
                        f"IQR: {q1:.2f} to {q3:.2f}."
                    ),
                    affected_columns=[col],
                    importance='high' if pct < 1 else 'medium',
                    confidence=0.9,
                    actionable=True,
                    recommendation=(
                        f"Review extreme values in '{col}' for possible data entry errors: "
                        f"{list(extreme_values.head(5).values)}"
                    ),
                    supporting_data={
                        'extreme_count': int(extreme_count),
                        'extreme_pct': round(pct, 2),
                        'sample_extremes': list(extreme_values.head(5).values),
                    },
                ))

    return findings
