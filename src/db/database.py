"""
Database connection and initialization module for Autonomous-GLM.

Provides connection management, schema initialization, and database utilities.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

# Default database path relative to project root
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "autonomous_glm.db"

# Schema file location
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Create a new database connection with foreign keys enabled.
    
    Args:
        db_path: Optional path to database file. Uses default if not provided.
    
    Returns:
        sqlite3.Connection: Database connection object.
    """
    path = db_path or DEFAULT_DB_PATH
    
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    
    # Enable foreign key support (required for SQLite)
    conn.execute("PRAGMA foreign_keys = ON")
    
    return conn


@contextmanager
def connection(db_path: Optional[Path] = None):
    """
    Context manager for database connections.
    
    Automatically handles connection lifecycle with proper cleanup.
    
    Args:
        db_path: Optional path to database file.
    
    Yields:
        sqlite3.Connection: Database connection object.
    
    Example:
        with connection() as conn:
            cursor = conn.execute("SELECT * FROM screens")
            rows = cursor.fetchall()
    """
    conn = None
    try:
        conn = get_connection(db_path)
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def init_database(db_path: Optional[Path] = None) -> bool:
    """
    Initialize the database with the schema.
    
    Creates all tables, indexes, and enum data if they don't exist.
    Safe to call multiple times (idempotent).
    
    Args:
        db_path: Optional path to database file.
    
    Returns:
        bool: True if initialization succeeded.
    
    Raises:
        FileNotFoundError: If schema.sql file not found.
        sqlite3.Error: If schema execution fails.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    schema_sql = SCHEMA_PATH.read_text()
    
    with connection(db_path) as conn:
        # Execute schema - SQLite handles IF NOT EXISTS for idempotency
        conn.executescript(schema_sql)
    
    return True


def reset_database(db_path: Optional[Path] = None) -> bool:
    """
    Drop all tables and recreate the database schema.
    
    WARNING: This destroys all data. Use only in development.
    
    Args:
        db_path: Optional path to database file.
    
    Returns:
        bool: True if reset succeeded.
    """
    path = db_path or DEFAULT_DB_PATH
    
    # Delete the database file entirely
    if path.exists():
        path.unlink()
    
    # Reinitialize with schema
    return init_database(db_path)


def get_schema_version(db_path: Optional[Path] = None) -> int:
    """
    Get the current schema version from the database.
    
    Args:
        db_path: Optional path to database file.
    
    Returns:
        int: Current schema version, or 0 if not initialized.
    """
    try:
        with connection(db_path) as conn:
            cursor = conn.execute(
                "SELECT MAX(version) as version FROM schema_version"
            )
            row = cursor.fetchone()
            return row["version"] if row and row["version"] else 0
    except sqlite3.OperationalError:
        # Table doesn't exist - database not initialized
        return 0


def is_database_initialized(db_path: Optional[Path] = None) -> bool:
    """
    Check if the database has been initialized with the schema.
    
    Args:
        db_path: Optional path to database file.
    
    Returns:
        bool: True if database is initialized.
    """
    return get_schema_version(db_path) > 0


def get_table_names(db_path: Optional[Path] = None) -> list[str]:
    """
    Get list of all table names in the database.
    
    Args:
        db_path: Optional path to database file.
    
    Returns:
        list[str]: List of table names.
    """
    with connection(db_path) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [row["name"] for row in cursor.fetchall()]


def get_table_count(db_path: Optional[Path] = None) -> int:
    """
    Get count of tables in the database (excluding sqlite internals).
    
    Args:
        db_path: Optional path to database file.
    
    Returns:
        int: Number of tables.
    """
    with connection(db_path) as conn:
        cursor = conn.execute(
            """SELECT COUNT(*) as count FROM sqlite_master 
               WHERE type='table' AND name NOT LIKE 'sqlite_%'"""
        )
        row = cursor.fetchone()
        return row["count"] if row else 0