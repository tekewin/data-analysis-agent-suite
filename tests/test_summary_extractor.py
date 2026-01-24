"""Tests for executive summary extraction utilities."""

import pytest
from src.summarization.extractor import (
    ExtractedMetric,
    ExtractedFinding,
    ExtractedData,
    SummaryConfig,
    extract_bluf,
    extract_metrics,
    extract_top_findings,
    extract_actions,
    extract_risks,
    extract_all,
    prioritize_findings,
    calculate_metric_status,
)
from src.summarization import SummaryInput


class TestExtractedMetric:
    """Tests for ExtractedMetric dataclass."""

    def test_create_metric(self):
        """Test creating an ExtractedMetric."""
        metric = ExtractedMetric(
            name='Revenue',
            value='$5.2M',
            change='+15%',
            status='good',
        )
        assert metric.name == 'Revenue'
        assert metric.value == '$5.2M'
        assert metric.change == '+15%'
        assert metric.status == 'good'

    def test_metric_to_dict(self):
        """Test converting metric to dictionary."""
        metric = ExtractedMetric(
            name='Revenue',
            value='$5.2M',
            change='+15%',
            status='good',
        )
        result = metric.to_dict()
        assert result['name'] == 'Revenue'
        assert result['status'] == 'good'

    def test_metric_default_status(self):
        """Test default status is neutral."""
        metric = ExtractedMetric(name='Test', value='100')
        assert metric.status == 'neutral'


class TestExtractedFinding:
    """Tests for ExtractedFinding dataclass."""

    def test_create_finding(self):
        """Test creating an ExtractedFinding."""
        finding = ExtractedFinding(
            title='Strong Correlation',
            impact='Revenue increases with quantity.',
            action='Investigate further.',
            importance='high',
        )
        assert finding.title == 'Strong Correlation'
        assert finding.importance == 'high'

    def test_finding_to_dict(self):
        """Test converting finding to dictionary."""
        finding = ExtractedFinding(
            title='Test',
            impact='Impact',
            action='Action',
            importance='medium',
        )
        result = finding.to_dict()
        assert result['title'] == 'Test'
        assert result['importance'] == 'medium'


class TestExtractedData:
    """Tests for ExtractedData dataclass."""

    def test_extracted_data_to_dict(self, sample_extracted_data):
        """Test converting extracted data to dictionary."""
        result = sample_extracted_data.to_dict()
        assert 'bluf' in result
        assert 'metrics' in result
        assert 'top_findings' in result
        assert 'recommended_actions' in result
        assert 'risks' in result


class TestSummaryConfig:
    """Tests for SummaryConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SummaryConfig()
        assert config.title == 'Executive Summary'
        assert config.max_findings == 3
        assert config.max_actions == 3
        assert config.max_risks == 3

    def test_custom_config(self):
        """Test custom configuration."""
        config = SummaryConfig(
            title='Custom Summary',
            max_findings=5,
        )
        assert config.title == 'Custom Summary'
        assert config.max_findings == 5

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = SummaryConfig()
        result = config.to_dict()
        assert 'title' in result
        assert 'max_findings' in result


class TestExtractBluf:
    """Tests for extract_bluf function."""

    def test_extract_bluf_from_analysis(self, sample_summary_input):
        """Test extracting BLUF from analysis."""
        bluf = extract_bluf(sample_summary_input)
        assert len(bluf) > 0
        assert 'correlation' in bluf.lower() or 'revenue' in bluf.lower()

    def test_extract_bluf_from_report(self, sample_report_content):
        """Test extracting BLUF from report content."""
        input_data = SummaryInput(
            source_file='test.csv',
            report_content=sample_report_content,
        )
        bluf = extract_bluf(input_data)
        assert len(bluf) > 0

    def test_extract_bluf_empty(self):
        """Test extracting BLUF with no data."""
        input_data = SummaryInput(source_file='test.csv')
        bluf = extract_bluf(input_data)
        assert 'Analysis complete' in bluf


class TestExtractMetrics:
    """Tests for extract_metrics function."""

    def test_extract_metrics_from_analysis(self, sample_summary_input):
        """Test extracting metrics from analysis."""
        metrics = extract_metrics(sample_summary_input)
        assert len(metrics) > 0
        assert isinstance(metrics[0], ExtractedMetric)

    def test_extract_metrics_max_limit(self, sample_summary_input):
        """Test metrics extraction respects max limit."""
        metrics = extract_metrics(sample_summary_input, max_metrics=2)
        assert len(metrics) <= 2

    def test_extract_metrics_no_analysis(self, sample_report_content):
        """Test extracting metrics with no analysis."""
        input_data = SummaryInput(
            source_file='test.csv',
            report_content=sample_report_content,
        )
        metrics = extract_metrics(input_data)
        assert len(metrics) == 0

    def test_metrics_include_trends(self, sample_summary_input):
        """Test metrics include trend information."""
        metrics = extract_metrics(sample_summary_input, max_metrics=10)
        trend_metrics = [m for m in metrics if 'Trend' in m.name]
        assert len(trend_metrics) > 0


class TestExtractTopFindings:
    """Tests for extract_top_findings function."""

    def test_extract_findings(self, sample_summary_input):
        """Test extracting top findings."""
        findings = extract_top_findings(sample_summary_input)
        assert len(findings) > 0
        assert isinstance(findings[0], ExtractedFinding)

    def test_findings_ordered_by_importance(self, sample_summary_input):
        """Test findings are ordered by importance."""
        findings = extract_top_findings(sample_summary_input)
        if len(findings) >= 2:
            # First should be high importance
            assert findings[0].importance == 'high'

    def test_findings_max_limit(self, sample_summary_input):
        """Test findings extraction respects max limit."""
        findings = extract_top_findings(sample_summary_input, count=1)
        assert len(findings) == 1

    def test_findings_no_analysis(self, sample_report_content):
        """Test extracting findings with no analysis."""
        input_data = SummaryInput(
            source_file='test.csv',
            report_content=sample_report_content,
        )
        findings = extract_top_findings(input_data)
        assert len(findings) == 0


class TestPrioritizeFindings:
    """Tests for prioritize_findings function."""

    def test_prioritize_by_importance(self, sample_analysis_result):
        """Test findings prioritized by importance."""
        findings = sample_analysis_result.findings
        prioritized = prioritize_findings(findings)
        assert prioritized[0].importance == 'high'

    def test_prioritize_count(self, sample_analysis_result):
        """Test prioritization respects count."""
        findings = sample_analysis_result.findings
        prioritized = prioritize_findings(findings, count=2)
        assert len(prioritized) == 2


class TestExtractActions:
    """Tests for extract_actions function."""

    def test_extract_actions(self, sample_summary_input):
        """Test extracting actions."""
        actions = extract_actions(sample_summary_input)
        assert len(actions) > 0
        assert isinstance(actions[0], str)

    def test_actions_max_limit(self, sample_summary_input):
        """Test actions extraction respects max limit."""
        actions = extract_actions(sample_summary_input, count=1)
        assert len(actions) == 1

    def test_actions_from_recommendations(self, sample_summary_input):
        """Test actions come from recommendations."""
        actions = extract_actions(sample_summary_input)
        # Should contain actionable recommendations
        assert any('Investigate' in a or 'Monitor' in a for a in actions)

    def test_actions_no_analysis(self, sample_report_content):
        """Test extracting actions with no analysis."""
        input_data = SummaryInput(
            source_file='test.csv',
            report_content=sample_report_content,
        )
        actions = extract_actions(input_data)
        assert len(actions) == 0


class TestExtractRisks:
    """Tests for extract_risks function."""

    def test_extract_risks(self, sample_summary_input):
        """Test extracting risks."""
        risks = extract_risks(sample_summary_input)
        assert len(risks) > 0
        assert isinstance(risks[0], str)

    def test_risks_max_limit(self, sample_summary_input):
        """Test risks extraction respects max limit."""
        risks = extract_risks(sample_summary_input, count=1)
        assert len(risks) == 1

    def test_risks_include_validation_caveat(self, sample_summary_input):
        """Test risks include validation caveat."""
        risks = extract_risks(sample_summary_input, count=5)
        # Should always include validation caveat
        assert any('validate' in r.lower() for r in risks)

    def test_risks_no_analysis(self, sample_report_content):
        """Test extracting risks with no analysis returns default."""
        input_data = SummaryInput(
            source_file='test.csv',
            report_content=sample_report_content,
        )
        risks = extract_risks(input_data)
        assert len(risks) >= 1  # Should have default caveat


class TestExtractAll:
    """Tests for extract_all function."""

    def test_extract_all_complete(self, sample_summary_input):
        """Test extracting all data."""
        config = SummaryConfig()
        extracted = extract_all(sample_summary_input, config)

        assert isinstance(extracted, ExtractedData)
        assert len(extracted.bluf) > 0
        assert len(extracted.metrics) > 0
        assert len(extracted.top_findings) > 0
        assert len(extracted.recommended_actions) > 0
        assert len(extracted.risks) > 0

    def test_extract_all_respects_config(self, sample_summary_input):
        """Test extraction respects configuration limits."""
        config = SummaryConfig(
            max_findings=1,
            max_actions=1,
            max_risks=1,
            max_metrics=1,
        )
        extracted = extract_all(sample_summary_input, config)

        assert len(extracted.top_findings) == 1
        assert len(extracted.recommended_actions) == 1
        assert len(extracted.risks) == 1

    def test_extract_all_default_config(self, sample_summary_input):
        """Test extraction with default config."""
        extracted = extract_all(sample_summary_input)
        assert extracted is not None
        assert len(extracted.top_findings) <= 3


class TestCalculateMetricStatus:
    """Tests for calculate_metric_status function."""

    def test_positive_change_good(self):
        """Test positive large change is good."""
        metric = ExtractedMetric(name='Test', value='100', change='+15%')
        status = calculate_metric_status(metric)
        assert status == 'good'

    def test_negative_change_critical(self):
        """Test negative large change is critical."""
        metric = ExtractedMetric(name='Test', value='100', change='-15%')
        status = calculate_metric_status(metric)
        assert status == 'critical'

    def test_small_negative_warning(self):
        """Test small negative change is warning."""
        metric = ExtractedMetric(name='Test', value='100', change='-5%')
        status = calculate_metric_status(metric)
        assert status == 'warning'

    def test_no_change_neutral(self):
        """Test no change is neutral."""
        metric = ExtractedMetric(name='Test', value='100', change=None)
        status = calculate_metric_status(metric)
        assert status == 'neutral'

    def test_small_positive_neutral(self):
        """Test small positive change is neutral."""
        metric = ExtractedMetric(name='Test', value='100', change='+5%')
        status = calculate_metric_status(metric)
        assert status == 'neutral'
