# Epic M7-1: Golden Dataset Creation

> **Milestone:** 7 - Testing Infrastructure  
> **Priority:** Critical  
> **Dependencies:** None  
> **Status:** ✅ Complete

---

## Objective

Create synthetic UI screenshots with known issues and expected audit outputs to validate CV detection accuracy (>95% target) and audit finding correctness.

---

## Scope

### In Scope
- Synthetic UI screenshot generation with controlled issues
- Expected detection results (bounding boxes, component types)
- Expected audit findings per screenshot
- Video flow with expected key frames and transitions
- CV accuracy validation script
- Audit accuracy validation script
- Test fixture organization and documentation

### Out of Scope
- Real-world screenshot collection (focus on synthetic for reproducibility)
- Performance benchmarking (M7-2)
- Integration tests with mocks (M7-3)
- CI pipeline configuration (M7-4)

---

## Deliverables

### 1. Synthetic Screenshot Generator (`tests/fixtures/synthetic_screens/`)

Programmatic generation of UI screenshots with controlled issues:

- `generator.py` — Screenshot generation with configurable issues
- `templates/` — Base UI templates (login, dashboard, form, list, etc.)
- `issue_injectors.py` — Inject specific issues (low contrast, bad spacing, etc.)

**Screenshot Categories:**
| Category | Count | Issues Covered |
|----------|-------|----------------|
| Hierarchy | 3 | Focal point, competing elements, visual weight |
| Spacing | 3 | Cramped margins, inconsistent rhythm, grid violations |
| Typography | 3 | Small font size, hierarchy breaks, weight inconsistency |
| Color | 3 | Low contrast, insufficient distinct colors, accessibility |
| Alignment | 3 | Off-grid elements, misalignment, centering issues |
| Components | 3 | Size inconsistency, style proliferation, variant chaos |
| States | 2 | Missing empty state, missing error state |
| **Total** | **20+** | All 13 dimensions covered |

### 2. Expected Detection Results (`tests/golden-dataset/detection/`)

JSON files with expected CV detection output:

```
detection/
├── hierarchy_001.json       # Expected components, bounding boxes
├── hierarchy_002.json
├── spacing_001.json
├── ...
└── schema.json              # Validation schema for expected results
```

**Schema:**
```json
{
  "screenshot_id": "uuid",
  "components": [
    {
      "type": "button|input|label|...",
      "bounding_box": {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.1},
      "confidence": 1.0,
      "attributes": {"text": "...", "visible": true}
    }
  ],
  "hierarchy": {
    "root": "container_1",
    "tree": {...}
  }
}
```

### 3. Expected Audit Findings (`tests/golden-dataset/findings/`)

JSON files with expected audit findings per screenshot:

```
findings/
├── hierarchy_001.json       # Expected findings with severity
├── hierarchy_002.json
├── spacing_001.json
├── ...
└── schema.json              # Validation schema
```

**Schema:**
```json
{
  "screenshot_id": "uuid",
  "expected_findings": [
    {
      "dimension": "typography",
      "issue": "font_size_too_small",
      "severity": "high",
      "location": {"component_id": "text_3"},
      "rationale": "Font size 11px below minimum 12px"
    }
  ],
  "tolerance": {
    "severity_flexibility": false,
    "max_extra_findings": 2
  }
}
```

### 4. Video Flow Fixtures (`tests/golden-dataset/videos/`)

Synthetic video flows with expected analysis:

```
videos/
├── login_flow.mp4           # 3-screen login flow
├── login_flow_expected.json # Expected key frames, transitions
├── navigation_flow.mp4      # Tab navigation flow
├── navigation_flow_expected.json
└── video_schema.json        # Validation schema
```

**Video Expected Schema:**
```json
{
  "video_id": "uuid",
  "key_frames": [
    {
      "timestamp_ms": 0,
      "reason": "first_frame",
      "expected_components": 5
    },
    {
      "timestamp_ms": 1500,
      "reason": "content_change",
      "expected_components": 8
    }
  ],
  "transitions": [
    {"from_frame": 0, "to_frame": 1, "type": "navigation"}
  ]
}
```

### 5. CV Accuracy Validator (`tests/golden-dataset/validators/`)

Scripts to validate detection and audit accuracy:

- `detection_validator.py` — Compare CV output to expected results
- `audit_validator.py` — Compare audit findings to expected findings
- `accuracy_reporter.py` — Generate accuracy metrics

**Metrics:**
- Component detection precision/recall
- Bounding box IoU (Intersection over Union)
- Finding detection rate
- False positive rate
- Severity classification accuracy

### 6. Dataset Documentation (`tests/golden-dataset/README.md`)

Comprehensive documentation:
- Dataset structure and organization
- How to add new test cases
- Validation procedures
- Accuracy targets and current results

---

## Technical Decisions

### Screenshot Generation: Programmatic Synthetic
- **Decision:** Generate synthetic UI screenshots programmatically
- **Rationale:**
  - Fully reproducible and version-controlled
  - Exact control over issues injected
  - No licensing/privacy concerns with real screenshots
  - Easy to extend with new test cases

**Approach:** Use PIL/Pillow to draw UI elements with precise positioning and styling.

### Bounding Box Tolerance: IoU > 0.7
- **Decision:** Accept bounding boxes with IoU > 0.7 as correct
- **Rationale:**
  - CV detection has inherent variance
  - 0.7 IoU is standard for object detection evaluation
  - Allows minor pixel-level differences

### Finding Tolerance: Severity Strict, Count Flexible
- **Decision:** Severity must match exactly, allow 2 extra findings
- **Rationale:**
  - Severity misclassification is a real issue
  - Extra findings may be valid (conservative auditor)
  - Missing findings is the critical failure mode

### Video Generation: Static Frame Sequences
- **Decision:** Create videos from static screenshot sequences
- **Rationale:**
  - Simpler than recording real interactions
  - Exact control over timing and transitions
  - Can reuse synthetic screenshots

---

## File Structure

```
tests/
├── fixtures/
│   └── synthetic_screens/
│       ├── __init__.py
│       ├── generator.py           # ScreenshotGenerator class
│       ├── templates.py           # UI templates (login, form, etc.)
│       ├── issue_injectors.py     # Issue injection functions
│       └── assets/                # Fonts, icons for generation
├── golden-dataset/
│   ├── README.md                  # Dataset documentation
│   ├── screenshots/               # Generated PNG files
│   │   ├── hierarchy_001.png
│   │   ├── hierarchy_002.png
│   │   └── ...
│   ├── detection/                 # Expected CV results
│   │   ├── schema.json
│   │   ├── hierarchy_001.json
│   │   └── ...
│   ├── findings/                  # Expected audit findings
│   │   ├── schema.json
│   │   ├── hierarchy_001.json
│   │   └── ...
│   ├── videos/                    # Video fixtures
│   │   ├── login_flow.mp4
│   │   ├── login_flow_expected.json
│   │   └── ...
│   └── validators/
│       ├── __init__.py
│       ├── detection_validator.py # Validate CV detection
│       ├── audit_validator.py     # Validate audit findings
│       └── accuracy_reporter.py   # Generate accuracy reports
└── unit/
    └── test_golden_dataset.py     # Tests for dataset validity
```

---

## Tasks

### Phase 1: Infrastructure Setup
- [ ] Create `tests/fixtures/synthetic_screens/` directory structure
- [ ] Create `tests/golden-dataset/` directory structure
- [ ] Create `tests/golden-dataset/README.md` with documentation
- [ ] Create detection schema (`detection/schema.json`)
- [ ] Create findings schema (`findings/schema.json`)
- [ ] Create video schema (`videos/video_schema.json`)

### Phase 2: Screenshot Generator
- [ ] Create `generator.py` with `ScreenshotGenerator` class
- [ ] Create `templates.py` with base UI templates
- [ ] Create `issue_injectors.py` with issue injection functions
- [ ] Add placeholder assets (fonts, basic shapes)
- [ ] Write unit tests for generator
- [ ] Generate 5 hierarchy test screenshots
- [ ] Generate 5 spacing test screenshots
- [ ] Generate 5 typography test screenshots
- [ ] Generate 5 color test screenshots
- [ ] Generate 3 alignment test screenshots
- [ ] Generate 3 component test screenshots
- [ ] Generate 2 state test screenshots

### Phase 3: Expected Results
- [ ] Create expected detection JSON for each screenshot
- [ ] Create expected findings JSON for each screenshot
- [ ] Validate all expected results against schemas
- [ ] Document the issue(s) each screenshot tests

### Phase 4: Video Fixtures
- [ ] Create 3-frame login flow from synthetic screenshots
- [ ] Create expected key frames JSON for login flow
- [ ] Create 4-frame navigation flow from synthetic screenshots
- [ ] Create expected key frames JSON for navigation flow
- [ ] Validate video expected results

### Phase 5: Validators
- [ ] Create `detection_validator.py` with IoU calculation
- [ ] Create `audit_validator.py` with finding comparison
- [ ] Create `accuracy_reporter.py` with metrics generation
- [ ] Write unit tests for validators
- [ ] Run validation against all golden dataset files

### Phase 6: Validation & Documentation
- [ ] Run full golden dataset validation
- [ ] Generate initial accuracy report
- [ ] Document any gaps or issues found
- [ ] Update README with usage instructions
- [ ] Add golden dataset tests to test suite

---

## Success Criteria

- [ ] 20+ synthetic screenshots covering all 13 audit dimensions
- [ ] Each screenshot has valid expected detection JSON
- [ ] Each screenshot has valid expected findings JSON
- [ ] 2 video flows with expected key frame analysis
- [ ] Detection validator calculates IoU correctly
- [ ] Audit validator compares findings correctly
- [ ] Accuracy reporter generates metrics
- [ ] All schemas validate in CI
- [ ] Golden dataset tests pass

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Synthetic screenshots don't reflect real UI | Include variety of patterns, use realistic text content |
| Expected results become outdated | Schema validation, automated tests |
| Video generation complexity | Start with simple 3-4 frame sequences |
| Bounding box IoU too strict | Start with 0.7, adjust based on results |
| False positives in findings | Tolerance allows 2 extra findings |

---

## Validation

Run after completion:
```bash
# Validate all schemas
python -c "from tests.golden_dataset.validators import validate_all_schemas; validate_all_schemas()"

# Run detection validation
python -m pytest tests/unit/test_golden_dataset.py -v -k detection

# Run audit validation
python -m pytest tests/unit/test_golden_dataset.py -v -k audit

# Generate accuracy report
python -c "from tests.golden_dataset.validators import AccuracyReporter; print(AccuracyReporter().generate_report())"

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- `pillow>=10.0.0` — Already installed
- `pydantic>=2.0.0` — Already installed

### Internal Dependencies
- `src.vision.client` — CV detection (for validation)
- `src.audit.orchestrator` — Audit execution (for validation)

---

*Created: 2026-03-13*