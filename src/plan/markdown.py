"""
Markdown report generation for human consumption.

Provides generators for creating Markdown reports from audit results,
implementation plans, and design system proposals.
"""

from datetime import datetime
from typing import Any, Optional


# =============================================================================
# MARKDOWN GENERATOR
# =============================================================================

class MarkdownGenerator:
    """Generator for Markdown reports.
    
    Creates human-readable Markdown reports from structured report data.
    All reports follow a consistent structure:
    1. Header (title, metadata, status)
    2. Summary (key metrics, critical findings)
    3. Details (findings/instructions/proposals)
    4. Next Steps (recommended actions)
    """
    
    def __init__(
        self,
        include_timestamps: bool = True,
        include_toc: bool = True,
        max_table_rows: int = 50,
    ):
        """Initialize the Markdown generator.
        
        Args:
            include_timestamps: Whether to include timestamps in output
            include_toc: Whether to include table of contents
            max_table_rows: Maximum rows in tables before summarizing
        """
        self.include_timestamps = include_timestamps
        self.include_toc = include_toc
        self.max_table_rows = max_table_rows
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _format_header(
        self,
        title: str,
        metadata: Any,
        level: int = 1
    ) -> str:
        """Format a report header with metadata.
        
        Args:
            title: Report title
            metadata: ReportMetadata object
            level: Header level (1-6)
        
        Returns:
            Markdown header string
        """
        prefix = "#" * level
        lines = [
            f"{prefix} {title}",
            "",
            f"**Report ID:** `{metadata.id}`",
            f"**Type:** {metadata.report_type.value}",
            f"**Version:** {metadata.version}",
        ]
        
        if metadata.audit_session_id:
            lines.append(f"**Audit Session:** `{metadata.audit_session_id}`")
        
        if metadata.screen_id:
            lines.append(f"**Screen:** `{metadata.screen_id}`")
        
        if self.include_timestamps:
            lines.append(f"**Generated:** {metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        lines.append(f"**Generator:** {metadata.generator}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _format_toc(self, sections: list[str]) -> str:
        """Format a table of contents.
        
        Args:
            sections: List of section titles
        
        Returns:
            Markdown TOC string
        """
        lines = ["## Table of Contents", ""]
        for section in sections:
            anchor = section.lower().replace(" ", "-").replace("/", "-")
            lines.append(f"- [{section}](#{anchor})")
        lines.append("")
        return "\n".join(lines)
    
    def format_finding_table(
        self,
        findings: list[dict[str, Any]],
        max_rows: Optional[int] = None
    ) -> str:
        """Format findings as a Markdown table.
        
        Args:
            findings: List of finding dictionaries
            max_rows: Maximum rows to display (defaults to self.max_table_rows)
        
        Returns:
            Markdown table string
        """
        if not findings:
            return "*No findings in this category.*\n"
        
        max_rows = max_rows or self.max_table_rows
        display_findings = findings[:max_rows]
        
        lines = [
            "| # | Severity | Dimension | Issue |",
            "|---|----------|-----------|-------|",
        ]
        
        for i, finding in enumerate(display_findings, 1):
            severity = finding.get("severity", "medium")
            dimension = finding.get("dimension", "unknown")
            issue = finding.get("issue", "No description")
            
            # Truncate long issues
            if len(issue) > 60:
                issue = issue[:57] + "..."
            
            # Escape pipe characters
            issue = issue.replace("|", "\\|")
            
            lines.append(f"| {i} | {severity} | {dimension} | {issue} |")
        
        if len(findings) > max_rows:
            remaining = len(findings) - max_rows
            lines.append(f"\n*...and {remaining} more findings*\n")
        
        return "\n".join(lines) + "\n"
    
    def format_instruction_list(
        self,
        instructions: list[dict[str, Any]],
        numbered: bool = True
    ) -> str:
        """Format instructions as a numbered or bulleted list.
        
        Args:
            instructions: List of instruction dictionaries
            numbered: Whether to use numbered list (vs bullets)
        
        Returns:
            Markdown list string
        """
        if not instructions:
            return "*No instructions.*\n"
        
        lines = []
        for i, instruction in enumerate(instructions, 1):
            target = instruction.get("target_entity", "Unknown")
            property_name = instruction.get("property", "")
            old_val = instruction.get("old_value", "")
            new_val = instruction.get("new_value", "")
            confidence = instruction.get("confidence", 0.0)
            
            # Format based on available data
            if property_name and old_val and new_val:
                desc = f"`{target}`: `{property_name}`: `{old_val}` → `{new_val}`"
            elif property_name and new_val:
                desc = f"`{target}`: `{property_name}` → `{new_val}`"
            else:
                desc = f"`{target}`: {instruction.get('description', 'No description')}"
            
            # Add confidence indicator
            if confidence >= 0.8:
                indicator = "✓"
            elif confidence >= 0.5:
                indicator = "⚠"
            else:
                indicator = "❓"
            
            prefix = f"{i}." if numbered else "-"
            lines.append(f"{prefix} [{indicator}] {desc}")
        
        return "\n".join(lines) + "\n"
    
    def _format_summary_stats(self, summary: dict[str, Any]) -> str:
        """Format summary statistics as a Markdown block.
        
        Args:
            summary: Summary statistics dictionary
        
        Returns:
            Markdown formatted summary
        """
        lines = ["### Summary Statistics", "", "| Metric | Value |", "|--------|-------|"]
        
        for key, value in sorted(summary.items()):
            # Format key as title case
            formatted_key = key.replace("_", " ").title()
            
            # Format value based on type
            if isinstance(value, float):
                formatted_value = f"{value:.2f}"
            elif isinstance(value, bool):
                formatted_value = "Yes" if value else "No"
            else:
                formatted_value = str(value)
            
            lines.append(f"| {formatted_key} | {formatted_value} |")
        
        lines.append("")
        return "\n".join(lines)
    
    def _format_next_steps(self, recommendations: list[str]) -> str:
        """Format next steps/recommendations section.
        
        Args:
            recommendations: List of recommended actions
        
        Returns:
            Markdown formatted next steps
        """
        lines = ["## Next Steps", ""]
        
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")
        
        lines.append("")
        return "\n".join(lines)
    
    # =========================================================================
    # REPORT GENERATION METHODS
    # =========================================================================
    
    def generate_audit_summary(self, report: Any) -> str:
        """Generate Markdown for an audit summary report.
        
        Args:
            report: AuditSummaryReport object
        
        Returns:
            Markdown formatted string
        """
        lines = [
            self._format_header("Audit Summary Report", report.metadata),
        ]
        
        # Table of contents
        sections = ["Summary", "Findings by Severity", "Findings by Dimension", "Top Issues", "Standards Violated", "Next Steps"]
        if self.include_toc:
            lines.append(self._format_toc(sections))
        
        # Summary statistics
        lines.extend([
            "## Summary",
            "",
            self._format_summary_stats(report.summary.model_dump()),
        ])
        
        # Findings by severity
        lines.extend([
            "## Findings by Severity",
            "",
        ])
        
        for severity in ["critical", "high", "medium", "low"]:
            findings = report.findings_by_severity.get(severity, [])
            if findings:
                lines.extend([
                    f"### {severity.upper()} ({len(findings)})",
                    "",
                    self.format_finding_table(findings),
                ])
        
        # Findings by dimension
        lines.extend([
            "## Findings by Dimension",
            "",
        ])
        
        for dimension, findings in sorted(report.findings_by_dimension.items()):
            lines.extend([
                f"### {dimension.replace('_', ' ').title()} ({len(findings)})",
                "",
                self.format_finding_table(findings[:10]),  # Limit per dimension
            ])
        
        # Top issues
        lines.extend([
            "## Top Issues",
            "",
        ])
        
        if report.top_issues:
            lines.append(self.format_finding_table(report.top_issues))
        else:
            lines.append("*No critical issues identified.*\n")
        
        # Standards violated
        lines.extend([
            "## Standards Violated",
            "",
        ])
        
        if report.standards_violated:
            for standard in report.standards_violated:
                lines.append(f"- {standard}")
            lines.append("")
        else:
            lines.append("*No standards violations identified.*\n")
        
        # Next steps
        recommendations = []
        if report.summary.has_critical_issues:
            recommendations.append("Address all **critical** findings immediately")
        if report.summary.high_count > 0:
            recommendations.append("Review and fix **high** priority findings")
        if report.standards_violated:
            recommendations.append("Review and address standards violations (WCAG, design tokens)")
        if not recommendations:
            recommendations.append("No immediate actions required")
        
        lines.append(self._format_next_steps(recommendations))
        
        return "\n".join(lines)
    
    def generate_implementation_plan(self, report: Any) -> str:
        """Generate Markdown for an implementation plan report.
        
        Args:
            report: ImplementationPlanReport object
        
        Returns:
            Markdown formatted string
        """
        lines = [
            self._format_header("Implementation Plan Report", report.metadata),
        ]
        
        # Table of contents
        sections = ["Summary", "Phase 1: Critical", "Phase 2: Refinement", "Phase 3: Polish", "All Instructions", "Next Steps"]
        if self.include_toc:
            lines.append(self._format_toc(sections))
        
        # Summary statistics
        lines.extend([
            "## Summary",
            "",
            self._format_summary_stats(report.summary.model_dump()),
            f"**Estimated Effort:** {report.estimated_effort}",
            "",
        ])
        
        # Phase 1: Critical
        critical = report.phases.get("critical", [])
        lines.extend([
            "## Phase 1: Critical",
            "",
            f"*{len(critical)} instructions*",
            "",
        ])
        if critical:
            lines.append(self.format_instruction_list(critical))
        else:
            lines.append("*No critical phase instructions.*\n")
        
        # Phase 2: Refinement
        refinement = report.phases.get("refinement", [])
        lines.extend([
            "## Phase 2: Refinement",
            "",
            f"*{len(refinement)} instructions*",
            "",
        ])
        if refinement:
            lines.append(self.format_instruction_list(refinement))
        else:
            lines.append("*No refinement phase instructions.*\n")
        
        # Phase 3: Polish
        polish = report.phases.get("polish", [])
        lines.extend([
            "## Phase 3: Polish",
            "",
            f"*{len(polish)} instructions*",
            "",
        ])
        if polish:
            lines.append(self.format_instruction_list(polish))
        else:
            lines.append("*No polish phase instructions.*\n")
        
        # All instructions (flattened)
        lines.extend([
            "## All Instructions",
            "",
            f"*{len(report.all_instructions)} total instructions*",
            "",
        ])
        
        if report.all_instructions:
            # Show first 20 with link to full
            lines.append(self.format_instruction_list(report.all_instructions[:20]))
            if len(report.all_instructions) > 20:
                lines.append(f"\n*...and {len(report.all_instructions) - 20} more instructions*\n")
        
        # Next steps
        recommendations = [
            "Start with **Phase 1: Critical** instructions",
            "Review instructions marked with ❓ (low confidence) before implementing",
            "Test changes after each phase",
        ]
        
        if report.summary.requires_inspection_count > 0:
            recommendations.insert(
                1,
                f"Manually inspect {report.summary.requires_inspection_count} instructions requiring verification"
            )
        
        lines.append(self._format_next_steps(recommendations))
        
        return "\n".join(lines)
    
    def generate_design_proposals(self, report: Any) -> str:
        """Generate Markdown for a design proposal report.
        
        Args:
            report: DesignProposalReport object
        
        Returns:
            Markdown formatted string
        """
        lines = [
            self._format_header("Design System Proposal Report", report.metadata),
        ]
        
        # Approval banner
        if report.requires_human_approval:
            lines.extend([
                "> ⚠️ **Human Approval Required**",
                "",
                "This proposal requires human review before implementation.",
                "",
            ])
        
        # Table of contents
        sections = ["Summary", "Token Proposals", "Component Proposals", "Before/After Comparisons", "Next Steps"]
        if self.include_toc:
            lines.append(self._format_toc(sections))
        
        # Summary statistics
        lines.extend([
            "## Summary",
            "",
            self._format_summary_stats(report.summary.model_dump()),
        ])
        
        # Token proposals
        lines.extend([
            "## Token Proposals",
            "",
        ])
        
        if report.token_proposals:
            lines.extend([
                "| Token Name | Type | Proposed Value | Rationale |",
                "|------------|------|----------------|-----------|",
            ])
            for tp in report.token_proposals:
                name = tp.get("token_name", "unknown")
                tok_type = tp.get("token_type", "unknown")
                value = tp.get("proposed_value", "")
                rationale = tp.get("rationale", "")
                if len(rationale) > 50:
                    rationale = rationale[:47] + "..."
                lines.append(f"| `{name}` | {tok_type} | `{value}` | {rationale} |")
            lines.append("")
        else:
            lines.append("*No token proposals.*\n")
        
        # Component proposals
        lines.extend([
            "## Component Proposals",
            "",
        ])
        
        if report.component_proposals:
            lines.extend([
                "| Component | Variant | Instances | Rationale |",
                "|-----------|---------|-----------|-----------|",
            ])
            for cp in report.component_proposals:
                component = cp.get("component_type", "unknown")
                variant = cp.get("variant_name", "unknown")
                instances = cp.get("detected_instances", 0)
                rationale = cp.get("rationale", "")
                if len(rationale) > 50:
                    rationale = rationale[:47] + "..."
                lines.append(f"| {component} | {variant} | {instances} | {rationale} |")
            lines.append("")
        else:
            lines.append("*No component proposals.*\n")
        
        # Before/After comparisons
        lines.extend([
            "## Before/After Comparisons",
            "",
        ])
        
        if report.before_after_descriptions:
            for key, ba in report.before_after_descriptions.items():
                lines.extend([
                    f"### {key}",
                    "",
                    f"**Currently:** {ba.get('before_text', 'N/A')}",
                    "",
                    f"**Proposed:** {ba.get('after_text', 'N/A')}",
                    "",
                ])
                if ba.get("benefit"):
                    lines.append(f"**Benefit:** {ba['benefit']}")
                    lines.append("")
                if ba.get("key_changes"):
                    lines.append("**Key Changes:**")
                    lines.append("")
                    for change in ba["key_changes"]:
                        lines.append(f"- {change}")
                    lines.append("")
        else:
            lines.append("*No before/after comparisons.*\n")
        
        # Next steps
        recommendations = []
        if report.requires_human_approval:
            recommendations.append("Submit for human review and approval")
        if report.token_proposals:
            recommendations.append("Review token proposals for design system fit")
        if report.component_proposals:
            recommendations.append("Evaluate component variants for reusability")
        if not recommendations:
            recommendations.append("No proposals to implement")
        
        lines.append(self._format_next_steps(recommendations))
        
        return "\n".join(lines)
    
    def generate_full_report(self, report: Any) -> str:
        """Generate Markdown for a complete report with all sections.
        
        Args:
            report: FullReport object
        
        Returns:
            Markdown formatted string
        """
        lines = [
            self._format_header("Full Audit Report", report.metadata),
        ]
        
        # Overall summary
        lines.extend([
            "## Overview",
            "",
            self._format_summary_stats(report.overall_summary),
        ])
        
        # Table of contents
        sections = ["Overview"]
        if report.audit_summary:
            sections.append("Audit Summary")
        if report.implementation_plan:
            sections.append("Implementation Plan")
        if report.design_proposals:
            sections.append("Design Proposals")
        sections.append("Appendix")
        
        if self.include_toc:
            lines.append(self._format_toc(sections))
        
        # Audit summary section
        if report.audit_summary:
            lines.extend([
                "---",
                "",
                "# Audit Summary",
                "",
                self.generate_audit_summary(report.audit_summary),
            ])
        
        # Implementation plan section
        if report.implementation_plan:
            lines.extend([
                "---",
                "",
                "# Implementation Plan",
                "",
                self.generate_implementation_plan(report.implementation_plan),
            ])
        
        # Design proposals section
        if report.design_proposals:
            lines.extend([
                "---",
                "",
                "# Design Proposals",
                "",
                self.generate_design_proposals(report.design_proposals),
            ])
        
        # Appendix
        lines.extend([
            "---",
            "",
            "# Appendix",
            "",
            "## Report Information",
            "",
            f"- **Report ID:** `{report.metadata.id}`",
            f"- **Generated:** {report.metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Version:** {report.metadata.version}",
            f"- **Generator:** {report.metadata.generator}",
            "",
        ])
        
        return "\n".join(lines)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_audit_summary_markdown(report: Any) -> str:
    """Generate Markdown for an audit summary report.
    
    Args:
        report: AuditSummaryReport object
    
    Returns:
        Markdown formatted string
    """
    generator = MarkdownGenerator()
    return generator.generate_audit_summary(report)


def generate_implementation_plan_markdown(report: Any) -> str:
    """Generate Markdown for an implementation plan report.
    
    Args:
        report: ImplementationPlanReport object
    
    Returns:
        Markdown formatted string
    """
    generator = MarkdownGenerator()
    return generator.generate_implementation_plan(report)


def generate_design_proposals_markdown(report: Any) -> str:
    """Generate Markdown for a design proposal report.
    
    Args:
        report: DesignProposalReport object
    
    Returns:
        Markdown formatted string
    """
    generator = MarkdownGenerator()
    return generator.generate_design_proposals(report)


def generate_full_report_markdown(report: Any) -> str:
    """Generate Markdown for a complete report.
    
    Args:
        report: FullReport object
    
    Returns:
        Markdown formatted string
    """
    generator = MarkdownGenerator()
    return generator.generate_full_report(report)