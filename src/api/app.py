"""
FastAPI application for Autonomous-GLM API.

Main application module with router registration, middleware,
exception handlers, and OpenAPI configuration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import APIConfig, default_api_config
from .exceptions import ProblemDetail, problem_detail_handler
from .routes import health_router, ingest_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan handler.
    
    Handles startup and shutdown events.
    """
    # Startup: Initialize database and verify directories
    from ..db.database import init_database
    from ..config import get_config
    
    config = get_config()
    init_database()
    
    # Ensure storage directories exist
    from pathlib import Path
    Path(config.paths.screenshots_dir).mkdir(parents=True, exist_ok=True)
    Path(config.paths.videos_dir).mkdir(parents=True, exist_ok=True)
    Path(config.paths.context_dir).mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown: Cleanup if needed
    pass


def create_app(config: APIConfig = default_api_config) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        config: API configuration
        
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=config.title,
        description=config.description,
        version=config.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=config.cors_allow_methods,
        allow_headers=config.cors_allow_headers,
    )
    
    # Register exception handlers
    app.add_exception_handler(ProblemDetail, problem_detail_handler)
    
    # Register routers
    # Health check is at root level (no prefix)
    app.include_router(health_router)
    
    # Ingestion endpoints are under API prefix
    app.include_router(
        ingest_router,
        prefix=config.api_prefix,
    )
    
    return app


# Create default app instance
app = create_app()