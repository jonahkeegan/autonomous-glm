# Epic M7-2: Coverage & Performance Testing

> **Milestone:** 7 - Testing Infrastructure  
> **Priority:** High  
> **Dependencies:** Epic M7-1 (Golden Dataset Creation)  
> **Status:** ✅ COMPLETED

---

## Objective

Achieve >90% unit test coverage across all modules and validate performance KPIs deferred from previous milestones.

---

## Scope

### In Scope
- Coverage gap analysis and identification
- Targeted unit tests to reach >90% coverage
- Performance benchmark tests for CLI commands
- Performance benchmark tests for watch mode
- Performance benchmark tests for report generation
- Performance benchmark tests for audit execution
- Coverage report generation (Markdown + terminal)
- Performance regression test suite

### Out of Scope
- Golden dataset creation (M7-1)
- Integration tests with mocks (M7-3)
- E2E tests and CI pipeline (M7-4)

---

## Deliverables

### 1. Coverage Gap Analysis (`tests/coverage/`)

Analysis tools and reports for coverage gaps:

- `coverage_analyzer.py` — Analyze coverage by module
- `gap_reporter.py` — Generate gap reports with recommendations
- `coverage_report.md` — Current coverage status

**Coverage Targets by Module:**
| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| `src/db/` | ~85% | >90% | Medium |
| `src/config/` | ~88% | >90% | Medium |
| `src/ingest/` | ~82% | >90% | High |
| `src/vision/` | ~78% | >90% | Critical |
| `src/audit/` | ~80% | >90% | Critical |
| `src/plan/` | ~85% | >90% | High |
| `src/protocol/` | ~82% | >90% | High |
| `src/cli/` | ~75% | >90% | High |
| `src/api/` | ~80% | >90% | Medium |

### 2. Coverage Gap Tests (`tests/unit/coverage/`)

Targeted tests to fill coverage gaps:

```
coverage/
├── __init__.py
├── test_db_edge_cases.py       # Database edge cases
├── test_config_edge_cases.py   # Config edge cases
├── test_ingest_edge_cases.py   # Ingestion edge cases
├── test_vision_edge_cases.py   # CV edge cases
├── test_audit_edge_cases.py    # Audit edge cases
├── test_plan_edge_cases.py     # Plan edge cases
├── test_protocol_edge_cases.py # Protocol edge cases
├── test_cli_edge_cases.py      # CLI edge cases
└── test_api_edge_cases.py      # API edge cases
```

**Test Categories:**
- Error path coverage (exceptions, validation failures)
- Edge case coverage (boundary values, empty inputs)
- Branch coverage (all if/else paths)
- Async path coverage (async functions)

### 3. Performance Benchmarks (`tests/performance/`)

Performance test suite with benchmark targets:

```
performance/
├── __init__.py
├── conftest.py                  # Performance test fixtures
├── benchmark_cli.py             # CLI command benchmarks
├── benchmark_watch.py           # Watch mode benchmarks
├── benchmark_report.py          # Report generation benchmarks
├── benchmark_audit.py           # Audit execution benchmarks
├── benchmark_ingest.py          # Ingestion benchmarks
└── results/
    └── .gitkeep                 # Benchmark results storage
```

**Performance KPIs (from PRD/Milestones):**
| Operation | Target | Source |
|-----------|--------|--------|
| Screenshot ingestion | <100ms | M1 KPIs |
| Video frame extraction | <2s/segment | M1 KPIs |
| CV detection | <1s/screenshot | M2 KPIs |
| Video segment analysis | <5s/segment | M2 KPIs |
| Audit execution | <1s/screenshot | M3 KPIs |
| Plan generation | <2s/audit | M4 KPIs |
| Message delivery | <100ms | M5 KPIs |
| CLI response time | <200ms | M6 KPIs |
| Watch mode detection | <500ms | M6 KPIs |
| Report generation | <1s | M6 KPIs |
| Throughput | >10 audits/min | PRD |

### 4. CLI Benchmarks (`tests/performance/benchmark_cli.py`)

Benchmarks for all CLI commands:

- `test_audit_command_latency()` — `glm audit <id>` response time
- `test_report_command_latency()` — `glm report <id>` response time
- `test_propose_command_latency()` — `glm propose` response time
- `test_dashboard_command_latency()` — `glm dashboard` response time
- `test_json_output_latency()` — JSON output overhead
- `test_startup_time()` — CLI initialization time

### 5. Watch Mode Benchmarks (`tests/performance/benchmark_watch.py`)

Benchmarks for watch mode performance:

- `test_file_detection_latency()` — Time from file creation to event
- `test_debounce_window()` — Debounce timing accuracy
- `test_queue_processing_rate()` — Items processed per second
- `test_batch_processing()` — Batch of 10, 50, 100 files
- `test_memory_usage()` — Memory stability during long runs

### 6. Audit & Report Benchmarks (`tests/performance/benchmark_audit.py`)

Benchmarks for core audit pipeline:

- `test_single_screenshot_audit()` — Full audit of one screenshot
- `test_batch_audit()` — Audit of 10, 50, 100 screenshots
- `test_all_dimensions()` — Audit with all 13 dimensions
- `test_plan_generation()` — Plan synthesis time
- `test_report_markdown()` — Markdown report generation
- `test_report_json()` — JSON report generation
- `test_report_pdf()` — PDF report generation

### 7. Coverage Report Generator (`scripts/coverage_report.py`)

Script to generate coverage reports:

```bash
# Generate terminal report
python scripts/coverage_report.py

# Generate Markdown report
python scripts/coverage_report.py --format markdown --output docs/coverage.md

# Generate HTML report
python scripts/coverage_report.py --format html --output htmlcov/
```

### 8. Performance Report Generator (`scripts/performance_report.py`)

Script to run benchmarks and generate reports:

```bash
# Run all benchmarks
python scripts/performance_report.py

# Run specific benchmark category
python scripts/performance_report.py --category cli

# Generate comparison report
python scripts/performance_report.py --compare baseline.json
```

---

## Technical Decisions

### Coverage Tool: pytest-cov
- **Decision:** Use pytest-cov with coverage.py
- **Rationale:**
  - Already configured in pytest.ini
  - Standard Python coverage tool
  - Supports multiple output formats
  - Branch coverage support

### Performance Benchmarking: pytest-benchmark
- **Decision:** Use pytest-benchmark for performance tests
- **Rationale:**
  - Integration with pytest
  - Statistical analysis (min, max, mean, median, stddev)
  - Comparison against baselines
  - JSON output for tracking

**Alternative Considered:** timeit (too manual), custom timing (less robust)

### Coverage Target: >90% Line Coverage
- **Decision:** Target 90% line coverage, not branch coverage
- **Rationale:**
  - Line coverage is more actionable
  - Branch coverage can be noisy
  - 90% is pragmatic (not 100% dogmatic)
  - Critical paths should have higher coverage

### Performance Test Isolation
- **Decision:** Performance tests in separate directory, not run by default
- **Rationale:**
  - Performance tests are slower
  - Results can vary by environment
  - Run explicitly for benchmarking
  - Don't slow down CI unit tests

---

## File Structure

```
tests/
├── coverage/
│   ├── __init__.py
│   ├── coverage_analyzer.py      # Coverage gap analysis
│   ├── gap_reporter.py           # Gap report generation
│   ├── test_db_edge_cases.py
│   ├── test_config_edge_cases.py
│   ├── test_ingest_edge_cases.py
│   ├── test_vision_edge_cases.py
│   ├── test_audit_edge_cases.py
│   ├── test_plan_edge_cases.py
│   ├── test_protocol_edge_cases.py
│   ├── test_cli_edge_cases.py
│   └── test_api_edge_cases.py
├── performance/
│   ├── __init__.py
│   ├── conftest.py               # Performance fixtures
│   ├── benchmark_cli.py          # CLI benchmarks
│   ├── benchmark_watch.py        # Watch mode benchmarks
│   ├── benchmark_report.py       # Report benchmarks
│   ├── benchmark_audit.py        # Audit benchmarks
│   ├── benchmark_ingest.py       # Ingestion benchmarks
│   └── results/
│       └── .gitkeep
scripts/
├── coverage_report.py            # Coverage report generator
└── performance_report.py         # Performance report generator
docs/
└── coverage.md                   # Generated coverage report
```

---

## Tasks

### Phase 1: Coverage Analysis
- [ ] Create `tests/coverage/` directory structure
- [ ] Create `coverage_analyzer.py` with module-level analysis
- [ ] Create `gap_reporter.py` with gap identification
- [ ] Run coverage analysis on all modules
- [ ] Generate initial coverage gap report
- [ ] Identify top 10 coverage gaps by impact

### Phase 2: Coverage Gap Tests - Core
- [ ] Create `test_db_edge_cases.py` for database edge cases
- [ ] Create `test_config_edge_cases.py` for config edge cases
- [ ] Create `test_ingest_edge_cases.py` for ingestion edge cases
- [ ] Create `test_vision_edge_cases.py` for CV edge cases
- [ ] Create `test_audit_edge_cases.py` for audit edge cases
- [ ] Run coverage and verify improvement

### Phase 3: Coverage Gap Tests - CLI & Protocol
- [ ] Create `test_plan_edge_cases.py` for plan edge cases
- [ ] Create `test_protocol_edge_cases.py` for protocol edge cases
- [ ] Create `test_cli_edge_cases.py` for CLI edge cases
- [ ] Create `test_api_edge_cases.py` for API edge cases
- [ ] Run coverage and verify >90% achieved

### Phase 4: Performance Infrastructure
- [ ] Create `tests/performance/` directory structure
- [ ] Add `pytest-benchmark` to requirements-test.txt
- [ ] Create `conftest.py` with performance fixtures
- [ ] Create `results/` directory for benchmark storage
- [ ] Create `scripts/performance_report.py`

### Phase 5: CLI & Watch Benchmarks
- [ ] Create `benchmark_cli.py` with CLI command benchmarks
- [ ] Create `benchmark_watch.py` with watch mode benchmarks
- [ ] Verify CLI response time < 200ms
- [ ] Verify watch mode detection < 500ms

### Phase 6: Audit & Report Benchmarks
- [ ] Create `benchmark_audit.py` with audit benchmarks
- [ ] Create `benchmark_report.py` with report benchmarks
- [ ] Create `benchmark_ingest.py` with ingestion benchmarks
- [ ] Verify all KPIs meet targets

### Phase 7: Report Generation & Validation
- [ ] Create `scripts/coverage_report.py`
- [ ] Generate Markdown coverage report
- [ ] Generate performance benchmark report
- [ ] Validate >90% coverage achieved
- [ ] Validate all performance KPIs met

---

## Success Criteria

- [ ] Overall test coverage > 90%
- [ ] All modules have > 90% coverage (no module below 85%)
- [ ] Coverage report generated in Markdown format
- [ ] All performance KPIs have benchmark tests
- [ ] Screenshot ingestion < 100ms
- [ ] CV detection < 1s/screenshot
- [ ] CLI response time < 200ms
- [ ] Watch mode detection < 500ms
- [ ] Report generation < 1s
- [ ] Throughput > 10 audits/min
- [ ] Performance benchmark report generated

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Coverage gaps in complex codepaths | Focus on critical paths first, accept <90% in some modules |
| Performance variance across environments | Use relative comparisons, statistical analysis |
| Benchmark flakiness | Multiple runs, warmup iterations, outlier filtering |
| New code reducing coverage | Coverage gates in CI (future M7-4) |

---

## Validation

Run after completion:
```bash
# Run coverage analysis
python -m pytest tests/ --cov=src --cov-report=term-missing

# Generate coverage report
python scripts/coverage_report.py --format markdown --output docs/coverage.md

# Run performance benchmarks
python -m pytest tests/performance/ -v --benchmark-only

# Generate performance report
python scripts/performance_report.py

# Verify coverage threshold
python -c "import coverage; cov = coverage.Coverage(); cov.load(); print(f'Coverage: {cov.report()}%')"

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- `pytest-cov>=4.0.0` — Already installed
- `pytest-benchmark>=4.0.0` — NEW (add to requirements-test.txt)
- `coverage>=7.0.0` — Already installed

### Internal Dependencies
- `tests/golden-dataset/` — Golden dataset for consistent benchmarking
- All `src/` modules — For coverage analysis

---

*Created: 2026-03-13*