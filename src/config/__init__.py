"""
Configuration management for Autonomous-GLM.

This module provides a flexible configuration system supporting:
- YAML-based configuration files
- Environment-specific overrides (development, staging, production)
- Environment variable overrides
- Path resolution utilities
- Type-safe validation via Pydantic

Quick Start:
    from src.config import get_config
    
    config = get_config()
    print(config.app.debug)
    print(config.paths.database_path)

Environment Variables:
    AUTONOMOUS_GLM_ENV - Environment (development|staging|production)
    AUTONOMOUS_GLM_DEBUG - Enable debug mode (true/false)
    AUTONOMOUS_GLM_LOG_LEVEL - Log level (DEBUG|INFO|WARNING|ERROR)
    AUTONOMOUS_GLM_DATA_DIR - Override data directory
    AUTONOMOUS_GLM_DATABASE_PATH - Override database path
    AUTONOMOUS_GLM_CONFIG_DIR - Custom config directory
"""

# Schema models
from .schema import (
    Config,
    AppConfig,
    PathsConfig,
    DatabaseConfig,
    AgentProtocolConfig,
    AgentsConfig,
    SingleAgentConfig,
    CVPipelineConfig,
    AuditConfig,
    SeverityThresholdsConfig,
    LoggingConfig,
    Environment,
    LogLevel,
)

# Loader functions
from .loader import (
    load_config,
    get_config,
    reload_config,
    clear_config,
    is_config_loaded,
    deep_merge,
)

# Path utilities
from .paths import (
    get_project_root,
    resolve_path,
    ensure_dir,
    get_default_config_dir,
    get_default_data_dir,
)

# Environment variable utilities
from .env import (
    get_env,
    get_env_bool,
    get_env_int,
    get_env_float,
    get_environment,
    get_log_level,
    is_debug,
    get_all_env_overrides,
    coerce_bool,
    coerce_int,
    coerce_float,
)

__all__ = [
    # Schema
    "Config",
    "AppConfig",
    "PathsConfig",
    "DatabaseConfig",
    "AgentProtocolConfig",
    "AgentsConfig",
    "SingleAgentConfig",
    "CVPipelineConfig",
    "AuditConfig",
    "SeverityThresholdsConfig",
    "LoggingConfig",
    "Environment",
    "LogLevel",
    # Loader
    "load_config",
    "get_config",
    "reload_config",
    "clear_config",
    "is_config_loaded",
    "deep_merge",
    # Paths
    "get_project_root",
    "resolve_path",
    "ensure_dir",
    "get_default_config_dir",
    "get_default_data_dir",
    # Environment
    "get_env",
    "get_env_bool",
    "get_env_int",
    "get_env_float",
    "get_environment",
    "get_log_level",
    "is_debug",
    "get_all_env_overrides",
    "coerce_bool",
    "coerce_int",
    "coerce_float",
]