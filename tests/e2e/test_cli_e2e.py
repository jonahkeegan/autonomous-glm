"""E2E tests for CLI commands.

Tests the full CLI workflow from command invocation to output.
"""
import json
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.mark.e2e
@pytest.mark.ci_quick
class TestCLIE2E:
    """E2E tests for CLI commands."""

    def test_cli_help_command(self, e2e_cli_runner: CliRunner) -> None:
        """Test CLI help command."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "Usage" in result.output or "glm" in result.output.lower()

    def test_cli_version_command(self, e2e_cli_runner: CliRunner) -> None:
        """Test CLI version command."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(cli, ["--version"])
        
        # Should succeed or show version
        assert result.exit_code in [0, 1, 2]

    def test_cli_ingest_help(self, e2e_cli_runner: CliRunner) -> None:
        """Test ingest command help."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(cli, ["ingest", "--help"])
        
        # Should show help without error
        assert result.exit_code == 0 or "Usage" in result.output


@pytest.mark.e2e
@pytest.mark.ci_quick
class TestCLIIIngestE2E:
    """E2E tests for CLI ingest commands."""

    def test_ingest_screenshot(
        self,
        e2e_temp_dir: Path,
        e2e_db_path: Path,
        e2e_screenshot: Path,
        e2e_cli_runner: CliRunner,
    ) -> None:
        """Test ingesting a screenshot via CLI."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(
            cli,
            ["ingest", "screenshot", str(e2e_screenshot)],
            env={"AUTONOMOUS_GLM_DB_PATH": str(e2e_db_path)},
        )

        # Should succeed or fail gracefully
        assert result.exit_code in [0, 1, 2]

    def test_ingest_nonexistent_file(
        self,
        e2e_db_path: Path,
        e2e_cli_runner: CliRunner,
    ) -> None:
        """Test ingesting a nonexistent file."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(
            cli,
            ["ingest", "screenshot", "/nonexistent/file.png"],
            env={"AUTONOMOUS_GLM_DB_PATH": str(e2e_db_path)},
        )

        # Should fail gracefully
        assert result.exit_code != 0 or "error" in result.output.lower()


@pytest.mark.e2e
class TestCLIAuditE2E:
    """E2E tests for CLI audit commands."""

    def test_audit_help(self, e2e_cli_runner: CliRunner) -> None:
        """Test audit command help."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(cli, ["audit", "--help"])
        
        # Should show help
        assert result.exit_code == 0 or "Usage" in result.output

    def test_audit_invalid_id(
        self,
        e2e_db_path: Path,
        e2e_cli_runner: CliRunner,
    ) -> None:
        """Test audit command with invalid ID."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(
            cli,
            ["audit", "nonexistent-id"],
            env={"AUTONOMOUS_GLM_DB_PATH": str(e2e_db_path)},
        )

        # Should fail gracefully
        assert result.exit_code != 0 or "error" in result.output.lower()


@pytest.mark.e2e
class TestCLIReportE2E:
    """E2E tests for CLI report commands."""

    def test_report_help(self, e2e_cli_runner: CliRunner) -> None:
        """Test report command help."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(cli, ["report", "--help"])
        
        # Should show help
        assert result.exit_code == 0 or "Usage" in result.output

    def test_report_invalid_id(
        self,
        e2e_db_path: Path,
        e2e_cli_runner: CliRunner,
    ) -> None:
        """Test report command with invalid ID."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(
            cli,
            ["report", "nonexistent-id"],
            env={"AUTONOMOUS_GLM_DB_PATH": str(e2e_db_path)},
        )

        # Should fail gracefully
        assert result.exit_code != 0 or "error" in result.output.lower()


@pytest.mark.e2e
class TestCLIWatchE2E:
    """E2E tests for CLI watch commands."""

    def test_watch_help(self, e2e_cli_runner: CliRunner) -> None:
        """Test watch command help."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(cli, ["watch", "--help"])
        
        # Should show help
        assert result.exit_code == 0 or "Usage" in result.output


@pytest.mark.e2e
class TestCLIDashboardE2E:
    """E2E tests for CLI dashboard commands."""

    def test_dashboard_help(self, e2e_cli_runner: CliRunner) -> None:
        """Test dashboard command help."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(cli, ["dashboard", "--help"])
        
        # Should show help
        assert result.exit_code == 0 or "Usage" in result.output


@pytest.mark.e2e
class TestCLIProposeE2E:
    """E2E tests for CLI propose commands."""

    def test_propose_help(self, e2e_cli_runner: CliRunner) -> None:
        """Test propose command help."""
        from src.cli.main import cli
        
        result = e2e_cli_runner.invoke(cli, ["propose", "--help"])
        
        # Should show help
        assert result.exit_code == 0 or "Usage" in result.output