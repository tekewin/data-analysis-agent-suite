"""Report generation orchestration.

This module provides the main entry point for generating complete reports,
compiling sections, and saving the output to files.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .loader import ReportInput
from .styles import ReportConfig, WritingStyle, get_style, create_default_config
from .sections import (
    GeneratedSection,
    generate_all_sections,
    generate_executive_summary,
    generate_introduction,
    generate_data_overview,
    generate_key_findings,
    generate_detailed_analysis,
    generate_visualizations_section,
    generate_recommendations,
    generate_appendix,
)
from .utils import (
    ensure_output_dir,
    format_date,
    generate_report_filename,
)


# =============================================================================
# REPORT OUTPUT DATACLASS
# =============================================================================

@dataclass
class GeneratedReport:
    """Complete report output."""

    title: str
    sections: List[GeneratedSection]
    style: str  # Style name used
    source_file: str
    generated_at: str
    total_findings: int
    total_charts: int
    filepath: str = ""  # Set after saving

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'title': self.title,
            'sections': [s.to_dict() for s in self.sections],
            'style': self.style,
            'source_file': self.source_file,
            'generated_at': self.generated_at,
            'total_findings': self.total_findings,
            'total_charts': self.total_charts,
            'filepath': self.filepath,
        }

    def to_markdown(self) -> str:
        """Compile the full report as markdown."""
        return compile_sections(self.sections, self.title, self.source_file, self.style)


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(
    report_input: ReportInput,
    config: Optional[ReportConfig] = None,
    style_name: Optional[str] = None,
) -> GeneratedReport:
    """
    Generate a complete report from analysis input.

    This is the main entry point for report generation.

    Args:
        report_input: ReportInput with analysis results and visualization manifest
        config: Optional ReportConfig (if not provided, created from style_name)
        style_name: Style name if config not provided (defaults to report_input.audience)

    Returns:
        GeneratedReport ready for saving or further processing
    """
    # Determine configuration
    if config is None:
        effective_style = style_name or report_input.audience
        # Generate title from source file
        source_stem = Path(report_input.source_file).stem
        title = f"{source_stem.replace('_', ' ').title()} Analysis Report"
        config = create_default_config(
            style_name=effective_style,
            title=title,
            include_visualizations=report_input.has_visualizations,
        )

    # Generate all sections
    sections = generate_all_sections(report_input, config)

    # Create the report object
    return GeneratedReport(
        title=config.title,
        sections=sections,
        style=config.style.name,
        source_file=report_input.source_file,
        generated_at=datetime.now().isoformat(),
        total_findings=report_input.finding_count,
        total_charts=report_input.chart_count,
    )


def generate_report_from_files(
    analysis_path: str,
    viz_path: Optional[str] = None,
    style_name: str = "business",
    output_dir: Optional[str] = None,
) -> GeneratedReport:
    """
    Generate and save a report directly from file paths.

    Convenience function that loads inputs, generates report, and saves it.

    Args:
        analysis_path: Path to analysis JSON file
        viz_path: Optional path to visualization manifest
        style_name: Writing style ('technical', 'business', 'executive')
        output_dir: Output directory (defaults to ./output)

    Returns:
        GeneratedReport with filepath set
    """
    from .loader import create_report_input

    # Load inputs
    report_input = create_report_input(
        analysis_path=analysis_path,
        viz_path=viz_path,
        audience=style_name,
    )

    # Generate report
    report = generate_report(report_input, style_name=style_name)

    # Save report
    filepath = save_report(report, output_dir)
    report.filepath = filepath

    return report


# =============================================================================
# COMPILATION AND OUTPUT
# =============================================================================

def compile_sections(
    sections: List[GeneratedSection],
    title: str = "Analysis Report",
    source_file: str = "",
    style: str = "business",
) -> str:
    """
    Compile report sections into a single markdown document.

    Args:
        sections: List of GeneratedSection objects
        title: Report title
        source_file: Source file name for header
        style: Style name for header

    Returns:
        Complete markdown document as string
    """
    lines = []

    # Report Header
    lines.append(f"# {title}")
    lines.append("")

    # Metadata block
    lines.append(f"**Generated:** {format_date()}")
    lines.append(f"**Source:** `{source_file}`")
    lines.append(f"**Style:** {style.title()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Add each section
    for section in sections:
        lines.append(section.to_markdown())
        lines.append("")
        lines.append("---")
        lines.append("")

    # Footer
    lines.append("*Generated by @report-writer agent*")
    lines.append("")

    return "\n".join(lines)


def save_report(
    report: GeneratedReport,
    output_dir: Optional[str] = None,
) -> str:
    """
    Save a generated report to a markdown file.

    Args:
        report: GeneratedReport to save
        output_dir: Output directory (defaults to ./output)

    Returns:
        Path to the saved file
    """
    # Ensure output directory exists
    out_path = ensure_output_dir(output_dir)

    # Generate filename
    filename = generate_report_filename(report.source_file, report.style)
    filepath = out_path / filename

    # Compile and write
    content = report.to_markdown()

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    # Update report with filepath
    report.filepath = str(filepath)

    return str(filepath)


# =============================================================================
# QUICK GENERATION HELPERS
# =============================================================================

def generate_technical_report(
    report_input: ReportInput,
    output_dir: Optional[str] = None,
) -> GeneratedReport:
    """
    Generate a technical-style report.

    Args:
        report_input: ReportInput with all data
        output_dir: Optional output directory

    Returns:
        GeneratedReport saved to file
    """
    report = generate_report(report_input, style_name='technical')
    if output_dir:
        save_report(report, output_dir)
    return report


def generate_business_report(
    report_input: ReportInput,
    output_dir: Optional[str] = None,
) -> GeneratedReport:
    """
    Generate a business-style report.

    Args:
        report_input: ReportInput with all data
        output_dir: Optional output directory

    Returns:
        GeneratedReport saved to file
    """
    report = generate_report(report_input, style_name='business')
    if output_dir:
        save_report(report, output_dir)
    return report


def generate_executive_report(
    report_input: ReportInput,
    output_dir: Optional[str] = None,
) -> GeneratedReport:
    """
    Generate an executive-style report.

    Args:
        report_input: ReportInput with all data
        output_dir: Optional output directory

    Returns:
        GeneratedReport saved to file
    """
    report = generate_report(report_input, style_name='executive')
    if output_dir:
        save_report(report, output_dir)
    return report


# =============================================================================
# REPORT SUMMARY
# =============================================================================

def get_report_summary(report: GeneratedReport) -> str:
    """
    Generate a human-readable summary of the report.

    Args:
        report: GeneratedReport to summarize

    Returns:
        Summary string for display
    """
    lines = [
        f"✅ Report Generated Successfully!",
        "",
        f"📄 **Output:** `{report.filepath}`",
        "",
        f"**Report Details:**",
        f"- Title: {report.title}",
        f"- Style: {report.style.title()}",
        f"- Sections: {len(report.sections)}",
        f"- Findings Included: {report.total_findings}",
    ]

    if report.total_charts > 0:
        lines.append(f"- Visualization References: {report.total_charts}")

    lines.extend([
        "",
        f"Generated at {report.generated_at}",
    ])

    return "\n".join(lines)
