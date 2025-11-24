"""
Main FastAPI application entry point.
Intelligent Document Q&A System - Phase 1
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

from utils import config, app_logger

# Validate configuration on startup
try:
    config.validate()
    app_logger.info("Configuration validated successfully")
except ValueError as e:
    app_logger.warning(f"Configuration validation warning: {e}")
    app_logger.warning("Some features may not work without proper API keys")

# Initialize FastAPI app
app = FastAPI(
    title="Intelligent Document Q&A API",
    description="NLP-powered document question-answering system with layout-aware parsing",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from routes import documents_router, query_router
app.include_router(documents_router)
app.include_router(query_router)


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Intelligent Document Q&A API",
        "version": "1.0.0"
    }
