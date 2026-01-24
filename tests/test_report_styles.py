"""Tests for report writing styles."""

import pytest
from src.reporting.styles import (
    WritingStyle,
    ReportConfig,
    get_style,
    get_available_styles,
    apply_style_to_finding,
    create_default_config,
    get_style_intro,
    get_style_methodology_text,
    TECHNICAL_STYLE,
    BUSINESS_STYLE,
    EXECUTIVE_STYLE,
)
from src.analysis import AnalysisFinding


class TestWritingStyle:
    """Tests for WritingStyle dataclass."""

    def test_technical_style_attributes(self):
        """Technical style has methodology and statistics enabled."""
        style = TECHNICAL_STYLE
        assert style.name == 'technical'
        assert style.include_methodology is True
        assert style.include_statistics is True
        assert style.include_confidence is True
        assert style.detail_level == 'high'

    def test_business_style_attributes(self):
        """Business style focuses on insights without methodology."""
        style = BUSINESS_STYLE
        assert style.name == 'business'
        assert style.include_methodology is False
        assert style.include_statistics is True
        assert style.include_confidence is False
        assert style.detail_level == 'medium'

    def test_executive_style_attributes(self):
        """Executive style is concise with limited findings."""
        style = EXECUTIVE_STYLE
        assert style.name == 'executive'
        assert style.include_methodology is False
        assert style.include_statistics is False
        assert style.max_findings == 5
        assert style.detail_level == 'low'

    def test_style_to_dict(self):
        """Style can be serialized to dictionary."""
        style = BUSINESS_STYLE
        result = style.to_dict()

        assert isinstance(result, dict)
        assert result['name'] == 'business'
        assert 'include_methodology' in result
        assert 'max_findings' in result


class TestGetStyle:
    """Tests for get_style function."""

    def test_get_technical_style(self):
        """Can retrieve technical style by name."""
        style = get_style('technical')
        assert style.name == 'technical'

    def test_get_business_style(self):
        """Can retrieve business style by name."""
        style = get_style('business')
        assert style.name == 'business'

    def test_get_executive_style(self):
        """Can retrieve executive style by name."""
        style = get_style('executive')
        assert style.name == 'executive'

    def test_get_style_case_insensitive(self):
        """Style lookup is case-insensitive."""
        style1 = get_style('TECHNICAL')
        style2 = get_style('Technical')
        style3 = get_style('technical')

        assert style1.name == style2.name == style3.name == 'technical'

    def test_get_invalid_style_raises(self):
        """Invalid style name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_style('invalid_style')

        assert 'Unknown style' in str(exc_info.value)
        assert 'technical' in str(exc_info.value)


class TestGetAvailableStyles:
    """Tests for get_available_styles function."""

    def test_returns_list_of_styles(self):
        """Returns a list of WritingStyle objects."""
        styles = get_available_styles()

        assert isinstance(styles, list)
        assert len(styles) >= 3
        assert all(isinstance(s, WritingStyle) for s in styles)

    def test_includes_all_styles(self):
        """All three main styles are included."""
        styles = get_available_styles()
        names = [s.name for s in styles]

        assert 'technical' in names
        assert 'business' in names
        assert 'executive' in names


class TestApplyStyleToFinding:
    """Tests for apply_style_to_finding function."""

    @pytest.fixture
    def sample_finding(self):
        """Create a sample finding for testing."""
        return AnalysisFinding(
            category='correlation',
            title='Strong correlation found',
            description='A very long description that exceeds the typical length limits. ' * 10,
            affected_columns=['col1', 'col2'],
            importance='high',
            confidence=0.85,
            actionable=True,
            recommendation='Consider investigating this correlation.',
            supporting_data={'coefficient': 0.92},
        )

    def test_technical_style_includes_confidence(self, sample_finding):
        """Technical style includes confidence information."""
        result = apply_style_to_finding(sample_finding, TECHNICAL_STYLE)

        assert 'confidence' in result
        assert result['confidence'] == 0.85
        assert 'confidence_display' in result

    def test_business_style_excludes_confidence(self, sample_finding):
        """Business style excludes confidence information."""
        result = apply_style_to_finding(sample_finding, BUSINESS_STYLE)

        assert 'confidence' not in result

    def test_technical_style_includes_supporting_data(self, sample_finding):
        """Technical style includes supporting data."""
        result = apply_style_to_finding(sample_finding, TECHNICAL_STYLE)

        assert 'supporting_data' in result
        assert result['supporting_data']['coefficient'] == 0.92

    def test_executive_style_truncates_description(self, sample_finding):
        """Executive style truncates long descriptions."""
        result = apply_style_to_finding(sample_finding, EXECUTIVE_STYLE)

        # Description should be shorter than original
        assert len(result['description']) < len(sample_finding.description)


class TestReportConfig:
    """Tests for ReportConfig dataclass."""

    def test_create_config(self):
        """Can create a ReportConfig."""
        config = ReportConfig(
            style=BUSINESS_STYLE,
            title='Test Report',
            include_visualizations=True,
            include_appendix=False,
        )

        assert config.title == 'Test Report'
        assert config.style.name == 'business'
        assert config.include_visualizations is True

    def test_config_to_dict(self):
        """Config can be serialized to dictionary."""
        config = ReportConfig(
            style=BUSINESS_STYLE,
            title='Test Report',
        )
        result = config.to_dict()

        assert isinstance(result, dict)
        assert result['title'] == 'Test Report'
        assert 'style' in result
        assert isinstance(result['style'], dict)


class TestCreateDefaultConfig:
    """Tests for create_default_config function."""

    def test_creates_config_with_style(self):
        """Creates a config with the specified style."""
        config = create_default_config('technical', 'My Report')

        assert config.style.name == 'technical'
        assert config.title == 'My Report'

    def test_technical_includes_appendix(self):
        """Technical config includes appendix by default."""
        config = create_default_config('technical', 'Test')

        assert config.include_appendix is True

    def test_business_excludes_appendix(self):
        """Business config excludes appendix by default."""
        config = create_default_config('business', 'Test')

        assert config.include_appendix is False


class TestStyleIntroText:
    """Tests for style-specific intro text."""

    def test_technical_intro(self):
        """Technical style has appropriate intro."""
        intro = get_style_intro(TECHNICAL_STYLE)

        assert 'comprehensive' in intro.lower() or 'statistical' in intro.lower()

    def test_business_intro(self):
        """Business style has appropriate intro."""
        intro = get_style_intro(BUSINESS_STYLE)

        assert 'insight' in intro.lower() or 'actionable' in intro.lower()

    def test_executive_intro(self):
        """Executive style has appropriate intro."""
        intro = get_style_intro(EXECUTIVE_STYLE)

        assert 'executive' in intro.lower() or 'strategic' in intro.lower()


class TestStyleMethodologyText:
    """Tests for style-specific methodology text."""

    def test_technical_has_methodology(self):
        """Technical style returns methodology text."""
        text = get_style_methodology_text(TECHNICAL_STYLE)

        assert text is not None
        assert 'Pearson' in text or 'correlation' in text.lower()

    def test_business_no_methodology(self):
        """Business style returns None for methodology."""
        text = get_style_methodology_text(BUSINESS_STYLE)

        assert text is None

    def test_executive_no_methodology(self):
        """Executive style returns None for methodology."""
        text = get_style_methodology_text(EXECUTIVE_STYLE)

        assert text is None
