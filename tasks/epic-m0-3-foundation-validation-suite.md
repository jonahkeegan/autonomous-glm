# Epic M0-3: Foundation Validation Suite

> **Milestone:** 0 - Foundation  
> **Priority:** High  
> **Dependencies:** Epic M0-1 (Database), Epic M0-2 (Configuration)  
> **Status:** ✅ COMPLETE

---

## Objective

Implement comprehensive validation infrastructure to verify that all foundation components are correctly initialized and operational, enabling confident progression to subsequent milestones.

---

## Scope

### In Scope
- JSON schema validation for all `/interfaces/*.schema.json` files
- Database schema verification tests
- Directory structure validation
- Design system file validation (parseable tokens, components, standards)
- Memory bank file validation
- Startup health check script
- Test framework initialization (pytest)

### Out of Scope
- CV pipeline validation (M2)
- API endpoint testing (M1)
- Agent communication testing (M5)
- Performance benchmarks (M7)

---

## Validation Categories

### 1. Schema Validation
Validate all JSON schemas in `/interfaces/`:
- `audit-complete.schema.json`
- `design-proposal.schema.json`
- `dispute.schema.json`
- `human-required.schema.json`

### 2. Database Validation
Verify database foundation:
- Database file exists and is accessible
- All required tables exist
- All columns have correct types
- Foreign key constraints are enforced
- Indexes are created

### 3. Directory Validation
Verify directory structure:
- All required directories exist
- Directories are writable
- `.gitkeep` files present for empty directories

### 4. Design System Validation
Verify design system files:
- `tokens.md` is parseable
- `components.md` is parseable
- `standards.md` is parseable
- Required sections exist in each file

### 5. Memory Bank Validation
Verify memory bank files:
- All required files exist
- JSON files are valid (`skill-matrix.json`)
- Markdown files have correct headers

### 6. Configuration Validation
Verify configuration:
- Configuration loads without errors
- All required paths resolve
- Environment variables work

---

## Deliverables

### 1. Test Framework Setup (`tests/`)

Initialize pytest infrastructure:
- `tests/conftest.py` — Shared fixtures and configuration ✅
- `tests/__init__.py` — Test package initialization ✅
- `pytest.ini` — Pytest configuration ✅
- `requirements-test.txt` — Test dependencies ✅

### 2. Schema Validation Tests (`tests/unit/test_schema_validation.py`) ✅

Test all JSON schemas:
- Schema files are valid JSON
- Schema files conform to JSON Schema draft-07
- Required fields are documented
- Enum values are consistent across schemas

### 3. Database Tests (`tests/unit/test_database.py`) ✅

Test database foundation:
- Database initialization succeeds
- All tables created with correct schema
- CRUD operations work for all entities
- Foreign key constraints enforced
- Migrations run idempotently

### 4. Configuration Tests (`tests/unit/test_config.py`) ✅

Test configuration system:
- Configuration loads from files
- Environment variables override correctly
- Path resolution works
- Missing config produces clear errors

### 5. Directory Tests (`tests/unit/test_directories.py`) ✅

Test directory structure:
- All required directories exist
- Directories are writable
- Artifact subdirectories correct

### 6. Design System Tests (`tests/unit/test_design_system.py`) ✅

Test design system files:
- All markdown files parseable
- Required token categories present
- Component categories documented
- Standards sections exist

### 7. Memory Bank Tests (`tests/unit/test_memory_bank.py`) ✅

Test memory bank files:
- All required files exist
- JSON files valid
- Markdown structure correct

### 8. Health Check Script (`scripts/health_check.py`) ✅

Comprehensive startup validation:
- Run all validation checks
- Report status for each category
- Exit 0 on success, non-zero on failure
- Generate report in `/output/reports/health_check.md`

---

## Technical Decisions

### Test Framework
- **Decision:** pytest with pytest-cov for coverage
- **Rationale:** Industry standard, excellent fixtures, coverage integration

### Validation Approach
- **Decision:** Fail-fast on critical issues, warn on non-critical
- **Rationale:** Clear signal for blocking issues, visibility for improvements

### Health Check Output
- **Decision:** Terminal output + Markdown report
- **Rationale:** Immediate feedback + persistent record

### Test Organization
- **Decision:** Mirror `src/` structure in `tests/`
- **Rationale:** Easy to find tests for specific modules

---

## File Structure

```
tests/
├── __init__.py
├── conftest.py
├── pytest.ini
├── unit/
│   ├── __init__.py
│   ├── test_schema_validation.py
│   ├── test_database.py
│   ├── test_config.py
│   ├── test_directories.py
│   ├── test_design_system.py
│   └── test_memory_bank.py
└── fixtures/
    └── __init__.py

scripts/
└── health_check.py

requirements-test.txt
```

---

## Tasks

### Phase 1: Test Framework Setup
- [x] Create `tests/conftest.py` with shared fixtures
- [x] Create `pytest.ini` with configuration
- [x] Create `requirements-test.txt` with dependencies
- [x] Verify pytest runs successfully

### Phase 2: Schema Validation Tests
- [x] Create `tests/unit/test_schema_validation.py`
- [x] Test each schema file is valid JSON
- [x] Test schemas conform to JSON Schema draft-07
- [x] Test cross-schema consistency (agent names, message types)

### Phase 3: Database Tests
- [x] Create `tests/unit/test_database.py`
- [x] Test database initialization
- [x] Test table creation for all entities
- [x] Test CRUD operations
- [x] Test foreign key constraints

### Phase 4: Configuration Tests
- [x] Create `tests/unit/test_config.py`
- [x] Test configuration loading
- [x] Test environment variable overrides
- [x] Test path resolution
- [x] Test validation errors

### Phase 5: Directory & File Tests
- [x] Create `tests/unit/test_directories.py`
- [x] Create `tests/unit/test_design_system.py`
- [x] Create `tests/unit/test_memory_bank.py`
- [x] Test all required files exist
- [x] Test all files are parseable

### Phase 6: Health Check Script
- [x] Create `scripts/health_check.py`
- [x] Implement all validation checks
- [x] Add terminal output with status indicators
- [x] Add Markdown report generation
- [x] Add exit codes for CI integration

### Phase 7: Integration
- [x] Run full test suite
- [x] Verify health check passes
- [x] Generate coverage report
- [x] Document test running in README

---

## Success Criteria

- [x] All unit tests pass (233/233)
- [x] Test coverage > 80% for foundation code (83%)
- [x] Health check script exits 0 on clean state
- [x] Health check generates readable report
- [x] All JSON schemas validate successfully
- [x] Database tests confirm schema correctness
- [x] Configuration tests confirm loading works

---

## Test Dependencies

```
# requirements-test.txt
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-json-report>=1.5.0
jsonschema>=4.0.0
pyyaml>=6.0
```

---

## Health Check Output Format

### Terminal Output
```
Autonomous GLM Health Check
==========================

[✓] Schema Validation        4/4 schemas valid
[✓] Database                 Connected, 6 tables
[✓] Configuration            Loaded (development)
[✓] Directories              10/10 directories ready
[✓] Design System            3/3 files parseable
[✓] Memory Bank              5/5 files valid

Status: HEALTHY
```

### Markdown Report
Generated at `/output/reports/health_check.md` with:
- Timestamp
- Environment details
- Detailed results per category
- Warnings and recommendations
- Next steps if issues found

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Tests too slow for rapid iteration | Unit tests only, integration in M7 |
| Flaky tests from file system | Use fixtures, mock where appropriate |
| Coverage targets block progress | 80% target, not 90% for foundation |

---

## Validation

Run after completion:
```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run with coverage
python -m pytest tests/unit/ --cov=src --cov-report=term-missing

# Run health check
python scripts/health_check.py

# Verify health check report
cat output/reports/health_check.md
```

---

## Completion Summary

**Completed:** 2026-03-01  
**Total Tests:** 233  
**Coverage:** 83%  
**Health Check:** 6/6 categories passing

### Files Created
- `tests/conftest.py`
- `tests/pytest.ini`
- `tests/requirements-test.txt`
- `tests/unit/test_schema_validation.py` (40 tests)
- `tests/unit/test_directories.py` (46 tests)
- `tests/unit/test_design_system.py` (27 tests)
- `tests/unit/test_memory_bank.py` (31 tests)
- `scripts/health_check.py`

---

*Created: 2026-02-28*  
*Completed: 2026-03-01*