"""
Report writer for file system output.

Provides functionality for writing reports to the file system in both
Markdown and JSON formats, with date-based directory organization.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.config.paths import get_output_dir
from src.plan.report_models import ReportType, FullReport
from src.plan.markdown import (
    MarkdownGenerator,
    generate_audit_summary_markdown,
    generate_implementation_plan_markdown,
    generate_design_proposals_markdown,
    generate_full_report_markdown,
)
from src.plan.json_output import JsonGenerator


# =============================================================================
# REPORT WRITER CLASS
# =============================================================================

class ReportWriter:
    """Writer for reports to file system.
    
    Writes reports to date-based directories under /output/reports/
    in both Markdown (human-readable) and JSON (agent-consumable) formats.
    """
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        date_based_dirs: bool = True,
        write_json: bool = True,
        write_markdown: bool = True,
    ):
        """Initialize the report writer.
        
        Args:
            output_dir: Base output directory (defaults to /output/reports/)
            date_based_dirs: Whether to organize by date subdirectories
            write_json: Whether to write JSON files
            write_markdown: Whether to write Markdown files
        """
        self.output_dir = output_dir or get_output_dir() / "reports"
        self.date_based_dirs = date_based_dirs
        self.write_json = write_json
        self.write_markdown = write_markdown
        
        self.markdown_generator = MarkdownGenerator()
        self.json_generator = JsonGenerator()
    
    def _get_output_dir(self) -> Path:
        """Get the output directory for today.
        
        Returns:
            Path to output directory (date-based if configured)
        """
        if self.date_based_dirs:
            date_str = datetime.now().strftime("%Y-%m-%d")
            return self.output_dir / date_str
        return self.output_dir
    
    def _ensure_output_dir(self) -> Path:
        """Ensure output directory exists and return it.
        
        Returns:
            Path to output directory
        """
        output_dir = self._get_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def generate_report_filename(
        self,
        report_type: ReportType,
        report_id: str,
        extension: str = "md"
    ) -> str:
        """Generate a standardized report filename.
        
        Args:
            report_type: Type of report
            report_id: Unique report identifier
            extension: File extension (md or json)
        
        Returns:
            Filename string
        """
        type_prefixes = {
            ReportType.AUDIT_SUMMARY: "audit_summary",
            ReportType.IMPLEMENTATION_PLAN: "implementation_plan",
            ReportType.DESIGN_PROPOSAL: "design_proposals",
            ReportType.FULL_REPORT: "full_report",
        }
        
        prefix = type_prefixes.get(report_type, "report")
        return f"{prefix}_{report_id[:8]}.{extension}"
    
    def write_markdown_report(
        self,
        report: Any,
        filename: Optional[str] = None
    ) -> str:
        """Write a Markdown report to the file system.
        
        Args:
            report: Report object (any report type)
            filename: Optional custom filename
        
        Returns:
            Path to the written file
        """
        output_dir = self._ensure_output_dir()
        
        # Generate filename if not provided
        if filename is None:
            filename = self.generate_report_filename(
                report.metadata.report_type,
                report.metadata.id,
                "md"
            )
        
        file_path = output_dir / filename
        
        # Generate markdown content based on report type
        if isinstance(report, FullReport):
            content = self.markdown_generator.generate_full_report(report)
        elif report.metadata.report_type == ReportType.AUDIT_SUMMARY:
            content = self.markdown_generator.generate_audit_summary(report)
        elif report.metadata.report_type == ReportType.IMPLEMENTATION_PLAN:
            content = self.markdown_generator.generate_implementation_plan(report)
        elif report.metadata.report_type == ReportType.DESIGN_PROPOSAL:
            content = self.markdown_generator.generate_design_proposals(report)
        else:
            content = self.markdown_generator.generate_full_report(report)
        
        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(file_path)
    
    def write_json_report(
        self,
        report: Any,
        filename: Optional[str] = None
    ) -> str:
        """Write a JSON report to the file system.
        
        Args:
            report: Report object (any report type)
            filename: Optional custom filename
        
        Returns:
            Path to the written file
        """
        output_dir = self._ensure_output_dir()
        
        # Generate filename if not provided
        if filename is None:
            filename = self.generate_report_filename(
                report.metadata.report_type,
                report.metadata.id,
                "json"
            )
        
        file_path = output_dir / filename
        
        # Generate JSON content
        content = self.json_generator.generate_full_report_json(report)
        
        # Write to file with pretty formatting
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, default=str)
        
        return str(file_path)
    
    def write_report(
        self,
        report: Any,
        write_both: bool = True
    ) -> dict[str, str]:
        """Write a report in all configured formats.
        
        Args:
            report: Report object (any report type)
            write_both: Override to write both formats
        
        Returns:
            Dict mapping format to file path
        """
        paths = {}
        
        if self.write_markdown or write_both:
            paths["markdown"] = self.write_markdown_report(report)
        
        if self.write_json or write_both:
            paths["json"] = self.write_json_report(report)
        
        return paths
    
    # =========================================================================
    # CONVENIENCE METHODS FOR SPECIFIC REPORT TYPES
    # =========================================================================
    
    def write_audit_summary(
        self,
        report: Any
    ) -> dict[str, str]:
        """Write an audit summary report.
        
        Args:
            report: AuditSummaryReport object
        
        Returns:
            Dict mapping format to file path
        """
        return self.write_report(report)
    
    def write_implementation_plan(
        self,
        report: Any
    ) -> dict[str, str]:
        """Write an implementation plan report.
        
        Args:
            report: ImplementationPlanReport object
        
        Returns:
            Dict mapping format to file path
        """
        return self.write_report(report)
    
    def write_design_proposals(
        self,
        report: Any
    ) -> dict[str, str]:
        """Write a design proposals report.
        
        Args:
            report: DesignProposalReport object
        
        Returns:
            Dict mapping format to file path
        """
        return self.write_report(report)
    
    def write_full_report(
        self,
        report: FullReport
    ) -> dict[str, str]:
        """Write a complete report with all sections.
        
        Args:
            report: FullReport object
        
        Returns:
            Dict mapping format to file path
        """
        return self.write_report(report)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def write_markdown_report(
    report: Any,
    output_dir: Optional[Path] = None
) -> str:
    """Write a Markdown report to the file system.
    
    Args:
        report: Report object
        output_dir: Optional output directory override
    
    Returns:
        Path to the written file
    """
    writer = ReportWriter(output_dir=output_dir)
    return writer.write_markdown_report(report)


def write_json_report(
    report: Any,
    output_dir: Optional[Path] = None
) -> str:
    """Write a JSON report to the file system.
    
    Args:
        report: Report object
        output_dir: Optional output directory override
    
    Returns:
        Path to the written file
    """
    writer = ReportWriter(output_dir=output_dir)
    return writer.write_json_report(report)


def write_full_report(
    report: FullReport,
    output_dir: Optional[Path] = None
) -> dict[str, str]:
    """Write a complete report in all formats.
    
    Args:
        report: FullReport object
        output_dir: Optional output directory override
    
    Returns:
        Dict mapping format to file path
    """
    writer = ReportWriter(output_dir=output_dir)
    return writer.write_full_report(report)


def generate_report_filename(
    report_type: ReportType,
    report_id: str,
    extension: str = "md"
) -> str:
    """Generate a standardized report filename.
    
    Args:
        report_type: Type of report
        report_id: Unique report identifier
        extension: File extension
    
    Returns:
        Filename string
    """
    writer = ReportWriter()
    return writer.generate_report_filename(report_type, report_id, extension)