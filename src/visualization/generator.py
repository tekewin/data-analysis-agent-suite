"""Chart generation orchestration and recommendation logic."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go

from .utils import (
    ChartConfig,
    ChartSpec,
    get_default_config,
    detect_chart_candidates,
    sanitize_filename,
)
from .charts import create_chart


# =============================================================================
# OUTPUT DATACLASSES
# =============================================================================

@dataclass
class GeneratedChart:
    """Result of generating a single chart."""

    chart_type: str
    title: str
    filename: str
    filepath: str
    columns_used: List[str]
    description: str
    html_content: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'chart_type': self.chart_type,
            'title': self.title,
            'filename': self.filename,
            'filepath': self.filepath,
            'columns_used': self.columns_used,
            'description': self.description,
        }


@dataclass
class VisualizationResult:
    """Complete visualization output."""

    charts: List[GeneratedChart]
    dashboard_path: str
    manifest_path: str
    output_dir: str
    total_charts: int
    source_file: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'charts': [c.to_dict() for c in self.charts],
            'dashboard_path': self.dashboard_path,
            'manifest_path': self.manifest_path,
            'output_dir': self.output_dir,
            'total_charts': self.total_charts,
            'source_file': self.source_file,
            'generated_at': self.generated_at,
        }


# =============================================================================
# RECOMMENDATION FUNCTIONS
# =============================================================================

def recommend_visualizations(
    df: pd.DataFrame,
    max_recommendations: int = 8,
) -> List[ChartSpec]:
    """
    Automatically recommend visualizations based on data structure.

    Analyzes the DataFrame and suggests appropriate chart types
    based on column types and relationships.

    Args:
        df: DataFrame to analyze
        max_recommendations: Maximum number of charts to recommend

    Returns:
        List of ChartSpec recommendations
    """
    candidates = detect_chart_candidates(df)

    # Prioritize diversity - one of each type first
    seen_types = set()
    prioritized = []
    remaining = []

    for spec in candidates:
        if spec.chart_type not in seen_types:
            prioritized.append(spec)
            seen_types.add(spec.chart_type)
        else:
            remaining.append(spec)

    # Combine prioritized + remaining, limited to max
    result = prioritized + remaining
    return result[:max_recommendations]


def get_chart_type_description(chart_type: str) -> str:
    """
    Get a human-readable description of what a chart type shows.

    Args:
        chart_type: Type of chart

    Returns:
        Description string
    """
    descriptions = {
        'line': 'Shows trends over time or sequential data',
        'bar': 'Compares values across categories',
        'scatter': 'Reveals relationships between two numeric variables',
        'heatmap': 'Displays correlation strength between multiple variables',
        'box': 'Shows data distribution, quartiles, and outliers',
        'pie': 'Shows proportional composition of categories',
        'histogram': 'Shows frequency distribution of values',
    }
    return descriptions.get(chart_type, 'Visualizes data')


# =============================================================================
# CHART GENERATION
# =============================================================================

def generate_chart(
    df: pd.DataFrame,
    spec: ChartSpec,
    config: Optional[ChartConfig] = None,
) -> go.Figure:
    """
    Generate a single chart from a specification.

    Args:
        df: DataFrame with source data
        spec: Chart specification
        config: Optional chart configuration

    Returns:
        Plotly Figure object
    """
    if config is None:
        config = get_default_config()

    return create_chart(df, spec, config)


def save_chart_html(
    fig: go.Figure,
    filepath: str,
    include_plotlyjs: str = 'cdn',
) -> str:
    """
    Save a Plotly figure to an HTML file.

    Args:
        fig: Plotly Figure to save
        filepath: Destination file path
        include_plotlyjs: How to include Plotly JS ('cdn', 'inline', True, False)

    Returns:
        Absolute path to saved file
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    html_content = fig.to_html(
        include_plotlyjs=include_plotlyjs,
        full_html=True,
        config={
            'responsive': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
        }
    )

    path.write_text(html_content, encoding='utf-8')
    return str(path.resolve())


def generate_all_charts(
    df: pd.DataFrame,
    specs: List[ChartSpec],
    output_dir: str,
    config: Optional[ChartConfig] = None,
) -> List[GeneratedChart]:
    """
    Generate multiple charts and save to files.

    Args:
        df: DataFrame with source data
        specs: List of chart specifications to generate
        output_dir: Directory to save chart HTML files
        config: Optional chart configuration

    Returns:
        List of GeneratedChart results
    """
    if config is None:
        config = get_default_config()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = []

    for spec in specs:
        try:
            # Generate the chart
            fig = generate_chart(df, spec, config)

            # Determine filename
            filename = f"{spec.chart_type}_{sanitize_filename(spec.title)}.html"
            filepath = output_path / filename

            # Save to file
            html_content = fig.to_html(
                include_plotlyjs='cdn',
                full_html=True,
                config={
                    'responsive': True,
                    'displayModeBar': True,
                    'displaylogo': False,
                }
            )
            filepath.write_text(html_content, encoding='utf-8')

            # Collect columns used
            columns_used = _get_columns_from_spec(spec)

            # Create result
            result = GeneratedChart(
                chart_type=spec.chart_type,
                title=spec.title,
                filename=filename,
                filepath=str(filepath.resolve()),
                columns_used=columns_used,
                description=spec.description or get_chart_type_description(spec.chart_type),
                html_content=html_content,
            )
            results.append(result)

        except Exception as e:
            # Log error but continue with other charts
            print(f"Warning: Failed to generate '{spec.title}': {e}")
            continue

    return results


def _get_columns_from_spec(spec: ChartSpec) -> List[str]:
    """
    Extract the list of columns used by a chart specification.

    Args:
        spec: Chart specification

    Returns:
        List of column names
    """
    columns = []

    if spec.x_column:
        columns.append(spec.x_column)
    if spec.y_column:
        columns.append(spec.y_column)
    if spec.y_columns:
        columns.extend(spec.y_columns)
    if spec.color_column:
        columns.append(spec.color_column)
    if spec.columns:
        columns.extend(spec.columns)

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for col in columns:
        if col not in seen:
            seen.add(col)
            unique.append(col)

    return unique


# =============================================================================
# OUTPUT DIRECTORY MANAGEMENT
# =============================================================================

def create_output_directory(
    source_file: str,
    base_dir: str = './output',
) -> str:
    """
    Create a timestamped output directory for visualizations.

    Args:
        source_file: Name of the source data file
        base_dir: Base output directory

    Returns:
        Path to created directory
    """
    # Extract base name from source file
    source_name = Path(source_file).stem
    source_name = sanitize_filename(source_name)

    # Create timestamped directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"{source_name}_visualizations_{timestamp}"

    output_path = Path(base_dir) / dir_name
    output_path.mkdir(parents=True, exist_ok=True)

    return str(output_path)
