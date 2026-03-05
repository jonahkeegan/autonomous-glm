"""
Unit tests for CLI formatters.

Tests the output formatting utilities.
"""

import pytest
from datetime import datetime

from src.cli.formatters import (
    format_json,
    output_json,
    create_table,
    format_audit_summary,
    format_findings_table,
    format_report_summary,
    format_reports_table,
    format_proposals_table,
    format_proposal_detail,
    _format_status,
    _get_severity_style,
    _get_status_style,
)


class TestFormatJson:
    """Tests for format_json function."""
    
    def test_format_simple_dict(self):
        """Test formatting a simple dictionary."""
        data = {"key": "value"}
        result = format_json(data)
        
        assert '"key": "value"' in result
    
    def test_format_with_datetime(self):
        """Test formatting with datetime object."""
        data = {"timestamp": datetime(2024, 1, 1, 12, 0, 0)}
        result = format_json(data)
        
        assert "2024-01-01T12:00:00" in result
    
    def test_format_with_pydantic_model(self):
        """Test formatting with Pydantic-like model."""
        class MockModel:
            def model_dump(self):
                return {"id": "123", "name": "Test"}
        
        data = {"model": MockModel()}
        result = format_json(data)
        
        assert '"id": "123"' in result
        assert '"name": "Test"' in result
    
    def test_format_nested_structure(self):
        """Test formatting nested structures."""
        data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        result = format_json(data)
        
        assert '"level3": "value"' in result


class TestCreateTable:
    """Tests for create_table function."""
    
    def test_create_simple_table(self):
        """Test creating a simple table."""
        table = create_table(
            title="Test Table",
            columns=["Col1", "Col2"],
            rows=[["A", "B"], ["C", "D"]],
        )
        
        # Table should be a Rich Table object
        assert table.title == "Test Table"
        assert len(table.columns) == 2
    
    def test_create_table_with_none_values(self):
        """Test creating a table with None values."""
        table = create_table(
            title="Test",
            columns=["A", "B"],
            rows=[["value", None]],
        )
        
        # Should handle None gracefully
        assert table is not None


class TestFormatAuditSummary:
    """Tests for format_audit_summary function."""
    
    def test_format_basic_summary(self):
        """Test formatting basic audit summary."""
        table = format_audit_summary(
            audit_id="audit_123",
            screen_id="screen_abc",
            status="completed",
            total_findings=10,
            by_severity={"critical": 2, "high": 3, "medium": 3, "low": 2},
        )
        
        assert table is not None
        assert table.title == "Audit Summary"
    
    def test_format_summary_with_duration(self):
        """Test formatting summary with duration."""
        table = format_audit_summary(
            audit_id="audit_123",
            screen_id="screen_abc",
            status="completed",
            total_findings=5,
            by_severity={},
            duration_ms=1234.5,
        )
        
        assert table is not None


class TestFormatFindingsTable:
    """Tests for format_findings_table function."""
    
    def test_format_empty_findings(self):
        """Test formatting empty findings list."""
        table = format_findings_table([])
        
        assert table is not None
    
    def test_format_multiple_findings(self):
        """Test formatting multiple findings."""
        findings = [
            {"id": "f1", "dimension": "typography", "severity": "high", "title": "Test 1"},
            {"id": "f2", "dimension": "color", "severity": "medium", "title": "Test 2"},
        ]
        
        table = format_findings_table(findings)
        
        assert table is not None


class TestFormatReportSummary:
    """Tests for format_report_summary function."""
    
    def test_format_basic_report(self):
        """Test formatting basic report summary."""
        table = format_report_summary(
            report_id="report_123",
            audit_id="audit_abc",
            phases={"Critical": 5, "Refinement": 10},
            created_at="2024-01-01T00:00:00",
        )
        
        assert table is not None
        assert table.title == "Report Summary"
    
    def test_format_report_with_output_path(self):
        """Test formatting report with output path."""
        table = format_report_summary(
            report_id="report_123",
            audit_id="audit_abc",
            phases={},
            created_at="2024-01-01",
            output_path="/path/to/report.md",
        )
        
        assert table is not None


class TestFormatProposalsTable:
    """Tests for format_proposals_table function."""
    
    def test_format_empty_proposals(self):
        """Test formatting empty proposals list."""
        table = format_proposals_table([])
        
        assert table is not None
    
    def test_format_multiple_proposals(self):
        """Test formatting multiple proposals."""
        proposals = [
            {"id": "p1", "change_type": "token", "target": "spacing.md", "status": "pending", "priority": "high"},
            {"id": "p2", "change_type": "component", "target": "Button", "status": "approved", "priority": "medium"},
        ]
        
        table = format_proposals_table(proposals)
        
        assert table is not None


class TestFormatProposalDetail:
    """Tests for format_proposal_detail function."""
    
    def test_format_basic_proposal(self):
        """Test formatting basic proposal."""
        panel = format_proposal_detail({
            "id": "prop_123",
            "change_type": "token",
            "target": "spacing.md",
            "status": "pending",
            "priority": "high",
        })
        
        assert panel is not None
    
    def test_format_proposal_with_diff(self):
        """Test formatting proposal with before/after."""
        panel = format_proposal_detail({
            "id": "prop_123",
            "change_type": "token",
            "target": "spacing.md",
            "status": "pending",
            "priority": "high",
            "before": "8px",
            "after": "12px",
            "rationale": "Improve readability",
        })
        
        assert panel is not None


class TestStatusFormatting:
    """Tests for status formatting helpers."""
    
    def test_format_status_completed(self):
        """Test formatting completed status."""
        result = _format_status("completed")
        assert "green" in result
        assert "completed" in result
    
    def test_format_status_running(self):
        """Test formatting running status."""
        result = _format_status("running")
        assert "yellow" in result
    
    def test_format_status_failed(self):
        """Test formatting failed status."""
        result = _format_status("failed")
        assert "red" in result
    
    def test_format_status_unknown(self):
        """Test formatting unknown status."""
        result = _format_status("unknown_status")
        assert "unknown_status" in result


class TestSeverityStyles:
    """Tests for severity style helpers."""
    
    def test_critical_style(self):
        """Test critical severity style."""
        style = _get_severity_style("critical")
        assert "bold red" == style
    
    def test_high_style(self):
        """Test high severity style."""
        style = _get_severity_style("high")
        assert "red" == style
    
    def test_medium_style(self):
        """Test medium severity style."""
        style = _get_severity_style("medium")
        assert "yellow" == style
    
    def test_low_style(self):
        """Test low severity style."""
        style = _get_severity_style("low")
        assert "green" == style


class TestProposalStatusStyles:
    """Tests for proposal status style helpers."""
    
    def test_approved_style(self):
        """Test approved status style."""
        style = _get_status_style("approved")
        assert "green" == style
    
    def test_pending_style(self):
        """Test pending status style."""
        style = _get_status_style("pending")
        assert "yellow" == style
    
    def test_rejected_style(self):
        """Test rejected status style."""
        style = _get_status_style("rejected")
        assert "red" == style
    
    def test_implemented_style(self):
        """Test implemented status style."""
        style = _get_status_style("implemented")
        assert "cyan" == style