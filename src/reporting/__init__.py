"""Report generation utilities for the @report-writer agent.

This module provides writing style configurations, section generators,
and report compilation for transforming analysis findings into
polished, audience-appropriate business reports.
"""

from .utils import (
    format_importance_indicator,
    format_confidence_level,
    format_finding_block,
    format_stats_table,
    format_correlation_table,
    format_trend_summary,
    format_segment_summary,
    format_number,
    format_percentage,
    format_date,
    ensure_output_dir,
)
from .styles import (
    WritingStyle,
    ReportConfig,
    get_style,
    get_available_styles,
    apply_style_to_finding,
    create_default_config,
)
from .loader import (
    ReportInput,
    load_analysis_result,
    load_visualization_manifest,
    create_report_input,
    find_analysis_files,
    find_visualization_manifest,
)
from .sections import (
    GeneratedSection,
    generate_executive_summary,
    generate_introduction,
    generate_data_overview,
    generate_key_findings,
    generate_detailed_analysis,
    generate_visualizations_section,
    generate_recommendations,
    generate_appendix,
    generate_all_sections,
)
from .generator import (
    GeneratedReport,
    generate_report,
    compile_sections,
    save_report,
)

__all__ = [
    # Utils
    "format_importance_indicator",
    "format_confidence_level",
    "format_finding_block",
    "format_stats_table",
    "format_correlation_table",
    "format_trend_summary",
    "format_segment_summary",
    "format_number",
    "format_percentage",
    "format_date",
    "ensure_output_dir",
    # Styles
    "WritingStyle",
    "ReportConfig",
    "get_style",
    "get_available_styles",
    "apply_style_to_finding",
    "create_default_config",
    # Loader
    "ReportInput",
    "load_analysis_result",
    "load_visualization_manifest",
    "create_report_input",
    "find_analysis_files",
    "find_visualization_manifest",
    # Sections
    "GeneratedSection",
    "generate_executive_summary",
    "generate_introduction",
    "generate_data_overview",
    "generate_key_findings",
    "generate_detailed_analysis",
    "generate_visualizations_section",
    "generate_recommendations",
    "generate_appendix",
    "generate_all_sections",
    # Generator
    "GeneratedReport",
    "generate_report",
    "compile_sections",
    "save_report",
]
