"""
Unit tests for the Autonomous-GLM API.

Tests API configuration, models, and health check endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.config import APIConfig, default_api_config
from src.api.models import (
    HealthCheckResponse,
    HealthStatus,
    ScreenshotIngestResponse,
    VideoIngestResponse,
    IngestStatusResponse,
    IngestStatus,
    ErrorResponse,
)


class TestAPIConfig:
    """Tests for API configuration."""
    
    def test_default_config_values(self):
        """Default config has expected values."""
        config = default_api_config
        
        assert config.title == "Autonomous-GLM API"
        assert config.version == "0.1.0"
        assert config.api_prefix == "/api/v1"
        assert config.max_screenshot_size_mb == 50.0
        assert config.max_video_size_mb == 500.0
    
    def test_custom_config(self):
        """Can create custom config."""
        config = APIConfig(
            title="Custom API",
            version="1.0.0",
            api_prefix="/v2",
        )
        
        assert config.title == "Custom API"
        assert config.version == "1.0.0"
        assert config.api_prefix == "/v2"
    
    def test_cors_defaults(self):
        """CORS defaults are reasonable."""
        config = default_api_config
        
        # CORS origins are specific localhost addresses
        assert "http://localhost:3000" in config.cors_origins
        assert "*" in config.cors_allow_methods


class TestHealthCheckResponse:
    """Tests for health check response model."""
    
    def test_healthy_response(self):
        """Can create healthy response."""
        response = HealthCheckResponse(
            status=HealthStatus.HEALTHY,
            version="0.1.0",
            checks={"database": "ok", "storage": "ok"},
        )
        
        assert response.status == HealthStatus.HEALTHY
        assert response.version == "0.1.0"
        assert response.checks["database"] == "ok"
    
    def test_degraded_response(self):
        """Can create degraded response."""
        response = HealthCheckResponse(
            status=HealthStatus.DEGRADED,
            version="0.1.0",
            checks={"database": "ok", "ffmpeg": "warning: not available"},
        )
        
        assert response.status == HealthStatus.DEGRADED
    
    def test_unhealthy_response(self):
        """Can create unhealthy response."""
        response = HealthCheckResponse(
            status=HealthStatus.UNHEALTHY,
            version="0.1.0",
            checks={"database": "error: connection failed"},
        )
        
        assert response.status == HealthStatus.UNHEALTHY


class TestScreenshotIngestResponse:
    """Tests for screenshot ingest response model."""
    
    def test_success_response(self):
        """Can create success response."""
        response = ScreenshotIngestResponse(
            ingest_id="test-id",
            screen_id="screen-123",
            status=IngestStatus.SUCCESS,
            storage_path="/data/screenshots/test.png",
            duplicate=False,
        )
        
        assert response.ingest_id == "test-id"
        assert response.screen_id == "screen-123"
        assert response.status == IngestStatus.SUCCESS
        assert not response.duplicate
    
    def test_duplicate_response(self):
        """Can create duplicate response."""
        response = ScreenshotIngestResponse(
            ingest_id="test-id",
            screen_id="screen-123",
            status=IngestStatus.DUPLICATE,
            storage_path="/data/screenshots/test.png",
            duplicate=True,
        )
        
        assert response.status == IngestStatus.DUPLICATE
        assert response.duplicate


class TestVideoIngestResponse:
    """Tests for video ingest response model."""
    
    def test_success_response(self):
        """Can create success response."""
        response = VideoIngestResponse(
            ingest_id="video-id",
            flow_id="flow-123",
            status=IngestStatus.SUCCESS,
            frame_count=30,
            storage_path="/data/videos/test.mp4",
        )
        
        assert response.ingest_id == "video-id"
        assert response.flow_id == "flow-123"
        assert response.frame_count == 30


class TestIngestStatusResponse:
    """Tests for ingest status response model."""
    
    def test_status_response(self):
        """Can create status response."""
        from datetime import datetime
        
        now = datetime.now()
        response = IngestStatusResponse(
            ingest_id="test-id",
            artifact_type="screenshot",
            status=IngestStatus.SUCCESS,
            created_at=now,
            artifact_id="screen-123",
        )
        
        assert response.ingest_id == "test-id"
        assert response.artifact_type == "screenshot"
        assert response.status == IngestStatus.SUCCESS
        assert response.created_at == now


class TestErrorResponse:
    """Tests for error response model."""
    
    def test_error_response(self):
        """Can create error response."""
        response = ErrorResponse(
            type="validation_error",
            title="Validation Error",
            status=400,
            detail="Invalid file format",
            instance="/api/v1/ingest/screenshot",
        )
        
        assert response.type == "validation_error"
        assert response.title == "Validation Error"
        assert response.status == 400
        assert response.detail == "Invalid file format"


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_health_check_returns_200(self, client):
        """Health check returns 200 status."""
        response = client.get("/health")
        
        assert response.status_code == 200
    
    def test_health_check_response_structure(self, client):
        """Health check has expected structure."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert "checks" in data
    
    def test_health_check_status_values(self, client):
        """Health check status is valid value."""
        response = client.get("/health")
        data = response.json()
        
        valid_statuses = ["healthy", "degraded", "unhealthy"]
        assert data["status"] in valid_statuses
    
    def test_health_check_includes_database(self, client):
        """Health check includes database check."""
        response = client.get("/health")
        data = response.json()
        
        assert "database" in data["checks"]
    
    def test_health_check_includes_storage(self, client):
        """Health check includes storage check."""
        response = client.get("/health")
        data = response.json()
        
        assert "storage" in data["checks"]


class TestOpenAPI:
    """Tests for OpenAPI documentation."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        return TestClient(app)
    
    def test_docs_endpoint(self, client):
        """Docs endpoint is available."""
        response = client.get("/docs")
        
        assert response.status_code == 200
    
    def test_openapi_json_endpoint(self, client):
        """OpenAPI JSON is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    def test_openapi_info(self, client):
        """OpenAPI has correct info."""
        response = client.get("/openapi.json")
        data = response.json()
        
        assert data["info"]["title"] == "Autonomous-GLM API"
        assert data["info"]["version"] == "0.1.0"