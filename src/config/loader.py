"""
Configuration loader for Autonomous-GLM.

Handles YAML file loading, environment-specific merging, and singleton management.
"""

from pathlib import Path
from typing import Any, Optional

import yaml

from .schema import Config, Environment
from .paths import get_project_root, get_default_config_dir
from .env import (
    get_environment,
    get_config_dir,
    get_all_env_overrides,
)


# Singleton instance
_config_instance: Optional[Config] = None


def deep_merge(base: dict, override: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Values in override take precedence over base. Nested dictionaries
    are merged recursively.
    
    Args:
        base: The base dictionary.
        override: The override dictionary (values take precedence).
    
    Returns:
        A new dictionary with merged values.
    """
    result = base.copy()
    
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def load_yaml_file(path: Path) -> dict:
    """
    Load a YAML file.
    
    Args:
        path: Path to the YAML file.
    
    Returns:
        Dictionary with file contents.
    
    Raises:
        FileNotFoundError: If file doesn't exist.
        yaml.YAMLError: If YAML parsing fails.
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def get_config_files(env: Optional[Environment] = None, config_dir: Optional[Path] = None) -> tuple[Path, Path]:
    """
    Get paths to default and environment-specific config files.
    
    Args:
        env: The environment to load. Defaults to auto-detected environment.
        config_dir: Custom config directory. Defaults to project config/.
    
    Returns:
        Tuple of (default_config_path, env_config_path).
    """
    if config_dir is None:
        config_dir_str = get_config_dir()
        if config_dir_str:
            config_dir = Path(config_dir_str)
        else:
            config_dir = get_default_config_dir()
    
    if env is None:
        env = get_environment()
    
    default_path = config_dir / "default.yaml"
    env_path = config_dir / f"{env.value}.yaml"
    
    return default_path, env_path


def load_raw_config(
    env: Optional[Environment] = None,
    config_dir: Optional[Path] = None
) -> dict:
    """
    Load raw configuration dictionary from YAML files.
    
    Loads default.yaml first, then merges environment-specific overrides.
    
    Args:
        env: The environment to load. Defaults to auto-detected environment.
        config_dir: Custom config directory.
    
    Returns:
        Merged configuration dictionary.
    
    Raises:
        FileNotFoundError: If default.yaml doesn't exist.
        yaml.YAMLError: If YAML parsing fails.
    """
    default_path, env_path = get_config_files(env, config_dir)
    
    # Load default configuration
    config = load_yaml_file(default_path)
    
    # Merge environment-specific configuration if it exists
    if env_path.exists():
        env_config = load_yaml_file(env_path)
        config = deep_merge(config, env_config)
    
    return config


def apply_env_overrides(config: dict, overrides: dict[tuple, Any]) -> dict:
    """
    Apply environment variable overrides to configuration.
    
    Args:
        config: The configuration dictionary.
        overrides: Dictionary of path tuples to values.
    
    Returns:
        Updated configuration dictionary.
    """
    for path, value in overrides.items():
        if len(path) == 1:
            # Top-level key (special cases like _config_dir)
            continue
        
        # Navigate to the nested location
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[path[-1]] = value
    
    return config


def load_config(
    env: Optional[Environment] = None,
    config_dir: Optional[Path] = None,
    reload: bool = False
) -> Config:
    """
    Load and validate configuration.
    
    Configuration is loaded in this order (later overrides earlier):
    1. default.yaml
    2. <environment>.yaml (development.yaml, staging.yaml, production.yaml)
    3. Environment variables (AUTONOMOUS_GLM_*)
    
    Args:
        env: The environment to load. Defaults to AUTONOMOUS_GLM_ENV or development.
        config_dir: Custom config directory. Defaults to AUTONOMOUS_GLM_CONFIG_DIR or ./config.
        reload: Force reload even if cached. Defaults to False.
    
    Returns:
        Validated Config object.
    
    Raises:
        FileNotFoundError: If required config files are missing.
        ValueError: If configuration validation fails.
    """
    global _config_instance
    
    # Return cached instance if available and not forcing reload
    if _config_instance is not None and not reload:
        return _config_instance
    
    # Detect environment if not provided
    if env is None:
        env = get_environment()
    
    # Load raw configuration from YAML files
    config_dict = load_raw_config(env, config_dir)
    
    # Apply environment variable overrides
    env_overrides = get_all_env_overrides()
    config_dict = apply_env_overrides(config_dict, env_overrides)
    
    # Validate and create Config object
    try:
        _config_instance = Config(**config_dict)
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}") from e
    
    return _config_instance


def get_config() -> Config:
    """
    Get the current configuration singleton.
    
    Loads configuration on first access. Subsequent calls return
    the cached instance.
    
    Returns:
        Validated Config object.
    
    Raises:
        FileNotFoundError: If config files are missing.
        ValueError: If configuration validation fails.
    """
    global _config_instance
    
    if _config_instance is None:
        return load_config()
    
    return _config_instance


def reload_config() -> Config:
    """
    Force reload configuration from files.
    
    Clears the cached instance and reloads from YAML files and
    environment variables.
    
    Returns:
        Newly loaded Config object.
    """
    return load_config(reload=True)


def clear_config() -> None:
    """
    Clear the cached configuration instance.
    
    Useful for testing or when configuration needs to be completely reset.
    """
    global _config_instance
    _config_instance = None


def is_config_loaded() -> bool:
    """
    Check if configuration has been loaded.
    
    Returns:
        True if configuration is cached.
    """
    return _config_instance is not None