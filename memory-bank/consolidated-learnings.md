# Consolidated Learnings

Refined actionable patterns consolidated from `mistakes.md` and audit cycles.

**Trigger**: This file is updated when `mistakes.md` reaches 10+ entries.

---

## Learning Categories

### CV Detection
*Learnings related to component detection accuracy*

*(No consolidated learnings yet)*

---

### Hierarchy Analysis
*Learnings related to visual hierarchy scoring*

*(No consolidated learnings yet)*

---

### Accessibility Audit
*Learnings related to WCAG compliance detection*

*(No consolidated learnings yet)*

---

### Color & Typography
*Learnings related to color contrast and typography analysis*

*(No consolidated learnings yet)*

---

### Motion & Transitions
*Learnings related to animation and transition analysis*

*(No consolidated learnings yet)*

---

### Agent Communication
*Learnings related to multi-agent protocol handling*

*(No consolidated learnings yet)*

---

### Human-in-the-Loop
*Learnings related to escalation and review processes*

*(No consolidated learnings yet)*

---

### Development Workflow
*Learnings related to development process and tooling*

#### 2026-02-28: SQLite + Pydantic Data Layer
- **Category**: Development Workflow
- **Derived from**: M0-1 Database Schema implementation
- **Pattern**: SQLite with Pydantic models provides type-safe local data storage with minimal boilerplate
- **Actions**:
  - Use UUID primary keys for all tables to support future distributed scenarios
  - Store flexible fields (hierarchy, actions) as JSON to avoid schema churn
  - Normalize enums into reference tables with joined views
- **Anti-patterns to avoid**:
  - Don't rely on Pydantic `min_length` for empty string validation - use DB constraints
  - Don't forget `PRAGMA foreign_keys = ON` for SQLite FK enforcement
  - Don't skip venv setup on macOS (PEP 668 externally-managed environment)

---

## Consolidation Log

| Date | Source Entries | Categories Updated |
|------|----------------|-------------------|
| 2026-02-28 | M0-1 Implementation | Development Workflow |

---

## Usage Notes

1. **When to consolidate**: When `mistakes.md` reaches 10+ entries
2. **How to consolidate**: 
   - Group related mistakes by category
   - Extract the reusable pattern or prevention strategy
   - Document as a consolidated learning below
   - Clear or archive the processed entries in `mistakes.md`
3. **Cross-reference**: Link to related `audit-patterns.md` entries where applicable

---

## Template for New Learning Entry

```markdown
### [Learning Title]
- **Category**: CV Detection | Hierarchy Analysis | Accessibility | Color/Typography | Motion | Agent Communication | Human-in-the-Loop
- **Derived from**: [Link to original mistake(s) or audit(s)]
- **Pattern**: [The reusable insight]
- **Action**: [How to apply this learning]
- **Anti-pattern to avoid**: [What NOT to do]