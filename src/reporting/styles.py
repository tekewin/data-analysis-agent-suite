"""Writing style configurations for report generation.

This module defines the three report writing styles (technical, business,
executive) and provides functions to apply style-specific transformations.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from src.analysis import AnalysisFinding


# =============================================================================
# STYLE DATACLASSES
# =============================================================================

@dataclass
class WritingStyle:
    """Configuration for a writing style."""

    name: str  # 'technical', 'business', 'executive'
    display_name: str  # Human-readable name
    description: str  # Description of the style
    tone: str  # 'formal', 'conversational', 'concise'

    # Content inclusion settings
    include_methodology: bool  # Include methodology details
    include_statistics: bool  # Include detailed statistics
    include_confidence: bool  # Include confidence scores
    include_supporting_data: bool  # Include raw supporting data

    # Finding limits
    max_findings: int  # Maximum findings to include
    max_recommendations: int  # Maximum recommendations

    # Focus areas
    recommendation_focus: str  # 'analysis', 'action', 'strategy'
    detail_level: str  # 'high', 'medium', 'low'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'tone': self.tone,
            'include_methodology': self.include_methodology,
            'include_statistics': self.include_statistics,
            'include_confidence': self.include_confidence,
            'include_supporting_data': self.include_supporting_data,
            'max_findings': self.max_findings,
            'max_recommendations': self.max_recommendations,
            'recommendation_focus': self.recommendation_focus,
            'detail_level': self.detail_level,
        }


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    style: WritingStyle
    title: str
    include_visualizations: bool = True
    include_appendix: bool = True
    max_detailed_findings: int = 10
    custom_sections: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'style': self.style.to_dict(),
            'title': self.title,
            'include_visualizations': self.include_visualizations,
            'include_appendix': self.include_appendix,
            'max_detailed_findings': self.max_detailed_findings,
            'custom_sections': self.custom_sections,
        }


# =============================================================================
# PREDEFINED STYLES
# =============================================================================

TECHNICAL_STYLE = WritingStyle(
    name='technical',
    display_name='Technical Report',
    description='Detailed, methodology-focused report for data teams and analysts',
    tone='formal',
    include_methodology=True,
    include_statistics=True,
    include_confidence=True,
    include_supporting_data=True,
    max_findings=20,
    max_recommendations=10,
    recommendation_focus='analysis',
    detail_level='high',
)

BUSINESS_STYLE = WritingStyle(
    name='business',
    display_name='Business Report',
    description='Insight-focused, actionable report for business stakeholders',
    tone='conversational',
    include_methodology=False,
    include_statistics=True,
    include_confidence=False,
    include_supporting_data=False,
    max_findings=12,
    max_recommendations=6,
    recommendation_focus='action',
    detail_level='medium',
)

EXECUTIVE_STYLE = WritingStyle(
    name='executive',
    display_name='Executive Summary',
    description='High-level, strategic report for leadership and decision-makers',
    tone='concise',
    include_methodology=False,
    include_statistics=False,
    include_confidence=False,
    include_supporting_data=False,
    max_findings=5,
    max_recommendations=3,
    recommendation_focus='strategy',
    detail_level='low',
)

# Style registry
_STYLES: Dict[str, WritingStyle] = {
    'technical': TECHNICAL_STYLE,
    'business': BUSINESS_STYLE,
    'executive': EXECUTIVE_STYLE,
}


# =============================================================================
# STYLE FUNCTIONS
# =============================================================================

def get_style(name: str) -> WritingStyle:
    """
    Get a writing style by name.

    Args:
        name: Style name ('technical', 'business', or 'executive')

    Returns:
        WritingStyle object

    Raises:
        ValueError: If style name is not recognized
    """
    name_lower = name.lower()
    if name_lower not in _STYLES:
        available = ', '.join(_STYLES.keys())
        raise ValueError(f"Unknown style '{name}'. Available: {available}")

    return _STYLES[name_lower]


def get_available_styles() -> List[WritingStyle]:
    """
    Get all available writing styles.

    Returns:
        List of WritingStyle objects
    """
    return list(_STYLES.values())


def apply_style_to_finding(
    finding: 'AnalysisFinding',
    style: WritingStyle,
) -> Dict[str, Any]:
    """
    Apply a writing style to transform a finding for display.

    Adjusts the finding's presentation based on the style's settings.

    Args:
        finding: AnalysisFinding to transform
        style: WritingStyle to apply

    Returns:
        Dictionary with styled finding data
    """
    result = {
        'title': finding.title,
        'description': finding.description,
        'importance': finding.importance,
        'category': finding.category,
        'columns': finding.affected_columns,
    }

    # Include confidence only for technical style
    if style.include_confidence:
        result['confidence'] = finding.confidence
        result['confidence_display'] = _format_confidence(finding.confidence)

    # Include recommendation based on style focus
    if finding.recommendation:
        result['recommendation'] = _transform_recommendation(
            finding.recommendation,
            style.recommendation_focus,
        )

    # Include supporting data only for technical style
    if style.include_supporting_data and finding.supporting_data:
        result['supporting_data'] = finding.supporting_data

    # Adjust description verbosity based on detail level
    if style.detail_level == 'low' and len(finding.description) > 150:
        result['description'] = _summarize_description(finding.description)
    elif style.detail_level == 'medium' and len(finding.description) > 300:
        result['description'] = finding.description[:297] + "..."

    return result


def get_style_intro(style: WritingStyle) -> str:
    """
    Get an introductory paragraph appropriate for the style.

    Args:
        style: WritingStyle to get intro for

    Returns:
        Introduction paragraph text
    """
    intros = {
        'technical': (
            "This technical report presents a comprehensive statistical analysis "
            "of the dataset, including methodology details, confidence intervals, "
            "and supporting data for all findings."
        ),
        'business': (
            "This report summarizes the key insights discovered during data analysis, "
            "focusing on actionable findings and practical recommendations for "
            "business decision-making."
        ),
        'executive': (
            "This executive summary highlights the most critical findings and "
            "strategic implications from the data analysis, designed to support "
            "informed leadership decisions."
        ),
    }
    return intros.get(style.name, intros['business'])


def get_style_methodology_text(style: WritingStyle) -> Optional[str]:
    """
    Get methodology explanation text if appropriate for the style.

    Args:
        style: WritingStyle to check

    Returns:
        Methodology text or None if not included
    """
    if not style.include_methodology:
        return None

    return (
        "The analysis employed multiple statistical techniques including:\n"
        "- **Descriptive Statistics**: Mean, median, standard deviation, "
        "skewness, and kurtosis for all numeric columns\n"
        "- **Correlation Analysis**: Pearson correlation coefficients with "
        "significance testing (p < 0.05)\n"
        "- **Trend Detection**: Linear regression with R-squared values "
        "and seasonal pattern detection\n"
        "- **Segmentation Analysis**: ANOVA F-tests for categorical comparisons "
        "with effect size (eta-squared) calculations"
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _format_confidence(confidence: float) -> str:
    """Format confidence as descriptive text."""
    if confidence >= 0.9:
        return "Very High"
    elif confidence >= 0.75:
        return "High"
    elif confidence >= 0.5:
        return "Moderate"
    elif confidence >= 0.25:
        return "Low"
    else:
        return "Very Low"


def _transform_recommendation(
    recommendation: str,
    focus: str,
) -> str:
    """
    Transform a recommendation based on focus area.

    Args:
        recommendation: Original recommendation text
        focus: 'analysis', 'action', or 'strategy'

    Returns:
        Transformed recommendation
    """
    if focus == 'strategy':
        # For executive style, make it more strategic
        # Remove specific technical details
        recommendation = recommendation.replace("Consider ", "Strategic priority: ")
        recommendation = recommendation.replace("Investigate ", "Review ")
    elif focus == 'action':
        # For business style, make it more action-oriented
        if not recommendation.startswith(("Consider", "Review", "Investigate", "Monitor")):
            recommendation = "Action: " + recommendation

    return recommendation


def _summarize_description(description: str, max_length: int = 120) -> str:
    """
    Summarize a long description to fit max length.

    Args:
        description: Original description
        max_length: Maximum length

    Returns:
        Summarized description
    """
    if len(description) <= max_length:
        return description

    # Try to cut at a sentence boundary
    truncated = description[:max_length]
    last_period = truncated.rfind('.')
    last_comma = truncated.rfind(',')

    if last_period > max_length * 0.6:
        return truncated[:last_period + 1]
    elif last_comma > max_length * 0.6:
        return truncated[:last_comma] + "..."
    else:
        return truncated[:max_length - 3] + "..."


def create_default_config(
    style_name: str,
    title: str,
    include_visualizations: bool = True,
) -> ReportConfig:
    """
    Create a default report configuration for a style.

    Args:
        style_name: Name of the writing style
        title: Report title
        include_visualizations: Whether to include visualization section

    Returns:
        ReportConfig object
    """
    style = get_style(style_name)

    return ReportConfig(
        style=style,
        title=title,
        include_visualizations=include_visualizations,
        include_appendix=style.include_methodology,  # Only technical gets appendix
        max_detailed_findings=style.max_findings,
    )
