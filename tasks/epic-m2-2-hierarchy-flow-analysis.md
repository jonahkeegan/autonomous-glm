# Epic M2-2: Hierarchy & Flow Analysis

> **Milestone:** 2 - CV/AI Analysis Core  
> **Priority:** High  
> **Dependencies:** Epic M2-1 (Component Detection Pipeline)  
> **Status:** 🔲 Not Started

---

## Objective

Extract visual hierarchy relationships from detected components within screens, and sequence flows from video-extracted frames to establish temporal relationships for activity-centric analysis.

---

## Scope

### In Scope
- Screen hierarchy extraction (parent-child component relationships)
- Z-order/layer inference from component positions
- Container detection and nesting relationships
- Flow sequencing from video frame components
- Frame similarity detection for deduplication
- Flow entity metadata enrichment
- Temporal relationship tracking between screens
- Database persistence of hierarchy and flow data

### Out of Scope
- Component detection (M2-1)
- Token extraction (M2-3)
- Activity analysis (future enhancement)
- Interaction pattern detection (M3 Audit Engine)
- User behavior inference
- Cross-flow analysis

---

## Deliverables

### 1. Hierarchy Analyzer (`src/vision/hierarchy.py`)

Screen hierarchy extraction:
- `HierarchyAnalyzer` — Main hierarchy analysis class
- `extract_hierarchy(components: list[Component]) -> HierarchyTree` — Build component tree
- `detect_containers(components: list[Component]) -> list[ContainerMatch]` — Find parent containers
- `infer_z_order(components: list[Component]) -> list[ZLayer]` — Determine layering
- `calculate_nesting_depth(hierarchy: HierarchyTree) -> int` — Depth analysis

### 2. Flow Sequencer (`src/vision/flow.py`)

Flow analysis from video frames:
- `FlowSequencer` — Flow sequence analysis class
- `sequence_screens(screens: list[Screen]) -> FlowSequence` — Order screens temporally
- `calculate_screen_similarity(s1: Screen, s2: Screen) -> float` — Compare screens
- `detect_key_frames(screens: list[Screen]) -> list[Screen]` — Find significant changes
- `deduplicate_frames(screens: list[Screen], threshold: float) -> list[Screen]` — Remove duplicates

### 3. Hierarchy Models (`src/vision/hierarchy_models.py`)

Pydantic models for hierarchy:
- `HierarchyNode` — Component with children reference
- `HierarchyTree` — Root node with full tree structure
- `ContainerMatch` — Parent-child relationship with confidence
- `ZLayer` — Layer info with component IDs
- `NestingLevel` — Depth and container info

### 4. Flow Models (`src/vision/flow_models.py`)

Pydantic models for flow:
- `FlowSequence` — Ordered screens with transition metadata
- `ScreenTransition` — Transition between two screens
- `SimilarityScore` — Screen comparison result
- `KeyFrameMarker` — Key frame indicator with reason

### 5. Database Integration

Update existing entities:
- Store hierarchy in `Screen.hierarchy` JSON field
- Update `Flow.metadata` with sequence information
- Create component relationships in database
- Track frame similarity scores

---

## Technical Decisions

### Hierarchy Representation Format
- **Decision:** Nested JSON structure in `Screen.hierarchy` field
- **Rationale:**
  - Matches existing schema design
  - Easy to query and traverse
  - Supports arbitrary depth
  - Compatible with API responses
- **Format:**
  ```json
  {
    "root_id": "component-uuid",
    "nodes": {
      "component-uuid": {
        "parent_id": "parent-uuid | null",
        "children": ["child-uuid-1", "child-uuid-2"],
        "z_index": 0,
        "level": 0
      }
    }
  }
  ```

### Container Detection Algorithm
- **Decision:** Bounding box containment + area ratio threshold
- **Rationale:**
  - Simple, deterministic algorithm
  - O(n²) is acceptable for typical component counts (10-50)
  - Area ratio prevents false positives (large containers)
  - Can be enhanced with ML later if needed
- **Algorithm:**
  ```
  For each component A:
    For each component B:
      If A.bbox contains B.bbox:
        If (B.area / A.area) > 0.1:  # B is meaningfully inside A
          A is potential parent of B
  Resolve conflicts (multiple parents) by:
    - Smallest containing parent wins
  ```

### Frame Similarity Detection
- **Decision:** Perceptual hashing (pHash) + component overlap comparison
- **Rationale:**
  - pHash is fast and robust to minor pixel changes
  - Component overlap catches structural similarity
  - Combined score provides reliable similarity measure
  - Threshold configurable (default 0.95 for deduplication)

### Z-Order Inference
- **Decision:** Position heuristics + size heuristics
- **Rationale:**
  - True z-order requires render engine access
  - Heuristics provide reasonable approximation:
    - Larger components → lower z-index (background)
    - Centered components → higher z-index (modals/overlays)
    - Overlapping detection + visual importance
  - Flag uncertain cases for human review

### Flow Sequencing
- **Decision:** Use existing frame extraction order + similarity validation
- **Rationale:**
  - Frames already sequenced by time (from M1-2)
  - Similarity detection identifies:
    - Duplicate frames (no UI change)
    - Key frames (significant UI change)
    - Transition points (navigation, modals)
  - Store transitions in Flow metadata

---

## File Structure

```
src/
└── vision/
    ├── __init__.py            # Update exports
    ├── hierarchy.py           # Hierarchy extraction
    ├── hierarchy_models.py    # Hierarchy Pydantic models
    ├── flow.py                # Flow sequencing
    ├── flow_models.py         # Flow Pydantic models
    └── similarity.py          # Screen similarity utilities
tests/
└── unit/
    ├── test_hierarchy.py      # Hierarchy unit tests
    └── test_flow.py           # Flow unit tests
```

---

## Tasks

### Phase 1: Foundation & Models
- [ ] Create `src/vision/hierarchy_models.py` with Pydantic models
- [ ] Create `src/vision/flow_models.py` with Pydantic models
- [ ] Add `imagehash` to requirements.txt for perceptual hashing
- [ ] Update `src/vision/__init__.py` with new exports

### Phase 2: Hierarchy Extraction
- [ ] Create `src/vision/hierarchy.py`
- [ ] Implement `detect_containers()` - bounding box containment
- [ ] Implement `infer_z_order()` - position and size heuristics
- [ ] Implement `extract_hierarchy()` - build tree structure
- [ ] Implement `calculate_nesting_depth()` - depth analysis
- [ ] Handle edge cases (overlapping siblings, orphan components)
- [ ] Write unit tests for hierarchy extraction

### Phase 3: Screen Similarity
- [ ] Create `src/vision/similarity.py`
- [ ] Implement perceptual hash calculation (pHash)
- [ ] Implement component overlap comparison
- [ ] Implement combined similarity score
- [ ] Make similarity threshold configurable
- [ ] Write unit tests for similarity functions

### Phase 4: Flow Sequencing
- [ ] Create `src/vision/flow.py`
- [ ] Implement `calculate_screen_similarity()` using similarity module
- [ ] Implement `detect_key_frames()` - identify significant changes
- [ ] Implement `deduplicate_frames()` - remove near-duplicates
- [ ] Implement `sequence_screens()` - validate and enrich order
- [ ] Generate transition metadata between screens
- [ ] Write unit tests for flow sequencing

### Phase 5: Database Integration
- [ ] Update `Screen.hierarchy` JSON field with extracted hierarchy
- [ ] Update `Flow.metadata` with sequence and transition info
- [ ] Add key frame markers to flow metadata
- [ ] Store similarity scores for audit trail
- [ ] Write integration tests for database operations

### Phase 6: Testing & Validation
- [ ] Create test fixtures (screens with known hierarchies)
- [ ] Create test fixtures (video frame sequences)
- [ ] Write comprehensive unit tests (>90% coverage)
- [ ] Test hierarchy edge cases (deep nesting, no nesting)
- [ ] Test flow edge cases (single frame, all duplicates)
- [ ] Validate hierarchy accuracy against manual annotations
- [ ] Run full test suite and verify no regressions

---

## Success Criteria

- [ ] Hierarchy extraction produces valid nested structures
- [ ] Container detection accuracy > 90% on test fixtures
- [ ] Z-order inference reasonable for typical UI layouts
- [ ] Frame similarity detection identifies duplicates (>95% accuracy)
- [ ] Key frame detection identifies significant UI changes
- [ ] Flow sequencing preserves temporal order correctly
- [ ] All data persisted correctly to database
- [ ] Hierarchy analysis time < 500ms per screen
- [ ] Flow analysis time < 2s per 100 frames
- [ ] Unit test coverage > 90% for new modules
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Complex nesting patterns misidentified | Flag low-confidence relationships for review |
| Z-order inference inaccurate | Document limitations, prioritize for ML enhancement |
| Similarity threshold too aggressive | Make configurable, log all scores for tuning |
| Deep hierarchies cause performance issues | Limit nesting depth, flatten beyond threshold |
| Frame order lost during processing | Preserve original timestamps, validate order |

---

## Validation

Run after completion:
```bash
# Run unit tests for hierarchy module
python -m pytest tests/unit/test_hierarchy.py -v

# Run unit tests for flow module
python -m pytest tests/unit/test_flow.py -v

# Run full test suite
python -m pytest tests/ -v

# Test hierarchy extraction manually
python -c "
from src.vision.hierarchy import HierarchyAnalyzer
from src.vision.models import DetectedComponent, BoundingBox

# Create test components
components = [
    DetectedComponent(type='container', bbox=BoundingBox(x=0, y=0, width=1, height=1), confidence=0.9),
    DetectedComponent(type='button', bbox=BoundingBox(x=0.1, y=0.1, width=0.2, height=0.1), confidence=0.95),
]
analyzer = HierarchyAnalyzer()
tree = analyzer.extract_hierarchy(components)
print(f'Root: {tree.root_id}')
print(f'Depth: {analyzer.calculate_nesting_depth(tree)}')
"

# Check coverage
python -m pytest tests/unit/test_hierarchy.py tests/unit/test_flow.py --cov=src/vision --cov-report=term-missing
```

---

## Dependencies

### Python Dependencies
- `imagehash>=4.3.1` — Perceptual hashing for similarity detection
- `Pillow` — Already installed (M1-1)

### Internal Dependencies
- `src/vision/models.py` — Component models from M2-1
- `src/db/crud.py` — Database operations
- `src/db/models.py` — Screen and Flow entities

---

*Created: 2026-03-02*