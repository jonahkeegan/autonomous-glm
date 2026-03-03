# Minimal Validation Dataset

**Purpose:** Synthetic UI screenshots with programmatically-known component layouts for testing the M3-1 persistence layer and validating detection accuracy.

## Dataset Overview

| Screenshot | Description | Components | Types |
|------------|-------------|------------|-------|
| screenshot_001 | Login form with inputs and buttons | 8 | header, input, button, text |
| screenshot_002 | Dashboard with stats cards | 23 | header, card, text |
| screenshot_003 | E-commerce product card | 7 | card, image, text, button |
| screenshot_004 | Settings form with inputs | 15 | header, text, input, button |
| screenshot_005 | Navigation sidebar layout | 12 | text, navigation, header, card |

**Total:** 58 components across 5 screenshots

## File Structure

```
validation/
├── README.md                           # This file
├── manifest.json                       # Dataset manifest
├── generate_validation_fixtures.py     # Generation script
├── screenshot_001.png                  # Login form
├── screenshot_001.json                 # Expected components
├── screenshot_002.png                  # Dashboard
├── screenshot_002.json                 # Expected components
├── screenshot_003.png                  # Product card
├── screenshot_003.json                 # Expected components
├── screenshot_004.png                  # Settings form
├── screenshot_004.json                 # Expected components
├── screenshot_005.png                  # Sidebar layout
└── screenshot_005.json                 # Expected components
```

## Component Types

The dataset includes the following component types:

- **button** - Clickable action buttons
- **input** - Text input fields with placeholders
- **text** - Static text labels and content
- **header** - Page/section headers
- **card** - Container cards
- **image** - Image placeholders
- **navigation** - Navigation menu items

## Metadata Format

Each JSON metadata file contains:

```json
{
  "name": "screenshot_001",
  "description": "Login form with inputs and buttons",
  "dimensions": {"width": 400, "height": 600},
  "components": [
    {
      "type": "button",
      "label": "Sign In",
      "bbox": {"x": 40, "y": 220, "width": 320, "height": 44},
      "bbox_normalized": {"x": 0.1, "y": 0.3667, "width": 0.8, "height": 0.0733}
    }
  ],
  "component_count": 8,
  "component_types": ["header", "input", "button", "text"]
}
```

## Usage

### For Persistence Testing

```python
from src.db.crud import batch_create_components
from src.vision.models import DetectedComponent, ComponentType

# Load expected components from metadata
import json
with open("tests/golden-dataset/validation/screenshot_001.json") as f:
    metadata = json.load(f)

# Create DetectedComponent objects
components = []
for c in metadata["components"]:
    comp = DetectedComponent(
        type=ComponentType(c["type"]),
        label=c.get("label"),
        bbox_x=c["bbox_normalized"]["x"],
        bbox_y=c["bbox_normalized"]["y"],
        bbox_width=c["bbox_normalized"]["width"],
        bbox_height=c["bbox_normalized"]["height"],
    )
    components.append(comp)

# Persist to database
persisted = batch_create_components(screen_id, components)
```

### For Detection Accuracy Validation

Compare vision detection results against known ground truth:

```python
from src.vision.client import VisionClient

client = VisionClient()
result = client.detect_components("tests/golden-dataset/validation/screenshot_001.png")

# Load expected components
with open("tests/golden-dataset/validation/screenshot_001.json") as f:
    expected = json.load(f)

# Compare detected vs expected
detected_types = [c.type.value for c in result.components]
expected_types = [c["type"] for c in expected["components"]]

# Calculate accuracy
# (simplified - real validation would compare bounding boxes too)
```

## Regenerating Fixtures

To regenerate the validation fixtures:

```bash
./venv/bin/python tests/golden-dataset/validation/generate_validation_fixtures.py
```

## Design Decisions

1. **Synthetic screenshots** - Programmatically generated with exact ground truth, no external dependencies
2. **Normalized coordinates** - Bounding boxes in both pixel and normalized (0.0-1.0) coordinates
3. **High contrast colors** - Simple color palette for reliable detection
4. **Variety of layouts** - Login forms, dashboards, cards, settings, navigation patterns

## Future Enhancements

- Add color token values for token extraction validation
- Add edge cases (empty states, error states, loading states)
- Add multi-viewport screenshots for responsiveness testing
- Add video flows with frame sequences

---

*Created: 2026-03-02*
*Part of: M3-1 Database Persistence Integration*
+++++++ REPLACE