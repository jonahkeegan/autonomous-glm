"""
Unit tests for CLI report command.

Tests the report command options, validation, and output.
"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from src.cli.main import cli
from src.cli.errors import ExitCode


class TestReportCommand:
    """Tests for the report command."""
    
    def test_report_help(self):
        """Test that report --help displays usage information."""
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "--help"])
        
        assert result.exit_code == ExitCode.SUCCESS
        assert "AUDIT_ID" in result.output
        assert "--latest" in result.output
        assert "--full" in result.output
        assert "--json" in result.output
        assert "--output" in result.output
    
    def test_report_requires_audit_id_or_flag(self):
        """Test that report requires audit_id or a flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["report"])
        
        # Should fail because no audit_id or flag provided
        assert result.exit_code != ExitCode.SUCCESS
        assert result.exception is not None
    
    @patch("src.cli.commands.report._get_report")
    def test_report_with_audit_id(self, mock_get_report):
        """Test report with a valid audit ID."""
        mock_get_report.return_value = {
            "report_id": "report_123",
            "audit_id": "audit_abc",
            "status": "completed",
            "total_findings": 5,
            "by_severity": {"high": 2, "medium": 3},
            "by_phase": {"Critical": 2, "Refinement": 3},
            "findings": [],
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "audit_abc"])
        
        assert result.exit_code == ExitCode.SUCCESS
        mock_get_report.assert_called_once()
    
    @patch("src.cli.commands.report._get_report")
    def test_report_json_output(self, mock_get_report):
        """Test report with JSON output flag."""
        mock_get_report.return_value = {
            "report_id": "report_123",
            "audit_id": "audit_abc",
            "status": "completed",
            "total_findings": 5,
            "by_severity": {"high": 2},
            "by_phase": {"Critical": 2},
            "findings": [],
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "audit_abc", "--json"])
        
        assert result.exit_code == ExitCode.SUCCESS
        import json
        output = json.loads(result.output)
        assert output["report_id"] == "report_123"
    
    @patch("src.cli.commands.report._list_reports")
    def test_report_list_flag(self, mock_list_reports):
        """Test report --list flag."""
        mock_list_reports.return_value = None  # Function prints directly
        
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "--list"])
        
        mock_list_reports.assert_called_once()
    
    @patch("src.cli.commands.report._get_latest_audit_id")
    @patch("src.cli.commands.report._get_report")
    def test_report_latest_flag(self, mock_get_report, mock_get_latest):
        """Test report --latest flag."""
        mock_get_latest.return_value = "audit_latest"
        mock_get_report.return_value = {
            "report_id": "report_latest",
            "audit_id": "audit_latest",
            "status": "completed",
            "total_findings": 3,
            "by_severity": {},
            "by_phase": {},
            "findings": [],
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "--latest"])
        
        assert result.exit_code == ExitCode.SUCCESS
        mock_get_latest.assert_called_once()
        mock_get_report.assert_called_once_with("audit_latest", include_full=False)
    
    @patch("src.cli.commands.report._get_report")
    def test_report_full_flag(self, mock_get_report):
        """Test report --full flag includes all details."""
        mock_get_report.return_value = {
            "report_id": "report_123",
            "audit_id": "audit_abc",
            "status": "completed",
            "total_findings": 5,
            "by_severity": {"high": 2},
            "by_phase": {"Critical": 2},
            "findings": [
                {"id": "f1", "dimension": "typography", "severity": "high"},
            ],
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "audit_abc", "--full"])
        
        assert result.exit_code == ExitCode.SUCCESS
        mock_get_report.assert_called_once_with("audit_abc", include_full=True)


class TestReportExport:
    """Tests for report export functionality."""
    
    @patch("src.cli.commands.report._get_report")
    def test_report_export_markdown(self, mock_get_report, tmp_path):
        """Test exporting report to markdown file."""
        mock_get_report.return_value = {
            "report_id": "report_123",
            "audit_id": "audit_abc",
            "status": "completed",
            "total_findings": 5,
            "by_severity": {"high": 2},
            "by_phase": {"Critical": 2},
            "findings": [],
            "created_at": "2024-01-01T00:00:00",
        }
        
        output_file = tmp_path / "report.md"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            "report", "audit_abc",
            "--output", str(output_file),
        ])
        
        assert result.exit_code == ExitCode.SUCCESS
        assert output_file.exists()
        content = output_file.read_text()
        assert "# Audit Report" in content
    
    @patch("src.cli.commands.report._get_report")
    def test_report_export_json(self, mock_get_report, tmp_path):
        """Test exporting report to JSON file."""
        mock_get_report.return_value = {
            "report_id": "report_123",
            "audit_id": "audit_abc",
            "status": "completed",
            "total_findings": 5,
            "by_severity": {"high": 2},
            "by_phase": {"Critical": 2},
            "findings": [],
        }
        
        output_file = tmp_path / "report.json"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            "report", "audit_abc",
            "--output", str(output_file),
        ])
        
        assert result.exit_code == ExitCode.SUCCESS
        assert output_file.exists()
        import json
        content = json.loads(output_file.read_text())
        assert content["report_id"] == "report_123"


class TestReportMarkdownFormatting:
    """Tests for markdown report formatting."""
    
    def test_report_to_markdown(self):
        """Test converting report to markdown."""
        from src.cli.commands.report import _report_to_markdown
        
        report = {
            "report_id": "report_123",
            "audit_id": "audit_abc",
            "created_at": "2024-01-01T00:00:00",
            "total_findings": 3,
            "by_severity": {"high": 1, "medium": 2},
            "by_phase": {"Critical": 1, "Refinement": 2},
            "findings": [
                {
                    "title": "Test Finding",
                    "dimension": "typography",
                    "severity": "high",
                    "phase": "Critical",
                    "description": "Test description",
                }
            ],
        }
        
        markdown = _report_to_markdown(report)
        
        assert "# Audit Report" in markdown
        assert "report_123" in markdown
        assert "Summary by Severity" in markdown
        assert "Summary by Phase" in markdown
        assert "Test Finding" in markdown