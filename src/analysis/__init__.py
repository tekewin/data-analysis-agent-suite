"""Data analysis utilities for the @data-analyzer agent.

This module provides statistical analysis, correlation discovery,
trend detection, and segmentation analysis for clean datasets.
"""

from .utils import (
    classify_column_type,
    identify_numeric_columns,
    identify_categorical_columns,
    identify_date_columns,
    calculate_confidence_score,
)
from .statistics import (
    DescriptiveStats,
    DistributionAnalysis,
    AnalysisFinding,
    AnalysisResult,
    calculate_descriptive_stats,
    analyze_distribution,
    analyze_all_numeric,
    find_statistical_anomalies,
)
from .correlations import (
    Correlation,
    calculate_correlation,
    find_all_correlations,
    generate_correlation_matrix,
    find_correlation_insights,
)
from .trends import (
    TrendAnalysis,
    detect_date_column,
    analyze_trend,
    detect_seasonality,
    find_trend_insights,
)
from .segmentation import (
    SegmentComparison,
    compare_segments,
    find_segment_insights,
    calculate_group_statistics,
)
from .reporter import (
    generate_analysis_report,
    save_analysis_results,
)

__all__ = [
    # Utils
    "classify_column_type",
    "identify_numeric_columns",
    "identify_categorical_columns",
    "identify_date_columns",
    "calculate_confidence_score",
    # Statistics
    "DescriptiveStats",
    "DistributionAnalysis",
    "AnalysisFinding",
    "AnalysisResult",
    "calculate_descriptive_stats",
    "analyze_distribution",
    "analyze_all_numeric",
    "find_statistical_anomalies",
    # Correlations
    "Correlation",
    "calculate_correlation",
    "find_all_correlations",
    "generate_correlation_matrix",
    "find_correlation_insights",
    # Trends
    "TrendAnalysis",
    "detect_date_column",
    "analyze_trend",
    "detect_seasonality",
    "find_trend_insights",
    # Segmentation
    "SegmentComparison",
    "compare_segments",
    "find_segment_insights",
    "calculate_group_statistics",
    # Reporter
    "generate_analysis_report",
    "save_analysis_results",
]
