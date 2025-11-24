"""
Main FastAPI application entry point.
Intelligent Document Q&A System - Phase 2

NOTE: This system does NOT preserve document history across restarts.
All uploaded documents and their indexes are cleared when the backend starts.
This is intentional to maintain a clean state and avoid stale data.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

from utils import config, app_logger
from services import UpstashVectorStore
from routes.documents import document_store

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


@app.on_event("startup")
async def clear_vector_stores_on_startup():
    """
    Clear all vector stores on startup to ensure clean state.
    
    This system does NOT preserve document history across restarts.
    All data is cleared when the backend starts to avoid:
    - Stale data from previous sessions
    - Orphaned vectors in cloud storage
    - Confusion between in-memory state and persistent storage
    
    Users must re-upload documents after each backend restart.
    
    Pure NLP approach - no external databases (Elasticsearch removed).
    """
    logger = app_logger
    
    # Check if document store is already empty (fresh start)
    if len(document_store) == 0:
        logger.warning("=" * 70)
        logger.warning("STARTUP: document_store is empty - clearing vector store")
        logger.warning("All previous documents will be removed from vector database")
        logger.warning("This is intentional behavior to maintain clean state")
        logger.warning("=" * 70)
        
        try:
            # Clear Upstash Vector DB
            vector_store = UpstashVectorStore()
            vector_store.reset()
            logger.info("✓ Upstash Vector DB cleared")
            
            logger.warning("=" * 70)
            logger.warning("STARTUP COMPLETE: System ready with clean state")
            logger.warning("Pure NLP approach: Dense embeddings + YAKE keywords + Neural reranking")
            logger.warning("Please upload documents to begin querying")
            logger.warning("=" * 70)
            
        except Exception as e:
            logger.error(f"Failed to clear vector store on startup: {e}")
            logger.warning("Continuing anyway - you may need to manually clear old data")
    else:
        logger.info(f"Resuming with {len(document_store)} documents in memory")


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Intelligent Document Q&A API",
        "version": "2.0.0"
    }
