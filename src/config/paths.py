"""
Path resolution utilities for configuration.

Provides utilities for resolving relative/absolute paths and finding project root.
"""

import os
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """
    Find the project root directory.
    
    Searches upward from the current file for a directory containing
    key project markers (pyproject.toml, .git, or requirements.txt).
    
    Returns:
        Path: The project root directory.
    
    Raises:
        RuntimeError: If project root cannot be determined.
    """
    # Start from the current file's directory
    current = Path(__file__).resolve()
    
    # Marker files/directories that indicate project root
    markers = ["pyproject.toml", ".git", "requirements.txt", "setup.py"]
    
    # Search upward through parent directories
    for parent in current.parents:
        for marker in markers:
            if (parent / marker).exists():
                return parent
    
    # Fallback: assume src/config is 2 levels below root
    # This works for the standard project structure
    fallback = current.parents[2]  # src/config -> src -> root
    if (fallback / "config").exists():
        return fallback
    
    raise RuntimeError(
        "Could not determine project root. "
        "Ensure you're running from within the project directory."
    )


def resolve_path(path: str, base: Optional[Path] = None) -> Path:
    """
    Resolve a path string to an absolute Path.
    
    Handles both relative and absolute paths. Relative paths are resolved
    from the project root (or a custom base if provided).
    
    Args:
        path: The path string to resolve.
        base: Optional base directory for relative paths. 
              Defaults to project root.
    
    Returns:
        Path: The resolved absolute path.
    
    Examples:
        >>> resolve_path("./data/db.sqlite")
        PosixPath('/path/to/project/data/db.sqlite')
        
        >>> resolve_path("/absolute/path")
        PosixPath('/absolute/path')
    """
    path_obj = Path(path)
    
    # Already absolute
    if path_obj.is_absolute():
        return path_obj
    
    # Resolve relative to base or project root
    base_dir = base or get_project_root()
    return (base_dir / path_obj).resolve()


def ensure_dir(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: The directory path to ensure exists.
    
    Returns:
        Path: The same path (for chaining).
    
    Raises:
        OSError: If directory creation fails.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_default_config_dir() -> Path:
    """
    Get the default configuration directory path.
    
    Returns:
        Path: Path to the config directory.
    """
    return get_project_root() / "config"


def get_default_data_dir() -> Path:
    """
    Get the default data directory path.
    
    Returns:
        Path: Path to the data directory.
    """
    return get_project_root() / "data"


def get_output_dir() -> Path:
    """
    Get the default output directory path.
    
    Returns:
        Path: Path to the output directory.
    """
    return get_project_root() / "output"
