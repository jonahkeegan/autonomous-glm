# Golden Dataset for Autonomous-GLM CV/Audit Validation

## Overview

This golden dataset provides synthetic UI screenshots with known ground truth for testing the Autonomous-GLM computer vision detection and audit accuracy validation pipeline.

## Dataset Structure

```
tests/golden-dataset/
├── README.md                 # This file
├── manifest.json             # Dataset manifest with metadata
├── screenshots/              # PNG images (22 synthetic screenshots)
├── detection/                # Expected detection results (JSON)
├── findings/                 # Expected audit findings (JSON)
└── validators/               # Python validators for accuracy testing
    ├── __init__.py
    ├── detection_validator.py
    ├── audit_validator.py
    └── accuracy_reporter.py
```

## Screenshots

The dataset contains **22 synthetic screenshots** covering **10 audit dimensions**:

| Dimension | Screenshots | Issues Covered |
|-----------|-------------|----------------|
| visual_hierarchy | 3 | no_focal_point, competing_elements |
| spacing_rhythm | 3 | cramped_margins, inconsistent_rhythm |
| typography | 3 | font_size_too_small, typography_hierarchy_break |
| color | 2 | low_contrast |
| alignment_grid | 3 | off_grid_elements, misalignment |
| components | 3 | size_inconsistency, style_proliferation |
| accessibility | 1 | color_accessibility |
| empty_states | 1 | missing_empty_state |
| error_states | 1 | missing_error_state |
| density | 2 | too_dense, too_sparse |

Each dimension includes:
- **Issue screenshots**: With specific injected issues
- **Clean screenshots**: With proper design (no issues)

## Detection Schema

Each detection JSON file contains:

```json
{
  "screenshot_id": "uuid",
  "name": "screenshot_name",
  "dimensions": {"width": 390, "height": 844},
  "components": [
    {
      "id": "comp_0",
      "type": "button|text|input|card|...",
      "label": "Component label",
      "bounding_box": {
        "x": 0.1,  // Normalized (0-1)
        "y": 0.2,
        "w": 0.3,
        "h": 0.1
      },
      "bounding_box_px": {
        "x": 39,    // Pixels
        "y": 169,
        "width": 117,
        "height": 84
      },
      "confidence": 1.0,
      "attributes": {
        "text": "Component label",
        "visible": true,
        "is_issue": false,
        "issue_type": null
      }
    }
  ],
  "component_count": 15,
  "component_types": ["button", "text", "input", ...],
  "created": "ISO-8601 timestamp"
}
```

## Findings Schema

Each findings JSON file contains:

```json
{
  "screenshot_id": "uuid",
  "name": "screenshot_name",
  "expected_findings": [
    {
      "dimension": "typography",
      "issue": "font_size_too_small",
      "severity": "high|medium|low",
      "location": {"component_ids": ["comp_5"]},
      "rationale": "Text too small to read"
    }
  ],
  "tolerance": {
    "severity_flexibility": false,
    "max_extra_findings": 2
  },
  "created": "ISO-8601 timestamp"
}
```

## Validators

### Detection Validator

Compares CV detection results against expected ground truth:

```python
from tests.golden_dataset.validators import validate_detection

result = validate_detection(expected, detected, iou_threshold=0.7)

# Result contains:
# - passed: bool
# - matched_count: int
# - missed_count: int
# - extra_count: int
# - mean_iou: float
```

### Audit Validator

Compares audit findings against expected results:

```python
from tests.golden_dataset.validators import validate_findings

result = validate_findings(expected, detected)

# Result contains:
# - passed: bool
# - matched_count: int
# - missed_count: int
# - severity_mismatches: int
```

### Accuracy Reporter

Generates comprehensive accuracy reports:

```python
from tests.golden_dataset.validators import generate_accuracy_report

report = generate_accuracy_report(detection_results, audit_results)

# Report contains:
# - total_screenshots: int
# - detection_accuracy: float
# - audit_accuracy: float
# - overall_accuracy: float
# - passed: bool (>= 95% accuracy)
```

## Usage

### Generate Dataset

```bash
python -m tests.fixtures.synthetic_screens.generator
```

### Run Validation Tests

```bash
python -m pytest tests/unit/test_golden_dataset.py -v
```

### Expected Accuracy Threshold

- **Detection accuracy**: >= 95%
- **Audit accuracy**: >= 95%
- **Mean IoU**: >= 0.7

## Design Principles

1. **Deterministic**: Same input always produces same output
2. **Comprehensive**: Covers all audit dimensions
3. **Realistic**: Mimics real-world UI patterns
4. **Ground Truth**: Every component and issue is known precisely
5. **Extensible**: Easy to add new templates and issue types

## Adding New Screenshots

1. Create a new template in `tests/fixtures/synthetic_screens/templates.py`
2. Add issue injector in `tests/fixtures/synthetic_screens/issue_injectors.py`
3. Add spec to `SCREENSHOT_SPECS` in `generator.py`
4. Run generator to create files