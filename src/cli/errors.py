"""
CLI-specific exceptions for autonomous-glm.

Defines exit codes and exception classes for CLI error handling.
"""

from typing import Optional


# =============================================================================
# EXIT CODES
# =============================================================================

class ExitCode:
    """Semantic exit codes for CLI commands."""
    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGUMENTS = 2
    ARTIFACT_NOT_FOUND = 3
    AUDIT_FAILED = 4
    CONFIGURATION_ERROR = 5


# =============================================================================
# BASE EXCEPTION
# =============================================================================

class CLIError(Exception):
    """Base exception for CLI errors.
    
    Attributes:
        message: Human-readable error message
        exit_code: Exit code to return when this error occurs
        details: Optional additional details for debugging
    """
    
    def __init__(
        self,
        message: str,
        exit_code: int = ExitCode.GENERAL_ERROR,
        details: Optional[str] = None,
    ):
        self.message = message
        self.exit_code = exit_code
        self.details = details
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


# =============================================================================
# SPECIFIC EXCEPTIONS
# =============================================================================

class InvalidArgumentsError(CLIError):
    """Raised when command arguments are invalid."""
    
    def __init__(
        self,
        message: str,
        details: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            exit_code=ExitCode.INVALID_ARGUMENTS,
            details=details,
        )


class ArtifactNotFoundError(CLIError):
    """Raised when a requested artifact (screen, flow) is not found."""
    
    def __init__(
        self,
        artifact_type: str,
        artifact_id: str,
        details: Optional[str] = None,
    ):
        message = f"{artifact_type} not found: {artifact_id}"
        super().__init__(
            message=message,
            exit_code=ExitCode.ARTIFACT_NOT_FOUND,
            details=details,
        )
        self.artifact_type = artifact_type
        self.artifact_id = artifact_id


class AuditFailedError(CLIError):
    """Raised when an audit operation fails."""
    
    def __init__(
        self,
        message: str,
        screen_id: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            exit_code=ExitCode.AUDIT_FAILED,
            details=details,
        )
        self.screen_id = screen_id


class ConfigurationError(CLIError):
    """Raised when there's a configuration problem."""
    
    def __init__(
        self,
        message: str,
        config_path: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            exit_code=ExitCode.CONFIGURATION_ERROR,
            details=details,
        )
        self.config_path = config_path


class ReportNotFoundError(CLIError):
    """Raised when a requested report is not found."""
    
    def __init__(
        self,
        audit_id: str,
        details: Optional[str] = None,
    ):
        message = f"Report not found for audit: {audit_id}"
        super().__init__(
            message=message,
            exit_code=ExitCode.ARTIFACT_NOT_FOUND,
            details=details,
        )
        self.audit_id = audit_id


class ProposalNotFoundError(CLIError):
    """Raised when a requested proposal is not found."""
    
    def __init__(
        self,
        proposal_id: str,
        details: Optional[str] = None,
    ):
        message = f"Proposal not found: {proposal_id}"
        super().__init__(
            message=message,
            exit_code=ExitCode.ARTIFACT_NOT_FOUND,
            details=details,
        )
        self.proposal_id = proposal_id