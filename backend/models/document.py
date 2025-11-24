"""
Document and chunk data models.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
import json


class Document(BaseModel):
    """Represents an uploaded document."""
    
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: str  # "pdf", "image", "docx"
    page_count: int = 0
    chunk_count: int = 0
    uploaded_at: datetime = Field(default_factory=datetime.now)
    status: str = "processing"  # "processing", "indexed", "failed"
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "contract.pdf",
                "file_type": "pdf",
                "page_count": 12,
                "chunk_count": 47,
                "uploaded_at": "2026-01-15T10:30:00Z",
                "status": "indexed"
            }
        }


class ChunkMetadata(BaseModel):
    """Represents a document chunk with layout metadata."""
    
    doc_id: str
    chunk_id: str  # e.g., "chunk_0", "chunk_1"
    text: str  # raw chunk text
    page: int
    bbox: List[float] = Field(default_factory=list)  # [x1, y1, x2, y2]
    block_type: str = "paragraph"  # "paragraph", "table", "heading", "caption", "footer"
    section_heading: Optional[str] = None
    doc_name: str  # original filename for citation display
    token_count: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "550e8400-e29b-41d4-a716-446655440000",
                "chunk_id": "chunk_23",
                "text": "Either party may terminate this agreement...",
                "page": 5,
                "bbox": [100.0, 200.0, 500.0, 250.0],
                "block_type": "paragraph",
                "section_heading": "Section 3: Termination",
                "doc_name": "contract.pdf",
                "token_count": 45
            }
        }
    
    def to_vector_metadata(self) -> dict:
        """Convert to metadata dict for vector storage."""
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "page": str(self.page),
            "bbox": json.dumps(self.bbox),
            "block_type": self.block_type,
            "section_heading": self.section_heading or "",
            "doc_name": self.doc_name,
            "token_count": str(self.token_count),
        }
    
    @classmethod
    def from_vector_metadata(cls, metadata: dict) -> "ChunkMetadata":
        """Create ChunkMetadata from vector store metadata."""
        bbox_val = metadata.get("bbox", "[]")
        if isinstance(bbox_val, str):
            try:
                bbox_parsed = json.loads(bbox_val)
            except json.JSONDecodeError:
                bbox_parsed = []
        else:
            bbox_parsed = bbox_val or []

        return cls(
            doc_id=metadata.get("doc_id", ""),
            chunk_id=metadata.get("chunk_id", ""),
            text=metadata.get("text", ""),
            page=int(metadata.get("page", 0)),
            bbox=bbox_parsed,
            block_type=metadata.get("block_type", "paragraph"),
            section_heading=metadata.get("section_heading"),
            doc_name=metadata.get("doc_name", ""),
            token_count=int(metadata.get("token_count", 0)),
        )

