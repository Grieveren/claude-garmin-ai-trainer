"""
AI-Powered Training Optimization System - Main Application.

This is the FastAPI entry point for the training optimizer application.
It sets up the web server, routes, middleware, and static file serving.
"""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from app.core.config import settings
from app.core.logger import log_request, log_response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting AI-Powered Training Optimization System")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Host: {settings.app_host}:{settings.app_port}")

    # Ensure required directories exist
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application")


# Initialize FastAPI application
app = FastAPI(
    title="AI-Powered Training Optimization System",
    description=(
        "An intelligent training analysis system that syncs with Garmin Connect, "
        "analyzes your training data using Claude AI, and provides personalized "
        "training recommendations."
    ),
    version="0.1.0",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS Middleware - Configure for your frontend if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware for tracking
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    Add unique request ID to each request for tracking.

    Args:
        request: The incoming request
        call_next: The next middleware/route handler

    Returns:
        Response with request ID header
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Log request
    log_request(request_id, request.method, request.url.path)

    # Process request
    import time
    start_time = time.time()

    response = await call_next(request)

    # Log response
    duration_ms = (time.time() - start_time) * 1000
    log_response(request_id, response.status_code, duration_ms)

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


# Mount static files
static_path = settings.static_dir
if static_path.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(static_path)),
        name="static"
    )
    logger.info(f"Static files mounted from {static_path}")

# Setup Jinja2 templates
templates_path = settings.templates_dir
templates = Jinja2Templates(directory=str(templates_path))
logger.info(f"Templates configured from {templates_path}")


# Health check endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """
    Root endpoint - Health check and basic info.

    Returns:
        HTML response with application status
    """
    return templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "app_name": "AI-Powered Training Optimization System",
            "version": "0.1.0",
            "status": "healthy"
        }
    )


@app.get("/health", response_class=JSONResponse)
async def health_check() -> JSONResponse:
    """
    Health check endpoint for monitoring.

    Returns:
        JSON response with application health status
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "version": "0.1.0",
            "debug": settings.debug,
        }
    )


@app.get("/api/info", response_class=JSONResponse)
async def api_info() -> JSONResponse:
    """
    API information endpoint.

    Returns:
        JSON response with API configuration
    """
    return JSONResponse(
        content={
            "application": "AI-Powered Training Optimization System",
            "version": "0.1.0",
            "ai_model": settings.ai_model,
            "training_goal": settings.training_goal,
            "athlete": settings.athlete_name,
            "endpoints": {
                "health": "/health",
                "docs": "/api/docs" if settings.debug else None,
                "activities": "/api/activities (coming soon)",
                "analysis": "/api/analysis (coming soon)",
                "recommendations": "/api/recommendations (coming soon)",
            }
        }
    )


# Include routers (placeholders for now)
# from app.routers import activities, analysis, recommendations
# app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
# app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
# app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting uvicorn server")
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
