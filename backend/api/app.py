"""
FastAPI application for IRA Workflow Builder.

This module sets up the FastAPI application with all routes, middleware,
and configuration for the IRA Workflow Builder backend.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.utils.config import get_config
from backend.api.routes import workflows, websockets
from backend.api.models.responses import ErrorResponse

logger = get_logger(__name__)
config = get_config()


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 80)
    logger.info("IRA WORKFLOW BUILDER API STARTING")
    logger.info("=" * 80)
    logger.info(f"Environment: {config.environment}")

    # Show LLM provider information (phase-specific)
    logger.info("LLM Configuration:")
    logger.info(f"  📋 Planning Phase: {config.planner_provider.upper()}")
    if config.planner_provider == 'openai':
        logger.info(f"     Model: {config.openai_model}")
    else:
        logger.info(f"     Model: {config.groq_model}")

    logger.info(f"  💻 Coding Phase: {config.coder_provider.upper()}")
    if config.coder_provider == 'openai':
        logger.info(f"     Model: {config.openai_model}")
    else:
        logger.info(f"     Model: {config.groq_model}")

    logger.info(f"  🎯 Intent Agent: {config.intent_agent_provider.upper()}")
    logger.info(f"     Model: {config.intent_agent_model}")

    # Show hybrid mode status
    if config.planner_provider != config.coder_provider or config.intent_agent_provider != config.planner_provider:
        logger.info("  🔄 Hybrid Mode: ENABLED")

    logger.info(f"CORS Origins: {config.cors_origins}")

    # Create necessary directories
    from pathlib import Path
    Path("./storage/workflows").mkdir(parents=True, exist_ok=True)
    Path("./storage/generated_code").mkdir(parents=True, exist_ok=True)
    Path("./data/uploads").mkdir(parents=True, exist_ok=True)
    Path("./data/output").mkdir(parents=True, exist_ok=True)

    logger.info("Storage directories initialized")
    logger.info("API ready to accept requests")

    yield

    # Shutdown
    logger.info("=" * 80)
    logger.info("IRA WORKFLOW BUILDER API SHUTTING DOWN")
    logger.info("=" * 80)


# Create FastAPI application
app = FastAPI(
    title="IRA Workflow Builder API",
    description="Backend API for the IRA (Intelligent Requirements Analyzer) Workflow Builder",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add a unique request ID to each request for tracking."""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        f"Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown"
        }
    )

    response = await call_next(request)

    logger.info(
        f"Request completed",
        extra={
            "request_id": request_id,
            "status_code": response.status_code,
        }
    )

    return response


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        f"HTTP error occurred",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail or "HTTP error",
            code=f"HTTP_{exc.status_code}"
        ).model_dump(),
        headers={"X-Request-ID": request_id}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")

    errors = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")

    error_detail = "; ".join(errors)

    logger.error(
        f"Validation error",
        extra={
            "request_id": request_id,
            "errors": error_detail,
        }
    )

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation error",
            detail=error_detail,
            code="VALIDATION_ERROR"
        ).model_dump(),
        headers={"X-Request-ID": request_id}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        f"Unhandled exception",
        extra={
            "request_id": request_id,
            "error": str(exc),
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if config.environment == "development" else "An unexpected error occurred",
            code="INTERNAL_ERROR"
        ).model_dump(),
        headers={"X-Request-ID": request_id}
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "IRA Workflow Builder API",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "IRA Workflow Builder API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


# Include routers
app.include_router(workflows.router, prefix="/api/v1", tags=["Workflows"])
app.include_router(websockets.router, prefix="/ws", tags=["WebSockets"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "ira_builder.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
