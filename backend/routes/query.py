"""
Query and answer generation endpoints.

Phase 2 enhancements:
- Hybrid retrieval (dense + keywords)
- Cross-encoder reranking
- Multi-hop query planning

Phase 3 enhancements:
- Confidence scoring (ROUGE-L)
- Extractive fallback for low-confidence answers
"""

import time
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from models import QueryRequest, QueryResponse, ChunkMetadata
from services import (
    # Phase 1 services
    GPTAnswerGenerator,
    # Phase 2 services
    HybridRetriever,
    QueryPlanner,
)
from utils import app_logger, config

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query")
async def query_documents(request: QueryRequest) -> QueryResponse:
    """
    Query documents and generate an answer.
    
    Phase 2 Workflow:
    1. Query planning: Analyze query for multi-hop requirements
    2. Hybrid retrieval: Combine dense + keyword matching
    3. Reranking: Use cross-encoder to rerank candidates
    4. Answer generation: GPT-5-mini with context
    5. Citation extraction
    
    Phase 3 Enhancements:
    6. Confidence scoring: ROUGE-L overlap validation
    7. Extractive fallback: Direct span extraction for low-confidence answers
    """
    logger = app_logger
    start_time = time.time()
    
    logger.info(f"Received query (Phase 3): {request.query}")
    
    try:
        # Phase 2: Initialize query planner
        query_planner = QueryPlanner()
        
        # Step 1: Analyze query
        query_analysis = query_planner.analyze_query(request.query)
        is_multi_hop = query_planner.should_use_multi_hop(query_analysis)
        
        logger.info(
            f"Query analysis: multi_hop={is_multi_hop}, "
            f"type={query_analysis.get('question_type')}"
        )
        
        # Step 2: Retrieve chunks using hybrid approach
        hybrid_retriever = HybridRetriever()
        
        if is_multi_hop:
            # Multi-hop retrieval: Process sub-queries sequentially
            chunks = await _multi_hop_retrieval(
                query_analysis=query_analysis,
                hybrid_retriever=hybrid_retriever,
                logger=logger
            )
        else:
            # Single-hop retrieval
            chunks = hybrid_retriever.retrieve(
                query=request.query,
                top_k_candidates=config.RERANK_TOP_K,
                final_top_k=config.FINAL_TOP_K
            )
        
        if not chunks:
            logger.warning("No chunks found")
            return QueryResponse(
                answer="I don't have any documents indexed to answer this question. Please upload a document first.",
                citations=[],
                query_time_ms=int((time.time() - start_time) * 1000),
                retrieved_chunks=0,
                confidence_score=0.0,
                confidence_level="low",
                answer_type="generative"
            )
        
        logger.info(f"Retrieved {len(chunks)} chunks after hybrid retrieval + reranking")
        
        # Step 3: Generate answer with confidence scoring (Phase 3)
        answer_generator = GPTAnswerGenerator()
        result = answer_generator.generate_with_confidence(request.query, chunks)
        
        # Calculate query time
        query_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Query completed in {query_time_ms}ms (Phase 3). "
            f"Answer type: {result.answer_type}, "
            f"Confidence: {result.confidence_score:.3f} ({result.confidence_level}), "
            f"Answer length: {len(result.answer)} chars, Citations: {len(result.citations)}"
        )
        
        return QueryResponse(
            answer=result.answer,
            citations=result.citations,
            query_time_ms=query_time_ms,
            retrieved_chunks=len(chunks),
            confidence_score=result.confidence_score,
            confidence_level=result.confidence_level,
            answer_type=result.answer_type,
            extractive_span=result.extractive_span
        )
    
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


async def _multi_hop_retrieval(
    query_analysis: Dict[str, Any],
    hybrid_retriever: HybridRetriever,
    logger
) -> List[ChunkMetadata]:
    """
    Execute multi-hop retrieval for complex queries.
    
    Strategy:
    1. Process each sub-query sequentially
    2. Combine and deduplicate results
    3. Rerank combined results
    
    Args:
        query_analysis: Query analysis from QueryPlanner
        hybrid_retriever: HybridRetriever instance
        logger: Logger instance
        
    Returns:
        List of ChunkMetadata objects
    """
    sub_queries = query_analysis.get('sub_queries', [])
    
    if not sub_queries:
        # Fallback to original query
        sub_queries = [query_analysis.get('original_query', '')]
    
    logger.info(f"Multi-hop retrieval with {len(sub_queries)} sub-queries")
    
    all_chunks = []
    seen_chunk_ids = set()
    
    for i, sub_query in enumerate(sub_queries):
        logger.info(f"Processing sub-query {i+1}/{len(sub_queries)}: {sub_query[:50]}...")
        
        # Retrieve for this sub-query
        sub_chunks = hybrid_retriever.retrieve(
            query=sub_query,
            top_k_candidates=config.RERANK_TOP_K,
            final_top_k=config.FINAL_TOP_K
        )
        
        # Add new chunks (deduplicate)
        for chunk in sub_chunks:
            chunk_key = f"{chunk.doc_id}::{chunk.chunk_id}"
            if chunk_key not in seen_chunk_ids:
                all_chunks.append(chunk)
                seen_chunk_ids.add(chunk_key)
        
        logger.info(f"Sub-query {i+1} retrieved {len(sub_chunks)} chunks")
    
    logger.info(
        f"Multi-hop retrieval complete: {len(all_chunks)} unique chunks "
        f"from {len(sub_queries)} sub-queries"
    )
    
    # Return top-k chunks (may already be limited by individual retrievals)
    return all_chunks[:config.FINAL_TOP_K * 2]  # Allow more chunks for multi-hop

