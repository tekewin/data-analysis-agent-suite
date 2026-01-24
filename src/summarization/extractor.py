"""Extraction utilities for executive summary generation.

This module provides functions to extract key metrics, top findings,
recommended actions, and risks from analysis results and reports.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from src.analysis import AnalysisResult, AnalysisFinding
from .loader import SummaryInput


# =============================================================================
# EXTRACTED DATA DATACLASSES
# =============================================================================

@dataclass
class ExtractedMetric:
    """A key metric extracted from analysis."""

    name: str
    value: str
    change: Optional[str] = None  # e.g., "+15% vs previous"
    status: str = "neutral"  # 'good', 'warning', 'critical', 'neutral'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'value': self.value,
            'change': self.change,
            'status': self.status,
        }


@dataclass
class ExtractedFinding:
    """A prioritized finding for the summary."""

    title: str
    impact: str  # Business impact statement
    action: str  # Recommended action
    importance: str  # 'high', 'medium', 'low'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'title': self.title,
            'impact': self.impact,
            'action': self.action,
            'importance': self.importance,
        }


@dataclass
class ExtractedData:
    """All data extracted for the executive summary."""

    bluf: str  # Bottom Line Up Front (2-3 sentences)
    metrics: List[ExtractedMetric]
    top_findings: List[ExtractedFinding]
    recommended_actions: List[str]
    risks: List[str]
    source_report: str
    analysis_period: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'bluf': self.bluf,
            'metrics': [m.to_dict() for m in self.metrics],
            'top_findings': [f.to_dict() for f in self.top_findings],
            'recommended_actions': self.recommended_actions,
            'risks': self.risks,
            'source_report': self.source_report,
            'analysis_period': self.analysis_period,
        }


# =============================================================================
# BLUF EXTRACTION
# =============================================================================

def extract_bluf(input_data: SummaryInput) -> str:
    """
    Extract or generate the Bottom Line Up Front statement.

    The BLUF is 2-3 sentences capturing the single most critical insight
    and its business implication.

    Args:
        input_data: SummaryInput with analysis and/or report

    Returns:
        BLUF statement string
    """
    if input_data.has_analysis and input_data.analysis_result:
        return _generate_bluf_from_analysis(input_data.analysis_result)

    if input_data.has_report and input_data.report_content:
        return _extract_bluf_from_report(input_data.report_content)

    return "Analysis complete. Review findings below for key insights."


def _generate_bluf_from_analysis(analysis: AnalysisResult) -> str:
    """Generate BLUF from analysis results."""
    high_importance = [f for f in analysis.findings if f.importance == 'high']

    if not high_importance:
        # Fall back to any findings
        if analysis.findings:
            top_finding = analysis.findings[0]
            return f"{top_finding.title}. {top_finding.description}"
        return "Analysis complete. No critical findings identified."

    # Use the top high-importance finding
    top = high_importance[0]

    # Build BLUF from top finding and any trend/correlation info
    bluf_parts = [top.description]

    # Add trend info if available
    if analysis.trends:
        trend = analysis.trends[0]
        direction = trend.trend_direction
        if trend.growth_rate_pct:
            bluf_parts.append(
                f"{trend.column.replace('_', ' ').title()} shows a {direction} trend "
                f"({trend.growth_rate_pct:+.1f}%)."
            )

    # Add recommendation if present
    if top.recommendation:
        bluf_parts.append(top.recommendation)

    return " ".join(bluf_parts[:3])  # Limit to ~3 sentences


def _extract_bluf_from_report(report_content: str) -> str:
    """Extract BLUF from report executive summary section."""
    lines = report_content.split('\n')

    # Look for executive summary section
    in_exec_summary = False
    exec_summary_lines = []

    for line in lines:
        if '## Executive Summary' in line or '## Bottom Line' in line:
            in_exec_summary = True
            continue

        if in_exec_summary:
            if line.startswith('## ') or line.startswith('# '):
                break
            if line.strip() and not line.startswith('---'):
                exec_summary_lines.append(line.strip())

    if exec_summary_lines:
        # Return first 2-3 sentences
        text = ' '.join(exec_summary_lines)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return ' '.join(sentences[:3])

    return "Review the full report for detailed findings and recommendations."


# =============================================================================
# METRICS EXTRACTION
# =============================================================================

def extract_metrics(input_data: SummaryInput, max_metrics: int = 5) -> List[ExtractedMetric]:
    """
    Extract key metrics from analysis results.

    Args:
        input_data: SummaryInput with analysis data
        max_metrics: Maximum number of metrics to extract

    Returns:
        List of ExtractedMetric objects
    """
    metrics = []

    if not input_data.has_analysis or not input_data.analysis_result:
        return metrics

    analysis = input_data.analysis_result

    # Extract from descriptive stats
    for col_name, stats in list(analysis.descriptive_stats.items())[:max_metrics]:
        # Determine status based on data quality
        missing_pct = stats.missing_pct if hasattr(stats, 'missing_pct') else 0
        if missing_pct > 10:
            status = 'warning'
        elif missing_pct > 0:
            status = 'neutral'
        else:
            status = 'good'

        metrics.append(ExtractedMetric(
            name=f"{col_name.replace('_', ' ').title()} (avg)",
            value=_format_metric_value(stats.mean),
            change=None,
            status=status,
        ))

    # Add metrics from trends
    for trend in analysis.trends:
        if trend.growth_rate_pct is not None:
            status = 'good' if trend.growth_rate_pct > 0 else 'warning'
            if abs(trend.growth_rate_pct) > 20:
                status = 'critical' if trend.growth_rate_pct < 0 else 'good'

            metrics.append(ExtractedMetric(
                name=f"{trend.column.replace('_', ' ').title()} Trend",
                value=trend.trend_direction.title(),
                change=f"{trend.growth_rate_pct:+.1f}%",
                status=status,
            ))

    return metrics[:max_metrics]


def _format_metric_value(value: float) -> str:
    """Format a numeric value for display."""
    if value is None:
        return "N/A"

    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif abs_val >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif abs_val >= 1_000:
        return f"{value:,.0f}"
    elif abs_val >= 1:
        return f"{value:.2f}"
    else:
        return f"{value:.4f}"


def calculate_metric_status(metric: ExtractedMetric) -> str:
    """
    Calculate the status indicator for a metric.

    Args:
        metric: ExtractedMetric to evaluate

    Returns:
        Status string: 'good', 'warning', 'critical', or 'neutral'
    """
    if metric.change is None:
        return 'neutral'

    # Try to parse change value
    try:
        change_str = metric.change.replace('%', '').replace('+', '')
        change_val = float(change_str)

        if change_val > 10:
            return 'good'
        elif change_val < -10:
            return 'critical'
        elif change_val < 0:
            return 'warning'
        else:
            return 'neutral'
    except (ValueError, AttributeError):
        return 'neutral'


# =============================================================================
# FINDINGS EXTRACTION
# =============================================================================

def extract_top_findings(
    input_data: SummaryInput,
    count: int = 3,
) -> List[ExtractedFinding]:
    """
    Extract and prioritize top findings for the summary.

    Args:
        input_data: SummaryInput with analysis data
        count: Number of findings to extract (default 3)

    Returns:
        List of ExtractedFinding objects, prioritized by importance
    """
    if not input_data.has_analysis or not input_data.analysis_result:
        return []

    findings = input_data.analysis_result.findings
    return prioritize_findings(findings, count)


def prioritize_findings(
    findings: List[AnalysisFinding],
    count: int = 3,
) -> List[ExtractedFinding]:
    """
    Prioritize and convert findings to executive summary format.

    Args:
        findings: List of AnalysisFinding objects
        count: Number to return

    Returns:
        List of ExtractedFinding objects
    """
    # Sort by importance and confidence
    importance_order = {'high': 0, 'medium': 1, 'low': 2}

    sorted_findings = sorted(
        findings,
        key=lambda f: (importance_order.get(f.importance, 3), -f.confidence)
    )

    result = []
    for finding in sorted_findings[:count]:
        result.append(_convert_to_extracted_finding(finding))

    return result


def _convert_to_extracted_finding(finding: AnalysisFinding) -> ExtractedFinding:
    """Convert an AnalysisFinding to ExtractedFinding format."""
    # Create impact statement from description
    impact = finding.description
    if len(impact) > 150:
        impact = impact[:147] + "..."

    # Use recommendation or generate action
    if finding.recommendation:
        action = finding.recommendation
    elif finding.actionable:
        action = f"Investigate {', '.join(finding.affected_columns[:2])} for optimization opportunities."
    else:
        action = "Monitor this metric for future changes."

    return ExtractedFinding(
        title=finding.title,
        impact=impact,
        action=action,
        importance=finding.importance,
    )


# =============================================================================
# ACTIONS EXTRACTION
# =============================================================================

def extract_actions(input_data: SummaryInput, count: int = 3) -> List[str]:
    """
    Extract recommended actions from findings.

    Args:
        input_data: SummaryInput with analysis data
        count: Maximum number of actions to extract

    Returns:
        List of action strings
    """
    actions = []

    if not input_data.has_analysis or not input_data.analysis_result:
        return actions

    # Get actionable findings
    findings = input_data.analysis_result.findings
    actionable = [f for f in findings if f.actionable and f.recommendation]

    # Sort by importance
    importance_order = {'high': 0, 'medium': 1, 'low': 2}
    actionable.sort(key=lambda f: importance_order.get(f.importance, 3))

    for finding in actionable[:count]:
        if finding.recommendation:
            actions.append(finding.recommendation)

    # If we need more actions, generate from non-recommendation findings
    if len(actions) < count:
        for finding in findings:
            if finding not in actionable and len(actions) < count:
                action = _generate_action_from_finding(finding)
                if action:
                    actions.append(action)

    return actions[:count]


def _generate_action_from_finding(finding: AnalysisFinding) -> Optional[str]:
    """Generate an action statement from a finding."""
    if finding.category == 'correlation':
        cols = finding.affected_columns[:2]
        if len(cols) >= 2:
            return f"Analyze the relationship between {cols[0]} and {cols[1]} for business opportunities."

    elif finding.category == 'trend':
        col = finding.affected_columns[0] if finding.affected_columns else 'the metric'
        return f"Monitor {col} trends and adjust strategy accordingly."

    elif finding.category == 'segment':
        return "Review segment performance and consider targeted strategies."

    elif finding.category == 'anomaly':
        return "Investigate anomalies to identify root causes."

    return None


# =============================================================================
# RISKS EXTRACTION
# =============================================================================

def extract_risks(input_data: SummaryInput, count: int = 3) -> List[str]:
    """
    Extract risks and considerations from the analysis.

    Args:
        input_data: SummaryInput with analysis data
        count: Maximum number of risks to extract

    Returns:
        List of risk/consideration strings
    """
    risks = []

    if input_data.has_analysis and input_data.analysis_result:
        analysis = input_data.analysis_result

        # Check for data quality issues
        for col_name, stats in analysis.descriptive_stats.items():
            if hasattr(stats, 'missing_pct') and stats.missing_pct > 5:
                risks.append(
                    f"Data quality: {col_name} has {stats.missing_pct:.1f}% missing values"
                )
            elif stats.missing_count > 0:
                missing_pct = (stats.missing_count / stats.count) * 100 if stats.count > 0 else 0
                if missing_pct > 5:
                    risks.append(
                        f"Data quality: {col_name} has {missing_pct:.1f}% missing values"
                    )

        # Check for low confidence findings
        low_conf = [f for f in analysis.findings if f.confidence < 0.6]
        if low_conf:
            risks.append(
                f"Some findings have lower confidence ({len(low_conf)} findings < 60% confidence)"
            )

        # Check sample size
        if analysis.rows_analyzed < 100:
            risks.append(
                f"Limited sample size ({analysis.rows_analyzed} rows) may affect reliability"
            )

    # Add general caveats if we don't have enough specific risks
    if len(risks) < 1:
        risks.append("Findings should be validated with domain expertise before action")

    return risks[:count]


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================

@dataclass
class SummaryConfig:
    """Configuration for executive summary generation."""

    title: str = "Executive Summary"
    max_findings: int = 3
    max_actions: int = 3
    max_risks: int = 3
    max_metrics: int = 5
    include_metrics_table: bool = True
    include_chart_references: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'title': self.title,
            'max_findings': self.max_findings,
            'max_actions': self.max_actions,
            'max_risks': self.max_risks,
            'max_metrics': self.max_metrics,
            'include_metrics_table': self.include_metrics_table,
            'include_chart_references': self.include_chart_references,
        }


def extract_all(
    input_data: SummaryInput,
    config: Optional[SummaryConfig] = None,
) -> ExtractedData:
    """
    Extract all data needed for an executive summary.

    This is the main entry point for extraction.

    Args:
        input_data: SummaryInput with all available data
        config: Optional SummaryConfig for customization

    Returns:
        ExtractedData containing all extracted information
    """
    if config is None:
        config = SummaryConfig()

    return ExtractedData(
        bluf=extract_bluf(input_data),
        metrics=extract_metrics(input_data, config.max_metrics),
        top_findings=extract_top_findings(input_data, config.max_findings),
        recommended_actions=extract_actions(input_data, config.max_actions),
        risks=extract_risks(input_data, config.max_risks),
        source_report=input_data.source_file,
        analysis_period=_extract_analysis_period(input_data),
    )


def _extract_analysis_period(input_data: SummaryInput) -> Optional[str]:
    """Extract the analysis period if available."""
    if input_data.has_analysis and input_data.analysis_result:
        # Check for trends with date info
        for trend in input_data.analysis_result.trends:
            if trend.date_column:
                return f"Based on {trend.date_column}"

    return None
