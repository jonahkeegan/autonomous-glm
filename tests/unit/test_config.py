"""
Unit tests for Autonomous-GLM configuration management.

Tests cover schema validation, configuration loading, environment variables,
and path resolution.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import (
    # Schema
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
    # Loader
    load_config,
    get_config,
    reload_config,
    clear_config,
    is_config_loaded,
    deep_merge,
    # Paths
    get_project_root,
    resolve_path,
    ensure_dir,
    get_default_config_dir,
    get_default_data_dir,
    # Environment
    get_env,
    get_env_bool,
    get_env_int,
    get_env_float,
    get_environment,
    get_log_level,
    is_debug,
    coerce_bool,
    coerce_int,
    coerce_float,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def clear_config_cache():
    """Clear config cache before and after each test."""
    clear_config()
    yield
    clear_config()


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "config"
        config_dir.mkdir()
        
        # Create default.yaml
        default_yaml = config_dir / "default.yaml"
        default_yaml.write_text("""
app:
  name: test-app
  version: "1.0.0"
  environment: development
  debug: false

paths:
  data_dir: "./data"
  database_path: "./data/test.db"

database:
  pool_size: 5
  timeout: 30

agent_protocol:
  message_timeout: 5000
  retry_attempts: 3
  retry_base_delay: 1000
  retry_max_delay: 1800000

logging:
  level: INFO
  format: "%(message)s"
  file_rotation: "10 MB"
  file_count: 5
""")
        
        # Create development.yaml
        dev_yaml = config_dir / "development.yaml"
        dev_yaml.write_text("""
app:
  debug: true

logging:
  level: DEBUG
""")
        
        # Create production.yaml
        prod_yaml = config_dir / "production.yaml"
        prod_yaml.write_text("""
app:
  environment: production
  debug: false

logging:
  level: WARNING
""")
        
        yield config_dir


# =============================================================================
# SCHEMA MODEL TESTS
# =============================================================================

class TestAppConfig:
    """Tests for AppConfig model."""
    
    def test_default_values(self):
        """AppConfig has correct defaults."""
        config = AppConfig()
        assert config.name == "autonomous-glm"
        assert config.version == "0.1.0"
        assert config.environment == Environment.DEVELOPMENT
        assert config.debug is False
    
    def test_custom_values(self):
        """AppConfig accepts custom values."""
        config = AppConfig(
            name="custom-app",
            version="2.0.0",
            environment=Environment.PRODUCTION,
            debug=True
        )
        assert config.name == "custom-app"
        assert config.version == "2.0.0"
        assert config.environment == Environment.PRODUCTION
        assert config.debug is True
    
    def test_invalid_version(self):
        """AppConfig rejects invalid version format."""
        with pytest.raises(ValueError):
            AppConfig(version="invalid")
    
    def test_valid_version_two_parts(self):
        """AppConfig accepts two-part version."""
        config = AppConfig(version="1.0")
        assert config.version == "1.0"


class TestDatabaseConfig:
    """Tests for DatabaseConfig model."""
    
    def test_default_values(self):
        """DatabaseConfig has correct defaults."""
        config = DatabaseConfig()
        assert config.pool_size == 5
        assert config.timeout == 30
    
    def test_pool_size_validation(self):
        """DatabaseConfig validates pool_size bounds."""
        DatabaseConfig(pool_size=1)  # Minimum
        DatabaseConfig(pool_size=100)  # Maximum
        
        with pytest.raises(ValueError):
            DatabaseConfig(pool_size=0)
        
        with pytest.raises(ValueError):
            DatabaseConfig(pool_size=101)


class TestAgentProtocolConfig:
    """Tests for AgentProtocolConfig model."""
    
    def test_default_values(self):
        """AgentProtocolConfig has correct defaults."""
        config = AgentProtocolConfig()
        assert config.message_timeout == 5000
        assert config.retry_attempts == 3
    
    def test_retry_delay_validation(self):
        """retry_max_delay must be greater than retry_base_delay."""
        with pytest.raises(ValueError):
            AgentProtocolConfig(retry_base_delay=1000, retry_max_delay=500)


class TestSeverityThresholdsConfig:
    """Tests for SeverityThresholdsConfig model."""
    
    def test_default_values(self):
        """SeverityThresholdsConfig has correct defaults."""
        config = SeverityThresholdsConfig()
        assert config.low == 0.0
        assert config.medium == 0.4
        assert config.high == 0.7
        assert config.critical == 0.9
    
    def test_threshold_ordering(self):
        """Thresholds must be ordered low < medium < high < critical."""
        with pytest.raises(ValueError):
            SeverityThresholdsConfig(medium=0.0)  # medium <= low
        
        with pytest.raises(ValueError):
            SeverityThresholdsConfig(high=0.4)  # high <= medium
        
        with pytest.raises(ValueError):
            SeverityThresholdsConfig(critical=0.7)  # critical <= high
    
    def test_custom_thresholds(self):
        """Custom thresholds work when properly ordered."""
        config = SeverityThresholdsConfig(
            low=0.1,
            medium=0.3,
            high=0.6,
            critical=0.9
        )
        assert config.low == 0.1
        assert config.medium == 0.3


class TestLoggingConfig:
    """Tests for LoggingConfig model."""
    
    def test_default_values(self):
        """LoggingConfig has correct defaults."""
        config = LoggingConfig()
        assert config.level == LogLevel.INFO
        assert "asctime" in config.format
    
    def test_log_level_enum(self):
        """LoggingConfig accepts LogLevel enum."""
        config = LoggingConfig(level=LogLevel.DEBUG)
        assert config.level == LogLevel.DEBUG


class TestConfig:
    """Tests for root Config model."""
    
    def test_default_values(self):
        """Config has all default sections."""
        config = Config()
        assert config.app is not None
        assert config.paths is not None
        assert config.database is not None
        assert config.logging is not None
    
    def test_nested_access(self):
        """Config allows nested attribute access."""
        config = Config()
        assert config.app.name == "autonomous-glm"
        assert config.database.pool_size == 5


# =============================================================================
# DEEP MERGE TESTS
# =============================================================================

class TestDeepMerge:
    """Tests for deep_merge function."""
    
    def test_simple_override(self):
        """Simple values are overridden."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}
    
    def test_nested_merge(self):
        """Nested dictionaries are merged recursively."""
        base = {"app": {"name": "base", "debug": False}}
        override = {"app": {"debug": True}}
        result = deep_merge(base, override)
        assert result == {"app": {"name": "base", "debug": True}}
    
    def test_deeply_nested(self):
        """Deeply nested dictionaries merge correctly."""
        base = {"a": {"b": {"c": 1}}}
        override = {"a": {"b": {"d": 2}}}
        result = deep_merge(base, override)
        assert result == {"a": {"b": {"c": 1, "d": 2}}}
    
    def test_override_replaces_non_dict(self):
        """Non-dict values in override replace base values."""
        base = {"a": [1, 2, 3]}
        override = {"a": [4, 5]}
        result = deep_merge(base, override)
        assert result == {"a": [4, 5]}


# =============================================================================
# ENVIRONMENT VARIABLE TESTS
# =============================================================================

class TestCoercion:
    """Tests for type coercion functions."""
    
    def test_coerce_bool_true(self):
        """coerce_bool handles true values."""
        assert coerce_bool("true") is True
        assert coerce_bool("TRUE") is True
        assert coerce_bool("1") is True
        assert coerce_bool("yes") is True
        assert coerce_bool("on") is True
    
    def test_coerce_bool_false(self):
        """coerce_bool handles false values."""
        assert coerce_bool("false") is False
        assert coerce_bool("FALSE") is False
        assert coerce_bool("0") is False
        assert coerce_bool("no") is False
        assert coerce_bool("") is False
    
    def test_coerce_bool_invalid(self):
        """coerce_bool rejects invalid values."""
        with pytest.raises(ValueError):
            coerce_bool("maybe")
    
    def test_coerce_int(self):
        """coerce_int converts strings to integers."""
        assert coerce_int("42") == 42
        assert coerce_int("-10") == -10
    
    def test_coerce_float(self):
        """coerce_float converts strings to floats."""
        assert coerce_float("3.14") == 3.14
        assert coerce_float("-0.5") == -0.5


class TestEnvFunctions:
    """Tests for environment variable functions."""
    
    def test_get_env_with_prefix(self):
        """get_env works with AUTONOMOUS_GLM_ prefix."""
        with patch.dict(os.environ, {"AUTONOMOUS_GLM_TEST": "value"}):
            assert get_env("TEST") == "value"
    
    def test_get_env_default(self):
        """get_env returns default for missing variables."""
        assert get_env("NONEXISTENT", default="default") == "default"
    
    def test_get_env_bool(self):
        """get_env_bool coerces to boolean."""
        with patch.dict(os.environ, {"AUTONOMOUS_GLM_DEBUG": "true"}):
            assert get_env_bool("DEBUG") is True
        
        with patch.dict(os.environ, {"AUTONOMOUS_GLM_DEBUG": "false"}):
            assert get_env_bool("DEBUG") is False
    
    def test_get_env_int(self):
        """get_env_int coerces to integer."""
        with patch.dict(os.environ, {"AUTONOMOUS_GLM_COUNT": "42"}):
            assert get_env_int("COUNT") == 42
    
    def test_get_environment(self):
        """get_environment returns Environment enum."""
        with patch.dict(os.environ, {"AUTONOMOUS_GLM_ENV": "production"}):
            assert get_environment() == Environment.PRODUCTION
        
        with patch.dict(os.environ, {"AUTONOMOUS_GLM_ENV": "staging"}):
            assert get_environment() == Environment.STAGING
    
    def test_get_environment_default(self):
        """get_environment defaults to DEVELOPMENT."""
        # Clear the env var if set
        with patch.dict(os.environ, {}, clear=True):
            # Remove AUTONOMOUS_GLM_ENV if it exists
            os.environ.pop("AUTONOMOUS_GLM_ENV", None)
            assert get_environment() == Environment.DEVELOPMENT
    
    def test_get_environment_invalid(self):
        """get_environment rejects invalid values."""
        with patch.dict(os.environ, {"AUTONOMOUS_GLM_ENV": "invalid"}):
            with pytest.raises(ValueError):
                get_environment()
    
    def test_is_debug(self):
        """is_debug returns debug mode status."""
        with patch.dict(os.environ, {"AUTONOMOUS_GLM_DEBUG": "true"}):
            assert is_debug() is True
        
        with patch.dict(os.environ, {"AUTONOMOUS_GLM_DEBUG": "false"}):
            assert is_debug() is False


# =============================================================================
# PATH RESOLUTION TESTS
# =============================================================================

class TestPathResolution:
    """Tests for path resolution functions."""
    
    def test_get_project_root(self):
        """get_project_root finds the project root."""
        root = get_project_root()
        assert root is not None
        assert (root / "config").exists()
        assert (root / "src").exists()
    
    def test_resolve_path_relative(self):
        """resolve_path handles relative paths."""
        result = resolve_path("./data/test.db")
        assert result.is_absolute()
        assert "data/test.db" in str(result) or "data" in str(result)
    
    def test_resolve_path_absolute(self):
        """resolve_path preserves absolute paths."""
        result = resolve_path("/absolute/path")
        assert result == Path("/absolute/path")
    
    def test_resolve_path_with_base(self):
        """resolve_path uses custom base directory."""
        base = Path("/custom/base")
        result = resolve_path("./file.txt", base=base)
        assert result == Path("/custom/base/file.txt")
    
    def test_ensure_dir(self):
        """ensure_dir creates directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "nested" / "dir"
            result = ensure_dir(new_dir)
            assert new_dir.exists()
            assert new_dir.is_dir()
            assert result == new_dir
    
    def test_get_default_config_dir(self):
        """get_default_config_dir returns config directory."""
        config_dir = get_default_config_dir()
        assert config_dir.name == "config"
        assert config_dir.exists()
    
    def test_get_default_data_dir(self):
        """get_default_data_dir returns data directory."""
        data_dir = get_default_data_dir()
        assert data_dir.name == "data"


# =============================================================================
# CONFIGURATION LOADER TESTS
# =============================================================================

class TestConfigLoader:
    """Tests for configuration loading."""
    
    def test_load_config(self, temp_config_dir):
        """load_config loads configuration from files."""
        config = load_config(config_dir=temp_config_dir)
        assert config.app.name == "test-app"
        assert config.app.version == "1.0.0"
    
    def test_load_config_environment_override(self, temp_config_dir):
        """load_config applies environment-specific overrides."""
        # Development environment (default)
        config = load_config(env=Environment.DEVELOPMENT, config_dir=temp_config_dir)
        assert config.app.debug is True
        assert config.logging.level == LogLevel.DEBUG
    
    def test_load_config_production(self, temp_config_dir):
        """load_config loads production configuration."""
        config = load_config(env=Environment.PRODUCTION, config_dir=temp_config_dir)
        assert config.app.environment == Environment.PRODUCTION
        assert config.logging.level == LogLevel.WARNING
    
    def test_get_config_singleton(self, temp_config_dir):
        """get_config returns singleton instance."""
        clear_config()
        
        config1 = load_config(config_dir=temp_config_dir)
        config2 = get_config()
        
        assert config1 is config2
    
    def test_reload_config(self, temp_config_dir):
        """reload_config forces reload from files."""
        config1 = load_config(config_dir=temp_config_dir)
        config2 = reload_config()
        
        # reload_config uses default config dir, so we get default values
        # The key test is that a new instance is created
        assert config2 is not None
        assert config2.app.name == "autonomous-glm"  # Default value
    
    def test_is_config_loaded(self, temp_config_dir):
        """is_config_loaded reports load status."""
        clear_config()
        assert is_config_loaded() is False
        
        load_config(config_dir=temp_config_dir)
        assert is_config_loaded() is True
        
        clear_config()
        assert is_config_loaded() is False
    
    def test_missing_config_file(self):
        """load_config raises error for missing config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                load_config(config_dir=Path(tmpdir))
    
    def test_env_var_override(self, temp_config_dir):
        """Environment variables override file configuration."""
        with patch.dict(os.environ, {"AUTONOMOUS_GLM_DEBUG": "false"}):
            config = load_config(
                env=Environment.DEVELOPMENT,
                config_dir=temp_config_dir
            )
            # Env var should override development.yaml debug=true
            assert config.app.debug is False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """End-to-end integration tests."""
    
    def test_full_config_loading(self, temp_config_dir):
        """Complete configuration loading workflow."""
        # Load configuration
        config = load_config(
            env=Environment.DEVELOPMENT,
            config_dir=temp_config_dir
        )
        
        # Verify all sections are accessible
        assert config.app.name == "test-app"
        assert config.paths.data_dir == "./data"
        assert config.database.pool_size == 5
        assert config.agent_protocol.message_timeout == 5000
        assert config.logging.level == LogLevel.DEBUG
    
    def test_config_with_env_vars(self, temp_config_dir):
        """Configuration with environment variable overrides."""
        with patch.dict(os.environ, {
            "AUTONOMOUS_GLM_ENV": "production",
            "AUTONOMOUS_GLM_DEBUG": "true",
        }):
            clear_config()
            config = load_config(config_dir=temp_config_dir)
            
            # Should use production config
            assert config.logging.level == LogLevel.WARNING
            # But env var overrides debug
            assert config.app.debug is True
    
    def test_path_resolution_integration(self, temp_config_dir):
        """Path resolution works with loaded configuration."""
        config = load_config(config_dir=temp_config_dir)
        
        # Resolve database path
        db_path = resolve_path(config.paths.database_path)
        assert db_path.is_absolute()
        assert "data" in str(db_path)