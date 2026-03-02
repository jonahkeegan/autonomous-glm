"""
Unit tests for the vision module.

Tests cover:
- DetectedComponent model validation
- DetectionResult model functionality
- VisionClient with mocked API responses
- Rate limiting and retry logic
- Error handling
"""

import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from src.vision import (
    ComponentType,
    DetectedComponent,
    DetectionResult,
    DetectionConfig,
    VisionClient,
    SYSTEM_PROMPT,
    build_detection_prompt,
)
from src.vision.client import (
    VisionClientError,
    RateLimitError,
    APIResponseError,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_api_response():
    """Sample API response with detected components."""
    return json.dumps({
        "components": [
            {
                "type": "button",
                "label": "Submit",
                "confidence": 0.95,
                "bbox_x": 0.4,
                "bbox_y": 0.8,
                "bbox_width": 0.2,
                "bbox_height": 0.05,
                "properties": {"variant": "primary"}
            },
            {
                "type": "input",
                "label": "Email",
                "confidence": 0.88,
                "bbox_x": 0.3,
                "bbox_y": 0.5,
                "bbox_width": 0.4,
                "bbox_height": 0.04,
                "properties": {"placeholder": "Enter email"}
            },
            {
                "type": "text",
                "label": "Welcome",
                "confidence": 0.92,
                "bbox_x": 0.1,
                "bbox_y": 0.1,
                "bbox_width": 0.8,
                "bbox_height": 0.08,
                "properties": None
            }
        ]
    })


@pytest.fixture
def sample_api_response_with_markdown():
    """Sample API response wrapped in markdown code blocks."""
    return """```json
{
    "components": [
        {
            "type": "button",
            "label": "Click Me",
            "confidence": 0.9,
            "bbox_x": 0.25,
            "bbox_y": 0.75,
            "bbox_width": 0.5,
            "bbox_height": 0.1
        }
    ]
}
```"""


@pytest.fixture
def detection_config():
    """Standard detection config for testing."""
    return DetectionConfig(
        model="gpt-4o",
        max_tokens=4096,
        temperature=0.1,
        confidence_threshold=0.5,
        rate_limit_per_minute=60,
        retry_attempts=2,
        retry_base_delay_ms=100,
        retry_max_delay_ms=1000,
    )


@pytest.fixture
def mock_openai_client(sample_api_response):
    """Mock OpenAI client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = sample_api_response
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


# =============================================================================
# COMPONENT TYPE TESTS
# =============================================================================

class TestComponentType:
    """Tests for ComponentType enum."""
    
    def test_all_component_types_exist(self):
        """Verify all expected component types are defined."""
        expected_types = [
            "button", "input", "modal", "label", "icon", "image",
            "text", "container", "card", "navigation", "checkbox",
            "radio", "select", "slider", "switch", "tab", "table",
            "header", "footer", "sidebar", "unknown"
        ]
        for type_name in expected_types:
            assert hasattr(ComponentType, type_name.upper())
    
    def test_component_type_values(self):
        """Verify component type string values."""
        assert ComponentType.BUTTON.value == "button"
        assert ComponentType.INPUT.value == "input"
        assert ComponentType.UNKNOWN.value == "unknown"


# =============================================================================
# DETECTED COMPONENT TESTS
# =============================================================================

class TestDetectedComponent:
    """Tests for DetectedComponent model."""
    
    def test_create_detected_component(self):
        """Test creating a valid detected component."""
        component = DetectedComponent(
            type=ComponentType.BUTTON,
            label="Submit",
            confidence=0.95,
            bbox_x=0.4,
            bbox_y=0.8,
            bbox_width=0.2,
            bbox_height=0.05,
        )
        
        assert component.type == ComponentType.BUTTON
        assert component.label == "Submit"
        assert component.confidence == 0.95
        assert component.bbox_x == 0.4
        assert component.bbox_y == 0.8
        assert component.bbox_width == 0.2
        assert component.bbox_height == 0.05
    
    def test_normalized_coordinate_validation_valid(self):
        """Test that valid normalized coordinates pass validation."""
        component = DetectedComponent(
            type=ComponentType.INPUT,
            bbox_x=0.0,
            bbox_y=0.5,
            bbox_width=1.0,
            bbox_height=0.25,
        )
        assert component.bbox_x == 0.0
        assert component.bbox_width == 1.0
    
    def test_normalized_coordinate_validation_invalid_x(self):
        """Test that out-of-range x coordinate raises error."""
        with pytest.raises(ValueError):
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=1.5,  # Invalid: > 1.0
                bbox_y=0.5,
                bbox_width=0.2,
                bbox_height=0.1,
            )
    
    def test_normalized_coordinate_validation_invalid_y(self):
        """Test that out-of-range y coordinate raises error."""
        with pytest.raises(ValueError):
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.5,
                bbox_y=-0.1,  # Invalid: < 0.0
                bbox_width=0.2,
                bbox_height=0.1,
            )
    
    def test_to_absolute_coordinates(self):
        """Test conversion to absolute pixel coordinates."""
        component = DetectedComponent(
            type=ComponentType.BUTTON,
            bbox_x=0.5,
            bbox_y=0.5,
            bbox_width=0.2,
            bbox_height=0.1,
        )
        
        x, y, w, h = component.to_absolute(800, 600)
        
        assert x == 400  # 0.5 * 800
        assert y == 300  # 0.5 * 600
        assert w == 160  # 0.2 * 800
        assert h == 60   # 0.1 * 600
    
    def test_default_values(self):
        """Test default values for optional fields."""
        component = DetectedComponent(
            type=ComponentType.TEXT,
            bbox_x=0.1,
            bbox_y=0.1,
            bbox_width=0.8,
            bbox_height=0.1,
        )
        
        assert component.confidence == 1.0
        assert component.label is None
        assert component.properties is None


# =============================================================================
# DETECTION RESULT TESTS
# =============================================================================

class TestDetectionResult:
    """Tests for DetectionResult model."""
    
    def test_create_detection_result(self):
        """Test creating a valid detection result."""
        components = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                label="Submit",
                confidence=0.95,
                bbox_x=0.4,
                bbox_y=0.8,
                bbox_width=0.2,
                bbox_height=0.05,
            )
        ]
        
        result = DetectionResult(
            components=components,
            image_id="test_image",
            image_width=800,
            image_height=600,
            processing_time_ms=1234.5,
            model_version="gpt-4o",
        )
        
        assert result.component_count == 1
        assert result.image_id == "test_image"
        assert result.image_width == 800
        assert result.image_height == 600
        assert result.processing_time_ms == 1234.5
        assert result.is_success is True
    
    def test_empty_result(self):
        """Test empty detection result."""
        result = DetectionResult()
        
        assert result.component_count == 0
        assert result.components == []
        assert result.is_success is True  # No error means success
    
    def test_error_result(self):
        """Test detection result with error."""
        result = DetectionResult(
            image_id="failed_image",
            error="API rate limit exceeded",
        )
        
        assert result.is_success is False
        assert result.error == "API rate limit exceeded"
    
    def test_get_components_by_type(self):
        """Test filtering components by type."""
        components = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.1, bbox_y=0.1, bbox_width=0.1, bbox_height=0.1,
            ),
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.2, bbox_y=0.2, bbox_width=0.1, bbox_height=0.1,
            ),
            DetectedComponent(
                type=ComponentType.INPUT,
                bbox_x=0.3, bbox_y=0.3, bbox_width=0.1, bbox_height=0.1,
            ),
        ]
        
        result = DetectionResult(components=components)
        
        buttons = result.get_components_by_type(ComponentType.BUTTON)
        inputs = result.get_components_by_type(ComponentType.INPUT)
        modals = result.get_components_by_type(ComponentType.MODAL)
        
        assert len(buttons) == 2
        assert len(inputs) == 1
        assert len(modals) == 0
    
    def test_get_high_confidence_components(self):
        """Test filtering by confidence threshold."""
        components = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                confidence=0.95,
                bbox_x=0.1, bbox_y=0.1, bbox_width=0.1, bbox_height=0.1,
            ),
            DetectedComponent(
                type=ComponentType.BUTTON,
                confidence=0.75,
                bbox_x=0.2, bbox_y=0.2, bbox_width=0.1, bbox_height=0.1,
            ),
            DetectedComponent(
                type=ComponentType.INPUT,
                confidence=0.45,
                bbox_x=0.3, bbox_y=0.3, bbox_width=0.1, bbox_height=0.1,
            ),
        ]
        
        result = DetectionResult(components=components)
        
        high_conf = result.get_high_confidence_components(0.7)
        very_high_conf = result.get_high_confidence_components(0.9)
        
        assert len(high_conf) == 2
        assert len(very_high_conf) == 1


# =============================================================================
# DETECTION CONFIG TESTS
# =============================================================================

class TestDetectionConfig:
    """Tests for DetectionConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = DetectionConfig()
        
        assert config.model == "gpt-4o"
        assert config.max_tokens == 4096
        assert config.temperature == 0.1
        assert config.confidence_threshold == 0.5
        assert config.rate_limit_per_minute == 60
        assert config.retry_attempts == 3
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = DetectionConfig(
            model="gpt-4o-mini",
            max_tokens=2048,
            temperature=0.0,
            confidence_threshold=0.8,
            rate_limit_per_minute=30,
        )
        
        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 2048
        assert config.temperature == 0.0
        assert config.confidence_threshold == 0.8
        assert config.rate_limit_per_minute == 30


# =============================================================================
# PROMPT TESTS
# =============================================================================

class TestPrompts:
    """Tests for prompt templates."""
    
    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 100
        assert "component" in SYSTEM_PROMPT.lower()
    
    def test_build_detection_prompt(self):
        """Test building detection prompt."""
        prompt = build_detection_prompt("test.png")
        
        assert "test.png" in prompt
        assert "component" in prompt.lower()
    
    def test_build_detection_prompt_with_context(self):
        """Test building prompt with additional context."""
        prompt = build_detection_prompt("test.png", "This is a login form")
        
        assert "test.png" in prompt
        assert "login form" in prompt


# =============================================================================
# VISION CLIENT INITIALIZATION TESTS
# =============================================================================

class TestVisionClientInit:
    """Tests for VisionClient initialization."""
    
    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = VisionClient(api_key="test-key-123")
        
        assert client.api_key == "test-key-123"
    
    def test_init_with_env_var(self):
        """Test initialization using environment variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key-456"}):
            client = VisionClient()
            assert client.api_key == "env-key-456"
    
    def test_init_without_api_key_raises(self):
        """Test that missing API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            # Also clear any existing OPENAI_API_KEY
            os.environ.pop("OPENAI_API_KEY", None)
            with pytest.raises(ValueError, match="OpenAI API key required"):
                VisionClient()
    
    def test_init_with_custom_config(self, detection_config):
        """Test initialization with custom config."""
        client = VisionClient(
            api_key="test-key",
            config=detection_config,
        )
        
        assert client.config.model == "gpt-4o"
        assert client.config.retry_attempts == 2


# =============================================================================
# VISION CLIENT API CALLS TESTS
# =============================================================================

class TestVisionClientDetection:
    """Tests for VisionClient detection functionality."""
    
    @patch("src.vision.client.VisionClient._get_client")
    def test_detect_components_success(self, mock_get_client, mock_openai_client, tmp_path):
        """Test successful component detection."""
        mock_get_client.return_value = mock_openai_client
        
        # Create a test image
        test_image = tmp_path / "test.png"
        from PIL import Image
        img = Image.new("RGB", (800, 600), color="white")
        img.save(test_image)
        
        client = VisionClient(api_key="test-key")
        result = client.detect_components(str(test_image))
        
        assert result.is_success is True
        assert result.component_count == 3
        assert result.image_width == 800
        assert result.image_height == 600
        assert result.model_version == "gpt-4o"
    
    @patch("src.vision.client.VisionClient._get_client")
    def test_detect_components_filters_by_confidence(self, mock_get_client, mock_openai_client, tmp_path):
        """Test that low confidence components are filtered."""
        mock_get_client.return_value = mock_openai_client
        
        test_image = tmp_path / "test.png"
        from PIL import Image
        img = Image.new("RGB", (800, 600), color="white")
        img.save(test_image)
        
        # Use high threshold config
        config = DetectionConfig(confidence_threshold=0.9)
        client = VisionClient(api_key="test-key", config=config)
        result = client.detect_components(str(test_image))
        
        # Only 2 components have confidence >= 0.9
        assert result.is_success is True
        assert result.component_count == 2
    
    def test_detect_components_file_not_found(self):
        """Test detection with non-existent file."""
        client = VisionClient(api_key="test-key")
        result = client.detect_components("/nonexistent/image.png")
        
        assert result.is_success is False
        assert "not found" in result.error.lower()
    
    @patch("src.vision.client.VisionClient._get_client")
    def test_detect_components_with_markdown_response(self, mock_get_client, sample_api_response_with_markdown, tmp_path):
        """Test parsing response wrapped in markdown."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = sample_api_response_with_markdown
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        test_image = tmp_path / "test.png"
        from PIL import Image
        img = Image.new("RGB", (800, 600), color="white")
        img.save(test_image)
        
        client = VisionClient(api_key="test-key")
        result = client.detect_components(str(test_image))
        
        assert result.is_success is True
        assert result.component_count == 1


# =============================================================================
# VISION CLIENT PARSING TESTS
# =============================================================================

class TestVisionClientParsing:
    """Tests for API response parsing."""
    
    def test_parse_valid_response(self, sample_api_response):
        """Test parsing a valid API response."""
        client = VisionClient.__new__(VisionClient)
        client.config = DetectionConfig()
        
        components = client._parse_response(sample_api_response)
        
        assert len(components) == 3
        assert components[0].type == ComponentType.BUTTON
        assert components[0].label == "Submit"
        assert components[0].confidence == 0.95
    
    def test_parse_response_with_unknown_type(self):
        """Test parsing response with unknown component type."""
        client = VisionClient.__new__(VisionClient)
        client.config = DetectionConfig()
        
        response = json.dumps({
            "components": [
                {
                    "type": "future_component",
                    "bbox_x": 0.1,
                    "bbox_y": 0.1,
                    "bbox_width": 0.2,
                    "bbox_height": 0.1,
                }
            ]
        })
        
        components = client._parse_response(response)
        
        assert len(components) == 1
        assert components[0].type == ComponentType.UNKNOWN
    
    def test_parse_invalid_json_raises(self):
        """Test that invalid JSON raises APIResponseError."""
        client = VisionClient.__new__(VisionClient)
        client.config = DetectionConfig()
        
        with pytest.raises(APIResponseError):
            client._parse_response("not valid json")


# =============================================================================
# RATE LIMITING TESTS
# =============================================================================

class TestRateLimiting:
    """Tests for rate limiting functionality."""
    
    def test_rate_limiting_delays_requests(self, detection_config):
        """Test that rate limiting adds delays between requests."""
        # Very low rate limit for testing
        config = DetectionConfig(
            rate_limit_per_minute=120,  # 0.5s between requests
        )
        client = VisionClient(api_key="test-key", config=config)
        
        # First request should not delay
        start = time.time()
        client._check_rate_limit()
        first_check = time.time() - start
        
        # Should be instant (no prior request)
        assert first_check < 0.1
        
        # Update last request time
        client._last_request_time = time.time()
        
        # Second immediate check should trigger delay
        start = time.time()
        client._check_rate_limit()
        second_check = time.time() - start
        
        # Should have delayed (allow some tolerance)
        assert second_check >= 0.4  # At least 0.5s - tolerance


# =============================================================================
# RETRY LOGIC TESTS
# =============================================================================

class TestRetryLogic:
    """Tests for retry with backoff logic."""
    
    def test_retry_succeeds_after_failure(self, detection_config):
        """Test that retry succeeds after initial failure."""
        config = DetectionConfig(
            retry_attempts=3,
            retry_base_delay_ms=100,  # Minimum allowed
            retry_max_delay_ms=1000,
        )
        client = VisionClient(api_key="test-key", config=config)
        
        call_count = 0
        
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = client._retry_with_backoff(flaky_function)
        
        assert result == "success"
        assert call_count == 2
    
    def test_retry_fails_after_max_attempts(self, detection_config):
        """Test that retry fails after max attempts."""
        config = DetectionConfig(
            retry_attempts=2,
            retry_base_delay_ms=100,
            retry_max_delay_ms=1000,
        )
        client = VisionClient(api_key="test-key", config=config)
        
        def always_fails():
            raise ValueError("Always fails")
        
        with pytest.raises(VisionClientError, match="3 attempts"):
            client._retry_with_backoff(always_fails)


# =============================================================================
# REQUEST COUNT TESTS
# =============================================================================

class TestRequestCount:
    """Tests for request count tracking."""
    
    @patch("src.vision.client.VisionClient._get_client")
    def test_request_count_increments(self, mock_get_client, mock_openai_client, tmp_path):
        """Test that request count increments with each request."""
        mock_get_client.return_value = mock_openai_client
        
        test_image = tmp_path / "test.png"
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="white")
        img.save(test_image)
        
        client = VisionClient(api_key="test-key")
        
        assert client.request_count == 0
        
        client.detect_components(str(test_image))
        assert client.request_count == 1
        
        client.detect_components(str(test_image))
        assert client.request_count == 2


# =============================================================================
# INTEGRATION WITH DATABASE MODELS
# =============================================================================

class TestDatabaseIntegration:
    """Tests for integration with database models."""
    
    def test_detected_component_to_db_component(self):
        """Test converting DetectedComponent to database Component."""
        from src.db.models import BoundingBox, ComponentCreate
        
        detected = DetectedComponent(
            type=ComponentType.BUTTON,
            label="Submit",
            confidence=0.95,
            bbox_x=0.4,
            bbox_y=0.8,
            bbox_width=0.2,
            bbox_height=0.05,
            properties={"variant": "primary"},
        )
        
        # Convert to absolute coordinates
        x, y, w, h = detected.to_absolute(800, 600)
        
        # Create database component
        db_component = ComponentCreate(
            screen_id="screen-123",
            type=detected.type.value,
            bounding_box=BoundingBox(x=x, y=y, width=w, height=h),
            properties=detected.properties,
        )
        
        assert db_component.screen_id == "screen-123"
        assert db_component.type == "button"
        assert db_component.bounding_box.x == 320  # 0.4 * 800
        assert db_component.bounding_box.y == 480  # 0.8 * 600
        assert db_component.bounding_box.width == 160  # 0.2 * 800
        assert db_component.bounding_box.height == 30  # 0.05 * 600