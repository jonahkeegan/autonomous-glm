"""
Custom exceptions for Autonomous-GLM API.

Implements RFC 7807 Problem Details format for standardized error responses.
"""

from typing import Any, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class ProblemDetail(HTTPException):
    """
    RFC 7807 Problem Details exception.
    
    Provides standardized error responses with:
    - type: URI reference identifying the error type
    - title: Short human-readable summary
    - status: HTTP status code
    - detail: Human-readable explanation specific to this occurrence
    - instance: URI reference to the specific occurrence
    """
    
    def __init__(
        self,
        type_uri: str,
        title: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: Optional[str] = None,
        instance: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        **extra: Any
    ):
        self.type_uri = type_uri
        self.title = title
        self.detail = detail
        self.instance = instance
        self.extra = extra
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class ValidationError(ProblemDetail):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        detail: str,
        instance: Optional[str] = None,
        field: Optional[str] = None
    ):
        extra = {}
        if field:
            extra["field"] = field
        super().__init__(
            type_uri="https://autonomous-glm.local/errors/validation",
            title="Validation Error",
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            instance=instance,
            **extra
        )


class FileNotFoundError(ProblemDetail):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        detail: str = "Resource not found",
        instance: Optional[str] = None
    ):
        super().__init__(
            type_uri="https://autonomous-glm.local/errors/not-found",
            title="Not Found",
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            instance=instance
        )


class UnsupportedMediaTypeError(ProblemDetail):
    """Raised when the uploaded file type is not supported."""
    
    def __init__(
        self,
        detail: str,
        instance: Optional[str] = None,
        supported_types: Optional[list[str]] = None
    ):
        extra = {}
        if supported_types:
            extra["supported_types"] = supported_types
        super().__init__(
            type_uri="https://autonomous-glm.local/errors/unsupported-media-type",
            title="Unsupported Media Type",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=detail,
            instance=instance,
            **extra
        )


class FileTooLargeError(ProblemDetail):
    """Raised when the uploaded file exceeds size limits."""
    
    def __init__(
        self,
        detail: str,
        instance: Optional[str] = None,
        max_size_mb: Optional[int] = None
    ):
        extra = {}
        if max_size_mb:
            extra["max_size_mb"] = max_size_mb
        super().__init__(
            type_uri="https://autonomous-glm.local/errors/file-too-large",
            title="File Too Large",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=detail,
            instance=instance,
            **extra
        )


class IngestionError(ProblemDetail):
    """Raised when file ingestion fails."""
    
    def __init__(
        self,
        detail: str,
        instance: Optional[str] = None,
        reason: Optional[str] = None
    ):
        extra = {}
        if reason:
            extra["reason"] = reason
        super().__init__(
            type_uri="https://autonomous-glm.local/errors/ingestion",
            title="Ingestion Error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            instance=instance,
            **extra
        )


class ServiceUnavailableError(ProblemDetail):
    """Raised when a required service is unavailable."""
    
    def __init__(
        self,
        detail: str,
        instance: Optional[str] = None,
        service: Optional[str] = None
    ):
        extra = {}
        if service:
            extra["service"] = service
        super().__init__(
            type_uri="https://autonomous-glm.local/errors/service-unavailable",
            title="Service Unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            instance=instance,
            **extra
        )


async def problem_detail_handler(
    request: Request,
    exc: ProblemDetail
) -> JSONResponse:
    """
    Exception handler for ProblemDetail exceptions.
    
    Converts ProblemDetail to RFC 7807 JSON response.
    """
    content = {
        "type": exc.type_uri,
        "title": exc.title,
        "status": exc.status_code,
        "detail": exc.detail,
    }
    
    if exc.instance:
        content["instance"] = exc.instance
    
    if exc.extra:
        content.update(exc.extra)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers
    )