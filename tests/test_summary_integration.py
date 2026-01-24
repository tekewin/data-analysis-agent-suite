"""Integration tests for executive summary generation pipeline."""

import pytest
from pathlib import Path
import json
from src.summarization import (
    # Loader
    SummaryInput,
    create_summary_input,
    auto_discover_inputs,
    find_latest_report,
    find_latest_analysis,
    # Extractor
    SummaryConfig,
    ExtractedData,
    extract_all,
    # Generator
    GeneratedSummary,
    generate_summary,
    save_summary,
    generate_summary_from_files,
    get_summary_stats,
)


class TestFullPipeline:
    """Tests for the complete summary generation pipeline."""

    def test_analysis_to_summary_pipeline(self, sample_analysis_json, temp_output_dir):
        """Test complete pipeline from analysis JSON to summary."""
        # Step 1: Load analysis
        input_data = create_summary_input(analysis_path=sample_analysis_json)
        assert input_data.has_analysis

        # Step 2: Extract data
        config = SummaryConfig(max_findings=3, max_actions=3)
        extracted = extract_all(input_data, config)
        assert len(extracted.bluf) > 0
        assert len(extracted.top_findings) > 0

        # Step 3: Generate summary
        summary = generate_summary(input_data, config)
        assert isinstance(summary, GeneratedSummary)
        assert len(summary.content) > 0

        # Step 4: Save summary
        filepath = save_summary(summary, temp_output_dir)
        assert Path(filepath).exists()

        # Step 5: Verify content
        with open(filepath, 'r') as f:
            content = f.read()

        assert 'Bottom Line Up Front' in content
        assert 'Top Findings' in content
        assert 'Recommended Actions' in content
        assert '@exec-summarizer' in content

    def test_report_to_summary_pipeline(self, sample_report_file, temp_output_dir):
        """Test complete pipeline from report markdown to summary."""
        # Step 1: Load report
        input_data = create_summary_input(report_path=sample_report_file)
        assert input_data.has_report

        # Step 2: Generate summary
        summary = generate_summary(input_data)
        assert isinstance(summary, GeneratedSummary)

        # Step 3: Save and verify
        filepath = save_summary(summary, temp_output_dir)
        assert Path(filepath).exists()

    def test_both_sources_pipeline(self, sample_analysis_json, sample_report_file, temp_output_dir):
        """Test pipeline with both analysis and report."""
        # Load both sources
        input_data = create_summary_input(
            analysis_path=sample_analysis_json,
            report_path=sample_report_file,
        )
        assert input_data.has_analysis
        assert input_data.has_report

        # Generate and save
        summary = generate_summary(input_data)
        filepath = save_summary(summary, temp_output_dir)

        # Verify output
        assert Path(filepath).exists()
        assert summary.finding_count > 0


class TestDiscoveryPipeline:
    """Tests for auto-discovery based pipeline."""

    def test_auto_discover_and_generate(self, sample_analysis_json, sample_report_file, temp_output_dir):
        """Test auto-discovery followed by generation."""
        # Copy files to have both in same directory
        analysis_dir = Path(sample_analysis_json).parent
        report_dest = analysis_dir / Path(sample_report_file).name
        report_dest.write_text(Path(sample_report_file).read_text())

        # Auto-discover
        input_data = auto_discover_inputs(str(analysis_dir))
        assert input_data is not None

        # Generate
        summary = generate_summary(input_data)
        assert summary is not None
        assert len(summary.content) > 0

    def test_convenience_function(self, sample_analysis_json, temp_output_dir):
        """Test generate_summary_from_files convenience function."""
        summary = generate_summary_from_files(
            analysis_path=sample_analysis_json,
            output_dir=temp_output_dir,
        )

        assert isinstance(summary, GeneratedSummary)
        assert Path(summary.filepath).exists()
        assert summary.finding_count > 0


class TestOutputFormat:
    """Tests for summary output format compliance."""

    def test_summary_structure(self, sample_summary_input, temp_output_dir):
        """Test summary has all required sections."""
        summary = generate_summary(sample_summary_input)
        content = summary.content

        required_sections = [
            '# Executive Summary',
            '## Bottom Line Up Front',
            '## Top Findings',
            '## Recommended Actions',
            '## Risks & Considerations',
        ]

        for section in required_sections:
            assert section in content, f"Missing section: {section}"

    def test_summary_has_header_metadata(self, sample_summary_input):
        """Test summary has header metadata."""
        summary = generate_summary(sample_summary_input)
        content = summary.content

        assert '**Date**:' in content
        assert '**Source**:' in content

    def test_summary_has_footer(self, sample_summary_input):
        """Test summary has proper footer."""
        summary = generate_summary(sample_summary_input)
        content = summary.content

        assert '@exec-summarizer' in content
        assert 'Full analysis' in content

    def test_findings_have_indicators(self, sample_summary_input):
        """Test findings have importance indicators."""
        summary = generate_summary(sample_summary_input)
        content = summary.content

        # Should have at least one importance indicator
        indicators = ['🔴', '🟡', '🟢']
        assert any(ind in content for ind in indicators)

    def test_findings_have_impact_and_action(self, sample_summary_input):
        """Test findings have impact and action fields."""
        summary = generate_summary(sample_summary_input)
        content = summary.content

        assert '**Impact**:' in content
        assert '**Action**:' in content


class TestConfigurationOptions:
    """Tests for configuration options."""

    def test_max_findings_config(self, sample_summary_input):
        """Test max_findings configuration is respected."""
        config_1 = SummaryConfig(max_findings=1)
        config_3 = SummaryConfig(max_findings=3)

        summary_1 = generate_summary(sample_summary_input, config_1)
        summary_3 = generate_summary(sample_summary_input, config_3)

        assert summary_1.finding_count == 1
        assert summary_3.finding_count == 3

    def test_max_actions_config(self, sample_summary_input):
        """Test max_actions configuration is respected."""
        config = SummaryConfig(max_actions=2)
        summary = generate_summary(sample_summary_input, config)

        assert summary.action_count <= 2

    def test_metrics_table_inclusion(self, sample_summary_input):
        """Test metrics table can be included/excluded."""
        config_with = SummaryConfig(include_metrics_table=True)
        config_without = SummaryConfig(include_metrics_table=False)

        summary_with = generate_summary(sample_summary_input, config_with)
        summary_without = generate_summary(sample_summary_input, config_without)

        assert '| Metric |' in summary_with.content
        # Without metrics table, should still have Key Metrics header but no table


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_analysis_result(self, sample_report_content):
        """Test handling of input with only report (no analysis)."""
        input_data = SummaryInput(
            source_file='test.csv',
            report_content=sample_report_content,
        )

        summary = generate_summary(input_data)
        assert summary is not None
        assert len(summary.content) > 0

    def test_minimal_findings(self, sample_analysis_result):
        """Test with minimal findings."""
        # Remove all but one finding
        sample_analysis_result.findings = sample_analysis_result.findings[:1]

        input_data = SummaryInput(
            source_file='test.csv',
            analysis_result=sample_analysis_result,
        )

        summary = generate_summary(input_data)
        assert summary.finding_count == 1

    def test_no_actionable_findings(self, sample_analysis_result):
        """Test with no actionable findings."""
        for finding in sample_analysis_result.findings:
            finding.actionable = False
            finding.recommendation = None

        input_data = SummaryInput(
            source_file='test.csv',
            analysis_result=sample_analysis_result,
        )

        summary = generate_summary(input_data)
        assert summary is not None  # Should still work

    def test_very_long_finding_description(self, sample_analysis_result):
        """Test handling of very long finding descriptions."""
        sample_analysis_result.findings[0].description = 'A' * 500

        input_data = SummaryInput(
            source_file='test.csv',
            analysis_result=sample_analysis_result,
        )

        summary = generate_summary(input_data)
        # Should truncate or handle gracefully
        assert summary is not None


class TestStatsOutput:
    """Tests for summary statistics output."""

    def test_stats_format(self, sample_summary_input, temp_output_dir):
        """Test stats output format."""
        summary = generate_summary(sample_summary_input)
        save_summary(summary, temp_output_dir)

        stats = get_summary_stats(summary)

        assert '✅' in stats
        assert 'Executive Summary Complete' in stats
        assert 'Output' in stats
        assert summary.filepath in stats

    def test_stats_includes_counts(self, sample_summary_input, temp_output_dir):
        """Test stats includes finding and action counts."""
        summary = generate_summary(sample_summary_input)
        save_summary(summary, temp_output_dir)

        stats = get_summary_stats(summary)

        # Should mention findings and recommendations
        assert 'finding' in stats.lower()
        assert 'recommendation' in stats.lower() or 'action' in stats.lower()


class TestFileSaving:
    """Tests for file saving functionality."""

    def test_unique_filenames(self, sample_summary_input, temp_output_dir):
        """Test that generated filenames are unique."""
        summary1 = generate_summary(sample_summary_input)
        filepath1 = save_summary(summary1, temp_output_dir)

        import time
        time.sleep(1)  # Ensure different timestamp

        summary2 = generate_summary(sample_summary_input)
        filepath2 = save_summary(summary2, temp_output_dir)

        assert filepath1 != filepath2
        assert Path(filepath1).exists()
        assert Path(filepath2).exists()

    def test_output_directory_creation(self, sample_summary_input, temp_output_dir):
        """Test output directory is created if needed."""
        new_dir = Path(temp_output_dir) / 'nested' / 'subdir'

        summary = generate_summary(sample_summary_input)
        filepath = save_summary(summary, str(new_dir))

        assert Path(filepath).exists()
        assert new_dir.exists()

    def test_file_encoding(self, sample_summary_input, temp_output_dir):
        """Test file is saved with UTF-8 encoding."""
        summary = generate_summary(sample_summary_input)
        filepath = save_summary(summary, temp_output_dir)

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should contain emoji indicators
        assert any(char in content for char in ['🟢', '🟡', '🔴', '⚪'])
