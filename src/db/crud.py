"""
CRUD operations for Autonomous-GLM database entities.

Provides create, read, update, and delete operations for all entities.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .database import connection
from .models import (
    AuditFinding,
    AuditFindingCreate,
    AuditFindingUpdate,
    Component,
    ComponentCreate,
    ComponentUpdate,
    Flow,
    FlowCreate,
    FlowUpdate,
    PlanPhase,
    PlanPhaseCreate,
    PlanPhaseUpdate,
    Screen,
    ScreenCreate,
    ScreenUpdate,
    SystemToken,
    SystemTokenCreate,
    SystemTokenUpdate,
    row_to_audit_finding,
    row_to_component,
    row_to_flow,
    row_to_plan_phase,
    row_to_screen,
    row_to_system_token,
    Severity,
    PhaseStatus,
    TokenType,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_severity_id(severity: Severity) -> int:
    """Convert Severity enum to database ID."""
    mapping = {
        Severity.LOW: 1,
        Severity.MEDIUM: 2,
        Severity.HIGH: 3,
        Severity.CRITICAL: 4,
    }
    return mapping[severity]


def _get_status_id(status: PhaseStatus) -> int:
    """Convert PhaseStatus enum to database ID."""
    mapping = {
        PhaseStatus.PROPOSED: 1,
        PhaseStatus.IN_PROGRESS: 2,
        PhaseStatus.COMPLETE: 3,
    }
    return mapping[status]


def _get_token_type_id(token_type: TokenType) -> int:
    """Convert TokenType enum to database ID."""
    mapping = {
        TokenType.COLOR: 1,
        TokenType.SPACING: 2,
        TokenType.TYPOGRAPHY: 3,
        TokenType.BORDER: 4,
        TokenType.SHADOW: 5,
        TokenType.ANIMATION: 6,
    }
    return mapping[token_type]


# =============================================================================
# SCREEN CRUD
# =============================================================================

def create_screen(screen: ScreenCreate, db_path: Optional[Path] = None) -> Screen:
    """Create a new screen in the database."""
    import uuid
    
    screen_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    with connection(db_path) as conn:
        conn.execute(
            """INSERT INTO screens (id, name, image_path, hierarchy, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                screen_id,
                screen.name,
                screen.image_path,
                json.dumps(screen.hierarchy) if screen.hierarchy else None,
                now,
            ),
        )
        
        cursor = conn.execute(
            "SELECT * FROM screens WHERE id = ?", (screen_id,)
        )
        row = cursor.fetchone()
        
    return row_to_screen(dict(row))


def get_screen(screen_id: str, db_path: Optional[Path] = None) -> Optional[Screen]:
    """Get a screen by ID."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM screens WHERE id = ?", (screen_id,)
        )
        row = cursor.fetchone()
        
    if row is None:
        return None
    
    return row_to_screen(dict(row))


def list_screens(
    limit: int = 100,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> list[Screen]:
    """List all screens with pagination."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM screens ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = cursor.fetchall()
        
    return [row_to_screen(dict(row)) for row in rows]


def update_screen(
    screen_id: str,
    screen: ScreenUpdate,
    db_path: Optional[Path] = None,
) -> Optional[Screen]:
    """Update an existing screen."""
    updates = []
    values = []
    
    if screen.name is not None:
        updates.append("name = ?")
        values.append(screen.name)
    if screen.image_path is not None:
        updates.append("image_path = ?")
        values.append(screen.image_path)
    if screen.hierarchy is not None:
        updates.append("hierarchy = ?")
        values.append(json.dumps(screen.hierarchy))
    
    if not updates:
        return get_screen(screen_id, db_path)
    
    values.append(screen_id)
    
    with connection(db_path) as conn:
        conn.execute(
            f"UPDATE screens SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        
    return get_screen(screen_id, db_path)


def delete_screen(screen_id: str, db_path: Optional[Path] = None) -> bool:
    """Delete a screen by ID."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM screens WHERE id = ?", (screen_id,)
        )
        return cursor.rowcount > 0


# =============================================================================
# FLOW CRUD
# =============================================================================

def create_flow(flow: FlowCreate, db_path: Optional[Path] = None) -> Flow:
    """Create a new flow in the database."""
    import uuid
    
    flow_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    with connection(db_path) as conn:
        conn.execute(
            """INSERT INTO flows (id, name, video_path, metadata, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                flow_id,
                flow.name,
                flow.video_path,
                json.dumps(flow.metadata) if flow.metadata else None,
                now,
            ),
        )
        
        # Add screens to flow with sequence ordering
        for seq, screen_id in enumerate(flow.screen_ids, start=1):
            conn.execute(
                """INSERT INTO flow_screens (flow_id, screen_id, sequence)
                   VALUES (?, ?, ?)""",
                (flow_id, screen_id, seq),
            )
        
        cursor = conn.execute(
            "SELECT * FROM flows WHERE id = ?", (flow_id,)
        )
        row = cursor.fetchone()
        
    return row_to_flow(dict(row), flow.screen_ids)


def get_flow(flow_id: str, db_path: Optional[Path] = None) -> Optional[Flow]:
    """Get a flow by ID with its ordered screen IDs."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM flows WHERE id = ?", (flow_id,)
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        # Get ordered screen IDs
        cursor = conn.execute(
            """SELECT screen_id FROM flow_screens 
               WHERE flow_id = ? ORDER BY sequence""",
            (flow_id,),
        )
        screen_ids = [r["screen_id"] for r in cursor.fetchall()]
        
    return row_to_flow(dict(row), screen_ids)


def list_flows(
    limit: int = 100,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> list[Flow]:
    """List all flows with pagination."""
    flows = []
    
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM flows ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = cursor.fetchall()
        
        for row in rows:
            # Get screen IDs for each flow
            cursor = conn.execute(
                """SELECT screen_id FROM flow_screens 
                   WHERE flow_id = ? ORDER BY sequence""",
                (row["id"],),
            )
            screen_ids = [r["screen_id"] for r in cursor.fetchall()]
            flows.append(row_to_flow(dict(row), screen_ids))
            
    return flows


def update_flow(
    flow_id: str,
    flow: FlowUpdate,
    db_path: Optional[Path] = None,
) -> Optional[Flow]:
    """Update an existing flow."""
    updates = []
    values = []
    
    if flow.name is not None:
        updates.append("name = ?")
        values.append(flow.name)
    if flow.video_path is not None:
        updates.append("video_path = ?")
        values.append(flow.video_path)
    if flow.metadata is not None:
        updates.append("metadata = ?")
        values.append(json.dumps(flow.metadata))
    
    with connection(db_path) as conn:
        if updates:
            values.append(flow_id)
            conn.execute(
                f"UPDATE flows SET {', '.join(updates)} WHERE id = ?",
                values,
            )
        
        # Update screen associations if provided
        if flow.screen_ids is not None:
            # Remove existing associations
            conn.execute(
                "DELETE FROM flow_screens WHERE flow_id = ?", (flow_id,)
            )
            # Add new associations
            for seq, screen_id in enumerate(flow.screen_ids, start=1):
                conn.execute(
                    """INSERT INTO flow_screens (flow_id, screen_id, sequence)
                       VALUES (?, ?, ?)""",
                    (flow_id, screen_id, seq),
                )
        
    return get_flow(flow_id, db_path)


def delete_flow(flow_id: str, db_path: Optional[Path] = None) -> bool:
    """Delete a flow by ID (cascade deletes flow_screens)."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM flows WHERE id = ?", (flow_id,)
        )
        return cursor.rowcount > 0


# =============================================================================
# COMPONENT CRUD
# =============================================================================

def create_component(
    component: ComponentCreate,
    db_path: Optional[Path] = None,
) -> Component:
    """Create a new component in the database."""
    import uuid
    
    component_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    with connection(db_path) as conn:
        conn.execute(
            """INSERT INTO components (id, screen_id, type, bounding_box, properties, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                component_id,
                component.screen_id,
                component.type,
                component.bounding_box.model_dump_json(),
                json.dumps(component.properties) if component.properties else None,
                now,
            ),
        )
        
        # Add token associations
        for token_id in component.token_ids:
            conn.execute(
                """INSERT INTO component_tokens (component_id, token_id)
                   VALUES (?, ?)""",
                (component_id, token_id),
            )
        
        cursor = conn.execute(
            "SELECT * FROM components WHERE id = ?", (component_id,)
        )
        row = cursor.fetchone()
        
    return row_to_component(dict(row), component.token_ids)


def get_component(
    component_id: str,
    db_path: Optional[Path] = None,
) -> Optional[Component]:
    """Get a component by ID with its token IDs."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM components WHERE id = ?", (component_id,)
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        # Get token IDs
        cursor = conn.execute(
            "SELECT token_id FROM component_tokens WHERE component_id = ?",
            (component_id,),
        )
        token_ids = [r["token_id"] for r in cursor.fetchall()]
        
    return row_to_component(dict(row), token_ids)


def list_components(
    screen_id: Optional[str] = None,
    component_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> list[Component]:
    """List components with optional filtering."""
    components = []
    
    with connection(db_path) as conn:
        query = "SELECT * FROM components WHERE 1=1"
        params = []
        
        if screen_id:
            query += " AND screen_id = ?"
            params.append(screen_id)
        if component_type:
            query += " AND type = ?"
            params.append(component_type)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        for row in rows:
            # Get token IDs for each component
            cursor = conn.execute(
                "SELECT token_id FROM component_tokens WHERE component_id = ?",
                (row["id"],),
            )
            token_ids = [r["token_id"] for r in cursor.fetchall()]
            components.append(row_to_component(dict(row), token_ids))
            
    return components


def update_component(
    component_id: str,
    component: ComponentUpdate,
    db_path: Optional[Path] = None,
) -> Optional[Component]:
    """Update an existing component."""
    updates = []
    values = []
    
    if component.type is not None:
        updates.append("type = ?")
        values.append(component.type)
    if component.bounding_box is not None:
        updates.append("bounding_box = ?")
        values.append(component.bounding_box.model_dump_json())
    if component.properties is not None:
        updates.append("properties = ?")
        values.append(json.dumps(component.properties))
    
    with connection(db_path) as conn:
        if updates:
            values.append(component_id)
            conn.execute(
                f"UPDATE components SET {', '.join(updates)} WHERE id = ?",
                values,
            )
        
        # Update token associations if provided
        if component.token_ids is not None:
            # Remove existing associations
            conn.execute(
                "DELETE FROM component_tokens WHERE component_id = ?",
                (component_id,),
            )
            # Add new associations
            for token_id in component.token_ids:
                conn.execute(
                    """INSERT INTO component_tokens (component_id, token_id)
                       VALUES (?, ?)""",
                    (component_id, token_id),
                )
        
    return get_component(component_id, db_path)


def delete_component(
    component_id: str,
    db_path: Optional[Path] = None,
) -> bool:
    """Delete a component by ID (cascade deletes component_tokens)."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM components WHERE id = ?", (component_id,)
        )
        return cursor.rowcount > 0


# =============================================================================
# SYSTEM TOKEN CRUD
# =============================================================================

def create_system_token(
    token: SystemTokenCreate,
    db_path: Optional[Path] = None,
) -> SystemToken:
    """Create a new system token in the database."""
    import uuid
    
    token_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    type_id = _get_token_type_id(token.type)
    
    with connection(db_path) as conn:
        conn.execute(
            """INSERT INTO system_tokens (id, name, type_id, value, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                token_id,
                token.name,
                type_id,
                token.value,
                token.description,
                now,
            ),
        )
        
        cursor = conn.execute(
            "SELECT * FROM system_tokens WHERE id = ?", (token_id,)
        )
        row = cursor.fetchone()
        
    return row_to_system_token(dict(row))


def get_system_token(
    token_id: str,
    db_path: Optional[Path] = None,
) -> Optional[SystemToken]:
    """Get a system token by ID."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM system_tokens WHERE id = ?", (token_id,)
        )
        row = cursor.fetchone()
        
    if row is None:
        return None
    
    return row_to_system_token(dict(row))


def list_system_tokens(
    token_type: Optional[TokenType] = None,
    limit: int = 100,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> list[SystemToken]:
    """List system tokens with optional type filtering."""
    with connection(db_path) as conn:
        query = "SELECT * FROM system_tokens WHERE 1=1"
        params = []
        
        if token_type:
            query += " AND type_id = ?"
            params.append(_get_token_type_id(token_type))
        
        query += " ORDER BY name LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
    return [row_to_system_token(dict(row)) for row in rows]


def update_system_token(
    token_id: str,
    token: SystemTokenUpdate,
    db_path: Optional[Path] = None,
) -> Optional[SystemToken]:
    """Update an existing system token."""
    updates = []
    values = []
    
    if token.name is not None:
        updates.append("name = ?")
        values.append(token.name)
    if token.type is not None:
        updates.append("type_id = ?")
        values.append(_get_token_type_id(token.type))
    if token.value is not None:
        updates.append("value = ?")
        values.append(token.value)
    if token.description is not None:
        updates.append("description = ?")
        values.append(token.description)
    
    if not updates:
        return get_system_token(token_id, db_path)
    
    values.append(token_id)
    
    with connection(db_path) as conn:
        conn.execute(
            f"UPDATE system_tokens SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        
    return get_system_token(token_id, db_path)


def delete_system_token(
    token_id: str,
    db_path: Optional[Path] = None,
) -> bool:
    """Delete a system token by ID."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM system_tokens WHERE id = ?", (token_id,)
        )
        return cursor.rowcount > 0


# =============================================================================
# AUDIT FINDING CRUD
# =============================================================================

def create_audit_finding(
    finding: AuditFindingCreate,
    db_path: Optional[Path] = None,
) -> AuditFinding:
    """Create a new audit finding in the database."""
    import uuid
    
    finding_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    severity_id = _get_severity_id(finding.severity)
    
    with connection(db_path) as conn:
        conn.execute(
            """INSERT INTO audit_findings 
               (id, entity_type, entity_id, issue, rationale, severity_id, related_standard, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                finding_id,
                finding.entity_type.value,
                finding.entity_id,
                finding.issue,
                finding.rationale,
                severity_id,
                finding.related_standard,
                json.dumps(finding.metadata) if finding.metadata else None,
                now,
            ),
        )
        
        cursor = conn.execute(
            "SELECT * FROM audit_findings WHERE id = ?", (finding_id,)
        )
        row = cursor.fetchone()
        
    return row_to_audit_finding(dict(row))


def get_audit_finding(
    finding_id: str,
    db_path: Optional[Path] = None,
) -> Optional[AuditFinding]:
    """Get an audit finding by ID."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM audit_findings WHERE id = ?", (finding_id,)
        )
        row = cursor.fetchone()
        
    if row is None:
        return None
    
    return row_to_audit_finding(dict(row))


def list_audit_findings(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    severity: Optional[Severity] = None,
    limit: int = 100,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> list[AuditFinding]:
    """List audit findings with optional filtering."""
    with connection(db_path) as conn:
        query = "SELECT * FROM audit_findings WHERE 1=1"
        params = []
        
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        if severity:
            query += " AND severity_id = ?"
            params.append(_get_severity_id(severity))
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
    return [row_to_audit_finding(dict(row)) for row in rows]


def update_audit_finding(
    finding_id: str,
    finding: AuditFindingUpdate,
    db_path: Optional[Path] = None,
) -> Optional[AuditFinding]:
    """Update an existing audit finding."""
    updates = []
    values = []
    
    if finding.issue is not None:
        updates.append("issue = ?")
        values.append(finding.issue)
    if finding.rationale is not None:
        updates.append("rationale = ?")
        values.append(finding.rationale)
    if finding.severity is not None:
        updates.append("severity_id = ?")
        values.append(_get_severity_id(finding.severity))
    if finding.related_standard is not None:
        updates.append("related_standard = ?")
        values.append(finding.related_standard)
    if finding.metadata is not None:
        updates.append("metadata = ?")
        values.append(json.dumps(finding.metadata))
    
    if not updates:
        return get_audit_finding(finding_id, db_path)
    
    values.append(finding_id)
    
    with connection(db_path) as conn:
        conn.execute(
            f"UPDATE audit_findings SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        
    return get_audit_finding(finding_id, db_path)


def delete_audit_finding(
    finding_id: str,
    db_path: Optional[Path] = None,
) -> bool:
    """Delete an audit finding by ID."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM audit_findings WHERE id = ?", (finding_id,)
        )
        return cursor.rowcount > 0


# =============================================================================
# PLAN PHASE CRUD
# =============================================================================

def create_plan_phase(
    phase: PlanPhaseCreate,
    db_path: Optional[Path] = None,
) -> PlanPhase:
    """Create a new plan phase in the database."""
    import uuid
    
    phase_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    status_id = _get_status_id(phase.status)
    actions_json = json.dumps([a.model_dump() for a in phase.actions])
    
    with connection(db_path) as conn:
        conn.execute(
            """INSERT INTO plan_phases 
               (id, audit_id, phase_name, sequence, actions, status_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                phase_id,
                phase.audit_id,
                phase.phase_name.value,
                phase.sequence,
                actions_json,
                status_id,
                now,
            ),
        )
        
        cursor = conn.execute(
            "SELECT * FROM plan_phases WHERE id = ?", (phase_id,)
        )
        row = cursor.fetchone()
        
    return row_to_plan_phase(dict(row))


def get_plan_phase(
    phase_id: str,
    db_path: Optional[Path] = None,
) -> Optional[PlanPhase]:
    """Get a plan phase by ID."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM plan_phases WHERE id = ?", (phase_id,)
        )
        row = cursor.fetchone()
        
    if row is None:
        return None
    
    return row_to_plan_phase(dict(row))


def list_plan_phases(
    audit_id: Optional[str] = None,
    status: Optional[PhaseStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> list[PlanPhase]:
    """List plan phases with optional filtering."""
    with connection(db_path) as conn:
        query = "SELECT * FROM plan_phases WHERE 1=1"
        params = []
        
        if audit_id:
            query += " AND audit_id = ?"
            params.append(audit_id)
        if status:
            query += " AND status_id = ?"
            params.append(_get_status_id(status))
        
        query += " ORDER BY sequence LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
    return [row_to_plan_phase(dict(row)) for row in rows]


def update_plan_phase(
    phase_id: str,
    phase: PlanPhaseUpdate,
    db_path: Optional[Path] = None,
) -> Optional[PlanPhase]:
    """Update an existing plan phase."""
    updates = []
    values = []
    
    if phase.phase_name is not None:
        updates.append("phase_name = ?")
        values.append(phase.phase_name.value)
    if phase.sequence is not None:
        updates.append("sequence = ?")
        values.append(phase.sequence)
    if phase.actions is not None:
        updates.append("actions = ?")
        values.append(json.dumps([a.model_dump() for a in phase.actions]))
    if phase.status is not None:
        updates.append("status_id = ?")
        values.append(_get_status_id(phase.status))
    
    if not updates:
        return get_plan_phase(phase_id, db_path)
    
    updates.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    
    values.append(phase_id)
    
    with connection(db_path) as conn:
        conn.execute(
            f"UPDATE plan_phases SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        
    return get_plan_phase(phase_id, db_path)


def delete_plan_phase(
    phase_id: str,
    db_path: Optional[Path] = None,
) -> bool:
    """Delete a plan phase by ID."""
    with connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM plan_phases WHERE id = ?", (phase_id,)
        )
        return cursor.rowcount > 0


# =============================================================================
# BATCH OPERATIONS FOR M3-1 PERSISTENCE
# =============================================================================

def batch_create_components(
    screen_id: str,
    components: list["DetectedComponent"],
    db_path: Optional[Path] = None,
) -> list[Component]:
    """Batch create components from M2 detection results.
    
    Args:
        screen_id: UUID of the parent screen
        components: List of DetectedComponent from vision detection
        db_path: Optional database path
        
    Returns:
        List of persisted Component models
        
    Raises:
        ValueError: If any component is invalid
        sqlite3.Error: If database operation fails (rolls back transaction)
    """
    import uuid
    from .models import BoundingBox
    
    now = datetime.now().isoformat()
    persisted = []
    
    with connection(db_path) as conn:
        for detected in components:
            component_id = str(uuid.uuid4())
            
            # Convert normalized bbox to BoundingBox model
            bbox = BoundingBox(
                x=detected.bbox_x,
                y=detected.bbox_y,
                width=detected.bbox_width,
                height=detected.bbox_height,
            )
            
            # Include confidence and label in properties
            properties = detected.properties or {}
            properties["_confidence"] = detected.confidence
            if detected.label:
                properties["_label"] = detected.label
            
            conn.execute(
                """INSERT INTO components (id, screen_id, type, bounding_box, properties, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    component_id,
                    screen_id,
                    detected.type.value,
                    bbox.model_dump_json(),
                    json.dumps(properties),
                    now,
                ),
            )
            
            persisted.append(Component(
                id=component_id,
                screen_id=screen_id,
                type=detected.type.value,
                bounding_box=bbox,
                properties=properties,
                token_ids=[],
                created_at=datetime.fromisoformat(now),
            ))
    
    return persisted


def batch_create_tokens(
    tokens: list["DesignToken"],
    db_path: Optional[Path] = None,
) -> list[SystemToken]:
    """Batch create system tokens from M2 token extraction.
    
    Args:
        tokens: List of DesignToken from token extraction
        db_path: Optional database path
        
    Returns:
        List of persisted SystemToken models
        
    Note:
        Uses INSERT OR IGNORE to skip duplicates (unique constraint on name+type)
    """
    import uuid
    
    now = datetime.now().isoformat()
    persisted = []
    
    # Map token types between vision and db models
    type_mapping = {
        "color": TokenType.COLOR,
        "spacing": TokenType.SPACING,
        "typography": TokenType.TYPOGRAPHY,
        "border": TokenType.BORDER,
        "shadow": TokenType.SHADOW,
    }
    
    with connection(db_path) as conn:
        for token in tokens:
            token_id = str(uuid.uuid4())
            
            # Get the token type string from the DesignToken
            token_type_str = token.token_type.value if hasattr(token.token_type, 'value') else str(token.token_type)
            db_token_type = type_mapping.get(token_type_str, TokenType.COLOR)
            type_id = _get_token_type_id(db_token_type)
            
            # Use INSERT OR IGNORE to handle duplicates gracefully
            conn.execute(
                """INSERT OR IGNORE INTO system_tokens (id, name, type_id, value, description, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    token_id,
                    token.name,
                    type_id,
                    token.value,
                    token.description,
                    now,
                ),
            )
            
            # Check if insert succeeded (rowcount > 0 means new row)
            cursor = conn.execute(
                "SELECT id FROM system_tokens WHERE name = ? AND type_id = ?",
                (token.name, type_id),
            )
            existing_row = cursor.fetchone()
            
            if existing_row:
                # Fetch the actual token (either newly inserted or existing)
                cursor = conn.execute(
                    "SELECT * FROM system_tokens WHERE id = ?", (existing_row["id"],)
                )
                row = cursor.fetchone()
                persisted.append(row_to_system_token(dict(row)))
    
    return persisted


def batch_link_components_tokens(
    links: list[tuple[str, str]],
    db_path: Optional[Path] = None,
) -> int:
    """Batch link components to tokens.
    
    Args:
        links: List of (component_id, token_id) tuples
        db_path: Optional database path
        
    Returns:
        Number of links created
    """
    count = 0
    
    with connection(db_path) as conn:
        for component_id, token_id in links:
            try:
                conn.execute(
                    """INSERT INTO component_tokens (component_id, token_id)
                       VALUES (?, ?)""",
                    (component_id, token_id),
                )
                count += 1
            except Exception:
                # Skip duplicate links (PRIMARY KEY constraint)
                pass
    
    return count


def delete_components_by_screen(
    screen_id: str,
    db_path: Optional[Path] = None,
) -> int:
    """Delete all components for a screen.
    
    Args:
        screen_id: UUID of the screen
        db_path: Optional database path
        
    Returns:
        Number of components deleted
    """
    with connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM components WHERE screen_id = ?", (screen_id,)
        )
        return cursor.rowcount


def clear_all_tokens(
    db_path: Optional[Path] = None,
) -> int:
    """Clear all system tokens.
    
    Args:
        db_path: Optional database path
        
    Returns:
        Number of tokens deleted
    """
    with connection(db_path) as conn:
        cursor = conn.execute("DELETE FROM system_tokens")
        return cursor.rowcount


def get_components_by_screen(
    screen_id: str,
    db_path: Optional[Path] = None,
) -> list[Component]:
    """Get all components for a screen.
    
    Args:
        screen_id: UUID of the screen
        db_path: Optional database path
        
    Returns:
        List of Component models
    """
    components = []
    
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM components WHERE screen_id = ? ORDER BY created_at",
            (screen_id,),
        )
        rows = cursor.fetchall()
        
        for row in rows:
            # Get token IDs for each component
            cursor = conn.execute(
                "SELECT token_id FROM component_tokens WHERE component_id = ?",
                (row["id"],),
            )
            token_ids = [r["token_id"] for r in cursor.fetchall()]
            components.append(row_to_component(dict(row), token_ids))
    
    return components


def get_all_tokens(
    db_path: Optional[Path] = None,
) -> list[SystemToken]:
    """Get all system tokens.
    
    Args:
        db_path: Optional database path
        
    Returns:
        List of SystemToken models
    """
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM system_tokens ORDER BY type_id, name"
        )
        rows = cursor.fetchall()
    
    return [row_to_system_token(dict(row)) for row in rows]


def get_component_tokens(
    component_id: str,
    db_path: Optional[Path] = None,
) -> list[SystemToken]:
    """Get all tokens linked to a component.
    
    Args:
        component_id: UUID of the component
        db_path: Optional database path
        
    Returns:
        List of SystemToken models
    """
    with connection(db_path) as conn:
        cursor = conn.execute(
            """SELECT st.* FROM system_tokens st
               INNER JOIN component_tokens ct ON st.id = ct.token_id
               WHERE ct.component_id = ?
               ORDER BY st.type_id, st.name""",
            (component_id,),
        )
        rows = cursor.fetchall()
    
    return [row_to_system_token(dict(row)) for row in rows]


def get_token_components(
    token_id: str,
    db_path: Optional[Path] = None,
) -> list[Component]:
    """Get all components using a specific token.
    
    Args:
        token_id: UUID of the token
        db_path: Optional database path
        
    Returns:
        List of Component models
    """
    components = []
    
    with connection(db_path) as conn:
        cursor = conn.execute(
            """SELECT c.* FROM components c
               INNER JOIN component_tokens ct ON c.id = ct.component_id
               WHERE ct.token_id = ?
               ORDER BY c.created_at""",
            (token_id,),
        )
        rows = cursor.fetchall()
        
        for row in rows:
            # Get all token IDs for each component (not just the queried one)
            cursor = conn.execute(
                "SELECT token_id FROM component_tokens WHERE component_id = ?",
                (row["id"],),
            )
            token_ids = [r["token_id"] for r in cursor.fetchall()]
            components.append(row_to_component(dict(row), token_ids))
    
    return components
