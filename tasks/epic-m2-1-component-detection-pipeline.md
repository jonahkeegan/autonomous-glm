# Epic M2-1: Component Detection Pipeline

> **Milestone:** 2 - CV/AI Analysis Core  
> **Priority:** Critical  
> **Dependencies:** Epic M1-1, Epic M1-2  
> **Status:** ✅ Complete

---

## Objective

Build the core CV pipeline that detects UI components in screenshots using GPT-4 Vision API with component.gallery few-shot prompting, classifies their types, and persists results to the database.

---

## Scope

### In Scope
- GPT-4 Vision API integration architecture
- component.gallery integration for few-shot prompt examples
- Component detection with bounding boxes
- Element type classification (button, input, modal, label, icon, image, text, container, card, navigation)
- Component entity persistence to database
- API client with retry and error handling
- Configuration for API keys and endpoints
- Minimal test fixtures for validation
- Rate limiting and cost tracking

### Out of Scope
- Hierarchy extraction (M2-2)
- Token extraction (M2-3)
- Golden dataset creation (M7)
- Full audit protocol (M3)
- Fine-tuned local model (future optimization)
- Real-time detection (video frame-by-frame is sufficient)

---

## Deliverables

### 1. Vision Client Module (`src/vision/client.py`)

GPT-4 Vision API client:
- `VisionClient` — API client with async support
- `detect_components(image_path: str) -> DetectionResult` — Main detection method
- `build_prompt(include_examples: bool) -> list` — Construct few-shot prompts
- `parse_response(response: dict) -> list[Component]` — Parse API response to components

### 2. Component Gallery Integration (`src/vision/gallery.py`)

Few-shot example management:
- `GalleryExample` — Pydantic model for example data
- `load_examples(category: str, count: int) -> list[GalleryExample]` — Load examples by type
- `format_examples_as_prompt(examples: list) -> str` — Format for API prompt
- Example storage in `data/component-gallery/` (downloaded from component.gallery)

### 3. Detection Models (`src/vision/models.py`)

Pydantic models for detection:
- `BoundingBox` — {x, y, width, height} normalized coordinates
- `DetectedComponent` — type, bbox, confidence, label
- `DetectionResult` — components list, image_id, processing_time
- `ComponentType` — Enum of supported component types

### 4. Component Persistence

Database integration using existing `Component` entity:
- Create `Component` records with bounding boxes
- Link to `Screen` entity via `screen_id`
- Store `token_refs` as empty (populated by M2-3)
- Use existing CRUD from `src/db/crud.py`

### 5. Configuration

Add to existing config system:
- `OPENAI_API_KEY` environment variable
- `vision.gpt4_model` — Model version (default: gpt-4o)
- `vision.max_tokens` — Response token limit
- `vision.temperature` — Sampling temperature
- `vision.rate_limit` — Requests per minute limit

---

## Technical Decisions

### CV Model Selection
- **Decision:** GPT-4 Vision API (gpt-4o)
- **Rationale:**
  - >95% accuracy on UI component detection tasks
  - Structured JSON output support
  - No training infrastructure required
  - Fast time-to-value (hours not weeks)
  - Reversible: architecture supports future model swapping

### Few-Shot Prompting Strategy
- **Decision:** Use component.gallery examples in system prompt
- **Rationale:**
  - component.gallery has 1000+ labeled UI components
  - Few-shot examples improve accuracy and consistency
  - Establishes component type taxonomy alignment
  - Reduces ambiguity in classification

### Bounding Box Format
- **Decision:** Normalized coordinates (0.0-1.0) relative to image dimensions
- **Rationale:**
  - Resolution-independent
  - Easier to scale and compare
  - Standard format for CV applications
  - Convert to absolute for storage/display

### Cost Management
- **Decision:** Implement rate limiting and cost tracking
- **Rationale:**
  - GPT-4 Vision costs ~$0.01-0.03 per image
  - Track usage per screen/flow
  - Configurable rate limits prevent runaway costs
  - Log all API calls for auditing

### Error Handling
- **Decision:** Exponential backoff with 3 retries
- **Rationale:**
  - API rate limits may be hit
  - Transient failures should be handled gracefully
  - Log failures for debugging
  - Partial results better than complete failure

---

## File Structure

```
src/
└── vision/
    ├── __init__.py           # Module exports
    ├── client.py             # GPT-4 Vision API client
    ├── gallery.py            # component.gallery integration
    ├── models.py             # Detection Pydantic models
    └── prompts.py            # Prompt templates
data/
└── component-gallery/        # Downloaded few-shot examples
    ├── buttons/              # Button examples
    ├── inputs/               # Input examples
    ├── cards/                # Card examples
    └── ...                   # Other component types
tests/
└── unit/
    └── test_vision_client.py # Unit tests
config/
└── default.yaml              # Updated with vision config
```

---

## Tasks

### Phase 1: Foundation & Configuration
- [ ] Create `src/vision/` directory structure
- [ ] Create `src/vision/__init__.py` with module exports
- [ ] Create `src/vision/models.py` with Pydantic models (BoundingBox, DetectedComponent, DetectionResult, ComponentType)
- [ ] Add openai to requirements.txt
- [ ] Add vision configuration section to `config/default.yaml`
- [ ] Add `VisionConfig` to `src/config/schema.py`
- [ ] Document OPENAI_API_KEY requirement in setup docs

### Phase 2: Prompt Engineering
- [ ] Create `src/vision/prompts.py` with prompt templates
- [ ] Design system prompt for UI component detection
- [ ] Define component type taxonomy (button, input, modal, etc.)
- [ ] Create output format specification (JSON schema)
- [ ] Write unit tests for prompt construction

### Phase 3: Component Gallery Integration
- [ ] Create `data/component-gallery/` directory structure
- [ ] Download representative examples from component.gallery (10 per type)
- [ ] Create `src/vision/gallery.py` for example management
- [ ] Implement `load_examples()` function
- [ ] Implement `format_examples_as_prompt()` function
- [ ] Write unit tests for gallery module

### Phase 4: Vision API Client
- [ ] Create `src/vision/client.py`
- [ ] Implement `VisionClient` class with async support
- [ ] Implement `detect_components()` main method
- [ ] Implement response parsing to `DetectedComponent` list
- [ ] Add retry logic with exponential backoff
- [ ] Add rate limiting (requests per minute)
- [ ] Add cost tracking/logging
- [ ] Write unit tests with mocked API responses

### Phase 5: Database Integration
- [ ] Integrate with existing `Component` CRUD
- [ ] Implement component persistence from detection results
- [ ] Convert normalized bboxes to absolute coordinates for storage
- [ ] Handle batch component creation
- [ ] Write integration tests for database operations

### Phase 6: Testing & Validation
- [ ] Create test fixtures (sample screenshots with known components)
- [ ] Write comprehensive unit tests (>90% coverage target)
- [ ] Test error handling (API failures, rate limits, malformed responses)
- [ ] Test edge cases (empty screens, dense screens, unusual layouts)
- [ ] Validate detection accuracy against manual annotations
- [ ] Run full test suite and verify no regressions

---

## Success Criteria

- [ ] Component detection accuracy > 95% on test fixtures
- [ ] Detection time < 1s per screenshot (API response time)
- [ ] All 10 component types correctly classified
- [ ] Bounding boxes accurately represent component positions
- [ ] Components persisted correctly to database
- [ ] Rate limiting prevents API quota exhaustion
- [ ] Cost tracking logs all API usage
- [ ] Unit test coverage > 90% for `src/vision/` module
- [ ] No regressions in existing test suite (361 tests still pass)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| OpenAI API downtime | Implement fallback/error handling, log failures, manual retry |
| Rate limit exceeded | Configurable rate limits, exponential backoff, queue system |
| High API costs | Track costs per screen, set daily limits, log all usage |
| Detection accuracy below target | Tune prompts, add more few-shot examples, validate on golden dataset |
| API response format changes | Version pin model, validate response schema, defensive parsing |
| component.gallery unavailable | Cache examples locally, version control the gallery data |

---

## Validation

Run after completion:
```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Run unit tests for vision module
python -m pytest tests/unit/test_vision_client.py -v

# Run full test suite (ensure no regressions)
python -m pytest tests/ -v

# Test detection manually
python -c "
from src.vision.client import VisionClient
client = VisionClient()
result = client.detect_components('tests/fixtures/sample.png')
print(f'Detected {len(result.components)} components')
for c in result.components:
    print(f'  - {c.type}: {c.confidence:.2f}')
"

# Check coverage
python -m pytest tests/unit/test_vision_client.py --cov=src/vision --cov-report=term-missing
```

---

## Dependencies

### Python Dependencies
- `openai>=1.0.0` — OpenAI API client
- `httpx` — Async HTTP client (already in openai deps)

### System Dependencies
- **OPENAI_API_KEY** — Required for API access
  - Get from: https://platform.openai.com/api-keys
  - Set via: `export OPENAI_API_KEY="sk-..."`

### External Resources
- **component.gallery** — Few-shot example source
  - URL: https://component.gallery/
  - Download examples for: buttons, inputs, cards, modals, navigation, etc.

---

## Cost Estimates

| Usage Level | Images | Estimated Cost |
|-------------|--------|----------------|
| Development | 100 | ~$1-3 |
| Testing | 500 | ~$5-15 |
| Light Production (monthly) | 5,000 | ~$50-150 |

---

*Created: 2026-03-02*