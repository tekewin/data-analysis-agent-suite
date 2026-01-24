"""Tests for report section generators."""

import pytest
from src.reporting.sections import (
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
from src.reporting.styles import (
    get_style,
    create_default_config,
    TECHNICAL_STYLE,
    BUSINESS_STYLE,
    EXECUTIVE_STYLE,
)


class TestGeneratedSection:
    """Tests for GeneratedSection dataclass."""

    def test_to_markdown(self):
        """Can convert section to markdown."""
        section = GeneratedSection(
            title='Test Section',
            content='This is the content.',
            level=2,
        )

        result = section.to_markdown()

        assert '## Test Section' in result
        assert 'This is the content.' in result

    def test_to_markdown_level_3(self):
        """Respects header level."""
        section = GeneratedSection(
            title='Subsection',
            content='Content here.',
            level=3,
        )

        result = section.to_markdown()

        assert '### Subsection' in result

    def test_to_dict(self):
        """Can serialize to dictionary."""
        section = GeneratedSection(
            title='Test',
            content='Content',
            level=2,
            section_id='test-section',
        )

        result = section.to_dict()

        assert result['title'] == 'Test'
        assert result['level'] == 2
        assert result['section_id'] == 'test-section'


class TestGenerateExecutiveSummary:
    """Tests for generate_executive_summary function."""

    def test_includes_finding_count(self, sample_report_input):
        """Executive summary includes finding count."""
        config = create_default_config('business', 'Test Report')

        result = generate_executive_summary(sample_report_input, config)

        assert isinstance(result, GeneratedSection)
        assert 'Executive Summary' in result.title
        assert '3' in result.content or 'findings' in result.content.lower()

    def test_includes_data_summary(self, sample_report_input):
        """Executive summary includes data summary."""
        config = create_default_config('business', 'Test Report')

        result = generate_executive_summary(sample_report_input, config)

        assert '1,000' in result.content or '1000' in result.content

    def test_highlights_high_importance(self, sample_report_input):
        """Executive summary highlights high importance findings."""
        config = create_default_config('business', 'Test Report')

        result = generate_executive_summary(sample_report_input, config)

        # Should mention critical/high findings
        assert 'high' in result.content.lower() or 'critical' in result.content.lower() or '🔴' in result.content


class TestGenerateIntroduction:
    """Tests for generate_introduction function."""

    def test_includes_objective(self, sample_report_input):
        """Introduction includes objective section."""
        config = create_default_config('business', 'Test Report')

        result = generate_introduction(sample_report_input, config)

        assert '1.1 Objective' in result.content

    def test_includes_data_source(self, sample_report_input):
        """Introduction includes data source section."""
        config = create_default_config('business', 'Test Report')

        result = generate_introduction(sample_report_input, config)

        assert '1.2 Data Source' in result.content
        assert 'test_data.csv' in result.content

    def test_technical_includes_methodology(self, sample_report_input):
        """Technical style includes methodology section."""
        config = create_default_config('technical', 'Test Report')

        result = generate_introduction(sample_report_input, config)

        assert '1.3 Methodology' in result.content

    def test_business_excludes_methodology(self, sample_report_input):
        """Business style excludes methodology section."""
        config = create_default_config('business', 'Test Report')

        result = generate_introduction(sample_report_input, config)

        assert 'Methodology' not in result.content


class TestGenerateDataOverview:
    """Tests for generate_data_overview function."""

    def test_includes_dataset_description(self, sample_report_input):
        """Data overview includes dataset description."""
        config = create_default_config('business', 'Test Report')

        result = generate_data_overview(sample_report_input, config)

        assert '2.1 Dataset Description' in result.content

    def test_includes_record_count(self, sample_report_input):
        """Data overview includes record count."""
        config = create_default_config('business', 'Test Report')

        result = generate_data_overview(sample_report_input, config)

        assert '1,000' in result.content or '1000' in result.content


class TestGenerateKeyFindings:
    """Tests for generate_key_findings function."""

    def test_includes_all_findings(self, sample_report_input):
        """Key findings section includes findings."""
        config = create_default_config('business', 'Test Report')

        result = generate_key_findings(sample_report_input, config)

        assert '3. Key Findings' in result.title
        # Should include at least some findings
        assert 'correlation' in result.content.lower() or 'trend' in result.content.lower()

    def test_shows_importance_indicators(self, sample_report_input):
        """Findings show importance indicators."""
        config = create_default_config('business', 'Test Report')

        result = generate_key_findings(sample_report_input, config)

        # Should have importance indicators
        assert '🔴' in result.content or '🟡' in result.content or '🟢' in result.content

    def test_technical_shows_confidence(self, sample_report_input):
        """Technical style shows confidence levels."""
        config = create_default_config('technical', 'Test Report')

        result = generate_key_findings(sample_report_input, config)

        assert 'Confidence' in result.content

    def test_executive_limits_findings(self, sample_report_input):
        """Executive style limits number of findings."""
        config = create_default_config('executive', 'Test Report')

        result = generate_key_findings(sample_report_input, config)

        # Executive should have fewer detailed findings
        section_count = result.content.count('### ')
        assert section_count <= 5


class TestGenerateDetailedAnalysis:
    """Tests for generate_detailed_analysis function."""

    def test_includes_correlations(self, sample_report_input):
        """Detailed analysis includes correlations."""
        config = create_default_config('business', 'Test Report')

        result = generate_detailed_analysis(sample_report_input, config)

        assert '4.1 Correlations' in result.content

    def test_includes_trends(self, sample_report_input):
        """Detailed analysis includes trends."""
        config = create_default_config('business', 'Test Report')

        result = generate_detailed_analysis(sample_report_input, config)

        assert '4.2 Trends' in result.content

    def test_executive_skips_details(self, sample_report_input):
        """Executive style skips detailed analysis."""
        config = create_default_config('executive', 'Test Report')

        result = generate_detailed_analysis(sample_report_input, config)

        # Should have minimal content
        assert 'technical report' in result.content.lower() or len(result.content) < 500


class TestGenerateVisualizationsSection:
    """Tests for generate_visualizations_section function."""

    def test_includes_chart_list(self, sample_report_input):
        """Visualizations section includes chart list."""
        config = create_default_config('business', 'Test Report')

        result = generate_visualizations_section(sample_report_input, config)

        assert 'Visualizations' in result.title
        assert 'Sales Over Time' in result.content or 'line' in result.content.lower()

    def test_includes_chart_count(self, sample_report_input):
        """Visualizations section shows chart count."""
        config = create_default_config('business', 'Test Report')

        result = generate_visualizations_section(sample_report_input, config)

        assert '3' in result.content

    def test_no_viz_shows_message(self, sample_analysis_result):
        """Shows message when no visualizations."""
        from src.reporting import ReportInput

        report_input = ReportInput(
            source_file='test.csv',
            analysis_result=sample_analysis_result,
            visualization_manifest=None,
        )
        config = create_default_config('business', 'Test Report')
        config.include_visualizations = False

        result = generate_visualizations_section(report_input, config)

        assert 'not included' in result.content.lower() or 'no visualization' in result.content.lower()


class TestGenerateRecommendations:
    """Tests for generate_recommendations function."""

    def test_includes_immediate_actions(self, sample_report_input):
        """Recommendations includes immediate actions for high-importance."""
        config = create_default_config('business', 'Test Report')

        result = generate_recommendations(sample_report_input, config)

        assert 'Recommendations' in result.title
        # Should have some recommendations
        assert 'Action' in result.content or 'Investigate' in result.content or 'Investigation' in result.content

    def test_extracts_from_findings(self, sample_report_input):
        """Recommendations are extracted from findings."""
        config = create_default_config('business', 'Test Report')

        result = generate_recommendations(sample_report_input, config)

        # Should reference finding content
        assert 'revenue' in result.content.lower() or 'sales' in result.content.lower() or 'correlation' in result.content.lower()


class TestGenerateAppendix:
    """Tests for generate_appendix function."""

    def test_technical_includes_appendix(self, sample_report_input):
        """Technical style includes full appendix."""
        config = create_default_config('technical', 'Test Report')

        result = generate_appendix(sample_report_input, config)

        assert '7.1 Data Dictionary' in result.content
        assert '7.2 Methodology' in result.content
        assert '7.3 Limitations' in result.content

    def test_business_excludes_appendix(self, sample_report_input):
        """Business style excludes appendix."""
        config = create_default_config('business', 'Test Report')

        result = generate_appendix(sample_report_input, config)

        assert 'not included' in result.content.lower()


class TestGenerateAllSections:
    """Tests for generate_all_sections function."""

    def test_returns_all_sections(self, sample_report_input):
        """Returns a list of all sections."""
        config = create_default_config('business', 'Test Report')

        result = generate_all_sections(sample_report_input, config)

        assert isinstance(result, list)
        assert len(result) >= 5  # At least core sections

    def test_sections_in_order(self, sample_report_input):
        """Sections are in correct order."""
        config = create_default_config('business', 'Test Report')

        result = generate_all_sections(sample_report_input, config)

        # First should be executive summary
        assert 'Executive' in result[0].title
        # Should have introduction early
        assert any('Introduction' in s.title for s in result[:3])

    def test_technical_has_more_sections(self, sample_report_input):
        """Technical style has more sections than executive."""
        tech_config = create_default_config('technical', 'Test Report')
        exec_config = create_default_config('executive', 'Test Report')

        tech_result = generate_all_sections(sample_report_input, tech_config)
        exec_result = generate_all_sections(sample_report_input, exec_config)

        # Technical should have appendix, executive should not
        assert len(tech_result) >= len(exec_result)
