"""
CLI module for autonomous-glm.

Provides command-line interface for triggering audits, viewing reports,
and managing design system proposals.
"""

from .main import main, cli
from .errors import (
    CLIError,
    ArtifactNotFoundError,
    AuditFailedError,
    ConfigurationError,
    InvalidArgumentsError,
)

__all__ = [
    "main",
    "cli",
    "CLIError",
    "ArtifactNotFoundError",
    "AuditFailedError",
    "ConfigurationError",
    "InvalidArgumentsError",
]