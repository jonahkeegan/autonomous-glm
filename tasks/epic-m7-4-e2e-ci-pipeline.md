# Epic M7-4: E2E & CI Pipeline

> **Milestone:** 7 - Testing Infrastructure  
> **Priority:** High  
> **Dependencies:** Epic M7-1 (Golden Dataset), Epic M7-2 (Coverage), Epic M7-3 (Integration)  
> **Status:** 🔲 Not Started

---

## Objective

Create end-to-end tests that validate the complete system in multi-process scenarios and configure the GitHub Actions CI pipeline for automated testing and validation.

---

## Scope

### In Scope
- E2E tests simulating full audit cycle with real processes
- Edge case tests (ambiguous, low-contrast, incomplete inputs)
- Fuzz testing for robustness validation
- GitHub Actions CI workflow configuration
- Test result reporting (Markdown coverage reports)
- CI quality gates (coverage thresholds, test pass requirements)
- Multi-process agent communication tests

### Out of Scope
- Golden dataset creation (M7-1)
- Coverage/performance testing (M7-2)
- Integration tests with mocks (M7-3)
- Production deployment (M9)

---

## Deliverables

### 1. E2E Test Suite (`tests/e2e/`)

End-to-end tests with real processes:

```
e2e/
├── __init__.py
├── conftest.py               # E2E fixtures and process management
├── test_full_audit_cycle.py  # Complete audit workflow
├── test_multi_agent.py       # Multi-agent communication
├── test_edge_cases.py        # Edge case handling
├── test_fuzz.py              # Fuzz testing
└── fixtures/
    └── .gitkeep              # E2E test fixtures
```

### 2. Full Audit Cycle Tests (`tests/e2e/test_full_audit_cycle.py`)

Tests for complete audit workflow:

- `test_screenshot_to_report()` — Screenshot → Audit → Plan → Report → Markdown
- `test_video_to_report()` — Video → Frames → Audit → Plan → Report
- `test_cli_audit_command()` — `glm audit` CLI end-to-end
- `test_cli_report_command()` — `glm report` CLI end-to-end
- `test_watch_mode_e2e()` — Watch directory → Auto-audit → Reports generated
- `test_proposal_workflow()` — Proposal → Approval → Design system updated

**E2E Flow:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Screenshot │────▶│    Audit    │────▶│    Plan     │
│   (file)    │     │  (process)  │     │  (process)  │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Claude    │◀────│  Proposal   │◀────│   Report    │
│  (process)  │     │  (process)  │     │   (file)    │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 3. Multi-Agent E2E Tests (`tests/e2e/test_multi_agent.py`)

Tests for multi-process agent communication:

- `test_four_agent_handshake()` — GLM, Claude, Minimax, Codex handshake
- `test_audit_notification()` — Audit complete notifies all agents
- `test_dispute_resolution_e2e()` — Dispute → Claude → Resolution
- `test_human_escalation_e2e()` — Escalation → Human mock → Response
- `test_agent_restart_recovery()` — Agent restarts, reconnects

**Process Architecture:**
```
┌─────────────────────────────────────────────────────┐
│                    E2E Test                         │
│                                                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │
│  │   GLM   │  │ Claude  │  │ Minimax │  │ Codex  │ │
│  │ :5001   │  │ :5002   │  │ :5003   │  │ :5004  │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └───┬────┘ │
│       │            │            │            │      │
│       └────────────┴────────────┴────────────┘      │
│                    Unix Sockets                     │
└─────────────────────────────────────────────────────┘
```

### 4. Edge Case Tests (`tests/e2e/test_edge_cases.py`)

Tests for boundary conditions and error handling:

- `test_ambiguous_ui()` — UI with unclear hierarchy
- `test_low_contrast_image()` — Very low contrast screenshot
- `test_incomplete_screenshot()` — Partially loaded/corrupted image
- `test_empty_screen()` — Blank/minimal UI
- `test_extreme_density()` — Very dense UI (many components)
- `test_unusual_aspect_ratio()` — Non-standard aspect ratios
- `test_animated_gif()` — GIF file handling
- `test_corrupted_video()` — Corrupted video file handling
- `test_very_large_image()` — Image at size limits (10000px)
- `test_special_characters()` — Unicode in component text

**Edge Case Categories:**
| Category | Tests | Expected Behavior |
|----------|-------|-------------------|
| Visual | Low contrast, ambiguous | Graceful degradation, partial findings |
| Format | Corrupted, unusual | Clear error message, no crash |
| Size | Large, dense | Performance acceptable, complete analysis |
| Content | Empty, special chars | Handle gracefully, no errors |

### 5. Fuzz Testing (`tests/e2e/test_fuzz.py`)

Fuzz tests for robustness:

- `fuzz_screenshot_ingestion()` — Random bytes as screenshot
- `fuzz_video_ingestion()` — Random bytes as video
- `fuzz_metadata_json()` — Malformed JSON metadata
- `fuzz_audit_config()` — Random config values
- `fuzz_protocol_messages()` — Malformed protocol messages

**Fuzz Strategy:**
- Use `hypothesis` library for property-based testing
- Generate random inputs within valid constraints
- Property: No crash, no data corruption, clear errors

### 6. GitHub Actions CI Workflow (`.github/workflows/`)

CI pipeline configuration:

```
.github/
└── workflows/
    ├── ci.yml              # Main CI workflow
    ├── coverage.yml        # Coverage reporting
    └── release.yml         # Release automation (optional)
```

**CI Workflow Stages:**
1. **Lint & Type Check** — ruff, mypy
2. **Unit Tests** — pytest with coverage
3. **Integration Tests** — pytest integration marker
4. **E2E Tests** — pytest e2e marker (selected tests)
5. **Coverage Gate** — Fail if < 90%
6. **Report Generation** — Coverage report artifact

### 7. CI Configuration Files

**`.github/workflows/ci.yml`:**
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Lint with ruff
        run: ruff check src/ tests/
      - name: Type check with mypy
        run: mypy src/

  test:
    runs-on: macos-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install system dependencies
        run: brew install pango gdk-pixbuf libffi ffmpeg
      - name: Install Python dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run unit tests
        run: pytest tests/unit/ --cov=src --cov-report=xml
      - name: Run integration tests
        run: pytest tests/integration/ -v
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml

  coverage-gate:
    runs-on: macos-latest
    needs: test
    steps:
      - name: Check coverage threshold
        run: |
          COVERAGE=$(python -c "import xml.etree.ElementTree as ET; root = ET.parse('coverage.xml').getroot(); print(root.attrib['line-rate'])")
          if (( $(echo "$COVERAGE < 0.90" | bc -l) )); then
            echo "Coverage $COVERAGE is below 90% threshold"
            exit 1
          fi
```

### 8. Test Result Reporting (`docs/test-results/`)

Generated test reports:

```
docs/
└── test-results/
    ├── coverage.md           # Coverage summary
    ├── e2e-results.md        # E2E test results
    └── performance.md        # Performance benchmarks
```

**Coverage Report Template:**
```markdown
# Test Coverage Report

**Generated:** 2026-03-13
**Total Coverage:** 92.3%

| Module | Coverage | Status |
|--------|----------|--------|
| src/db/ | 94.1% | ✅ |
| src/config/ | 91.2% | ✅ |
| src/ingest/ | 89.5% | ⚠️ |
| src/vision/ | 93.8% | ✅ |
| src/audit/ | 91.7% | ✅ |
| src/plan/ | 92.4% | ✅ |
| src/protocol/ | 90.1% | ✅ |
| src/cli/ | 88.9% | ⚠️ |
| src/api/ | 93.2% | ✅ |
```

### 9. CI Quality Gates (`scripts/ci_gates.py`)

Script for CI quality checks:

```bash
# Run all quality gates
python scripts/ci_gates.py

# Run specific gate
python scripts/ci_gates.py --gate coverage
python scripts/ci_gates.py --gate lint
python scripts/ci_gates.py --gate tests
```

**Quality Gates:**
- Coverage threshold: 90%
- Zero linting errors
- All unit tests pass
- All integration tests pass
- Selected E2E tests pass

---

## Technical Decisions

### E2E Test Strategy: Selected Scenarios
- **Decision:** Run subset of E2E tests in CI, full suite on release
- **Rationale:**
  - Full E2E suite is slow (multi-process setup)
  - CI should be fast for developer feedback
  - Release branch gets full validation

**CI E2E Markers:**
```python
@pytest.mark.e2e
@pytest.mark.ci_quick  # Fast E2E tests for CI
def test_audit_cycle_quick():
    ...
```

### Process Management: subprocess + pytest fixtures
- **Decision:** Use subprocess for agent processes, pytest for lifecycle
- **Rationale:**
  - Real process isolation
  - Proper cleanup via fixtures
  - Timeout handling built-in

### Fuzz Testing: hypothesis library
- **Decision:** Use hypothesis for property-based fuzz testing
- **Rationale:**
  - Python-native
  - Powerful test case generation
  - Shrinking for minimal failures
  - Integrates with pytest

### CI Platform: GitHub Actions
- **Decision:** Use GitHub Actions for CI
- **Rationale:**
  - Native GitHub integration
  - macOS runners available
  - Free for public repos
  - Easy artifact upload

---

## File Structure

```
.github/
└── workflows/
    ├── ci.yml                  # Main CI workflow
    ├── coverage.yml            # Coverage reporting
    └── release.yml             # Release automation
tests/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py             # E2E fixtures
│   ├── test_full_audit_cycle.py
│   ├── test_multi_agent.py
│   ├── test_edge_cases.py
│   ├── test_fuzz.py
│   └── fixtures/
│       └── .gitkeep
scripts/
├── ci_gates.py                 # CI quality gate script
└── generate_test_report.py     # Test report generator
docs/
└── test-results/
    ├── .gitkeep
    ├── coverage.md             # Generated coverage report
    └── e2e-results.md          # Generated E2E report
```

---

## Tasks

### Phase 1: E2E Infrastructure
- [ ] Create `tests/e2e/` directory structure
- [ ] Create `tests/e2e/conftest.py` with process management fixtures
- [ ] Create `tests/e2e/fixtures/` for E2E test fixtures
- [ ] Add `hypothesis` to requirements-test.txt
- [ ] Add E2E markers to pytest.ini

### Phase 2: Full Audit Cycle Tests
- [ ] Create `test_full_audit_cycle.py`
- [ ] Implement `test_screenshot_to_report()`
- [ ] Implement `test_video_to_report()`
- [ ] Implement `test_cli_audit_command()`
- [ ] Implement `test_cli_report_command()`
- [ ] Implement `test_watch_mode_e2e()`

### Phase 3: Multi-Agent E2E Tests
- [ ] Create `test_multi_agent.py`
- [ ] Implement process fixtures for agents
- [ ] Implement `test_four_agent_handshake()`
- [ ] Implement `test_audit_notification()`
- [ ] Implement `test_dispute_resolution_e2e()`

### Phase 4: Edge Case Tests
- [ ] Create `test_edge_cases.py`
- [ ] Create edge case fixtures (low contrast, corrupted, etc.)
- [ ] Implement visual edge case tests
- [ ] Implement format edge case tests
- [ ] Implement size edge case tests
- [ ] Verify graceful degradation

### Phase 5: Fuzz Testing
- [ ] Create `test_fuzz.py`
- [ ] Implement `fuzz_screenshot_ingestion()` with hypothesis
- [ ] Implement `fuzz_video_ingestion()` with hypothesis
- [ ] Implement `fuzz_metadata_json()` with hypothesis
- [ ] Implement `fuzz_protocol_messages()` with hypothesis
- [ ] Run fuzz tests for 1000 iterations each

### Phase 6: CI Configuration
- [ ] Create `.github/workflows/` directory
- [ ] Create `ci.yml` with lint, test, coverage stages
- [ ] Configure macOS runner with system dependencies
- [ ] Add coverage upload to Codecov (optional)
- [ ] Create `coverage.yml` for coverage reporting
- [ ] Test CI workflow on feature branch

### Phase 7: Quality Gates & Reporting
- [ ] Create `scripts/ci_gates.py`
- [ ] Create `scripts/generate_test_report.py`
- [ ] Add coverage threshold check to CI
- [ ] Generate coverage report artifact
- [ ] Generate E2E results report
- [ ] Document CI workflow in README

### Phase 8: Validation
- [ ] Run full E2E suite locally
- [ ] Verify CI passes on all tests
- [ ] Verify coverage threshold enforcement
- [ ] Run fuzz tests for extended period
- [ ] Document any known limitations

---

## Success Criteria

- [ ] E2E tests cover full audit cycle
- [ ] Multi-agent E2E tests pass with real processes
- [ ] Edge case tests handle all scenarios gracefully
- [ ] Fuzz tests run without crashes
- [ ] GitHub Actions CI configured and passing
- [ ] Coverage gate enforces 90% threshold
- [ ] Test reports generated automatically
- [ ] CI runs in < 15 minutes
- [ ] Zero flaky E2E tests

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| E2E tests flaky in CI | Timeouts, retries, isolated fixtures |
| CI too slow | Parallel jobs, caching, selected E2E in CI |
| macOS runner limitations | Document requirements, use containers where possible |
| Fuzz tests find many issues | Prioritize by severity, fix incrementally |
| Coverage threshold too strict | Allow temporary exemptions with tracked issues |

---

## Validation

Run after completion:
```bash
# Run E2E tests locally
python -m pytest tests/e2e/ -v

# Run specific E2E test
python -m pytest tests/e2e/test_full_audit_cycle.py -v

# Run fuzz tests
python -m pytest tests/e2e/test_fuzz.py -v --hypothesis-seed=0

# Run CI quality gates locally
python scripts/ci_gates.py

# Generate test report
python scripts/generate_test_report.py

# Verify CI workflow syntax
gh workflow lint .github/workflows/ci.yml

# Run full test suite
python -m pytest tests/ -v

# Check coverage threshold
python -c "import coverage; cov = coverage.Coverage(); cov.load(); assert cov.report() >= 90"
```

---

## Dependencies

### Python Dependencies
- `hypothesis>=6.0.0` — NEW (add to requirements-test.txt)
- `pytest-timeout>=2.0.0` — NEW (add to requirements-test.txt)
- All existing test dependencies

### System Dependencies
- macOS runner (GitHub Actions)
- ffmpeg (already in requirements)
- pango, gdk-pixbuf (for WeasyPrint)

### External Services
- GitHub Actions (free for public repos)
- Codecov (optional, free for public repos)

---

*Created: 2026-03-13*