"""
Cross-encoder reranking service for improving retrieval precision.
Uses a transformer model to rerank initial retrieval results.
"""

from typing import List, Dict, Any, Tuple
from sentence_transformers import CrossEncoder
from models import ChunkMetadata
from utils import config, app_logger


class CrossEncoderReranker:
    """Rerank retrieved chunks using a cross-encoder model."""
    
    def __init__(self):
        self.model_name = config.RERANK_MODEL
        self.logger = app_logger
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the cross-encoder model."""
        try:
            self.model = CrossEncoder(self.model_name, max_length=512)
            self.logger.info(f"Loaded cross-encoder model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load cross-encoder model: {e}")
            self.model = None
    
    def rerank(
        self,
        query: str,
        chunks: List[ChunkMetadata],
        top_k: int = None
    ) -> List[Tuple[ChunkMetadata, float]]:
        """
        Rerank chunks using cross-encoder.
        
        Args:
            query: User query
            chunks: List of candidate chunks to rerank
            top_k: Number of top results to return
            
        Returns:
            List of (chunk, rerank_score) tuples sorted by score descending
        """
        if not self.model:
            self.logger.warning("Cross-encoder model not loaded - returning chunks without reranking")
            return [(chunk, 0.0) for chunk in chunks]
        
        if not chunks:
            return []
        
        top_k = top_k or config.FINAL_TOP_K
        
        try:
            # Prepare query-text pairs for the cross-encoder
            pairs = [(query, chunk.text) for chunk in chunks]
            
            # Compute relevance scores
            # Cross-encoder returns relevance scores (higher is better)
            scores = self.model.predict(pairs)
            
            # Combine chunks with scores
            chunk_score_pairs = list(zip(chunks, scores))
            
            # Sort by score descending
            chunk_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            # Return top_k results
            reranked = chunk_score_pairs[:top_k]
            
            self.logger.info(
                f"Reranked {len(chunks)} chunks, returning top {len(reranked)}. "
                f"Score range: [{reranked[-1][1]:.4f}, {reranked[0][1]:.4f}]"
            )
            
            return reranked
        
        except Exception as e:
            self.logger.error(f"Reranking failed: {e}")
            # Fallback: return original chunks without reranking
            return [(chunk, 0.0) for chunk in chunks[:top_k]]
    
    def rerank_from_dicts(
        self,
        query: str,
        chunk_dicts: List[Dict[str, Any]],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks provided as dictionaries.
        
        Args:
            query: User query
            chunk_dicts: List of chunk dictionaries with 'text' field
            top_k: Number of top results to return
            
        Returns:
            List of chunk dictionaries with added 'rerank_score' field, sorted by score
        """
        if not self.model or not chunk_dicts:
            return chunk_dicts[:top_k] if top_k else chunk_dicts
        
        top_k = top_k or config.FINAL_TOP_K
        
        try:
            # Prepare query-text pairs
            pairs = [(query, chunk_dict.get('text', '')) for chunk_dict in chunk_dicts]
            
            # Compute relevance scores
            scores = self.model.predict(pairs)
            
            # Add scores to dictionaries
            for chunk_dict, score in zip(chunk_dicts, scores):
                chunk_dict['rerank_score'] = float(score)
            
            # Sort by rerank score descending
            chunk_dicts.sort(key=lambda x: x.get('rerank_score', 0.0), reverse=True)
            
            # Return top_k results
            reranked = chunk_dicts[:top_k]
            
            self.logger.info(
                f"Reranked {len(chunk_dicts)} chunk dicts, returning top {len(reranked)}"
            )
            
            return reranked
        
        except Exception as e:
            self.logger.error(f"Reranking from dicts failed: {e}")
            return chunk_dicts[:top_k]
    
    def is_available(self) -> bool:
        """Check if the reranker model is available."""
        return self.model is not None

