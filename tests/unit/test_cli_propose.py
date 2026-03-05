"""
Unit tests for CLI propose command.

Tests the propose command options, validation, and output.
"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from src.cli.main import cli
from src.cli.errors import ExitCode


class TestProposeCommand:
    """Tests for the propose command."""
    
    def test_propose_help(self):
        """Test that propose --help displays usage information."""
        runner = CliRunner()
        result = runner.invoke(cli, ["propose", "--help"])
        
        assert result.exit_code == ExitCode.SUCCESS
        assert "PROPOSAL_ID" in result.output
        assert "--diff" in result.output
        assert "--status" in result.output
        assert "--json" in result.output
        assert "--approve" in result.output
        assert "--reject" in result.output
    
    @patch("src.cli.commands.propose._list_proposals")
    def test_propose_list_all(self, mock_list_proposals):
        """Test listing all proposals."""
        mock_list_proposals.return_value = None  # Function prints directly
        
        runner = CliRunner()
        result = runner.invoke(cli, ["propose"])
        
        mock_list_proposals.assert_called_once()
    
    @patch("src.cli.commands.propose._list_proposals")
    def test_propose_list_with_status_filter(self, mock_list_proposals):
        """Test listing proposals with status filter."""
        mock_list_proposals.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ["propose", "--status", "pending"])
        
        mock_list_proposals.assert_called_once_with(status="pending", use_json=False)
    
    @patch("src.cli.commands.propose._show_proposal")
    def test_propose_view_specific(self, mock_show_proposal):
        """Test viewing a specific proposal."""
        mock_show_proposal.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ["propose", "proposal_123"])
        
        mock_show_proposal.assert_called_once_with(
            "proposal_123",
            show_diff=False,
            use_json=False,
        )
    
    @patch("src.cli.commands.propose._show_proposal")
    def test_propose_view_with_diff(self, mock_show_proposal):
        """Test viewing a proposal with diff."""
        mock_show_proposal.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ["propose", "proposal_123", "--diff"])
        
        mock_show_proposal.assert_called_once_with(
            "proposal_123",
            show_diff=True,
            use_json=False,
        )
    
    @patch("src.cli.commands.propose._list_proposals")
    def test_propose_json_output(self, mock_list_proposals):
        """Test propose with JSON output flag."""
        mock_list_proposals.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ["propose", "--json"])
        
        mock_list_proposals.assert_called_once()
        call_args = mock_list_proposals.call_args
        assert call_args[1]["use_json"] is True


class TestProposeStatusChanges:
    """Tests for proposal status changes."""
    
    @patch("src.cli.commands.propose._update_proposal_status")
    def test_propose_approve(self, mock_update_status):
        """Test approving a proposal."""
        mock_update_status.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ["propose", "proposal_123", "--approve"])
        
        mock_update_status.assert_called_once_with("proposal_123", "approved")
    
    @patch("src.cli.commands.propose._update_proposal_status")
    def test_propose_reject(self, mock_update_status):
        """Test rejecting a proposal."""
        mock_update_status.return_value = None
        
        runner = CliRunner()
        result = runner.invoke(cli, ["propose", "proposal_123", "--reject"])
        
        mock_update_status.assert_called_once_with("proposal_123", "rejected")
    
    def test_approve_requires_proposal_id(self):
        """Test that --approve requires a proposal ID."""
        runner = CliRunner()
        result = runner.invoke(cli, ["propose", "--approve"])
        
        assert result.exit_code != ExitCode.SUCCESS
        assert result.exception is not None
    
    def test_reject_requires_proposal_id(self):
        """Test that --reject requires a proposal ID."""
        runner = CliRunner()
        result = runner.invoke(cli, ["propose", "--reject"])
        
        assert result.exit_code != ExitCode.SUCCESS
        assert result.exception is not None


class TestProposeStatusFilter:
    """Tests for status filter choices."""
    
    def test_valid_status_choices(self):
        """Test that valid status choices are accepted."""
        valid_statuses = ["pending", "approved", "rejected", "implemented"]
        
        for status in valid_statuses:
            runner = CliRunner()
            result = runner.invoke(cli, ["propose", "--status", status, "--help"])
            
            # Should not fail with invalid choice
            assert "Invalid value" not in result.output
    
    def test_invalid_status_choice(self):
        """Test that invalid status is rejected."""
        runner = CliRunner()
        result = runner.invoke(cli, ["propose", "--status", "invalid_status"])
        
        # Should fail with invalid choice
        assert result.exit_code != ExitCode.SUCCESS