# Epic M1-3: Context Metadata & API Endpoints

> **Milestone:** 1 - Input Ingestion Pipeline  
> **Priority:** High  
> **Dependencies:** Epic M1-1 (Screenshot Ingestion), Epic M1-2 (Video Ingestion)  
> **Status:** ✅ COMPLETE

---

## Objective

Add context metadata parsing capabilities and REST API endpoints that expose the screenshot and video ingestion functionality to other agents and external clients.

---

## Scope

### In Scope
- JSON and YAML context metadata parser
- Metadata association with artifacts (screenshots, videos, flows)
- FastAPI-based REST API with OpenAPI documentation
- Two core endpoints: `POST /ingest/screenshot`, `POST /ingest/video`
- Request/response validation with Pydantic
- Error handling with appropriate HTTP status codes
- API health check endpoint
- Unit and integration tests

### Out of Scope
- Authentication/authorization (local-only initially)
- Rate limiting (not needed for agent use)
- Additional query endpoints (later milestones)
- WebSocket support
- API versioning (single version for now)
- CV/analysis endpoints (M2)

---

## Deliverables

### 1. Context Metadata Parser (`src/ingest/metadata.py`)

Metadata handling:
- `parse_metadata(file_path: str) -> ArtifactMetadata` — Parse JSON/YAML files
- `parse_metadata_dict(data: dict) -> ArtifactMetadata` — Parse from dict
- `associate_metadata(artifact_id: str, metadata: ArtifactMetadata) -> bool` — Link to artifact
- Support for both JSON and YAML formats

### 2. Metadata Models (`src/ingest/metadata_models.py`)

Pydantic models for:
- `ArtifactMetadata` — User-provided context (project, feature, tags, notes)
- `ScreenMetadata` — Screenshot-specific metadata
- `FlowMetadata` — Video/flow-specific metadata
- `MetadataSource` — Origin tracking (file, api, agent)

### 3. FastAPI Application (`src/api/app.py`)

Main API application:
- FastAPI app initialization
- Router registration
- Middleware configuration
- Exception handlers
- CORS configuration for local development

### 4. Ingestion Endpoints (`src/api/routes/ingest.py`)

REST endpoints:
- `POST /ingest/screenshot` — Upload and ingest screenshot
  - Accepts multipart/form-data with file + optional metadata
  - Returns ingest_id, screen_id, status
- `POST /ingest/video` — Upload and ingest video
  - Accepts multipart/form-data with file + optional metadata
  - Returns ingest_id, flow_id, frame_count, status
- `GET /ingest/{ingest_id}` — Query ingest status

### 5. API Models (`src/api/models.py`)

Request/response models:
- `ScreenshotIngestRequest` — Request body for screenshot upload
- `ScreenshotIngestResponse` — Response with ingest results
- `VideoIngestRequest` — Request body for video upload
- `VideoIngestResponse` — Response with ingest results
- `ErrorResponse` — Standardized error responses
- `HealthCheckResponse` — Health check response

### 6. API Configuration (`src/api/config.py`)

API-specific configuration:
- Server host/port settings
- Max upload size limits
- CORS allowed origins
- API metadata (title, description, version)

---

## Technical Decisions

### API Framework
- **Decision:** FastAPI
- **Rationale:**
  - Async support for future scalability
  - Automatic OpenAPI documentation
  - Built-in Pydantic validation
  - Type hints throughout
  - High performance

### Metadata Storage
- **Decision:** Store metadata in artifact entity JSON fields
- **Rationale:**
  - `Screen` and `Flow` entities have metadata JSON fields
  - No schema changes required
  - Flexible for evolving metadata structure

### File Upload Handling
- **Decision:** Use FastAPI's `UploadFile` with temporary file storage
- **Rationale:**
  - Handles multipart/form-data automatically
  - Spools to disk for large files
  - Async-compatible

### Error Response Format
- **Decision:** RFC 7807 Problem Details format
- **Rationale:**
  - Standardized error format
  - Machine-readable
  - Supports extensible details

### API Prefix
- **Decision:** All endpoints under `/api/v1`
- **Rationale:**
  - Future-proof for versioning
  - Clear separation from future non-API routes
  - Standard convention

---

## File Structure

```
src/
├── api/
│   ├── __init__.py
│   ├── app.py              # FastAPI application
│   ├── config.py           # API configuration
│   ├── models.py           # Request/response models
│   ├── exceptions.py       # Custom exceptions
│   └── routes/
│       ├── __init__.py
│       ├── ingest.py       # Ingestion endpoints
│       └── health.py       # Health check endpoint
└── ingest/
    ├── metadata.py         # Metadata parser
    └── metadata_models.py  # Metadata Pydantic models
tests/
└── unit/
    └── test_api.py         # API unit tests
```

---

## Tasks

### Phase 1: API Foundation
- [ ] Add FastAPI and uvicorn to requirements.txt
- [ ] Create `src/api/` directory structure
- [ ] Create `src/api/__init__.py` with exports
- [ ] Create `src/api/config.py` with API settings
- [ ] Add API config section to `config/default.yaml`
- [ ] Create `src/api/exceptions.py` with custom exceptions

### Phase 2: API Models
- [ ] Create `src/api/models.py`
- [ ] Define `ScreenshotIngestRequest` model
- [ ] Define `ScreenshotIngestResponse` model
- [ ] Define `VideoIngestRequest` model
- [ ] Define `VideoIngestResponse` model
- [ ] Define `ErrorResponse` model (RFC 7807)
- [ ] Define `HealthCheckResponse` model

### Phase 3: Metadata Parser
- [ ] Create `src/ingest/metadata_models.py`
- [ ] Define `ArtifactMetadata` model
- [ ] Define `ScreenMetadata` model
- [ ] Define `FlowMetadata` model
- [ ] Create `src/ingest/metadata.py`
- [ ] Implement `parse_metadata()` for JSON files
- [ ] Implement `parse_metadata()` for YAML files
- [ ] Implement `associate_metadata()` for database updates
- [ ] Write unit tests for metadata parser

### Phase 4: Health Endpoint
- [ ] Create `src/api/routes/` directory
- [ ] Create `src/api/routes/health.py`
- [ ] Implement `GET /health` endpoint
- [ ] Check database connectivity
- [ ] Check storage directory accessibility
- [ ] Return detailed health status

### Phase 5: Ingestion Endpoints
- [ ] Create `src/api/routes/ingest.py`
- [ ] Implement `POST /api/v1/ingest/screenshot` endpoint
- [ ] Implement `POST /api/v1/ingest/video` endpoint
- [ ] Implement `GET /api/v1/ingest/{ingest_id}` status endpoint
- [ ] Add file upload validation
- [ ] Add error handling with proper HTTP status codes
- [ ] Integrate with M1-1 screenshot handler
- [ ] Integrate with M1-2 video handler

### Phase 6: FastAPI Application
- [ ] Create `src/api/app.py`
- [ ] Initialize FastAPI application
- [ ] Register routers
- [ ] Configure CORS middleware
- [ ] Add exception handlers
- [ ] Configure OpenAPI metadata
- [ ] Add startup/shutdown events

### Phase 7: Testing & Documentation
- [ ] Create API test fixtures
- [ ] Write unit tests for endpoints using TestClient
- [ ] Write integration tests for full ingest flow
- [ ] Test error scenarios (invalid files, missing files)
- [ ] Verify OpenAPI spec generation
- [ ] Test metadata association
- [ ] Run full test suite and verify no regressions

---

## Success Criteria

- [ ] API starts without errors on configured port
- [ ] `POST /api/v1/ingest/screenshot` accepts and processes screenshots
- [ ] `POST /api/v1/ingest/video` accepts and processes videos
- [ ] Response time < 100ms for API overhead (excluding processing)
- [ ] OpenAPI documentation accessible at `/docs`
- [ ] Metadata correctly associates with artifacts
- [ ] Error responses follow RFC 7807 format
- [ ] Health check endpoint reports system status
- [ ] Unit test coverage > 90% for API module
- [ ] No regressions in existing test suite

---

## API Specification

### POST /api/v1/ingest/screenshot

**Request:**
```
POST /api/v1/ingest/screenshot
Content-Type: multipart/form-data

file: <binary>
metadata: <json> (optional)
```

**Response (201 Created):**
```json
{
  "ingest_id": "uuid",
  "screen_id": "uuid",
  "status": "success",
  "storage_path": "data/artifacts/screenshots/2026/03/uuid.png",
  "duplicate": false
}
```

**Response (200 OK - Duplicate):**
```json
{
  "ingest_id": "uuid",
  "screen_id": "uuid",
  "status": "duplicate",
  "storage_path": "data/artifacts/screenshots/2026/03/uuid.png",
  "duplicate": true
}
```

### POST /api/v1/ingest/video

**Request:**
```
POST /api/v1/ingest/video
Content-Type: multipart/form-data

file: <binary>
metadata: <json> (optional)
extraction_interval: <float> (optional, default 1.0)
```

**Response (201 Created):**
```json
{
  "ingest_id": "uuid",
  "flow_id": "uuid",
  "status": "success",
  "frame_count": 30,
  "storage_path": "data/artifacts/videos/2026/03/"
}
```

### GET /api/v1/ingest/{ingest_id}

**Response (200 OK):**
```json
{
  "ingest_id": "uuid",
  "artifact_type": "screenshot|video",
  "status": "success|processing|failed",
  "created_at": "2026-03-01T12:00:00Z",
  "artifact_id": "uuid"
}
```

### GET /health

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "checks": {
    "database": "ok",
    "storage": "ok",
    "ffmpeg": "ok"
  }
}
```

### Error Response Format (RFC 7807)

```json
{
  "type": "https://autonomous-glm.local/errors/validation",
  "title": "Validation Error",
  "status": 400,
  "detail": "Invalid file format. Expected PNG or JPEG.",
  "instance": "/api/v1/ingest/screenshot"
}
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large file uploads timeout | Configure appropriate timeout, document limits |
| Memory issues with concurrent uploads | Limit concurrent uploads, use streaming |
| Invalid metadata format | Strict Pydantic validation, clear error messages |
| API changes break clients | Version API from start (/api/v1/) |

---

## Validation

Run after completion:
```bash
# Start API server
uvicorn src.api.app:app --reload --port 8000

# Check OpenAPI docs
open http://localhost:8000/docs

# Test health endpoint
curl http://localhost:8000/health

# Test screenshot ingestion
curl -X POST http://localhost:8000/api/v1/ingest/screenshot \
  -F "file=@tests/fixtures/sample.png"

# Test video ingestion
curl -X POST http://localhost:8000/api/v1/ingest/video \
  -F "file=@tests/fixtures/sample.mp4"

# Run API tests
python -m pytest tests/unit/test_api.py -v

# Run full test suite
python -m pytest tests/ -v

# Check coverage
python -m pytest tests/unit/test_api.py --cov=src/api --cov-report=term-missing
```

---

## Dependencies

### Python Dependencies
- `fastapi` — Web framework
- `uvicorn` — ASGI server
- `python-multipart` — Multipart form data parsing
- `pyyaml` — YAML metadata parsing (already in project)

---

*Created: 2026-03-01*