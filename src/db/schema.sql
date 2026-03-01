-- Autonomous-GLM Database Schema
-- Version: 1.0
-- Created: 2026-02-28
-- Description: SQLite schema for UI/UX Design Agent data model

-- Enable foreign key support (must be enabled per-connection)
PRAGMA foreign_keys = ON;

-- =============================================================================
-- ENUM TABLES
-- =============================================================================

-- Severity levels for audit findings
CREATE TABLE IF NOT EXISTS severity_levels (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

INSERT OR IGNORE INTO severity_levels (id, name, description) VALUES
    (1, 'low', 'Minor issue, cosmetic or polish-level'),
    (2, 'medium', 'Noticeable issue, affects user experience'),
    (3, 'high', 'Significant issue, impacts usability'),
    (4, 'critical', 'Severe issue, blocks user tasks or accessibility');

-- Phase statuses for plan phases
CREATE TABLE IF NOT EXISTS phase_statuses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

INSERT OR IGNORE INTO phase_statuses (id, name, description) VALUES
    (1, 'proposed', 'Phase proposed, awaiting approval'),
    (2, 'in-progress', 'Phase actively being implemented'),
    (3, 'complete', 'Phase implementation finished');

-- Token types for system tokens
CREATE TABLE IF NOT EXISTS token_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

INSERT OR IGNORE INTO token_types (id, name, description) VALUES
    (1, 'color', 'Color tokens (primary, secondary, etc.)'),
    (2, 'spacing', 'Spacing tokens (margins, padding, gaps)'),
    (3, 'typography', 'Typography tokens (font-family, size, weight)'),
    (4, 'border', 'Border tokens (radius, width)'),
    (5, 'shadow', 'Shadow tokens (elevation, depth)'),
    (6, 'animation', 'Animation tokens (duration, easing)');

-- =============================================================================
-- ENTITY TABLES
-- =============================================================================

-- Screens: Captured screens with hierarchy and layout data
CREATE TABLE IF NOT EXISTS screens (
    id TEXT PRIMARY KEY,              -- UUID as string
    name TEXT NOT NULL,
    image_path TEXT NOT NULL,
    hierarchy TEXT,                   -- JSON: nested structure of components
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    CONSTRAINT valid_image_path CHECK (length(image_path) > 0)
);

-- Flows: Sequence of screens representing an activity
CREATE TABLE IF NOT EXISTS flows (
    id TEXT PRIMARY KEY,              -- UUID as string
    name TEXT NOT NULL,
    video_path TEXT,                  -- Optional: path to source video
    metadata TEXT,                    -- JSON: additional flow metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    CONSTRAINT valid_name CHECK (length(name) > 0)
);

-- Flow-Screens junction table (ordered many-to-many)
CREATE TABLE IF NOT EXISTS flow_screens (
    flow_id TEXT NOT NULL,
    screen_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,        -- Order of screen in flow
    
    PRIMARY KEY (flow_id, screen_id, sequence),
    FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE,
    FOREIGN KEY (screen_id) REFERENCES screens(id) ON DELETE CASCADE
);

-- Components: Parsed UI elements with bounding boxes
CREATE TABLE IF NOT EXISTS components (
    id TEXT PRIMARY KEY,              -- UUID as string
    screen_id TEXT NOT NULL,
    type TEXT NOT NULL,               -- button, input, modal, text, icon, etc.
    bounding_box TEXT NOT NULL,       -- JSON: {x, y, width, height}
    properties TEXT,                  -- JSON: additional component properties
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (screen_id) REFERENCES screens(id) ON DELETE CASCADE,
    CONSTRAINT valid_type CHECK (length(type) > 0)
);

-- System Tokens: Design system variables
CREATE TABLE IF NOT EXISTS system_tokens (
    id TEXT PRIMARY KEY,              -- UUID as string
    name TEXT NOT NULL,
    type_id INTEGER NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (type_id) REFERENCES token_types(id),
    CONSTRAINT unique_token_name UNIQUE (name, type_id)
);

-- Component-Tokens junction table (many-to-many)
CREATE TABLE IF NOT EXISTS component_tokens (
    component_id TEXT NOT NULL,
    token_id TEXT NOT NULL,
    
    PRIMARY KEY (component_id, token_id),
    FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE,
    FOREIGN KEY (token_id) REFERENCES system_tokens(id) ON DELETE CASCADE
);

-- Audit Findings: Issues detected during audit
CREATE TABLE IF NOT EXISTS audit_findings (
    id TEXT PRIMARY KEY,              -- UUID as string
    entity_type TEXT NOT NULL,        -- 'Screen', 'Flow', or 'Component'
    entity_id TEXT NOT NULL,          -- FK to relevant entity
    issue TEXT NOT NULL,
    rationale TEXT,
    severity_id INTEGER NOT NULL DEFAULT 2,
    related_standard TEXT,            -- Reference to design system or WCAG
    metadata TEXT,                    -- JSON: additional finding metadata
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    
    FOREIGN KEY (severity_id) REFERENCES severity_levels(id),
    CONSTRAINT valid_entity_type CHECK (entity_type IN ('Screen', 'Flow', 'Component'))
);

-- Plan Phases: Phased improvement plans
CREATE TABLE IF NOT EXISTS plan_phases (
    id TEXT PRIMARY KEY,              -- UUID as string
    audit_id TEXT,                    -- Optional link to audit finding
    phase_name TEXT NOT NULL,         -- 'Critical', 'Refinement', 'Polish'
    sequence INTEGER NOT NULL,
    actions TEXT NOT NULL,            -- JSON array: [{description, target_entity, fix, rationale}]
    status_id INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    
    FOREIGN KEY (status_id) REFERENCES phase_statuses(id),
    CONSTRAINT valid_phase_name CHECK (phase_name IN ('Critical', 'Refinement', 'Polish'))
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Screens
CREATE INDEX IF NOT EXISTS idx_screens_created_at ON screens(created_at);
CREATE INDEX IF NOT EXISTS idx_screens_name ON screens(name);

-- Flows
CREATE INDEX IF NOT EXISTS idx_flows_created_at ON flows(created_at);
CREATE INDEX IF NOT EXISTS idx_flows_name ON flows(name);

-- Flow-Screens
CREATE INDEX IF NOT EXISTS idx_flow_screens_flow ON flow_screens(flow_id);
CREATE INDEX IF NOT EXISTS idx_flow_screens_screen ON flow_screens(screen_id);

-- Components
CREATE INDEX IF NOT EXISTS idx_components_screen ON components(screen_id);
CREATE INDEX IF NOT EXISTS idx_components_type ON components(type);
CREATE INDEX IF NOT EXISTS idx_components_created_at ON components(created_at);

-- System Tokens
CREATE INDEX IF NOT EXISTS idx_system_tokens_type ON system_tokens(type_id);
CREATE INDEX IF NOT EXISTS idx_system_tokens_name ON system_tokens(name);

-- Component-Tokens
CREATE INDEX IF NOT EXISTS idx_component_tokens_component ON component_tokens(component_id);
CREATE INDEX IF NOT EXISTS idx_component_tokens_token ON component_tokens(token_id);

-- Audit Findings
CREATE INDEX IF NOT EXISTS idx_audit_findings_entity ON audit_findings(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_findings_severity ON audit_findings(severity_id);
CREATE INDEX IF NOT EXISTS idx_audit_findings_created_at ON audit_findings(created_at);

-- Plan Phases
CREATE INDEX IF NOT EXISTS idx_plan_phases_audit ON plan_phases(audit_id);
CREATE INDEX IF NOT EXISTS idx_plan_phases_status ON plan_phases(status_id);
CREATE INDEX IF NOT EXISTS idx_plan_phases_sequence ON plan_phases(sequence);

-- =============================================================================
-- SCHEMA VERSION TRACKING
-- =============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT
);

INSERT OR IGNORE INTO schema_version (version, description) VALUES
    (1, 'Initial schema with all entity tables');