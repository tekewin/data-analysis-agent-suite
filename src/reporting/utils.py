"""Shared utilities for report generation.

This module provides formatting helpers for numbers, dates, findings,
tables, and other report elements.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from pathlib import Path
from datetime import datetime

if TYPE_CHECKING:
    from src.analysis import (
        AnalysisFinding,
        DescriptiveStats,
        Correlation,
        TrendAnalysis,
        SegmentComparison,
    )


# =============================================================================
# IMPORTANCE AND CONFIDENCE FORMATTING
# =============================================================================

def format_importance_indicator(importance: str) -> str:
    """
    Return an emoji indicator for importance level.

    Args:
        importance: 'high', 'medium', or 'low'

    Returns:
        Colored circle emoji (🔴, 🟡, or 🟢)
    """
    indicators = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢',
    }
    return indicators.get(importance.lower(), '⚪')


def format_confidence_level(confidence: float) -> str:
    """
    Format a confidence score as a descriptive level.

    Args:
        confidence: Float from 0.0 to 1.0

    Returns:
        Descriptive string like "High (92%)"
    """
    if confidence >= 0.9:
        level = "Very High"
    elif confidence >= 0.75:
        level = "High"
    elif confidence >= 0.5:
        level = "Moderate"
    elif confidence >= 0.25:
        level = "Low"
    else:
        level = "Very Low"

    return f"{level} ({confidence:.0%})"


# =============================================================================
# NUMBER AND DATE FORMATTING
# =============================================================================

def format_number(value: float, precision: int = 2) -> str:
    """
    Format a number with appropriate precision and thousands separators.

    Args:
        value: Numeric value to format
        precision: Decimal places (default 2)

    Returns:
        Formatted string like "1,234.56" or "1.2M"
    """
    if value is None:
        return "N/A"

    # Handle special float values
    if isinstance(value, float):
        if value != value:  # NaN check
            return "N/A"
        if value == float('inf') or value == float('-inf'):
            return "∞" if value > 0 else "-∞"

    # Use abbreviations for large numbers
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.{precision}f}B"
    elif abs_value >= 1_000_000:
        return f"{value / 1_000_000:,.{precision}f}M"
    elif abs_value >= 1_000:
        return f"{value:,.{precision}f}"
    elif abs_value >= 1 or abs_value == 0:
        return f"{value:.{precision}f}"
    else:
        # Small decimal - show more precision
        return f"{value:.{precision + 2}f}"


def format_percentage(value: float, precision: int = 1) -> str:
    """
    Format a value as a percentage.

    Args:
        value: Value (0-1 or 0-100 range)
        precision: Decimal places (default 1)

    Returns:
        Formatted string like "45.2%"
    """
    if value is None:
        return "N/A"

    # Assume values > 1 are already percentages
    if abs(value) <= 1:
        value = value * 100

    return f"{value:.{precision}f}%"


def format_date(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format a datetime object as a string.

    Args:
        dt: Datetime object (defaults to now)
        fmt: Format string (default "YYYY-MM-DD HH:MM")

    Returns:
        Formatted date string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


# =============================================================================
# FINDING FORMATTING
# =============================================================================

def format_finding_block(
    finding: 'AnalysisFinding',
    include_recommendation: bool = True,
    include_confidence: bool = True,
    include_stats: bool = False,
) -> str:
    """
    Format a single finding as a markdown block.

    Args:
        finding: AnalysisFinding object to format
        include_recommendation: Include the recommendation if present
        include_confidence: Include confidence level
        include_stats: Include supporting data statistics

    Returns:
        Markdown formatted finding block
    """
    indicator = format_importance_indicator(finding.importance)
    lines = [
        f"{indicator} **{finding.title}**",
        "",
        finding.description,
        "",
    ]

    if include_confidence:
        lines.append(f"*Confidence: {format_confidence_level(finding.confidence)}*")
        lines.append("")

    if include_recommendation and finding.recommendation:
        lines.append(f"💡 **Recommendation:** {finding.recommendation}")
        lines.append("")

    if include_stats and finding.supporting_data:
        lines.append("**Supporting Data:**")
        for key, value in finding.supporting_data.items():
            if isinstance(value, float):
                value = format_number(value)
            lines.append(f"- {key}: {value}")
        lines.append("")

    return "\n".join(lines)


def format_finding_brief(finding: 'AnalysisFinding') -> str:
    """
    Format a finding as a single-line summary.

    Args:
        finding: AnalysisFinding object to format

    Returns:
        Single line summary with indicator
    """
    indicator = format_importance_indicator(finding.importance)
    # Truncate description if too long
    desc = finding.description
    if len(desc) > 100:
        desc = desc[:97] + "..."
    return f"{indicator} **{finding.title}** - {desc}"


# =============================================================================
# TABLE FORMATTING
# =============================================================================

def format_stats_table(stats_dict: Dict[str, 'DescriptiveStats']) -> str:
    """
    Format descriptive statistics as a markdown table.

    Args:
        stats_dict: Dictionary mapping column names to DescriptiveStats

    Returns:
        Markdown table string
    """
    if not stats_dict:
        return "*No numeric columns analyzed.*"

    lines = [
        "| Column | Count | Mean | Median | Std Dev | Min | Max |",
        "|--------|-------|------|--------|---------|-----|-----|",
    ]

    for col_name, stats in stats_dict.items():
        lines.append(
            f"| {col_name} | {stats.count:,} | "
            f"{format_number(stats.mean)} | {format_number(stats.median)} | "
            f"{format_number(stats.std)} | {format_number(stats.min)} | "
            f"{format_number(stats.max)} |"
        )

    return "\n".join(lines)


def format_correlation_table(correlations: List['Correlation'], max_rows: int = 10) -> str:
    """
    Format correlations as a markdown table.

    Args:
        correlations: List of Correlation objects
        max_rows: Maximum number of rows to include

    Returns:
        Markdown table string
    """
    if not correlations:
        return "*No significant correlations found.*"

    lines = [
        "| Variable 1 | Variable 2 | Correlation | Strength | Direction |",
        "|------------|------------|-------------|----------|-----------|",
    ]

    for corr in correlations[:max_rows]:
        direction_arrow = "↑" if corr.direction == "positive" else "↓"
        lines.append(
            f"| {corr.column1} | {corr.column2} | "
            f"{corr.coefficient:+.3f} | {corr.strength.replace('_', ' ').title()} | "
            f"{direction_arrow} {corr.direction.title()} |"
        )

    if len(correlations) > max_rows:
        lines.append(f"| ... | *{len(correlations) - max_rows} more* | | | |")

    return "\n".join(lines)


def format_trend_summary(trends: List['TrendAnalysis']) -> str:
    """
    Format trend analyses as a markdown list.

    Args:
        trends: List of TrendAnalysis objects

    Returns:
        Markdown formatted summary
    """
    if not trends:
        return "*No time-based trends detected.*"

    lines = ["**Detected Trends:**", ""]

    for trend in trends:
        direction_emoji = {
            'increasing': '📈',
            'decreasing': '📉',
            'stable': '➡️',
            'volatile': '📊',
        }.get(trend.trend_direction, '❓')

        growth_str = ""
        if trend.growth_rate_pct is not None:
            growth_str = f" ({trend.growth_rate_pct:+.1f}%)"

        seasonality_str = ""
        if trend.seasonality_detected:
            seasonality_str = f" | {trend.seasonal_period} seasonality"

        lines.append(
            f"- {direction_emoji} **{trend.column}**: "
            f"{trend.trend_direction.title()}{growth_str} "
            f"(R²={trend.r_squared:.2f}){seasonality_str}"
        )

    return "\n".join(lines)


def format_segment_summary(segments: List['SegmentComparison'], max_segments: int = 5) -> str:
    """
    Format segment comparisons as markdown.

    Args:
        segments: List of SegmentComparison objects
        max_segments: Maximum comparisons to include

    Returns:
        Markdown formatted summary
    """
    if not segments:
        return "*No significant segment differences found.*"

    lines = []

    for seg in segments[:max_segments]:
        if not seg.notable_differences:
            continue

        lines.append(f"**{seg.metric_column} by {seg.segment_column}:**")
        lines.append(f"- Variance explained: {format_percentage(seg.variance_ratio)}")

        for diff in seg.notable_differences[:3]:
            lines.append(f"- {diff}")

        lines.append("")

    return "\n".join(lines) if lines else "*No notable segment differences.*"


# =============================================================================
# FILE UTILITIES
# =============================================================================

def ensure_output_dir(output_dir: Optional[str] = None) -> Path:
    """
    Ensure the output directory exists.

    Args:
        output_dir: Optional directory path (defaults to ./output)

    Returns:
        Path object for the output directory
    """
    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = Path("./output")

    out_path.mkdir(parents=True, exist_ok=True)
    return out_path


def generate_report_filename(source_file: str, style: str = "report") -> str:
    """
    Generate a timestamped filename for a report.

    Args:
        source_file: Original source file name
        style: Report style name (for filename)

    Returns:
        Filename like "sales_report_20240124_143022.md"
    """
    source_name = Path(source_file).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{source_name}_report_{timestamp}.md"
