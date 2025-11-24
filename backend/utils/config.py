"""
Configuration management for the Document Q&A system.
Loads and validates environment variables.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Upstash Vector
    UPSTASH_VECTOR_REST_URL: str = os.getenv("UPSTASH_VECTOR_REST_URL", "")
    UPSTASH_VECTOR_REST_TOKEN: str = os.getenv("UPSTASH_VECTOR_REST_TOKEN", "")
    
    # Unstructured.io
    UNSTRUCTURED_API_KEY: str = os.getenv("UNSTRUCTURED_API_KEY", "")
    UNSTRUCTURED_API_URL: str = os.getenv(
        "UNSTRUCTURED_API_URL",
        "https://api.unstructured.io/general/v0/general"
    )
    
    # FastAPI
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    
    # Next.js
    NEXT_PUBLIC_API_URL: str = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")
    
    # File upload limits
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set = {".pdf", ".png", ".jpg", ".jpeg", ".docx"}
    
    # Chunking parameters
    MAX_CHUNK_TOKENS: int = 512
    
    # Retrieval parameters
    TOP_K_CHUNKS: int = 5
    
    # Phase 2: Hybrid retrieval weights (Pure NLP: Dense + Keywords)
    # Note: BM25 removed - using only dense embeddings + YAKE keywords
    DENSE_WEIGHT: float = float(os.getenv("DENSE_WEIGHT", "0.7"))  # Semantic similarity (increased)
    KEYWORD_WEIGHT: float = float(os.getenv("KEYWORD_WEIGHT", "0.3"))  # YAKE keyword overlap (increased)
    
    # Phase 2: Neural reranking
    RERANK_MODEL: str = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    RERANK_TOP_K: int = int(os.getenv("RERANK_TOP_K", "20"))  # Candidates before reranking
    FINAL_TOP_K: int = int(os.getenv("FINAL_TOP_K", "5"))  # Final results after reranking
    
    # Phase 2: Query planner (spaCy)
    SPACY_MODEL: str = os.getenv("SPACY_MODEL", "en_core_web_sm")
    ENABLE_MULTI_HOP: bool = os.getenv("ENABLE_MULTI_HOP", "true").lower() == "true"
    
    # Phase 2: YAKE keyword extraction
    YAKE_MAX_KEYWORDS: int = int(os.getenv("YAKE_MAX_KEYWORDS", "10"))
    YAKE_NGRAM_SIZE: int = int(os.getenv("YAKE_NGRAM_SIZE", "3"))
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate that required environment variables are set.
        Raises ValueError if any required variable is missing.
        """
        required_vars = {
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
            "UPSTASH_VECTOR_REST_URL": cls.UPSTASH_VECTOR_REST_URL,
            "UPSTASH_VECTOR_REST_TOKEN": cls.UPSTASH_VECTOR_REST_TOKEN,
            "UNSTRUCTURED_API_KEY": cls.UNSTRUCTURED_API_KEY,
        }
        
        missing = [key for key, value in required_vars.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please check your .env file."
            )
    
    @classmethod
    def get_temp_upload_dir(cls) -> str:
        """Get the temporary upload directory path."""
        temp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir


# Singleton config instance
config = Config()

