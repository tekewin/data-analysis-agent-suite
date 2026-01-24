"""Utility functions and dataclasses for the visualization module."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re

import pandas as pd
import numpy as np


# =============================================================================
# CONFIGURATION DATACLASSES
# =============================================================================

@dataclass
class ChartConfig:
    """Configuration for chart styling and defaults."""

    theme: str = "plotly_white"
    color_palette: List[str] = field(default_factory=lambda: [
        "#636EFA",  # blue
        "#EF553B",  # red
        "#00CC96",  # green
        "#AB63FA",  # purple
        "#FFA15A",  # orange
        "#19D3F3",  # cyan
        "#FF6692",  # pink
        "#B6E880",  # lime
        "#FF97FF",  # magenta
        "#FECB52",  # yellow
    ])
    show_legend: bool = True
    interactive: bool = True
    responsive: bool = True
    title_font_size: int = 18
    axis_font_size: int = 12
    height: int = 500
    width: Optional[int] = None  # None means responsive width

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'theme': self.theme,
            'color_palette': self.color_palette,
            'show_legend': self.show_legend,
            'interactive': self.interactive,
            'responsive': self.responsive,
            'title_font_size': self.title_font_size,
            'axis_font_size': self.axis_font_size,
            'height': self.height,
            'width': self.width,
        }


@dataclass
class ChartSpec:
    """Specification for a chart to generate."""

    chart_type: str  # 'line', 'bar', 'scatter', 'heatmap', 'box', 'pie', 'histogram'
    title: str
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    y_columns: List[str] = field(default_factory=list)  # For multi-series charts
    color_column: Optional[str] = None  # For grouping/coloring
    columns: List[str] = field(default_factory=list)  # For heatmaps, correlation matrices
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'chart_type': self.chart_type,
            'title': self.title,
            'x_column': self.x_column,
            'y_column': self.y_column,
            'y_columns': self.y_columns,
            'color_column': self.color_column,
            'columns': self.columns,
            'description': self.description,
        }


# =============================================================================
# DEFAULT CONFIGURATION
# =============================================================================

def get_default_config() -> ChartConfig:
    """Get default chart configuration."""
    return ChartConfig()


# =============================================================================
# COLOR UTILITIES
# =============================================================================

def get_color_sequence(n: int, config: Optional[ChartConfig] = None) -> List[str]:
    """
    Get a sequence of n colors from the palette, cycling if needed.

    Args:
        n: Number of colors needed
        config: Chart configuration with color palette

    Returns:
        List of n color hex codes
    """
    if config is None:
        config = get_default_config()

    palette = config.color_palette
    colors = []
    for i in range(n):
        colors.append(palette[i % len(palette)])
    return colors


def get_single_color(index: int = 0, config: Optional[ChartConfig] = None) -> str:
    """
    Get a single color from the palette.

    Args:
        index: Index in the palette (cycles if out of bounds)
        config: Chart configuration with color palette

    Returns:
        Color hex code
    """
    if config is None:
        config = get_default_config()

    palette = config.color_palette
    return palette[index % len(palette)]


# =============================================================================
# FILENAME UTILITIES
# =============================================================================

def sanitize_filename(title: str) -> str:
    """
    Convert a chart title to a safe filename.

    Args:
        title: Chart title (e.g., "Sales Over Time")

    Returns:
        Safe filename (e.g., "sales_over_time")
    """
    # Convert to lowercase
    filename = title.lower()
    # Replace spaces and special characters with underscores
    filename = re.sub(r'[^a-z0-9]+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    # Limit length
    if len(filename) > 50:
        filename = filename[:50].rstrip('_')
    return filename or "chart"


# =============================================================================
# COLUMN TYPE DETECTION
# =============================================================================

def detect_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Detect and categorize column types for visualization purposes.

    Args:
        df: DataFrame to analyze

    Returns:
        Dictionary with keys 'numeric', 'categorical', 'datetime', 'text'
    """
    result = {
        'numeric': [],
        'categorical': [],
        'datetime': [],
        'text': [],
    }

    for col in df.columns:
        col_type = _classify_column(df[col])
        result[col_type].append(col)

    return result


def _classify_column(series: pd.Series) -> str:
    """
    Classify a single column's type for visualization.

    Args:
        series: Pandas Series to classify

    Returns:
        One of 'numeric', 'categorical', 'datetime', 'text'
    """
    # Check for datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return 'datetime'

    # Try to convert to datetime if it looks like dates
    if series.dtype == object:
        sample = series.dropna().head(20)
        if len(sample) > 0:
            try:
                pd.to_datetime(sample, format='mixed')
                # If more than 80% can be parsed as dates, treat as datetime
                success_rate = pd.to_datetime(series, errors='coerce').notna().mean()
                if success_rate > 0.8:
                    return 'datetime'
            except (ValueError, TypeError):
                pass

    # Check for numeric
    if pd.api.types.is_numeric_dtype(series):
        return 'numeric'

    # Check for categorical (low cardinality strings)
    if series.dtype == object or pd.api.types.is_categorical_dtype(series):
        n_unique = series.nunique()
        n_total = len(series)

        # If less than 20 unique values or less than 5% of total, treat as categorical
        if n_unique <= 20 or (n_total > 0 and n_unique / n_total < 0.05):
            return 'categorical'
        else:
            return 'text'

    # Default to text
    return 'text'


def identify_date_column(df: pd.DataFrame) -> Optional[str]:
    """
    Find the most likely date/time column in a DataFrame.

    Args:
        df: DataFrame to analyze

    Returns:
        Column name or None if no date column found
    """
    col_types = detect_column_types(df)
    datetime_cols = col_types['datetime']

    if not datetime_cols:
        return None

    # Prefer columns with common date names
    date_keywords = ['date', 'time', 'timestamp', 'created', 'updated', 'day', 'month', 'year']
    for col in datetime_cols:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in date_keywords):
            return col

    # Return first datetime column
    return datetime_cols[0]


def identify_numeric_columns(df: pd.DataFrame) -> List[str]:
    """
    Get all numeric columns in a DataFrame.

    Args:
        df: DataFrame to analyze

    Returns:
        List of numeric column names
    """
    col_types = detect_column_types(df)
    return col_types['numeric']


def identify_categorical_columns(df: pd.DataFrame) -> List[str]:
    """
    Get all categorical columns in a DataFrame.

    Args:
        df: DataFrame to analyze

    Returns:
        List of categorical column names
    """
    col_types = detect_column_types(df)
    return col_types['categorical']


# =============================================================================
# CHART CANDIDATE DETECTION
# =============================================================================

def detect_chart_candidates(df: pd.DataFrame) -> List[ChartSpec]:
    """
    Automatically recommend chart types based on data structure.

    Analyzes the DataFrame and suggests appropriate visualizations
    based on column types and relationships.

    Args:
        df: DataFrame to analyze

    Returns:
        List of ChartSpec recommendations
    """
    candidates = []
    col_types = detect_column_types(df)

    numeric_cols = col_types['numeric']
    categorical_cols = col_types['categorical']
    datetime_cols = col_types['datetime']

    # 1. Time series line charts (date + numeric)
    if datetime_cols and numeric_cols:
        date_col = identify_date_column(df)
        if date_col:
            # Suggest line chart for first few numeric columns
            for num_col in numeric_cols[:3]:
                candidates.append(ChartSpec(
                    chart_type='line',
                    title=f'{num_col} Over Time',
                    x_column=date_col,
                    y_column=num_col,
                    description=f'Trend of {num_col} over {date_col}'
                ))

    # 2. Bar charts (categorical + numeric)
    if categorical_cols and numeric_cols:
        # Pick best categorical (not too many unique values)
        for cat_col in categorical_cols[:2]:
            n_unique = df[cat_col].nunique()
            if n_unique <= 15:  # Reasonable for bar chart
                for num_col in numeric_cols[:2]:
                    candidates.append(ChartSpec(
                        chart_type='bar',
                        title=f'{num_col} by {cat_col}',
                        x_column=cat_col,
                        y_column=num_col,
                        description=f'Comparison of {num_col} across {cat_col} categories'
                    ))

    # 3. Scatter plots (numeric vs numeric)
    if len(numeric_cols) >= 2:
        # Create scatter for first pair
        candidates.append(ChartSpec(
            chart_type='scatter',
            title=f'{numeric_cols[0]} vs {numeric_cols[1]}',
            x_column=numeric_cols[0],
            y_column=numeric_cols[1],
            color_column=categorical_cols[0] if categorical_cols else None,
            description=f'Relationship between {numeric_cols[0]} and {numeric_cols[1]}'
        ))

    # 4. Correlation heatmap (multiple numeric columns)
    if len(numeric_cols) >= 3:
        candidates.append(ChartSpec(
            chart_type='heatmap',
            title='Correlation Matrix',
            columns=numeric_cols[:10],  # Limit to 10 columns for readability
            description='Correlation coefficients between numeric variables'
        ))

    # 5. Box plots for distributions
    if numeric_cols:
        for num_col in numeric_cols[:2]:
            if categorical_cols:
                # Grouped box plot
                candidates.append(ChartSpec(
                    chart_type='box',
                    title=f'{num_col} Distribution by {categorical_cols[0]}',
                    y_column=num_col,
                    color_column=categorical_cols[0],
                    description=f'Distribution of {num_col} across {categorical_cols[0]} groups'
                ))
            else:
                # Simple box plot
                candidates.append(ChartSpec(
                    chart_type='box',
                    title=f'{num_col} Distribution',
                    y_column=num_col,
                    description=f'Distribution and outliers for {num_col}'
                ))

    # 6. Histograms
    if numeric_cols:
        for num_col in numeric_cols[:2]:
            candidates.append(ChartSpec(
                chart_type='histogram',
                title=f'{num_col} Frequency Distribution',
                x_column=num_col,
                description=f'Frequency distribution of {num_col} values'
            ))

    # 7. Pie charts (categorical with counts)
    if categorical_cols:
        for cat_col in categorical_cols[:1]:
            n_unique = df[cat_col].nunique()
            if 2 <= n_unique <= 8:  # Pie charts work best with few categories
                candidates.append(ChartSpec(
                    chart_type='pie',
                    title=f'{cat_col} Composition',
                    x_column=cat_col,
                    description=f'Proportional breakdown of {cat_col} categories'
                ))

    return candidates


# =============================================================================
# DATA PREPARATION UTILITIES
# =============================================================================

def prepare_time_series_data(
    df: pd.DataFrame,
    date_column: str,
    value_column: str,
    aggregation: str = 'mean'
) -> pd.DataFrame:
    """
    Prepare data for time series visualization by sorting and optionally aggregating.

    Args:
        df: Source DataFrame
        date_column: Name of date column
        value_column: Name of value column
        aggregation: Aggregation method if multiple values per date ('mean', 'sum', 'first')

    Returns:
        Prepared DataFrame sorted by date
    """
    # Ensure date column is datetime
    result = df.copy()
    result[date_column] = pd.to_datetime(result[date_column], errors='coerce')

    # Remove rows with invalid dates
    result = result.dropna(subset=[date_column])

    # Sort by date
    result = result.sort_values(date_column)

    # Aggregate if there are duplicates
    if result[date_column].duplicated().any():
        agg_func = {'mean': 'mean', 'sum': 'sum', 'first': 'first'}.get(aggregation, 'mean')
        result = result.groupby(date_column)[value_column].agg(agg_func).reset_index()

    return result


def prepare_categorical_data(
    df: pd.DataFrame,
    category_column: str,
    value_column: str,
    aggregation: str = 'sum',
    top_n: Optional[int] = None
) -> pd.DataFrame:
    """
    Prepare data for categorical visualizations (bar, pie) by aggregating.

    Args:
        df: Source DataFrame
        category_column: Name of category column
        value_column: Name of value column
        aggregation: Aggregation method ('sum', 'mean', 'count')
        top_n: Limit to top N categories by value

    Returns:
        Aggregated DataFrame
    """
    agg_func = {'sum': 'sum', 'mean': 'mean', 'count': 'count'}.get(aggregation, 'sum')

    result = df.groupby(category_column)[value_column].agg(agg_func).reset_index()
    result.columns = [category_column, value_column]

    # Sort by value descending
    result = result.sort_values(value_column, ascending=False)

    # Limit to top N if specified
    if top_n and len(result) > top_n:
        result = result.head(top_n)

    return result


def calculate_correlation_matrix(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calculate correlation matrix for numeric columns.

    Args:
        df: Source DataFrame
        columns: Specific columns to include (defaults to all numeric)

    Returns:
        Correlation matrix as DataFrame
    """
    if columns:
        numeric_df = df[columns].select_dtypes(include=[np.number])
    else:
        numeric_df = df.select_dtypes(include=[np.number])

    return numeric_df.corr()
