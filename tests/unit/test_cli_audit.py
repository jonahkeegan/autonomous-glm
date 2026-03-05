"""
Unit tests for CLI audit command.

Tests the audit command options, validation, and output.
"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from src.cli.main import cli
from src.cli.errors import ExitCode


class TestAuditCommand:
    """Tests for the audit command."""
    
    def test_audit_help(self):
        """Test that audit --help displays usage information."""
        runner = CliRunner()
        result = runner.invoke(cli, ["audit", "--help"])
        
        assert result.exit_code == ExitCode.SUCCESS
        assert "ARTIFACT_ID" in result.output
        assert "--dimensions" in result.output
        assert "--json" in result.output
        assert "--verbose" in result.output
    
    def test_audit_requires_artifact_id(self):
        """Test that audit requires an artifact ID argument."""
        runner = CliRunner()
        result = runner.invoke(cli, ["audit"])
        
        # Should fail because artifact_id is required
        assert result.exit_code != ExitCode.SUCCESS
    
    @patch("src.cli.commands.audit._run_audit")
    def test_audit_with_artifact_id(self, mock_run_audit):
        """Test audit with a valid artifact ID."""
        mock_run_audit.return_value = {
            "audit_id": "audit_123",
            "screen_id": "screen_abc",
            "status": "completed",
            "total_findings": 5,
            "by_severity": {"high": 2, "medium": 3},
            "findings": [],
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, ["audit", "screen_abc"])
        
        assert result.exit_code == ExitCode.SUCCESS
        mock_run_audit.assert_called_once()
    
    @patch("src.cli.commands.audit._run_audit")
    def test_audit_json_output(self, mock_run_audit):
        """Test audit with JSON output flag."""
        mock_run_audit.return_value = {
            "audit_id": "audit_123",
            "screen_id": "screen_abc",
            "status": "completed",
            "total_findings": 5,
            "by_severity": {"high": 2, "medium": 3},
            "findings": [],
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, ["audit", "screen_abc", "--json"])
        
        assert result.exit_code == ExitCode.SUCCESS
        # JSON output should be parseable
        import json
        output = json.loads(result.output)
        assert output["audit_id"] == "audit_123"
    
    @patch("src.cli.commands.audit._run_audit")
    def test_audit_with_dimensions(self, mock_run_audit):
        """Test audit with specific dimensions."""
        mock_run_audit.return_value = {
            "audit_id": "audit_123",
            "screen_id": "screen_abc",
            "status": "completed",
            "total_findings": 2,
            "by_severity": {"medium": 2},
            "findings": [],
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            "audit", "screen_abc",
            "-d", "typography",
            "-d", "spacing_rhythm",
        ])
        
        assert result.exit_code == ExitCode.SUCCESS
        # Check that dimensions were passed
        call_args = mock_run_audit.call_args
        assert "typography" in call_args[1]["dimensions"]
    
    def test_audit_invalid_dimension(self):
        """Test audit with an invalid dimension."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "audit", "screen_abc",
            "-d", "invalid_dimension",
        ])
        
        # Should fail with error (Click CliRunner returns 1 for exceptions)
        assert result.exit_code != ExitCode.SUCCESS
        # Exception was raised (visible in exception type)
        assert result.exception is not None
    
    @patch("src.cli.commands.audit._run_audit")
    def test_audit_verbose_flag(self, mock_run_audit):
        """Test audit with verbose output."""
        mock_run_audit.return_value = {
            "audit_id": "audit_123",
            "screen_id": "screen_abc",
            "status": "completed",
            "total_findings": 2,
            "by_severity": {"medium": 2},
            "findings": [
                {"id": "f1", "dimension": "typography", "severity": "medium", "title": "Test"},
            ],
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, ["audit", "screen_abc", "--verbose"])
        
        assert result.exit_code == ExitCode.SUCCESS
    
    @patch("src.cli.commands.audit._run_audit")
    def test_audit_with_global_json_flag(self, mock_run_audit):
        """Test audit with global --json flag."""
        mock_run_audit.return_value = {
            "audit_id": "audit_123",
            "screen_id": "screen_abc",
            "status": "completed",
            "total_findings": 5,
            "by_severity": {"high": 2},
            "findings": [],
        }
        
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "audit", "screen_abc"])
        
        assert result.exit_code == ExitCode.SUCCESS


class TestAuditValidation:
    """Tests for audit command validation."""
    
    def test_valid_dimensions_list(self):
        """Test that valid dimensions are accepted."""
        from src.cli.commands.audit import _get_valid_dimensions
        
        dimensions = _get_valid_dimensions()
        
        assert "typography" in dimensions
        assert "spacing_rhythm" in dimensions
        assert "color" in dimensions
        assert "accessibility" in dimensions
        assert len(dimensions) == 15


class TestAuditResultFormatting:
    """Tests for audit result formatting."""
    
    def test_audit_result_to_dict(self):
        """Test conversion of audit result to dict."""
        from src.cli.commands.audit import _audit_result_to_dict
        
        # Mock result object
        class MockResult:
            def model_dump(self):
                return {
                    "id": "audit_123",
                    "screen_id": "screen_abc",
                    "status": "completed",
                    "total_findings": 5,
                    "by_severity": {"high": 2},
                }
        
        result = _audit_result_to_dict(MockResult())
        
        assert result["audit_id"] == "audit_123"
        assert result["screen_id"] == "screen_abc"
        assert result["status"] == "completed"
        assert result["total_findings"] == 5
    
    def test_audit_result_to_dict_with_dict(self):
        """Test conversion of dict result."""
        from src.cli.commands.audit import _audit_result_to_dict
        
        result_dict = {
            "id": "audit_456",
            "screen_id": "screen_xyz",
        }
        
        result = _audit_result_to_dict(result_dict)
        
        assert result["audit_id"] == "audit_456"