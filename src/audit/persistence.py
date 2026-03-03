"""
Audit persistence layer for database operations.

Provides persistence for audit sessions and findings, integrating with existing CRUD.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.db.database import connection
from src.db.crud import create_audit_finding, get_audit_finding, list_audit_findings
from src.db.models import AuditFindingCreate as DbAuditFindingCreate, EntityType

from .models import (
    AuditDimension,
    AuditSession,
    AuditSessionStatus,
    AuditFindingCreate,
)

logger = logging.getLogger(__name__)


# =============================================================================
# AUDIT SESSION PERSISTENCE
# =============================================================================

def save_audit_session(session: AuditSession, db_path: Optional[Path] = None) -> AuditSession:
    """Save an audit session to the database.
    
    Creates a new session record or updates existing one.
    
    Args:
        session: AuditSession to save
        db_path: Optional database path
        
    Returns:
        Saved AuditSession
    """
    now = datetime.now().isoformat()
    
    with connection(db_path) as conn:
        # Check if session exists
        cursor = conn.execute(
            "SELECT id FROM audit_sessions WHERE id = ?", (session.id,)
        )
        exists = cursor.fetchone() is not None
        
        if exists:
            # Update existing session
            conn.execute(
                """UPDATE audit_sessions 
                   SET status = ?, 
                       dimensions = ?, 
                       completed_dimensions = ?,
                       finding_ids = ?,
                       started_at = ?,
                       completed_at = ?,
                       error_message = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (
                    session.status.value,
                    json.dumps([d.value for d in session.dimensions]),
                    json.dumps([d.value for d in session.completed_dimensions]),
                    json.dumps(session.finding_ids),
                    session.started_at.isoformat() if session.started_at else None,
                    session.completed_at.isoformat() if session.completed_at else None,
                    session.error_message,
                    now,
                    session.id,
                ),
            )
        else:
            # Create new session
            conn.execute(
                """INSERT INTO audit_sessions 
                   (id, screen_id, status, dimensions, completed_dimensions, 
                    finding_ids, started_at, completed_at, error_message, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session.id,
                    session.screen_id,
                    session.status.value,
                    json.dumps([d.value for d in session.dimensions]),
                    json.dumps([d.value for d in session.completed_dimensions]),
                    json.dumps(session.finding_ids),
                    session.started_at.isoformat() if session.started_at else None,
                    session.completed_at.isoformat() if session.completed_at else None,
                    session.error_message,
                    session.created_at.isoformat() if session.created_at else now,
                    now,
                ),
            )
    
    return session


def get_audit_session(session_id: str, db_path: Optional[Path] = None) -> Optional[AuditSession]:
    """Get an audit session by ID.
    
    Args:
        session_id: UUID of the session
        db_path: Optional database path
        
    Returns:
        AuditSession or None if not found
    """
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT * FROM audit_sessions WHERE id = ?", (session_id,)
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return _row_to_session(dict(row))


def get_audit_sessions_by_screen(
    screen_id: str,
    db_path: Optional[Path] = None,
) -> list[AuditSession]:
    """Get all audit sessions for a screen.
    
    Args:
        screen_id: UUID of the screen
        db_path: Optional database path
        
    Returns:
        List of AuditSession objects
    """
    with connection(db_path) as conn:
        cursor = conn.execute(
            """SELECT * FROM audit_sessions 
               WHERE screen_id = ? 
               ORDER BY created_at DESC""",
            (screen_id,),
        )
        rows = cursor.fetchall()
    
    return [_row_to_session(dict(row)) for row in rows]


def complete_audit_session(
    session_id: str,
    updates: Optional[dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> Optional[AuditSession]:
    """Mark an audit session as complete.
    
    Args:
        session_id: UUID of the session
        updates: Optional additional updates
        db_path: Optional database path
        
    Returns:
        Updated AuditSession or None if not found
    """
    now = datetime.now().isoformat()
    
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT id FROM audit_sessions WHERE id = ?", (session_id,)
        )
        if cursor.fetchone() is None:
            return None
        
        # Build update query
        update_fields = ["completed_at = ?", "updated_at = ?"]
        values = [now, now]
        
        if updates:
            if "status" in updates:
                update_fields.append("status = ?")
                values.append(updates["status"])
            if "completed_dimensions" in updates:
                update_fields.append("completed_dimensions = ?")
                values.append(json.dumps(updates["completed_dimensions"]))
            if "finding_ids" in updates:
                update_fields.append("finding_ids = ?")
                values.append(json.dumps(updates["finding_ids"]))
            if "error_message" in updates:
                update_fields.append("error_message = ?")
                values.append(updates["error_message"])
        
        values.append(session_id)
        
        conn.execute(
            f"UPDATE audit_sessions SET {', '.join(update_fields)} WHERE id = ?",
            values,
        )
    
    return get_audit_session(session_id, db_path)


def _row_to_session(row: dict) -> AuditSession:
    """Convert database row to AuditSession model."""
    return AuditSession(
        id=row["id"],
        screen_id=row["screen_id"],
        status=AuditSessionStatus(row["status"]),
        dimensions=[AuditDimension(d) for d in json.loads(row["dimensions"])],
        completed_dimensions=[
            AuditDimension(d) for d in json.loads(row["completed_dimensions"] or "[]")
        ],
        finding_ids=json.loads(row["finding_ids"] or "[]"),
        started_at=datetime.fromisoformat(row["started_at"]) if row.get("started_at") else None,
        completed_at=datetime.fromisoformat(row["completed_at"]) if row.get("completed_at") else None,
        error_message=row.get("error_message"),
        created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
    )


# =============================================================================
# AUDIT FINDING PERSISTENCE
# =============================================================================

def save_audit_finding(
    session_id: str,
    finding: AuditFindingCreate,
    db_path: Optional[Path] = None,
) -> str:
    """Save an audit finding to the database.
    
    Args:
        session_id: UUID of the audit session
        finding: AuditFindingCreate to save
        db_path: Optional database path
        
    Returns:
        UUID of the created finding
    """
    # Convert to DB model
    db_finding = DbAuditFindingCreate(
        entity_type=finding.entity_type,
        entity_id=finding.entity_id,
        issue=finding.issue,
        rationale=finding.rationale,
        severity=finding.severity,
        related_standard=_extract_standard_ref(finding),
        metadata=_build_metadata(session_id, finding),
    )
    
    # Use existing CRUD
    created = create_audit_finding(db_finding, db_path)
    
    logger.debug(f"Saved audit finding {created.id} for session {session_id}")
    
    return created.id


def get_findings_by_screen(
    screen_id: str,
    db_path: Optional[Path] = None,
) -> list[dict]:
    """Get all audit findings for a screen.
    
    Args:
        screen_id: UUID of the screen
        db_path: Optional database path
        
    Returns:
        List of finding dictionaries
    """
    findings = list_audit_findings(
        entity_type=EntityType.SCREEN.value,
        entity_id=screen_id,
        db_path=db_path,
    )
    
    return [f.model_dump() for f in findings]


def get_findings_by_dimension(
    dimension: AuditDimension,
    session_id: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> list[dict]:
    """Get all audit findings for a dimension.
    
    Args:
        dimension: Audit dimension to filter by
        session_id: Optional session ID to filter by
        db_path: Optional database path
        
    Returns:
        List of finding dictionaries
    """
    with connection(db_path) as conn:
        query = """
            SELECT af.* FROM audit_findings af
            INNER JOIN audit_sessions ase ON json_extract(af.metadata, '$.session_id') = ase.id
            WHERE json_extract(af.metadata, '$.dimension') = ?
        """
        params = [dimension.value]
        
        if session_id:
            query += " AND ase.id = ?"
            params.append(session_id)
        
        query += " ORDER BY af.created_at DESC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


def get_findings_by_session(
    session_id: str,
    db_path: Optional[Path] = None,
) -> list[dict]:
    """Get all findings for an audit session.
    
    Args:
        session_id: UUID of the audit session
        db_path: Optional database path
        
    Returns:
        List of finding dictionaries
    """
    with connection(db_path) as conn:
        cursor = conn.execute(
            """SELECT af.* FROM audit_findings af
               WHERE json_extract(af.metadata, '$.session_id') = ?
               ORDER BY af.created_at""",
            (session_id,),
        )
        rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _extract_standard_ref(finding: AuditFindingCreate) -> Optional[str]:
    """Extract standard reference string from finding."""
    if not finding.standards_refs:
        return None
    
    refs = []
    for ref in finding.standards_refs:
        if ref.wcag:
            refs.append(f"WCAG {ref.wcag.criterion}")
        if ref.design_token:
            refs.append(ref.design_token.token_name)
        if ref.custom:
            refs.append(ref.custom)
    
    return "; ".join(refs) if refs else None


def _build_metadata(session_id: str, finding: AuditFindingCreate) -> dict:
    """Build metadata dict for finding storage."""
    metadata = finding.metadata or {}
    
    # Add audit-specific metadata
    metadata["session_id"] = session_id
    metadata["dimension"] = finding.dimension.value
    metadata["jobs_filtered"] = finding.jobs_filtered
    
    if finding.jobs_filter_score is not None:
        metadata["jobs_filter_score"] = finding.jobs_filter_score
    
    if finding.standards_refs:
        metadata["standards_refs"] = [
            {
                "design_token": r.design_token.model_dump() if r.design_token else None,
                "wcag": r.wcag.model_dump() if r.wcag else None,
                "custom": r.custom,
            }
            for r in finding.standards_refs
        ]
    
    return metadata


# =============================================================================
# DATABASE SCHEMA ENSURED
# =============================================================================

def ensure_audit_tables(db_path: Optional[Path] = None) -> None:
    """Ensure audit_sessions table exists.
    
    Creates the table if it doesn't exist.
    
    Args:
        db_path: Optional database path
    """
    with connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_sessions (
                id TEXT PRIMARY KEY,
                screen_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                dimensions TEXT NOT NULL DEFAULT '[]',
                completed_dimensions TEXT NOT NULL DEFAULT '[]',
                finding_ids TEXT NOT NULL DEFAULT '[]',
                started_at TEXT,
                completed_at TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (screen_id) REFERENCES screens(id) ON DELETE CASCADE
            )
        """)
        
        # Create index for faster lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_sessions_screen_id 
            ON audit_sessions(screen_id)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_sessions_status 
            ON audit_sessions(status)
        """)
    
    logger.info("Audit tables ensured")