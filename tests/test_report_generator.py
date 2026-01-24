"""Tests for report generation orchestration."""

import pytest
from pathlib import Path
from src.reporting.generator import (
    GeneratedReport,
    generate_report,
    generate_report_from_files,
    compile_sections,
    save_report,
    get_report_summary,
    generate_technical_report,
    generate_business_report,
    generate_executive_report,
)
from src.reporting.sections import GeneratedSection
from src.reporting.styles import create_default_config


class TestGeneratedReport:
    """Tests for GeneratedReport dataclass."""

    def test_to_dict(self, sample_report_input):
        """Can serialize report to dictionary."""
        config = create_default_config('business', 'Test Report')
        report = generate_report(sample_report_input, config)

        result = report.to_dict()

        assert isinstance(result, dict)
        assert result['title'] == 'Test Report'
        assert 'sections' in result
        assert result['style'] == 'business'

    def test_to_markdown(self, sample_report_input):
        """Can compile report to markdown."""
        config = create_default_config('business', 'Test Report')
        report = generate_report(sample_report_input, config)

        result = report.to_markdown()

        assert isinstance(result, str)
        assert '# Test Report' in result
        assert 'Executive Summary' in result


class TestGenerateReport:
    """Tests for generate_report function."""

    def test_generates_business_report(self, sample_report_input):
        """Can generate a business-style report."""
        report = generate_report(sample_report_input, style_name='business')

        assert isinstance(report, GeneratedReport)
        assert report.style == 'business'
        assert len(report.sections) >= 5

    def test_generates_technical_report(self, sample_report_input):
        """Can generate a technical-style report."""
        report = generate_report(sample_report_input, style_name='technical')

        assert report.style == 'technical'
        # Technical has more sections (appendix)
        assert len(report.sections) >= 6

    def test_generates_executive_report(self, sample_report_input):
        """Can generate an executive-style report."""
        report = generate_report(sample_report_input, style_name='executive')

        assert report.style == 'executive'

    def test_uses_audience_as_default_style(self, sample_report_input):
        """Uses report_input.audience as default style."""
        sample_report_input.audience = 'technical'

        report = generate_report(sample_report_input)

        assert report.style == 'technical'

    def test_includes_finding_count(self, sample_report_input):
        """Report includes total finding count."""
        report = generate_report(sample_report_input)

        assert report.total_findings == 3

    def test_includes_chart_count(self, sample_report_input):
        """Report includes chart count."""
        report = generate_report(sample_report_input)

        assert report.total_charts == 3

    def test_sets_generated_at(self, sample_report_input):
        """Report has generated_at timestamp."""
        report = generate_report(sample_report_input)

        assert report.generated_at is not None
        assert len(report.generated_at) > 0


class TestGenerateReportFromFiles:
    """Tests for generate_report_from_files function."""

    def test_generates_from_file_paths(self, sample_analysis_json, sample_visualization_manifest, temp_output_dir):
        """Can generate report directly from file paths."""
        report = generate_report_from_files(
            analysis_path=sample_analysis_json,
            viz_path=sample_visualization_manifest,
            style_name='business',
            output_dir=temp_output_dir,
        )

        assert isinstance(report, GeneratedReport)
        assert report.filepath != ''
        assert Path(report.filepath).exists()

    def test_generates_without_viz(self, sample_analysis_json, temp_output_dir):
        """Can generate report without visualizations."""
        report = generate_report_from_files(
            analysis_path=sample_analysis_json,
            style_name='business',
            output_dir=temp_output_dir,
        )

        assert report.total_charts == 0


class TestCompileSections:
    """Tests for compile_sections function."""

    def test_compiles_to_markdown(self):
        """Compiles sections into markdown document."""
        sections = [
            GeneratedSection(title='Summary', content='Summary content.', level=2),
            GeneratedSection(title='Details', content='Detail content.', level=2),
        ]

        result = compile_sections(sections, 'Test Report', 'test.csv', 'business')

        assert '# Test Report' in result
        assert '## Summary' in result
        assert '## Details' in result
        assert 'test.csv' in result

    def test_includes_metadata(self):
        """Compiled report includes metadata."""
        sections = [GeneratedSection(title='Test', content='Content', level=2)]

        result = compile_sections(sections, 'Report', 'data.csv', 'technical')

        assert 'Generated:' in result
        assert 'Source:' in result
        assert 'Style:' in result

    def test_includes_footer(self):
        """Compiled report includes footer."""
        sections = [GeneratedSection(title='Test', content='Content', level=2)]

        result = compile_sections(sections, 'Report', 'data.csv', 'business')

        assert '@report-writer' in result


class TestSaveReport:
    """Tests for save_report function."""

    def test_saves_to_file(self, sample_report_input, temp_output_dir):
        """Can save report to file."""
        report = generate_report(sample_report_input)

        filepath = save_report(report, temp_output_dir)

        assert Path(filepath).exists()
        assert filepath.endswith('.md')

    def test_creates_timestamped_filename(self, sample_report_input, temp_output_dir):
        """Filename includes timestamp."""
        report = generate_report(sample_report_input)

        filepath = save_report(report, temp_output_dir)
        filename = Path(filepath).name

        # Should have format: {source}_report_{timestamp}.md
        assert 'report' in filename
        assert filename.endswith('.md')

    def test_updates_report_filepath(self, sample_report_input, temp_output_dir):
        """Updates report.filepath after saving."""
        report = generate_report(sample_report_input)
        assert report.filepath == ''

        filepath = save_report(report, temp_output_dir)

        assert report.filepath == filepath

    def test_creates_output_dir_if_needed(self, sample_report_input, temp_output_dir):
        """Creates output directory if it doesn't exist."""
        new_dir = Path(temp_output_dir) / 'new_subdir'
        report = generate_report(sample_report_input)

        filepath = save_report(report, str(new_dir))

        assert Path(filepath).exists()


class TestGetReportSummary:
    """Tests for get_report_summary function."""

    def test_returns_summary_string(self, sample_report_input, temp_output_dir):
        """Returns a human-readable summary."""
        report = generate_report(sample_report_input)
        report.filepath = f"{temp_output_dir}/test_report.md"

        result = get_report_summary(report)

        assert isinstance(result, str)
        assert 'Report Generated' in result

    def test_includes_key_info(self, sample_report_input, temp_output_dir):
        """Summary includes key information."""
        report = generate_report(sample_report_input)
        report.filepath = f"{temp_output_dir}/test_report.md"

        result = get_report_summary(report)

        assert 'Title' in result or report.title in result
        assert 'Style' in result or report.style in result


class TestQuickGenerators:
    """Tests for quick generation helper functions."""

    def test_generate_technical_report(self, sample_report_input):
        """Can use technical report shortcut."""
        report = generate_technical_report(sample_report_input)

        assert report.style == 'technical'

    def test_generate_business_report(self, sample_report_input):
        """Can use business report shortcut."""
        report = generate_business_report(sample_report_input)

        assert report.style == 'business'

    def test_generate_executive_report(self, sample_report_input):
        """Can use executive report shortcut."""
        report = generate_executive_report(sample_report_input)

        assert report.style == 'executive'

    def test_shortcut_with_output_dir(self, sample_report_input, temp_output_dir):
        """Shortcuts can save to output directory."""
        report = generate_business_report(sample_report_input, temp_output_dir)

        assert Path(report.filepath).exists()
