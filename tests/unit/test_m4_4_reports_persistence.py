"""
Unit tests for M4-4: Reports Generation & Persistence.

Tests the report models, markdown generation, JSON output,
persistence, and report writer functionality.
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

# Import the modules under test
from src.plan.report_models import (
    ReportType,
    ReportMetadata,
    AuditSummaryReport,
    ImplementationPlanReport,
    DesignProposalReport,
    FullReport,
    FindingsSummary,
    InstructionsSummary,
    ProposalsSummary,
)
from src.plan.markdown import (
    MarkdownGenerator,
    generate_audit_summary_markdown,
)
from src.plan.json_output import (
    JsonGenerator,
    generate_agent_payload,
    generate_findings_json,
)
from src.plan.persistence import (
    PlanPersistence,
    save_plan,
    get_plan,
)
from src.plan.report_writer import (
    ReportWriter,
    generate_report_filename,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_metadata():
    """Create sample report metadata."""
    return ReportMetadata(
        id=str(uuid4()),
        report_type=ReportType.FULL_REPORT,
        audit_session_id="session-123",
        screen_id="screen-456",
        version="1.0.0",
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_findings_summary():
    """Create sample findings summary stats."""
    return FindingsSummary(
        total_findings=10,
        critical_count=2,
        high_count=3,
        by_severity={"low": 1, "medium": 4, "high": 3, "critical": 2},
        by_dimension={"accessibility": 5, "typography": 3, "visual_hierarchy": 2},
    )


@pytest.fixture
def sample_findings():
    """Create sample findings for testing."""
    return [
        {
            "id": "finding-1",
            "severity": "critical",
            "dimension": "accessibility",
            "issue": "Color contrast too low",
            "rationale": "WCAG 2.1 AA requires 4.5:1 ratio",
        },
        {
            "id": "finding-2",
            "severity": "high",
            "dimension": "visual_hierarchy",
            "issue": "Missing visual hierarchy",
            "rationale": "No clear focal point",
        },
        {
            "id": "finding-3",
            "severity": "medium",
            "dimension": "typography",
            "issue": "Font size too small",
            "rationale": "Minimum 16px for body text",
        },
    ]


@pytest.fixture
def sample_instructions_summary():
    """Create sample implementation summary."""
    return InstructionsSummary(
        total_instructions=15,
        by_phase={"critical": 2, "refinement": 8, "polish": 5},
        high_confidence_count=10,
        requires_inspection_count=5,
    )


@pytest.fixture
def sample_proposals_summary():
    """Create sample proposal summary."""
    return ProposalsSummary(
        total_proposals=5,
        token_proposals=3,
        component_proposals=2,
        by_priority={"high": 2, "medium": 3},
    )


@pytest.fixture
def sample_audit_report(sample_metadata, sample_findings_summary, sample_findings):
    """Create sample audit summary report."""
    return AuditSummaryReport(
        metadata=sample_metadata,
        summary=sample_findings_summary,
        findings_by_severity={
            "critical": sample_findings[:1],
            "high": sample_findings[1:2],
            "medium": sample_findings[2:],
        },
        findings_by_dimension={
            "accessibility": sample_findings[:1],
            "visual_hierarchy": sample_findings[1:2],
            "typography": sample_findings[2:],
        },
        top_issues=sample_findings,
        standards_violated=["WCAG 2.1 AA", "Design System Tokens"],
    )


@pytest.fixture
def sample_implementation_report(sample_metadata, sample_instructions_summary):
    """Create sample implementation plan report."""
    return ImplementationPlanReport(
        metadata=sample_metadata,
        summary=sample_instructions_summary,
        phases={
            "critical": [
                {"target_entity": "button-primary", "property": "color", "new_value": "#0000FF"}
            ],
            "refinement": [
                {"target_entity": "header", "property": "padding", "new_value": "24px"}
            ],
            "polish": [
                {"target_entity": "footer", "property": "margin", "new_value": "16px"}
            ],
        },
        all_instructions=[
            {"sequence": 1, "target_entity": "button-primary", "property": "color"},
            {"sequence": 2, "target_entity": "header", "property": "padding"},
        ],
        estimated_effort="medium",
    )


@pytest.fixture
def sample_proposal_report(sample_metadata, sample_proposals_summary):
    """Create sample design proposal report."""
    return DesignProposalReport(
        metadata=sample_metadata,
        summary=sample_proposals_summary,
        token_proposals=[
            {
                "token_name": "color-primary",
                "token_type": "color",
                "proposed_value": "#0066CC",
                "rationale": "Brand primary color",
            }
        ],
        component_proposals=[
            {
                "component_type": "Button",
                "variant_name": "primary",
                "detected_instances": 5,
                "rationale": "Consistent primary buttons",
            }
        ],
        before_after_descriptions={
            "button-primary": {
                "before_text": "Blue button with low contrast",
                "after_text": "High contrast accessible button",
                "benefit": "Improved accessibility",
            }
        },
        requires_human_approval=True,
    )


@pytest.fixture
def sample_full_report(
    sample_metadata,
    sample_findings_summary,
    sample_instructions_summary,
    sample_proposals_summary,
    sample_audit_report,
    sample_implementation_report,
    sample_proposal_report,
):
    """Create sample full report."""
    return FullReport(
        metadata=sample_metadata,
        audit_summary=sample_audit_report,
        implementation_plan=sample_implementation_report,
        design_proposals=sample_proposal_report,
        overall_summary={
            "total_findings": 10,
            "total_proposals": 5,
            "estimated_effort": "medium",
        },
    )


# =============================================================================
# REPORT MODELS TESTS
# =============================================================================

class TestReportModels:
    """Tests for report model classes."""
    
    def test_report_type_enum_values(self):
        """Test ReportType enum has expected values."""
        assert ReportType.AUDIT_SUMMARY.value == "audit_summary"
        assert ReportType.IMPLEMENTATION_PLAN.value == "implementation_plan"
        assert ReportType.DESIGN_PROPOSAL.value == "design_proposal"
        assert ReportType.FULL_REPORT.value == "full_report"
    
    def test_report_metadata_creation(self, sample_metadata):
        """Test ReportMetadata creation."""
        assert sample_metadata.id is not None
        assert sample_metadata.report_type == ReportType.FULL_REPORT
        assert sample_metadata.version == "1.0.0"
        assert sample_metadata.audit_session_id == "session-123"
    
    def test_report_metadata_defaults(self):
        """Test ReportMetadata default values."""
        metadata = ReportMetadata(
            id=str(uuid4()),
            report_type=ReportType.AUDIT_SUMMARY,
        )
        assert metadata.version == "1.0.0"
        assert metadata.generator == "autonomous-glm"
        assert metadata.audit_session_id is None
    
    def test_findings_summary_defaults(self):
        """Test FindingsSummary default values."""
        summary = FindingsSummary()
        assert summary.total_findings == 0
        assert summary.critical_count == 0
        assert summary.has_critical_issues == False
    
    def test_instructions_summary_defaults(self):
        """Test InstructionsSummary default values."""
        summary = InstructionsSummary()
        assert summary.total_instructions == 0
        assert summary.high_confidence_count == 0
        assert summary.requires_inspection_count == 0
    
    def test_proposals_summary_defaults(self):
        """Test ProposalsSummary default values."""
        summary = ProposalsSummary()
        assert summary.total_proposals == 0
        assert summary.token_proposals == 0
        assert summary.component_proposals == 0
    
    def test_audit_summary_report_creation(self, sample_audit_report):
        """Test AuditSummaryReport creation."""
        assert sample_audit_report.metadata is not None
        assert sample_audit_report.summary.total_findings == 10
        assert len(sample_audit_report.findings_by_severity) == 3
        assert len(sample_audit_report.standards_violated) == 2
    
    def test_implementation_plan_report_creation(self, sample_implementation_report):
        """Test ImplementationPlanReport creation."""
        assert sample_implementation_report.metadata is not None
        assert sample_implementation_report.summary.total_instructions == 15
        assert len(sample_implementation_report.phases) == 3
    
    def test_design_proposal_report_creation(self, sample_proposal_report):
        """Test DesignProposalReport creation."""
        assert sample_proposal_report.metadata is not None
        assert sample_proposal_report.summary.total_proposals == 5
        assert len(sample_proposal_report.token_proposals) == 1
        assert len(sample_proposal_report.component_proposals) == 1
    
    def test_full_report_creation(self, sample_full_report):
        """Test FullReport creation."""
        assert sample_full_report.metadata is not None
        assert sample_full_report.audit_summary is not None
        assert sample_full_report.implementation_plan is not None
        assert sample_full_report.design_proposals is not None
        assert sample_full_report.overall_summary is not None
    
    def test_full_report_to_json_dict(self, sample_full_report):
        """Test FullReport JSON serialization."""
        json_dict = sample_full_report.to_json_dict()
        
        assert "metadata" in json_dict
        assert "audit_summary" in json_dict
        assert "implementation_plan" in json_dict
        assert "design_proposals" in json_dict
        assert "overall_summary" in json_dict
        
        # Verify nested structure
        assert json_dict["metadata"]["id"] == sample_full_report.metadata.id
        assert json_dict["metadata"]["report_type"] == "full_report"


# =============================================================================
# MARKDOWN GENERATOR TESTS
# =============================================================================

class TestMarkdownGenerator:
    """Tests for MarkdownGenerator class."""
    
    def test_generator_initialization(self):
        """Test MarkdownGenerator initialization."""
        generator = MarkdownGenerator()
        assert generator.include_timestamps == True
        assert generator.include_toc == True
        assert generator.max_table_rows == 50
    
    def test_generator_custom_options(self):
        """Test MarkdownGenerator with custom options."""
        generator = MarkdownGenerator(
            include_timestamps=False,
            include_toc=False,
            max_table_rows=25,
        )
        assert generator.include_timestamps == False
        assert generator.include_toc == False
        assert generator.max_table_rows == 25
    
    def test_format_finding_table_empty(self):
        """Test format_finding_table with empty list."""
        generator = MarkdownGenerator()
        result = generator.format_finding_table([])
        assert "No findings" in result
    
    def test_format_finding_table_with_data(self):
        """Test format_finding_table with findings."""
        generator = MarkdownGenerator()
        findings = [
            {"severity": "high", "dimension": "accessibility", "issue": "Contrast low"},
            {"severity": "medium", "dimension": "typography", "issue": "Font small"},
        ]
        result = generator.format_finding_table(findings)
        
        assert "| # | Severity | Dimension | Issue |" in result
        assert "| 1 |" in result
        assert "| 2 |" in result
    
    def test_format_finding_table_truncation(self):
        """Test format_finding_table truncates long issues."""
        generator = MarkdownGenerator()
        long_issue = "A" * 100
        findings = [{"severity": "medium", "dimension": "test", "issue": long_issue}]
        result = generator.format_finding_table(findings)
        
        # Should be truncated to 60 chars
        assert len([l for l in result.split("\n") if "AAA" in l][0]) < 150
    
    def test_format_instruction_list_empty(self):
        """Test format_instruction_list with empty list."""
        generator = MarkdownGenerator()
        result = generator.format_instruction_list([])
        assert "No instructions" in result
    
    def test_format_instruction_list_numbered(self):
        """Test format_instruction_list with numbered format."""
        generator = MarkdownGenerator()
        instructions = [
            {"target_entity": "button", "property": "color", "new_value": "#000"},
            {"target_entity": "header", "property": "padding", "new_value": "10px"},
        ]
        result = generator.format_instruction_list(instructions, numbered=True)
        
        assert "1." in result
        assert "2." in result
    
    def test_format_instruction_list_bulleted(self):
        """Test format_instruction_list with bulleted format."""
        generator = MarkdownGenerator()
        instructions = [
            {"target_entity": "button", "property": "color"},
        ]
        result = generator.format_instruction_list(instructions, numbered=False)
        
        assert "- " in result
        assert "1." not in result
    
    def test_generate_audit_summary_report(self, sample_audit_report):
        """Test generate_audit_summary method."""
        generator = MarkdownGenerator()
        result = generator.generate_audit_summary(sample_audit_report)
        
        assert "# Audit Summary Report" in result
        assert "**Report ID:**" in result
        assert "## Summary" in result
        assert "## Findings by Severity" in result
    
    def test_generate_implementation_plan_report(self, sample_implementation_report):
        """Test generate_implementation_plan method."""
        generator = MarkdownGenerator()
        result = generator.generate_implementation_plan(sample_implementation_report)
        
        assert "# Implementation Plan Report" in result
        assert "## Phase 1: Critical" in result
        assert "## Phase 2: Refinement" in result
        assert "## Phase 3: Polish" in result
    
    def test_generate_design_proposals_report(self, sample_proposal_report):
        """Test generate_design_proposals method."""
        generator = MarkdownGenerator()
        result = generator.generate_design_proposals(sample_proposal_report)
        
        assert "# Design System Proposal Report" in result
        assert "## Token Proposals" in result
        assert "## Component Proposals" in result
        assert "Human Approval Required" in result
    
    def test_generate_full_report(self, sample_full_report):
        """Test generate_full_report method."""
        generator = MarkdownGenerator()
        result = generator.generate_full_report(sample_full_report)
        
        assert "# Full Audit Report" in result
        assert "## Overview" in result
        assert "# Audit Summary" in result
        assert "# Implementation Plan" in result
        assert "# Design Proposals" in result


# =============================================================================
# JSON GENERATOR TESTS
# =============================================================================

class TestJsonGenerator:
    """Tests for JsonGenerator class."""
    
    def test_generator_initialization(self):
        """Test JsonGenerator initialization."""
        generator = JsonGenerator()
        assert generator.validate_schemas in [True, False]  # Depends on jsonschema
    
    def test_generate_agent_payload(self):
        """Test generate_agent_payload method."""
        generator = JsonGenerator()
        
        # Mock plan object
        plan = Mock()
        plan.screen_id = "screen-123"
        plan.audit_session_id = "session-456"
        plan.phases = []
        plan.summary = Mock(critical_count=2)
        
        result = generator.generate_agent_payload(plan)
        
        assert result["source_agent"] == "autonomous-glm"
        assert result["target_agent"] == "claude"
        assert result["message_type"] == "AUDIT_COMPLETE"
        assert "message_id" in result
        assert "timestamp" in result
    
    def test_generate_findings_json(self):
        """Test generate_findings_json method."""
        generator = JsonGenerator()
        
        findings = [
            Mock(model_dump=Mock(return_value={
                "id": "finding-1",
                "severity": "high",
                "dimension": "accessibility",
                "issue": "Test issue",
            }))
        ]
        
        result = generator.generate_findings_json(findings)
        
        assert len(result) == 1
        assert result[0]["severity"] == "high"
    
    def test_generate_instructions_json(self):
        """Test generate_instructions_json method."""
        generator = JsonGenerator()
        
        instructions = [
            Mock(model_dump=Mock(return_value={
                "target_file": "test.css",
                "component": {"name": "button"},
                "property": "color",
                "new_value": "#000",
                "confidence": 0.9,
            }))
        ]
        
        result = generator.generate_instructions_json(instructions)
        
        assert len(result) == 1
        assert result[0]["sequence"] == 1
        assert result[0]["target_file"] == "test.css"


# =============================================================================
# REPORT WRITER TESTS
# =============================================================================

class TestReportWriter:
    """Tests for ReportWriter class."""
    
    def test_writer_initialization(self, tmp_path):
        """Test ReportWriter initialization."""
        writer = ReportWriter(output_dir=tmp_path)
        assert writer.output_dir == tmp_path
        assert writer.date_based_dirs == True
        assert writer.write_json == True
        assert writer.write_markdown == True
    
    def test_generate_report_filename(self):
        """Test generate_report_filename method."""
        writer = ReportWriter()
        
        filename = writer.generate_report_filename(
            ReportType.AUDIT_SUMMARY,
            "12345678-1234-5678-1234-567812345678",
            "md"
        )
        
        assert filename.startswith("audit_summary_")
        assert filename.endswith(".md")
    
    def test_generate_report_filename_json(self):
        """Test generate_report_filename for JSON."""
        writer = ReportWriter()
        
        filename = writer.generate_report_filename(
            ReportType.FULL_REPORT,
            "12345678-1234-5678-1234-567812345678",
            "json"
        )
        
        assert filename.startswith("full_report_")
        assert filename.endswith(".json")
    
    def test_write_markdown_report(self, sample_full_report, tmp_path):
        """Test write_markdown_report method."""
        writer = ReportWriter(output_dir=tmp_path, date_based_dirs=False)
        
        file_path = writer.write_markdown_report(sample_full_report)
        
        assert Path(file_path).exists()
        content = Path(file_path).read_text()
        assert "# Full Audit Report" in content
    
    def test_write_json_report(self, sample_full_report, tmp_path):
        """Test write_json_report method."""
        writer = ReportWriter(output_dir=tmp_path, date_based_dirs=False)
        
        file_path = writer.write_json_report(sample_full_report)
        
        assert Path(file_path).exists()
        content = Path(file_path).read_text()
        data = json.loads(content)
        assert "metadata" in data
    
    def test_write_report_both_formats(self, sample_full_report, tmp_path):
        """Test write_report method with both formats."""
        writer = ReportWriter(output_dir=tmp_path, date_based_dirs=False)
        
        paths = writer.write_report(sample_full_report)
        
        assert "markdown" in paths
        assert "json" in paths
        assert Path(paths["markdown"]).exists()
        assert Path(paths["json"]).exists()
    
    def test_date_based_directory_creation(self, sample_full_report, tmp_path):
        """Test that date-based directories are created."""
        writer = ReportWriter(output_dir=tmp_path, date_based_dirs=True)
        
        file_path = writer.write_markdown_report(sample_full_report)
        
        # Check that path contains date directory
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        assert date_str in file_path


# =============================================================================
# PERSISTENCE TESTS
# =============================================================================

class TestPlanPersistence:
    """Tests for PlanPersistence class."""
    
    def test_persistence_initialization(self):
        """Test PlanPersistence initialization."""
        persistence = PlanPersistence()
        assert persistence.db_path is None
    
    def test_persistence_custom_db_path(self, tmp_path):
        """Test PlanPersistence with custom db path."""
        db_path = tmp_path / "test.db"
        persistence = PlanPersistence(db_path=db_path)
        assert persistence.db_path == db_path


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_generate_report_filename_function(self):
        """Test generate_report_filename function."""
        filename = generate_report_filename(
            ReportType.IMPLEMENTATION_PLAN,
            "12345678-1234-5678-1234-567812345678",
            "json"
        )
        
        assert filename.startswith("implementation_plan_")
        assert filename.endswith(".json")
    
    def test_generate_agent_payload_function(self):
        """Test generate_agent_payload function."""
        plan = Mock()
        plan.screen_id = "screen-123"
        plan.audit_session_id = "session-456"
        plan.phases = []
        plan.summary = None
        
        result = generate_agent_payload(plan)
        
        assert result["source_agent"] == "autonomous-glm"
        assert "message_id" in result
    
    def test_generate_findings_json_function(self):
        """Test generate_findings_json function."""
        findings = [
            {"severity": "high", "issue": "Test"}
        ]
        
        result = generate_findings_json(findings)
        
        assert len(result) == 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the complete workflow."""
    
    def test_full_report_workflow(self, sample_full_report, tmp_path):
        """Test complete workflow from report creation to file output."""
        # 1. Create writer
        writer = ReportWriter(output_dir=tmp_path, date_based_dirs=False)
        
        # 2. Write report in both formats
        paths = writer.write_report(sample_full_report)
        
        # 3. Verify markdown
        md_content = Path(paths["markdown"]).read_text()
        assert "# Full Audit Report" in md_content
        assert "Audit Summary" in md_content
        assert "Implementation Plan" in md_content
        
        # 4. Verify JSON
        json_content = Path(paths["json"]).read_text()
        data = json.loads(json_content)
        assert data["metadata"]["report_type"] == "full_report"
    
    def test_report_types_generate_correct_prefixes(self):
        """Test that different report types generate correct filename prefixes."""
        writer = ReportWriter()
        
        prefixes = {
            ReportType.AUDIT_SUMMARY: "audit_summary",
            ReportType.IMPLEMENTATION_PLAN: "implementation_plan",
            ReportType.DESIGN_PROPOSAL: "design_proposals",
            ReportType.FULL_REPORT: "full_report",
        }
        
        for report_type, expected_prefix in prefixes.items():
            filename = writer.generate_report_filename(
                report_type, "12345678-1234", "md"
            )
            assert filename.startswith(expected_prefix), \
                f"Expected {expected_prefix} prefix for {report_type}"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_findings_table(self):
        """Test handling of empty findings."""
        generator = MarkdownGenerator()
        result = generator.format_finding_table([])
        assert "No findings" in result
    
    def test_empty_instructions_list(self):
        """Test handling of empty instructions."""
        generator = MarkdownGenerator()
        result = generator.format_instruction_list([])
        assert "No instructions" in result
    
    def test_very_long_issue_description(self):
        """Test truncation of very long issue descriptions."""
        generator = MarkdownGenerator()
        findings = [{
            "severity": "medium",
            "dimension": "test",
            "issue": "A" * 200  # Very long issue
        }]
        result = generator.format_finding_table(findings)
        # Should be truncated with ellipsis
        assert "..." in result
    
    def test_special_characters_in_findings(self):
        """Test handling of special characters in findings."""
        generator = MarkdownGenerator()
        findings = [{
            "severity": "medium",
            "dimension": "test",
            "issue": "Test | pipe | characters"
        }]
        result = generator.format_finding_table(findings)
        # Pipe characters should be escaped
        assert "\\|" in result
    
    def test_report_with_no_phases(self, sample_metadata, sample_instructions_summary):
        """Test implementation report with empty phases."""
        report = ImplementationPlanReport(
            metadata=sample_metadata,
            summary=sample_instructions_summary,
            phases={},  # Empty phases
            all_instructions=[],
            estimated_effort="low",
        )
        
        generator = MarkdownGenerator()
        result = generator.generate_implementation_plan(report)
        
        assert "No critical phase instructions" in result
        assert "No refinement phase instructions" in result
        assert "No polish phase instructions" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])