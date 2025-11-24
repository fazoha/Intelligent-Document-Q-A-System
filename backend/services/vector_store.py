"""
Vector storage service using Upstash Vector DB.
"""

from typing import List, Dict, Any, Optional
from upstash_vector import Index
from models import ChunkMetadata
from utils import config, app_logger


class UpstashVectorStore:
    """Manage vector storage and retrieval using Upstash Vector DB."""
    
    def __init__(self):
        self.index = Index(
            url=config.UPSTASH_VECTOR_REST_URL,
            token=config.UPSTASH_VECTOR_REST_TOKEN
        )
        self.logger = app_logger
    
    def upsert_chunks(
        self,
        chunks: List[ChunkMetadata],
        embeddings: List[List[float]]
    ) -> None:
        """
        Upsert chunks with their embeddings to the vector store.
        
        Args:
            chunks: List of ChunkMetadata objects
            embeddings: Corresponding embedding vectors
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings"
            )
        
        # Prepare vectors for upsert
        # Format: (id, vector, metadata)
        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            vector_id = f"{chunk.doc_id}::{chunk.chunk_id}"
            metadata = chunk.to_vector_metadata()
            vectors.append((vector_id, embedding, metadata))
        
        # Batch upsert (Upstash supports up to 1000 vectors per request)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            
            try:
                self.index.upsert(vectors=batch)
                self.logger.info(
                    f"Upserted batch {i // batch_size + 1} "
                    f"({len(batch)} vectors)"
                )
            except Exception as e:
                self.logger.error(f"Failed to upsert batch: {e}")
                raise
        
        self.logger.info(f"Successfully upserted {len(vectors)} chunks to vector store")
    
    def query(
        self,
        query_embedding: List[float],
        top_k: int = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[ChunkMetadata]:
        """
        Query the vector store for similar chunks.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of ChunkMetadata objects sorted by similarity
        """
        top_k = top_k or config.TOP_K_CHUNKS
        
        try:
            query_kwargs = {
                "vector": query_embedding,
                "top_k": top_k,
                "include_metadata": True,
            }
            if filter_dict:
                query_kwargs["filter"] = filter_dict

            results = self.index.query(**query_kwargs)
            
            # Convert results to ChunkMetadata objects
            chunks = []
            for result in results:
                if hasattr(result, 'metadata') and result.metadata:
                    chunk = ChunkMetadata.from_vector_metadata(result.metadata)
                    chunks.append(chunk)
            
            self.logger.info(f"Retrieved {len(chunks)} chunks from vector store")
            
            return chunks
        
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            raise
    
    def delete_by_doc_id(self, doc_id: str) -> int:
        """
        Delete all chunks belonging to a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Number of chunks deleted
        """
        try:
            # Upstash Vector doesn't have a direct filter-based delete
            # We need to fetch all vectors with this doc_id and delete by ID
            # For Phase 1, we'll implement this as a placeholder
            # In production, you'd query all vectors, filter, and delete by IDs
            
            self.logger.warning(
                f"Delete by doc_id not fully implemented. "
                f"Requested deletion for doc_id: {doc_id}"
            )
            
            # TODO: Implement proper deletion logic
            # This would involve:
            # 1. Querying all vectors (pagination)
            # 2. Filtering by doc_id in metadata
            # 3. Deleting by vector IDs
            
            return 0
        
        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            raise
    
    def reset(self) -> None:
        """
        Reset the entire index (delete all vectors).
        WARNING: This deletes everything!
        """
        try:
            self.index.reset()
            self.logger.warning("Vector store has been reset (all vectors deleted)")
        
        except Exception as e:
            self.logger.error(f"Reset failed: {e}")
            raise
    
    def info(self) -> Dict[str, Any]:
        """Get information about the index."""
        try:
            info = self.index.info()
            return info
        except Exception as e:
            self.logger.error(f"Failed to get index info: {e}")
            return {}

