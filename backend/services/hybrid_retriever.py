"""
Hybrid retrieval service combining dense embeddings and keyword matching.
Implements weighted score fusion for improved retrieval accuracy.

Pure NLP approach - no external databases required (Elasticsearch removed).
"""

from typing import List, Dict, Any, Optional
from models import ChunkMetadata
from services import (
    OpenAIEmbedder,
    UpstashVectorStore,
    YAKEKeywordService,
    CrossEncoderReranker
)
from utils import config, app_logger


class HybridRetriever:
    """
    Combine multiple NLP retrieval strategies for robust document search.
    
    Implements:
    1. Dense retrieval (semantic embeddings via OpenAI)
    2. YAKE keyword matching (unsupervised keyword extraction)
    3. Cross-encoder reranking (neural reranking)
    
    This is a pure NLP approach without external databases.
    """
    
    def __init__(self):
        self.embedder = OpenAIEmbedder()
        self.vector_store = UpstashVectorStore()
        self.keyword_service = YAKEKeywordService()
        self.reranker = CrossEncoderReranker()
        
        # Adjusted weights for 2-component hybrid (dense + keywords)
        self.dense_weight = config.DENSE_WEIGHT
        self.keyword_weight = config.KEYWORD_WEIGHT
        
        self.logger = app_logger
    
    def retrieve(
        self,
        query: str,
        top_k_candidates: int = None,
        final_top_k: int = None,
        filter_doc_id: Optional[str] = None
    ) -> List[ChunkMetadata]:
        """
        Retrieve and rerank chunks using hybrid NLP approach.
        
        Workflow:
        1. Get candidates from dense retrieval (semantic embeddings)
        2. Compute keyword scores using YAKE
        3. Merge scores using weighted fusion
        4. Rerank top candidates using cross-encoder (neural)
        5. Return final top-k results
        
        Args:
            query: User query
            top_k_candidates: Number of candidates before reranking
            final_top_k: Number of final results after reranking
            filter_doc_id: Optional document ID filter (not used currently)
            
        Returns:
            List of ChunkMetadata objects sorted by relevance
        """
        top_k_candidates = top_k_candidates or config.RERANK_TOP_K
        final_top_k = final_top_k or config.FINAL_TOP_K
        
        self.logger.info(
            f"Hybrid NLP retrieval: query='{query[:50]}...', "
            f"candidates={top_k_candidates}, final={final_top_k}"
        )
        
        # Step 1: Dense retrieval (semantic embeddings)
        query_embedding = self.embedder.embed(query)
        dense_chunks = self.vector_store.query(
            query_embedding,
            top_k=top_k_candidates
        )
        
        self.logger.info(f"Dense retrieval (semantic): {len(dense_chunks)} chunks")
        
        # Step 2: Merge dense results with keyword scores
        merged_chunks = self._merge_results(
            query=query,
            dense_chunks=dense_chunks
        )
        
        self.logger.info(f"Hybrid scoring complete: {len(merged_chunks)} chunks")
        
        # Step 3: Rerank using cross-encoder (neural reranking)
        if self.reranker.is_available() and len(merged_chunks) > 0:
            # Convert merged results to ChunkMetadata for reranking
            chunks_for_reranking = self._dicts_to_chunks(merged_chunks)
            
            reranked_pairs = self.reranker.rerank(
                query=query,
                chunks=chunks_for_reranking,
                top_k=final_top_k
            )
            
            # Extract chunks from (chunk, score) pairs
            final_chunks = [chunk for chunk, score in reranked_pairs]
            
            self.logger.info(
                f"Neural reranking complete: {len(final_chunks)} final results"
            )
        else:
            # No reranking - sort by hybrid score and take top_k
            merged_chunks.sort(key=lambda x: x.get('hybrid_score', 0.0), reverse=True)
            chunks_for_output = self._dicts_to_chunks(merged_chunks[:final_top_k])
            final_chunks = chunks_for_output
            
            self.logger.warning(
                "Reranker unavailable - using hybrid scores only"
            )
        
        return final_chunks
    
    def _merge_results(
        self,
        query: str,
        dense_chunks: List[ChunkMetadata]
    ) -> List[Dict[str, Any]]:
        """
        Merge dense retrieval results with keyword scores.
        
        Implements weighted score fusion:
        hybrid_score = w1 * dense_score + w2 * keyword_score
        
        Args:
            query: User query
            dense_chunks: Results from dense retrieval (semantic embeddings)
            
        Returns:
            List of chunk dictionaries with hybrid scores
        """
        # Build chunk map from dense results
        chunk_map = {}  # chunk_id -> chunk data
        dense_scores = {}
        
        if dense_chunks:
            # Normalize dense scores based on rank
            for i, chunk in enumerate(dense_chunks):
                chunk_id = f"{chunk.doc_id}::{chunk.chunk_id}"
                # Assign decreasing scores based on rank (0-1 normalized)
                dense_scores[chunk_id] = (len(dense_chunks) - i) / len(dense_chunks)
                
                chunk_map[chunk_id] = {
                    'chunk_id': chunk.chunk_id,
                    'doc_id': chunk.doc_id,
                    'text': chunk.text,
                    'doc_name': chunk.doc_name,
                    'page': chunk.page,
                    'block_type': chunk.block_type,
                    'section_heading': chunk.section_heading,
                    'token_count': chunk.token_count,
                    'bbox': chunk.bbox
                }
        
        # Compute keyword scores for all chunks using YAKE
        all_chunks = self._dicts_to_chunks(list(chunk_map.values()))
        chunk_keywords = self.keyword_service.extract_keywords_from_chunks(all_chunks)
        keyword_scores = self.keyword_service.rank_chunks_by_keywords(query, chunk_keywords)
        
        # Compute hybrid scores (dense + keywords)
        merged_results = []
        for chunk_id, chunk_data in chunk_map.items():
            dense_score = dense_scores.get(chunk_id, 0.0)
            keyword_score = keyword_scores.get(chunk_id, 0.0)
            
            # Weighted fusion (2 components: semantic + keywords)
            # Weights are normalized to sum to 1.0
            total_weight = self.dense_weight + self.keyword_weight
            norm_dense_weight = self.dense_weight / total_weight
            norm_keyword_weight = self.keyword_weight / total_weight
            
            hybrid_score = (
                norm_dense_weight * dense_score +
                norm_keyword_weight * keyword_score
            )
            
            chunk_data['hybrid_score'] = hybrid_score
            chunk_data['dense_score'] = dense_score
            chunk_data['keyword_score'] = keyword_score
            
            merged_results.append(chunk_data)
        
        # Sort by hybrid score descending
        merged_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return merged_results
    
    def _dicts_to_chunks(self, chunk_dicts: List[Dict[str, Any]]) -> List[ChunkMetadata]:
        """Convert chunk dictionaries to ChunkMetadata objects."""
        chunks = []
        for d in chunk_dicts:
            chunk = ChunkMetadata(
                doc_id=d['doc_id'],
                chunk_id=d['chunk_id'],
                text=d['text'],
                page=d.get('page', 1),
                bbox=d.get('bbox', []),
                block_type=d.get('block_type', 'paragraph'),
                section_heading=d.get('section_heading'),
                doc_name=d['doc_name'],
                token_count=d.get('token_count', 0)
            )
            chunks.append(chunk)
        return chunks

