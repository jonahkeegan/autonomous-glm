# Epic M1-2: Video Ingestion

> **Milestone:** 1 - Input Ingestion Pipeline  
> **Priority:** High  
> **Dependencies:** M1-1 (Screenshot Ingestion)  
> **Status:** 🔲 Not Started

---

## Objective

Extend the artifact ingestion system to handle video files (MP4, MOV) with time-based frame extraction, enabling downstream CV analysis of user flow recordings.

---

## Scope

### In Scope
- Video file handlers for MP4 and MOV formats
- Video file validation (container format, codec support)
- Time-based frame extraction at configurable intervals
- Key frame selection and storage as `Screen` entities
- `Flow` entity creation linking extracted frames
- Storage management for extracted frames
- Database integration with existing entities
- Unit tests with >90% coverage

### Out of Scope
- Scene detection algorithms (use time-based extraction only)
- Real-time video processing
- CV/analysis of extracted frames (M2)
- API endpoints (M1-3)
- Audio track processing
- Video transcoding or format conversion

---

## Deliverables

### 1. Video Handler Module (`src/ingest/video.py`)

Core video ingestion logic:
- `ingest_video(file_path: str, config: VideoIngestConfig) -> VideoIngestResult` — Main entry point
- `validate_video(file_path: str) -> ValidationResult` — Video file validation
- `extract_frames(file_path: str, interval: float) -> List[FrameInfo]` — Time-based extraction
- `create_flow(screens: List[Screen], video_path: str) -> Flow` — Flow entity creation

### 2. Frame Extractor (`src/ingest/frames.py`)

Frame extraction utilities:
- Time-based extraction at configurable FPS (default 1 fps)
- Frame metadata capture (timestamp, frame number)
- Temporary frame storage during processing
- Integration with screenshot storage manager for final storage

### 3. Video Validator (`src/ingest/video_validators.py`)

Video-specific validation:
- MP4 container validation (ftyp box detection)
- MOV container validation
- Codec support check (H.264, H.265, VP8, VP9)
- Video duration limits (configurable, default 30 minutes max)
- Resolution limits (matching screenshot limits)
- Corruption detection via header parsing

### 4. Flow Entity Integration

Database integration using existing entities:
- Create `Flow` record linking extracted `Screen` entities
- Store `video_path` reference to original video
- Store extraction metadata in `Flow.metadata` JSON field
- Use existing CRUD from `src/db/crud.py`

### 5. Video Ingestion Models (`src/ingest/video_models.py`)

Pydantic models for:
- `VideoIngestResult` — Success/failure, ingest_id, flow_id, frame_count
- `FrameInfo` — Timestamp, frame_number, temp_path, hash
- `VideoIngestConfig` — Extraction interval, max frames, codec settings

---

## Technical Decisions

### Frame Extraction Library
- **Decision:** Use ffmpeg (via ffmpeg-python wrapper)
- **Rationale:**
  - Industry standard for video processing
  - Supports all common codecs and containers
  - Efficient frame extraction without full decode
  - Well-maintained Python bindings

### Extraction Strategy
- **Decision:** Time-based extraction at configurable intervals (default 1 fps)
- **Rationale:**
  - Simple, predictable, deterministic
  - Sufficient for UI flow analysis
  - Scene detection can be added later without breaking changes
  - Configurable interval allows tuning per use case

### Frame Storage
- **Decision:** Extract frames as PNG, store using existing screenshot storage pattern
- **Rationale:**
  - Reuses M1-1 storage infrastructure
  - PNG preserves quality for CV analysis
  - Consistent with screenshot handling
  - Date-based organization maintained

### Flow Entity Structure
- **Decision:** Store extraction metadata in `Flow.metadata` JSON field
- **Rationale:**
  - Flexible for future metadata additions
  - No schema changes required
  - Tracks: fps, total_frames, extraction_interval, source_duration

### Maximum Frames
- **Decision:** Default limit of 500 frames per video
- **Rationale:**
  - Prevents runaway extraction from long videos
  - 500 frames at 1 fps = 8+ minutes of video
  - Configurable for special cases

---

## File Structure

```
src/
└── ingest/
    ├── __init__.py            # Update exports
    ├── video.py               # Main video ingestion logic
    ├── video_validators.py    # Video-specific validation
    ├── frames.py              # Frame extraction utilities
    └── video_models.py        # Pydantic models for video
tests/
└── unit/
    └── test_video_ingest.py   # Unit tests
```

---

## Tasks

### Phase 1: Foundation & Models
- [ ] Add ffmpeg-python to requirements.txt
- [ ] Create `src/ingest/video_models.py` with Pydantic models
- [ ] Create `src/ingest/video_validators.py` stub
- [ ] Add video ingestion config section to `config/default.yaml`
- [ ] Document ffmpeg system dependency in README/setup docs

### Phase 2: Video Validation
- [ ] Implement MP4 container validation (ftyp box)
- [ ] Implement MOV container validation
- [ ] Implement codec detection (H.264, H.265, VP8, VP9)
- [ ] Implement video duration check
- [ ] Implement resolution validation
- [ ] Implement corruption detection (header parsing)
- [ ] Write unit tests for video validators

### Phase 3: Frame Extraction
- [ ] Create `src/ingest/frames.py`
- [ ] Implement time-based frame extraction using ffmpeg
- [ ] Implement frame metadata capture (timestamp, frame number)
- [ ] Implement temporary frame storage
- [ ] Implement frame hash calculation for deduplication
- [ ] Handle extraction errors gracefully
- [ ] Write unit tests for frame extractor

### Phase 4: Video Handler Integration
- [ ] Create `src/ingest/video.py`
- [ ] Implement `validate_video()` using video validators
- [ ] Implement `extract_frames()` using frame extractor
- [ ] Implement frame storage using existing screenshot patterns
- [ ] Implement `create_flow()` for Flow entity creation
- [ ] Implement `ingest_video()` as main entry point
- [ ] Write unit tests for video handler

### Phase 5: Database Integration
- [ ] Integrate with `Screen` CRUD for extracted frames
- [ ] Integrate with `Flow` CRUD for flow creation
- [ ] Store extraction metadata in `Flow.metadata`
- [ ] Handle transaction rollback on partial failure
- [ ] Write integration tests for database operations

### Phase 6: Configuration & Testing
- [ ] Add video settings to `src/config/schema.py`
- [ ] Update `config/default.yaml` with video defaults
- [ ] Create video test fixtures (short MP4, MOV clips)
- [ ] Write comprehensive unit tests (>90% coverage)
- [ ] Test edge cases (corrupt video, unsupported codec, too long)
- [ ] Test frame deduplication
- [ ] Run full test suite and verify no regressions

---

## Success Criteria

- [ ] Videos ingest and extract frames correctly
- [ ] Frame extraction time < 2s per video segment (10s at 1fps)
- [ ] Extracted frames stored as valid `Screen` entities
- [ ] `Flow` entity correctly links sequential frames
- [ ] Video validation rejects unsupported formats clearly
- [ ] All paths use configuration (no hardcoded paths)
- [ ] Unit test coverage > 90% for video ingestion module
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| ffmpeg not installed | Check at startup, clear error message with install instructions |
| Large videos cause storage issues | Enforce max frames and duration limits |
| Unsupported codec | Validate codec before extraction, clear error message |
| Partial extraction failure | Transaction rollback, cleanup temp files |
| Memory issues with high-res video | Process frames one at a time, don't load all into memory |

---

## Validation

Run after completion:
```bash
# Check ffmpeg availability
ffmpeg -version

# Run unit tests for video ingestion
python -m pytest tests/unit/test_video_ingest.py -v

# Run full test suite
python -m pytest tests/ -v

# Test video ingestion manually
python -c "
from src.ingest.video import ingest_video
from src.ingest.video_models import VideoIngestConfig
config = VideoIngestConfig(extraction_interval=1.0)
result = ingest_video('tests/fixtures/sample.mp4', config)
print(f'Ingest ID: {result.ingest_id}')
print(f'Flow ID: {result.flow_id}')
print(f'Frames extracted: {result.frame_count}')
"

# Check coverage
python -m pytest tests/unit/test_video_ingest.py --cov=src/ingest --cov-report=term-missing
```

---

## Dependencies

### System Dependencies
- **ffmpeg** — Required for video processing
  - macOS: `brew install ffmpeg`
  - Ubuntu: `apt-get install ffmpeg`

### Python Dependencies
- `ffmpeg-python` — Python wrapper for ffmpeg
- `Pillow` — Already added in M1-1

---

*Created: 2026-03-01*