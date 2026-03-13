"""
Shared pytest fixtures for integration tests.

Provides fixtures for:
- Agent mocks (all 4 agents)
- Integration database (real SQLite :memory:)
- Socket test utilities
- Golden dataset artifacts
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from src.db.database import init_database
from src.db.models import (
    ScreenCreate,
    ComponentCreate,
    SystemTokenCreate,
    BoundingBox,
    TokenType,
)
from src.db import crud
from src.protocol.message import AgentType
from tests.integration.mocks import ClaudeMock, MinimaxMock, CodexMock, HumanMock


# =============================================================================
# ASYNC SUPPORT
# =============================================================================

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# AGENT MOCK FIXTURES
# =============================================================================

@pytest.fixture
def claude_mock():
    """Create a Claude (PM/Arbiter) mock."""
    mock = ClaudeMock()
    mock.connect()
    yield mock
    mock.disconnect()


@pytest.fixture
def minimax_mock():
    """Create a Minimax (FE Engineer) mock."""
    mock = MinimaxMock()
    mock.connect()
    yield mock
    mock.disconnect()


@pytest.fixture
def codex_mock():
    """Create a Codex (BE Engineer) mock."""
    mock = CodexMock()
    mock.connect()
    yield mock
    mock.disconnect()


@pytest.fixture
def human_mock():
    """Create a Human (Design Lead) mock."""
    mock = HumanMock()
    mock.connect()
    yield mock
    mock.disconnect()


@pytest.fixture
def mock_agents(claude_mock, minimax_mock, codex_mock, human_mock):
    """
    All 4 agent mocks connected and ready.
    
    Returns a dict mapping agent type to mock instance.
    """
    return {
        AgentType.CLAUDE: claude_mock,
        AgentType.MINIMAX: minimax_mock,
        AgentType.CODEX: codex_mock,
        AgentType.HUMAN: human_mock,
    }


@pytest.fixture
def mock_agents_with_handshake(mock_agents):
    """
    All 4 agent mocks with completed handshake.
    """
    for agent_mock in mock_agents.values():
        agent_mock.complete_handshake()
    return mock_agents


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture
def integration_db():
    """
    Real SQLite in-memory database for integration tests.
    
    Initialized with schema but no data.
    """
    # Use temp file for database (needed for Path compatibility)
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    init_database(db_path)
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def populated_db(integration_db):
    """
    Database with sample data for testing.
    
    Includes:
    - 1 screen
    - 3 components
    - 2 tokens
    """
    # Create a test screen
    screen = crud.create_screen(ScreenCreate(
        name="Test Screen",
        image_path="/data/artifacts/screenshots/test.png",
    ))
    
    # Create test components with BoundingBox
    comp1 = crud.create_component(ComponentCreate(
        screen_id=screen.id,
        type="button",
        bounding_box=BoundingBox(x=0.1, y=0.5, width=0.3, height=0.05),
    ))
    
    comp2 = crud.create_component(ComponentCreate(
        screen_id=screen.id,
        type="text",
        bounding_box=BoundingBox(x=0.1, y=0.2, width=0.8, height=0.1),
    ))
    
    comp3 = crud.create_component(ComponentCreate(
        screen_id=screen.id,
        type="container",
        bounding_box=BoundingBox(x=0.0, y=0.0, width=1.0, height=1.0),
    ))
    
    # Create test tokens
    token1 = crud.create_system_token(SystemTokenCreate(
        name="primary",
        type=TokenType.COLOR,
        value="#0066CC",
    ))
    
    token2 = crud.create_system_token(SystemTokenCreate(
        name="md",
        type=TokenType.SPACING,
        value="16px",
    ))
    
    yield {
        "db_path": integration_db,
        "screen": screen,
        "components": [comp1, comp2, comp3],
        "tokens": [token1, token2],
    }


# =============================================================================
# SOCKET FIXTURES
# =============================================================================

@pytest.fixture
def temp_socket_dir():
    """
    Temporary directory for Unix socket testing.
    
    Automatically cleaned up after test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def socket_path(temp_socket_dir):
    """
    Path for a test Unix socket.
    """
    return str(temp_socket_dir / "test.sock")


# =============================================================================
# ARTIFACT FIXTURES
# =============================================================================

@pytest.fixture
def golden_screenshot(project_root):
    """
    Path to a screenshot from the golden dataset.
    """
    screenshot_path = project_root / "tests" / "golden-dataset" / "screenshots" / "login_clean.png"
    if not screenshot_path.exists():
        pytest.skip("Golden dataset screenshot not found")
    return screenshot_path


@pytest.fixture
def sample_detection_result():
    """
    Sample detection result for testing.
    """
    return {
        "components": [
            {
                "type": "button",
                "bbox": [0.1, 0.5, 0.3, 0.05],
                "confidence": 0.95,
            },
            {
                "type": "text",
                "bbox": [0.1, 0.2, 0.8, 0.1],
                "confidence": 0.98,
            },
            {
                "type": "input",
                "bbox": [0.1, 0.35, 0.8, 0.06],
                "confidence": 0.92,
            },
        ],
        "confidence_threshold": 0.8,
    }


@pytest.fixture
def sample_audit_findings():
    """
    Sample audit findings for testing.
    """
    return [
        {
            "dimension": "spacing",
            "severity": "medium",
            "description": "Inconsistent spacing between buttons",
            "element_id": "btn-1",
            "standard_reference": "spacing-rhythm-8px-grid",
        },
        {
            "dimension": "typography",
            "severity": "low",
            "description": "Font size below recommended minimum",
            "element_id": "text-1",
            "standard_reference": "typography-min-16px",
        },
        {
            "dimension": "accessibility",
            "severity": "high",
            "description": "Insufficient color contrast ratio",
            "element_id": "btn-1",
            "standard_reference": "wcag-1.4.3",
        },
    ]


# =============================================================================
# PROTOCOL FIXTURES
# =============================================================================

@pytest.fixture
def sample_audit_complete_message():
    """
    Sample AUDIT_COMPLETE message payload.
    """
    return {
        "artifact_id": "artifact-001",
        "audit_id": "audit-001",
        "findings_count": 3,
        "critical_count": 0,
        "phases": ["Critical", "Refinement"],
        "report_path": "/output/reports/2026-03-13/audit-001.md",
    }


@pytest.fixture
def sample_design_proposal_message():
    """
    Sample DESIGN_PROPOSAL message payload.
    """
    return {
        "proposal_id": "proposal-001",
        "proposal_type": "token_addition",
        "changes": [
            {
                "target_file": "design_system/tokens.md",
                "change_type": "add",
                "new_value": "spacing-xl: 24px",
                "rationale": "Missing extra-large spacing token",
            }
        ],
        "affected_components": ["card", "modal"],
        "human_approval_required": True,
        "audit_source": "audit-001",
    }


@pytest.fixture
def sample_dispute_message():
    """
    Sample DISPUTE message payload.
    """
    return {
        "dispute_id": "dispute-001",
        "audit_id": "audit-001",
        "finding_id": "finding-001",
        "finding_summary": "Insufficient color contrast ratio",
        "dispute_reason": "False positive - the contrast ratio is actually 4.8:1",
        "proposed_alternative": "Reduce severity to low or dismiss",
        "severity": "medium",
    }


@pytest.fixture
def sample_human_required_message():
    """
    Sample HUMAN_REQUIRED message payload.
    """
    return {
        "review_type": "design_system_change",
        "reason": "Adding new token requires human approval",
        "related_artifact_id": "artifact-001",
        "related_audit_id": "audit-001",
        "related_proposal_id": "proposal-001",
        "blocking": True,
        "options": [
            {"label": "Approve", "action": "approve"},
            {"label": "Reject", "action": "reject"},
            {"label": "Modify", "action": "modify"},
        ],
        "report_path": "/output/reports/2026-03-13/proposal-001.md",
    }