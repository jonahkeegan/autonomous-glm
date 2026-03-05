# Epic M6-3: Dashboard & PDF Export

> **Milestone:** 6 - Reporting & CLI  
> **Priority:** Medium  
> **Dependencies:** Epic M6-1 (CLI Core Commands)  
> **Status:** 🔲 Not Started

---

## Objective

Build metrics dashboard for aggregate audit statistics and PDF export capability for human-friendly report distribution, completing the CLI deliverables for Milestone 6.

---

## Scope

### In Scope
- Metrics aggregation from audit history
- Dashboard display (terminal and HTML formats)
- PDF export from Markdown reports
- Template-based HTML generation
- Summary statistics (audits, findings, trends)
- CLI commands: `--dashboard`, `--report --pdf`

### Out of Scope
- CLI core commands (M6-1)
- Watch mode functionality (M6-2)
- Real-time dashboard updates
- Web server for dashboard hosting
- Custom PDF styling/theming

---

## Deliverables

### 1. Metrics Aggregator (`src/cli/dashboard/metrics.py`)

Aggregate audit statistics:
- `MetricsAggregator` — Collects and computes metrics
- `get_audit_count(period: str) -> int` — Total audits in period
- `get_findings_summary(period: str) -> FindingsSummary` — Findings breakdown
- `get_severity_distribution(period: str) -> dict` — Severity counts
- `get_dimension_breakdown(period: str) -> dict` — Findings by dimension
- `get_trend_data(days: int) -> TrendData` — Historical trends
- `get_artifact_stats(period: str) -> ArtifactStats` — Processed artifacts

### 2. Dashboard Renderer (`src/cli/dashboard/renderer.py`)

Dashboard display rendering:
- `DashboardRenderer` — Renders dashboard output
- `render_terminal(metrics: DashboardMetrics) -> str` — Rich terminal output
- `render_html(metrics: DashboardMetrics) -> str` — HTML output
- `render_json(metrics: DashboardMetrics) -> str` — JSON output

### 3. PDF Generator (`src/cli/export/pdf.py`)

PDF generation from reports:
- `PDFGenerator` — Generates PDF files
- `generate_from_markdown(md_path: Path) -> Path` — MD to PDF
- `generate_from_report(report: Plan) -> Path` — Plan to PDF
- `set_template(template_name: str)` — Choose PDF template

### 4. HTML Templates (`src/cli/export/templates/`)

Jinja2 templates for PDF generation:
- `report.html` — Full report template
- `summary.html` — Summary report template
- `proposal.html` — Design proposal template
- `dashboard.html` — Dashboard template

### 5. Dashboard Command (`src/cli/commands/dashboard.py`)

CLI command for dashboard:
- `glm dashboard` — Display dashboard in terminal
- `glm dashboard --html` — Generate HTML dashboard
- `glm dashboard --output <path>` — Save to file
- `glm dashboard --period <period>` — Time period filter

### 6. Export Command (`src/cli/commands/export.py`)

CLI command for exports:
- `glm report <id> --pdf` — Export report as PDF
- `glm report <id> --pdf --output <path>` — Specify output path
- `glm propose <id> --pdf` — Export proposal as PDF

---

## Technical Decisions

### PDF Library: WeasyPrint
- **Decision:** Use WeasyPrint for HTML-to-PDF conversion
- **Rationale:**
  - Pure Python (no wkhtmltopdf binary dependency)
  - CSS print media support
  - Good typography and layout control
  - Active maintenance

**System Dependencies (macOS):**
```bash
brew install pango gdk-pixbuf libffi
```

**PDF Generation Flow:**
```
Report (Plan) → Jinja2 Template → HTML + CSS → WeasyPrint → PDF File
```

### Dashboard Display: Rich + HTML
- **Decision:** Dual output format (terminal + HTML)
- **Rationale:**
  - Terminal: Quick local viewing with Rich tables
  - HTML: Shareable, printable, web-viewable
  - Same underlying data, different renderers

**Terminal Dashboard Layout:**
```
╭─────────────────────────────────────────────────────────────────╮
│                    AUTONOMOUS-GLM DASHBOARD                      │
│                       Last 7 Days                                │
├─────────────────────────────────────────────────────────────────┤
│  AUDITS                                                          │
│  ├─ Total: 47                                                    │
│  ├─ Successful: 45 (96%)                                         │
│  └─ Failed: 2 (4%)                                               │
├─────────────────────────────────────────────────────────────────┤
│  FINDINGS BY SEVERITY                                            │
│  ├─ 🔴 Critical: 12                                              │
│  ├─ 🟠 High: 34                                                  │
│  ├─ 🟡 Medium: 89                                                │
│  └─ 🟢 Low: 156                                                  │
├─────────────────────────────────────────────────────────────────┤
│  TOP DIMENSIONS                                                  │
│  ├─ Typography: 67 issues                                        │
│  ├─ Spacing: 54 issues                                           │
│  └─ Color: 43 issues                                             │
╰─────────────────────────────────────────────────────────────────╯
```

### Template Engine: Jinja2
- **Decision:** Use Jinja2 for HTML templates
- **Rationale:**
  - Familiar syntax, widely used
  - Template inheritance for consistent styling
  - Auto-escaping for security
  - Already in dependencies via other tools

**Template Structure:**
```
templates/
├── base.html           # Base template with styles
├── report.html         # Extends base
├── summary.html        # Extends base
├── proposal.html       # Extends base
└── dashboard.html      # Standalone
```

### Metrics Storage
- **Decision:** Query database directly for metrics
- **Rationale:**
  - No additional storage needed
  - Real-time data from audit tables
  - SQLite handles aggregation efficiently

**Key Queries:**
```sql
-- Audits per day
SELECT DATE(created_at) as day, COUNT(*) 
FROM audit_sessions 
WHERE created_at > datetime('now', '-7 days')
GROUP BY day;

-- Findings by severity
SELECT severity, COUNT(*) 
FROM audit_findings 
WHERE created_at > datetime('now', '-7 days')
GROUP BY severity;

-- Findings by dimension
SELECT dimension, COUNT(*) 
FROM audit_findings 
WHERE created_at > datetime('now', '-7 days')
GROUP BY dimension
ORDER BY COUNT(*) DESC;
```

---

## File Structure

```
src/
└── cli/
    ├── dashboard/
    │   ├── __init__.py       # Module exports
    │   ├── metrics.py        # MetricsAggregator
    │   └── renderer.py       # DashboardRenderer
    └── export/
        ├── __init__.py       # Module exports
        ├── pdf.py            # PDFGenerator
        └── templates/
            ├── base.html     # Base HTML template
            ├── report.html   # Report template
            ├── summary.html  # Summary template
            ├── proposal.html # Proposal template
            └── dashboard.html# Dashboard template
config/
└── default.yaml              # Updated with dashboard/export config
tests/
└── unit/
    ├── test_dashboard_metrics.py
    ├── test_dashboard_renderer.py
    └── test_export_pdf.py
```

---

## Tasks

### Phase 1: Dashboard Foundation
- [ ] Create `src/cli/dashboard/` directory structure
- [ ] Create `src/cli/dashboard/__init__.py` with module exports
- [ ] Create `src/cli/export/` directory structure
- [ ] Create `src/cli/export/__init__.py` with module exports
- [ ] Add `weasyprint>=60.0` to requirements.txt
- [ ] Add `jinja2>=3.0.0` to requirements.txt
- [ ] Add `dashboard:` and `export:` config sections to `config/default.yaml`
- [ ] Add `DashboardConfig` and `ExportConfig` to `src/config/schema.py`
- [ ] Define `DashboardMetrics`, `FindingsSummary`, `TrendData` models
- [ ] Write unit tests for foundation models

### Phase 2: Metrics Aggregator
- [ ] Create `src/cli/dashboard/metrics.py`
- [ ] Implement `MetricsAggregator` class
- [ ] Implement `get_audit_count()` method
- [ ] Implement `get_findings_summary()` method
- [ ] Implement `get_severity_distribution()` method
- [ ] Implement `get_dimension_breakdown()` method
- [ ] Implement `get_trend_data()` method
- [ ] Implement `get_artifact_stats()` method
- [ ] Add period filtering (day, week, month, all)
- [ ] Write unit tests for metrics aggregator

### Phase 3: Dashboard Renderer
- [ ] Create `src/cli/dashboard/renderer.py`
- [ ] Implement `DashboardRenderer` class
- [ ] Implement `render_terminal()` with Rich tables
- [ ] Implement `render_html()` with basic styling
- [ ] Implement `render_json()` with pretty formatting
- [ ] Add color coding for severity levels
- [ ] Add trend indicators (up/down arrows)
- [ ] Write unit tests for renderer

### Phase 4: HTML Templates
- [ ] Create `src/cli/export/templates/` directory
- [ ] Create `base.html` with CSS styles
- [ ] Create `report.html` extending base
- [ ] Create `summary.html` for condensed view
- [ ] Create `proposal.html` for design proposals
- [ ] Create `dashboard.html` for metrics dashboard
- [ ] Add print-friendly CSS media queries
- [ ] Write tests for template rendering

### Phase 5: PDF Generator
- [ ] Create `src/cli/export/pdf.py`
- [ ] Implement `PDFGenerator` class
- [ ] Implement `generate_from_markdown()` method
- [ ] Implement `generate_from_report()` method
- [ ] Implement `set_template()` method
- [ ] Add markdown-to-HTML conversion
- [ ] Handle images in PDF (embed base64)
- [ ] Add page numbers and headers/footers
- [ ] Write unit tests for PDF generator

### Phase 6: CLI Commands
- [ ] Create `src/cli/commands/dashboard.py`
- [ ] Implement `glm dashboard` command
- [ ] Add `--html` flag for HTML output
- [ ] Add `--output` flag for file save
- [ ] Add `--period` flag for time filtering
- [ ] Create `src/cli/commands/export.py`
- [ ] Add `--pdf` flag to report command
- [ ] Add `--pdf` flag to propose command
- [ ] Write integration tests for commands

### Phase 7: Integration & Testing
- [ ] Test dashboard with populated database
- [ ] Test PDF generation with sample reports
- [ ] Verify HTML output renders correctly
- [ ] Test print CSS in browser
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] `glm dashboard` displays metrics in terminal
- [ ] `glm dashboard --html` generates valid HTML file
- [ ] `glm dashboard --period week` filters to last 7 days
- [ ] `glm report <id> --pdf` generates PDF file
- [ ] `glm propose <id> --pdf` generates proposal PDF
- [ ] PDF includes proper formatting and page numbers
- [ ] HTML templates render correctly in browser
- [ ] Metrics reflect actual database contents
- [ ] Unit test coverage > 90% for new modules
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| WeasyPrint system deps missing | Document brew install commands clearly |
| Large PDF generation slow | Progress indicator, async option |
| HTML rendering differences | Use print CSS, test in major browsers |
| Database query performance | Add indexes, cache frequent queries |
| Template XSS vulnerabilities | Jinja2 auto-escaping enabled |

---

## Validation

Run after completion:
```bash
# Test dashboard command
glm dashboard

# Test HTML dashboard
glm dashboard --html --output /tmp/dashboard.html
open /tmp/dashboard.html

# Test PDF export
glm report latest --pdf --output /tmp/report.pdf
open /tmp/report.pdf

# Test period filtering
glm dashboard --period month

# Run dashboard/export tests
python -m pytest tests/unit/test_dashboard*.py tests/unit/test_export*.py -v

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- `weasyprint>=60.0` — PDF generation
- `jinja2>=3.0.0` — HTML templates

### System Dependencies (macOS)
- `pango` — Text rendering
- `gdk-pixbuf` — Image handling
- `libffi` — Foreign function interface

Install via Homebrew:
```bash
brew install pango gdk-pixbuf libffi
```

### Internal Dependencies
- `src.cli.commands` — CLI integration
- `src.db.crud` — Database queries
- `src.plan.models` — Report models
- `src.plan.report_writer` — Report data

---

*Created: 2026-03-05*