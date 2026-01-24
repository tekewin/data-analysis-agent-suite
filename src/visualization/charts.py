"""Chart builder functions for creating Plotly visualizations."""

from typing import List, Optional

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from .utils import (
    ChartConfig,
    ChartSpec,
    get_default_config,
    get_color_sequence,
    get_single_color,
    prepare_time_series_data,
    prepare_categorical_data,
    calculate_correlation_matrix,
)


# =============================================================================
# COMMON LAYOUT UTILITIES
# =============================================================================

def _apply_common_layout(
    fig: go.Figure,
    title: str,
    config: ChartConfig,
    x_title: Optional[str] = None,
    y_title: Optional[str] = None,
) -> go.Figure:
    """
    Apply common layout settings to a figure.

    Args:
        fig: Plotly figure to modify
        title: Chart title
        config: Chart configuration
        x_title: X-axis title
        y_title: Y-axis title

    Returns:
        Modified figure
    """
    layout_updates = {
        'title': {
            'text': title,
            'font': {'size': config.title_font_size},
            'x': 0.5,
            'xanchor': 'center',
        },
        'template': config.theme,
        'showlegend': config.show_legend,
        'height': config.height,
        'margin': {'l': 60, 'r': 40, 't': 60, 'b': 60},
        'hovermode': 'closest',
    }

    if config.width:
        layout_updates['width'] = config.width

    if x_title:
        layout_updates['xaxis'] = {'title': {'text': x_title, 'font': {'size': config.axis_font_size}}}

    if y_title:
        layout_updates['yaxis'] = {'title': {'text': y_title, 'font': {'size': config.axis_font_size}}}

    fig.update_layout(**layout_updates)

    return fig


def _validate_columns_exist(df: pd.DataFrame, columns: List[str], chart_type: str) -> None:
    """
    Validate that required columns exist in the DataFrame.

    Args:
        df: DataFrame to check
        columns: List of column names to validate
        chart_type: Chart type for error message

    Raises:
        ValueError: If any column is missing
    """
    missing = [col for col in columns if col and col not in df.columns]
    if missing:
        raise ValueError(
            f"Cannot create {chart_type} chart: missing columns {missing}. "
            f"Available columns: {list(df.columns)}"
        )


# =============================================================================
# LINE CHART
# =============================================================================

def create_line_chart(
    df: pd.DataFrame,
    spec: ChartSpec,
    config: Optional[ChartConfig] = None,
) -> go.Figure:
    """
    Create an interactive line chart for time series or sequential data.

    Args:
        df: DataFrame with source data
        spec: Chart specification with x_column, y_column (or y_columns)
        config: Optional chart configuration

    Returns:
        Plotly Figure object

    Raises:
        ValueError: If required columns are missing
    """
    if config is None:
        config = get_default_config()

    # Determine y columns
    y_cols = spec.y_columns if spec.y_columns else ([spec.y_column] if spec.y_column else [])
    if not y_cols:
        raise ValueError("Line chart requires at least one y column")

    required_cols = [spec.x_column] + y_cols
    _validate_columns_exist(df, required_cols, 'line')

    # Prepare data (sort by x if it's datetime)
    plot_df = df.copy()
    try:
        plot_df[spec.x_column] = pd.to_datetime(plot_df[spec.x_column])
        plot_df = plot_df.sort_values(spec.x_column)
    except (ValueError, TypeError):
        pass  # Not a datetime column, keep original order

    # Create figure
    fig = go.Figure()

    colors = get_color_sequence(len(y_cols), config)

    for i, y_col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=plot_df[spec.x_column],
            y=plot_df[y_col],
            mode='lines+markers',
            name=y_col,
            line={'color': colors[i], 'width': 2},
            marker={'size': 6},
            hovertemplate=f'{y_col}: %{{y:,.2f}}<br>{spec.x_column}: %{{x}}<extra></extra>',
        ))

    # Apply layout
    fig = _apply_common_layout(
        fig, spec.title, config,
        x_title=spec.x_column,
        y_title=y_cols[0] if len(y_cols) == 1 else 'Value'
    )

    return fig


# =============================================================================
# BAR CHART
# =============================================================================

def create_bar_chart(
    df: pd.DataFrame,
    spec: ChartSpec,
    config: Optional[ChartConfig] = None,
    orientation: str = 'v',
) -> go.Figure:
    """
    Create an interactive bar chart for categorical comparisons.

    Args:
        df: DataFrame with source data
        spec: Chart specification with x_column, y_column
        config: Optional chart configuration
        orientation: 'v' for vertical, 'h' for horizontal

    Returns:
        Plotly Figure object

    Raises:
        ValueError: If required columns are missing
    """
    if config is None:
        config = get_default_config()

    _validate_columns_exist(df, [spec.x_column, spec.y_column], 'bar')

    # Aggregate data by category
    plot_df = prepare_categorical_data(df, spec.x_column, spec.y_column, aggregation='sum')

    # Create figure
    if spec.color_column and spec.color_column in df.columns:
        # Grouped bar chart
        fig = px.bar(
            df,
            x=spec.x_column if orientation == 'v' else spec.y_column,
            y=spec.y_column if orientation == 'v' else spec.x_column,
            color=spec.color_column,
            orientation=orientation,
            color_discrete_sequence=config.color_palette,
        )
    else:
        # Simple bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=plot_df[spec.x_column] if orientation == 'v' else plot_df[spec.y_column],
            y=plot_df[spec.y_column] if orientation == 'v' else plot_df[spec.x_column],
            orientation=orientation,
            marker_color=get_single_color(0, config),
            hovertemplate=f'{spec.x_column}: %{{x}}<br>{spec.y_column}: %{{y:,.2f}}<extra></extra>'
            if orientation == 'v' else
            f'{spec.x_column}: %{{y}}<br>{spec.y_column}: %{{x:,.2f}}<extra></extra>',
        ))

    # Apply layout
    fig = _apply_common_layout(
        fig, spec.title, config,
        x_title=spec.x_column if orientation == 'v' else spec.y_column,
        y_title=spec.y_column if orientation == 'v' else spec.x_column
    )

    return fig


# =============================================================================
# SCATTER CHART
# =============================================================================

def create_scatter_chart(
    df: pd.DataFrame,
    spec: ChartSpec,
    config: Optional[ChartConfig] = None,
) -> go.Figure:
    """
    Create an interactive scatter plot for correlation analysis.

    Args:
        df: DataFrame with source data
        spec: Chart specification with x_column, y_column, optional color_column
        config: Optional chart configuration

    Returns:
        Plotly Figure object

    Raises:
        ValueError: If required columns are missing
    """
    if config is None:
        config = get_default_config()

    _validate_columns_exist(df, [spec.x_column, spec.y_column], 'scatter')

    # Create figure
    if spec.color_column and spec.color_column in df.columns:
        fig = px.scatter(
            df,
            x=spec.x_column,
            y=spec.y_column,
            color=spec.color_column,
            color_discrete_sequence=config.color_palette,
        )
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[spec.x_column],
            y=df[spec.y_column],
            mode='markers',
            marker={
                'color': get_single_color(0, config),
                'size': 8,
                'opacity': 0.7,
            },
            hovertemplate=f'{spec.x_column}: %{{x:,.2f}}<br>{spec.y_column}: %{{y:,.2f}}<extra></extra>',
        ))

    # Add trendline
    try:
        x_numeric = pd.to_numeric(df[spec.x_column], errors='coerce')
        y_numeric = pd.to_numeric(df[spec.y_column], errors='coerce')
        mask = x_numeric.notna() & y_numeric.notna()

        if mask.sum() >= 2:
            z = np.polyfit(x_numeric[mask], y_numeric[mask], 1)
            p = np.poly1d(z)
            x_range = np.linspace(x_numeric[mask].min(), x_numeric[mask].max(), 50)

            fig.add_trace(go.Scatter(
                x=x_range,
                y=p(x_range),
                mode='lines',
                name='Trend',
                line={'color': 'rgba(128, 128, 128, 0.5)', 'dash': 'dash'},
                hoverinfo='skip',
            ))
    except (ValueError, TypeError):
        pass  # Skip trendline if data isn't suitable

    # Apply layout
    fig = _apply_common_layout(
        fig, spec.title, config,
        x_title=spec.x_column,
        y_title=spec.y_column
    )

    return fig


# =============================================================================
# HEATMAP (CORRELATION MATRIX)
# =============================================================================

def create_heatmap(
    df: pd.DataFrame,
    spec: ChartSpec,
    config: Optional[ChartConfig] = None,
) -> go.Figure:
    """
    Create an interactive heatmap for correlation matrices.

    Args:
        df: DataFrame with source data
        spec: Chart specification with columns list for correlation
        config: Optional chart configuration

    Returns:
        Plotly Figure object
    """
    if config is None:
        config = get_default_config()

    # Calculate correlation matrix
    columns = spec.columns if spec.columns else None
    corr_matrix = calculate_correlation_matrix(df, columns)

    if corr_matrix.empty:
        raise ValueError("Cannot create heatmap: no numeric columns found")

    # Create figure
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns.tolist(),
        y=corr_matrix.index.tolist(),
        colorscale='RdBu_r',
        zmin=-1,
        zmax=1,
        text=np.round(corr_matrix.values, 2),
        texttemplate='%{text}',
        textfont={'size': 10},
        hovertemplate='%{x} vs %{y}<br>Correlation: %{z:.3f}<extra></extra>',
        colorbar={'title': 'Correlation'},
    ))

    # Apply layout with square aspect ratio
    fig = _apply_common_layout(fig, spec.title, config)
    fig.update_layout(
        xaxis={'tickangle': 45},
        yaxis={'autorange': 'reversed'},
    )

    return fig


# =============================================================================
# BOX PLOT
# =============================================================================

def create_box_plot(
    df: pd.DataFrame,
    spec: ChartSpec,
    config: Optional[ChartConfig] = None,
) -> go.Figure:
    """
    Create an interactive box plot for distribution analysis.

    Args:
        df: DataFrame with source data
        spec: Chart specification with y_column, optional color_column for grouping
        config: Optional chart configuration

    Returns:
        Plotly Figure object

    Raises:
        ValueError: If required columns are missing
    """
    if config is None:
        config = get_default_config()

    _validate_columns_exist(df, [spec.y_column], 'box')

    # Create figure
    if spec.color_column and spec.color_column in df.columns:
        fig = px.box(
            df,
            x=spec.color_column,
            y=spec.y_column,
            color=spec.color_column,
            color_discrete_sequence=config.color_palette,
        )
    else:
        fig = go.Figure()
        fig.add_trace(go.Box(
            y=df[spec.y_column],
            name=spec.y_column,
            marker_color=get_single_color(0, config),
            boxpoints='outliers',
            hovertemplate=f'{spec.y_column}: %{{y:,.2f}}<extra></extra>',
        ))

    # Apply layout
    fig = _apply_common_layout(
        fig, spec.title, config,
        y_title=spec.y_column
    )

    return fig


# =============================================================================
# PIE CHART
# =============================================================================

def create_pie_chart(
    df: pd.DataFrame,
    spec: ChartSpec,
    config: Optional[ChartConfig] = None,
) -> go.Figure:
    """
    Create an interactive pie chart for composition analysis.

    Args:
        df: DataFrame with source data
        spec: Chart specification with x_column (categories), optional y_column (values)
        config: Optional chart configuration

    Returns:
        Plotly Figure object

    Raises:
        ValueError: If required columns are missing
    """
    if config is None:
        config = get_default_config()

    _validate_columns_exist(df, [spec.x_column], 'pie')

    # Prepare data - aggregate by category
    if spec.y_column and spec.y_column in df.columns:
        plot_df = prepare_categorical_data(df, spec.x_column, spec.y_column, aggregation='sum')
        values = plot_df[spec.y_column]
    else:
        # Count occurrences
        plot_df = df[spec.x_column].value_counts().reset_index()
        plot_df.columns = [spec.x_column, 'count']
        values = plot_df['count']

    labels = plot_df[spec.x_column]

    # Create figure
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        hole=0.3,  # Makes it a donut chart for better readability
        marker={'colors': get_color_sequence(len(labels), config)},
        textinfo='percent+label',
        textposition='outside',
        hovertemplate='%{label}<br>Value: %{value:,.0f}<br>Percent: %{percent}<extra></extra>',
    ))

    # Apply layout
    fig = _apply_common_layout(fig, spec.title, config)
    fig.update_layout(showlegend=True)

    return fig


# =============================================================================
# HISTOGRAM
# =============================================================================

def create_histogram(
    df: pd.DataFrame,
    spec: ChartSpec,
    config: Optional[ChartConfig] = None,
    nbins: Optional[int] = None,
) -> go.Figure:
    """
    Create an interactive histogram for frequency distribution analysis.

    Args:
        df: DataFrame with source data
        spec: Chart specification with x_column
        config: Optional chart configuration
        nbins: Number of bins (auto-calculated if not specified)

    Returns:
        Plotly Figure object

    Raises:
        ValueError: If required columns are missing
    """
    if config is None:
        config = get_default_config()

    _validate_columns_exist(df, [spec.x_column], 'histogram')

    # Create figure
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df[spec.x_column],
        nbinsx=nbins,
        marker_color=get_single_color(0, config),
        opacity=0.8,
        hovertemplate=f'{spec.x_column}: %{{x}}<br>Count: %{{y}}<extra></extra>',
    ))

    # Apply layout
    fig = _apply_common_layout(
        fig, spec.title, config,
        x_title=spec.x_column,
        y_title='Frequency'
    )

    return fig


# =============================================================================
# CHART FACTORY
# =============================================================================

CHART_BUILDERS = {
    'line': create_line_chart,
    'bar': create_bar_chart,
    'scatter': create_scatter_chart,
    'heatmap': create_heatmap,
    'box': create_box_plot,
    'pie': create_pie_chart,
    'histogram': create_histogram,
}


def create_chart(
    df: pd.DataFrame,
    spec: ChartSpec,
    config: Optional[ChartConfig] = None,
) -> go.Figure:
    """
    Create a chart based on the specification.

    Factory function that dispatches to the appropriate chart builder.

    Args:
        df: DataFrame with source data
        spec: Chart specification
        config: Optional chart configuration

    Returns:
        Plotly Figure object

    Raises:
        ValueError: If chart_type is not supported
    """
    builder = CHART_BUILDERS.get(spec.chart_type)
    if builder is None:
        supported = list(CHART_BUILDERS.keys())
        raise ValueError(
            f"Unknown chart type '{spec.chart_type}'. "
            f"Supported types: {supported}"
        )

    return builder(df, spec, config)
