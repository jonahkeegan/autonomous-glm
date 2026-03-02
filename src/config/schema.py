"""
Pydantic models for configuration validation.

Defines typed configuration models with validation rules for all configuration sections.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Environment(str, Enum):
    """Supported environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Supported logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AppConfig(BaseModel):
    """Application-level configuration."""
    name: str = Field(default="autonomous-glm", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Running environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Ensure version is a valid semver-like string."""
        parts = v.split(".")
        if len(parts) < 2:
            raise ValueError(f"Invalid version format: {v}. Expected X.Y or X.Y.Z")
        return v


class PathsConfig(BaseModel):
    """Path configuration for all project directories."""
    data_dir: str = Field(default="./data", description="Data directory")
    artifacts_dir: str = Field(default="./data/artifacts", description="Artifacts directory")
    screenshots_dir: str = Field(default="./data/artifacts/screenshots", description="Screenshots directory")
    videos_dir: str = Field(default="./data/artifacts/videos", description="Videos directory")
    context_dir: str = Field(default="./data/artifacts/context", description="Context metadata directory")
    logs_dir: str = Field(default="./logs", description="Logs directory")
    output_dir: str = Field(default="./output", description="Output directory")
    reports_dir: str = Field(default="./output/reports", description="Reports directory")
    design_system_dir: str = Field(default="./design_system", description="Design system directory")
    memory_bank_dir: str = Field(default="./memory-bank", description="Memory bank directory")
    database_path: str = Field(default="./data/autonomous_glm.db", description="Database file path")


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    pool_size: int = Field(default=5, ge=1, le=100, description="Connection pool size")
    timeout: int = Field(default=30, ge=1, le=300, description="Connection timeout in seconds")


class AgentProtocolConfig(BaseModel):
    """Agent communication protocol configuration."""
    message_timeout: int = Field(
        default=5000,
        ge=100,
        le=60000,
        description="Message timeout in milliseconds"
    )
    retry_attempts: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of retry attempts"
    )
    retry_base_delay: int = Field(
        default=1000,
        ge=100,
        description="Base delay for retries in milliseconds"
    )
    retry_max_delay: int = Field(
        default=1800000,
        ge=1000,
        description="Maximum delay for retries in milliseconds"
    )

    @field_validator("retry_max_delay")
    @classmethod
    def validate_retry_delays(cls, v: int, info) -> int:
        """Ensure max delay is greater than base delay."""
        base_delay = info.data.get("retry_base_delay", 1000)
        if v < base_delay:
            raise ValueError("retry_max_delay must be greater than retry_base_delay")
        return v


class SingleAgentConfig(BaseModel):
    """Configuration for a single agent."""
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    endpoint: Optional[str] = Field(default=None, description="Optional custom endpoint URL")


class AgentsConfig(BaseModel):
    """Configuration for all collaborating agents."""
    claude: SingleAgentConfig = Field(default_factory=SingleAgentConfig)
    minimax: SingleAgentConfig = Field(default_factory=SingleAgentConfig)
    codex: SingleAgentConfig = Field(default_factory=SingleAgentConfig)


class CVPipelineConfig(BaseModel):
    """Computer Vision pipeline configuration."""
    model: str = Field(default="glm-5-vision", description="CV model to use")
    detection_threshold: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Detection confidence threshold"
    )
    batch_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Batch size for processing"
    )


class SeverityThresholdsConfig(BaseModel):
    """Severity threshold configuration for audit findings."""
    low: float = Field(default=0.0, ge=0.0, le=1.0)
    medium: float = Field(default=0.4, ge=0.0, le=1.0)
    high: float = Field(default=0.7, ge=0.0, le=1.0)
    critical: float = Field(default=0.9, ge=0.0, le=1.0)

    @field_validator("medium")
    @classmethod
    def validate_medium(cls, v: float, info) -> float:
        """Ensure medium > low."""
        low = info.data.get("low", 0.0)
        if v <= low:
            raise ValueError("medium threshold must be greater than low")
        return v

    @field_validator("high")
    @classmethod
    def validate_high(cls, v: float, info) -> float:
        """Ensure high > medium."""
        medium = info.data.get("medium", 0.4)
        if v <= medium:
            raise ValueError("high threshold must be greater than medium")
        return v

    @field_validator("critical")
    @classmethod
    def validate_critical(cls, v: float, info) -> float:
        """Ensure critical > high."""
        high = info.data.get("high", 0.7)
        if v <= high:
            raise ValueError("critical threshold must be greater than high")
        return v


class AuditConfig(BaseModel):
    """Audit engine configuration."""
    dimensions: list[str] = Field(
        default=[
            "visual_hierarchy",
            "spacing_rhythm",
            "typography",
            "color",
            "alignment_grid",
            "components",
            "iconography",
            "motion_transitions",
            "empty_states",
            "loading_states",
            "error_states",
            "dark_mode_theming",
            "density",
            "responsiveness",
            "accessibility",
        ],
        description="List of audit dimensions to evaluate"
    )
    severity_thresholds: SeverityThresholdsConfig = Field(
        default_factory=SeverityThresholdsConfig,
        description="Severity classification thresholds"
    )


class IngestionConfig(BaseModel):
    """Configuration for screenshot/video ingestion."""
    max_file_size_mb: float = Field(
        default=50.0,
        ge=0.1,
        le=1000.0,
        description="Maximum file size in megabytes"
    )
    min_width: int = Field(
        default=100,
        ge=1,
        description="Minimum image width in pixels"
    )
    min_height: int = Field(
        default=100,
        ge=1,
        description="Minimum image height in pixels"
    )
    max_width: int = Field(
        default=10000,
        ge=100,
        description="Maximum image width in pixels"
    )
    max_height: int = Field(
        default=10000,
        ge=100,
        description="Maximum image height in pixels"
    )
    allowed_formats: list[str] = Field(
        default=["png", "jpeg", "jpg"],
        description="List of allowed image formats"
    )
    
    @field_validator("max_width")
    @classmethod
    def validate_max_width(cls, v: int, info) -> int:
        """Ensure max_width > min_width."""
        min_width = info.data.get("min_width", 100)
        if v <= min_width:
            raise ValueError("max_width must be greater than min_width")
        return v
    
    @field_validator("max_height")
    @classmethod
    def validate_max_height(cls, v: int, info) -> int:
        """Ensure max_height > min_height."""
        min_height = info.data.get("min_height", 100)
        if v <= min_height:
            raise ValueError("max_height must be greater than min_height")
        return v


class VideoIngestionConfig(BaseModel):
    """Configuration for video ingestion."""
    max_file_size_mb: float = Field(
        default=500.0,
        ge=0.1,
        le=10000.0,
        description="Maximum video file size in megabytes"
    )
    max_duration_seconds: float = Field(
        default=1800.0,
        ge=1.0,
        le=7200.0,
        description="Maximum video duration in seconds"
    )
    max_width: int = Field(
        default=10000,
        ge=100,
        description="Maximum video width in pixels"
    )
    max_height: int = Field(
        default=10000,
        ge=100,
        description="Maximum video height in pixels"
    )
    allowed_containers: list[str] = Field(
        default=["mp4", "mov"],
        description="List of allowed container formats"
    )
    allowed_codecs: list[str] = Field(
        default=["h264", "h265", "hevc", "vp8", "vp9"],
        description="List of allowed video codecs"
    )
    extraction_interval: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Frame extraction interval in seconds"
    )
    max_frames: int = Field(
        default=500,
        ge=1,
        le=5000,
        description="Maximum number of frames to extract per video"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    file_rotation: str = Field(default="10 MB", description="Log file rotation size")
    file_count: int = Field(default=5, ge=1, le=100, description="Number of log files to keep")


class Config(BaseModel):
    """Root configuration model containing all configuration sections."""
    app: AppConfig = Field(default_factory=AppConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    agent_protocol: AgentProtocolConfig = Field(default_factory=AgentProtocolConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    cv_pipeline: CVPipelineConfig = Field(default_factory=CVPipelineConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    video_ingestion: VideoIngestionConfig = Field(default_factory=VideoIngestionConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
