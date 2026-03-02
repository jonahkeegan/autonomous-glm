# Epic M1-1: Screenshot Ingestion

> **Milestone:** 1 - Input Ingestion Pipeline  
> **Priority:** Critical  
> **Dependencies:** Epic M0-1, Epic M0-2  
> **Status:** ✅ COMPLETE

---

## Objective

Build the foundational artifact ingestion system for screenshot images (PNG, JPEG) with file validation, organized storage, and database tracking using the existing `Screen` entity.

---

## Scope

### In Scope
- File handlers for PNG and JPEG formats
- Magic byte validation for file type verification
- File size limits and corruption detection
- Organized storage with date-based directory structure
- Ingest ID generation (UUID-based, deterministic hash)
- Database integration using existing `Screen` entity from M0-1
- Unit tests with >90% coverage
- Integration with existing configuration system

### Out of Scope
- Video handling (M1-2)
- API endpoints (M1-3)
- CV/analysis integration (M2)
- Metadata parsing (M1-3)
- Multi-agent communication (M5)

---

## Deliverables

### 1. Screenshot Handler Module (`src/ingest/screenshot.py`)

Core ingestion logic:
- `ingest_screenshot(file_path: str) -> IngestResult` — Main entry point
- `validate_screenshot(file_path: str) -> ValidationResult` — File validation
- `generate_ingest_id(file_path: str) -> str` — Deterministic UUID from content hash
- `store_screenshot(file_path: str, ingest_id: str) -> str` — Returns storage path

### 2. File Validator (`src/ingest/validators.py`)

Validation utilities:
- PNG magic bytes: `\x89PNG\r\n\x1a\n`
- JPEG magic bytes: `\xff\xd8\xff`
- File size limits (configurable, default 50MB max)
- Image dimension validation (min 100x100, max 10000x10000)
- Corruption detection via PIL/Pillow

### 3. Storage Manager (`src/ingest/storage.py`)

Organized file storage:
- Directory structure: `data/artifacts/screenshots/{YYYY}/{MM}/{uuid}.png`
- Atomic file operations (write to temp, then rename)
- Duplicate detection via content hash
- Cleanup utilities for failed ingests

### 4. Database Integration

Uses existing `Screen` entity:
- Create `Screen` record with `image_path` pointing to storage location
- Store `hierarchy` as NULL (populated by M2 CV analysis)
- Link `name` to original filename
- Use existing CRUD from `src/db/crud.py`

### 5. Ingestion Result Model (`src/ingest/models.py`)

Pydantic models for:
- `IngestResult` — Success/failure, ingest_id, screen_id, storage_path
- `ValidationResult` — Valid flag, errors, warnings
- `IngestConfig` — Configurable limits and paths

---

## Technical Decisions

### Storage Path Format
- **Decision:** `data/artifacts/screenshots/{YYYY}/{MM}/{uuid}.{ext}`
- **Rationale:** 
  - Date-based folders prevent single-directory overflow
  - UUID filename prevents collisions
  - Original extension preserved for format detection

### Ingest ID Generation
- **Decision:** SHA-256 hash of file content → UUID v5
- **Rationale:** 
  - Deterministic: same file = same ID
  - Enables duplicate detection
  - Content-addressable for future deduplication

### Image Library
- **Decision:** Use Pillow (PIL) for image validation
- **Rationale:** 
  - Battle-tested, pure Python with C extensions
  - Already commonly available
  - Handles PNG/JPEG validation reliably

### Duplicate Handling
- **Decision:** Return existing ingest_id for duplicate files
- **Rationale:** 
  - Idempotent ingestion
  - Prevents storage waste
  - Consistent with content-addressable pattern

---

## File Structure

```
src/
└── ingest/
    ├── __init__.py
    ├── screenshot.py      # Main ingestion logic
    ├── validators.py      # File validation utilities
    ├── storage.py         # Storage management
    └── models.py          # Pydantic models for ingestion
tests/
└── unit/
    └── test_screenshot_ingest.py  # Unit tests
```

---

## Tasks

### Phase 1: Foundation & Models
- [ ] Create `src/ingest/` directory structure
- [ ] Create `src/ingest/__init__.py` with module exports
- [ ] Create `src/ingest/models.py` with Pydantic models (IngestResult, ValidationResult, IngestConfig)
- [ ] Add Pillow to requirements.txt
- [ ] Add ingestion config section to `config/default.yaml`

### Phase 2: File Validation
- [ ] Create `src/ingest/validators.py`
- [ ] Implement magic byte validation for PNG
- [ ] Implement magic byte validation for JPEG
- [ ] Implement file size validation (configurable limits)
- [ ] Implement image dimension validation via Pillow
- [ ] Implement corruption detection (attempt to load image)
- [ ] Write unit tests for validators

### Phase 3: Storage Management
- [ ] Create `src/ingest/storage.py`
- [ ] Implement date-based directory creation
- [ ] Implement atomic file copy (temp → final location)
- [ ] Implement content hash calculation (SHA-256)
- [ ] Implement duplicate detection via hash lookup
- [ ] Write unit tests for storage manager

### Phase 4: Screenshot Handler Integration
- [ ] Create `src/ingest/screenshot.py`
- [ ] Implement `generate_ingest_id()` with content hash
- [ ] Implement `validate_screenshot()` using validators
- [ ] Implement `store_screenshot()` using storage manager
- [ ] Implement `ingest_screenshot()` as main entry point
- [ ] Integrate with existing `Screen` CRUD operations
- [ ] Write unit tests for screenshot handler

### Phase 5: Configuration Integration
- [ ] Add ingestion settings to `src/config/schema.py`
- [ ] Update `config/default.yaml` with ingestion defaults
- [ ] Update `config/development.yaml` with dev settings
- [ ] Ensure paths use configuration (no hardcoded paths)
- [ ] Write tests for configuration integration

### Phase 6: Testing & Validation
- [ ] Create test fixtures (sample PNG, JPEG, corrupt files)
- [ ] Write comprehensive unit tests (>90% coverage target)
- [ ] Test duplicate file handling
- [ ] Test edge cases (empty files, huge files, wrong types)
- [ ] Run full test suite and verify no regressions
- [ ] Update health check script if needed

---

## Success Criteria

- [ ] Screenshots ingest correctly and store in organized structure
- [ ] File validation rejects invalid/corrupt files with clear errors
- [ ] Ingest time < 100ms per screenshot (excluding file copy time)
- [ ] Database records created with correct `Screen` entity
- [ ] Duplicate files return existing ingest_id (idempotent)
- [ ] All paths use configuration (no hardcoded paths)
- [ ] Unit test coverage > 90% for `src/ingest/` module
- [ ] No regressions in existing test suite (233 tests still pass)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large files cause memory issues | Stream file reads, enforce size limits before loading |
| Pillow vulnerability | Pin version in requirements.txt, monitor CVEs |
| Storage directory permissions | Check permissions at startup, clear error messages |
| Hash collisions (theoretical) | SHA-256 has 2^128 collision resistance - negligible risk |

---

## Validation

Run after completion:
```bash
# Run unit tests for ingestion module
python -m pytest tests/unit/test_screenshot_ingest.py -v

# Run full test suite (ensure no regressions)
python -m pytest tests/ -v

# Test ingestion manually
python -c "
from src.ingest.screenshot import ingest_screenshot
result = ingest_screenshot('tests/fixtures/sample.png')
print(f'Ingest ID: {result.ingest_id}')
print(f'Stored at: {result.storage_path}')
"

# Check coverage
python -m pytest tests/unit/test_screenshot_ingest.py --cov=src/ingest --cov-report=term-missing
```

---

*Created: 2026-03-01*