# Epic M2-3: Token Extraction

> **Milestone:** 2 - CV/AI Analysis Core  
> **Priority:** High  
> **Dependencies:** Epic M2-1 (Component Detection Pipeline)  
> **Status:** 🔲 Not Started

---

## Objective

Extract design tokens (colors, spacing, typography) from detected UI components and match them against the design system, enabling the audit engine to identify inconsistencies and deviations from standards.

---

## Scope

### In Scope
- Color extraction from component regions
- Color normalization (hex, RGB, HSL conversions)
- Dominant color identification per component
- Color clustering to find repeated palette colors
- Spacing/margin/padding inference from bounding boxes
- Typography detection (font size, weight estimation)
- Token reference matching to design system tokens
- SystemToken entity persistence
- Component-to-token linking

### Out of Scope
- Design system proposals (M4)
- Contrast checking (M3 Audit Engine)
- Token evolution tracking
- Font family identification (requires OCR)
- Exact pixel measurement (estimation only)
- Animation/motion tokens

---

## Deliverables

### 1. Color Extractor (`src/vision/tokens/color.py`)

Color extraction utilities:
- `ColorExtractor` — Main color extraction class
- `extract_colors(image_path: str, bbox: BoundingBox) -> ColorResult` — Extract from region
- `get_dominant_color(pixels: np.array) -> RGB` — Find dominant color
- `cluster_colors(colors: list[RGB], n_clusters: int) -> list[ColorCluster]` — Group similar colors
- `normalize_color(color: RGB) -> ColorNormalizations` — Convert to all formats

### 2. Spacing Analyzer (`src/vision/tokens/spacing.py`)

Spacing inference utilities:
- `SpacingAnalyzer` — Spacing analysis class
- `infer_margins(component: Component, screen: Screen) -> Margins` — Calculate margins
- `infer_padding(container: Component, children: list[Component]) -> Padding` — Estimate padding
- `detect_spacing_pattern(spacings: list[float]) -> SpacingPattern` — Find consistent spacing
- `quantize_to_grid(value: float, grid_base: int) -> int` — Snap to grid

### 3. Typography Detector (`src/vision/tokens/typography.py`)

Typography estimation utilities:
- `TypographyDetector` — Typography detection class
- `estimate_font_size(component: Component, image_path: str) -> FontSizeEstimate` — Size from bbox
- `estimate_font_weight(component: Component) -> FontWeightEstimate` — Weight from appearance
- `detect_line_height(text_bbox: BoundingBox, font_size: int) -> float` — Line height calculation

### 4. Token Matcher (`src/vision/tokens/matcher.py`)

Design system matching:
- `TokenMatcher` — Token matching class
- `match_color(color: RGB, design_tokens: list[SystemToken]) -> TokenMatch` — Find closest color token
- `match_spacing(value: float, design_tokens: list[SystemToken]) -> TokenMatch` — Find spacing token
- `match_typography(size: int, weight: str, design_tokens: list[SystemToken]) -> TokenMatch` — Find type token
- `calculate_token_distance(value: Any, token: SystemToken) -> float` — Similarity score

### 5. Token Models (`src/vision/tokens/models.py`)

Pydantic models for tokens:
- `RGB`, `HSL`, `HexColor` — Color representations
- `ColorResult` — Extracted color with all formats
- `ColorCluster` — Grouped similar colors
- `Margins`, `Padding` — Spacing models
- `FontSizeEstimate`, `FontWeightEstimate` — Typography models
- `TokenMatch` — Match result with confidence

### 6. Database Integration

SystemToken persistence:
- Create `SystemToken` records for discovered tokens
- Link components to tokens via `Component.token_refs`
- Track token usage frequency
- Update design system reference files

---

## Technical Decisions

### Color Extraction Method
- **Decision:** k-means clustering on pixel colors in component region
- **Rationale:**
  - k-means finds dominant colors reliably
  - Works well for UI components (typically 1-3 colors)
  - Fast with scikit-learn implementation
  - Can be tuned with cluster count parameter
- **Implementation:**
  - Extract pixels within bounding box
  - Run k-means with k=3 (background, foreground, accent)
  - Return cluster centers as dominant colors

### Color Distance Metric
- **Decision:** CIEDE2000 color difference on LAB color space
- **Rationale:**
  - Perceptually uniform distance
  - Better than RGB Euclidean distance
  - Standard for color matching
  - Available in colormath library

### Spacing Inference Strategy
- **Decision:** Edge detection + quantization to 4px/8px grid
- **Rationale:**
  - Most design systems use 4px or 8px base grid
  - Quantization handles measurement noise
  - Edge detection identifies component boundaries
  - Relative positioning gives spacing hints
- **Algorithm:**
  ```
  margin_left = component.bbox.x
  margin_right = screen_width - (component.bbox.x + component.bbox.width)
  Quantize to nearest: 4, 8, 12, 16, 24, 32, 48, 64
  ```

### Typography Estimation
- **Decision:** Bbox height estimation with OCR fallback (optional)
- **Rationale:**
  - Font size correlates with text bbox height
  - Simple estimation: `font_size ≈ bbox_height * 0.8`
  - OCR (Tesseract) can provide exact size but adds complexity
  - Make OCR optional enhancement
- **Weight Detection:**
  - Analyze pixel density in text region
  - Heavier fonts have higher pixel density
  - Classify as: light, regular, medium, semibold, bold

### Token Matching Threshold
- **Decision:** Configurable thresholds per token type
- **Rationale:**
  - Colors: ΔE < 5 for match (perceptually similar)
  - Spacing: Exact match or ±4px tolerance
  - Typography: Size within ±2px, weight exact
  - Unmatched tokens flagged for design system review

---

## File Structure

```
src/
└── vision/
    └── tokens/
        ├── __init__.py         # Module exports
        ├── color.py            # Color extraction
        ├── spacing.py          # Spacing inference
        ├── typography.py       # Typography detection
        ├── matcher.py          # Design system matching
        └── models.py           # Token Pydantic models
tests/
└── unit/
    └── test_tokens.py          # Token extraction tests
```

---

## Tasks

### Phase 1: Foundation & Models
- [ ] Create `src/vision/tokens/` directory structure
- [ ] Create `src/vision/tokens/__init__.py` with exports
- [ ] Create `src/vision/tokens/models.py` with all Pydantic models
- [ ] Add scikit-learn, colormath to requirements.txt
- [ ] Add numpy (already likely present via other deps)

### Phase 2: Color Extraction
- [ ] Create `src/vision/tokens/color.py`
- [ ] Implement `extract_colors()` - extract from image region
- [ ] Implement `get_dominant_color()` - k-means clustering
- [ ] Implement `cluster_colors()` - group similar colors across components
- [ ] Implement `normalize_color()` - convert to hex, RGB, HSL, LAB
- [ ] Write unit tests for color extraction

### Phase 3: Spacing Analysis
- [ ] Create `src/vision/tokens/spacing.py`
- [ ] Implement `infer_margins()` - calculate from position
- [ ] Implement `infer_padding()` - estimate from children
- [ ] Implement `detect_spacing_pattern()` - find consistent values
- [ ] Implement `quantize_to_grid()` - snap to design grid
- [ ] Write unit tests for spacing analysis

### Phase 4: Typography Detection
- [ ] Create `src/vision/tokens/typography.py`
- [ ] Implement `estimate_font_size()` - from bbox height
- [ ] Implement `estimate_font_weight()` - from pixel density
- [ ] Implement `detect_line_height()` - from text spacing
- [ ] Handle text components specifically
- [ ] Write unit tests for typography detection

### Phase 5: Token Matching
- [ ] Create `src/vision/tokens/matcher.py`
- [ ] Load design system tokens from `design_system/tokens.md`
- [ ] Implement `match_color()` with CIEDE2000 distance
- [ ] Implement `match_spacing()` with tolerance
- [ ] Implement `match_typography()` with size/weight matching
- [ ] Calculate match confidence scores
- [ ] Write unit tests for token matching

### Phase 6: Database Integration
- [ ] Create `SystemToken` records for matched tokens
- [ ] Link components to tokens via `token_refs` JSON field
- [ ] Track token usage frequency
- [ ] Handle unmatched tokens (flag for review)
- [ ] Write integration tests for database operations

### Phase 7: Testing & Validation
- [ ] Create test fixtures (components with known colors/spacing)
- [ ] Write comprehensive unit tests (>90% coverage)
- [ ] Test color extraction accuracy against known values
- [ ] Test spacing inference against measured values
- [ ] Test token matching against design system
- [ ] Test edge cases (gradients, images, transparent)
- [ ] Run full test suite and verify no regressions

---

## Success Criteria

- [ ] Color extraction identifies dominant colors correctly (>90% accuracy)
- [ ] Color clustering groups similar palette colors
- [ ] Color matching finds correct design system token (>85% accuracy)
- [ ] Spacing inference produces reasonable estimates (±4px)
- [ ] Typography estimation within ±2px of actual size
- [ ] Token matching confidence scores calibrated
- [ ] SystemToken entities created and linked correctly
- [ ] Unmatched tokens flagged for design system review
- [ ] Color extraction time < 100ms per component
- [ ] Full token extraction < 500ms per screen
- [ ] Unit test coverage > 90% for token modules
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Gradients confuse color extraction | Sample multiple points, report color range |
| Images within components skew colors | Detect image components, exclude from color analysis |
| Spacing inference inaccurate | Document as estimation, flag low-confidence |
| Font weight detection unreliable | Conservative classification, flag uncertain |
| Design system has no matching token | Flag as "unmatched", suggest new token |
| Performance with many components | Batch processing, limit cluster count |

---

## Validation

Run after completion:
```bash
# Run unit tests for tokens module
python -m pytest tests/unit/test_tokens.py -v

# Run full test suite
python -m pytest tests/ -v

# Test color extraction manually
python -c "
from src.vision.tokens.color import ColorExtractor
from src.vision.models import BoundingBox

extractor = ColorExtractor()
bbox = BoundingBox(x=0.1, y=0.1, width=0.3, height=0.2)
result = extractor.extract_colors('tests/fixtures/sample.png', bbox)
print(f'Dominant color: {result.dominant.hex}')
print(f'All colors: {[c.hex for c in result.colors]}')
"

# Test token matching
python -c "
from src.vision.tokens.matcher import TokenMatcher
from src.vision.tokens.models import RGB

matcher = TokenMatcher()
color = RGB(r=59, g=130, b=246)  # Tailwind blue-500
match = matcher.match_color(color, 'color')
print(f'Matched: {match.token_name}')
print(f'Confidence: {match.confidence}')
"

# Check coverage
python -m pytest tests/unit/test_tokens.py --cov=src/vision/tokens --cov-report=term-missing
```

---

## Dependencies

### Python Dependencies
- `scikit-learn>=1.3.0` — K-means clustering for color extraction
- `colormath>=3.0.0` — CIEDE2000 color distance calculation
- `numpy>=1.24.0` — Array operations (likely already present)

### Internal Dependencies
- `src/vision/models.py` — Component and bounding box models
- `src/db/crud.py` — Database operations
- `src/db/models.py` — SystemToken entity
- `design_system/tokens.md` — Design token definitions

---

## Design System Token Format

The token matcher reads from `design_system/tokens.md`. Expected format:

```markdown
## Colors

### Primary
- `color-primary-500`: #3B82F6
- `color-primary-600`: #2563EB

### Spacing
- `spacing-1`: 4px
- `spacing-2`: 8px
- `spacing-4`: 16px

### Typography
- `font-size-sm`: 14px
- `font-size-base`: 16px
- `font-weight-medium`: 500
```

---

*Created: 2026-03-02*