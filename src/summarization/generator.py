"""Executive summary generation orchestration.

This module provides the main entry point for generating complete executive
summaries, compiling sections, and saving the output to files.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .loader import SummaryInput
from .extractor import (
    ExtractedData,
    SummaryConfig,
    extract_all,
)
from .formatter import (
    format_summary_header,
    format_bluf_section,
    format_metrics_table,
    format_finding_list,
    format_action_list,
    format_risk_list,
    format_summary_footer,
)


# =============================================================================
# SUMMARY OUTPUT DATACLASS
# =============================================================================

@dataclass
class GeneratedSummary:
    """Complete executive summary output."""

    title: str
    content: str  # Full markdown content
    source_file: str
    generated_at: str
    finding_count: int
    action_count: int
    filepath: str = ""  # Set after saving

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'title': self.title,
            'source_file': self.source_file,
            'generated_at': self.generated_at,
            'finding_count': self.finding_count,
            'action_count': self.action_count,
            'filepath': self.filepath,
        }

    def to_markdown(self) -> str:
        """Return the full markdown content."""
        return self.content


# =============================================================================
# SUMMARY GENERATION
# =============================================================================

def generate_summary(
    input_data: SummaryInput,
    config: Optional[SummaryConfig] = None,
) -> GeneratedSummary:
    """
    Generate a complete executive summary from input data.

    This is the main entry point for summary generation.

    Args:
        input_data: SummaryInput with analysis results and/or report
        config: Optional SummaryConfig for customization

    Returns:
        GeneratedSummary ready for saving or further processing
    """
    if config is None:
        config = SummaryConfig()

    # Generate title from source file
    source_stem = Path(input_data.source_file).stem
    title = source_stem.replace('_', ' ').title()
    config.title = title

    # Extract all data
    extracted = extract_all(input_data, config)

    # Compile the summary
    content = compile_summary(extracted, config)

    return GeneratedSummary(
        title=config.title,
        content=content,
        source_file=input_data.source_file,
        generated_at=datetime.now().isoformat(),
        finding_count=len(extracted.top_findings),
        action_count=len(extracted.recommended_actions),
    )


def compile_summary(
    extracted: ExtractedData,
    config: SummaryConfig,
) -> str:
    """
    Compile extracted data into a markdown executive summary.

    Args:
        extracted: ExtractedData with all information
        config: SummaryConfig for formatting options

    Returns:
        Complete markdown document as string
    """
    sections = []

    # Header
    sections.append(format_summary_header(
        title=config.title,
        date=datetime.now().strftime("%Y-%m-%d"),
        analysis_period=extracted.analysis_period,
        source=extracted.source_report,
    ))

    # BLUF Section
    sections.append("## Bottom Line Up Front")
    sections.append("")
    sections.append(format_bluf_section(extracted.bluf))
    sections.append("")
    sections.append("---")
    sections.append("")

    # Metrics Table
    if config.include_metrics_table and extracted.metrics:
        sections.append("## Key Metrics at a Glance")
        sections.append("")
        sections.append(format_metrics_table(extracted.metrics))
        sections.append("")
        sections.append("---")
        sections.append("")

    # Top Findings
    sections.append("## Top Findings")
    sections.append("")
    sections.append(format_finding_list(extracted.top_findings))
    sections.append("---")
    sections.append("")

    # Recommended Actions
    sections.append("## Recommended Actions")
    sections.append("")
    sections.append(format_action_list(extracted.recommended_actions))
    sections.append("")
    sections.append("---")
    sections.append("")

    # Risks & Considerations
    sections.append("## Risks & Considerations")
    sections.append("")
    sections.append(format_risk_list(extracted.risks))
    sections.append("")

    # Footer
    sections.append(format_summary_footer(f"{extracted.source_report}_report.md"))

    return "\n".join(sections)


# =============================================================================
# FILE OPERATIONS
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


def generate_summary_filename(source_file: str) -> str:
    """
    Generate a timestamped filename for an executive summary.

    Args:
        source_file: Original source file name

    Returns:
        Filename like "sales_executive_summary_20240124_143022.md"
    """
    source_name = Path(source_file).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{source_name}_executive_summary_{timestamp}.md"


def save_summary(
    summary: GeneratedSummary,
    output_dir: Optional[str] = None,
) -> str:
    """
    Save a generated summary to a markdown file.

    Args:
        summary: GeneratedSummary to save
        output_dir: Output directory (defaults to ./output)

    Returns:
        Path to the saved file
    """
    out_path = ensure_output_dir(output_dir)

    filename = generate_summary_filename(summary.source_file)
    filepath = out_path / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(summary.content)

    summary.filepath = str(filepath)
    return str(filepath)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_summary_from_files(
    analysis_path: Optional[str] = None,
    report_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> GeneratedSummary:
    """
    Generate and save a summary directly from file paths.

    Convenience function that loads inputs, generates summary, and saves it.

    Args:
        analysis_path: Path to analysis JSON file
        report_path: Path to report markdown file
        output_dir: Output directory (defaults to ./output)

    Returns:
        GeneratedSummary with filepath set
    """
    from .loader import create_summary_input

    input_data = create_summary_input(
        analysis_path=analysis_path,
        report_path=report_path,
    )

    summary = generate_summary(input_data)

    if output_dir:
        save_summary(summary, output_dir)
    else:
        save_summary(summary)

    return summary


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================

def get_summary_stats(summary: GeneratedSummary) -> str:
    """
    Generate a human-readable summary of the generated summary.

    Args:
        summary: GeneratedSummary to describe

    Returns:
        Summary string for display
    """
    lines = [
        "✅ Executive Summary Complete!",
        "",
        f"📄 **Output:** `{summary.filepath}`",
        "",
        "**Summary includes:**",
        "- Bottom Line Up Front (key insight)",
    ]

    if summary.finding_count > 0:
        lines.append(f"- Top {summary.finding_count} findings with actions")

    if summary.action_count > 0:
        lines.append(f"- {summary.action_count} prioritized recommendations")

    lines.extend([
        "- Key metrics at a glance",
        "- Risk considerations",
        "",
        f"Generated at {summary.generated_at}",
    ])

    return "\n".join(lines)
