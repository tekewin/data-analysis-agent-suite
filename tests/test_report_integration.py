"""Integration tests for report generation pipeline."""

import pytest
import json
from pathlib import Path
from src.reporting import (
    # Loader
    create_report_input,
    load_analysis_result,
    load_visualization_manifest,
    ReportInput,
    # Styles
    get_style,
    get_available_styles,
    create_default_config,
    WritingStyle,
    ReportConfig,
    # Sections
    generate_all_sections,
    GeneratedSection,
    # Generator
    generate_report,
    save_report,
    GeneratedReport,
    compile_sections,
)


class TestFullPipeline:
    """Integration tests for the complete report generation pipeline."""

    def test_full_pipeline_business_style(self, sample_analysis_json, sample_visualization_manifest, temp_output_dir):
        """Complete pipeline: load -> configure -> generate -> save (business)."""
        # Step 1: Load inputs
        report_input = create_report_input(
            analysis_path=sample_analysis_json,
            viz_path=sample_visualization_manifest,
            audience='business',
        )

        assert isinstance(report_input, ReportInput)
        assert report_input.has_visualizations

        # Step 2: Configure
        config = create_default_config('business', 'Sales Analysis Report')

        assert isinstance(config, ReportConfig)
        assert config.style.name == 'business'

        # Step 3: Generate
        report = generate_report(report_input, config)

        assert isinstance(report, GeneratedReport)
        assert len(report.sections) >= 5
        assert report.total_findings == 3

        # Step 4: Save
        filepath = save_report(report, temp_output_dir)

        assert Path(filepath).exists()

        # Verify content
        content = Path(filepath).read_text()
        assert '# Sales Analysis Report' in content
        assert 'Executive Summary' in content
        assert 'Key Findings' in content

    def test_full_pipeline_technical_style(self, sample_analysis_json, temp_output_dir):
        """Complete pipeline with technical style."""
        report_input = create_report_input(
            analysis_path=sample_analysis_json,
            audience='technical',
        )

        report = generate_report(report_input)
        filepath = save_report(report, temp_output_dir)

        content = Path(filepath).read_text()

        # Technical should include methodology and appendix
        assert 'Methodology' in content
        assert 'Appendix' in content
        assert 'Confidence' in content

    def test_full_pipeline_executive_style(self, sample_analysis_json, temp_output_dir):
        """Complete pipeline with executive style."""
        report_input = create_report_input(
            analysis_path=sample_analysis_json,
            audience='executive',
        )

        report = generate_report(report_input)
        filepath = save_report(report, temp_output_dir)

        content = Path(filepath).read_text()

        # Executive should be concise
        assert 'Executive Summary' in content
        # Should NOT have detailed methodology
        assert content.count('Methodology Notes') == 0 or 'not included' in content.lower()


class TestStyleDifferences:
    """Tests verifying differences between writing styles."""

    def test_technical_longer_than_executive(self, sample_report_input):
        """Technical reports are longer than executive reports."""
        tech_report = generate_report(sample_report_input, style_name='technical')
        exec_report = generate_report(sample_report_input, style_name='executive')

        tech_content = tech_report.to_markdown()
        exec_content = exec_report.to_markdown()

        assert len(tech_content) > len(exec_content)

    def test_technical_has_more_sections(self, sample_report_input):
        """Technical reports have more sections."""
        tech_report = generate_report(sample_report_input, style_name='technical')
        exec_report = generate_report(sample_report_input, style_name='executive')

        assert len(tech_report.sections) >= len(exec_report.sections)

    def test_styles_have_different_content(self, sample_report_input):
        """Different styles produce different content."""
        tech_content = generate_report(sample_report_input, style_name='technical').to_markdown()
        bus_content = generate_report(sample_report_input, style_name='business').to_markdown()
        exec_content = generate_report(sample_report_input, style_name='executive').to_markdown()

        # All should be different
        assert tech_content != bus_content
        assert bus_content != exec_content
        assert tech_content != exec_content


class TestNoVisualizationsPipeline:
    """Tests for pipeline when visualizations are not available."""

    def test_pipeline_without_visualizations(self, sample_analysis_json, temp_output_dir):
        """Can generate report without visualization manifest."""
        report_input = create_report_input(
            analysis_path=sample_analysis_json,
            viz_path=None,  # No visualizations
        )

        assert not report_input.has_visualizations

        report = generate_report(report_input)
        filepath = save_report(report, temp_output_dir)

        content = Path(filepath).read_text()

        # Should still generate valid report
        assert 'Executive Summary' in content
        assert 'Key Findings' in content
        # No visualization section should be present (or minimal reference)
        # Since there are no visualizations, the section won't be included
        # or will have minimal content
        assert report.total_charts == 0


class TestReportContent:
    """Tests for report content quality."""

    def test_findings_in_report(self, sample_report_input, temp_output_dir):
        """Report includes findings from analysis."""
        report = generate_report(sample_report_input)
        content = report.to_markdown()

        # Should include finding titles
        assert 'correlation' in content.lower()
        assert 'trend' in content.lower()

    def test_importance_indicators_present(self, sample_report_input):
        """Report includes importance indicators."""
        report = generate_report(sample_report_input)
        content = report.to_markdown()

        # Should have emoji indicators
        assert '🔴' in content or '🟡' in content or '🟢' in content

    def test_statistics_in_technical(self, sample_report_input):
        """Technical report includes detailed statistics."""
        report = generate_report(sample_report_input, style_name='technical')
        content = report.to_markdown()

        # Should have stats tables
        assert 'Mean' in content or 'mean' in content
        assert 'Count' in content or 'count' in content

    def test_recommendations_present(self, sample_report_input):
        """Report includes recommendations."""
        report = generate_report(sample_report_input)
        content = report.to_markdown()

        assert 'Recommendations' in content


class TestMultipleReports:
    """Tests for generating multiple reports."""

    def test_generate_all_styles(self, sample_report_input, temp_output_dir):
        """Can generate reports in all three styles."""
        styles = ['technical', 'business', 'executive']
        reports = []

        for style in styles:
            report = generate_report(sample_report_input, style_name=style)
            # Store the markdown content directly (avoids timestamp collision)
            reports.append((style, report.to_markdown()))

        # All reports should have content
        assert len(reports) == 3
        assert all(content for _, content in reports)

        # All reports should be different (compare markdown content)
        contents = [content for _, content in reports]
        # At minimum, the Style: line should differ (markdown formatted)
        assert '**Style:** Technical' in contents[0]
        assert '**Style:** Business' in contents[1]
        assert '**Style:** Executive' in contents[2]

    def test_reports_are_unique(self, sample_report_input, temp_output_dir):
        """Each report generation creates a unique file."""
        import time

        report1 = generate_report(sample_report_input)
        filepath1 = save_report(report1, temp_output_dir)

        time.sleep(1)  # Ensure different timestamp

        report2 = generate_report(sample_report_input)
        filepath2 = save_report(report2, temp_output_dir)

        # Filenames should be different (timestamped)
        assert filepath1 != filepath2


class TestErrorHandling:
    """Tests for error handling in the pipeline."""

    def test_invalid_analysis_file(self, temp_output_dir):
        """Handles missing analysis file gracefully."""
        with pytest.raises(FileNotFoundError):
            create_report_input(
                analysis_path=f"{temp_output_dir}/nonexistent.json",
            )

    def test_invalid_style_name(self, sample_report_input):
        """Handles invalid style name."""
        with pytest.raises(ValueError):
            generate_report(sample_report_input, style_name='invalid_style')

    def test_empty_findings_report(self, temp_output_dir):
        """Can generate report with no findings."""
        from src.analysis import AnalysisResult

        # Create minimal analysis result with no findings
        empty_result = AnalysisResult(
            findings=[],
            descriptive_stats={},
            correlations=[],
            trends=[],
            segments=[],
            depth_level='quick_scan',
            columns_analyzed=5,
            rows_analyzed=100,
        )

        report_input = ReportInput(
            source_file='empty.csv',
            analysis_result=empty_result,
        )

        # Should still generate valid report
        report = generate_report(report_input)
        content = report.to_markdown()

        assert 'Executive Summary' in content
        # Should indicate no findings
        assert 'no' in content.lower() or '0' in content


class TestModuleImports:
    """Tests for module imports and exports."""

    def test_all_exports_available(self):
        """All exported symbols are importable."""
        from src.reporting import (
            # Utils
            format_importance_indicator,
            format_confidence_level,
            format_number,
            format_percentage,
            # Styles
            WritingStyle,
            ReportConfig,
            get_style,
            get_available_styles,
            # Loader
            ReportInput,
            load_analysis_result,
            create_report_input,
            # Sections
            GeneratedSection,
            generate_executive_summary,
            generate_key_findings,
            # Generator
            GeneratedReport,
            generate_report,
            save_report,
        )

        # All should be importable without error
        assert callable(format_importance_indicator)
        assert callable(generate_report)

    def test_styles_registry(self):
        """Style registry contains all expected styles."""
        styles = get_available_styles()
        names = [s.name for s in styles]

        assert 'technical' in names
        assert 'business' in names
        assert 'executive' in names
