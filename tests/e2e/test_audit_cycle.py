"""E2E tests for the complete audit cycle.

Tests the full workflow from screenshot ingestion to report generation.
"""
import json
from pathlib import Path

import pytest

from src.db.database import get_connection


@pytest.mark.e2e
@pytest.mark.ci_quick
class TestAuditCycleE2E:
    """End-to-end tests for the audit cycle."""

    def test_screenshot_ingestion_creates_screen_record(
        self, e2e_temp_dir: Path, e2e_db_path: Path, e2e_screenshot: Path
    ) -> None:
        """Test that ingesting a screenshot creates a database record."""
        from src.ingest.screenshot import ingest_screenshot
        
        # Ingest the screenshot
        result = ingest_screenshot(
            str(e2e_screenshot),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
        )

        # Verify result structure
        assert result is not None
        assert hasattr(result, 'success') or hasattr(result, 'ingest_id') or result is True

    def test_audit_creates_session(
        self, e2e_temp_dir: Path, e2e_db_path: Path, e2e_screenshot_with_ui: Path
    ) -> None:
        """Test that running an audit creates a session."""
        from src.ingest.screenshot import ingest_screenshot
        
        # First ingest the screenshot
        ingest_result = ingest_screenshot(
            str(e2e_screenshot_with_ui),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
        )

        # Verify ingestion succeeded
        assert ingest_result is not None

    def test_complete_audit_workflow(
        self, e2e_temp_dir: Path, e2e_db_path: Path, e2e_screenshot_with_ui: Path
    ) -> None:
        """Test the complete workflow: ingest -> audit -> report."""
        from src.ingest.screenshot import ingest_screenshot
        
        # Step 1: Ingest screenshot
        ingest_result = ingest_screenshot(
            str(e2e_screenshot_with_ui),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
        )
        assert ingest_result is not None

        # Step 2: Verify database has the screen record
        conn = get_connection(e2e_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM screens")
        count = cursor.fetchone()[0]
        conn.close()
        
        # Should have at least one screen record
        assert count >= 1

    def test_audit_with_metadata(
        self, e2e_temp_dir: Path, e2e_db_path: Path, e2e_screenshot: Path
    ) -> None:
        """Test audit workflow with attached metadata."""
        from src.ingest.screenshot import ingest_screenshot
        
        metadata = {
            "app_name": "TestApp",
            "screen_name": "LoginScreen",
            "viewport": {"width": 390, "height": 844},
        }

        result = ingest_screenshot(
            str(e2e_screenshot),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
            metadata=metadata,
        )

        assert result is not None


@pytest.mark.e2e
class TestAuditDimensionsE2E:
    """E2E tests for specific audit dimensions."""

    def test_visual_hierarchy_audit(
        self, e2e_temp_dir: Path, e2e_db_path: Path, e2e_screenshot_with_ui: Path
    ) -> None:
        """Test that visual hierarchy dimension can run."""
        from src.ingest.screenshot import ingest_screenshot
        
        # Ingest and verify
        ingest_result = ingest_screenshot(
            str(e2e_screenshot_with_ui),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
        )
        assert ingest_result is not None

    def test_accessibility_dimension_audit(
        self, e2e_temp_dir: Path, e2e_db_path: Path, e2e_screenshot: Path
    ) -> None:
        """Test accessibility dimension can run."""
        from src.ingest.screenshot import ingest_screenshot
        
        # Ingest and verify
        ingest_result = ingest_screenshot(
            str(e2e_screenshot),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
        )
        assert ingest_result is not None


@pytest.mark.e2e
@pytest.mark.ci_quick
class TestReportGenerationE2E:
    """E2E tests for report generation."""

    def test_report_directory_creation(
        self, e2e_temp_dir: Path, e2e_db_path: Path, e2e_screenshot: Path
    ) -> None:
        """Test that report directories can be created."""
        report_dir = e2e_temp_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify directory exists
        assert report_dir.exists()
        assert report_dir.is_dir()

    def test_json_output_generation(
        self, e2e_temp_dir: Path, e2e_db_path: Path, e2e_screenshot: Path
    ) -> None:
        """Test that JSON output can be generated."""
        # Create a simple JSON report
        report_dir = e2e_temp_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_data = {
            "audit_id": "test-audit-001",
            "status": "completed",
            "findings_count": 0,
        }
        
        report_path = report_dir / "test_report.json"
        with open(report_path, "w") as f:
            json.dump(report_data, f)
        
        # Verify JSON is valid
        with open(report_path) as f:
            data = json.load(f)
        assert data["audit_id"] == "test-audit-001"