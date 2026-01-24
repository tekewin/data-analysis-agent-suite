"""Tests for executive summary formatting utilities."""

import pytest
from src.summarization.formatter import (
    format_status_indicator,
    format_importance_indicator,
    format_metrics_table,
    format_finding_block,
    format_finding_list,
    format_action_list,
    format_risk_list,
    format_bluf_section,
    format_summary_header,
    format_summary_footer,
    format_change,
    format_number_compact,
    format_currency,
)
from src.summarization import ExtractedMetric, ExtractedFinding


class TestStatusIndicator:
    """Tests for format_status_indicator."""

    def test_good_status(self):
        """Test good status returns green."""
        assert format_status_indicator('good') == '🟢'

    def test_warning_status(self):
        """Test warning status returns yellow."""
        assert format_status_indicator('warning') == '🟡'

    def test_critical_status(self):
        """Test critical status returns red."""
        assert format_status_indicator('critical') == '🔴'

    def test_neutral_status(self):
        """Test neutral status returns white."""
        assert format_status_indicator('neutral') == '⚪'

    def test_unknown_status(self):
        """Test unknown status defaults to white."""
        assert format_status_indicator('unknown') == '⚪'

    def test_case_insensitive(self):
        """Test status indicators are case insensitive."""
        assert format_status_indicator('GOOD') == '🟢'
        assert format_status_indicator('Warning') == '🟡'
        assert format_status_indicator('CRITICAL') == '🔴'


class TestImportanceIndicator:
    """Tests for format_importance_indicator."""

    def test_high_importance(self):
        """Test high importance returns red."""
        assert format_importance_indicator('high') == '🔴'

    def test_medium_importance(self):
        """Test medium importance returns yellow."""
        assert format_importance_indicator('medium') == '🟡'

    def test_low_importance(self):
        """Test low importance returns green."""
        assert format_importance_indicator('low') == '🟢'

    def test_unknown_importance(self):
        """Test unknown importance defaults to white."""
        assert format_importance_indicator('unknown') == '⚪'


class TestMetricsTable:
    """Tests for format_metrics_table."""

    def test_empty_metrics(self):
        """Test empty metrics list returns placeholder."""
        result = format_metrics_table([])
        assert 'No key metrics' in result

    def test_single_metric(self, sample_extracted_metrics):
        """Test single metric formatting."""
        result = format_metrics_table([sample_extracted_metrics[0]])
        assert '| Metric | Value | Change | Status |' in result
        assert 'Revenue' in result
        assert '+15%' in result
        assert '🟢' in result

    def test_multiple_metrics(self, sample_extracted_metrics):
        """Test multiple metrics formatting."""
        result = format_metrics_table(sample_extracted_metrics)
        assert 'Revenue' in result
        assert 'Quantity' in result
        assert 'Sales Trend' in result

    def test_metric_without_change(self, sample_extracted_metrics):
        """Test metric without change shows dash."""
        # The second metric has no change
        result = format_metrics_table([sample_extracted_metrics[1]])
        assert '| - |' in result


class TestFindingBlock:
    """Tests for format_finding_block."""

    def test_high_importance_finding(self, sample_extracted_findings):
        """Test high importance finding has red indicator."""
        result = format_finding_block(sample_extracted_findings[0], 1)
        assert '### 1.' in result
        assert '🔴' in result
        assert '**Impact**:' in result
        assert '**Action**:' in result

    def test_medium_importance_finding(self, sample_extracted_findings):
        """Test medium importance finding has yellow indicator."""
        result = format_finding_block(sample_extracted_findings[1], 2)
        assert '### 2.' in result
        assert '🟡' in result

    def test_low_importance_finding(self, sample_extracted_findings):
        """Test low importance finding has green indicator."""
        result = format_finding_block(sample_extracted_findings[2], 3)
        assert '### 3.' in result
        assert '🟢' in result

    def test_finding_content(self, sample_extracted_findings):
        """Test finding content is included."""
        result = format_finding_block(sample_extracted_findings[0], 1)
        assert 'Strong correlation' in result
        assert 'Investigate' in result


class TestFindingList:
    """Tests for format_finding_list."""

    def test_empty_findings(self):
        """Test empty findings list returns placeholder."""
        result = format_finding_list([])
        assert 'No key findings' in result

    def test_multiple_findings(self, sample_extracted_findings):
        """Test multiple findings are numbered."""
        result = format_finding_list(sample_extracted_findings)
        assert '### 1.' in result
        assert '### 2.' in result
        assert '### 3.' in result


class TestActionList:
    """Tests for format_action_list."""

    def test_empty_actions(self):
        """Test empty actions list returns placeholder."""
        result = format_action_list([])
        assert 'No specific actions' in result

    def test_action_categories(self):
        """Test actions are categorized."""
        actions = ['Do this now', 'Do this soon', 'Plan for this']
        result = format_action_list(actions)
        assert '**Immediate**:' in result
        assert '**Short-term**:' in result
        assert '**Strategic**:' in result

    def test_action_numbering(self):
        """Test actions are numbered."""
        actions = ['First', 'Second', 'Third']
        result = format_action_list(actions)
        assert '1. ' in result
        assert '2. ' in result
        assert '3. ' in result


class TestRiskList:
    """Tests for format_risk_list."""

    def test_empty_risks(self):
        """Test empty risks list returns placeholder."""
        result = format_risk_list([])
        assert 'No significant risks' in result

    def test_risk_formatting(self):
        """Test risks are bullet-pointed."""
        risks = ['Risk one', 'Risk two']
        result = format_risk_list(risks)
        assert '- Risk one' in result
        assert '- Risk two' in result


class TestBlufSection:
    """Tests for format_bluf_section."""

    def test_normal_bluf(self):
        """Test normal BLUF is returned as-is."""
        bluf = "This is the key insight."
        result = format_bluf_section(bluf)
        assert result == bluf

    def test_empty_bluf(self):
        """Test empty BLUF returns placeholder."""
        result = format_bluf_section("")
        assert 'not available' in result


class TestSummaryHeader:
    """Tests for format_summary_header."""

    def test_basic_header(self):
        """Test basic header formatting."""
        result = format_summary_header(
            title='Test Report',
            date='2024-01-24',
            source='test_data.csv',
        )
        assert '# Executive Summary: Test Report' in result
        assert '**Date**: 2024-01-24' in result
        assert '**Source**: `test_data.csv`' in result

    def test_header_with_analysis_period(self):
        """Test header with analysis period."""
        result = format_summary_header(
            title='Test Report',
            date='2024-01-24',
            analysis_period='Q1 2024',
            source='test_data.csv',
        )
        assert '**Analysis Period**: Q1 2024' in result


class TestSummaryFooter:
    """Tests for format_summary_footer."""

    def test_footer_content(self):
        """Test footer includes report reference."""
        result = format_summary_footer('full_report.md')
        assert 'full_report.md' in result
        assert '@exec-summarizer' in result


class TestFormatChange:
    """Tests for format_change."""

    def test_positive_change(self):
        """Test positive change has plus sign."""
        assert format_change(15.5) == '+15.5%'

    def test_negative_change(self):
        """Test negative change is formatted correctly."""
        assert format_change(-3.2) == '-3.2%'

    def test_zero_change(self):
        """Test zero change."""
        assert format_change(0) == '0%'

    def test_none_change(self):
        """Test None change returns dash."""
        assert format_change(None) == '-'

    def test_custom_suffix(self):
        """Test custom suffix."""
        assert format_change(10, suffix='pts') == '+10.0pts'


class TestFormatNumberCompact:
    """Tests for format_number_compact."""

    def test_billions(self):
        """Test billion formatting."""
        assert format_number_compact(1_500_000_000) == '1.5B'

    def test_millions(self):
        """Test million formatting."""
        assert format_number_compact(1_500_000) == '1.5M'

    def test_thousands(self):
        """Test thousand formatting."""
        assert format_number_compact(5_500) == '5.5K'

    def test_small_numbers(self):
        """Test small number formatting."""
        assert format_number_compact(500) == '500'

    def test_none(self):
        """Test None returns N/A."""
        assert format_number_compact(None) == 'N/A'


class TestFormatCurrency:
    """Tests for format_currency."""

    def test_default_currency(self):
        """Test default USD currency symbol."""
        assert format_currency(1_500_000) == '$1.5M'

    def test_custom_currency(self):
        """Test custom currency symbol."""
        assert format_currency(1_500_000, currency='€') == '€1.5M'

    def test_thousands(self):
        """Test currency with thousands."""
        assert format_currency(5_500) == '$5.5K'

    def test_none(self):
        """Test None returns N/A."""
        assert format_currency(None) == 'N/A'
