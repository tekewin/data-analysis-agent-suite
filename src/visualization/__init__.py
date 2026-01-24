"""Visualization utilities for the @data-visualizer agent.

This module provides tools for generating interactive Plotly visualizations
from pandas DataFrames, including automatic chart recommendation, dashboard
generation, and manifest tracking.

Example usage:
    from src.visualization import (
        recommend_visualizations,
        generate_all_charts,
        generate_dashboard,
        create_manifest,
        save_manifest,
    )

    # Get chart recommendations
    specs = recommend_visualizations(df)

    # Generate all charts
    charts = generate_all_charts(df, specs, output_dir)

    # Create dashboard
    dashboard_path = generate_dashboard(charts, source_file, output_dir)

    # Save manifest
    manifest = create_manifest(charts, source_file, output_dir)
    manifest_path = save_manifest(manifest, output_dir)
"""

# Configuration and utilities
from .utils import (
    ChartConfig,
    ChartSpec,
    get_default_config,
    detect_column_types,
    detect_chart_candidates,
    identify_date_column,
    identify_numeric_columns,
    identify_categorical_columns,
    sanitize_filename,
    get_color_sequence,
    prepare_time_series_data,
    prepare_categorical_data,
    calculate_correlation_matrix,
)

# Chart builders
from .charts import (
    create_chart,
    create_line_chart,
    create_bar_chart,
    create_scatter_chart,
    create_heatmap,
    create_box_plot,
    create_pie_chart,
    create_histogram,
    CHART_BUILDERS,
)

# Generation and orchestration
from .generator import (
    GeneratedChart,
    VisualizationResult,
    recommend_visualizations,
    generate_chart,
    generate_all_charts,
    save_chart_html,
    create_output_directory,
    get_chart_type_description,
)

# Dashboard generation
from .dashboard import (
    generate_dashboard,
    generate_dashboard_from_template,
    create_chart_card_html,
)

# Manifest management
from .manifest import (
    ChartManifest,
    ChartManifestEntry,
    create_manifest,
    create_manifest_entry,
    save_manifest,
    load_manifest,
)


__all__ = [
    # Configuration
    'ChartConfig',
    'ChartSpec',
    'get_default_config',
    # Detection utilities
    'detect_column_types',
    'detect_chart_candidates',
    'identify_date_column',
    'identify_numeric_columns',
    'identify_categorical_columns',
    # Data preparation
    'prepare_time_series_data',
    'prepare_categorical_data',
    'calculate_correlation_matrix',
    # Chart builders
    'create_chart',
    'create_line_chart',
    'create_bar_chart',
    'create_scatter_chart',
    'create_heatmap',
    'create_box_plot',
    'create_pie_chart',
    'create_histogram',
    'CHART_BUILDERS',
    # Generation
    'GeneratedChart',
    'VisualizationResult',
    'recommend_visualizations',
    'generate_chart',
    'generate_all_charts',
    'save_chart_html',
    'create_output_directory',
    'get_chart_type_description',
    # Dashboard
    'generate_dashboard',
    'generate_dashboard_from_template',
    'create_chart_card_html',
    # Manifest
    'ChartManifest',
    'ChartManifestEntry',
    'create_manifest',
    'create_manifest_entry',
    'save_manifest',
    'load_manifest',
    # Utilities
    'sanitize_filename',
    'get_color_sequence',
]
