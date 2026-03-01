# Epic M0-2: Configuration Management

> **Milestone:** 0 - Foundation  
> **Priority:** High  
> **Dependencies:** None (parallel with Epic M0-1)  
> **Status:** 🔲 Not Started

---

## Objective

Implement a flexible configuration management system that supports environment-specific settings, path resolution, and runtime overrides for the Autonomous UI/UX Design Agent.

---

## Scope

### In Scope
- YAML-based configuration file structure
- Environment variable support with fallbacks
- Path configuration for all project directories
- Agent protocol configuration (message formats, retry settings)
- Configuration validation on startup
- Default values and required field enforcement

### Out of Scope
- Secrets management (no runtime secrets in early phase)
- Remote configuration loading
- Hot-reload of configuration changes

---

## Configuration Schema

### Required Configuration Sections

```yaml
# Application
app:
  name: autonomous-glm
  version: 0.1.0
  environment: development | staging | production
  debug: bool

# Paths
paths:
  data_dir: string
  artifacts_dir: string
  screenshots_dir: string
  videos_dir: string
  context_dir: string
  logs_dir: string
  output_dir: string
  reports_dir: string
  design_system_dir: string
  memory_bank_dir: string
  database_path: string

# Database
database:
  pool_size: int
  timeout: int (seconds)

# Agent Protocol
agent_protocol:
  message_timeout: int (ms)
  retry_attempts: int
  retry_base_delay: int (ms)
  retry_max_delay: int (ms)
  
# Agents
agents:
  claude:
    enabled: bool
    endpoint: string (optional)
  minimax:
    enabled: bool
    endpoint: string (optional)
  codex:
    enabled: bool
    endpoint: string (optional)

# CV Pipeline
cv_pipeline:
  model: string
  detection_threshold: float
  batch_size: int

# Audit
audit:
  dimensions: list[string]
  severity_thresholds:
    low: float
    medium: float
    high: float
    critical: float

# Logging
logging:
  level: DEBUG | INFO | WARNING | ERROR
  format: string
  file_rotation: string (e.g., "10 MB")
  file_count: int
```

---

## Deliverables

### 1. Configuration Files (`config/`)

Create configuration hierarchy:
- `config/default.yaml` — Base configuration with all defaults
- `config/development.yaml` — Development environment overrides
- `config/staging.yaml` — Staging environment overrides
- `config/production.yaml` — Production environment overrides

### 2. Configuration Loader (`src/config/loader.py`)

Python module providing:
- `load_config(env: str = None)` — Load and merge configuration
- `get_config()` — Return current configuration singleton
- `reload_config()` — Force reload of configuration

### 3. Configuration Models (`src/config/schema.py`)

Pydantic models for:
- `AppConfig` — Application settings
- `PathsConfig` — Path configuration
- `DatabaseConfig` — Database settings
- `AgentProtocolConfig` — Agent communication settings
- `AgentsConfig` — Individual agent settings
- `CVPipelineConfig` — CV pipeline settings
- `AuditConfig` — Audit settings
- `LoggingConfig` — Logging settings
- `Config` — Root configuration model

### 4. Environment Variable Support (`src/config/env.py`)

Environment variable handling:
- `AUTONOMOUS_GLM_ENV` — Environment selection
- `AUTONOMOUS_GLM_CONFIG_DIR` — Custom config directory
- `AUTONOMOUS_GLM_DATA_DIR` — Override data directory
- `AUTONOMOUS_GLM_DEBUG` — Debug mode override
- `AUTONOMOUS_GLM_LOG_LEVEL` — Log level override

### 5. Path Resolution (`src/config/paths.py`)

Path utilities:
- `resolve_path(path: str)` — Resolve relative/absolute paths
- `ensure_dir(path: str)` — Create directory if not exists
- `get_project_root()` — Return project root directory

---

## Technical Decisions

### Configuration Format
- **Decision:** YAML for configuration files
- **Rationale:** Human-readable, supports comments, widely used

### Configuration Merging
- **Decision:** Deep merge with environment-specific overrides
- **Rationale:** Allows minimal override files, inherited defaults

### Validation
- **Decision:** Pydantic for configuration validation
- **Rationale:** Type safety, clear error messages, serialization support

### Singleton Pattern
- **Decision:** Single configuration instance per process
- **Rationale:** Consistent access, no repeated file I/O

---

## File Structure

```
config/
├── default.yaml
├── development.yaml
├── staging.yaml
└── production.yaml

src/
└── config/
    ├── __init__.py
    ├── loader.py
    ├── schema.py
    ├── env.py
    └── paths.py
```

---

## Tasks

### Phase 1: Configuration Schema
- [ ] Create `config/` directory
- [ ] Define `default.yaml` with all configuration sections
- [ ] Create `development.yaml` with dev overrides
- [ ] Create placeholder `staging.yaml` and `production.yaml`
- [ ] Add comments documenting each configuration option

### Phase 2: Configuration Models
- [ ] Create `src/config/` directory
- [ ] Implement Pydantic models in `schema.py`
- [ ] Add validation rules for required fields
- [ ] Add default values where appropriate
- [ ] Add docstrings for all models

### Phase 3: Configuration Loader
- [ ] Implement `loader.py` with YAML parsing
- [ ] Add deep merge for environment overrides
- [ ] Add environment detection (env var, default to development)
- [ ] Implement singleton pattern for configuration
- [ ] Add error handling for missing/invalid config

### Phase 4: Environment Variables
- [ ] Implement `env.py` with environment variable mapping
- [ ] Add support for all documented env vars
- [ ] Add type coercion for env var values
- [ ] Document environment variable usage

### Phase 5: Path Resolution
- [ ] Implement `paths.py` with path utilities
- [ ] Add project root detection
- [ ] Add relative path resolution
- [ ] Add directory creation utility

### Phase 6: Integration
- [ ] Wire all configuration modules together
- [ ] Add `get_config()` convenience function
- [ ] Test configuration loading from scratch
- [ ] Test environment variable overrides

---

## Success Criteria

- [ ] Configuration loads without errors
- [ ] All paths resolve correctly (relative and absolute)
- [ ] Environment overrides work as expected
- [ ] Missing required config produces helpful error messages
- [ ] Environment variables override file configuration
- [ ] Configuration accessible via simple `get_config()` call

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTONOMOUS_GLM_ENV` | `development` | Environment name |
| `AUTONOMOUS_GLM_CONFIG_DIR` | `./config` | Configuration directory |
| `AUTONOMOUS_GLM_DATA_DIR` | `./data` | Data directory override |
| `AUTONOMOUS_GLM_DEBUG` | `false` | Enable debug mode |
| `AUTONOMOUS_GLM_LOG_LEVEL` | From config | Log level override |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Invalid configuration at runtime | Pydantic validation on load, fail fast |
| Missing configuration files | Clear error messages with file paths |
| Path resolution issues | Comprehensive path testing, logging |

---

## Validation

Run after completion:
```bash
# Test configuration loading
python -c "from src.config import get_config; c = get_config(); print(c.model_dump())"

# Test environment override
AUTONOMOUS_GLM_DEBUG=true python -c "from src.config import get_config; print(get_config().app.debug)"

# Test path resolution
python -c "from src.config.paths import get_project_root; print(get_project_root())"
```

---

*Created: 2026-02-28*