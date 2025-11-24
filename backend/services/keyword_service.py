"""
YAKE keyword extraction service for computing keyword-based retrieval scores.
Provides lightweight unsupervised keyword extraction to enhance retrieval.
"""

from typing import List, Dict, Set
import yake
from models import ChunkMetadata
from utils import config, app_logger


class YAKEKeywordService:
    """Extract and match keywords using YAKE algorithm."""
    
    def __init__(self):
        self.max_keywords = config.YAKE_MAX_KEYWORDS
        self.ngram_size = config.YAKE_NGRAM_SIZE
        self.logger = app_logger
        
        # Initialize YAKE extractor
        # Parameters:
        # - lan: language (English)
        # - n: max ngram size
        # - dedupLim: deduplication threshold (0.9 is high similarity)
        # - top: number of keywords to extract
        # - features: None means use default features
        self.extractor = yake.KeywordExtractor(
            lan="en",
            n=self.ngram_size,
            dedupLim=0.9,
            top=self.max_keywords,
            features=None
        )
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text using YAKE.
        
        Args:
            text: Input text
            
        Returns:
            List of keywords (strings) sorted by relevance
        """
        if not text or not text.strip():
            return []
        
        try:
            # YAKE returns list of (keyword, score) tuples
            # Lower scores are better (more relevant)
            keywords_with_scores = self.extractor.extract_keywords(text)
            
            # Extract just the keywords
            keywords = [kw for kw, score in keywords_with_scores]
            
            return keywords
        
        except Exception as e:
            self.logger.warning(f"YAKE keyword extraction failed: {e}")
            return []
    
    def extract_keywords_from_chunks(
        self,
        chunks: List[ChunkMetadata]
    ) -> Dict[str, List[str]]:
        """
        Extract keywords for multiple chunks.
        
        Args:
            chunks: List of ChunkMetadata objects
            
        Returns:
            Dictionary mapping chunk_id to list of keywords
        """
        chunk_keywords = {}
        
        for chunk in chunks:
            keywords = self.extract_keywords(chunk.text)
            chunk_id = f"{chunk.doc_id}::{chunk.chunk_id}"
            chunk_keywords[chunk_id] = keywords
        
        self.logger.info(
            f"Extracted keywords for {len(chunks)} chunks. "
            f"Avg keywords per chunk: {sum(len(kw) for kw in chunk_keywords.values()) / len(chunks) if chunks else 0:.1f}"
        )
        
        return chunk_keywords
    
    def compute_keyword_overlap_score(
        self,
        query_keywords: List[str],
        chunk_keywords: List[str]
    ) -> float:
        """
        Compute normalized keyword overlap score between query and chunk.
        
        Uses Jaccard similarity: |intersection| / |union|
        
        Args:
            query_keywords: Keywords from query
            chunk_keywords: Keywords from chunk
            
        Returns:
            Overlap score between 0.0 and 1.0
        """
        if not query_keywords or not chunk_keywords:
            return 0.0
        
        # Convert to sets (case-insensitive)
        query_set = set(kw.lower() for kw in query_keywords)
        chunk_set = set(kw.lower() for kw in chunk_keywords)
        
        # Compute Jaccard similarity
        intersection = query_set & chunk_set
        union = query_set | chunk_set
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def rank_chunks_by_keywords(
        self,
        query: str,
        chunks_with_keywords: Dict[str, List[str]]
    ) -> Dict[str, float]:
        """
        Rank chunks by keyword overlap with query.
        
        Args:
            query: User query
            chunks_with_keywords: Dict mapping chunk_id to keywords
            
        Returns:
            Dictionary mapping chunk_id to keyword overlap score
        """
        # Extract query keywords
        query_keywords = self.extract_keywords(query)
        
        if not query_keywords:
            self.logger.warning("No keywords extracted from query")
            return {chunk_id: 0.0 for chunk_id in chunks_with_keywords.keys()}
        
        # Compute overlap scores
        scores = {}
        for chunk_id, chunk_keywords in chunks_with_keywords.items():
            score = self.compute_keyword_overlap_score(query_keywords, chunk_keywords)
            scores[chunk_id] = score
        
        return scores
    
    def get_top_chunks_by_keywords(
        self,
        query: str,
        chunks: List[ChunkMetadata],
        top_k: int = None
    ) -> List[Dict]:
        """
        Retrieve top chunks based on keyword overlap.
        
        Args:
            query: User query
            chunks: List of candidate chunks
            top_k: Number of results to return
            
        Returns:
            List of dicts with chunk metadata and keyword scores
        """
        top_k = top_k or config.RERANK_TOP_K
        
        # Extract keywords for all chunks
        chunk_keywords = self.extract_keywords_from_chunks(chunks)
        
        # Rank by keywords
        scores = self.rank_chunks_by_keywords(query, chunk_keywords)
        
        # Sort chunks by score
        ranked_results = []
        for chunk in chunks:
            chunk_id = f"{chunk.doc_id}::{chunk.chunk_id}"
            score = scores.get(chunk_id, 0.0)
            
            result = {
                'chunk_id': chunk.chunk_id,
                'doc_id': chunk.doc_id,
                'text': chunk.text,
                'doc_name': chunk.doc_name,
                'page': chunk.page,
                'block_type': chunk.block_type,
                'section_heading': chunk.section_heading,
                'token_count': chunk.token_count,
                'keyword_score': score,
                'keywords': chunk_keywords.get(chunk_id, [])
            }
            ranked_results.append(result)
        
        # Sort by keyword score descending
        ranked_results.sort(key=lambda x: x['keyword_score'], reverse=True)
        
        return ranked_results[:top_k]

