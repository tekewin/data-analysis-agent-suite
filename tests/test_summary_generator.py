"""Tests for executive summary generation utilities."""

import pytest
from pathlib import Path
from src.summarization.generator import (
    GeneratedSummary,
    generate_summary,
    compile_summary,
    save_summary,
    generate_summary_from_files,
    get_summary_stats,
    ensure_output_dir,
    generate_summary_filename,
)
from src.summarization import SummaryConfig, SummaryInput


class TestGeneratedSummary:
    """Tests for GeneratedSummary dataclass."""

    def test_create_summary(self):
        """Test creating a GeneratedSummary."""
        summary = GeneratedSummary(
            title='Test Summary',
            content='# Test\nContent here.',
            source_file='test.csv',
            generated_at='2024-01-24T15:00:00',
            finding_count=3,
            action_count=3,
        )
        assert summary.title == 'Test Summary'
        assert summary.finding_count == 3

    def test_summary_to_dict(self):
        """Test converting summary to dictionary."""
        summary = GeneratedSummary(
            title='Test',
            content='Content',
            source_file='test.csv',
            generated_at='2024-01-24',
            finding_count=3,
            action_count=3,
        )
        result = summary.to_dict()
        assert 'title' in result
        assert 'source_file' in result
        assert 'finding_count' in result

    def test_summary_to_markdown(self):
        """Test getting markdown content."""
        content = '# Test\nThis is the content.'
        summary = GeneratedSummary(
            title='Test',
            content=content,
            source_file='test.csv',
            generated_at='2024-01-24',
            finding_count=3,
            action_count=3,
        )
        assert summary.to_markdown() == content


class TestGenerateSummary:
    """Tests for generate_summary function."""

    def test_generate_summary(self, sample_summary_input):
        """Test generating a summary."""
        summary = generate_summary(sample_summary_input)
        assert isinstance(summary, GeneratedSummary)
        assert len(summary.content) > 0

    def test_generate_summary_with_config(self, sample_summary_input):
        """Test generating summary with custom config."""
        config = SummaryConfig(
            title='Custom Title',
            max_findings=2,
        )
        summary = generate_summary(sample_summary_input, config)
        assert '2.' in summary.content  # At least 2 findings
        # Should have max 2 findings
        assert summary.finding_count <= 2

    def test_summary_contains_bluf(self, sample_summary_input):
        """Test summary contains BLUF section."""
        summary = generate_summary(sample_summary_input)
        assert 'Bottom Line Up Front' in summary.content

    def test_summary_contains_findings(self, sample_summary_input):
        """Test summary contains findings section."""
        summary = generate_summary(sample_summary_input)
        assert 'Top Findings' in summary.content

    def test_summary_contains_actions(self, sample_summary_input):
        """Test summary contains actions section."""
        summary = generate_summary(sample_summary_input)
        assert 'Recommended Actions' in summary.content

    def test_summary_contains_risks(self, sample_summary_input):
        """Test summary contains risks section."""
        summary = generate_summary(sample_summary_input)
        assert 'Risks & Considerations' in summary.content

    def test_summary_contains_footer(self, sample_summary_input):
        """Test summary contains footer."""
        summary = generate_summary(sample_summary_input)
        assert '@exec-summarizer' in summary.content


class TestCompileSummary:
    """Tests for compile_summary function."""

    def test_compile_summary(self, sample_extracted_data, sample_summary_config):
        """Test compiling a summary."""
        content = compile_summary(sample_extracted_data, sample_summary_config)
        assert '# Executive Summary' in content
        assert 'Bottom Line Up Front' in content
        assert 'Top Findings' in content

    def test_compile_includes_metrics(self, sample_extracted_data, sample_summary_config):
        """Test compiled summary includes metrics table."""
        content = compile_summary(sample_extracted_data, sample_summary_config)
        assert '| Metric |' in content

    def test_compile_includes_separator(self, sample_extracted_data, sample_summary_config):
        """Test compiled summary includes section separators."""
        content = compile_summary(sample_extracted_data, sample_summary_config)
        assert '---' in content


class TestSaveSummary:
    """Tests for save_summary function."""

    def test_save_summary(self, sample_summary_input, temp_output_dir):
        """Test saving a summary."""
        summary = generate_summary(sample_summary_input)
        filepath = save_summary(summary, temp_output_dir)

        assert Path(filepath).exists()
        assert filepath.endswith('.md')
        assert 'executive_summary' in filepath

    def test_save_summary_updates_filepath(self, sample_summary_input, temp_output_dir):
        """Test saving updates summary filepath."""
        summary = generate_summary(sample_summary_input)
        filepath = save_summary(summary, temp_output_dir)

        assert summary.filepath == filepath

    def test_save_summary_content(self, sample_summary_input, temp_output_dir):
        """Test saved summary has correct content."""
        summary = generate_summary(sample_summary_input)
        filepath = save_summary(summary, temp_output_dir)

        with open(filepath, 'r') as f:
            content = f.read()

        assert 'Bottom Line Up Front' in content
        assert '@exec-summarizer' in content


class TestGenerateSummaryFromFiles:
    """Tests for generate_summary_from_files function."""

    def test_generate_from_analysis_file(self, sample_analysis_json, temp_output_dir):
        """Test generating summary from analysis file."""
        summary = generate_summary_from_files(
            analysis_path=sample_analysis_json,
            output_dir=temp_output_dir,
        )
        assert isinstance(summary, GeneratedSummary)
        assert len(summary.filepath) > 0
        assert Path(summary.filepath).exists()

    def test_generate_from_report_file(self, sample_report_file, temp_output_dir):
        """Test generating summary from report file."""
        summary = generate_summary_from_files(
            report_path=sample_report_file,
            output_dir=temp_output_dir,
        )
        assert isinstance(summary, GeneratedSummary)

    def test_generate_from_both(self, sample_analysis_json, sample_report_file, temp_output_dir):
        """Test generating summary from both files."""
        summary = generate_summary_from_files(
            analysis_path=sample_analysis_json,
            report_path=sample_report_file,
            output_dir=temp_output_dir,
        )
        assert summary.finding_count > 0


class TestGetSummaryStats:
    """Tests for get_summary_stats function."""

    def test_stats_output(self, sample_summary_input, temp_output_dir):
        """Test summary stats output."""
        summary = generate_summary(sample_summary_input)
        save_summary(summary, temp_output_dir)

        stats = get_summary_stats(summary)
        assert '✅' in stats
        assert 'Executive Summary Complete' in stats
        assert summary.filepath in stats

    def test_stats_includes_counts(self, sample_summary_input, temp_output_dir):
        """Test stats include finding counts."""
        summary = generate_summary(sample_summary_input)
        save_summary(summary, temp_output_dir)

        stats = get_summary_stats(summary)
        assert 'findings' in stats.lower()


class TestEnsureOutputDir:
    """Tests for ensure_output_dir function."""

    def test_create_new_directory(self, temp_output_dir):
        """Test creating new directory."""
        new_dir = Path(temp_output_dir) / 'new_subdir'
        result = ensure_output_dir(str(new_dir))
        assert result.exists()

    def test_existing_directory(self, temp_output_dir):
        """Test with existing directory."""
        result = ensure_output_dir(temp_output_dir)
        assert result.exists()

    def test_default_directory(self):
        """Test default directory is ./output."""
        result = ensure_output_dir()
        assert result.name == 'output'
        # Clean up
        if result.exists() and not any(result.iterdir()):
            result.rmdir()


class TestGenerateSummaryFilename:
    """Tests for generate_summary_filename function."""

    def test_filename_format(self):
        """Test filename has correct format."""
        filename = generate_summary_filename('sales_data.csv')
        assert 'sales_data' in filename
        assert 'executive_summary' in filename
        assert filename.endswith('.md')

    def test_filename_includes_timestamp(self):
        """Test filename includes timestamp."""
        filename = generate_summary_filename('test.csv')
        # Should have YYYYMMDD format
        assert any(c.isdigit() for c in filename)

    def test_filename_with_path(self):
        """Test filename with full path source."""
        filename = generate_summary_filename('/path/to/data.csv')
        assert 'data' in filename
        assert '/path/to' not in filename
