"""Report generation utilities for data analysis.

This module provides functions for generating markdown reports
and saving analysis results to files.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json

from .statistics import AnalysisResult, DescriptiveStats, AnalysisFinding
from .utils import format_number, format_percentage


def generate_analysis_report(
    result: AnalysisResult,
    source_file: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Generate a markdown report from analysis results.

    Args:
        result: AnalysisResult containing all findings
        source_file: Path to the original data file
        output_dir: Optional output directory path

    Returns:
        Markdown formatted report string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_name = Path(source_file).name

    # Build report sections
    sections = []

    # Header
    sections.append(f"# Data Analysis Report\n")
    sections.append(f"**Generated:** {timestamp}")
    sections.append(f"**Source File:** `{source_name}`")
    sections.append(f"**Analysis Depth:** {result.depth_level}")
    sections.append("")

    # Summary section
    sections.append("---\n")
    sections.append("## Summary\n")
    sections.append(f"| Metric | Value |")
    sections.append(f"|--------|-------|")
    sections.append(f"| Rows Analyzed | {result.rows_analyzed:,} |")
    sections.append(f"| Columns Analyzed | {result.columns_analyzed} |")
    sections.append(f"| Total Findings | {len(result.findings)} |")
    sections.append(f"| High Importance | {len(result.get_findings_by_importance('high'))} |")
    sections.append(f"| Correlations Found | {len(result.correlations)} |")
    sections.append(f"| Trends Detected | {len(result.trends)} |")
    sections.append(f"| Segment Comparisons | {len(result.segments)} |")
    sections.append("")

    # Key Findings section
    sections.append("---\n")
    sections.append("## Key Findings\n")

    top_findings = result.get_top_findings(10)
    if top_findings:
        for i, finding in enumerate(top_findings, 1):
            importance_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(finding.importance, '⚪')

            sections.append(f"### {i}. {finding.title}\n")
            sections.append(f"**Importance:** {importance_emoji} {finding.importance.title()}")
            sections.append(f"**Confidence:** {format_percentage(finding.confidence)}")
            sections.append(f"**Category:** {finding.category.title()}")
            sections.append(f"**Columns:** {', '.join(finding.affected_columns)}")
            sections.append("")
            sections.append(finding.description)
            sections.append("")

            if finding.recommendation:
                sections.append(f"💡 **Recommendation:** {finding.recommendation}")
                sections.append("")
    else:
        sections.append("*No significant findings detected.*\n")

    # Descriptive Statistics section
    if result.descriptive_stats:
        sections.append("---\n")
        sections.append("## Descriptive Statistics\n")
        sections.append("| Column | Count | Mean | Median | Std | Min | Max |")
        sections.append("|--------|-------|------|--------|-----|-----|-----|")

        for col_name, stats in result.descriptive_stats.items():
            sections.append(
                f"| {col_name} | {stats.count:,} | "
                f"{format_number(stats.mean)} | {format_number(stats.median)} | "
                f"{format_number(stats.std)} | {format_number(stats.min)} | "
                f"{format_number(stats.max)} |"
            )

        sections.append("")

    # Correlations section
    if result.correlations:
        sections.append("---\n")
        sections.append("## Significant Correlations\n")
        sections.append("| Column 1 | Column 2 | Correlation | Strength | Direction |")
        sections.append("|----------|----------|-------------|----------|-----------|")

        for corr in result.correlations[:15]:  # Top 15
            sections.append(
                f"| {corr.column1} | {corr.column2} | "
                f"{corr.coefficient:.3f} | {corr.strength} | {corr.direction} |"
            )

        sections.append("")

    # Trends section
    if result.trends:
        sections.append("---\n")
        sections.append("## Time-Based Trends\n")
        sections.append("| Column | Direction | Growth Rate | R² | Seasonality |")
        sections.append("|--------|-----------|-------------|----|--------------")

        for trend in result.trends:
            growth = format_percentage(trend.growth_rate_pct / 100) if trend.growth_rate_pct else "N/A"
            seasonality = trend.seasonal_period if trend.seasonality_detected else "None"
            sections.append(
                f"| {trend.column} | {trend.trend_direction} | "
                f"{growth} | {trend.r_squared:.2f} | {seasonality} |"
            )

        sections.append("")

    # Segments section
    if result.segments:
        sections.append("---\n")
        sections.append("## Segment Comparisons\n")

        for seg in result.segments[:10]:  # Top 10
            sections.append(f"### {seg.metric_column} by {seg.segment_column}\n")
            sections.append(f"**Variance Ratio:** {format_percentage(seg.variance_ratio)}\n")

            if seg.notable_differences:
                sections.append("**Notable Differences:**")
                for diff in seg.notable_differences:
                    sections.append(f"- {diff}")
                sections.append("")

            sections.append("| Segment | Count | Mean | Std |")
            sections.append("|---------|-------|------|-----|")

            sorted_segs = sorted(
                seg.segments.items(),
                key=lambda x: x[1]['mean'],
                reverse=True
            )

            for seg_name, seg_stats in sorted_segs:
                sections.append(
                    f"| {seg_name} | {seg_stats['count']:,} | "
                    f"{format_number(seg_stats['mean'])} | "
                    f"{format_number(seg_stats['std'])} |"
                )

            sections.append("")

    # Findings by Category section
    sections.append("---\n")
    sections.append("## All Findings by Category\n")

    categories = {}
    for finding in result.findings:
        if finding.category not in categories:
            categories[finding.category] = []
        categories[finding.category].append(finding)

    for category, findings_list in sorted(categories.items()):
        sections.append(f"### {category.title()} ({len(findings_list)})\n")

        for finding in findings_list:
            importance_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(finding.importance, '⚪')
            sections.append(f"- {importance_emoji} **{finding.title}** - {finding.description[:100]}...")
            sections.append("")

    # Footer
    sections.append("---\n")
    sections.append("*Generated by @data-analyzer agent*\n")

    return "\n".join(sections)


def save_analysis_results(
    result: AnalysisResult,
    report: str,
    source_file: str,
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    Save analysis results to files.

    Creates:
    - Markdown report file
    - JSON results file (for programmatic access)

    Args:
        result: AnalysisResult to save
        report: Generated markdown report
        source_file: Original source file path
        output_dir: Optional output directory

    Returns:
        Dictionary with paths to saved files
    """
    # Determine output directory
    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = Path("./output")

    out_path.mkdir(parents=True, exist_ok=True)

    # Generate filenames with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    source_name = Path(source_file).stem

    report_filename = f"{source_name}_analysis_{timestamp}.md"
    json_filename = f"{source_name}_analysis_{timestamp}.json"

    report_path = out_path / report_filename
    json_path = out_path / json_filename

    # Save markdown report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    # Save JSON results
    json_data = result.to_dict()
    json_data['metadata'] = {
        'source_file': source_file,
        'generated_at': timestamp,
        'report_file': report_filename,
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)

    return {
        'report': str(report_path),
        'json': str(json_path),
    }


def format_finding_summary(finding: AnalysisFinding) -> str:
    """
    Format a single finding as a concise summary.

    Args:
        finding: The finding to format

    Returns:
        Formatted string summary
    """
    importance_emoji = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    }.get(finding.importance, '⚪')

    lines = [
        f"{importance_emoji} **{finding.title}**",
        f"   {finding.description}",
    ]

    if finding.recommendation:
        lines.append(f"   💡 {finding.recommendation}")

    return "\n".join(lines)


def format_stats_table(stats_dict: Dict[str, DescriptiveStats]) -> str:
    """
    Format descriptive statistics as a markdown table.

    Args:
        stats_dict: Dictionary of column name to DescriptiveStats

    Returns:
        Markdown table string
    """
    if not stats_dict:
        return "*No numeric columns analyzed.*"

    lines = [
        "| Column | Count | Mean | Median | Std | Min | Max | Skewness |",
        "|--------|-------|------|--------|-----|-----|-----|----------|",
    ]

    for col_name, stats in stats_dict.items():
        lines.append(
            f"| {col_name} | {stats.count:,} | "
            f"{format_number(stats.mean)} | {format_number(stats.median)} | "
            f"{format_number(stats.std)} | {format_number(stats.min)} | "
            f"{format_number(stats.max)} | {stats.skewness:.2f} |"
        )

    return "\n".join(lines)
