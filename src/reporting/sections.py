"""Section generators for report generation.

This module provides functions to generate each section of the report,
adapting content based on the writing style configuration.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .loader import ReportInput
from .styles import ReportConfig, WritingStyle, get_style_intro, get_style_methodology_text
from .utils import (
    format_importance_indicator,
    format_confidence_level,
    format_finding_block,
    format_finding_brief,
    format_stats_table,
    format_correlation_table,
    format_trend_summary,
    format_segment_summary,
    format_number,
    format_percentage,
)


# =============================================================================
# SECTION DATACLASS
# =============================================================================

@dataclass
class GeneratedSection:
    """A single section of the report."""

    title: str  # Section title
    content: str  # Section content (markdown)
    level: int  # Header level (1, 2, 3)
    section_id: str = ""  # Optional section identifier

    def to_markdown(self) -> str:
        """Convert section to markdown with appropriate header."""
        header_prefix = "#" * self.level
        return f"{header_prefix} {self.title}\n\n{self.content}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'title': self.title,
            'content': self.content,
            'level': self.level,
            'section_id': self.section_id,
        }


# =============================================================================
# EXECUTIVE SUMMARY
# =============================================================================

def generate_executive_summary(
    report_input: ReportInput,
    config: ReportConfig,
) -> GeneratedSection:
    """
    Generate the executive summary section.

    The executive summary provides a high-level overview of the most
    critical findings, adapted to the writing style.

    Args:
        report_input: ReportInput with all data
        config: ReportConfig with style settings

    Returns:
        GeneratedSection with executive summary content
    """
    style = config.style
    findings = report_input.analysis_result.findings
    result = report_input.analysis_result

    # Get top findings based on style
    num_highlights = 3 if style.detail_level == 'low' else 5
    top_findings = result.get_top_findings(num_highlights)
    high_findings = result.get_findings_by_importance('high')

    lines = []

    # Opening paragraph
    intro = get_style_intro(style)
    lines.append(intro)
    lines.append("")

    # Data overview paragraph
    lines.append(
        f"The analysis examined **{result.rows_analyzed:,} records** across "
        f"**{result.columns_analyzed} data fields**, uncovering "
        f"**{len(findings)} key findings**."
    )

    # Highlight critical findings if any
    if high_findings:
        lines.append("")
        if style.detail_level == 'low':
            lines.append(f"**{len(high_findings)} critical findings require attention:**")
        else:
            lines.append(f"**Critical Findings ({len(high_findings)}):**")

        for finding in high_findings[:3]:
            indicator = format_importance_indicator(finding.importance)
            lines.append(f"- {indicator} {finding.title}")

    # Key metrics summary
    if result.correlations and style.detail_level != 'low':
        strong_corrs = [c for c in result.correlations if c.strength in ('strong', 'very_strong')]
        if strong_corrs:
            lines.append("")
            lines.append(
                f"**{len(strong_corrs)} strong correlations** were identified "
                "between variables."
            )

    if result.trends:
        increasing = [t for t in result.trends if t.trend_direction == 'increasing']
        decreasing = [t for t in result.trends if t.trend_direction == 'decreasing']
        if increasing or decreasing:
            lines.append("")
            trend_summary = []
            if increasing:
                trend_summary.append(f"{len(increasing)} upward trends")
            if decreasing:
                trend_summary.append(f"{len(decreasing)} downward trends")
            lines.append(f"Time-based analysis revealed {' and '.join(trend_summary)}.")

    # Visualization summary
    if report_input.has_visualizations:
        lines.append("")
        lines.append(
            f"**{report_input.chart_count} visualizations** have been generated "
            "to illustrate these findings."
        )

    return GeneratedSection(
        title="Executive Summary",
        content="\n".join(lines),
        level=2,
        section_id="executive-summary",
    )


# =============================================================================
# INTRODUCTION
# =============================================================================

def generate_introduction(
    report_input: ReportInput,
    config: ReportConfig,
) -> GeneratedSection:
    """
    Generate the introduction section.

    Includes objective, data source, and methodology (if technical style).

    Args:
        report_input: ReportInput with all data
        config: ReportConfig with style settings

    Returns:
        GeneratedSection with introduction content
    """
    style = config.style
    result = report_input.analysis_result

    lines = []

    # Objective subsection
    lines.append("### 1.1 Objective")
    lines.append("")

    if report_input.context:
        lines.append(report_input.context)
    else:
        lines.append(
            "This analysis aims to uncover patterns, relationships, and insights "
            "within the dataset that can inform decision-making and highlight "
            "areas requiring attention."
        )
    lines.append("")

    # Data Source subsection
    lines.append("### 1.2 Data Source")
    lines.append("")
    lines.append(f"**Source File:** `{report_input.source_file}`")
    lines.append(f"**Records Analyzed:** {result.rows_analyzed:,}")
    lines.append(f"**Fields Examined:** {result.columns_analyzed}")
    lines.append(f"**Analysis Depth:** {result.depth_level.replace('_', ' ').title()}")
    lines.append("")

    # Methodology subsection (technical style only)
    if style.include_methodology:
        lines.append("### 1.3 Methodology")
        lines.append("")
        methodology_text = get_style_methodology_text(style)
        if methodology_text:
            lines.append(methodology_text)
        lines.append("")

    return GeneratedSection(
        title="1. Introduction",
        content="\n".join(lines),
        level=2,
        section_id="introduction",
    )


# =============================================================================
# DATA OVERVIEW
# =============================================================================

def generate_data_overview(
    report_input: ReportInput,
    config: ReportConfig,
) -> GeneratedSection:
    """
    Generate the data overview section.

    Includes dataset description, data quality notes, and key metrics.

    Args:
        report_input: ReportInput with all data
        config: ReportConfig with style settings

    Returns:
        GeneratedSection with data overview content
    """
    style = config.style
    result = report_input.analysis_result

    lines = []

    # Dataset Description
    lines.append("### 2.1 Dataset Description")
    lines.append("")

    # Summary table
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Records | {result.rows_analyzed:,} |")
    lines.append(f"| Total Fields | {result.columns_analyzed} |")
    lines.append(f"| Numeric Fields | {len(result.descriptive_stats)} |")
    lines.append(f"| Analysis Depth | {result.depth_level.replace('_', ' ').title()} |")
    lines.append("")

    # Data Quality Notes
    if style.include_statistics:
        lines.append("### 2.2 Data Quality Notes")
        lines.append("")

        # Check for missing values in stats
        missing_issues = []
        for col_name, stats in result.descriptive_stats.items():
            if stats.missing_pct > 5:
                missing_issues.append(
                    f"- **{col_name}**: {format_percentage(stats.missing_pct / 100)} missing values"
                )

        if missing_issues:
            lines.append("**Columns with Missing Data:**")
            lines.extend(missing_issues[:5])  # Top 5
            if len(missing_issues) > 5:
                lines.append(f"- *...and {len(missing_issues) - 5} more*")
        else:
            lines.append("✅ No significant missing data detected.")
        lines.append("")

    # Key Metrics Definitions (technical only)
    if style.include_methodology and result.descriptive_stats:
        lines.append("### 2.3 Key Metrics")
        lines.append("")
        lines.append(format_stats_table(result.descriptive_stats))
        lines.append("")

    return GeneratedSection(
        title="2. Data Overview",
        content="\n".join(lines),
        level=2,
        section_id="data-overview",
    )


# =============================================================================
# KEY FINDINGS
# =============================================================================

def generate_key_findings(
    report_input: ReportInput,
    config: ReportConfig,
) -> GeneratedSection:
    """
    Generate the key findings section.

    Lists top findings sorted by importance with indicators.

    Args:
        report_input: ReportInput with all data
        config: ReportConfig with style settings

    Returns:
        GeneratedSection with key findings content
    """
    style = config.style
    result = report_input.analysis_result

    # Get findings up to max allowed by style
    top_findings = result.get_top_findings(style.max_findings)

    lines = []

    if not top_findings:
        lines.append("*No significant findings were identified in this analysis.*")
        return GeneratedSection(
            title="3. Key Findings",
            content="\n".join(lines),
            level=2,
            section_id="key-findings",
        )

    # Group by importance for better organization
    high_findings = [f for f in top_findings if f.importance == 'high']
    medium_findings = [f for f in top_findings if f.importance == 'medium']
    low_findings = [f for f in top_findings if f.importance == 'low']

    # Findings summary
    lines.append(
        f"The analysis identified **{len(result.findings)} findings** total: "
        f"**{len(high_findings)} high**, **{len(medium_findings)} medium**, "
        f"and **{len(low_findings)} low** importance."
    )
    lines.append("")

    # List findings with full detail for high/medium, brief for low
    finding_num = 1

    for finding in top_findings:
        indicator = format_importance_indicator(finding.importance)

        lines.append(f"### {finding_num}. {finding.title}")
        lines.append("")
        lines.append(f"**Importance:** {indicator} {finding.importance.title()}")

        if style.include_confidence:
            lines.append(f"**Confidence:** {format_confidence_level(finding.confidence)}")

        lines.append(f"**Category:** {finding.category.title()}")
        lines.append(f"**Columns:** {', '.join(finding.affected_columns)}")
        lines.append("")
        lines.append(finding.description)
        lines.append("")

        if finding.recommendation and style.max_recommendations > 0:
            lines.append(f"💡 **Recommendation:** {finding.recommendation}")
            lines.append("")

        finding_num += 1

    return GeneratedSection(
        title="3. Key Findings",
        content="\n".join(lines),
        level=2,
        section_id="key-findings",
    )


# =============================================================================
# DETAILED ANALYSIS
# =============================================================================

def generate_detailed_analysis(
    report_input: ReportInput,
    config: ReportConfig,
) -> GeneratedSection:
    """
    Generate the detailed analysis section.

    Includes correlations, trends, patterns, and segment comparisons.

    Args:
        report_input: ReportInput with all data
        config: ReportConfig with style settings

    Returns:
        GeneratedSection with detailed analysis content
    """
    style = config.style
    result = report_input.analysis_result

    lines = []

    # Skip detailed analysis for executive style
    if style.detail_level == 'low':
        lines.append(
            "*For detailed statistical analysis, please refer to the full technical report.*"
        )
        return GeneratedSection(
            title="4. Detailed Analysis",
            content="\n".join(lines),
            level=2,
            section_id="detailed-analysis",
        )

    # 4.1 Correlations & Relationships
    lines.append("### 4.1 Correlations & Relationships")
    lines.append("")

    if result.correlations:
        strong_corrs = [c for c in result.correlations if c.strength in ('strong', 'very_strong')]
        moderate_corrs = [c for c in result.correlations if c.strength == 'moderate']

        lines.append(
            f"Analysis found **{len(result.correlations)} significant correlations**, "
            f"including **{len(strong_corrs)} strong** relationships."
        )
        lines.append("")

        if style.include_statistics:
            lines.append(format_correlation_table(result.correlations))
            lines.append("")
        else:
            # Just list top correlations
            for corr in result.correlations[:5]:
                direction_arrow = "↑" if corr.direction == "positive" else "↓"
                lines.append(
                    f"- **{corr.column1}** & **{corr.column2}**: "
                    f"{corr.strength.replace('_', ' ').title()} {direction_arrow} "
                    f"({corr.coefficient:+.2f})"
                )
            lines.append("")
    else:
        lines.append("*No significant correlations detected.*")
        lines.append("")

    # 4.2 Trends & Patterns
    lines.append("### 4.2 Trends & Patterns")
    lines.append("")

    if result.trends:
        lines.append(format_trend_summary(result.trends))
        lines.append("")
    else:
        lines.append("*No time-based trends detected (no date column identified).*")
        lines.append("")

    # 4.3 Segment Comparisons
    if result.segments:
        lines.append("### 4.3 Segment Comparisons")
        lines.append("")

        significant_segments = [s for s in result.segments if s.variance_ratio >= 0.05]
        lines.append(
            f"Analysis compared metrics across **{len(significant_segments)} "
            f"categorical groupings** with statistically significant differences."
        )
        lines.append("")
        lines.append(format_segment_summary(significant_segments))
        lines.append("")

    # 4.4 Statistical Anomalies (technical only)
    if style.include_statistics:
        anomaly_findings = [
            f for f in result.findings
            if f.category in ('anomaly', 'statistic')
        ]

        if anomaly_findings:
            lines.append("### 4.4 Statistical Anomalies")
            lines.append("")

            for finding in anomaly_findings[:5]:
                lines.append(format_finding_brief(finding))
            lines.append("")

    return GeneratedSection(
        title="4. Detailed Analysis",
        content="\n".join(lines),
        level=2,
        section_id="detailed-analysis",
    )


# =============================================================================
# VISUALIZATIONS SECTION
# =============================================================================

def generate_visualizations_section(
    report_input: ReportInput,
    config: ReportConfig,
) -> GeneratedSection:
    """
    Generate the visualizations section.

    References charts with insights about each visualization.

    Args:
        report_input: ReportInput with all data
        config: ReportConfig with style settings

    Returns:
        GeneratedSection with visualization references
    """
    lines = []

    if not config.include_visualizations or not report_input.has_visualizations:
        lines.append("*No visualizations included in this report.*")
        return GeneratedSection(
            title="5. Visualizations",
            content="\n".join(lines),
            level=2,
            section_id="visualizations",
        )

    manifest = report_input.visualization_manifest

    lines.append(
        f"**{len(manifest.charts)} interactive visualizations** have been generated "
        f"to illustrate the analysis findings."
    )
    lines.append("")
    lines.append(f"📊 **Dashboard:** `{manifest.dashboard_file}`")
    lines.append(f"📂 **Location:** `{manifest.output_dir}`")
    lines.append("")

    # Chart listing
    lines.append("### Generated Charts")
    lines.append("")
    lines.append("| Chart | Type | Description |")
    lines.append("|-------|------|-------------|")

    chart_emojis = {
        'line': '📉',
        'bar': '📊',
        'scatter': '🔵',
        'heatmap': '🟦',
        'box': '📦',
        'pie': '🥧',
        'histogram': '📊',
    }

    for chart in manifest.charts:
        emoji = chart_emojis.get(chart.chart_type, '📈')
        # Truncate description if too long
        desc = chart.description
        if len(desc) > 60:
            desc = desc[:57] + "..."
        lines.append(f"| {emoji} {chart.title} | {chart.chart_type.title()} | {desc} |")

    lines.append("")
    lines.append(
        "*Open the dashboard HTML file in a browser for interactive exploration.*"
    )

    return GeneratedSection(
        title="5. Visualizations",
        content="\n".join(lines),
        level=2,
        section_id="visualizations",
    )


# =============================================================================
# RECOMMENDATIONS
# =============================================================================

def generate_recommendations(
    report_input: ReportInput,
    config: ReportConfig,
) -> GeneratedSection:
    """
    Generate the recommendations section.

    Compiles actionable recommendations from findings.

    Args:
        report_input: ReportInput with all data
        config: ReportConfig with style settings

    Returns:
        GeneratedSection with recommendations
    """
    style = config.style
    findings = report_input.analysis_result.findings

    lines = []

    # Extract actionable findings with recommendations
    actionable = [
        f for f in findings
        if f.actionable and f.recommendation
    ]

    # Sort by importance
    importance_order = {'high': 0, 'medium': 1, 'low': 2}
    actionable.sort(key=lambda f: (importance_order.get(f.importance, 3), -f.confidence))

    # Limit based on style
    actionable = actionable[:style.max_recommendations]

    if not actionable:
        lines.append("*No specific recommendations generated from this analysis.*")
        return GeneratedSection(
            title="6. Recommendations",
            content="\n".join(lines),
            level=2,
            section_id="recommendations",
        )

    # Immediate Actions
    high_priority = [f for f in actionable if f.importance == 'high']
    other_priority = [f for f in actionable if f.importance != 'high']

    if high_priority:
        lines.append("### 6.1 Immediate Actions")
        lines.append("")
        lines.append("The following require prompt attention:")
        lines.append("")

        for i, finding in enumerate(high_priority, 1):
            lines.append(f"**{i}. {finding.title}**")
            lines.append(f"   - {finding.recommendation}")
            lines.append("")

    if other_priority:
        lines.append("### 6.2 Further Investigation")
        lines.append("")
        lines.append("Consider investigating the following:")
        lines.append("")

        for finding in other_priority:
            indicator = format_importance_indicator(finding.importance)
            lines.append(f"- {indicator} **{finding.title}**: {finding.recommendation}")
        lines.append("")

    # General guidance based on findings
    if style.detail_level != 'low':
        lines.append("### 6.3 General Guidance")
        lines.append("")

        guidance_items = []

        # Add guidance based on what was found
        result = report_input.analysis_result

        if result.correlations:
            strong_corrs = [c for c in result.correlations if c.strength in ('strong', 'very_strong')]
            if strong_corrs:
                guidance_items.append(
                    "Review strong correlations for potential causal relationships "
                    "or redundant variables."
                )

        if result.trends:
            declining = [t for t in result.trends if t.trend_direction == 'decreasing']
            if declining:
                guidance_items.append(
                    "Monitor declining trends and investigate root causes."
                )

        if result.segments:
            significant = [s for s in result.segments if s.variance_ratio >= 0.1]
            if significant:
                guidance_items.append(
                    "Consider segment-specific strategies based on identified differences."
                )

        for item in guidance_items[:3]:
            lines.append(f"- {item}")

        if not guidance_items:
            lines.append("- Continue regular monitoring and analysis of key metrics.")

    return GeneratedSection(
        title="6. Recommendations",
        content="\n".join(lines),
        level=2,
        section_id="recommendations",
    )


# =============================================================================
# APPENDIX
# =============================================================================

def generate_appendix(
    report_input: ReportInput,
    config: ReportConfig,
) -> GeneratedSection:
    """
    Generate the appendix section.

    Includes data dictionary, methodology notes, and limitations.

    Args:
        report_input: ReportInput with all data
        config: ReportConfig with style settings

    Returns:
        GeneratedSection with appendix content
    """
    style = config.style
    result = report_input.analysis_result

    lines = []

    # Skip appendix for non-technical styles
    if not config.include_appendix:
        return GeneratedSection(
            title="7. Appendix",
            content="*Appendix not included in this report style.*",
            level=2,
            section_id="appendix",
        )

    # 7.1 Data Dictionary
    lines.append("### 7.1 Data Dictionary")
    lines.append("")

    if result.descriptive_stats:
        lines.append("| Column | Type | Count | Range |")
        lines.append("|--------|------|-------|-------|")

        for col_name, stats in result.descriptive_stats.items():
            col_range = f"{format_number(stats.min)} - {format_number(stats.max)}"
            lines.append(f"| {col_name} | Numeric | {stats.count:,} | {col_range} |")
        lines.append("")
    else:
        lines.append("*No column metadata available.*")
        lines.append("")

    # 7.2 Methodology Notes
    lines.append("### 7.2 Methodology Notes")
    lines.append("")

    methodology_notes = [
        "- Correlations calculated using Pearson coefficient (significance threshold: p < 0.05)",
        "- Trend detection via linear regression with R-squared goodness-of-fit",
        "- Segment comparisons using one-way ANOVA with eta-squared effect size",
        "- Outliers identified using IQR method (1.5× interquartile range)",
    ]

    for note in methodology_notes:
        lines.append(note)
    lines.append("")

    # 7.3 Limitations
    lines.append("### 7.3 Limitations")
    lines.append("")

    limitations = [
        "- Correlation does not imply causation",
        "- Results depend on data quality and completeness",
        "- Time-series analysis requires sufficient historical data",
        "- Categorical comparisons may not account for confounding variables",
    ]

    for limitation in limitations:
        lines.append(limitation)
    lines.append("")

    # Analysis metadata
    lines.append("### 7.4 Analysis Metadata")
    lines.append("")
    lines.append(f"- **Analysis Depth:** {result.depth_level}")
    lines.append(f"- **Records Analyzed:** {result.rows_analyzed:,}")
    lines.append(f"- **Columns Analyzed:** {result.columns_analyzed}")
    lines.append(f"- **Total Findings:** {len(result.findings)}")
    lines.append(f"- **Correlations Found:** {len(result.correlations)}")
    lines.append(f"- **Trends Detected:** {len(result.trends)}")
    lines.append(f"- **Segment Comparisons:** {len(result.segments)}")

    return GeneratedSection(
        title="7. Appendix",
        content="\n".join(lines),
        level=2,
        section_id="appendix",
    )


# =============================================================================
# ALL SECTIONS GENERATOR
# =============================================================================

def generate_all_sections(
    report_input: ReportInput,
    config: ReportConfig,
) -> List[GeneratedSection]:
    """
    Generate all report sections.

    Args:
        report_input: ReportInput with all data
        config: ReportConfig with style settings

    Returns:
        List of all GeneratedSection objects in order
    """
    sections = [
        generate_executive_summary(report_input, config),
        generate_introduction(report_input, config),
        generate_data_overview(report_input, config),
        generate_key_findings(report_input, config),
        generate_detailed_analysis(report_input, config),
    ]

    if config.include_visualizations:
        sections.append(generate_visualizations_section(report_input, config))

    sections.append(generate_recommendations(report_input, config))

    if config.include_appendix:
        sections.append(generate_appendix(report_input, config))

    return sections
