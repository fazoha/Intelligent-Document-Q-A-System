"""Service layer for document processing and querying."""

# Phase 1 services
from .document_parser import UnstructuredParser
from .chunk_builder import ChunkBuilder
from .embedding_service import OpenAIEmbedder
from .vector_store import UpstashVectorStore
from .answer_generator import GPTAnswerGenerator

# Phase 2 services (Pure NLP - no external databases)
from .keyword_service import YAKEKeywordService
from .reranker_service import CrossEncoderReranker
from .hybrid_retriever import HybridRetriever
from .query_planner import QueryPlanner

__all__ = [
    # Phase 1
    "UnstructuredParser",
    "ChunkBuilder",
    "OpenAIEmbedder",
    "UpstashVectorStore",
    "GPTAnswerGenerator",
    # Phase 2
    "YAKEKeywordService",
    "CrossEncoderReranker",
    "HybridRetriever",
    "QueryPlanner",
]

