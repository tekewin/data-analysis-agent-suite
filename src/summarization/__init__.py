"""Executive summary generation utilities for the @exec-summarizer agent.

This module provides BLUF-first executive summaries optimized for C-suite
consumption, distilling full analysis reports into scannable 1-2 page documents.

Example usage:
    from src.summarization import (
        create_summary_input,
        generate_summary,
        save_summary,
    )

    # Load data and generate summary
    input_data = create_summary_input(
        analysis_path="./output/sales_analysis_20240124_143022.json",
        report_path="./output/sales_report_business_20240124_144500.md",
    )

    summary = generate_summary(input_data)
    save_summary(summary, "./output")
"""

from .formatter import (
    format_status_indicator,
    format_importance_indicator,
    format_metrics_table,
    format_finding_block,
    format_finding_list,
    format_action_list,
    format_risk_list,
    format_bluf_section,
    format_summary_header,
    format_summary_footer,
    format_change,
    format_number_compact,
    format_currency,
)
from .loader import (
    SummaryInput,
    load_report,
    load_analysis_result,
    create_summary_input,
    find_report_files,
    find_latest_report,
    find_analysis_files,
    find_latest_analysis,
    find_visualization_directory,
    auto_discover_inputs,
    extract_title_from_report,
    extract_date_from_report,
)
from .extractor import (
    ExtractedMetric,
    ExtractedFinding,
    ExtractedData,
    SummaryConfig,
    extract_bluf,
    extract_metrics,
    extract_top_findings,
    extract_actions,
    extract_risks,
    extract_all,
    prioritize_findings,
    calculate_metric_status,
)
from .generator import (
    GeneratedSummary,
    generate_summary,
    compile_summary,
    save_summary,
    generate_summary_from_files,
    get_summary_stats,
    ensure_output_dir,
    generate_summary_filename,
)

__all__ = [
    # Formatter
    "format_status_indicator",
    "format_importance_indicator",
    "format_metrics_table",
    "format_finding_block",
    "format_finding_list",
    "format_action_list",
    "format_risk_list",
    "format_bluf_section",
    "format_summary_header",
    "format_summary_footer",
    "format_change",
    "format_number_compact",
    "format_currency",
    # Loader
    "SummaryInput",
    "load_report",
    "load_analysis_result",
    "create_summary_input",
    "find_report_files",
    "find_latest_report",
    "find_analysis_files",
    "find_latest_analysis",
    "find_visualization_directory",
    "auto_discover_inputs",
    "extract_title_from_report",
    "extract_date_from_report",
    # Extractor
    "ExtractedMetric",
    "ExtractedFinding",
    "ExtractedData",
    "SummaryConfig",
    "extract_bluf",
    "extract_metrics",
    "extract_top_findings",
    "extract_actions",
    "extract_risks",
    "extract_all",
    "prioritize_findings",
    "calculate_metric_status",
    # Generator
    "GeneratedSummary",
    "generate_summary",
    "compile_summary",
    "save_summary",
    "generate_summary_from_files",
    "get_summary_stats",
    "ensure_output_dir",
    "generate_summary_filename",
]
