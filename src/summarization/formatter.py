"""Formatting utilities for executive summary generation.

This module provides formatting helpers for status indicators, metrics tables,
finding blocks, action lists, and risk lists used in executive summaries.
"""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .extractor import ExtractedMetric, ExtractedFinding


# =============================================================================
# STATUS INDICATOR FORMATTING
# =============================================================================

def format_status_indicator(status: str) -> str:
    """
    Return an emoji indicator for status level.

    Args:
        status: 'good', 'warning', 'critical', or 'neutral'

    Returns:
        Colored circle emoji (🟢, 🟡, 🔴, or ⚪)

    Examples:
        >>> format_status_indicator('good')
        '🟢'
        >>> format_status_indicator('critical')
        '🔴'
    """
    indicators = {
        'good': '🟢',
        'warning': '🟡',
        'critical': '🔴',
        'neutral': '⚪',
    }
    return indicators.get(status.lower(), '⚪')


def format_importance_indicator(importance: str) -> str:
    """
    Return an emoji indicator for importance level.

    Args:
        importance: 'high', 'medium', or 'low'

    Returns:
        Colored circle emoji (🔴, 🟡, or 🟢)

    Examples:
        >>> format_importance_indicator('high')
        '🔴'
        >>> format_importance_indicator('low')
        '🟢'
    """
    indicators = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢',
    }
    return indicators.get(importance.lower(), '⚪')


# =============================================================================
# METRICS TABLE FORMATTING
# =============================================================================

def format_metrics_table(metrics: List['ExtractedMetric']) -> str:
    """
    Format a list of metrics as a markdown table.

    Args:
        metrics: List of ExtractedMetric objects

    Returns:
        Markdown table string with columns: Metric, Value, Change, Status

    Examples:
        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class Metric:
        ...     name: str
        ...     value: str
        ...     change: str = None
        ...     status: str = 'neutral'
        >>> metrics = [Metric('Revenue', '$5.2M', '+15%', 'good')]
        >>> print(format_metrics_table(metrics))
        | Metric | Value | Change | Status |
        |--------|-------|--------|--------|
        | Revenue | $5.2M | +15% | 🟢 |
    """
    if not metrics:
        return "*No key metrics available.*"

    lines = [
        "| Metric | Value | Change | Status |",
        "|--------|-------|--------|--------|",
    ]

    for metric in metrics:
        change_str = metric.change if metric.change else "-"
        status_emoji = format_status_indicator(metric.status)
        lines.append(
            f"| {metric.name} | {metric.value} | {change_str} | {status_emoji} |"
        )

    return "\n".join(lines)


# =============================================================================
# FINDING BLOCK FORMATTING
# =============================================================================

def format_finding_block(finding: 'ExtractedFinding', number: int) -> str:
    """
    Format a single finding as a markdown block for executive summary.

    Args:
        finding: ExtractedFinding object
        number: Finding number (1, 2, 3, etc.)

    Returns:
        Markdown formatted finding block with impact and action

    Examples:
        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class Finding:
        ...     title: str
        ...     impact: str
        ...     action: str
        ...     importance: str
        >>> f = Finding('Sales Up', 'Revenue increased 15%', 'Scale team', 'high')
        >>> block = format_finding_block(f, 1)
        >>> '### 1.' in block
        True
    """
    indicator = format_importance_indicator(finding.importance)

    lines = [
        f"### {number}. {finding.title} {indicator}",
        f"**Impact**: {finding.impact}",
        f"**Action**: {finding.action}",
        "",
    ]

    return "\n".join(lines)


def format_finding_list(findings: List['ExtractedFinding']) -> str:
    """
    Format a list of findings as markdown blocks.

    Args:
        findings: List of ExtractedFinding objects

    Returns:
        Markdown formatted findings with numbered headers
    """
    if not findings:
        return "*No key findings to highlight.*"

    blocks = []
    for i, finding in enumerate(findings, 1):
        blocks.append(format_finding_block(finding, i))

    return "\n".join(blocks)


# =============================================================================
# ACTION AND RISK FORMATTING
# =============================================================================

def format_action_list(actions: List[str]) -> str:
    """
    Format recommended actions as a numbered markdown list.

    Args:
        actions: List of action strings

    Returns:
        Markdown numbered list with categorized actions

    Examples:
        >>> actions = ['Take action A', 'Consider B', 'Plan for C']
        >>> result = format_action_list(actions)
        >>> '1. **Immediate**:' in result
        True
    """
    if not actions:
        return "*No specific actions recommended.*"

    # Categorize actions by priority
    categories = ['Immediate', 'Short-term', 'Strategic']
    lines = []

    for i, action in enumerate(actions):
        # Assign category based on position
        category = categories[min(i, len(categories) - 1)]
        lines.append(f"{i + 1}. **{category}**: {action}")

    return "\n".join(lines)


def format_risk_list(risks: List[str]) -> str:
    """
    Format risks and considerations as a bulleted markdown list.

    Args:
        risks: List of risk/consideration strings

    Returns:
        Markdown bulleted list

    Examples:
        >>> risks = ['Data quality issues', 'Limited sample size']
        >>> result = format_risk_list(risks)
        >>> '- Data quality issues' in result
        True
    """
    if not risks:
        return "*No significant risks or caveats noted.*"

    lines = [f"- {risk}" for risk in risks]
    return "\n".join(lines)


# =============================================================================
# BLUF SECTION FORMATTING
# =============================================================================

def format_bluf_section(bluf: str) -> str:
    """
    Format the Bottom Line Up Front section.

    Args:
        bluf: 2-3 sentence BLUF statement

    Returns:
        Markdown formatted BLUF section with proper styling

    Examples:
        >>> bluf = "Sales increased 15%. Consider expanding team."
        >>> result = format_bluf_section(bluf)
        >>> bluf in result
        True
    """
    if not bluf:
        return "*Executive summary not available.*"

    return bluf


# =============================================================================
# HEADER AND METADATA FORMATTING
# =============================================================================

def format_summary_header(
    title: str,
    date: str,
    analysis_period: str = None,
    source: str = "",
) -> str:
    """
    Format the executive summary header section.

    Args:
        title: Summary title
        date: Generation date
        analysis_period: Optional period covered
        source: Source data file

    Returns:
        Markdown formatted header
    """
    lines = [
        f"# Executive Summary: {title}",
        "",
        f"**Date**: {date}",
    ]

    if analysis_period:
        lines.append(f"**Analysis Period**: {analysis_period}")

    lines.append(f"**Source**: `{source}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def format_summary_footer(report_reference: str) -> str:
    """
    Format the executive summary footer.

    Args:
        report_reference: Filename of the full report

    Returns:
        Markdown formatted footer
    """
    lines = [
        "",
        "---",
        "",
        f"*Full analysis: {report_reference}*",
        "*Generated by @exec-summarizer*",
        "",
    ]

    return "\n".join(lines)


# =============================================================================
# CHANGE FORMATTING
# =============================================================================

def format_change(value: float, suffix: str = "%") -> str:
    """
    Format a numeric change value with sign and suffix.

    Args:
        value: The change value
        suffix: Suffix to append (default '%')

    Returns:
        Formatted string like '+15%' or '-3.2%'

    Examples:
        >>> format_change(15.5)
        '+15.5%'
        >>> format_change(-3.2)
        '-3.2%'
        >>> format_change(0)
        '0%'
    """
    if value is None:
        return "-"

    if value > 0:
        return f"+{value:.1f}{suffix}"
    elif value < 0:
        return f"{value:.1f}{suffix}"
    else:
        return f"0{suffix}"


def format_number_compact(value: float) -> str:
    """
    Format a number in compact notation.

    Args:
        value: Numeric value

    Returns:
        Compact string like '1.2M' or '5.5K'

    Examples:
        >>> format_number_compact(1500000)
        '1.5M'
        >>> format_number_compact(5500)
        '5.5K'
        >>> format_number_compact(500)
        '500'
    """
    if value is None:
        return "N/A"

    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif abs_value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif abs_value >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return f"{value:.0f}"


def format_currency(value: float, currency: str = "$") -> str:
    """
    Format a value as currency.

    Args:
        value: Numeric value
        currency: Currency symbol (default '$')

    Returns:
        Formatted currency string

    Examples:
        >>> format_currency(1500000)
        '$1.5M'
        >>> format_currency(5500)
        '$5.5K'
    """
    compact = format_number_compact(value)
    if compact == "N/A":
        return compact
    return f"{currency}{compact}"
