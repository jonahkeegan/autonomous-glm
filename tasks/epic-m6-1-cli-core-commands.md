# Epic M6-1: CLI Core Commands

> **Milestone:** 6 - Reporting & CLI  
> **Priority:** Critical  
> **Dependencies:** Epic M5-3 (Arbitration & Reliability)  
> **Status:** 🔲 Not Started

---

## Objective

Build the command-line interface entry point and core commands that enable users and agents to trigger audits, fetch reports, and view design system proposals through a structured CLI.

---

## Scope

### In Scope
- CLI entry point (`glm` command) using Click framework
- Core commands: `--audit`, `--report`, `--propose`
- Terminal table output using Rich library
- JSON output format for agent consumption
- Configuration integration (respects config files)
- Error handling with user-friendly messages
- Progress indicators for long-running operations

### Out of Scope
- Watch mode for directory monitoring (M6-2)
- Dashboard metrics display (M6-3)
- PDF export functionality (M6-3)
- GUI/web interface

---

## Deliverables

### 1. CLI Entry Point (`src/cli/__init__.py`)

Main CLI module with Click application:
- `glm` — Root command group
- `glm --version` — Display version information
- `glm --help` — Show help text
- `glm --config <path>` — Specify custom config file

### 2. Audit Command (`src/cli/commands/audit.py`)

Trigger audit on artifact:
- `glm audit <artifact_id>` — Run full audit on artifact
- `glm audit <artifact_id> --json` — Output as JSON
- `glm audit <artifact_id> --dimensions <dim1,dim2>` — Run specific dimensions
- `glm audit <artifact_id> --verbose` — Detailed progress output

### 3. Report Command (`src/cli/commands/report.py`)

Fetch and display reports:
- `glm report <audit_id>` — Display report summary
- `glm report <audit_id> --full` — Display full report
- `glm report <audit_id> --json` — Output as JSON
- `glm report <audit_id> --output <path>` — Save to file
- `glm report --latest` — Fetch most recent report

### 4. Propose Command (`src/cli/commands/propose.py`)

View design system proposals:
- `glm propose` — List all pending proposals
- `glm propose <proposal_id>` — View specific proposal
- `glm propose <proposal_id> --diff` — Show before/after diff
- `glm propose <proposal_id> --apply` — Apply proposal (requires confirmation)

### 5. Output Formatters (`src/cli/formatters.py`)

Terminal output formatting:
- `format_audit_summary(result: AuditResult) -> str` — Markdown summary
- `format_report_table(report: Plan) -> Table` — Rich table
- `format_findings_list(findings: list) -> Table` — Rich table
- `format_proposal_diff(proposal: Proposal) -> str` — Colored diff
- `format_json(data: Any) -> str` — Pretty JSON output

### 6. Progress Indicators (`src/cli/progress.py`)

Progress display for long operations:
- `AuditProgress` — Progress bar for audit phases
- `Spinner` — Spinner for indeterminate operations
- `StatusDisplay` — Real-time status updates

---

## Technical Decisions

### CLI Framework: Click
- **Decision:** Use Click over argparse/Typer
- **Rationale:**
  - Mature, well-documented library
  - Decorator-based syntax for clean command definitions
  - Built-in support for subcommands, options, context
  - Rich integration via `click-rich` or custom formatters

**Command Structure:**
```
glm                          # Root group
├── audit <artifact_id>      # Run audit
├── report <audit_id>        # View report
├── propose [proposal_id]    # View proposals
└── --version / --help       # Built-in
```

### Terminal Output: Rich
- **Decision:** Use Rich for all terminal formatting
- **Rationale:**
  - Beautiful tables, progress bars, syntax highlighting
  - Cross-platform color support
  - Markdown rendering capability
  - Built-in pager for long output

**Table Example:**
```
┌─────────────────┬──────────┬─────────────────────────────────┐
│ Dimension       │ Severity │ Issue                           │
├─────────────────┼──────────┼─────────────────────────────────┤
│ Typography      │ High     │ Font size too small (11px)      │
│ Color           │ Medium   │ Contrast ratio 3.2:1 (need 4.5) │
│ Spacing         │ Low      │ Inconsistent margin (8px vs 12) │
└─────────────────┴──────────┴─────────────────────────────────┘
```

### JSON Output Format
- **Decision:** Structured JSON matching existing schema
- **Rationale:**
  - Agent-consumable format
  - Validates against existing schemas
  - Machine-parseable for automation

**JSON Output Structure:**
```json
{
  "status": "success",
  "audit_id": "uuid",
  "artifact_id": "uuid",
  "findings_count": 12,
  "critical_count": 2,
  "phases": [
    {"name": "Critical", "actions": 5},
    {"name": "Refinement", "actions": 4},
    {"name": "Polish", "actions": 3}
  ],
  "report_path": "/output/reports/2026-03-05/audit-uuid.md"
}
```

### Exit Codes
- **Decision:** Semantic exit codes for scripting
- **Rationale:**
  - Enables shell script integration
  - CI/CD pipeline support
  - Agent automation

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Artifact not found |
| 4 | Audit failed |
| 5 | Configuration error |

---

## File Structure

```
src/
└── cli/
    ├── __init__.py           # Entry point, main group
    ├── main.py               # Click root command
    ├── commands/
    │   ├── __init__.py       # Command exports
    │   ├── audit.py          # glm audit command
    │   ├── report.py         # glm report command
    │   └── propose.py        # glm propose command
    ├── formatters.py         # Output formatting (tables, JSON)
    ├── progress.py           # Progress indicators
    └── errors.py             # CLI-specific exceptions
config/
└── default.yaml              # Updated with cli config
tests/
└── unit/
    ├── test_cli_main.py
    ├── test_cli_audit.py
    ├── test_cli_report.py
    ├── test_cli_propose.py
    └── test_cli_formatters.py
```

---

## Tasks

### Phase 1: CLI Foundation
- [ ] Create `src/cli/` directory structure
- [ ] Create `src/cli/__init__.py` with module exports
- [ ] Create `src/cli/main.py` with Click root group
- [ ] Create `src/cli/errors.py` with CLI exceptions
- [ ] Add `click>=8.0.0` to requirements.txt
- [ ] Add `rich>=13.0.0` to requirements.txt
- [ ] Add `cli:` configuration section to `config/default.yaml`
- [ ] Add `CliConfig` model to `src/config/schema.py`
- [ ] Create entry point in `setup.py` or `pyproject.toml`
- [ ] Write unit tests for CLI foundation

### Phase 2: Audit Command
- [ ] Create `src/cli/commands/__init__.py`
- [ ] Create `src/cli/commands/audit.py`
- [ ] Implement `audit` command with artifact_id argument
- [ ] Add `--json` flag for JSON output
- [ ] Add `--dimensions` option for filtering
- [ ] Add `--verbose` flag for detailed output
- [ ] Integrate with `AuditOrchestrator` from M3
- [ ] Add progress indicator for audit phases
- [ ] Handle errors with user-friendly messages
- [ ] Write unit tests for audit command

### Phase 3: Report Command
- [ ] Create `src/cli/commands/report.py`
- [ ] Implement `report` command with audit_id argument
- [ ] Add `--full` flag for complete report display
- [ ] Add `--json` flag for JSON output
- [ ] Add `--output` option for file save
- [ ] Implement `--latest` for most recent report
- [ ] Integrate with `ReportWriter` from M4
- [ ] Format output with Rich tables
- [ ] Handle missing report errors gracefully
- [ ] Write unit tests for report command

### Phase 4: Propose Command
- [ ] Create `src/cli/commands/propose.py`
- [ ] Implement `propose` command (list all proposals)
- [ ] Implement `propose <id>` for specific proposal
- [ ] Add `--diff` flag for before/after display
- [ ] Add `--apply` flag with confirmation prompt
- [ ] Integrate with `ProposalGenerator` from M4
- [ ] Format proposals with syntax highlighting
- [ ] Handle proposal not found errors
- [ ] Write unit tests for propose command

### Phase 5: Formatters & Progress
- [ ] Create `src/cli/formatters.py`
- [ ] Implement `format_audit_summary()`
- [ ] Implement `format_report_table()` with Rich
- [ ] Implement `format_findings_list()` with Rich
- [ ] Implement `format_proposal_diff()` with colors
- [ ] Implement `format_json()` with pretty printing
- [ ] Create `src/cli/progress.py`
- [ ] Implement `AuditProgress` progress bar
- [ ] Implement `Spinner` for indeterminate operations
- [ ] Write unit tests for formatters and progress

### Phase 6: Integration & Testing
- [ ] Create integration tests for full command flow
- [ ] Test CLI with actual database
- [ ] Test JSON output validates against schemas
- [ ] Test exit codes for error conditions
- [ ] Add CLI usage documentation
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] `glm --version` displays correct version
- [ ] `glm audit <id>` triggers audit and displays summary
- [ ] `glm audit <id> --json` outputs valid JSON
- [ ] `glm report <id>` displays report in table format
- [ ] `glm report --latest` fetches most recent report
- [ ] `glm propose` lists pending proposals
- [ ] Terminal tables render correctly with Rich
- [ ] Progress indicators show during long operations
- [ ] Exit codes are semantic and consistent
- [ ] Error messages are user-friendly
- [ ] Unit test coverage > 90% for `src/cli/`
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Click/Click version conflicts | Pin versions in requirements.txt |
| Rich output on non-TTY | Detect TTY and fall back to plain text |
| Large reports overflow terminal | Use Rich pager for long output |
| Progress bars on Windows | Rich handles cross-platform |
| Missing artifact/database errors | Clear error messages with suggestions |

---

## Validation

Run after completion:
```bash
# Test CLI installation
glm --version

# Test audit command
glm audit test-artifact-id

# Test JSON output
glm audit test-artifact-id --json | jq .

# Test report command
glm report latest
glm report latest --json | jq .

# Test propose command
glm propose

# Run CLI tests
python -m pytest tests/unit/test_cli*.py -v

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- `click>=8.0.0` — CLI framework
- `rich>=13.0.0` — Terminal formatting

### Internal Dependencies
- `src.audit.orchestrator` — Audit execution
- `src.plan.report_writer` — Report generation
- `src.plan.proposals` — Proposal management
- `src.db.crud` — Database operations

---

*Created: 2026-03-05*