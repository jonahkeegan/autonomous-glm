"""
PDF generation for autonomous-glm CLI.

Generates PDF files from reports and proposals using WeasyPrint.
"""

import base64
from io import BytesIO
from pathlib import Path
from typing import Optional, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"


class PDFGenerator:
    """Generates PDF files from reports and proposals.
    
    Uses Jinja2 for HTML templates and WeasyPrint for PDF generation.
    
    Example:
        >>> generator = PDFGenerator()
        >>> pdf_path = generator.generate_from_report(report_data, output_path)
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize the PDF generator.
        
        Args:
            template_dir: Optional custom template directory
        """
        self.template_dir = template_dir or TEMPLATE_DIR
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self.current_template = "report"
    
    def set_template(self, template_name: str) -> None:
        """Set the template to use for PDF generation.
        
        Args:
            template_name: Name of template (without .html extension)
        """
        self.current_template = template_name
    
    def _render_html(self, context: dict) -> str:
        """Render HTML from template and context.
        
        Args:
            context: Template context dictionary
            
        Returns:
            Rendered HTML string
        """
        template = self.env.get_template(f"{self.current_template}.html")
        return template.render(**context)
    
    def _html_to_pdf(self, html: str) -> bytes:
        """Convert HTML to PDF using WeasyPrint.
        
        Args:
            html: HTML string
            
        Returns:
            PDF bytes
        """
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            raise ImportError(
                "WeasyPrint is required for PDF generation. "
                "Install with: pip install weasyprint>=60.0\n"
                "On macOS, you may also need: brew install pango gdk-pixbuf libffi"
            )
        
        # Generate PDF
        pdf_bytes = HTML(string=html).write_pdf()
        return pdf_bytes
    
    def generate_from_markdown(
        self,
        md_path: Path,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate PDF from a Markdown file.
        
        Args:
            md_path: Path to Markdown file
            output_path: Optional output path (defaults to same name with .pdf)
            
        Returns:
            Path to generated PDF file
        """
        import markdown
        
        # Read markdown
        md_content = md_path.read_text()
        
        # Convert to HTML
        html_content = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "toc"]
        )
        
        # Wrap in full HTML document
        context = {
            "title": md_path.stem,
            "content": html_content,
            "generated_at": self._get_timestamp(),
        }
        
        self.set_template("report")
        full_html = self._render_html(context)
        
        # Generate PDF
        pdf_bytes = self._html_to_pdf(full_html)
        
        # Determine output path
        if output_path is None:
            output_path = md_path.with_suffix(".pdf")
        
        # Write PDF
        output_path.write_bytes(pdf_bytes)
        
        return output_path
    
    def generate_from_report(
        self,
        report: dict,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate PDF from a report dictionary.
        
        Args:
            report: Report dictionary from report command
            output_path: Optional output path
            
        Returns:
            Path to generated PDF file
        """
        # Prepare context
        context = {
            "title": f"Audit Report: {report.get('report_id', 'Unknown')}",
            "report": report,
            "findings": report.get("findings", []),
            "by_severity": report.get("by_severity", {}),
            "by_phase": report.get("by_phase", {}),
            "generated_at": self._get_timestamp(),
        }
        
        self.set_template("report")
        html = self._render_html(context)
        
        # Generate PDF
        pdf_bytes = self._html_to_pdf(html)
        
        # Determine output path
        if output_path is None:
            output_path = Path(f"report_{report.get('audit_id', 'unknown')}.pdf")
        
        # Write PDF
        output_path.write_bytes(pdf_bytes)
        
        return output_path
    
    def generate_from_proposal(
        self,
        proposal: dict,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate PDF from a design system proposal.
        
        Args:
            proposal: Proposal dictionary
            output_path: Optional output path
            
        Returns:
            Path to generated PDF file
        """
        # Prepare context
        context = {
            "title": f"Design Proposal: {proposal.get('id', 'Unknown')}",
            "proposal": proposal,
            "tokens": proposal.get("tokens", []),
            "changes": proposal.get("changes", []),
            "generated_at": self._get_timestamp(),
        }
        
        self.set_template("proposal")
        html = self._render_html(context)
        
        # Generate PDF
        pdf_bytes = self._html_to_pdf(html)
        
        # Determine output path
        if output_path is None:
            output_path = Path(f"proposal_{proposal.get('id', 'unknown')}.pdf")
        
        # Write PDF
        output_path.write_bytes(pdf_bytes)
        
        return output_path
    
    def generate_from_dashboard(
        self,
        metrics: Any,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate PDF from dashboard metrics.
        
        Args:
            metrics: DashboardMetrics model
            output_path: Optional output path
            
        Returns:
            Path to generated PDF file
        """
        # Convert to dict if needed
        if hasattr(metrics, "model_dump"):
            metrics_dict = metrics.model_dump()
        else:
            metrics_dict = dict(metrics)
        
        # Prepare context
        context = {
            "title": "Autonomous-GLM Dashboard",
            "metrics": metrics_dict,
            "generated_at": self._get_timestamp(),
        }
        
        self.set_template("dashboard")
        html = self._render_html(context)
        
        # Generate PDF
        pdf_bytes = self._html_to_pdf(html)
        
        # Determine output path
        if output_path is None:
            output_path = Path("dashboard.pdf")
        
        # Write PDF
        output_path.write_bytes(pdf_bytes)
        
        return output_path
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def embed_image(self, image_path: Path) -> str:
        """Embed an image as base64 data URI.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Data URI string
        """
        image_bytes = image_path.read_bytes()
        mime_type = self._get_mime_type(image_path)
        b64 = base64.b64encode(image_bytes).decode()
        return f"data:{mime_type};base64,{b64}"
    
    def _get_mime_type(self, path: Path) -> str:
        """Get MIME type from file extension.
        
        Args:
            path: File path
            
        Returns:
            MIME type string
        """
        ext = path.suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".webp": "image/webp",
        }
        return mime_map.get(ext, "application/octet-stream")


def generate_pdf(
    data: dict,
    output_path: str | Path,
    template: str = "report",
) -> Path:
    """Generate PDF from data dictionary.
    
    Convenience function for quick PDF generation.
    
    Args:
        data: Data dictionary
        output_path: Output file path
        template: Template name
        
    Returns:
        Path to generated PDF
    """
    generator = PDFGenerator()
    generator.set_template(template)
    
    if template == "proposal":
        return generator.generate_from_proposal(data, Path(output_path))
    else:
        return generator.generate_from_report(data, Path(output_path))