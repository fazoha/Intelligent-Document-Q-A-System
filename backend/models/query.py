"""
Query request and response models.
"""

from pydantic import BaseModel, Field
from typing import List


class QueryRequest(BaseModel):
    """Request model for document queries."""
    
    query: str = Field(..., min_length=1, description="Natural language question")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the termination clause in the employment contract?"
            }
        }


class Citation(BaseModel):
    """Citation information for an answer."""
    
    chunk_id: str
    text: str
    page: int
    bbox: List[float] = Field(default_factory=list)
    doc_name: str
    block_type: str = "paragraph"
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_23",
                "text": "Either party may terminate this agreement by providing...",
                "page": 5,
                "bbox": [100.0, 200.0, 500.0, 250.0],
                "doc_name": "employment_contract.pdf",
                "block_type": "paragraph"
            }
        }


class QueryResponse(BaseModel):
    """Response model for document queries."""
    
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    query_time_ms: int = 0
    retrieved_chunks: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The termination clause [chunk_23] states that either party may terminate with 30 days written notice [chunk_24].",
                "citations": [
                    {
                        "chunk_id": "chunk_23",
                        "text": "Either party may terminate this agreement by providing...",
                        "page": 5,
                        "bbox": [100.0, 200.0, 500.0, 250.0],
                        "doc_name": "employment_contract.pdf",
                        "block_type": "paragraph"
                    }
                ],
                "query_time_ms": 3421,
                "retrieved_chunks": 5
            }
        }

