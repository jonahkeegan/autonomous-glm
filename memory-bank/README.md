# Autonomous-GLM Memory Bank

**Purpose:** Persistent memory for the Autonomous UI/UX Design Agent that enables compound learning across audit cycles and multi-agent collaboration.

This directory stores:
- Current session context and milestone progress
- Skill matrix for CV/audit capabilities
- Audit patterns and anti-patterns (mistakes)
- Cross-agent feedback and dispute resolutions
- Consolidated learnings from design audit cycles

**Mode:** Design Agent (audit-driven, activity-centric, agent-collaborative)

---

## What Lives Here

### Core Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `active-context.md` | Current session state, milestone progress, agent handshakes | Every session |
| `skill-matrix.json` | CV/audit capability confidence scores (0.0-1.0) | After each audit cycle |

### Learnings Files

| File | Purpose | Format |
|------|---------|--------|
| `audit-patterns.md` | Reusable detection patterns for UI/UX audits | Append-only markdown |
| `mistakes.md` | Anti-patterns: false positives, misclassifications, missed issues | Append-only markdown |
| `agent-feedback.md` | Cross-agent learning log (disputes, resolutions, handshakes) | Append-only markdown |
| `consolidated-learnings.md` | Refined patterns extracted from multiple audit cycles | Periodic consolidation |

---

## Update Protocol

### Session Start

1. Read `active-context.md` to restore current state
2. Check `skill-matrix.json` for current capability confidence
3. Review relevant entries in `audit-patterns.md` for applicable patterns
4. Check `agent-feedback.md` for pending disputes or unresolved feedback

### During Audit Cycle

| Event | Action |
|-------|--------|
| Audit completed | Update `skill-matrix.json` with confidence delta |
| Pattern discovered | Append to `audit-patterns.md` |
| Mistake made | Append to `mistakes.md` with prevention rule |
| Agent feedback received | Log to `agent-feedback.md` |
| Dispute escalated | Document in `agent-feedback.md` with resolution pending |
| Human override | Log to `agent-feedback.md` with rationale |

### Session End

1. Update `active-context.md` with:
   - Current milestone and epic progress
   - Recent audits completed
   - Active blockers or pending reviews
   - Agent handshake status
   - Notes for next session
2. If `mistakes.md` has 10+ new entries, trigger consolidation review
3. Update skill confidence based on audit performance

---

## Learning Loop

After each completed audit cycle:

### Capture Artifacts
1. **Successful Patterns** — Detection approaches that worked well
2. **Mistakes** — False positives, missed issues, misclassified severity
3. **Agent Feedback** — Disputes received and their resolutions
4. **Human Overrides** — When human disagreed and why

### Consolidation Trigger
When `mistakes.md` reaches 10+ entries, consolidate into `consolidated-learnings.md`:
- Extract common themes
- Document prevention rules
- Update skill confidence deltas
- Archive processed entries

---

## Skill Matrix Schema

```json
{
  "cv_detection": { "confidence": 0.0, "last_updated": null },
  "hierarchy_analysis": { "confidence": 0.0, "last_updated": null },
  "accessibility_audit": { "confidence": 0.0, "last_updated": null },
  "color_typography": { "confidence": 0.0, "last_updated": null },
  "motion_transitions": { "confidence": 0.0, "last_updated": null }
}
```

**Confidence Scale:**
- `0.0` — Uninitialized / no data
- `0.1-0.3` — Low confidence (learning)
- `0.4-0.6` — Medium confidence (developing)
- `0.7-0.9` — High confidence (reliable)
- `1.0` — Mastered (consistent accuracy)

---

## Agent Communication

### Collaborating Agents

| Agent | Role | Communication Focus |
|-------|------|---------------------|
| **Claude** | Product Manager / Arbiter | Audit summaries, dispute routing, design system changes |
| **Minimax** | Frontend Engineer | Implementation-ready findings, phased plans |
| **Codex** | Backend Engineer | Visual fit confirmations post-API integration |
| **Human** | Design Lead | Disputed findings, design system proposals, overrides |

### Handshake Status

Track in `active-context.md`:
- **Pending** — Not yet connected
- **Active** — Communication established
- **Error** — Connection failed, requires intervention

### Message Types
- `AUDIT_COMPLETE` — Full audit cycle finished
- `DESIGN_PROPOSAL` — Design system change proposed
- `DISPUTE` — Agent or human disagreement
- `HUMAN_REQUIRED` — Escalation for human review

---

## Key Principles

1. **Audit-first persistence** — Every audit cycle generates learnings
2. **Append-only learnings** — Never overwrite; always append
3. **Agent-aware context** — Track multi-agent collaboration state
4. **Confidence-driven** — Skill matrix reflects real capability
5. **Human-in-the-loop** — Escalate design system changes and disputes
6. **Activity-centric** — Capture user intent, not just pixel analysis
7. **Standards-referenced** — Every finding links to design system or WCAG

---

## Quality Gates

Per AGENTS.md, track against:

| Metric | Target |
|--------|--------|
| CV Detection Accuracy | >95% on golden dataset |
| Audit Completeness | All 15+ SOUL.md dimensions |
| Finding Classification | Consistent severity levels |
| Standards Reference | Every finding linked |

---

## Related Documentation

- **PRD:** `autonomous-glm-prd.md`
- **Design Philosophy:** `SOUL.md`
- **Agent Rules:** `AGENTS.md`
- **Design System:** `design_system/tokens.md`, `design_system/components.md`, `design_system/standards.md`
- **Milestone Plans:** `tasks/aes-autonomous-glm-milestones.md`

---

*"Every audit makes the next audit smarter. The Memory Bank is your design conscience."*