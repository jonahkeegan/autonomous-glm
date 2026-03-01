# Epic M0-1: Database Schema & Data Layer

> **Milestone:** 0 - Foundation  
> **Priority:** Critical  
> **Dependencies:** None  
> **Status:** 🔲 Not Started

---

## Objective

Implement the SQLite database schema and data access layer for all core entities, establishing the persistence foundation for the Autonomous UI/UX Design Agent.

---

## Scope

### In Scope
- SQLite database file creation and initialization
- Schema definition for all 6 entities from PRD data model
- Basic CRUD operations via data access layer
- Idempotent migration support
- Foreign key relationship enforcement

### Out of Scope
- API endpoints (M1)
- CV/AI integration (M2)
- Complex queries for audit operations (M3)

---

## Data Model Reference

From `autonomous-glm-prd.md`:

```
Screen
  - id: UUID (PK)
  - name: string (not null)
  - image_path: string (not null)
  - hierarchy: JSON (optional)
  - created_at: datetime

Flow
  - id: UUID (PK)
  - name: string (not null)
  - screens: [Screen] (1-N)
  - video_path: string (optional)
  - metadata: JSON

Component
  - id: UUID (PK)
  - screen_id: UUID (FK)
  - type: string (button, input, modal, etc.)
  - bounding_box: JSON {x, y, w, h}
  - token_refs: [SystemToken]
  - created_at: datetime

AuditFinding
  - id: UUID (PK)
  - entity_type: string (Screen, Flow, Component)
  - entity_id: UUID (FK)
  - issue: string
  - rationale: string
  - severity: enum (low, medium, high, critical)
  - related_standard: string
  - created_at: datetime

PlanPhase
  - id: UUID (PK)
  - audit_id: UUID (FK)
  - sequence: int
  - actions: JSON [{description, target_entity, fix, rationale}]
  - status: enum (proposed, in-progress, complete)
  - created_at: datetime

SystemToken
  - id: UUID (PK)
  - name: string
  - type: enum (color, spacing, typography, etc.)
  - value: string
  - used_in: [Component]
```

---

## Deliverables

### 1. Database Schema (`src/db/schema.sql`)

Create SQL schema with:
- All 6 entity tables
- Proper foreign key constraints
- Indexes for common query patterns
- JSON columns for flexible data (hierarchy, metadata, actions)
- Enum tables for severity, status, token types

### 2. Database Module (`src/db/database.py`)

Python module providing:
- `init_database()` — Initialize database with schema
- `get_connection()` — Context manager for database connections
- `reset_database()` — Drop and recreate all tables (dev utility)

### 3. Entity Models (`src/db/models.py`)

Dataclasses or Pydantic models for:
- `Screen` entity
- `Flow` entity
- `Component` entity
- `AuditFinding` entity
- `PlanPhase` entity
- `SystemToken` entity

### 4. Data Access Layer (`src/db/crud.py`)

CRUD operations for each entity:
- `create_*()` — Insert new records
- `get_*()` — Retrieve by ID
- `list_*()` — List with optional filters
- `update_*()` — Update existing records
- `delete_*()` — Remove records

### 5. Migration Support (`src/db/migrations/`)

Simple migration system:
- Version tracking table
- Migration files with up/down SQL
- `run_migrations()` function

---

## Technical Decisions

### Database Location
- **Decision:** Store database at `/data/autonomous_glm.db`
- **Rationale:** Colocated with artifact data, easy backup/restore

### UUID Generation
- **Decision:** Use Python `uuid.uuid4()` for ID generation
- **Rationale:** No coordination needed, works with distributed scenarios

### JSON Handling
- **Decision:** Use SQLite's JSON1 extension for JSON columns
- **Rationale:** Native JSON support, queryable if needed

### ORM vs Raw SQL
- **Decision:** Start with raw SQL + dataclasses
- **Rationale:** Simpler, fewer dependencies, can add ORM later if needed

---

## File Structure

```
src/
└── db/
    ├── __init__.py
    ├── schema.sql
    ├── database.py
    ├── models.py
    ├── crud.py
    └── migrations/
        ├── __init__.py
        ├── 001_initial.sql
        └── tracker.py
data/
└── autonomous_glm.db (created at runtime)
```

---

## Tasks

### Phase 1: Schema Definition
- [ ] Create `src/db/` directory structure
- [ ] Write `schema.sql` with all entity tables
- [ ] Add foreign key constraints and indexes
- [ ] Create initial migration file `001_initial.sql`

### Phase 2: Database Connection
- [ ] Implement `database.py` with connection management
- [ ] Add `init_database()` function
- [ ] Add `reset_database()` function for development
- [ ] Test database creation from scratch

### Phase 3: Entity Models
- [ ] Create `models.py` with dataclasses for all entities
- [ ] Add type hints for all fields
- [ ] Add `to_dict()` and `from_dict()` methods for serialization

### Phase 4: CRUD Operations
- [ ] Implement `crud.py` with basic operations
- [ ] Create operations for all 6 entities
- [ ] Read operations (get by ID, list all)
- [ ] Update and delete operations

### Phase 5: Migration System
- [ ] Implement migration tracker table
- [ ] Create `run_migrations()` function
- [ ] Test migration from empty database

---

## Success Criteria

- [ ] Database initializes without errors
- [ ] All 6 entity tables created with correct schema
- [ ] Foreign key relationships enforced
- [ ] CRUD operations work for all entities
- [ ] Migrations run idempotently
- [ ] No hardcoded paths (uses configuration)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Schema changes break existing data | Migration system supports versioned changes |
| JSON column queries needed later | SQLite JSON1 extension supports querying |
| Performance issues with large datasets | Indexes on foreign keys and common queries |

---

## Validation

Run after completion:
```bash
# Initialize database
python -c "from src.db.database import init_database; init_database()"

# Verify tables created
sqlite3 data/autonomous_glm.db ".tables"

# Test CRUD operations
python -m pytest tests/unit/test_database.py -v
```

---

*Created: 2026-02-28*