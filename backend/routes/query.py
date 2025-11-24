"""
Query and answer generation endpoints.
"""

import time
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from models import QueryRequest, QueryResponse, Citation
from services import OpenAIEmbedder, UpstashVectorStore, GPTAnswerGenerator
from utils import app_logger

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query")
async def query_documents(request: QueryRequest) -> QueryResponse:
    """
    Query documents and generate an answer.
    
    Workflow:
    1. Embed the query
    2. Retrieve top-k similar chunks from vector store
    3. Generate answer using GPT-5-mini with retrieved context
    4. Extract citations
    5. Return answer with citations
    """
    logger = app_logger
    start_time = time.time()
    
    logger.info(f"Received query: {request.query}")
    
    try:
        # Step 1: Embed query
        embedder = OpenAIEmbedder()
        query_embedding = embedder.embed(request.query)
        
        # Step 2: Retrieve similar chunks
        vector_store = UpstashVectorStore()
        chunks = vector_store.query(query_embedding)
        
        if not chunks:
            logger.warning("No chunks found in vector store")
            return QueryResponse(
                answer="I don't have any documents indexed to answer this question. Please upload a document first.",
                citations=[],
                query_time_ms=int((time.time() - start_time) * 1000),
                retrieved_chunks=0
            )
        
        logger.info(f"Retrieved {len(chunks)} chunks")
        
        # Step 3 & 4: Generate answer and extract citations
        answer_generator = GPTAnswerGenerator()
        answer, citations = answer_generator.generate(request.query, chunks)
        
        # Calculate query time
        query_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Query completed in {query_time_ms}ms. "
            f"Answer length: {len(answer)} chars, Citations: {len(citations)}"
        )
        
        return QueryResponse(
            answer=answer,
            citations=citations,
            query_time_ms=query_time_ms,
            retrieved_chunks=len(chunks)
        )
    
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )

