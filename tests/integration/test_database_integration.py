"""
Integration tests for database operations.

Tests real SQLite database integration including:
- Full audit persistence
- Cascade delete behavior
- Component-token relationships
"""

import tempfile
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


# =============================================================================
# PERSISTENCE TESTS
# =============================================================================

class TestFullAuditPersistence:
    """Tests for complete audit persistence workflow."""
    
    def test_create_and_retrieve_screen(self, db_path):
        """Create and retrieve a screen record."""
        screen_data = ScreenCreate(
            name="Test Screen",
            image_path="/data/test.png",
        )
        
        created = crud.create_screen(screen_data, db_path)
        
        assert created.id is not None
        assert created.name == "Test Screen"
        
        # Retrieve by ID
        retrieved = crud.get_screen(created.id, db_path)
        assert retrieved is not None
        assert retrieved.name == "Test Screen"
    
    def test_create_and_retrieve_component(self, db_path):
        """Create and retrieve component with screen relationship."""
        # Create screen first
        screen = crud.create_screen(ScreenCreate(
            name="Component Test Screen",
            image_path="/data/test.png",
        ), db_path)
        
        # Create component with BoundingBox
        component = crud.create_component(ComponentCreate(
            screen_id=screen.id,
            type="button",
            bounding_box=BoundingBox(x=0.1, y=0.5, width=0.3, height=0.05),
        ), db_path)
        
        assert component.id is not None
        assert component.screen_id == screen.id
        
        # Retrieve components for screen
        components = crud.get_components_by_screen(screen.id, db_path)
        assert len(components) == 1
        assert components[0].type == "button"
    
    def test_create_and_retrieve_token(self, db_path):
        """Create and retrieve design token."""
        token = crud.create_system_token(SystemTokenCreate(
            name="primary",
            type=TokenType.COLOR,
            value="#0066CC",
        ), db_path)
        
        assert token.id is not None
        
        # Retrieve by type
        colors = crud.list_system_tokens(token_type=TokenType.COLOR, db_path=db_path)
        assert any(t.name == "primary" for t in colors)


# =============================================================================
# CASCADE DELETE TESTS
# =============================================================================

class TestCascadeDelete:
    """Tests for cascade delete behavior."""
    
    def test_screen_delete_cascades_to_components(self, db_path):
        """Deleting a screen cascades to its components."""
        # Create screen with components
        screen = crud.create_screen(ScreenCreate(
            name="Cascade Test Screen",
            image_path="/data/test.png",
        ), db_path)
        
        crud.create_component(ComponentCreate(
            screen_id=screen.id,
            type="button",
            bounding_box=BoundingBox(x=0.1, y=0.5, width=0.3, height=0.05),
        ), db_path)
        
        crud.create_component(ComponentCreate(
            screen_id=screen.id,
            type="text",
            bounding_box=BoundingBox(x=0.1, y=0.2, width=0.8, height=0.1),
        ), db_path)
        
        # Verify components exist
        components = crud.get_components_by_screen(screen.id, db_path)
        assert len(components) == 2
        
        # Delete screen
        crud.delete_screen(screen.id, db_path)
        
        # Verify components are gone
        remaining = crud.get_components_by_screen(screen.id, db_path)
        assert len(remaining) == 0


# =============================================================================
# RELATIONSHIP TESTS
# =============================================================================

class TestComponentTokenRelationships:
    """Tests for M:N component-token relationships."""
    
    def test_link_component_to_token(self, db_path):
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
        
        token = crud.create_system_token(SystemTokenCreate(
            name="primary",
            type=TokenType.COLOR,
            value="#0066CC",
        ), db_path)
        
        # Link component to token
        count = crud.batch_link_components_tokens([
            (component.id, token.id),
        ], db_path)
        
        assert count == 1
    
    def test_get_tokens_for_component(self, db_path):
        """Retrieve tokens linked to a component."""
        screen = crud.create_screen(ScreenCreate(
            name="Token Test Screen",
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
        
        # Link multiple tokens to component
        crud.batch_link_components_tokens([
            (component.id, token1.id),
            (component.id, token2.id),
        ], db_path)
        
        # Retrieve linked tokens
        linked = crud.get_component_tokens(component.id, db_path)
        
        assert len(linked) == 2
        assert any(t.name == "primary" for t in linked)
        assert any(t.name == "md" for t in linked)
    
    def test_get_components_for_token(self, db_path):
        """Retrieve components linked to a token."""
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
        
        # Link token to multiple components
        crud.batch_link_components_tokens([
            (comp1.id, token.id),
            (comp2.id, token.id),
        ], db_path)
        
        # Retrieve linked components
        linked = crud.get_token_components(token.id, db_path)
        
        assert len(linked) == 2


# =============================================================================
# AUDIT FINDING PERSISTENCE TESTS
# =============================================================================

class TestAuditFindingPersistence:
    """Tests for audit finding persistence."""
    
    def test_create_audit_finding(self, db_path):
        """Create and retrieve audit findings."""
        # Create screen first
        screen = crud.create_screen(ScreenCreate(
            name="Audit Test Screen",
            image_path="/data/audit.png",
        ), db_path)
        
        # Create finding
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
    
    def test_audit_findings_by_severity(self, db_path):
        """Filter audit findings by severity."""
        # Create screen
        screen = crud.create_screen(ScreenCreate(
            name="Severity Test Screen",
            image_path="/data/severity.png",
        ), db_path)
        
        # Create findings with different severities
        crud.create_audit_finding(AuditFindingCreate(
            entity_type=EntityType.SCREEN,
            entity_id=screen.id,
            issue="Low severity issue",
            severity=Severity.LOW,
        ), db_path)
        
        crud.create_audit_finding(AuditFindingCreate(
            entity_type=EntityType.SCREEN,
            entity_id=screen.id,
            issue="High severity issue",
            severity=Severity.HIGH,
        ), db_path)
        
        # Filter by high severity
        high_findings = crud.list_audit_findings(severity=Severity.HIGH, db_path=db_path)
        assert len(high_findings) == 1
        assert high_findings[0].severity == Severity.HIGH


# =============================================================================
# BATCH OPERATIONS TESTS
# =============================================================================

class TestBatchOperations:
    """Tests for batch CRUD operations."""
    
    def test_list_screens_pagination(self, db_path):
        """List screens with pagination."""
        # Create multiple screens
        for i in range(5):
            crud.create_screen(ScreenCreate(
                name=f"Screen {i}",
                image_path=f"/data/screen{i}.png",
            ), db_path)
        
        # Get first page
        page1 = crud.list_screens(limit=3, offset=0, db_path=db_path)
        assert len(page1) == 3
        
        # Get second page
        page2 = crud.list_screens(limit=3, offset=3, db_path=db_path)
        assert len(page2) == 2
    
    def test_list_tokens_by_type(self, db_path):
        """List tokens filtered by type."""
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
            name="color-secondary",
            type=TokenType.COLOR,
            value="#FF6600",
        ), db_path)
        
        # Filter by color type
        colors = crud.list_system_tokens(token_type=TokenType.COLOR, db_path=db_path)
        assert len(colors) == 2
        
        # All should be colors
        for token in colors:
            assert token.type == TokenType.COLOR