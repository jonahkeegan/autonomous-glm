"""
API routes for Autonomous-GLM.
"""

from .health import router as health_router
from .ingest import router as ingest_router

__all__ = [
    "health_router",
    "ingest_router",
]