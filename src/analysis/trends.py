"""Time-series trend detection and analysis utilities.

This module provides functions for detecting trends, seasonality,
and growth patterns in time-series data.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np
from scipy import stats

from .utils import (
    identify_numeric_columns,
    identify_date_columns,
    calculate_confidence_score,
    classify_importance,
    safe_numeric_conversion,
    ColumnType,
    classify_column_type,
)
from .statistics import AnalysisFinding


@dataclass
class TrendAnalysis:
    """Time-based trend analysis for a numeric column."""
    column: str
    date_column: str
    trend_direction: str  # 'increasing', 'decreasing', 'stable', 'volatile'
    slope: float  # Rate of change per unit time
    r_squared: float  # Fit quality (0-1)
    growth_rate_pct: Optional[float] = None  # Percentage change over period
    seasonality_detected: bool = False
    seasonal_period: Optional[str] = None  # 'weekly', 'monthly', 'quarterly'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'column': self.column,
            'date_column': self.date_column,
            'trend_direction': self.trend_direction,
            'slope': round(self.slope, 6),
            'r_squared': round(self.r_squared, 4),
            'growth_rate_pct': round(self.growth_rate_pct, 2) if self.growth_rate_pct is not None else None,
            'seasonality_detected': self.seasonality_detected,
            'seasonal_period': self.seasonal_period,
        }

    def describe(self) -> str:
        """Generate a human-readable description of the trend."""
        if self.trend_direction == 'stable':
            return f"'{self.column}' shows no significant trend over time."

        direction = self.trend_direction
        growth = f" ({self.growth_rate_pct:+.1f}%)" if self.growth_rate_pct is not None else ""
        seasonality = f" with {self.seasonal_period} seasonality" if self.seasonality_detected else ""

        return f"'{self.column}' is {direction}{growth}{seasonality}."


def detect_date_column(df: pd.DataFrame) -> Optional[str]:
    """
    Detect the most likely date column for time-series analysis.

    Prioritizes columns by:
    1. Already datetime dtype
    2. Column name contains 'date', 'time', 'timestamp'
    3. Successfully parseable as dates

    Args:
        df: DataFrame to analyze

    Returns:
        Column name of detected date column, or None if not found
    """
    candidates = []

    for col in df.columns:
        series = df[col]
        score = 0

        # Check if already datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            score = 100
        else:
            # Check column name
            name_lower = col.lower()
            if any(kw in name_lower for kw in ['date', 'time', 'timestamp', 'created', 'updated']):
                score += 30

            # Try to parse as datetime
            if classify_column_type(series) == ColumnType.DATE:
                score += 50

        if score > 0:
            candidates.append((col, score))

    if not candidates:
        return None

    # Return the highest scoring candidate
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


def _ensure_datetime(series: pd.Series) -> pd.Series:
    """Convert a series to datetime if not already."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    return pd.to_datetime(series, errors='coerce')


def analyze_trend(
    df: pd.DataFrame,
    value_col: str,
    date_col: str
) -> TrendAnalysis:
    """
    Analyze the trend of a numeric column over time.

    Fits a linear regression to determine trend direction and strength.

    Args:
        df: DataFrame containing the data
        value_col: Numeric column to analyze
        date_col: Date column to use as time axis

    Returns:
        TrendAnalysis with trend metrics
    """
    # Prepare data
    temp_df = df[[date_col, value_col]].copy()
    temp_df[date_col] = _ensure_datetime(temp_df[date_col])

    if not pd.api.types.is_numeric_dtype(temp_df[value_col]):
        temp_df[value_col] = safe_numeric_conversion(temp_df[value_col])

    # Drop missing values and sort by date
    temp_df = temp_df.dropna().sort_values(date_col)

    if len(temp_df) < 5:
        return TrendAnalysis(
            column=value_col,
            date_column=date_col,
            trend_direction='unknown',
            slope=0.0,
            r_squared=0.0,
        )

    # Convert dates to numeric (days since first date)
    first_date = temp_df[date_col].min()
    temp_df['_days'] = (temp_df[date_col] - first_date).dt.days

    # Perform linear regression
    x = temp_df['_days'].values
    y = temp_df[value_col].values

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    r_squared = r_value ** 2

    # Calculate growth rate
    first_value = y[0]
    last_value = y[-1]
    if first_value != 0:
        growth_rate_pct = ((last_value - first_value) / abs(first_value)) * 100
    else:
        growth_rate_pct = None

    # Determine trend direction
    # Consider both slope significance and coefficient of variation
    cv = np.std(y) / np.mean(y) if np.mean(y) != 0 else float('inf')

    if r_squared < 0.1 or p_value > 0.1:
        # Poor fit - check for volatility
        if cv > 0.5:
            trend_direction = 'volatile'
        else:
            trend_direction = 'stable'
    elif slope > 0:
        trend_direction = 'increasing'
    else:
        trend_direction = 'decreasing'

    # Check for seasonality
    seasonality_detected, seasonal_period = detect_seasonality(df, value_col, date_col)

    return TrendAnalysis(
        column=value_col,
        date_column=date_col,
        trend_direction=trend_direction,
        slope=float(slope),
        r_squared=float(r_squared),
        growth_rate_pct=float(growth_rate_pct) if growth_rate_pct is not None else None,
        seasonality_detected=seasonality_detected,
        seasonal_period=seasonal_period,
    )


def detect_seasonality(
    df: pd.DataFrame,
    value_col: str,
    date_col: str
) -> tuple:
    """
    Detect if there is seasonality in the data.

    Checks for weekly, monthly, and quarterly patterns using
    autocorrelation at relevant lags.

    Args:
        df: DataFrame containing the data
        value_col: Numeric column to analyze
        date_col: Date column to use as time axis

    Returns:
        Tuple of (is_seasonal: bool, period: Optional[str])
    """
    temp_df = df[[date_col, value_col]].copy()
    temp_df[date_col] = _ensure_datetime(temp_df[date_col])

    if not pd.api.types.is_numeric_dtype(temp_df[value_col]):
        temp_df[value_col] = safe_numeric_conversion(temp_df[value_col])

    temp_df = temp_df.dropna().sort_values(date_col)

    if len(temp_df) < 30:
        return (False, None)

    values = temp_df[value_col].values

    # Determine the time span
    date_range = temp_df[date_col].max() - temp_df[date_col].min()
    days = date_range.days

    # Check different seasonal periods based on data span
    periods_to_check = []

    if days >= 60:  # At least 2 months
        # Weekly patterns (7 days)
        periods_to_check.append(('weekly', 7))

    if days >= 180:  # At least 6 months
        # Monthly patterns (~30 days)
        periods_to_check.append(('monthly', 30))

    if days >= 365:  # At least 1 year
        # Quarterly patterns (~90 days)
        periods_to_check.append(('quarterly', 90))

    # Calculate autocorrelation at each lag
    best_period = None
    best_acf = 0.0

    for period_name, lag in periods_to_check:
        if lag >= len(values) // 2:
            continue

        # Calculate autocorrelation at this lag
        n = len(values)
        mean = np.mean(values)
        var = np.var(values)

        if var == 0:
            continue

        # Autocorrelation formula
        acf = np.correlate(values - mean, values - mean, mode='full')[n-1:n+lag]
        if len(acf) > lag:
            acf_at_lag = acf[lag] / (var * n)

            if acf_at_lag > 0.3 and acf_at_lag > best_acf:
                best_period = period_name
                best_acf = acf_at_lag

    return (best_period is not None, best_period)


def find_trend_insights(
    df: pd.DataFrame,
    date_col: str
) -> List[AnalysisFinding]:
    """
    Analyze trends for all numeric columns and generate insights.

    Args:
        df: DataFrame to analyze
        date_col: Date column to use as time axis

    Returns:
        List of AnalysisFinding objects with trend insights
    """
    findings = []
    numeric_cols = identify_numeric_columns(df)

    for col in numeric_cols:
        if col == date_col:
            continue

        trend = analyze_trend(df, col, date_col)

        # Skip unknown/insufficient data
        if trend.trend_direction == 'unknown':
            continue

        if trend.trend_direction in ('increasing', 'decreasing'):
            if trend.r_squared >= 0.5:
                # Strong trend
                importance = 'high'
                strength = "strong"
            elif trend.r_squared >= 0.25:
                importance = 'medium'
                strength = "moderate"
            else:
                importance = 'low'
                strength = "weak"

            direction = "upward" if trend.trend_direction == 'increasing' else "downward"
            growth_str = f" ({trend.growth_rate_pct:+.1f}%)" if trend.growth_rate_pct is not None else ""

            title = f"{strength.title()} {direction} trend in {col}"
            description = (
                f"'{col}' shows a {strength} {direction} trend over time{growth_str}. "
                f"The trend explains {trend.r_squared*100:.1f}% of the variation."
            )

            recommendation = None
            if importance == 'high' and trend.trend_direction == 'decreasing':
                recommendation = f"Investigate the cause of declining '{col}' values."
            elif importance == 'high' and trend.trend_direction == 'increasing':
                recommendation = f"Monitor if '{col}' growth is sustainable."

            findings.append(AnalysisFinding(
                category='trend',
                title=title,
                description=description,
                affected_columns=[col, date_col],
                importance=importance,
                confidence=min(0.95, 0.5 + trend.r_squared * 0.5),
                actionable=importance in ('high', 'medium'),
                recommendation=recommendation,
                supporting_data=trend.to_dict(),
            ))

        elif trend.trend_direction == 'volatile':
            # High volatility finding
            findings.append(AnalysisFinding(
                category='trend',
                title=f"High volatility in {col}",
                description=(
                    f"'{col}' shows high variability over time without a clear trend. "
                    f"This may indicate instability or seasonal fluctuations."
                ),
                affected_columns=[col, date_col],
                importance='medium',
                confidence=0.7,
                actionable=True,
                recommendation=(
                    f"Consider smoothing techniques or investigate "
                    f"what factors cause '{col}' volatility."
                ),
                supporting_data=trend.to_dict(),
            ))

        # Add seasonality findings
        if trend.seasonality_detected:
            findings.append(AnalysisFinding(
                category='trend',
                title=f"{trend.seasonal_period.title()} seasonality in {col}",
                description=(
                    f"'{col}' shows a {trend.seasonal_period} seasonal pattern. "
                    f"Values tend to repeat in {trend.seasonal_period} cycles."
                ),
                affected_columns=[col, date_col],
                importance='medium',
                confidence=0.7,
                actionable=True,
                recommendation=(
                    f"Account for {trend.seasonal_period} seasonality when "
                    f"forecasting or comparing '{col}' values across different periods."
                ),
                supporting_data={
                    'column': col,
                    'seasonal_period': trend.seasonal_period,
                },
            ))

    return findings
