# Epic M3-1: Database Persistence Integration

> **Milestone:** 3 - Audit Engine  
> **Priority:** Critical  
> **Dependencies:** Epic M2-1, Epic M2-2, Epic M2-3  
> **Status:** 🔲 Not Started

---

## Objective

Bridge the gap from M2 by persisting detected Components and extracted Tokens to the database, and create a minimal validation dataset for accuracy verification during audit development.

---

## Scope

### In Scope
- Persist Component entities from M2-1 detection results
- Persist SystemToken entities from M2-3 extraction results
- Update CRUD operations for batch inserts and component-token relationships
- Create minimal validation dataset (5-10 synthetic screenshots with known components)
- Integration tests for persistence layer
- Database migration for any schema updates needed

### Out of Scope
- Audit logic (M3-2)
- New detection or extraction capabilities
- API endpoints for querying persisted data
- Golden dataset creation (M7)

---

## Deliverables

### 1. Component Persistence Module

Update `src/db/crud.py` with:
- `batch_create_components(screen_id: UUID, components: list[DetectedComponent]) -> list[Component]`
- `get_components_by_screen(screen_id: UUID) -> list[Component]`
- `update_component_tokens(component_id: UUID, token_refs: list[str]) -> Component`

### 2. SystemToken Persistence Module

Update `src/db/crud.py` with:
- `batch_create_tokens(tokens: list[DesignToken]) -> list[SystemToken]`
- `get_tokens_by_type(token_type: str) -> list[SystemToken]`
- `get_all_tokens() -> list[SystemToken]`

### 3. Component-Token Relationship

Implement many-to-many join table operations:
- `link_component_token(component_id: UUID, token_id: UUID) -> None`
- `get_component_tokens(component_id: UUID) -> list[SystemToken]`
- `get_token_components(token_id: UUID) -> list[Component]`

### 4. Minimal Validation Dataset

Create synthetic test fixtures in `tests/golden-dataset/validation/`:
- 5-10 UI screenshots with known component layouts
- JSON metadata files with expected components per screenshot
- Known token values (colors, spacing) for verification
- Documented expected findings for accuracy validation

### 5. Integration Tests

Test persistence operations:
- Component batch creation from detection results
- Token batch creation from extraction results
- Component-token linking
- Query operations for audit engine consumption

---

## Technical Decisions

### Persistence Strategy
- **Decision:** Batch inserts with transaction rollback on failure
- **Rationale:** Detection results contain 10-50+ components; atomic batch operations ensure consistency

### Component-Token Relationship
- **Decision:** Many-to-many via `component_tokens` join table (already in schema.sql)
- **Rationale:** One component may use multiple tokens (color + spacing + typography); one token may be used across many components

### Validation Dataset Approach
- **Decision:** Create synthetic UI screenshots with programmatically-known layouts
- **Rationale:**
  - No external dependencies
  - Exact ground truth for validation
  - Can be generated programmatically
  - Extends to golden dataset in M7

### Schema Validation
- **Decision:** Verify existing schema supports persistence before implementation
- **Rationale:** M2 was designed with deferred persistence; ensure schema alignment

---

## File Structure

```
src/
└── db/
    ├── crud.py                  # Updated with batch operations
    └── models.py                # Updated if needed
tests/
├── golden-dataset/
│   └── validation/              # New: minimal validation dataset
│       ├── screenshot_001.png
│       ├── screenshot_001.json  # Expected components
│       ├── screenshot_002.png
│       ├── screenshot_002.json
│       └── ...
└── unit/
    └── test_persistence.py      # New: persistence tests
```

---

## Tasks

### Phase 1: Schema Verification
- [ ] Review existing `src/db/schema.sql` for Component and SystemToken tables
- [ ] Verify `component_tokens` join table exists and is correct
- [ ] Check `src/db/models.py` Pydantic models align with schema
- [ ] Identify any missing fields or constraints
- [ ] Create migration file if schema changes needed

### Phase 2: Component Persistence
- [ ] Add `batch_create_components()` to `src/db/crud.py`
- [ ] Add `get_components_by_screen()` to `src/db/crud.py`
- [ ] Add `update_component_tokens()` to `src/db/crud.py`
- [ ] Add `delete_components_by_screen()` for cleanup
- [ ] Write unit tests for component CRUD operations

### Phase 3: SystemToken Persistence
- [ ] Add `batch_create_tokens()` to `src/db/crud.py`
- [ ] Add `get_tokens_by_type()` to `src/db/crud.py`
- [ ] Add `get_all_tokens()` to `src/db/crud.py`
- [ ] Add `clear_tokens()` for reset operations
- [ ] Write unit tests for token CRUD operations

### Phase 4: Component-Token Relationships
- [ ] Add `link_component_token()` to `src/db/crud.py`
- [ ] Add `get_component_tokens()` to `src/db/crud.py`
- [ ] Add `get_token_components()` to `src/db/crud.py`
- [ ] Add `batch_link_components_tokens()` for efficiency
- [ ] Write unit tests for relationship operations

### Phase 5: Minimal Validation Dataset
- [ ] Create `tests/golden-dataset/validation/` directory
- [ ] Generate 5 synthetic UI screenshots with known layouts
- [ ] Create JSON metadata files with expected components
- [ ] Include known color/spacing values for token validation
- [ ] Document expected findings in README.md

### Phase 6: Integration & Testing
- [ ] Create `tests/unit/test_persistence.py`
- [ ] Test end-to-end: detect → persist → query
- [ ] Test batch operations with rollback scenarios
- [ ] Validate against minimal dataset
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] Components from M2-1 detection persist correctly to database
- [ ] Tokens from M2-3 extraction persist correctly to database
- [ ] Component-token relationships created and queryable
- [ ] Batch operations are atomic (rollback on failure)
- [ ] Minimal validation dataset created with 5+ screenshots
- [ ] All persistence tests passing (>90% coverage for new code)
- [ ] No regressions in existing test suite (508 tests still pass)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Schema mismatch with M2 models | Verify schema before implementation; create migration if needed |
| Batch insert performance | Use SQLite transactions; benchmark with 100+ components |
| Validation dataset too simple | Include variety of layouts, densities, and edge cases |
| Component-token linking complexity | Test many-to-many scenarios thoroughly |

---

## Validation

Run after completion:
```bash
# Verify database schema
sqlite3 data/autonomous_glm.db ".schema components"
sqlite3 data/autonomous_glm.db ".schema system_tokens"
sqlite3 data/autonomous_glm.db ".schema component_tokens"

# Run persistence tests
python -m pytest tests/unit/test_persistence.py -v

# Test component persistence end-to-end
python -c "
from src.vision.client import VisionClient
from src.db.crud import batch_create_components, get_components_by_screen
from src.db.database import get_db_connection

# Detect components
client = VisionClient()
result = client.detect_components('tests/fixtures/sample.png')

# Persist to database
with get_db_connection() as conn:
    components = batch_create_components(conn, screen_id, result.components)
    print(f'Persisted {len(components)} components')
"

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- All M2 dependencies (openai, pillow, scikit-learn, imagehash)
- No new dependencies required

### System Dependencies
- SQLite database (already initialized from M0)
- OPENAI_API_KEY for detection validation

---

*Created: 2026-03-02*