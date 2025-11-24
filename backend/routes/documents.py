"""
Document upload and management endpoints.
"""

import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from typing import List, Dict, Any
from datetime import datetime

from models import Document
from services import (
    UnstructuredParser,
    ChunkBuilder,
    OpenAIEmbedder,
    UpstashVectorStore
)
from utils import config, app_logger

router = APIRouter(prefix="/api/documents", tags=["documents"])

# In-memory document store (for Phase 1)
# In production, this would be a database
document_store: Dict[str, Document] = {}

# Directory containing sample documents
# Assuming sample-docs is in the project root, one level up from backend/routes/
SAMPLE_DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../sample-docs"))


def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file.
    
    Raises:
        HTTPException: If file is invalid
    """
    # Check file extension
    filename = file.filename or ""
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Only {', '.join(config.ALLOWED_EXTENSIONS)} allowed."
        )
    
    # Check file size (rough estimate from content_type if available)
    # Note: Actual size check would require reading the file
    # For now, we'll do a simple validation
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )


def get_file_type(filename: str) -> str:
    """Determine file type from extension."""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == ".pdf":
        return "pdf"
    elif ext in [".png", ".jpg", ".jpeg"]:
        return "image"
    elif ext == ".docx":
        return "docx"
    else:
        return "unknown"


async def _process_document_file(file_path: str, filename: str) -> Dict[str, Any]:
    """
    Internal helper to process a document file from a path.
    """
    logger = app_logger
    
    # Create document record
    doc = Document(
        filename=filename,
        file_type=get_file_type(filename),
        status="processing"
    )
    document_store[doc.doc_id] = doc
    
    try:
        # Parse document
        parser = UnstructuredParser()
        # Note: we use the file_path directly here. 
        # If it's an upload, it should be the temp path.
        # If it's a sample, it should be the sample path.
        elements = parser.parse(file_path)
        
        if not elements:
            raise Exception("No content extracted from document")
        
        # Build chunks
        chunk_builder = ChunkBuilder()
        chunks = chunk_builder.build_chunks(
            elements=elements,
            doc_id=doc.doc_id,
            doc_name=doc.filename,
            parser=parser
        )
        
        if not chunks:
            raise Exception("No chunks created from document")
        
        # Update document with chunk count and page count
        doc.chunk_count = len(chunks)
        # Estimate page count from max page number in chunks
        doc.page_count = max((chunk.page for chunk in chunks), default=1)
        
        # Generate embeddings
        embedder = OpenAIEmbedder()
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = embedder.embed_batch(chunk_texts)
        
        # Store in vector DB (semantic embeddings)
        vector_store = UpstashVectorStore()
        vector_store.upsert_chunks(chunks, embeddings)
        
        logger.info(f"Successfully indexed {len(chunks)} chunks in vector store")
        
        # Update document status
        doc.status = "indexed"
        document_store[doc.doc_id] = doc
        
        logger.info(
            f"Successfully indexed document {doc.filename}: "
            f"{doc.chunk_count} chunks, {doc.page_count} pages"
        )
        
        return {
            "doc_id": doc.doc_id,
            "filename": doc.filename,
            "page_count": doc.page_count,
            "chunk_count": doc.chunk_count,
            "status": doc.status,
            "uploaded_at": doc.uploaded_at.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        
        # Update document status to failed
        doc.status = "failed"
        doc.error_message = str(e)
        document_store[doc.doc_id] = doc
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload and process a document.
    """
    logger = app_logger
    logger.info(f"Received upload request for file: {file.filename}")
    
    # Validate file
    validate_file(file)
    
    temp_file_path = None
    
    try:
        # Create doc_id early just for temp filename (will be created properly in _process_document_file too but that's ok)
        # Actually, _process_document_file creates a NEW Document instance with a new ID.
        # To avoid double ID generation or issues, we can't easily pass the ID in without changing the helper signature.
        # BUT, since _process_document_file is the one that records it in document_store, we should rely on THAT ID.
        # We just need a temp filename here.
        
        import uuid
        temp_id = str(uuid.uuid4())
        temp_dir = config.get_temp_upload_dir()
        temp_file_path = os.path.join(temp_dir, f"{temp_id}_{file.filename}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved file temporarily to: {temp_file_path}")
        
        # Process the file
        return await _process_document_file(temp_file_path, file.filename or "unknown")

    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


@router.get("/samples")
async def list_sample_documents() -> Dict[str, List[str]]:
    """List available sample documents."""
    try:
        if not os.path.exists(SAMPLE_DOCS_DIR):
            app_logger.warning(f"Sample directory not found: {SAMPLE_DOCS_DIR}")
            return {"samples": []}
            
        samples = [
            f for f in os.listdir(SAMPLE_DOCS_DIR) 
            if os.path.isfile(os.path.join(SAMPLE_DOCS_DIR, f)) and 
            os.path.splitext(f)[1].lower() in config.ALLOWED_EXTENSIONS
        ]
        samples.sort()
        return {"samples": samples}
    except Exception as e:
        app_logger.error(f"Error listing samples: {e}")
        return {"samples": []}


@router.post("/samples/load")
async def load_sample_document(payload: Dict[str, str] = Body(...)) -> Dict[str, Any]:
    """Load and process a sample document."""
    filename = payload.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Filename required")
        
    file_path = os.path.join(SAMPLE_DOCS_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample document not found")
        
    app_logger.info(f"Loading sample document: {filename}")
    return await _process_document_file(file_path, filename)


@router.get("")
async def list_documents() -> Dict[str, List[Dict[str, Any]]]:
    """List all uploaded documents."""
    documents = []
    
    for doc in document_store.values():
        documents.append({
            "doc_id": doc.doc_id,
            "filename": doc.filename,
            "page_count": doc.page_count,
            "chunk_count": doc.chunk_count,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "status": doc.status
        })
    
    # Sort by upload time (most recent first)
    documents.sort(key=lambda x: x["uploaded_at"], reverse=True)
    
    return {"documents": documents}


@router.delete("/clear")
async def clear_all_documents() -> Dict[str, Any]:
    """Clear all documents and reset the vector store."""
    try:
        # Reset vector store
        vector_store = UpstashVectorStore()
        vector_store.reset()
        
        # Get count before clearing
        deleted_count = len(document_store)
        
        # Clear in-memory store
        document_store.clear()
        
        app_logger.warning("All documents cleared from the system")
        
        return {
            "message": "All documents and embeddings cleared",
            "deleted_count": deleted_count
        }
    
    except Exception as e:
        app_logger.error(f"Error clearing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear documents: {str(e)}"
        )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str) -> Dict[str, str]:
    """Delete a specific document."""
    if doc_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = document_store[doc_id]
    
    try:
        # Delete from vector store
        vector_store = UpstashVectorStore()
        deleted_count = vector_store.delete_by_doc_id(doc_id)
        
        # Remove from in-memory store
        del document_store[doc_id]
        
        app_logger.info(f"Deleted document {doc.filename} (ID: {doc_id})")
        
        return {
            "message": f"Document {doc.filename} deleted successfully",
            "deleted_chunks": deleted_count
        }
    
    except Exception as e:
        app_logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )
