"""
Environment variable support for configuration.

Maps environment variables to configuration values with type coercion.
"""

import os
from typing import Any, Optional

from .schema import Environment, LogLevel


# Environment variable prefix
ENV_PREFIX = "AUTONOMOUS_GLM_"

# Mapping of environment variables to config paths
ENV_VAR_MAPPING = {
    "AUTONOMOUS_GLM_ENV": ("app", "environment"),
    "AUTONOMOUS_GLM_CONFIG_DIR": ("_config_dir",),  # Special: not in config schema
    "AUTONOMOUS_GLM_DATA_DIR": ("paths", "data_dir"),
    "AUTONOMOUS_GLM_DEBUG": ("app", "debug"),
    "AUTONOMOUS_GLM_LOG_LEVEL": ("logging", "level"),
    "AUTONOMOUS_GLM_DATABASE_PATH": ("paths", "database_path"),
}


def get_env_var(name: str) -> Optional[str]:
    """
    Get an environment variable value.
    
    Args:
        name: The environment variable name (with or without prefix).
    
    Returns:
        The environment variable value, or None if not set.
    """
    if not name.startswith(ENV_PREFIX):
        name = f"{ENV_PREFIX}{name}"
    return os.environ.get(name)


def get_env(name: str, default: Any = None) -> Any:
    """
    Get an environment variable with optional default.
    
    Args:
        name: The environment variable name (without prefix).
        default: Default value if not set.
    
    Returns:
        The environment variable value or default.
    """
    full_name = f"{ENV_PREFIX}{name}" if not name.startswith(ENV_PREFIX) else name
    value = os.environ.get(full_name)
    return value if value is not None else default


def coerce_bool(value: str) -> bool:
    """
    Coerce a string to boolean.
    
    Args:
        value: The string value to coerce.
    
    Returns:
        Boolean representation.
    
    Raises:
        ValueError: If value cannot be coerced.
    """
    true_values = {"true", "1", "yes", "on", "enabled"}
    false_values = {"false", "0", "no", "off", "disabled", ""}
    
    lower = value.lower().strip()
    if lower in true_values:
        return True
    elif lower in false_values:
        return False
    else:
        raise ValueError(f"Cannot coerce '{value}' to boolean")


def coerce_int(value: str) -> int:
    """
    Coerce a string to integer.
    
    Args:
        value: The string value to coerce.
    
    Returns:
        Integer representation.
    
    Raises:
        ValueError: If value cannot be coerced.
    """
    return int(value)


def coerce_float(value: str) -> float:
    """
    Coerce a string to float.
    
    Args:
        value: The string value to coerce.
    
    Returns:
        Float representation.
    
    Raises:
        ValueError: If value cannot be coerced.
    """
    return float(value)


def get_env_bool(name: str, default: bool = False) -> bool:
    """
    Get a boolean environment variable.
    
    Args:
        name: The environment variable name (without prefix).
        default: Default value if not set.
    
    Returns:
        Boolean value.
    """
    value = get_env(name)
    if value is None:
        return default
    try:
        return coerce_bool(value)
    except ValueError:
        return default


def get_env_int(name: str, default: int = 0) -> int:
    """
    Get an integer environment variable.
    
    Args:
        name: The environment variable name (without prefix).
        default: Default value if not set.
    
    Returns:
        Integer value.
    """
    value = get_env(name)
    if value is None:
        return default
    try:
        return coerce_int(value)
    except ValueError:
        return default


def get_env_float(name: str, default: float = 0.0) -> float:
    """
    Get a float environment variable.
    
    Args:
        name: The environment variable name (without prefix).
        default: Default value if not set.
    
    Returns:
        Float value.
    """
    value = get_env(name)
    if value is None:
        return default
    try:
        return coerce_float(value)
    except ValueError:
        return default


def get_environment() -> Environment:
    """
    Get the current environment from AUTONOMOUS_GLM_ENV.
    
    Returns:
        Environment enum value. Defaults to DEVELOPMENT.
    """
    value = get_env("ENV")
    if value is None:
        return Environment.DEVELOPMENT
    
    try:
        return Environment(value.lower())
    except ValueError:
        valid = [e.value for e in Environment]
        raise ValueError(
            f"Invalid environment '{value}'. Must be one of: {valid}"
        )


def get_log_level() -> Optional[LogLevel]:
    """
    Get the log level from AUTONOMOUS_GLM_LOG_LEVEL.
    
    Returns:
        LogLevel enum value, or None if not set.
    """
    value = get_env("LOG_LEVEL")
    if value is None:
        return None
    
    try:
        return LogLevel(value.upper())
    except ValueError:
        valid = [l.value for l in LogLevel]
        raise ValueError(
            f"Invalid log level '{value}'. Must be one of: {valid}"
        )


def get_config_dir() -> Optional[str]:
    """
    Get custom config directory from AUTONOMOUS_GLM_CONFIG_DIR.
    
    Returns:
        Config directory path, or None if using default.
    """
    return get_env("CONFIG_DIR")


def get_data_dir() -> Optional[str]:
    """
    Get custom data directory from AUTONOMOUS_GLM_DATA_DIR.
    
    Returns:
        Data directory path, or None if using default.
    """
    return get_env("DATA_DIR")


def is_debug() -> bool:
    """
    Check if debug mode is enabled via AUTONOMOUS_GLM_DEBUG.
    
    Returns:
        True if debug mode is enabled.
    """
    return get_env_bool("DEBUG", default=False)


def get_all_env_overrides() -> dict[str, Any]:
    """
    Get all configuration overrides from environment variables.
    
    Returns:
        Dictionary of config path tuples to values.
    """
    overrides = {}
    
    # Environment
    env = get_env("ENV")
    if env:
        try:
            overrides[("app", "environment")] = Environment(env.lower())
        except ValueError:
            pass
    
    # Debug
    debug = get_env("DEBUG")
    if debug:
        try:
            overrides[("app", "debug")] = coerce_bool(debug)
        except ValueError:
            pass
    
    # Log level
    log_level = get_env("LOG_LEVEL")
    if log_level:
        try:
            overrides[("logging", "level")] = LogLevel(log_level.upper())
        except ValueError:
            pass
    
    # Data directory
    data_dir = get_env("DATA_DIR")
    if data_dir:
        overrides[("paths", "data_dir")] = data_dir
    
    # Database path
    db_path = get_env("DATABASE_PATH")
    if db_path:
        overrides[("paths", "database_path")] = db_path
    
    return overrides