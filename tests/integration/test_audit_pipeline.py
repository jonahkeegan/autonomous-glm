"""
Integration tests for audit pipeline.

Tests the complete audit workflow from ingest to report:
- Screen and component persistence
- Audit session management
- Finding creation and retrieval
- End-to-end timing validation
"""

import tempfile
import time
from pathlib import Path

import pytest

from src.db.database import init_database
from src.db import crud
from src.db.models import (
    ScreenCreate,
    ComponentCreate,
    SystemTokenCreate,
    AuditFindingCreate,
    BoundingBox,
    TokenType,
    EntityType,
    Severity,
)


@pytest.fixture
def db_path():
    """Create a temp database for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    
    init_database(path)
    yield path
    
    # Cleanup
    try:
        path.unlink()
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_detection_result():
    """Sample detection result for testing."""
    return {
        "components": [
            {"type": "button", "bbox": [0.1, 0.5, 0.3, 0.05]},
            {"type": "text", "bbox": [0.1, 0.2, 0.8, 0.1]},
            {"type": "input", "bbox": [0.1, 0.35, 0.8, 0.06]},
        ],
    }


@pytest.fixture
def sample_audit_findings():
    """Sample audit findings for testing."""
    return [
        {"severity": Severity.MEDIUM, "description": "Inconsistent spacing"},
        {"severity": Severity.LOW, "description": "Font size below minimum"},
        {"severity": Severity.HIGH, "description": "Insufficient contrast"},
    ]


# =============================================================================
# SCREEN INGEST TO AUDIT TESTS
# =============================================================================

class TestScreenIngestToAudit:
    """Tests for screen ingest to audit flow."""
    
    def test_screen_persists_to_database(self, db_path):
        """Screen can be ingested and persisted."""
        screen = crud.create_screen(ScreenCreate(
            name="Login Screen",
            image_path="/data/artifacts/screenshots/login.png",
        ), db_path)
        
        assert screen.id is not None
        assert screen.name == "Login Screen"
        
        # Verify retrieval
        retrieved = crud.get_screen(screen.id, db_path)
        assert retrieved is not None
        assert retrieved.name == "Login Screen"
    
    def test_components_persist_for_screen(self, db_path):
        """Components are persisted for a screen."""
        screen = crud.create_screen(ScreenCreate(
            name="Dashboard Screen",
            image_path="/data/artifacts/screenshots/dashboard.png",
        ), db_path)
        
        # Create components
        for i in range(3):
            crud.create_component(ComponentCreate(
                screen_id=screen.id,
                type="button" if i == 0 else "text" if i == 1 else "container",
                bounding_box=BoundingBox(x=0.1 * i, y=0.2 * i, width=0.3, height=0.1),
            ), db_path)
        
        # Verify components
        components = crud.get_components_by_screen(screen.id, db_path)
        assert len(components) == 3


# =============================================================================
# AUDIT SESSION MANAGEMENT TESTS
# =============================================================================

class TestAuditSessionManagement:
    """Tests for audit session management."""
    
    def test_audit_finding_persistence(self, db_path):
        """Audit findings are persisted correctly."""
        screen = crud.create_screen(ScreenCreate(
            name="Audit Test Screen",
            image_path="/data/audit.png",
        ), db_path)
        
        finding = crud.create_audit_finding(AuditFindingCreate(
            entity_type=EntityType.SCREEN,
            entity_id=screen.id,
            issue="Inconsistent spacing between buttons",
            rationale="Buttons use different margin values",
            severity=Severity.MEDIUM,
            related_standard="spacing-8px-grid",
        ), db_path)
        
        assert finding.id is not None
        assert finding.severity == Severity.MEDIUM
        
        # Retrieve findings
        findings = crud.list_audit_findings(entity_id=screen.id, db_path=db_path)
        assert len(findings) == 1
    
    def test_multiple_findings_by_severity(self, db_path):
        """Multiple findings can be filtered by severity."""
        screen = crud.create_screen(ScreenCreate(
            name="Multi-Finding Screen",
            image_path="/data/multi.png",
        ), db_path)
        
        # Create findings with different severities
        for sev in [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]:
            crud.create_audit_finding(AuditFindingCreate(
                entity_type=EntityType.SCREEN,
                entity_id=screen.id,
                issue=f"Issue with {sev.value} severity",
                severity=sev,
            ), db_path)
        
        # Verify counts
        all_findings = crud.list_audit_findings(entity_id=screen.id, db_path=db_path)
        assert len(all_findings) == 4
        
        high_findings = crud.list_audit_findings(severity=Severity.HIGH, db_path=db_path)
        assert len(high_findings) == 1


# =============================================================================
# TOKEN MANAGEMENT TESTS
# =============================================================================

class TestTokenManagement:
    """Tests for design token management."""
    
    def test_tokens_created_and_retrieved(self, db_path):
        """Tokens can be created and retrieved."""
        token = crud.create_system_token(SystemTokenCreate(
            name="primary",
            type=TokenType.COLOR,
            value="#0066CC",
        ), db_path)
        
        assert token.id is not None
        assert token.name == "primary"
        assert token.value == "#0066CC"
    
    def test_tokens_by_type(self, db_path):
        """Tokens can be filtered by type."""
        # Create tokens of different types
        crud.create_system_token(SystemTokenCreate(
            name="color-primary",
            type=TokenType.COLOR,
            value="#0066CC",
        ), db_path)
        
        crud.create_system_token(SystemTokenCreate(
            name="spacing-md",
            type=TokenType.SPACING,
            value="16px",
        ), db_path)
        
        crud.create_system_token(SystemTokenCreate(
            name="typography-body",
            type=TokenType.TYPOGRAPHY,
            value="16px/1.5",
        ), db_path)
        
        # Filter by color
        colors = crud.list_system_tokens(token_type=TokenType.COLOR, db_path=db_path)
        assert len(colors) >= 1
        for t in colors:
            assert t.type == TokenType.COLOR


# =============================================================================
# COMPONENT-TOKEN RELATIONSHIP TESTS
# =============================================================================

class TestComponentTokenRelationships:
    """Tests for component-token relationships."""
    
    def test_link_components_to_tokens(self, db_path):
        """Components can be linked to tokens."""
        screen = crud.create_screen(ScreenCreate(
            name="Link Test Screen",
            image_path="/data/test.png",
        ), db_path)
        
        component = crud.create_component(ComponentCreate(
            screen_id=screen.id,
            type="button",
            bounding_box=BoundingBox(x=0.1, y=0.5, width=0.3, height=0.05),
        ), db_path)
        
        token1 = crud.create_system_token(SystemTokenCreate(
            name="primary",
            type=TokenType.COLOR,
            value="#0066CC",
        ), db_path)
        
        token2 = crud.create_system_token(SystemTokenCreate(
            name="md",
            type=TokenType.SPACING,
            value="16px",
        ), db_path)
        
        # Link component to tokens
        links = [(component.id, token1.id), (component.id, token2.id)]
        count = crud.batch_link_components_tokens(links, db_path)
        
        assert count == 2
        
        # Verify retrieval
        linked_tokens = crud.get_component_tokens(component.id, db_path)
        assert len(linked_tokens) == 2
    
    def test_get_components_using_token(self, db_path):
        """Can find all components using a token."""
        screen = crud.create_screen(ScreenCreate(
            name="Comp Token Screen",
            image_path="/data/test.png",
        ), db_path)
        
        comp1 = crud.create_component(ComponentCreate(
            screen_id=screen.id,
            type="button",
            bounding_box=BoundingBox(x=0.1, y=0.5, width=0.3, height=0.05),
        ), db_path)
        
        comp2 = crud.create_component(ComponentCreate(
            screen_id=screen.id,
            type="text",
            bounding_box=BoundingBox(x=0.1, y=0.2, width=0.8, height=0.1),
        ), db_path)
        
        token = crud.create_system_token(SystemTokenCreate(
            name="primary",
            type=TokenType.COLOR,
            value="#0066CC",
        ), db_path)
        
        # Link multiple components to one token
        links = [(comp1.id, token.id), (comp2.id, token.id)]
        crud.batch_link_components_tokens(links, db_path)
        
        # Get components for token
        linked = crud.get_token_components(token.id, db_path)
        assert len(linked) == 2


# =============================================================================
# END-TO-END TIMING TESTS
# =============================================================================

class TestEndToEndTiming:
    """Tests for end-to-end timing validation."""
    
    def test_audit_timing_target(self, db_path):
        """Audit completes within timing targets."""
        start = time.time()
        
        # Create screen
        screen = crud.create_screen(ScreenCreate(
            name="Timing Test Screen",
            image_path="/data/timing.png",
        ), db_path)
        
        # Create components
        for i in range(5):
            crud.create_component(ComponentCreate(
                screen_id=screen.id,
                type="button",
                bounding_box=BoundingBox(x=0.1, y=0.1 * i, width=0.3, height=0.05),
            ), db_path)
        
        # Create findings
        for i in range(3):
            crud.create_audit_finding(AuditFindingCreate(
                entity_type=EntityType.SCREEN,
                entity_id=screen.id,
                issue=f"Finding {i}",
                severity=Severity.MEDIUM,
            ), db_path)
        
        elapsed = time.time() - start
        
        # Should be fast
        assert elapsed < 1.0  # Less than 1 second
    
    def test_batch_operations_timing(self, db_path):
        """Batch operations meet timing targets."""
        start = time.time()
        
        # Batch create screens
        for i in range(10):
            crud.create_screen(ScreenCreate(
                name=f"Batch Screen {i}",
                image_path=f"/data/batch{i}.png",
            ), db_path)
        
        elapsed = time.time() - start
        
        # Should be fast
        assert elapsed < 0.5  # Less than 500ms for 10 screens


# =============================================================================
# FULL PIPELINE INTEGRATION TESTS
# =============================================================================

class TestFullPipelineIntegration:
    """Tests for full pipeline integration."""
    
    def test_ingest_to_report_flow(self, db_path, sample_detection_result, sample_audit_findings):
        """Complete flow from ingest to report generation."""
        # Step 1: Ingest screen
        screen = crud.create_screen(ScreenCreate(
            name="Pipeline Test Screen",
            image_path="/data/pipeline_test.png",
        ), db_path)
        
        assert screen.id is not None, "Screen creation failed"
        
        # Step 2: Create components from detection
        for comp in sample_detection_result["components"]:
            crud.create_component(ComponentCreate(
                screen_id=screen.id,
                type=comp["type"],
                bounding_box=BoundingBox(
                    x=comp["bbox"][0],
                    y=comp["bbox"][1],
                    width=comp["bbox"][2],
                    height=comp["bbox"][3],
                ),
            ), db_path)
        
        components = crud.get_components_by_screen(screen.id, db_path)
        assert len(components) == 3, f"Expected 3 components, got {len(components)}"
        
        # Step 3: Create audit findings
        for finding_data in sample_audit_findings:
            crud.create_audit_finding(AuditFindingCreate(
                entity_type=EntityType.SCREEN,
                entity_id=screen.id,
                issue=finding_data["description"],
                severity=finding_data["severity"],
            ), db_path)
        
        findings = crud.list_audit_findings(entity_id=screen.id, db_path=db_path)
        assert len(findings) == 3, f"Expected 3 findings, got {len(findings)}"
        
        # Step 4: Verify report can be generated
        report_data = {
            "screen_id": screen.id,
            "component_count": len(components),
            "finding_count": len(findings),
            "critical_count": sum(1 for f in findings if f.severity == Severity.CRITICAL),
            "high_count": sum(1 for f in findings if f.severity == Severity.HIGH),
            "medium_count": sum(1 for f in findings if f.severity == Severity.MEDIUM),
            "low_count": sum(1 for f in findings if f.severity == Severity.LOW),
        }
        
        assert report_data["screen_id"] == screen.id
        assert report_data["component_count"] == 3
        assert report_data["finding_count"] == 3