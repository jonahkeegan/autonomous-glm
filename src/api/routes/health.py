"""
Health check endpoint for Autonomous-GLM API.

Provides system health status including database connectivity,
storage accessibility, and ffmpeg availability.
"""

from fastapi import APIRouter

from ..models import HealthCheckResponse, HealthStatus
from ..config import default_api_config

router = APIRouter(tags=["health"])


def check_database() -> tuple[bool, str]:
    """
    Check database connectivity.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        from ...db.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            return True, "ok"
        else:
            return False, "query returned unexpected result"
    except Exception as e:
        return False, str(e)


def check_storage() -> tuple[bool, str]:
    """
    Check storage directory accessibility.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        from pathlib import Path
        
        # Check required directories
        required_dirs = [
            "data/artifacts/screenshots",
            "data/artifacts/videos",
            "data/artifacts/context",
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            if not path.exists():
                return False, f"directory not found: {dir_path}"
            if not path.is_dir():
                return False, f"not a directory: {dir_path}"
            # Try to write a test file
            test_file = path / ".health_check"
            try:
                test_file.write_text("ok")
                test_file.unlink()
            except Exception as e:
                return False, f"cannot write to {dir_path}: {e}"
        
        return True, "ok"
    except Exception as e:
        return False, str(e)


def check_ffmpeg() -> tuple[bool, str]:
    """
    Check ffmpeg availability.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        from ...ingest.video_validators import check_ffmpeg_available
        
        if check_ffmpeg_available():
            return True, "ok"
        else:
            return False, "ffmpeg not available"
    except Exception as e:
        return False, str(e)


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check the health status of the API and its dependencies",
)
async def health_check() -> HealthCheckResponse:
    """
    Perform health check on all system components.
    
    Checks:
    - Database connectivity
    - Storage directory accessibility
    - ffmpeg availability for video processing
    
    Returns overall health status:
    - healthy: All checks pass
    - degraded: Some non-critical checks fail (ffmpeg)
    - unhealthy: Critical checks fail (database, storage)
    """
    checks: dict[str, str] = {}
    has_critical_failure = False
    has_degraded = False
    
    # Check database (critical)
    db_ok, db_msg = check_database()
    checks["database"] = "ok" if db_ok else f"error: {db_msg}"
    if not db_ok:
        has_critical_failure = True
    
    # Check storage (critical)
    storage_ok, storage_msg = check_storage()
    checks["storage"] = "ok" if storage_ok else f"error: {storage_msg}"
    if not storage_ok:
        has_critical_failure = True
    
    # Check ffmpeg (non-critical, degraded if unavailable)
    ffmpeg_ok, ffmpeg_msg = check_ffmpeg()
    checks["ffmpeg"] = "ok" if ffmpeg_ok else f"warning: {ffmpeg_msg}"
    if not ffmpeg_ok:
        has_degraded = True
    
    # Determine overall status
    if has_critical_failure:
        status = HealthStatus.UNHEALTHY
    elif has_degraded:
        status = HealthStatus.DEGRADED
    else:
        status = HealthStatus.HEALTHY
    
    return HealthCheckResponse(
        status=status,
        version=default_api_config.version,
        checks=checks,
    )