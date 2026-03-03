"""
Integration tests for M3-1 Database Persistence layer.

Tests batch CRUD operations, persistence bridge functions, and
component-token relationships.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.db.crud import (
    batch_create_components,
    batch_create_tokens,
    batch_link_components_tokens,
    delete_components_by_screen,
    clear_all_tokens,
    get_components_by_screen,
    get_all_tokens,
    get_component_tokens,
    get_token_components,
    create_screen,
    list_system_tokens,
)
from src.db.database import init_database, reset_database
from src.db.models import (
    ScreenCreate,
    SystemToken,
    Component,
    TokenType,
)
from src.db.persistence import (
    persist_detection_result,
    persist_token_extraction,
    link_component_tokens_by_match,
    get_screen_analysis,
)
from src.vision.models import DetectedComponent, ComponentType, DetectionResult
from src.vision.tokens.models import DesignToken, TokenType as VisionTokenType


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_database(db_path)
        yield db_path


@pytest.fixture
def sample_screen(temp_db):
    """Create a sample screen for testing."""
    screen = create_screen(
        ScreenCreate(
            name="Test Screen",
            image_path="/tmp/test.png",
        ),
        db_path=temp_db,
    )
    return screen


@pytest.fixture
def sample_detected_components():
    """Create sample detected components (M2 format)."""
    return [
        DetectedComponent(
            type=ComponentType.BUTTON,
            label="Submit",
            confidence=0.95,
            bbox_x=0.1,
            bbox_y=0.2,
            bbox_width=0.3,
            bbox_height=0.1,
        ),
        DetectedComponent(
            type=ComponentType.INPUT,
            label="Email",
            confidence=0.88,
            bbox_x=0.1,
            bbox_y=0.35,
            bbox_width=0.8,
            bbox_height=0.08,
        ),
        DetectedComponent(
            type=ComponentType.TEXT,
            label="Welcome",
            confidence=0.92,
            bbox_x=0.1,
            bbox_y=0.05,
            bbox_width=0.4,
            bbox_height=0.1,
        ),
    ]


@pytest.fixture
def sample_design_tokens():
    """Create sample design tokens (M2 format)."""
    return [
        DesignToken(
            name="color-primary-500",
            value="#3B82F6",
            token_type=VisionTokenType.COLOR,
            description="Primary blue color",
        ),
        DesignToken(
            name="spacing-4",
            value="16px",
            token_type=VisionTokenType.SPACING,
            description="4-step spacing",
        ),
        DesignToken(
            name="font-size-lg",
            value="18px",
            token_type=VisionTokenType.TYPOGRAPHY,
            description="Large font size",
        ),
    ]


# =============================================================================
# BATCH COMPONENT TESTS
# =============================================================================

class TestBatchCreateComponents:
    """Tests for batch_create_components function."""

    def test_batch_create_empty_list(self, sample_screen, temp_db):
        """Test batch create with empty list."""
        result = batch_create_components(
            screen_id=sample_screen.id,
            components=[],
            db_path=temp_db,
        )
        assert result == []

    def test_batch_create_single_component(self, sample_screen, sample_detected_components, temp_db):
        """Test batch create with single component."""
        result = batch_create_components(
            screen_id=sample_screen.id,
            components=[sample_detected_components[0]],
            db_path=temp_db,
        )
        
        assert len(result) == 1
        assert result[0].type == "button"
        assert result[0].screen_id == sample_screen.id
        assert result[0].bounding_box.x == 0.1
        assert result[0].bounding_box.y == 0.2

    def test_batch_create_multiple_components(self, sample_screen, sample_detected_components, temp_db):
        """Test batch create with multiple components."""
        result = batch_create_components(
            screen_id=sample_screen.id,
            components=sample_detected_components,
            db_path=temp_db,
        )
        
        assert len(result) == 3
        types = [c.type for c in result]
        assert "button" in types
        assert "input" in types
        assert "text" in types

    def test_batch_create_includes_confidence_in_properties(self, sample_screen, sample_detected_components, temp_db):
        """Test that confidence is stored in properties."""
        result = batch_create_components(
            screen_id=sample_screen.id,
            components=sample_detected_components,
            db_path=temp_db,
        )
        
        for comp in result:
            assert comp.properties is not None
            assert "_confidence" in comp.properties

    def test_batch_create_includes_label_in_properties(self, sample_screen, sample_detected_components, temp_db):
        """Test that label is stored in properties."""
        result = batch_create_components(
            screen_id=sample_screen.id,
            components=sample_detected_components,
            db_path=temp_db,
        )
        
        button = next(c for c in result if c.type == "button")
        assert button.properties.get("_label") == "Submit"

    def test_persisted_components_retrievable(self, sample_screen, sample_detected_components, temp_db):
        """Test that persisted components can be retrieved."""
        batch_create_components(
            screen_id=sample_screen.id,
            components=sample_detected_components,
            db_path=temp_db,
        )
        
        retrieved = get_components_by_screen(sample_screen.id, db_path=temp_db)
        assert len(retrieved) == 3


class TestDeleteComponentsByScreen:
    """Tests for delete_components_by_screen function."""

    def test_delete_existing_components(self, sample_screen, sample_detected_components, temp_db):
        """Test deleting all components for a screen."""
        batch_create_components(
            screen_id=sample_screen.id,
            components=sample_detected_components,
            db_path=temp_db,
        )
        
        count = delete_components_by_screen(sample_screen.id, db_path=temp_db)
        assert count == 3
        
        retrieved = get_components_by_screen(sample_screen.id, db_path=temp_db)
        assert len(retrieved) == 0

    def test_delete_empty_screen(self, sample_screen, temp_db):
        """Test deleting components from screen with none."""
        count = delete_components_by_screen(sample_screen.id, db_path=temp_db)
        assert count == 0


# =============================================================================
# BATCH TOKEN TESTS
# =============================================================================

class TestBatchCreateTokens:
    """Tests for batch_create_tokens function."""

    def test_batch_create_empty_list(self, temp_db):
        """Test batch create with empty list."""
        result = batch_create_tokens(tokens=[], db_path=temp_db)
        assert result == []

    def test_batch_create_single_token(self, sample_design_tokens, temp_db):
        """Test batch create with single token."""
        result = batch_create_tokens(
            tokens=[sample_design_tokens[0]],
            db_path=temp_db,
        )
        
        assert len(result) == 1
        assert result[0].name == "color-primary-500"
        assert result[0].value == "#3B82F6"
        assert result[0].type == TokenType.COLOR

    def test_batch_create_multiple_tokens(self, sample_design_tokens, temp_db):
        """Test batch create with multiple tokens."""
        result = batch_create_tokens(
            tokens=sample_design_tokens,
            db_path=temp_db,
        )
        
        assert len(result) == 3
        names = [t.name for t in result]
        assert "color-primary-500" in names
        assert "spacing-4" in names
        assert "font-size-lg" in names

    def test_batch_create_handles_duplicates(self, sample_design_tokens, temp_db):
        """Test that duplicate tokens are handled gracefully."""
        # Create first batch
        batch_create_tokens(tokens=sample_design_tokens, db_path=temp_db)
        
        # Create same tokens again (should not fail)
        result = batch_create_tokens(tokens=sample_design_tokens, db_path=temp_db)
        
        # Should return existing tokens
        assert len(result) == 3

    def test_token_type_mapping(self, sample_design_tokens, temp_db):
        """Test that token types are correctly mapped."""
        result = batch_create_tokens(
            tokens=sample_design_tokens,
            db_path=temp_db,
        )
        
        type_map = {t.name: t.type for t in result}
        assert type_map["color-primary-500"] == TokenType.COLOR
        assert type_map["spacing-4"] == TokenType.SPACING
        assert type_map["font-size-lg"] == TokenType.TYPOGRAPHY


class TestGetAllTokens:
    """Tests for get_all_tokens function."""

    def test_get_all_empty(self, temp_db):
        """Test getting tokens when none exist."""
        result = get_all_tokens(db_path=temp_db)
        assert result == []

    def test_get_all_returns_all(self, sample_design_tokens, temp_db):
        """Test getting all tokens."""
        batch_create_tokens(tokens=sample_design_tokens, db_path=temp_db)
        
        result = get_all_tokens(db_path=temp_db)
        assert len(result) == 3


class TestClearAllTokens:
    """Tests for clear_all_tokens function."""

    def test_clear_all(self, sample_design_tokens, temp_db):
        """Test clearing all tokens."""
        batch_create_tokens(tokens=sample_design_tokens, db_path=temp_db)
        
        count = clear_all_tokens(db_path=temp_db)
        assert count == 3
        
        result = get_all_tokens(db_path=temp_db)
        assert result == []


# =============================================================================
# COMPONENT-TOKEN RELATIONSHIP TESTS
# =============================================================================

class TestBatchLinkComponentsTokens:
    """Tests for batch_link_components_tokens function."""

    def test_batch_link_empty(self, temp_db):
        """Test linking with empty list."""
        count = batch_link_components_tokens(links=[], db_path=temp_db)
        assert count == 0

    def test_batch_link_single(self, sample_screen, sample_detected_components, sample_design_tokens, temp_db):
        """Test linking single component to single token."""
        components = batch_create_components(
            screen_id=sample_screen.id,
            components=[sample_detected_components[0]],
            db_path=temp_db,
        )
        tokens = batch_create_tokens(tokens=[sample_design_tokens[0]], db_path=temp_db)
        
        links = [(components[0].id, tokens[0].id)]
        count = batch_link_components_tokens(links=links, db_path=temp_db)
        
        assert count == 1

    def test_batch_link_multiple(self, sample_screen, sample_detected_components, sample_design_tokens, temp_db):
        """Test linking multiple components to tokens."""
        components = batch_create_components(
            screen_id=sample_screen.id,
            components=sample_detected_components,
            db_path=temp_db,
        )
        tokens = batch_create_tokens(tokens=sample_design_tokens, db_path=temp_db)
        
        links = [
            (components[0].id, tokens[0].id),  # button -> color
            (components[0].id, tokens[1].id),  # button -> spacing
            (components[1].id, tokens[0].id),  # input -> color
        ]
        count = batch_link_components_tokens(links=links, db_path=temp_db)
        
        assert count == 3


class TestGetComponentTokens:
    """Tests for get_component_tokens function."""

    def test_get_component_tokens_none(self, sample_screen, sample_detected_components, temp_db):
        """Test getting tokens for component with none linked."""
        components = batch_create_components(
            screen_id=sample_screen.id,
            components=[sample_detected_components[0]],
            db_path=temp_db,
        )
        
        result = get_component_tokens(components[0].id, db_path=temp_db)
        assert result == []

    def test_get_component_tokens_linked(self, sample_screen, sample_detected_components, sample_design_tokens, temp_db):
        """Test getting tokens for component with linked tokens."""
        components = batch_create_components(
            screen_id=sample_screen.id,
            components=[sample_detected_components[0]],
            db_path=temp_db,
        )
        tokens = batch_create_tokens(tokens=sample_design_tokens[:2], db_path=temp_db)
        
        links = [
            (components[0].id, tokens[0].id),
            (components[0].id, tokens[1].id),
        ]
        batch_link_components_tokens(links=links, db_path=temp_db)
        
        result = get_component_tokens(components[0].id, db_path=temp_db)
        assert len(result) == 2


class TestGetTokenComponents:
    """Tests for get_token_components function."""

    def test_get_token_components_none(self, sample_design_tokens, temp_db):
        """Test getting components for token with none linked."""
        tokens = batch_create_tokens(tokens=[sample_design_tokens[0]], db_path=temp_db)
        
        result = get_token_components(tokens[0].id, db_path=temp_db)
        assert result == []

    def test_get_token_components_linked(self, sample_screen, sample_detected_components, sample_design_tokens, temp_db):
        """Test getting components for token with linked components."""
        components = batch_create_components(
            screen_id=sample_screen.id,
            components=sample_detected_components[:2],
            db_path=temp_db,
        )
        tokens = batch_create_tokens(tokens=[sample_design_tokens[0]], db_path=temp_db)
        
        links = [
            (components[0].id, tokens[0].id),
            (components[1].id, tokens[0].id),
        ]
        batch_link_components_tokens(links=links, db_path=temp_db)
        
        result = get_token_components(tokens[0].id, db_path=temp_db)
        assert len(result) == 2


# =============================================================================
# PERSISTENCE BRIDGE TESTS
# =============================================================================

class TestPersistDetectionResult:
    """Tests for persist_detection_result bridge function."""

    def test_persist_empty_result(self, sample_screen, temp_db):
        """Test persisting empty detection result."""
        result = DetectionResult(components=[])
        persisted = persist_detection_result(
            screen_id=sample_screen.id,
            detection_result=result,
            db_path=temp_db,
        )
        assert persisted == []

    def test_persist_full_result(self, sample_screen, sample_detected_components, temp_db):
        """Test persisting full detection result."""
        result = DetectionResult(
            components=sample_detected_components,
            image_width=800,
            image_height=600,
        )
        persisted = persist_detection_result(
            screen_id=sample_screen.id,
            detection_result=result,
            db_path=temp_db,
        )
        
        assert len(persisted) == 3
        assert all(isinstance(c, Component) for c in persisted)


class TestPersistTokenExtraction:
    """Tests for persist_token_extraction bridge function."""

    def test_persist_empty(self, temp_db):
        """Test persisting empty token list."""
        persisted = persist_token_extraction(tokens=[], db_path=temp_db)
        assert persisted == []

    def test_persist_tokens(self, sample_design_tokens, temp_db):
        """Test persisting token list."""
        persisted = persist_token_extraction(
            tokens=sample_design_tokens,
            db_path=temp_db,
        )
        
        assert len(persisted) == 3
        assert all(isinstance(t, SystemToken) for t in persisted)


class TestGetScreenAnalysis:
    """Tests for get_screen_analysis bridge function."""

    def test_get_analysis_empty(self, sample_screen, temp_db):
        """Test getting analysis for screen with no data."""
        result = get_screen_analysis(sample_screen.id, db_path=temp_db)
        
        assert result["components"] == []
        assert result["tokens"] == []
        assert result["component_count"] == 0
        assert result["token_count"] == 0

    def test_get_analysis_with_data(self, sample_screen, sample_detected_components, sample_design_tokens, temp_db):
        """Test getting analysis for screen with data."""
        persist_detection_result(
            screen_id=sample_screen.id,
            detection_result=DetectionResult(components=sample_detected_components),
            db_path=temp_db,
        )
        persist_token_extraction(tokens=sample_design_tokens, db_path=temp_db)
        
        result = get_screen_analysis(sample_screen.id, db_path=temp_db)
        
        assert result["component_count"] == 3
        assert result["token_count"] == 3


# =============================================================================
# VALIDATION DATASET TESTS
# =============================================================================

class TestValidationDataset:
    """Tests using the validation dataset fixtures."""

    def test_load_validation_metadata(self):
        """Test that validation metadata can be loaded."""
        manifest_path = Path(__file__).parent.parent / "golden-dataset" / "validation" / "manifest.json"
        
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            assert "screenshots" in manifest
            assert len(manifest["screenshots"]) == 5

    def test_persist_validation_components(self, temp_db):
        """Test persisting components from validation dataset."""
        manifest_path = Path(__file__).parent.parent / "golden-dataset" / "validation" / "manifest.json"
        
        if not manifest_path.exists():
            pytest.skip("Validation dataset not generated")
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # Create a screen for the first validation screenshot
        screen = create_screen(
            ScreenCreate(
                name="Validation Screen",
                image_path="validation/screenshot_001.png",
            ),
            db_path=temp_db,
        )
        
        # Load first screenshot metadata
        screenshot_info = manifest["screenshots"][0]
        metadata_path = manifest_path.parent / screenshot_info["metadata"]
        
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        # Convert to DetectedComponent format
        components = []
        for c in metadata["components"]:
            comp = DetectedComponent(
                type=ComponentType(c["type"]),
                label=c.get("label"),
                confidence=1.0,  # Ground truth
                bbox_x=c["bbox_normalized"]["x"],
                bbox_y=c["bbox_normalized"]["y"],
                bbox_width=c["bbox_normalized"]["width"],
                bbox_height=c["bbox_normalized"]["height"],
            )
            components.append(comp)
        
        # Persist
        persisted = batch_create_components(
            screen_id=screen.id,
            components=components,
            db_path=temp_db,
        )
        
        assert len(persisted) == metadata["component_count"]