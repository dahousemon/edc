"""Main FastAPI application for Aurora EDC AI Assistant."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.database import init_db
from app.routers import (
    chat_router,
    leads_router,
    analytics_router,
    knowledge_router,
    properties_router,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    Aurora EDC AI Assistant - Helping businesses discover opportunities in Aurora, Colorado.

    ## Features
    - **Chat**: AI-powered conversation about Aurora business opportunities
    - **Properties**: Search available commercial/industrial properties
    - **Leads**: Capture and manage prospective business leads
    - **Knowledge Base**: Manage Aurora-specific information
    - **Analytics**: Track usage and performance metrics
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


# Health check endpoints
@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/health/detailed", tags=["health"])
async def detailed_health_check():
    """Detailed health check with service status."""
    from app.models.database import async_session
    from app.services.rag import get_rag_service

    # Check database
    db_status = "healthy"
    try:
        async with async_session() as session:
            await session.execute("SELECT 1")
    except Exception as e:
        db_status = f"unhealthy: {e}"

    # Check vector store
    vector_status = "healthy"
    try:
        rag = get_rag_service()
        stats = rag.get_collection_stats()
        vector_status = f"healthy ({stats['count']} documents)"
    except Exception as e:
        vector_status = f"unhealthy: {e}"

    return {
        "status": "healthy" if "healthy" in db_status and "healthy" in vector_status else "degraded",
        "version": settings.app_version,
        "environment": settings.environment,
        "services": {
            "database": db_status,
            "vector_store": vector_status,
        },
    }


# Include routers
app.include_router(chat_router)
app.include_router(leads_router)
app.include_router(analytics_router)
app.include_router(knowledge_router)
app.include_router(properties_router)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Aurora EDC AI Assistant API",
        "documentation": "/docs" if settings.debug else "Documentation disabled in production",
        "endpoints": {
            "chat": "/chat",
            "properties": "/properties",
            "leads": "/leads",
            "knowledge": "/knowledge",
            "analytics": "/analytics",
            "health": "/health",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
