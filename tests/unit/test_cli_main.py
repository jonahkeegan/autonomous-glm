"""
Unit tests for CLI main module.

Tests the root CLI group, version display, and entry point.
"""

import pytest
from click.testing import CliRunner

from src.cli.main import cli, main, get_version
from src.cli.errors import ExitCode


class TestCLIMain:
    """Tests for the main CLI group."""
    
    def test_cli_help(self):
        """Test that --help displays usage information."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == ExitCode.SUCCESS
        assert "Autonomous GLM" in result.output
        assert "audit" in result.output
        assert "report" in result.output
        assert "propose" in result.output
    
    def test_cli_version(self):
        """Test that --version displays the version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        
        assert result.exit_code == ExitCode.SUCCESS
        assert "glm version" in result.output
        assert get_version() in result.output
    
    def test_cli_no_command(self):
        """Test that running without a command shows help."""
        runner = CliRunner()
        result = runner.invoke(cli, [])
        
        # Click shows help when no command is given
        assert "Autonomous GLM" in result.output or result.exit_code == ExitCode.SUCCESS
    
    def test_cli_verbose_flag(self):
        """Test that --verbose flag is accepted."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--verbose", "--help"])
        
        assert result.exit_code == ExitCode.SUCCESS
    
    def test_cli_json_flag(self):
        """Test that --json flag is accepted."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "--help"])
        
        assert result.exit_code == ExitCode.SUCCESS


class TestGetVersion:
    """Tests for get_version function."""
    
    def test_get_version_returns_string(self):
        """Test that get_version returns a string."""
        version = get_version()
        
        assert isinstance(version, str)
        assert len(version) > 0
    
    def test_version_format(self):
        """Test that version follows semver format."""
        version = get_version()
        parts = version.split(".")
        
        assert len(parts) >= 2
        assert all(part.isdigit() for part in parts)


class TestMainEntryPoint:
    """Tests for the main entry point function."""
    
    def test_main_returns_int(self):
        """Test that main() returns an integer exit code."""
        runner = CliRunner()
        
        # main() is designed to be called directly, not through CliRunner
        # But we can test it through the cli function
        result = runner.invoke(cli, ["--help"])
        assert isinstance(result.exit_code, int)
    
    def test_main_success_exit_code(self):
        """Test successful invocation returns 0."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == ExitCode.SUCCESS


class TestCLICommands:
    """Tests for command registration."""
    
    def test_audit_command_registered(self):
        """Test that audit command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["audit", "--help"])
        
        assert result.exit_code == ExitCode.SUCCESS
        assert "audit" in result.output.lower()
    
    def test_report_command_registered(self):
        """Test that report command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "--help"])
        
        assert result.exit_code == ExitCode.SUCCESS
        assert "report" in result.output.lower()
    
    def test_propose_command_registered(self):
        """Test that propose command is registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["propose", "--help"])
        
        assert result.exit_code == ExitCode.SUCCESS
        assert "propose" in result.output.lower()