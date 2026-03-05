# Epic M4-4: Reports & Persistence

> **Milestone:** 4 - Plan Generation  
> **Priority:** High  
> **Dependencies:** Epic M4-3 (Design System Proposals)  
> **Status:** ✅ Completed

---

## Objective

Build the report generation and persistence layer that outputs Markdown reports for human review, JSON output for agent consumption, and persists PlanPhase entities to the database.

---

## Scope

### In Scope
- Markdown report generation (`/output/reports/`)
- JSON output for agent consumption
- PlanPhase entity persistence to database
- Report templates (audit summary, implementation plan, design proposals)
- Plan status tracking (PENDING, IN_PROGRESS, COMPLETED)
- Report metadata (timestamps, versioning)

### Out of Scope
- CLI interface (M6)
- Agent communication protocol (M5)
- PDF export (M6)
- Dashboard/HTML output (M6)

---

## Deliverables

### 1. Report Models (`src/plan/report_models.py`)

Pydantic models for reports:
- `ReportType` — Enum (AUDIT_SUMMARY, IMPLEMENTATION_PLAN, DESIGN_PROPOSAL, FULL_REPORT)
- `ReportMetadata` — {id, report_type, audit_session_id, created_at, version}
- `AuditSummaryReport` — {metadata, summary_stats, findings_by_severity, findings_by_dimension}
- `ImplementationPlanReport` — {metadata, phases, instructions, total_actions}
- `DesignProposalReport` — {metadata, proposals, before_after_descriptions}
- `FullReport` — {metadata, audit_summary, implementation_plan, design_proposals}

### 2. Markdown Generator (`src/plan/markdown.py`)

Markdown report generation:
- `MarkdownGenerator` — Main generator class
- `generate_audit_summary(report: AuditSummaryReport) -> str`
- `generate_implementation_plan(report: ImplementationPlanReport) -> str`
- `generate_design_proposals(report: DesignProposalReport) -> str`
- `generate_full_report(report: FullReport) -> str`
- `format_finding_table(findings: list) -> str` — Markdown table
- `format_instruction_list(instructions: list) -> str` — Numbered list

### 3. JSON Generator (`src/plan/json_output.py`)

JSON output for agents:
- `JsonGenerator` — Main generator class
- `generate_agent_payload(plan: Plan) -> dict`
- `generate_findings_json(findings: list[AuditFinding]) -> list[dict]`
- `generate_instructions_json(instructions: list) -> list[dict]`
- `generate_proposals_json(proposals: list) -> list[dict]`
- Validates against `/interfaces/*.schema.json` schemas

### 4. Plan Persistence (`src/plan/persistence.py`)

Database persistence:
- `PlanPersistence` — Main persistence class
- `save_plan(plan: Plan) -> UUID`
- `save_plan_phase(phase: PlanPhase) -> UUID`
- `save_report(report: FullReport) -> UUID`
- `get_plan(plan_id: UUID) -> Plan`
- `get_plans_by_session(session_id: UUID) -> list[Plan]`
- `update_plan_status(plan_id: UUID, status: PlanStatus) -> bool`
- `get_report(report_id: UUID) -> FullReport`

### 5. Report Writer (`src/plan/report_writer.py`)

File output:
- `ReportWriter` — Writes reports to filesystem
- `write_markdown_report(report: FullReport, path: str) -> str`
- `write_json_report(report: FullReport, path: str) -> str`
- `generate_report_filename(report_type: ReportType) -> str`
- Directory: `/output/reports/{YYYY-MM-DD}/{report_type}_{id}.md`

---

## Technical Decisions

### Report Directory Structure
- **Decision:** Date-based organization with unique IDs
- **Rationale:**
  - Easy to find reports by date
  - Prevents filename collisions
  - Supports cleanup by age

**Structure:**
```
/output/reports/
├── 2026-03-04/
│   ├── audit_summary_abc123.md
│   ├── implementation_plan_abc123.md
│   ├── design_proposals_abc123.md
│   └── full_report_abc123.json
└── 2026-03-05/
    └── ...
```

### Markdown Template Structure
- **Decision:** Consistent sections across all report types
- **Rationale:**
  - Predictable structure for readers
  - Easy to parse programmatically
  - Supports partial reads

**Standard Sections:**
1. Header (title, metadata, status)
2. Summary (key metrics, critical findings)
3. Details (findings/instructions/proposals)
4. Next Steps (recommended actions)

### JSON Schema Compliance
- **Decision:** Validate JSON output against interface schemas
- **Rationale:**
  - Ensures agent compatibility
  - Catches formatting errors early
  - Documents the contract

**Schemas Used:**
- `interfaces/audit-complete.schema.json` — Audit completion messages
- `interfaces/design-proposal.schema.json` — Design system proposals

### Database Persistence Strategy
- **Decision:** Save after each phase completes
- **Rationale:**
  - Partial results preserved on failure
  - Progress trackable
  - Supports resume after interruption

---

## File Structure

```
src/
└── plan/
    ├── __init__.py           # Updated exports
    ├── report_models.py      # Report Pydantic models
    ├── markdown.py           # Markdown generation
    ├── json_output.py        # JSON output for agents
    ├── persistence.py        # Database persistence
    └── report_writer.py      # File output
output/
└── reports/
    └── .gitkeep
interfaces/
├── audit-complete.schema.json    # Existing
└── design-proposal.schema.json   # Existing
tests/
└── unit/
    ├── test_report_models.py
    ├── test_markdown.py
    ├── test_json_output.py
    ├── test_plan_persistence.py
    └── test_report_writer.py
```

---

## Tasks

### Phase 1: Report Models
- [ ] Create `src/plan/report_models.py`
- [ ] Define `ReportType` enum
- [ ] Define `ReportMetadata` model
- [ ] Define `AuditSummaryReport` model
- [ ] Define `ImplementationPlanReport` model
- [ ] Define `DesignProposalReport` model
- [ ] Define `FullReport` aggregate model
- [ ] Write unit tests for models

### Phase 2: Markdown Generator
- [ ] Create `src/plan/markdown.py`
- [ ] Implement `MarkdownGenerator` class
- [ ] Implement `format_finding_table()` helper
- [ ] Implement `format_instruction_list()` helper
- [ ] Implement `generate_audit_summary()` method
- [ ] Implement `generate_implementation_plan()` method
- [ ] Implement `generate_design_proposals()` method
- [ ] Implement `generate_full_report()` method
- [ ] Write unit tests for markdown generation

### Phase 3: JSON Generator
- [ ] Create `src/plan/json_output.py`
- [ ] Implement `JsonGenerator` class
- [ ] Implement `generate_findings_json()` method
- [ ] Implement `generate_instructions_json()` method
- [ ] Implement `generate_proposals_json()` method
- [ ] Implement `generate_agent_payload()` method
- [ ] Add schema validation against interface files
- [ ] Write unit tests for JSON output

### Phase 4: Plan Persistence
- [ ] Create `src/plan/persistence.py`
- [ ] Implement `PlanPersistence` class
- [ ] Implement `save_plan()` method
- [ ] Implement `save_plan_phase()` method
- [ ] Implement `save_report()` method
- [ ] Implement `get_plan()` method
- [ ] Implement `get_plans_by_session()` method
- [ ] Implement `update_plan_status()` method
- [ ] Update `src/db/schema.sql` if needed (plan_phases table)
- [ ] Write unit tests for persistence

### Phase 5: Report Writer
- [ ] Create `src/plan/report_writer.py`
- [ ] Implement `ReportWriter` class
- [ ] Implement `generate_report_filename()` method
- [ ] Implement `write_markdown_report()` method
- [ ] Implement `write_json_report()` method
- [ ] Create date-based directory structure
- [ ] Write unit tests for report writer

### Phase 6: Integration
- [ ] Update `src/plan/__init__.py` with all exports
- [ ] Create end-to-end test: audit → plan → report
- [ ] Validate JSON against schema files
- [ ] Test with M3-1 validation dataset
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] Report models validate correctly with all fields
- [ ] Markdown reports render correctly in viewers
- [ ] JSON output validates against interface schemas
- [ ] Plans persist correctly to database
- [ ] Reports save to correct directory structure
- [ ] Plan status updates correctly
- [ ] Unit test coverage > 90% for report module
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Report files grow large | Add pagination; summarize by default |
| JSON schema drift | Validate at runtime; version schemas |
| Database write failures | Log errors; retry with backoff |
| Filename collisions | Use UUID in filename; timestamp prefix |

---

## Validation

Run after completion:
```bash
# Run report module tests
python -m pytest tests/unit/test_report*.py tests/unit/test_markdown*.py tests/unit/test_json*.py tests/unit/test_plan_persistence*.py -v

# Test markdown generation
python -c "
from src.plan.markdown import MarkdownGenerator
from src.plan.report_models import AuditSummaryReport, ReportMetadata

generator = MarkdownGenerator()
metadata = ReportMetadata(report_type='audit_summary')
# Would generate markdown
print('Markdown generator ready')
"

# Test JSON output
python -c "
from src.plan.json_output import JsonGenerator

generator = JsonGenerator()
# Would generate JSON payload
print('JSON generator ready')
"

# Test persistence
python -c "
from src.plan.persistence import PlanPersistence

persistence = PlanPersistence()
# Would save/retrieve plans
print('Persistence ready')
"

# Validate output directory
ls -la output/reports/

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- All M4-3 dependencies
- `jsonschema` (already in requirements)

### System Dependencies
- SQLite database with audit tables
- `/output/reports/` directory (writable)
- Interface schema files

---

*Created: 2026-03-04*