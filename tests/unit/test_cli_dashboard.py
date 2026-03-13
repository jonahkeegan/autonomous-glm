"""
Unit tests for CLI dashboard command.
"""

import pytest
from click.testing import CliRunner
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.cli.main import cli
from src.cli.dashboard.metrics import (
    MetricsAggregator,
    DashboardMetrics,
    FindingsSummary,
    TrendData,
    TrendPoint,
    ArtifactStats,
    Period,
)
from src.cli.dashboard.renderer import DashboardRenderer, render_dashboard


class TestPeriod:
    """Tests for Period enum."""
    
    def test_period_values(self):
        """Test Period enum has expected values."""
        assert Period.DAY == "day"
        assert Period.WEEK == "week"
        assert Period.MONTH == "month"
        assert Period.ALL == "all"


class TestFindingsSummary:
    """Tests for FindingsSummary model."""
    
    def test_default_values(self):
        """Test default values are zero."""
        summary = FindingsSummary()
        assert summary.critical == 0
        assert summary.high == 0
        assert summary.medium == 0
        assert summary.low == 0
        assert summary.total == 0
    
    def test_custom_values(self):
        """Test custom values are set correctly."""
        summary = FindingsSummary(critical=5, high=10, medium=20, low=30)
        assert summary.critical == 5
        assert summary.high == 10
        assert summary.medium == 20
        assert summary.low == 30
        # Note: total is not auto-calculated in the model


class TestTrendPoint:
    """Tests for TrendPoint model."""
    
    def test_trend_point_creation(self):
        """Test TrendPoint creation."""
        point = TrendPoint(date="2025-01-15", audits=5, findings=12)
        assert point.date == "2025-01-15"
        assert point.audits == 5
        assert point.findings == 12


class TestTrendData:
    """Tests for TrendData model."""
    
    def test_default_values(self):
        """Test default TrendData."""
        trend = TrendData()
        assert trend.points == []
        assert trend.period_days == 7
    
    def test_with_points(self):
        """Test TrendData with points."""
        points = [
            TrendPoint(date="2025-01-15", audits=5, findings=12),
            TrendPoint(date="2025-01-16", audits=3, findings=8),
        ]
        trend = TrendData(points=points, period_days=2)
        assert len(trend.points) == 2
        assert trend.period_days == 2


class TestArtifactStats:
    """Tests for ArtifactStats model."""
    
    def test_default_values(self):
        """Test default ArtifactStats."""
        stats = ArtifactStats()
        assert stats.total_screens == 0
        assert stats.total_flows == 0
        assert stats.total_components == 0
        assert stats.total_tokens == 0


class TestDashboardMetrics:
    """Tests for DashboardMetrics model."""
    
    def test_dashboard_metrics_creation(self):
        """Test DashboardMetrics creation with required fields."""
        metrics = DashboardMetrics(
            period=Period.WEEK,
            period_start="2025-01-08T00:00:00",
            period_end="2025-01-15T00:00:00",
        )
        assert metrics.period == Period.WEEK
        assert metrics.total_audits == 0
        assert metrics.findings_summary.total == 0
    
    def test_dashboard_metrics_with_data(self):
        """Test DashboardMetrics with full data."""
        metrics = DashboardMetrics(
            period=Period.MONTH,
            period_start="2024-12-15T00:00:00",
            period_end="2025-01-15T00:00:00",
            total_audits=50,
            successful_audits=45,
            failed_audits=5,
            findings_summary=FindingsSummary(critical=2, high=10, medium=20, low=30),
        )
        assert metrics.total_audits == 50
        assert metrics.successful_audits == 45
        assert metrics.failed_audits == 5
        assert metrics.findings_summary.critical == 2


class TestMetricsAggregator:
    """Tests for MetricsAggregator class."""
    
    def test_get_period_range_day(self):
        """Test period range for day."""
        aggregator = MetricsAggregator()
        start, end = aggregator.get_period_range(Period.DAY)
        
        # End should be now, start should be ~24 hours ago
        assert end > start
        delta = end - start
        assert timedelta(hours=23) <= delta <= timedelta(hours=25)
    
    def test_get_period_range_week(self):
        """Test period range for week."""
        aggregator = MetricsAggregator()
        start, end = aggregator.get_period_range(Period.WEEK)
        
        delta = end - start
        assert timedelta(days=6) <= delta <= timedelta(days=8)
    
    def test_get_period_range_month(self):
        """Test period range for month."""
        aggregator = MetricsAggregator()
        start, end = aggregator.get_period_range(Period.MONTH)
        
        delta = end - start
        assert timedelta(days=29) <= delta <= timedelta(days=31)
    
    def test_get_period_range_all(self):
        """Test period range for all time."""
        aggregator = MetricsAggregator()
        start, end = aggregator.get_period_range(Period.ALL)
        
        # Should be a very wide range
        assert start.year < 2025
    
    @patch('src.db.database.connection')
    def test_get_audit_count_empty(self, mock_connection):
        """Test audit count with empty database."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"count": 0}
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connection.return_value = mock_conn
        
        aggregator = MetricsAggregator()
        count = aggregator.get_audit_count(Period.WEEK)
        
        assert count == 0
    
    @patch('src.db.database.connection')
    def test_get_audit_count_with_data(self, mock_connection):
        """Test audit count with data."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"count": 42}
        mock_conn.execute.return_value = mock_cursor
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_connection.return_value = mock_conn
        
        aggregator = MetricsAggregator()
        count = aggregator.get_audit_count(Period.WEEK)
        
        assert count == 42


class TestDashboardRenderer:
    """Tests for DashboardRenderer class."""
    
    def test_render_json(self):
        """Test JSON rendering."""
        metrics = DashboardMetrics(
            period=Period.WEEK,
            period_start="2025-01-08T00:00:00",
            period_end="2025-01-15T00:00:00",
            total_audits=10,
        )
        
        renderer = DashboardRenderer()
        json_output = renderer.render_json(metrics)
        
        assert '"total_audits": 10' in json_output
        assert '"period": "week"' in json_output
    
    def test_render_html(self):
        """Test HTML rendering."""
        metrics = DashboardMetrics(
            period=Period.WEEK,
            period_start="2025-01-08T00:00:00",
            period_end="2025-01-15T00:00:00",
            total_audits=10,
        )
        
        renderer = DashboardRenderer()
        html_output = renderer.render_html(metrics)
        
        assert "<!DOCTYPE html>" in html_output
        assert "Autonomous-GLM Dashboard" in html_output
        assert "10" in html_output
    
    def test_render_terminal(self):
        """Test terminal rendering."""
        metrics = DashboardMetrics(
            period=Period.WEEK,
            period_start="2025-01-08T00:00:00",
            period_end="2025-01-15T00:00:00",
            total_audits=10,
            successful_audits=8,
            failed_audits=2,
        )
        
        renderer = DashboardRenderer()
        terminal_output = renderer.render_terminal(metrics)
        
        # Should contain Rich markup
        assert "AUDITS" in terminal_output or "10" in terminal_output


class TestRenderDashboard:
    """Tests for render_dashboard convenience function."""
    
    def test_render_json_format(self):
        """Test render_dashboard with JSON format."""
        metrics = DashboardMetrics(
            period=Period.WEEK,
            period_start="2025-01-08T00:00:00",
            period_end="2025-01-15T00:00:00",
        )
        
        output = render_dashboard(metrics, format="json")
        assert '"period"' in output
    
    def test_render_html_format(self):
        """Test render_dashboard with HTML format."""
        metrics = DashboardMetrics(
            period=Period.WEEK,
            period_start="2025-01-08T00:00:00",
            period_end="2025-01-15T00:00:00",
        )
        
        output = render_dashboard(metrics, format="html")
        assert "<!DOCTYPE html>" in output
    
    def test_render_to_file(self, tmp_path):
        """Test render_dashboard writes to file."""
        metrics = DashboardMetrics(
            period=Period.WEEK,
            period_start="2025-01-08T00:00:00",
            period_end="2025-01-15T00:00:00",
        )
        
        output_file = tmp_path / "dashboard.json"
        output = render_dashboard(metrics, format="json", output_path=str(output_file))
        
        assert output_file.exists()
        assert '"period"' in output_file.read_text()


class TestDashboardCommand:
    """Tests for the dashboard CLI command."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    @patch.object(MetricsAggregator, 'get_metrics')
    def test_dashboard_command_default(self, mock_get_metrics, runner):
        """Test dashboard command with default options."""
        mock_get_metrics.return_value = DashboardMetrics(
            period=Period.WEEK,
            period_start="2025-01-08T00:00:00",
            period_end="2025-01-15T00:00:00",
            total_audits=10,
        )
        
        result = runner.invoke(cli, ['dashboard'])
        
        assert result.exit_code == 0
    
    @patch.object(MetricsAggregator, 'get_metrics')
    def test_dashboard_command_json(self, mock_get_metrics, runner):
        """Test dashboard command with JSON output."""
        mock_get_metrics.return_value = DashboardMetrics(
            period=Period.WEEK,
            period_start="2025-01-08T00:00:00",
            period_end="2025-01-15T00:00:00",
            total_audits=10,
        )
        
        result = runner.invoke(cli, ['dashboard', '--json'])
        
        assert result.exit_code == 0
        assert '"period"' in result.output
    
    @patch.object(MetricsAggregator, 'get_metrics')
    def test_dashboard_command_period(self, mock_get_metrics, runner):
        """Test dashboard command with custom period."""
        mock_get_metrics.return_value = DashboardMetrics(
            period=Period.MONTH,
            period_start="2024-12-15T00:00:00",
            period_end="2025-01-15T00:00:00",
            total_audits=50,
        )
        
        result = runner.invoke(cli, ['dashboard', '--period', 'month'])
        
        assert result.exit_code == 0
        # Verify get_metrics was called with MONTH period
        mock_get_metrics.assert_called_once()
        called_period = mock_get_metrics.call_args[0][0]
        assert called_period == Period.MONTH
    
    @patch.object(MetricsAggregator, 'get_metrics')
    def test_dashboard_command_html(self, mock_get_metrics, runner):
        """Test dashboard command with HTML output."""
        mock_get_metrics.return_value = DashboardMetrics(
            period=Period.WEEK,
            period_start="2025-01-08T00:00:00",
            period_end="2025-01-15T00:00:00",
            total_audits=10,
        )
        
        result = runner.invoke(cli, ['dashboard', '--html'])
        
        assert result.exit_code == 0
        assert "<!DOCTYPE html>" in result.output
    
    @patch.object(MetricsAggregator, 'get_metrics')
    def test_dashboard_command_empty_data(self, mock_get_metrics, runner):
        """Test dashboard command with empty data."""
        mock_get_metrics.return_value = DashboardMetrics(
            period=Period.WEEK,
            period_start="2025-01-08T00:00:00",
            period_end="2025-01-15T00:00:00",
            total_audits=0,
        )
        
        result = runner.invoke(cli, ['dashboard'])
        
        assert result.exit_code == 0
        assert "No data available" in result.output


class TestPDFExport:
    """Tests for PDF export functionality."""
    
    def test_pdf_generator_imports(self):
        """Test PDFGenerator can be imported."""
        from src.cli.export.pdf import PDFGenerator, generate_pdf
        
        assert PDFGenerator is not None
        assert generate_pdf is not None
    
    def test_pdf_generator_init(self):
        """Test PDFGenerator initialization."""
        from src.cli.export.pdf import PDFGenerator
        
        generator = PDFGenerator()
        assert generator.template_dir is not None
    
    def test_pdf_generator_set_template(self):
        """Test PDFGenerator template setting."""
        from src.cli.export.pdf import PDFGenerator
        
        generator = PDFGenerator()
        generator.set_template("report")
        
        assert generator.current_template == "report"